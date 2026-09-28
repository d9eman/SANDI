from __future__ import annotations

from typing import Any, Iterable
from urllib.parse import urlencode

from app.domain.enums import (
    MAINTENANCE_STATUSES,
    NON_MATCH_STATUSES,
    POSSIBLE_MATCH_STATUSES,
    STRONG_MATCH_STATUSES,
)


RESULT_GROUP_ORDER = ("best", "possible", "updating", "other")


def group_assessments(assessments: Iterable[Any]) -> dict[str, list[Any]]:
    """Create user-facing result groups without changing eligibility decisions.

    Rule freshness is a system state, not a user mismatch, so rules that need
    review are kept in their own group instead of being shown under "not a
    match." Direct food remains a separate shortcut outside benefit results.
    """
    groups: dict[str, list[Any]] = {name: [] for name in RESULT_GROUP_ORDER}
    for assessment in assessments:
        if assessment.program_id == "direct_food":
            continue
        if assessment.status in STRONG_MATCH_STATUSES:
            groups["best"].append(assessment)
        elif assessment.status in POSSIBLE_MATCH_STATUSES:
            groups["possible"].append(assessment)
        elif assessment.status in MAINTENANCE_STATUSES:
            groups["updating"].append(assessment)
        elif assessment.status in NON_MATCH_STATUSES:
            groups["other"].append(assessment)
        else:
            groups["other"].append(assessment)
    return groups


def resolve_actions(resource_service: Any, assessments: Iterable[Any], zip_code: str = "") -> dict[str, list[dict[str, Any]]]:
    """Resolve rule-configured service IDs to safe, trackable public links."""
    output: dict[str, list[dict[str, Any]]] = {}
    for assessment in assessments:
        actions: list[dict[str, Any]] = []
        for configured in assessment.actions:
            action = dict(configured)
            service_id = str(action.get("service_id") or "")
            if service_id:
                service = resource_service.public_service(service_id)
                if service is None:
                    continue
                query = urlencode({"location": zip_code}) if zip_code else ""
                action.update(
                    {
                        "href": f"/go/{service_id}" + (f"?{query}" if query else ""),
                        "external": True,
                        "provider_name": service.get("provider_name", ""),
                        "service_name": service.get("service_name", ""),
                    }
                )
            elif action.get("url"):
                action.update({"href": str(action["url"]), "external": True})
            else:
                continue
            actions.append(action)
        output[assessment.program_id] = actions
    return output
