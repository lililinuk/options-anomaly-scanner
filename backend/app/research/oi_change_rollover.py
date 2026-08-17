from __future__ import annotations

import argparse
import asyncio
import csv
import json
import os
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import date, datetime, time, timezone
from pathlib import Path
from typing import Any, Protocol
from zoneinfo import ZoneInfo

import exchange_calendars as xcals
import pandas as pd

from app.config import get_settings
from app.nightwatch.client import NightwatchClient
from app.nightwatch.errors import NightwatchError
from app.nightwatch.models import ApiUsageEvent, NightwatchResult

EXPERIMENT_TICKERS = ("NVDA", "AAPL", "TSLA")
TARGET_SOURCE_DATES = (
    date(2026, 8, 17),
    date(2026, 8, 18),
    date(2026, 8, 19),
    date(2026, 8, 20),
    date(2026, 8, 21),
)
APPROVED_PROBE_DATES = frozenset(
    {
        date(2026, 8, 18),
        date(2026, 8, 19),
        date(2026, 8, 20),
        date(2026, 8, 21),
        date(2026, 8, 24),
    }
)
NEW_YORK = ZoneInfo("America/New_York")
SCHEMA_VERSION = "oi_change_rollover_probe.v1"
REFERENCE_SEMANTICS = {
    "event_date": "vendor observation_date",
    "first_seen_at": "earliest experiment probe that observed the vendor date",
    "exact_vendor_publication_time": "UNKNOWN",
}


class ProbeClient(Protocol):
    async def request(
        self,
        method: str,
        path: str,
        *,
        command: str | None = None,
        ticker: str | None = None,
    ) -> NightwatchResult: ...


@dataclass(frozen=True)
class ExperimentGuard:
    request_time_utc: datetime
    request_time_new_york: datetime
    new_york_date: date
    eligible: bool
    expected_latest_completed_xnys_session: date | None
    status: str


@dataclass(frozen=True)
class ProbeRecord:
    schema_version: str
    github_run_id: str
    github_run_attempt: str
    request_time_utc: str
    request_time_new_york: str
    ticker: str
    endpoint: str
    http_status: int | None
    success: bool
    result_state: str
    network_attempts: int
    retries: int
    row_count: int
    distinct_observation_dates: list[str]
    invalid_observation_date_count: int
    earliest_observation_date: str | None
    latest_observation_date: str | None
    distinct_previous_dates: list[str]
    invalid_previous_date_count: int
    latest_date_row_count: int
    non_null_premium_usd_count: int
    non_null_oi_diff_count: int
    vendor_rank_min: int | None
    vendor_rank_max: int | None
    expected_latest_completed_xnys_session: str
    freshness_state: str
    trading_session_lag: int | None
    quota_remaining_after_request: int | None


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def xnys_calendar() -> Any:
    return xcals.get_calendar("XNYS")


def expected_latest_completed_session(
    probe_date: date, *, calendar: Any | None = None
) -> date | None:
    calendar = calendar or xnys_calendar()
    label = pd.Timestamp(probe_date.isoformat())
    if not calendar.is_session(label):
        return None
    return calendar.previous_session(label).date()


def evaluate_experiment_guard(now_utc: datetime, *, calendar: Any | None = None) -> ExperimentGuard:
    request_utc = _utc(now_utc)
    request_ny = request_utc.astimezone(NEW_YORK)
    ny_date = request_ny.date()
    expected = expected_latest_completed_session(ny_date, calendar=calendar)
    eligible = ny_date in APPROVED_PROBE_DATES and expected in TARGET_SOURCE_DATES
    status = "ELIGIBLE" if eligible else "SKIPPED_DATE_GUARD"
    return ExperimentGuard(request_utc, request_ny, ny_date, eligible, expected, status)


def _parsed_date(value: Any) -> date | None:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if not isinstance(value, str):
        return None
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        return None


