from __future__ import annotations

import csv
import io
import math
import re
from typing import Any
from urllib.parse import urlparse

from app.ports.repositories import AuditRepository, ResourceRepository


class ResourceService:
    """Application service for public resources, provider data, and usage feedback."""

    @staticmethod
    def extract_zip(location_text: str) -> str:
        match = re.search(r"(?<!\d)(\d{5})(?!\d)", (location_text or "").strip())
        return match.group(1) if match else ""

    @classmethod
    def _coarse_location(cls, location_text: str) -> tuple[str, str]:
        """Retain only a five-digit ZIP for analytics; discard addresses/coordinates."""
        value = (location_text or "").strip()
        if not value:
            return "", "none"
        zip_code = cls.extract_zip(value)
        if zip_code:
            return zip_code, "zip"
        return "", "other_not_retained"

    @staticmethod
    def _distance_miles(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        radius = 3958.8
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)
        a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
        return radius * (2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)))

    def __init__(self, resources: ResourceRepository, audit: AuditRepository):
        self.resources = resources
        self.audit = audit

    def find_food(
        self,
        actor_id: str,
        zip_code: str | None,
        journey_stage: str | None = None,
        profile_id: str | None = None,
        latitude: float | None = None,
        longitude: float | None = None,
        direct_site_radius_miles: float = 15.0,
    ) -> list[dict[str, Any]]:
        normalized_zip = self.extract_zip(zip_code or "")
        matches = self.resources.search_food(normalized_zip or None, journey_stage=journey_stage, limit=500)

        # Locator tools and public guides remain countywide. Direct sites are
        # intentionally local: when coordinates are available, show at most five
        # sites inside the closest useful radius (1 mile first, then 5, then 15).
        # This keeps the page short while making the nearest options feel useful.
        non_direct: list[dict[str, Any]] = []
        direct_candidates: list[dict[str, Any]] = []
        for item in matches:
            if item.get("service_mode") != "direct_service":
                non_direct.append(item)
                continue
            if latitude is not None and longitude is not None and item.get("latitude") is not None and item.get("longitude") is not None:
                distance = self._distance_miles(latitude, longitude, float(item["latitude"]), float(item["longitude"]))
                item["distance_miles"] = round(distance, 1)
                item["_distance_raw"] = distance
                direct_candidates.append(item)
            elif normalized_zip and str(item.get("zip_code") or "") == normalized_zip:
                direct_candidates.append(item)

        if latitude is not None and longitude is not None:
            selected_radius = direct_site_radius_miles
            for radius in (1.0, 5.0, direct_site_radius_miles):
                if any(float(item.get("_distance_raw", 999999)) <= radius for item in direct_candidates):
                    selected_radius = radius
                    break
            direct_candidates = [
                item for item in direct_candidates if float(item.get("_distance_raw", 999999)) <= selected_radius
            ]
            direct_candidates.sort(key=lambda item: float(item.get("_distance_raw", 999999)))
            direct_candidates = direct_candidates[:5]
            for item in direct_candidates:
                item.pop("_distance_raw", None)
                item["search_radius_miles"] = selected_radius
        else:
            direct_candidates = direct_candidates[:5]

        filtered = non_direct + direct_candidates

        self.audit.record(
            "user" if profile_id else "visitor",
            profile_id or actor_id,
            "search",
            "food_resources",
            journey_stage or "all",
            "immediate food routing",
            "success",
            {
                "result_count": len(filtered),
                "location_supplied": bool(zip_code or latitude is not None),
                "coordinates_used_ephemerally": latitude is not None and longitude is not None,
            },
        )
        coarse_location, location_kind = self._coarse_location(zip_code or "")
        self.resources.record_interaction(
            visitor_id=actor_id,
            profile_id=profile_id,
            service_id=None,
            action="search",
            location_text=coarse_location,
            metadata={
                "journey_stage": journey_stage or "all",
                "result_count": len(filtered),
                "location_kind": location_kind,
                "coordinates_used_ephemerally": latitude is not None and longitude is not None,
            },
        )
        return filtered

    def public_service(self, service_id: str) -> dict[str, Any] | None:
        return self.resources.get_public_service(service_id)

    def record_open(
        self,
        visitor_id: str,
        profile_id: str | None,
        service_id: str,
        location_text: str = "",
    ) -> str:
        item = self.resources.get_public_service(service_id)
        if item is None:
            raise KeyError(service_id)
        target = str(item.get("website") or item.get("source_url") or "").strip()
        parsed = urlparse(target)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("This resource does not have a safe public link.")
        coarse_location, location_kind = self._coarse_location(location_text)
        self.resources.record_interaction(
            visitor_id=visitor_id,
            profile_id=profile_id,
            service_id=service_id,
            action="open",
            location_text=coarse_location,
            metadata={
                "provider_id": item["provider_id"],
                "journey_stage": item["journey_stage"],
                "location_kind": location_kind,
            },
        )
        self.audit.record(
            "user" if profile_id else "visitor",
            profile_id or visitor_id,
            "open",
            "service",
            service_id,
            "resource handoff",
            "success",
            {"provider_id": item["provider_id"], "journey_stage": item["journey_stage"]},
        )
        return target

    def record_feedback(
        self,
        visitor_id: str,
        profile_id: str | None,
        service_id: str,
        outcome: str,
        location_text: str = "",
        note: str = "",
    ) -> None:
        if outcome not in {"yes", "no", "not_yet"}:
            raise ValueError("Feedback outcome is not supported.")
        if self.resources.get_public_service(service_id) is None:
            raise KeyError(service_id)
        coarse_location, location_kind = self._coarse_location(location_text)
        self.resources.record_interaction(
            visitor_id=visitor_id,
            profile_id=profile_id,
            service_id=service_id,
            action="feedback",
            location_text=coarse_location,
            outcome=outcome,
            metadata={"note": note[:500], "location_kind": location_kind},
        )
        self.audit.record(
            "user" if profile_id else "visitor",
            profile_id or visitor_id,
            "feedback",
            "service",
            service_id,
            "resource outcome feedback",
            "success",
            {"outcome": outcome},
        )

    def import_csv(self, content: bytes, actor_id: str) -> tuple[int, list[str]]:
        decoded = content.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(decoded))
        required = {"provider_name", "service_name", "zip_code"}
        if not reader.fieldnames or not required.issubset(set(reader.fieldnames)):
            missing = sorted(required - set(reader.fieldnames or []))
            raise ValueError(f"CSV is missing required columns: {', '.join(missing)}")
        count = 0
        ids: list[str] = []
        for row in reader:
            if not any((value or "").strip() for value in row.values()):
                continue
            self.resources.upsert_provider_record(row)
            count += 1
            ids.append(row.get("provider_id") or row.get("provider_name") or "provider")
        self.audit.record(
            "provider",
            actor_id,
            "import",
            "provider_catalog",
            "csv",
            "provider data update",
            "success",
            {"rows": count},
        )
        return count, ids

    def add_provider_record(self, record: dict[str, Any], actor_id: str) -> None:
        self.resources.upsert_provider_record(record)
        self.audit.record(
            "provider",
            actor_id,
            "upsert",
            "provider",
            record.get("provider_id", record.get("provider_name", "new")),
            "provider data update",
            "success",
        )

    def update_availability(
        self,
        service_id: str,
        status: str,
        visibility: str,
        details: str,
        actor_id: str,
    ) -> None:
        if self.resources.get_service_identity(service_id) is None:
            raise KeyError(service_id)
        self.resources.add_availability(service_id, status, visibility, details, "provider_portal")
        self.audit.record(
            "provider",
            actor_id,
            "update_availability",
            "service",
            service_id,
            "current resource availability",
            "success",
            {"status": status, "visibility": visibility},
        )
