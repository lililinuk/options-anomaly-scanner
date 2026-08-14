import argparse
import asyncio
import sys

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.config import get_settings
from app.confirmation.service import Phase2bContextService
from app.confirmation.state_v2 import Phase2bV2StateService
from app.db.session import get_session_factory
from app.metadata.service import ApiUsageCollector, refresh_metadata
from app.nightwatch.client import NightwatchClient
from app.nightwatch.errors import NightwatchError
from app.persistence.api_usage import persist_api_usage
from app.persistence.metadata import MetadataRepository
from app.scanner.archive import ArchiveConcurrentError, DailyOiArchiver
from app.scanner.daily import DailyCollectionConcurrentError, DailyDataPipeline, DailyRadarBackfill
from app.scanner.service import ConcurrentScanError
from app.scanner.v13 import Mag7Scanner


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Options Anomaly Scanner developer commands")
    subcommands = parser.add_subparsers(dest="command", required=True)
    subcommands.add_parser(
        "refresh-metadata",
        help="Fetch /v1/discover, persist it, and verify database read-back",
    )
    subcommands.add_parser(
        "run-mag7-scan",
        help="Run one budget-bounded manual Phase 2A v1.2 calibrated-discovery scan",
    )
    subcommands.add_parser(
        "archive-mag7-oi",
        help="Idempotently archive complete 0-180 DTE MAG7 daily OI snapshots",
    )
    subcommands.add_parser(
        "archive-mag7-daily",
        help="Run independent daily OI, expiry-activity, and OI-change Radar subjobs",
    )
    subcommands.add_parser(
        "backfill-mag7-radar",
        help="Evaluate stored Radar and fetch only missing latest-date MAG7 ticker coverage",
    )
    phase2b = subcommands.add_parser(
        "refresh-phase2b-context",
        help="Refresh five safe Phase 2B context products for selected persisted candidates",
    )
    phase2b.add_argument("--contract", action="append", required=True)
    phase2b.add_argument("--force", action="store_true")
    phase2b.add_argument(
        "--reuse-latest-raw",
        action="store_true",
        help="Append current-spec normalization from preserved raw ticker context when available",
    )
    phase2b_v2 = subcommands.add_parser(
        "build-phase2b-v2-states",
        help="Build append-only Phase 2B v2 research states from persisted evidence only",
    )
    phase2b_v2.add_argument("--contract", action="append", required=True)
    return parser


async def run_refresh_metadata() -> int:
    settings = get_settings()
    collector = ApiUsageCollector()
    try:
        with get_session_factory()() as session:
            # Fail before contacting Nightwatch when persistence is unavailable.
            session.execute(text("SELECT 1"))
            store = MetadataRepository(session)
            async with NightwatchClient(
                base_url=str(settings.nightwatch_base_url),
                api_key=settings.nightwatch_api_key,
                timeout_seconds=settings.nightwatch_timeout_seconds,
                max_retries=settings.nightwatch_max_retries,
                max_concurrency=settings.nightwatch_max_concurrency,
                usage_observer=collector,
            ) as client:
                summary = await refresh_metadata(
                    client=client,
                    store=store,
                    usage_collector=collector,
                )
    except SQLAlchemyError:
        print(
            "Metadata refresh failed: development database unavailable; verify DATABASE_URL "
            "and apply migrations.",
            file=sys.stderr,
        )
        return 2
    except NightwatchError as error:
        print(f"Metadata refresh failed safely: {error}", file=sys.stderr)
        return 3

    action = "stored" if summary.created else "already stored"
    print(
        f"Metadata refresh {action}: status={summary.http_status} "
        f"capabilities={summary.capability_count} available={summary.available_count} "
        f"quota={summary.quota_remaining}/{summary.quota_limit} "
        f"rate_remaining={summary.rate_limit_remaining} retries={summary.retry_count} "
        f"request_id={summary.source_request_id}"
    )
    return 0


