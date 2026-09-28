from __future__ import annotations

import json
import uuid
from typing import Any

from app.db import Database
from app.ports.repositories import ResourceRepository

from .common import utcnow


class SqliteResourceRepository(ResourceRepository):
    """SQLite implementation for provider, service, location, and interaction data."""

    def __init__(self, database: Database):
        self.database = database

    @staticmethod
    def _public_resource_query() -> str:
        return """
            SELECT
                p.id AS provider_id,
                p.name AS provider_name,
                p.legal_name,
                p.description AS provider_description,
                p.website,
                p.phone,
                p.source_type,
                p.source_url,
                p.data_quality_status,
                p.last_verified_at,
                p.organization_type,
                p.partner_status,
                s.id AS service_id,
                s.name AS service_name,
                s.service_type,
                s.service_category,
                s.service_mode,
                s.journey_stage,
                s.public_visibility AS service_public_visibility,
                s.description AS service_description,
                s.eligibility_summary,
                s.eligibility_group,
                s.documentation_notes,
                s.call_first,
                s.referral_enabled,
                l.id AS location_id,
                l.name AS location_name,
                l.address,
                l.city,
                l.state,
                l.zip_code,
                l.hours_text,
                l.service_area,
                l.languages,
                l.accessibility,
                l.schedule_exceptions,
                l.transport_notes,
                l.latitude,
                l.longitude,
                COALESCE(a.status, 'UNKNOWN') AS availability_status,
                COALESCE(a.visibility, 'PUBLIC') AS availability_visibility,
                COALESCE(a.details, '') AS availability_details,
                a.observed_at AS availability_observed_at
            FROM providers p
            JOIN services s ON s.provider_id = p.id
            JOIN service_locations l ON l.service_id = s.id
            LEFT JOIN availability_snapshots a ON a.id = (
                SELECT a2.id
                FROM availability_snapshots a2
                WHERE a2.service_id = s.id
                ORDER BY a2.observed_at DESC, a2.id DESC
                LIMIT 1
            )
        """

    @staticmethod
    def _apply_availability_visibility(item: dict[str, Any]) -> dict[str, Any]:
        if item["availability_visibility"] != "PUBLIC":
            item["availability_status"] = "CALL_TO_VERIFY"
            item["availability_details"] = (
                "Detailed availability is restricted to authorized coordinators."
            )
        return item

    def search_food(
        self,
        zip_code: str | None,
        journey_stage: str | None = None,
        limit: int = 30,
    ) -> list[dict[str, Any]]:
        query = self._public_resource_query() + """
            WHERE p.public_visibility = 'PUBLIC'
              AND s.public_visibility = 'PUBLIC'
              AND s.service_type IN (
                  'food',
                  'food_locator',
                  'food_navigation',
                  'benefits_application'
              )
              AND (? IS NULL OR s.journey_stage = ?)
            ORDER BY
              CASE WHEN l.zip_code = ? THEN 0 WHEN l.zip_code = '' THEN 1 ELSE 2 END,
              p.name,
              s.name
            LIMIT ?
        """
        with self.database.connect() as connection:
            rows = connection.execute(
                query,
                (journey_stage, journey_stage, zip_code or "", limit),
            ).fetchall()
        return [self._apply_availability_visibility(dict(row)) for row in rows]

    def get_public_service(self, service_id: str) -> dict[str, Any] | None:
        query = self._public_resource_query() + """
            WHERE p.public_visibility = 'PUBLIC' AND s.public_visibility = 'PUBLIC' AND s.id = ?
            LIMIT 1
        """
        with self.database.connect() as connection:
            row = connection.execute(query, (service_id,)).fetchone()
        if row is None:
            return None
        return self._apply_availability_visibility(dict(row))

    def get_service_identity(self, service_id: str) -> dict[str, Any] | None:
        """Return minimal service ownership/referral metadata regardless of public visibility."""
        with self.database.connect() as connection:
            row = connection.execute(
                """
                SELECT s.id AS service_id, s.provider_id, s.referral_enabled, s.public_visibility
                FROM services s
                WHERE s.id = ?
                LIMIT 1
                """,
                (service_id,),
            ).fetchone()
        return dict(row) if row is not None else None

    def list_providers(self) -> list[dict[str, Any]]:
        with self.database.connect() as connection:
            rows = connection.execute(
                """
                SELECT
                    p.*,
                    s.id AS service_id,
                    s.name AS service_name,
                    s.service_type,
                    s.service_category,
                    s.service_mode,
                    s.journey_stage,
                    s.public_visibility AS service_public_visibility,
                    s.description AS service_description,
                    s.eligibility_summary,
                    s.documentation_notes,
                    s.eligibility_group,
                    s.referral_enabled,
                    l.name AS location_name,
                    l.address,
                    l.city,
                    l.state,
                    l.zip_code,
                    l.hours_text,
                    l.service_area,
                    l.languages,
                    l.accessibility,
                    l.schedule_exceptions,
                    l.transport_notes,
                    l.latitude,
                    l.longitude,
                    COALESCE(a.status, 'UNKNOWN') AS availability_status,
                    COALESCE(a.visibility, 'PUBLIC') AS availability_visibility,
                    COALESCE(a.details, '') AS availability_details,
                    a.observed_at AS availability_observed_at
                FROM providers p
                LEFT JOIN services s ON s.provider_id = p.id
                LEFT JOIN service_locations l ON l.service_id = s.id
                LEFT JOIN availability_snapshots a ON a.id = (
                    SELECT a2.id
                    FROM availability_snapshots a2
                    WHERE a2.service_id = s.id
                    ORDER BY a2.observed_at DESC, a2.id DESC
                    LIMIT 1
                )
                ORDER BY p.name, s.name
                """
            ).fetchall()
        return [dict(row) for row in rows]

    @staticmethod
    def _as_bool(value: Any, default: bool = False) -> int:
        if value is None or value == "":
            return 1 if default else 0
        return 1 if str(value).lower() in {"1", "true", "yes", "y"} else 0

    @staticmethod
    def _as_float(value: Any) -> float | None:
        if value in (None, ""):
            return None
        return float(value)

    def upsert_provider_record(self, record: dict[str, Any]) -> None:
        now = utcnow()
        provider_id = record.get("provider_id") or f"prov_{uuid.uuid4().hex[:10]}"
        service_id = record.get("service_id") or f"svc_{uuid.uuid4().hex[:10]}"
        location_id = record.get("location_id") or f"loc_{uuid.uuid4().hex[:10]}"
        referral_enabled = self._as_bool(record.get("referral_enabled"), default=True)
        call_first = self._as_bool(record.get("call_first"), default=False)

        with self.database.transaction() as connection:
            connection.execute(
                """
                INSERT INTO providers(
                    id, name, legal_name, description, website, phone,
                    source_type, source_url, data_quality_status,
                    last_verified_at, public_visibility, organization_type,
                    partner_status, created_at, updated_at
                )
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(id) DO UPDATE SET
                    name=excluded.name,
                    legal_name=excluded.legal_name,
                    description=excluded.description,
                    website=excluded.website,
                    phone=excluded.phone,
                    source_type=excluded.source_type,
                    source_url=excluded.source_url,
                    data_quality_status=excluded.data_quality_status,
                    last_verified_at=excluded.last_verified_at,
                    public_visibility=excluded.public_visibility,
                    organization_type=excluded.organization_type,
                    partner_status=excluded.partner_status,
                    updated_at=excluded.updated_at
                """,
                (
                    provider_id,
                    record.get("provider_name", "Unnamed provider"),
                    record.get("legal_name", ""),
                    record.get("provider_description", ""),
                    record.get("website", ""),
                    record.get("phone", ""),
                    record.get("source_type", "manual"),
                    record.get("source_url", ""),
                    record.get("data_quality_status", "under_review"),
                    record.get("last_verified_at") or now,
                    record.get("public_visibility", "PUBLIC"),
                    record.get("organization_type", "community_provider"),
                    record.get("partner_status", "not_contacted"),
                    now,
                    now,
                ),
            )
            connection.execute(
                """
                INSERT INTO services(
                    id, provider_id, name, service_type, service_category,
                    service_mode, journey_stage, public_visibility, description,
                    eligibility_summary, eligibility_group,
                    documentation_notes, call_first, referral_enabled,
                    created_at, updated_at
                )
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(id) DO UPDATE SET
                    provider_id=excluded.provider_id,
                    name=excluded.name,
                    service_type=excluded.service_type,
                    service_category=excluded.service_category,
                    service_mode=excluded.service_mode,
                    journey_stage=excluded.journey_stage,
                    public_visibility=excluded.public_visibility,
                    description=excluded.description,
                    eligibility_summary=excluded.eligibility_summary,
                    eligibility_group=excluded.eligibility_group,
                    documentation_notes=excluded.documentation_notes,
                    call_first=excluded.call_first,
                    referral_enabled=excluded.referral_enabled,
                    updated_at=excluded.updated_at
                """,
                (
                    service_id,
                    provider_id,
                    record.get("service_name", "Food service"),
                    record.get("service_type", "food"),
                    record.get("service_category", "food"),
                    record.get("service_mode", "direct_service"),
                    record.get("journey_stage", "direct_help"),
                    record.get("service_public_visibility", record.get("public_visibility", "PUBLIC")),
                    record.get("service_description", ""),
                    record.get("eligibility_summary", ""),
                    record.get("eligibility_group", ""),
                    record.get("documentation_notes", ""),
                    call_first,
                    referral_enabled,
                    now,
                    now,
                ),
            )
            connection.execute(
                """
                INSERT INTO service_locations(
                    id, service_id, name, address, city, state, zip_code,
                    hours_text, service_area, languages, accessibility,
                    schedule_exceptions, transport_notes, latitude, longitude,
                    created_at, updated_at
                )
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(id) DO UPDATE SET
                    service_id=excluded.service_id,
                    name=excluded.name,
                    address=excluded.address,
                    city=excluded.city,
                    state=excluded.state,
                    zip_code=excluded.zip_code,
                    hours_text=excluded.hours_text,
                    service_area=excluded.service_area,
                    languages=excluded.languages,
                    accessibility=excluded.accessibility,
                    schedule_exceptions=excluded.schedule_exceptions,
                    transport_notes=excluded.transport_notes,
                    latitude=excluded.latitude,
                    longitude=excluded.longitude,
                    updated_at=excluded.updated_at
                """,
                (
                    location_id,
                    service_id,
                    record.get("location_name")
                    or record.get("provider_name", "Service location"),
                    record.get("address", ""),
                    record.get("city", "San Diego"),
                    record.get("state", "CA"),
                    record.get("zip_code", ""),
                    record.get("hours_text", "Call or open source to verify"),
                    record.get("service_area", "San Diego County"),
                    record.get("languages", ""),
                    record.get("accessibility", ""),
                    record.get("schedule_exceptions", ""),
                    record.get("transport_notes", ""),
                    self._as_float(record.get("latitude")),
                    self._as_float(record.get("longitude")),
                    now,
                    now,
                ),
            )

            requested_status = record.get("availability_status")
            if requested_status:
                latest = connection.execute(
                    """
                    SELECT status, visibility, details, source, observed_at
                    FROM availability_snapshots
                    WHERE service_id=?
                    ORDER BY observed_at DESC, id DESC
                    LIMIT 1
                    """,
                    (service_id,),
                ).fetchone()
                candidate = (
                    requested_status,
                    record.get("availability_visibility", "PUBLIC"),
                    record.get("availability_details", ""),
                    record.get("source_type", "manual"),
                    record.get("last_verified_at") or now,
                )
                latest_tuple = (
                    latest["status"],
                    latest["visibility"],
                    latest["details"],
                    latest["source"],
                    latest["observed_at"],
                ) if latest else None
                if latest_tuple != candidate:
                    connection.execute(
                        """
                        INSERT INTO availability_snapshots(
                            service_id, status, visibility, details, source,
                            observed_at, expires_at
                        )
                        VALUES(?,?,?,?,?,?,?)
                        """,
                        (
                            service_id,
                            *candidate,
                            record.get("availability_expires_at"),
                        ),
                    )

    def add_availability(
        self,
        service_id: str,
        status: str,
        visibility: str,
        details: str,
        source: str,
    ) -> None:
        with self.database.transaction() as connection:
            connection.execute(
                """
                INSERT INTO availability_snapshots(
                    service_id, status, visibility, details, source, observed_at
                )
                VALUES(?,?,?,?,?,?)
                """,
                (service_id, status, visibility, details, source, utcnow()),
            )

    def record_interaction(
        self,
        visitor_id: str,
        profile_id: str | None,
        service_id: str | None,
        action: str,
        location_text: str = "",
        outcome: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> None:
        with self.database.transaction() as connection:
            # Local demo cookies and catalog records can outlive a reset database.
            # Interaction analytics must never take down the user-facing resource
            # finder because an optional foreign-key reference became stale.
            stored_profile_id = profile_id
            stored_service_id = service_id
            payload = dict(metadata or {})
            if stored_profile_id and connection.execute(
                "SELECT 1 FROM profiles WHERE id=?", (stored_profile_id,)
            ).fetchone() is None:
                stored_profile_id = None
                payload["stale_profile_reference_removed"] = True
            if stored_service_id and connection.execute(
                "SELECT 1 FROM services WHERE id=?", (stored_service_id,)
            ).fetchone() is None:
                stored_service_id = None
                payload["stale_service_reference_removed"] = True
            connection.execute(
                """
                INSERT INTO resource_interactions(
                    visitor_id, profile_id, service_id, action, location_text,
                    outcome, metadata_json, created_at
                )
                VALUES(?,?,?,?,?,?,?,?)
                """,
                (
                    visitor_id,
                    stored_profile_id,
                    stored_service_id,
                    action,
                    location_text,
                    outcome,
                    json.dumps(payload),
                    utcnow(),
                ),
            )