def _signed_trading_session_lag(
    latest: date | None,
    expected: date,
    *,
    calendar: Any | None = None,
) -> int | None:
    if latest is None:
        return None
    calendar = calendar or xnys_calendar()
    latest_label = pd.Timestamp(latest.isoformat())
    expected_label = pd.Timestamp(expected.isoformat())
    if not calendar.is_session(latest_label) or not calendar.is_session(expected_label):
        return None
    if latest == expected:
        return 0
    if latest < expected:
        return len(calendar.sessions_in_range(calendar.next_session(latest_label), expected_label))
    return -len(calendar.sessions_in_range(calendar.next_session(expected_label), latest_label))


def freshness_state(
    observation_dates: Iterable[date],
    *,
    invalid_date_count: int,
    expected: date,
) -> str:
    distinct = sorted(set(observation_dates))
    if not distinct:
        return "UNAVAILABLE"
    if invalid_date_count or len(distinct) != 1:
        return "AMBIGUOUS"
    latest = distinct[-1]
    if latest == expected:
        return "CURRENT"
    if latest < expected:
        return "STALE"
    return "AHEAD_OR_UNEXPECTED"


def _integer(value: Any) -> int | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def summarize_response(
    *,
    ticker: str,
    payload: Any,
    http_status: int,
    request_time_utc: datetime,
    expected_session: date,
    github_run_id: str,
    github_run_attempt: str,
    network_attempts: int,
    retries: int,
    quota_remaining_after: int | None,
    calendar: Any | None = None,
) -> ProbeRecord:
    request_utc = _utc(request_time_utc)
    request_ny = request_utc.astimezone(NEW_YORK)
    data = payload.get("data") if isinstance(payload, dict) else None
    raw_rows = data.get("contracts") if isinstance(data, dict) else None
    parse_error = not isinstance(raw_rows, list)
    rows = raw_rows if isinstance(raw_rows, list) else []
    dict_rows = [row for row in rows if isinstance(row, dict)]

    parsed_observation_dates = [_parsed_date(row.get("date")) for row in dict_rows]
    observation_dates = [value for value in parsed_observation_dates if value is not None]
    invalid_observation_dates = len(rows) - len(observation_dates)
    distinct_observations = sorted(set(observation_dates))
    latest = distinct_observations[-1] if distinct_observations else None
    earliest = distinct_observations[0] if distinct_observations else None

    parsed_previous_dates = [_parsed_date(row.get("prev_date")) for row in dict_rows]
    previous_dates = [value for value in parsed_previous_dates if value is not None]
    invalid_previous_dates = len(rows) - len(previous_dates)

    latest_rows = [
        row for row in dict_rows if latest is not None and _parsed_date(row.get("date")) == latest
    ]
    ranks = [_integer(row.get("rank")) for row in latest_rows]
    valid_ranks = [value for value in ranks if value is not None]
    freshness = freshness_state(
        observation_dates,
        invalid_date_count=invalid_observation_dates,
        expected=expected_session,
    )

    if parse_error:
        result_state = "PARSE_ERROR"
    elif not rows:
        result_state = "EMPTY_RESPONSE"
    elif not observation_dates:
        result_state = "NO_OBSERVATION_DATE"
    elif freshness == "AMBIGUOUS":
        result_state = "AMBIGUOUS_OBSERVATION_DATES"
    else:
        result_state = "SUCCESS"

    return ProbeRecord(
        schema_version=SCHEMA_VERSION,
        github_run_id=github_run_id,
        github_run_attempt=github_run_attempt,
        request_time_utc=request_utc.isoformat(),
        request_time_new_york=request_ny.isoformat(),
        ticker=ticker,
        endpoint=f"/v1/options/oi-change/{ticker}",
        http_status=http_status,
        success=result_state == "SUCCESS",
        result_state=result_state,
        network_attempts=network_attempts,
        retries=retries,
        row_count=len(rows),
        distinct_observation_dates=[value.isoformat() for value in distinct_observations],
        invalid_observation_date_count=invalid_observation_dates,
        earliest_observation_date=earliest.isoformat() if earliest else None,
        latest_observation_date=latest.isoformat() if latest else None,
        distinct_previous_dates=[value.isoformat() for value in sorted(set(previous_dates))],
        invalid_previous_date_count=invalid_previous_dates,
        latest_date_row_count=len(latest_rows),
        non_null_premium_usd_count=sum(row.get("premium_usd") is not None for row in latest_rows),
        non_null_oi_diff_count=sum(row.get("oi_diff") is not None for row in latest_rows),
        vendor_rank_min=min(valid_ranks) if valid_ranks else None,
        vendor_rank_max=max(valid_ranks) if valid_ranks else None,
        expected_latest_completed_xnys_session=expected_session.isoformat(),
        freshness_state=freshness,
        trading_session_lag=_signed_trading_session_lag(
            latest, expected_session, calendar=calendar
        ),
        quota_remaining_after_request=quota_remaining_after,
    )


