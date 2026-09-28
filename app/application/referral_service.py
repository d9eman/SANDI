from __future__ import annotations

from typing import Any

from app.domain.enums import ReferralState
from app.domain.referrals import ReferralStateMachine
from app.ports.repositories import AuditRepository, ReferralRepository, ResourceRepository
from app.ports.services import NotificationService


class ReferralService:
    def __init__(
        self,
        referrals: ReferralRepository,
        resources: ResourceRepository,
        audit: AuditRepository,
        notifications: NotificationService,
    ):
        self.referrals = referrals
        self.resources = resources
        self.audit = audit
        self.notifications = notifications
        self.machine = ReferralStateMachine()

    def create_food_referral(
        self,
        profile_id: str,
        urgency: str,
        zip_code: str | None,
        provider_id: str | None,
        service_id: str | None,
        consent: bool,
    ):
        if not consent:
            raise ValueError("Consent is required before a referral summary is sent.")
        if service_id:
            service = self.resources.get_service_identity(service_id)
            if service is None:
                raise ValueError("That service is not available for referral.")
            if not bool(service.get("referral_enabled")):
                raise ValueError("That service has not enabled direct SANDI referrals.")
            if provider_id and provider_id != service.get("provider_id"):
                raise ValueError("The selected provider and service do not match.")
            provider_id = str(service["provider_id"])
        initial_state = ReferralState.OFFERED if provider_id else ReferralState.OPEN
        ticket = self.referrals.create(
            {
                "profile_id": profile_id,
                "provider_id": provider_id,
                "service_id": service_id,
                "need_type": "food",
                "urgency": urgency,
                "zip_code": zip_code,
                "state": initial_state.value,
                "consent_scope": "need type, urgency, ZIP/area, language/accessibility needs, and selected profile facts",
                "actor_type": "user",
                "actor_id": profile_id,
                "note": "User requested closed-loop food support.",
            }
        )
        self.audit.record("user", profile_id, "create", "referral_ticket", ticket.ticket_id, "food referral", "success", {"provider_id": provider_id})
        if provider_id:
            self.notifications.send("demo-log", provider_id, f"New SANDI food referral {ticket.ticket_id} is waiting for a response.")
        return ticket

    def transition(
        self,
        ticket_id: str,
        target: ReferralState,
        actor_type: str,
        actor_id: str,
        note: str = "",
        scheduled_for: str | None = None,
        outcome: str | None = None,
        decline_reason: str | None = None,
    ):
        ticket = self.referrals.get(ticket_id)
        if ticket is None:
            raise KeyError(ticket_id)
        self.machine.validate(ticket.state, target)
        updated = self.referrals.transition(
            ticket_id, target.value, actor_type, actor_id, note, scheduled_for, outcome, decline_reason
        )
        self.audit.record(actor_type, actor_id, "transition", "referral_ticket", ticket_id, "closed-loop referral management", "success", {"from": ticket.state.value, "to": target.value})
        self.notifications.send("demo-log", ticket.profile_id, f"Referral {ticket_id} changed to {target.value}.")
        return updated

    def allowed_targets(self, ticket_id: str):
        ticket = self.referrals.get(ticket_id)
        if ticket is None:
            raise KeyError(ticket_id)
        return self.machine.allowed_targets(ticket.state)
