from __future__ import annotations

"""Definitions for profile fields that are derived from a stored answer.

Rules should reference the meaning they need (for example ``age_60_plus``),
while the questionnaire stores the smallest reusable fact (``age``). Keeping
both the dependency and derivation here gives the rule engine, question
planner, and config validator one shared source of truth.
"""

from dataclasses import dataclass
from typing import Any, Callable


@dataclass(frozen=True)
class DerivedField:
    source_question: str
    resolver: Callable[[Any], Any | None]


def _age_60_plus(age: Any) -> bool | None:
    return None if age is None else int(age) >= 60


def _no_fixed_address(status: Any) -> bool | None:
    if status is None:
        return None
    return str(status) in {"unsheltered", "sheltered", "temporary", "no_fixed_address"}


def _county_from_zip(zip_code: Any) -> str | None:
    value = str(zip_code or "")
    if not value:
        return None
    # Demo-only heuristic. A production pilot should replace this resolver with
    # an authoritative ZIP/county data adapter without changing program rules.
    return "San Diego" if value.startswith(("919", "920", "921")) else "Other"


DERIVED_FIELDS: dict[str, DerivedField] = {
    "age_60_plus": DerivedField("age", _age_60_plus),
    "no_fixed_address": DerivedField("housing_status", _no_fixed_address),
    "county_residence": DerivedField("zip_code", _county_from_zip),
}


def question_field_for(field_name: str) -> str:
    """Return the stored question ID that supplies a raw or derived rule field."""
    derived = DERIVED_FIELDS.get(field_name)
    return derived.source_question if derived else field_name


def derived_value(field_name: str, value_for: Callable[[str], Any | None]) -> Any | None:
    """Calculate a derived rule value using the profile's ordinary value getter."""
    derived = DERIVED_FIELDS.get(field_name)
    if derived is None:
        return None
    return derived.resolver(value_for(derived.source_question))
