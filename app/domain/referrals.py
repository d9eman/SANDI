from __future__ import annotations

from .enums import ReferralState


class InvalidTransition(ValueError):
    pass


class ReferralStateMachine:
    """Validates the closed-loop referral lifecycle."""

    _allowed: dict[ReferralState, set[ReferralState]] = {
        ReferralState.DRAFT: {ReferralState.OPEN, ReferralState.CANCELLED},
        ReferralState.OPEN: {ReferralState.OFFERED, ReferralState.CANCELLED, ReferralState.EXPIRED},
        ReferralState.OFFERED: {
            ReferralState.ACCEPTED,
            ReferralState.WAITLISTED,
            ReferralState.DECLINED,
            ReferralState.EXPIRED,
            ReferralState.CANCELLED,
        },
        ReferralState.ACCEPTED: {
            ReferralState.SCHEDULED,
            ReferralState.DELIVERED,
            ReferralState.CANCELLED,
        },
        ReferralState.SCHEDULED: {ReferralState.DELIVERED, ReferralState.CANCELLED},
        ReferralState.DELIVERED: {ReferralState.USER_CONFIRMED, ReferralState.CLOSED},
        ReferralState.USER_CONFIRMED: {ReferralState.CLOSED},
        ReferralState.WAITLISTED: {ReferralState.OFFERED, ReferralState.CANCELLED, ReferralState.EXPIRED},
        ReferralState.DECLINED: {ReferralState.OFFERED, ReferralState.CLOSED},
        ReferralState.EXPIRED: {ReferralState.OFFERED, ReferralState.CLOSED},
        ReferralState.CANCELLED: set(),
        ReferralState.CLOSED: set(),
    }

    def allowed_targets(self, current: ReferralState) -> tuple[ReferralState, ...]:
        return tuple(sorted(self._allowed[current], key=lambda state: state.value))

    def validate(self, current: ReferralState, target: ReferralState) -> None:
        if target not in self._allowed[current]:
            raise InvalidTransition(f"Cannot move referral from {current.value} to {target.value}.")
