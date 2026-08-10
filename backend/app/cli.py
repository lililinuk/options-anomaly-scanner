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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Options Anomaly Scanner developer commands")
    subcommands = parser.add_subparsers(dest="command", required=True)
    subcommands.add_parser(
        "refresh-metadata",
        help="Fetch /v1/discover, persist it, and verify database read-back",
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


def main() -> int:
    args = build_parser().parse_args()
    if args.command == "refresh-metadata":
        return asyncio.run(run_refresh_metadata())
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
