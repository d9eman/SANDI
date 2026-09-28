from __future__ import annotations

from typing import Any


def service_quality(record: dict[str, Any]) -> dict[str, Any]:
    """Score provider data completeness—not case volume or client outcomes.

    This is intentionally a data-quality game mechanic. It rewards providers for
    maintaining information that prevents failed trips and bad referrals. It must
    never be used as a public provider ranking or a worker-performance score.
    """
    checks: list[tuple[str, int, bool]] = [
        ("Official source", 15, bool(str(record.get("source_url") or "").strip())),
        ("Recently verified", 15, bool(str(record.get("last_verified_at") or "").strip())),
        (
            "Contact route",
            10,
            bool(str(record.get("phone") or "").strip() or str(record.get("website") or "").strip()),
        ),
        ("Clear service description", 10, bool(str(record.get("service_description") or "").strip())),
        ("Current hours", 10, bool(str(record.get("hours_text") or "").strip())),
        ("Eligibility/intake notes", 10, bool(str(record.get("eligibility_summary") or "").strip())),
        ("Languages", 5, bool(str(record.get("languages") or "").strip())),
        ("Accessibility", 5, bool(str(record.get("accessibility") or "").strip())),
        (
            "Availability status",
            10,
            str(record.get("availability_status") or "UNKNOWN").upper() not in {"", "UNKNOWN"},
        ),
    ]
    direct = str(record.get("service_mode") or "") == "direct_service"
    location_ready = bool(
        (str(record.get("address") or "").strip() and str(record.get("zip_code") or "").strip())
        or (record.get("latitude") is not None and record.get("longitude") is not None)
    )
    checks.append(("Mappable service location", 10, location_ready if direct else True))

    score = sum(points for _, points, passed in checks if passed)
    missing = [label for label, _, passed in checks if not passed]
    if score >= 85:
        label = "Ready to share"
    elif score >= 65:
        label = "Almost ready"
    else:
        label = "Needs details"
    return {"score": min(score, 100), "label": label, "missing": missing}
