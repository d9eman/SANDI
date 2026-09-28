from __future__ import annotations

from urllib.parse import urlencode

from fastapi import APIRouter, Form, HTTPException, Request

from app.domain.enums import AnswerState
from app.security.web import authorize_profile, verify_csrf

from .public_context import container, redirect, render_page


router = APIRouter()


@router.get("/profile/start")
def profile_start(request: Request, source: str = "direct", notice: str = ""):
    return render_page(
        request,
        "profile_start.html",
        {
            "source": source,
            "prefill_zip": request.session.get("last_food_zip", "") if source == "food" else "",
            "notice": notice,
        },
    )


@router.post("/start")
def start(
    request: Request,
    csrf: str = Form(...),
    need: str = Form("food"),
    danger: str = Form("no"),
    language: str = Form("en"),
    source: str = Form("direct"),
):
    verify_csrf(request, csrf)
    if need != "food":
        raise HTTPException(400, "This prototype currently supports food needs only.")

    old_visitor = request.session.get("visitor_id")
    prefill_zip = str(request.session.get("last_food_zip") or "") if source == "food" else ""
    prefill_urgency = str(request.session.get("last_food_urgency") or "") if source == "food" else ""

    app = container(request)
    profile, phrase = app.profiles.create_guest(language)
    request.session.clear()
    if old_visitor:
        request.session["visitor_id"] = old_visitor
    request.session["profile_id"] = profile.profile_id
    request.session["recovery_phrase_once"] = phrase

    if prefill_zip:
        app.profiles.save_answer(profile.profile_id, "zip_code", AnswerState.KNOWN, prefill_zip)
    if prefill_urgency:
        app.profiles.save_answer(profile.profile_id, "urgency", AnswerState.KNOWN, prefill_urgency)
    if danger == "yes":
        request.session["return_after_emergency"] = True
        return redirect(f"/p/{profile.profile_id}/emergency")
    return redirect(f"/p/{profile.profile_id}/created")


@router.get("/p/{profile_id}/created")
def profile_created(request: Request, profile_id: str):
    authorize_profile(request, profile_id)
    phrase = request.session.pop("recovery_phrase_once", None)
    if not phrase:
        return redirect(f"/p/{profile_id}")
    profile = container(request).profiles.require(profile_id)
    return render_page(
        request,
        "profile_created.html",
        {"profile": profile, "profile_id": profile_id, "recovery_phrase": phrase},
    )


@router.get("/p/{profile_id}/emergency")
def emergency(request: Request, profile_id: str):
    authorize_profile(request, profile_id)
    return render_page(request, "emergency.html", {"profile_id": profile_id})


@router.post("/p/{profile_id}/emergency/continue")
def emergency_continue(request: Request, profile_id: str, csrf: str = Form(...)):
    authorize_profile(request, profile_id)
    verify_csrf(request, csrf)
    request.session.pop("return_after_emergency", None)
    phrase = request.session.get("recovery_phrase_once")
    return redirect(f"/p/{profile_id}/created" if phrase else f"/p/{profile_id}/questions")


@router.get("/return")
def return_form(request: Request):
    return render_page(request, "return.html")


@router.post("/return")
def return_profile(
    request: Request,
    csrf: str = Form(...),
    profile_id: str = Form(...),
    recovery_phrase: str = Form(...),
):
    verify_csrf(request, csrf)
    normalized = profile_id.strip().upper()
    if not container(request).profiles.authenticate(normalized, recovery_phrase):
        return render_page(
            request,
            "return.html",
            {"error": "Profile ID or recovery phrase was not recognized."},
            400,
        )
    request.session.clear()
    request.session["profile_id"] = normalized
    return redirect(f"/p/{normalized}")


@router.post("/logout")
def logout(request: Request, csrf: str = Form(...)):
    verify_csrf(request, csrf)
    request.session.clear()
    return redirect("/")


# Compatibility endpoints preserve old v2/v3 bookmarks without keeping old UX.
@router.get("/p/{profile_id}/routing")
def routing_form(request: Request, profile_id: str):
    authorize_profile(request, profile_id)
    return redirect(f"/p/{profile_id}/questions?question=zip_code")


@router.post("/p/{profile_id}/routing")
def routing_save(
    request: Request,
    profile_id: str,
    csrf: str = Form(...),
    zip_code: str = Form(""),
    urgency: str = Form("today"),
    accessibility_needs: str = Form(""),
):
    authorize_profile(request, profile_id)
    verify_csrf(request, csrf)
    app = container(request)
    clean_zip = app.resources.extract_zip(zip_code)
    app.profiles.save_answer(
        profile_id,
        "zip_code",
        AnswerState.KNOWN if clean_zip else AnswerState.UNKNOWN,
        clean_zip or None,
    )
    app.profiles.save_answer(profile_id, "urgency", AnswerState.KNOWN, urgency)
    app.profiles.save_answer(
        profile_id,
        "accessibility_needs",
        AnswerState.KNOWN if accessibility_needs.strip() else AnswerState.SKIPPED,
        accessibility_needs.strip() or None,
    )
    return redirect(f"/p/{profile_id}/questions")


@router.get("/p/{profile_id}/resources")
def resources_compatibility(request: Request, profile_id: str):
    authorize_profile(request, profile_id)
    profile = container(request).profiles.require(profile_id)
    query = urlencode({"location": str(profile.value("zip_code") or "")})
    return redirect(f"/food-now?{query}")


@router.get("/p/{profile_id}/help")
def more_help_compatibility(request: Request, profile_id: str):
    authorize_profile(request, profile_id)
    return redirect(f"/p/{profile_id}/results")


@router.get("/p/{profile_id}")
def profile_dashboard(request: Request, profile_id: str):
    authorize_profile(request, profile_id)
    app = container(request)
    profile = app.profiles.require(profile_id)
    assessments = app.screening.evaluate(profile)
    return render_page(
        request,
        "dashboard.html",
        {
            "profile": profile,
            "assessments": assessments,
            "tickets": app.referral_repository.list_for_profile(profile_id),
            "documents": app.documents.list_for_profile(profile_id),
            "questions": app.screening.rules.questions(),
            "progress": app.screening.progress_summary(profile, assessments),
        },
    )
