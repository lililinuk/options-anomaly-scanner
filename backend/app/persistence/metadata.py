from dataclasses import dataclass
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import CapabilitySnapshot, MetadataRefresh
from app.ingestion.raw import RawIngestor, parse_vendor_observed_at
from app.nightwatch.models import ApiUsageEvent, NightwatchResult
from app.normalization.capabilities import NormalizedCapability
from app.persistence.api_usage import persist_api_usage


@dataclass(frozen=True)
class PersistedMetadataSummary:
    source_request_id: str
    capability_count: int
    available_count: int
    observed_at: Any
    created: bool


class MetadataRepository:
    """Transactional persistence and verified read-back for metadata refreshes."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def persist_refresh(
        self,
        *,
        result: NightwatchResult,
        usage_event: ApiUsageEvent,
        capabilities: list[NormalizedCapability],
    ) -> PersistedMetadataSummary:
        source_request_id = result.vendor_request_id or result.request_id
        existing = self._get_refresh(source_request_id)
        if existing is not None:
            return self._readback(existing, created=False)

        if not isinstance(result.payload, (dict, list)):
            raise ValueError("Discover payload must be a JSON object or list")

        try:
            raw = RawIngestor(self._session).persist(
                endpoint="/v1/discover",
                request_id=source_request_id,
                vendor_request_id=result.vendor_request_id,
                payload=result.payload,
                vendor_observed_at=parse_vendor_observed_at(result.payload),
            )
            persist_api_usage(self._session, usage_event)
            refresh = MetadataRefresh(
                raw_payload_id=raw.id,
                observed_at=usage_event.requested_at,
                source_request_id=source_request_id,
                http_status=result.status_code,
                capability_count=len(capabilities),
            )
            self._session.add(refresh)
            self._session.flush()
            self._session.add_all(
                [
                    CapabilitySnapshot(
                        refresh_id=refresh.id,
                        observed_at=item.observed_at,
                        capability_identifier=item.capability_identifier,
                        available=item.available,
                        coverage=item.coverage,
                        weight=item.weight,
                        source_request_id=item.source_request_id,
                        source_metadata=item.source_metadata,
                    )
                    for item in capabilities
                ]
            )
            self._session.commit()
        except Exception:
            self._session.rollback()
            raise

        persisted = self._get_refresh(source_request_id)
        if persisted is None:
            raise RuntimeError("Metadata refresh read-back failed")
        return self._readback(persisted, created=True)

    def persist_usage_only(self, event: ApiUsageEvent) -> None:
        try:
            persist_api_usage(self._session, event)
            self._session.commit()
        except Exception:
            self._session.rollback()
            raise

    def _get_refresh(self, source_request_id: str) -> MetadataRefresh | None:
        return self._session.scalar(
            select(MetadataRefresh).where(
                MetadataRefresh.source_request_id == source_request_id
            )
        )

    def _readback(
        self, refresh: MetadataRefresh, *, created: bool
    ) -> PersistedMetadataSummary:
        capability_count = self._session.scalar(
            select(func.count(CapabilitySnapshot.id)).where(
                CapabilitySnapshot.refresh_id == refresh.id
            )
        )
        available_count = self._session.scalar(
            select(func.count(CapabilitySnapshot.id)).where(
                CapabilitySnapshot.refresh_id == refresh.id,
                CapabilitySnapshot.available.is_(True),
            )
        )
        actual_count = int(capability_count or 0)
        if actual_count != refresh.capability_count:
            raise RuntimeError(
                "Capability read-back count does not match the persisted refresh"
            )
        return PersistedMetadataSummary(
            source_request_id=refresh.source_request_id,
            capability_count=actual_count,
            available_count=int(available_count or 0),
            observed_at=refresh.observed_at,
            created=created,
        )
