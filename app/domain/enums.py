from __future__ import annotations

from enum import StrEnum


class AnswerState(StrEnum):
    KNOWN = "known"
    UNKNOWN = "unknown"
    SKIPPED = "skipped"


class EligibilityStatus(StrEnum):
    DIRECT_RESOURCE = "DIRECT_RESOURCE"
    LIKELY_ELIGIBLE = "LIKELY_ELIGIBLE"
    MAY_QUALIFY = "MAY_QUALIFY"
    NEEDS_INFORMATION = "NEEDS_INFORMATION"
    LIKELY_NOT_ELIGIBLE = "LIKELY_NOT_ELIGIBLE"
    RULE_UNDER_REVIEW = "RULE_UNDER_REVIEW"


class ReferralState(StrEnum):
    DRAFT = "DRAFT"
    OPEN = "OPEN"
    OFFERED = "OFFERED"
    ACCEPTED = "ACCEPTED"
    SCHEDULED = "SCHEDULED"
    DELIVERED = "DELIVERED"
    USER_CONFIRMED = "USER_CONFIRMED"
    CLOSED = "CLOSED"
    WAITLISTED = "WAITLISTED"
    DECLINED = "DECLINED"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"


class AvailabilityStatus(StrEnum):
    AVAILABLE = "AVAILABLE"
    LIMITED = "LIMITED"
    FULL = "FULL"
    CLOSED = "CLOSED"
    CALL_TO_VERIFY = "CALL_TO_VERIFY"
    UNKNOWN = "UNKNOWN"


class Visibility(StrEnum):
    PUBLIC = "PUBLIC"
    RESTRICTED = "RESTRICTED"
    NOT_SHARED = "NOT_SHARED"


class TriState(StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"
    UNKNOWN = "UNKNOWN"

# Shared eligibility semantics. Presentation and application services import
# these sets so "strong match", "possible", and "actionable" never drift.
STRONG_MATCH_STATUSES = frozenset({
    EligibilityStatus.DIRECT_RESOURCE,
    EligibilityStatus.LIKELY_ELIGIBLE,
})
POSSIBLE_MATCH_STATUSES = frozenset({
    EligibilityStatus.MAY_QUALIFY,
    EligibilityStatus.NEEDS_INFORMATION,
})
ACTIONABLE_STATUSES = frozenset({
    EligibilityStatus.DIRECT_RESOURCE,
    EligibilityStatus.LIKELY_ELIGIBLE,
    EligibilityStatus.MAY_QUALIFY,
})
NON_MATCH_STATUSES = frozenset({EligibilityStatus.LIKELY_NOT_ELIGIBLE})
MAINTENANCE_STATUSES = frozenset({EligibilityStatus.RULE_UNDER_REVIEW})