def failure_record(
    *,
    ticker: str,
    request_time_utc: datetime,
    expected_session: date,
    github_run_id: str,
    github_run_attempt: str,
    http_status: int | None,
    result_state: str,
    network_attempts: int,
    retries: int,
) -> ProbeRecord:
    request_utc = _utc(request_time_utc)
    return ProbeRecord(
        schema_version=SCHEMA_VERSION,
        github_run_id=github_run_id,
        github_run_attempt=github_run_attempt,
        request_time_utc=request_utc.isoformat(),
        request_time_new_york=request_utc.astimezone(NEW_YORK).isoformat(),
        ticker=ticker,
        endpoint=f"/v1/options/oi-change/{ticker}",
        http_status=http_status,
        success=False,
        result_state=result_state,
        network_attempts=network_attempts,
        retries=retries,
        row_count=0,
        distinct_observation_dates=[],
        invalid_observation_date_count=0,
        earliest_observation_date=None,
        latest_observation_date=None,
        distinct_previous_dates=[],
        invalid_previous_date_count=0,
        latest_date_row_count=0,
        non_null_premium_usd_count=0,
        non_null_oi_diff_count=0,
        vendor_rank_min=None,
        vendor_rank_max=None,
        expected_latest_completed_xnys_session=expected_session.isoformat(),
        freshness_state="UNAVAILABLE",
        trading_session_lag=None,
        quota_remaining_after_request=None,
    )


async def run_live_probes(
    *,
    client: ProbeClient,
    usage_events: list[ApiUsageEvent],
    expected_session: date,
    approved_new_york_date: date,
    github_run_id: str,
    github_run_attempt: str,
) -> list[ProbeRecord]:
    records: list[ProbeRecord] = []
    for ticker in EXPERIMENT_TICKERS:
        actual_now = datetime.now(timezone.utc)
        if actual_now.astimezone(NEW_YORK).date() != approved_new_york_date:
            break
        event_count = len(usage_events)
        try:
            result = await client.request(
                "GET",
                f"/v1/options/oi-change/{ticker}",
                command="research.options.oi_change.rollover_timing",
                ticker=ticker,
            )
        except NightwatchError as error:
            event = usage_events[-1] if len(usage_events) > event_count else None
            records.append(
                failure_record(
                    ticker=ticker,
                    request_time_utc=event.requested_at if event else actual_now,
                    expected_session=expected_session,
                    github_run_id=github_run_id,
                    github_run_attempt=github_run_attempt,
                    http_status=error.status_code,
                    result_state="HTTP_ERROR" if error.status_code else "TRANSPORT_ERROR",
                    network_attempts=event.attempt_count if event else 0,
                    retries=event.retry_count if event else 0,
                )
            )
            continue

        event = usage_events[-1]
        records.append(
            summarize_response(
                ticker=ticker,
                payload=result.payload,
                http_status=result.status_code,
                request_time_utc=event.requested_at,
                expected_session=expected_session,
                github_run_id=github_run_id,
                github_run_attempt=github_run_attempt,
                network_attempts=event.attempt_count,
                retries=event.retry_count,
                quota_remaining_after=result.quota.quota_remaining,
            )
        )
    return records


