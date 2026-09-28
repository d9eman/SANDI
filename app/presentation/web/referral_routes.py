from __future__ import annotations

from fastapi import APIRouter, Form, HTTPException, Request

from app.domain.enums import ReferralState
from app.security.web import authorize_profile, verify_csrf

from .public_context import container, redirect, render_page


router = APIRouter()


@router.post("/p/{profile_id}/referrals")
def create_referral(
    request: Request,
    profile_id: str,
    csrf: str = Form(...),
    provider_id: str = Form(""),
    service_id: str = Form(""),
    consent: str | None = Form(None),
):
    authorize_profile(request, profile_id)
    verify_csrf(request, csrf)
    app = container(request)
    profile = app.profiles.require(profile_id)
    try:
        ticket = app.referrals.create_food_referral(
            profile_id=profile_id,
            urgency=str(profile.value("urgency") or "planning"),
            zip_code=profile.value("zip_code"),
            provider_id=provider_id or None,
            service_id=service_id or None,
            consent=consent == "yes",
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    return redirect(f"/p/{profile_id}/referrals#{ticket.ticket_id}")


@router.get("/p/{profile_id}/referrals")
def referral_list(request: Request, profile_id: str):
    authorize_profile(request, profile_id)
    tickets = container(request).referral_repository.list_for_profile(profile_id)
    return render_page(request, "referrals.html", {"profile_id": profile_id, "tickets": tickets})


@router.post("/p/{profile_id}/referrals/{ticket_id}/confirm")
def confirm_referral(
    request: Request,
    profile_id: str,
    ticket_id: str,
    csrf: str = Form(...),
    received: str = Form(...),
    note: str = Form(""),
):
    authorize_profile(request, profile_id)
    verify_csrf(request, csrf)
    app = container(request)
    ticket = app.referral_repository.get(ticket_id)
    if ticket is None or ticket.profile_id != profile_id:
        raise HTTPException(404, "Referral not found.")

    target = ReferralState.USER_CONFIRMED if received == "yes" else ReferralState.CANCELLED
    try:
        app.referrals.transition(
            ticket_id,
            target,
            "user",
            profile_id,
            note=note
            or (
                "User confirmed receipt."
                if received == "yes"
                else "User reported the referral was no longer needed."
            ),
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    return redirect(f"/p/{profile_id}/referrals#{ticket_id}")