async def run_mag7_scan() -> int:
    settings = get_settings()
    try:
        with get_session_factory()() as session:
            async with NightwatchClient(
                base_url=str(settings.nightwatch_base_url),
                api_key=settings.nightwatch_api_key,
                timeout_seconds=settings.nightwatch_timeout_seconds,
                max_retries=0,
                max_concurrency=min(settings.nightwatch_max_concurrency, 4),
            ) as client:
                summary = await Mag7Scanner(session, client).execute(trigger="cli")
    except ConcurrentScanError as error:
        print(f"MAG7 scan not started: {error}", file=sys.stderr)
        return 4
    except (SQLAlchemyError, NightwatchError, RuntimeError) as error:
        print(f"MAG7 scan failed safely: {type(error).__name__}", file=sys.stderr)
        return 5
    print(
        f"MAG7 scan: scan_run_id={summary.scan_run_id} status={summary.status} "
        f"tickers={summary.tickers_scanned} deep_tickers={summary.deep_tickers} "
        f"deep_expiries={summary.expirations_deep_scanned} contracts={summary.contracts_analyzed} "
        f"clusters={summary.clusters_found} consumed_units={summary.consumed_quota_units} "
        f"network_attempts={summary.network_attempts} cache_hits={summary.cache_hits} "
        f"fresh_requests={summary.fresh_requests} elapsed_seconds={summary.elapsed_seconds}"
    )
    return 0


async def run_archive_mag7_oi() -> int:
    settings = get_settings()
    try:
        with get_session_factory()() as session:
            session.execute(text("SELECT 1"))
            async with NightwatchClient(
                base_url=str(settings.nightwatch_base_url),
                api_key=settings.nightwatch_api_key,
                timeout_seconds=settings.nightwatch_timeout_seconds,
                max_retries=0,
                max_concurrency=min(settings.nightwatch_max_concurrency, 4),
            ) as client:
                summary = await DailyOiArchiver(session, client).execute(trigger="cli")
    except ArchiveConcurrentError as error:
        print(f"Daily OI archive not started: {error}", file=sys.stderr)
        return 4
    except (SQLAlchemyError, NightwatchError, RuntimeError) as error:
        print(f"Daily OI archive failed safely: {type(error).__name__}", file=sys.stderr)
        return 5
    dates = ",".join(
        f"{ticker}:{value or 'unavailable'}"
        for ticker, value in sorted(summary.vendor_dates.items())
    )
    print(
        f"Daily OI archive: archive_run_id={summary.archive_run_id} status={summary.status} "
        f"vendor_dates={dates} tickers_attempted={summary.tickers_attempted} "
        f"tickers_skipped={summary.tickers_skipped} "
        f"expiries_attempted={summary.expiries_attempted} "
        f"complete_chains={summary.complete_chains} incomplete_chains={summary.incomplete_chains} "
        f"contracts_persisted={summary.contracts_persisted} "
        f"consumed_units={summary.consumed_quota_units} network_attempts={summary.network_attempts}"
    )
    return 0


async def run_archive_mag7_daily() -> int:
    settings = get_settings()
    try:
        with get_session_factory()() as session:
            session.execute(text("SELECT 1"))
            async with NightwatchClient(
                base_url=str(settings.nightwatch_base_url),
                api_key=settings.nightwatch_api_key,
                timeout_seconds=settings.nightwatch_timeout_seconds,
                max_retries=0,
                max_concurrency=min(settings.nightwatch_max_concurrency, 4),
            ) as client:
                summary = await DailyDataPipeline(session, client).execute(trigger="cli")
    except DailyCollectionConcurrentError as error:
        print(f"Daily MAG7 collection not started: {error}", file=sys.stderr)
        return 4
    except (SQLAlchemyError, NightwatchError, RuntimeError) as error:
        print(f"Daily MAG7 collection failed safely: {type(error).__name__}", file=sys.stderr)
        return 5
    subjobs = ",".join(
        f"{name}:{details['status']}" for name, details in sorted(summary.subjobs.items())
    )
    print(
        f"Daily MAG7 collection: daily_run_id={summary.daily_run_id} "
        f"status={summary.status} subjobs={subjobs} "
        f"consumed_units={summary.consumed_quota_units} "
        f"network_attempts={summary.network_attempts} "
        f"elapsed_seconds={summary.elapsed_seconds}"
    )
    return 0