CSV_FIELDS = tuple(ProbeRecord.__dataclass_fields__)


def _csv_value(value: Any) -> Any:
    if isinstance(value, list):
        return "|".join(str(item) for item in value)
    return value


def write_probe_outputs(
    output_dir: Path,
    *,
    metadata: dict[str, Any],
    records: list[ProbeRecord],
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    document = {
        "schema_version": SCHEMA_VERSION,
        "semantics": REFERENCE_SEMANTICS,
        "run": metadata,
        "records": [asdict(record) for record in records],
    }
    (output_dir / "probe_results.json").write_text(
        json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    with (output_dir / "probe_results.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for record in records:
            writer.writerow({key: _csv_value(value) for key, value in asdict(record).items()})
    (output_dir / "step_summary.md").write_text(
        current_step_summary(metadata, records), encoding="utf-8"
    )


def current_step_summary(metadata: dict[str, Any], records: list[ProbeRecord]) -> str:
    lines = [
        "## Nightwatch OI Change Rollover Timing Experiment",
        "",
        f"- Run status: `{metadata['status']}`",
        f"- Mode: `{metadata['mode']}`",
        f"- Probe time ET: `{metadata['guard']['request_time_new_york']}`",
        f"- Expected vendor date: `{metadata['guard'].get('expected_session') or 'N/A'}`",
        f"- Network attempts: `{metadata['network_attempts']}`",
        "",
    ]
    if not records:
        lines.append("No Nightwatch request was made.")
    else:
        lines.extend(
            [
                "| Ticker | Latest observation date | Freshness | Result |",
                "|---|---|---|---|",
            ]
        )
        for record in records:
            lines.append(
                f"| {record.ticker} | {record.latest_observation_date or 'N/A'} | "
                f"{record.freshness_state} | {record.result_state} |"
            )
        failures = sum(not record.success for record in records)
        rollover = sum(record.freshness_state == "CURRENT" for record in records)
        lines.extend(
            [
                "",
                f"- Current/rollover observations: `{rollover}`",
                f"- Failures or non-authoritative responses: `{failures}`",
            ]
        )
    return "\n".join(lines) + "\n"


def _record_time(record: dict[str, Any]) -> datetime:
    return datetime.fromisoformat(record["request_time_new_york"])


def _availability_by(records: list[dict[str, Any]], cutoff: time) -> str:
    current_before = any(
        record.get("freshness_state") == "CURRENT" and _record_time(record).time() <= cutoff
        for record in records
    )
    if current_before:
        return "YES"
    stale_at_or_after = any(
        record.get("freshness_state") == "STALE" and _record_time(record).time() >= cutoff
        for record in records
    )
    return "NO" if stale_at_or_after else "UNKNOWN"


def cumulative_rows(records: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        target = record.get("expected_latest_completed_xnys_session")
        ticker = record.get("ticker")
        if target and ticker in EXPERIMENT_TICKERS:
            grouped[(target, ticker)].append(record)

    rows: list[dict[str, Any]] = []
    for (target, ticker), items in sorted(grouped.items()):
        items.sort(key=_record_time)
        current = [item for item in items if item.get("freshness_state") == "CURRENT"]
        first_current = current[0] if current else None
        stale = [
            item
            for item in items
            if item.get("freshness_state") == "STALE"
            and (first_current is None or _record_time(item) < _record_time(first_current))
        ]
        last_stale = stale[-1] if stale else None
        first_text = first_current["request_time_new_york"] if first_current else None
        stale_text = last_stale["request_time_new_york"] if last_stale else None
        first_current_run_key = (
            f"{first_current.get('github_run_id')}:{first_current.get('github_run_attempt')}"
            if first_current
            else None
        )
        if stale_text and first_text:
            publication_window = f"({stale_text}, {first_text}]"
        elif first_text:
            publication_window = f"(no prior stale probe, {first_text}]"
        else:
            publication_window = "UNRESOLVED"
        rows.append(
            {
                "target_date": target,
                "ticker": ticker,
                "last_stale_probe": stale_text,
                "first_current_probe": first_text,
                "first_current_run_key": first_current_run_key,
                "observed_publication_window": publication_window,
                "premarket_by_09_25_et": _availability_by(items, time(9, 25)),
                "available_by_09_30_et": _availability_by(items, time(9, 30)),
                "available_by_10_00_et": _availability_by(items, time(10, 0)),
                "final_state": items[-1].get("freshness_state", "UNRESOLVED"),
                "probe_count": len(items),
            }
        )
    return rows


def cross_ticker_rollover(rows: Iterable[dict[str, Any]]) -> dict[str, str]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[row["target_date"]].append(row)
    result: dict[str, str] = {}
    for target, items in grouped.items():
        by_ticker = {item["ticker"]: item for item in items}
        first_seen_runs = [
            by_ticker[ticker].get("first_current_run_key")
            for ticker in EXPERIMENT_TICKERS
            if ticker in by_ticker
        ]
        if len(by_ticker) < len(EXPERIMENT_TICKERS):
            result[target] = "INCOMPLETE"
        elif not any(first_seen_runs):
            result[target] = "UNRESOLVED"
        elif not all(first_seen_runs):
            result[target] = "INCOMPLETE"
        elif len(set(first_seen_runs)) == 1:
            result[target] = "SIMULTANEOUS_WITHIN_PROBE_RESOLUTION"
        else:
            result[target] = "STAGGERED"
    return result


CUMULATIVE_FIELDS = (
    "target_date",
    "ticker",
    "last_stale_probe",
    "first_current_probe",
    "observed_publication_window",
    "premarket_by_09_25_et",
    "available_by_09_30_et",
    "available_by_10_00_et",
    "final_state",
    "probe_count",
)


def load_probe_records(paths: Iterable[Path]) -> list[dict[str, Any]]:
    deduplicated: dict[tuple[str, str, str], dict[str, Any]] = {}
    for path in paths:
        try:
            document = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if document.get("schema_version") != SCHEMA_VERSION:
            continue
        for record in document.get("records", []):
            if not isinstance(record, dict):
                continue
            key = (
                str(record.get("github_run_id")),
                str(record.get("github_run_attempt")),
                str(record.get("ticker")),
            )
            deduplicated[key] = record
    return sorted(deduplicated.values(), key=_record_time)


def write_cumulative_outputs(output_dir: Path, records: list[dict[str, Any]]) -> None:
    rows = cumulative_rows(records)
    cross_ticker = cross_ticker_rollover(rows)
    with (output_dir / "oi_change_rollover_cumulative.csv").open(
        "w", newline="", encoding="utf-8"
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=CUMULATIVE_FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    lines = [
        "## Cumulative OI Change Rollover Summary",
        "",
        "`first_seen_at` is the earliest experiment observation, not the exact vendor "
        "publication timestamp.",
        "",
        "| Target Date | Ticker | Last Stale Probe | First Current Probe | "
        "Observed Publication Window | Premarket by 09:25 ET? | Available by 09:30 ET? | "
        "Available by 10:00 ET? | Final State |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['target_date']} | {row['ticker']} | "
            f"{row['last_stale_probe'] or 'N/A'} | {row['first_current_probe'] or 'N/A'} | "
            f"{row['observed_publication_window']} | {row['premarket_by_09_25_et']} | "
            f"{row['available_by_09_30_et']} | {row['available_by_10_00_et']} | "
            f"{row['final_state']} |"
        )
    lines.extend(["", "### Cross-ticker rollover", ""])
    if cross_ticker:
        for target, state in sorted(cross_ticker.items()):
            lines.append(f"- {target}: `{state}`")
    else:
        lines.append("No live probe records are available yet.")
    lines.extend(
        [
            "",
            "`event_date` = vendor `observation_date`; `exact_vendor_publication_time` = "
            "`UNKNOWN`.",
            "",
        ]
    )
    (output_dir / "oi_change_rollover_summary.md").write_text("\n".join(lines), encoding="utf-8")


async def probe_command(mode: str, output_dir: Path) -> int:
    now = datetime.now(timezone.utc)
    guard = evaluate_experiment_guard(now)
    github_run_id = os.getenv("GITHUB_RUN_ID", "local")
    github_run_attempt = os.getenv("GITHUB_RUN_ATTEMPT", "1")
    records: list[ProbeRecord] = []
    usage_events: list[ApiUsageEvent] = []

    if mode == "dry_run":
        status = "DRY_RUN"
    elif not guard.eligible or guard.expected_latest_completed_xnys_session is None:
        status = "SKIPPED_DATE_GUARD"
    else:
        settings = get_settings()
        if settings.nightwatch_api_key is None:
            status = "CONFIGURATION_ERROR"
        else:

            async def observe(event: ApiUsageEvent) -> None:
                usage_events.append(event)

            async with NightwatchClient(
                base_url=str(settings.nightwatch_base_url),
                api_key=settings.nightwatch_api_key,
                timeout_seconds=settings.nightwatch_timeout_seconds,
                max_retries=0,
                max_concurrency=1,
                usage_observer=observe,
            ) as client:
                records = await run_live_probes(
                    client=client,
                    usage_events=usage_events,
                    expected_session=guard.expected_latest_completed_xnys_session,
                    approved_new_york_date=guard.new_york_date,
                    github_run_id=github_run_id,
                    github_run_attempt=github_run_attempt,
                )
            success_count = sum(record.success for record in records)
            status = (
                "COMPLETE"
                if success_count == len(EXPERIMENT_TICKERS)
                else "PARTIAL"
                if success_count
                else "FAILED"
            )

    metadata = {
        "mode": mode,
        "status": status,
        "github_run_id": github_run_id,
        "github_run_attempt": github_run_attempt,
        "tickers": list(EXPERIMENT_TICKERS),
        "guard": {
            "status": guard.status,
            "eligible": guard.eligible,
            "request_time_utc": guard.request_time_utc.isoformat(),
            "request_time_new_york": guard.request_time_new_york.isoformat(),
            "new_york_date": guard.new_york_date.isoformat(),
            "expected_session": (
                guard.expected_latest_completed_xnys_session.isoformat()
                if guard.expected_latest_completed_xnys_session
                else None
            ),
        },
        "network_attempts": sum(event.attempt_count for event in usage_events),
        "retries": sum(event.retry_count for event in usage_events),
        "nightwatch_requests": len(usage_events),
        "database_writes": 0,
        "raw_responses_persisted": False,
        "exact_paid_units": "NOT_INFERRED",
    }
    write_probe_outputs(output_dir, metadata=metadata, records=records)
    print(
        f"status={status} mode={mode} records={len(records)} "
        f"network_attempts={metadata['network_attempts']} retries={metadata['retries']}"
    )
    return 2 if status == "CONFIGURATION_ERROR" else 0


def aggregate_command(output_dir: Path, current: Path, prior_root: Path | None) -> int:
    paths = [current]
    if prior_root and prior_root.exists():
        paths.extend(prior_root.rglob("probe_results.json"))
    records = load_probe_records(paths)
    write_cumulative_outputs(output_dir, records)
    print(f"cumulative_records={len(records)}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Isolated OI-change rollover timing research")
    subcommands = parser.add_subparsers(dest="command", required=True)
    probe = subcommands.add_parser("probe")
    probe.add_argument("--mode", choices=("dry_run", "live"), required=True)
    probe.add_argument("--output-dir", type=Path, required=True)
    aggregate = subcommands.add_parser("aggregate")
    aggregate.add_argument("--output-dir", type=Path, required=True)
    aggregate.add_argument("--current", type=Path, required=True)
    aggregate.add_argument("--prior-root", type=Path)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.command == "probe":
        return asyncio.run(probe_command(args.mode, args.output_dir))
    return aggregate_command(args.output_dir, args.current, args.prior_root)


if __name__ == "__main__":
    raise SystemExit(main())
