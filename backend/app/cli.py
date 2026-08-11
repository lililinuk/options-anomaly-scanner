import argparse
import asyncio
import sys

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.config import get_settings
from app.db.session import get_session_factory
from app.metadata.service import ApiUsageCollector, refresh_metadata
from app.nightwatch.client import NightwatchClient
from app.nightwatch.errors import NightwatchError
from app.persistence.metadata import MetadataRepository
from app.scanner.service import ConcurrentScanError, Mag7Scanner


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Options Anomaly Scanner developer commands")
    subcommands = parser.add_subparsers(dest="command", required=True)
    subcommands.add_parser(
        "refresh-metadata",
        help="Fetch /v1/discover, persist it, and verify database read-back",
    )
    subcommands.add_parser(
        "run-mag7-scan",
        help="Run one budget-bounded manual Phase 2A MAG7 positioning scan",
    )
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


def main() -> int:
    args = build_parser().parse_args()
    if args.command == "refresh-metadata":
        return asyncio.run(run_refresh_metadata())
    if args.command == "run-mag7-scan":
        return asyncio.run(run_mag7_scan())
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