async def run_backfill_mag7_radar() -> int:
    settings = get_settings()
    try:
        with get_session_factory()() as session:
            session.execute(text("SELECT 1"))
            async with NightwatchClient(
                base_url=str(settings.nightwatch_base_url),
                api_key=settings.nightwatch_api_key,
                timeout_seconds=settings.nightwatch_timeout_seconds,
                max_retries=0,
                max_concurrency=min(settings.nightwatch_max_concurrency, 4),
            ) as client:
                summary = await DailyRadarBackfill(session, client).execute(trigger="cli")
    except DailyCollectionConcurrentError as error:
        print(f"Radar backfill not started: {error}", file=sys.stderr)
        return 4
    except (SQLAlchemyError, NightwatchError, RuntimeError) as error:
        print(f"Radar backfill failed safely: {type(error).__name__}", file=sys.stderr)
        return 5
    radar = summary.subjobs["radar"]
    print(
        f"Radar backfill: daily_run_id={summary.daily_run_id} status={summary.status} "
        f"tickers_attempted={radar['tickers_attempted']} "
        f"tickers_skipped={radar['tickers_skipped']} rows_persisted={radar['rows_persisted']} "
        f"consumed_units={summary.consumed_quota_units} "
        f"network_attempts={summary.network_attempts}"
    )
    return 0


async def run_phase2b_context(
    contracts: list[str], *, force: bool, reuse_latest_raw: bool
) -> int:
    settings = get_settings()
    collector = ApiUsageCollector()
    try:
        with get_session_factory()() as session:
            session.execute(text("SELECT 1"))
            async with NightwatchClient(
                base_url=str(settings.nightwatch_base_url),
                api_key=settings.nightwatch_api_key,
                timeout_seconds=settings.nightwatch_timeout_seconds,
                max_retries=0,
                max_concurrency=1,
                usage_observer=collector,
            ) as client:
                summary = await Phase2bContextService(session, client).refresh_contracts(
                    contracts, force=force, reuse_latest_raw=reuse_latest_raw
                )
            for event in collector.events:
                persist_api_usage(session, event)
            session.commit()
    except (SQLAlchemyError, NightwatchError, RuntimeError) as error:
        print(f"Phase 2B context refresh failed safely: {type(error).__name__}", file=sys.stderr)
        return 5
    consumed = sum(event.consumed_quota is True for event in collector.events)
    attempts = sum(event.attempt_count for event in collector.events)
    remaining = next(
        (event.quota_remaining for event in reversed(collector.events)
         if event.quota_remaining is not None), None,
    )
    print(
        f"Phase 2B context: evaluations={len(summary.evaluations)} "
        f"ticker_snapshots_created={summary.ticker_snapshots_created} "
        f"ticker_snapshots_reused={summary.ticker_snapshots_reused} "
        f"ticker_snapshots_reprocessed={summary.ticker_snapshots_reprocessed} "
        f"paid_units={consumed} network_attempts={attempts} quota_remaining={remaining}"
    )
    return 0


def run_phase2b_v2_states(contracts: list[str]) -> int:
    try:
        with get_session_factory()() as session:
            session.execute(text("SELECT 1"))
            summary = Phase2bV2StateService(session).materialize_contracts(contracts)
    except (SQLAlchemyError, RuntimeError) as error:
        print(f"Phase 2B v2 state build failed safely: {type(error).__name__}", file=sys.stderr)
        return 5
    print(
        f"Phase 2B v2 states: created={summary.created} reused={summary.reused} "
        f"missing={len(summary.missing)} network_attempts=0 paid_units=0"
    )
    return 0 if not summary.missing else 4


def main() -> int:
    args = build_parser().parse_args()
    if args.command == "refresh-metadata":
        return asyncio.run(run_refresh_metadata())
    if args.command == "run-mag7-scan":
        return asyncio.run(run_mag7_scan())
    if args.command == "archive-mag7-oi":
        return asyncio.run(run_archive_mag7_oi())
    if args.command == "archive-mag7-daily":
        return asyncio.run(run_archive_mag7_daily())
    if args.command == "backfill-mag7-radar":
        return asyncio.run(run_backfill_mag7_radar())
    if args.command == "refresh-phase2b-context":
        return asyncio.run(
            run_phase2b_context(
                args.contract,
                force=args.force,
                reuse_latest_raw=args.reuse_latest_raw,
            )
        )
    if args.command == "build-phase2b-v2-states":
        return run_phase2b_v2_states(args.contract)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
