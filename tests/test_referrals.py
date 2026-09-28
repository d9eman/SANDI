from __future__ import annotations

import pytest

from app.bootstrap import build_container
from app.domain.enums import AnswerState, ReferralState
from app.domain.referrals import InvalidTransition


def test_closed_loop_referral_transitions(settings):
    app = build_container(settings)
    profile, _ = app.profiles.create_guest("en")
    app.profiles.save_answer(profile.profile_id, "zip_code", AnswerState.KNOWN, "92101")
    # The production catalog keeps direct referrals disabled until a provider agrees.
    # This test explicitly simulates that agreement before exercising the state machine.
    with app.database.transaction() as connection:
        connection.execute("UPDATE services SET referral_enabled=1 WHERE id=?", ("svc_211_food_navigation",))
    ticket = app.referrals.create_food_referral(profile.profile_id, "today", "92101", "prov_211_sd", "svc_211_food_navigation", True)
    assert ticket.state == ReferralState.OFFERED
    ticket = app.referrals.transition(ticket.ticket_id, ReferralState.ACCEPTED, "provider", "provider")
    ticket = app.referrals.transition(ticket.ticket_id, ReferralState.SCHEDULED, "provider", "provider", scheduled_for="2026-08-01T10:00")
    ticket = app.referrals.transition(ticket.ticket_id, ReferralState.DELIVERED, "provider", "provider")
    ticket = app.referrals.transition(ticket.ticket_id, ReferralState.USER_CONFIRMED, "user", profile.profile_id)
    ticket = app.referrals.transition(ticket.ticket_id, ReferralState.CLOSED, "provider", "provider", outcome="food_received")
    assert ticket.state == ReferralState.CLOSED


def test_invalid_transition_is_rejected(settings):
    app = build_container(settings)
    profile, _ = app.profiles.create_guest("en")
    ticket = app.referrals.create_food_referral(profile.profile_id, "today", None, None, None, True)
    with pytest.raises(InvalidTransition):
        app.referrals.transition(ticket.ticket_id, ReferralState.DELIVERED, "provider", "provider")
