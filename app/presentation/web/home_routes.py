from __future__ import annotations

from urllib.parse import urlencode

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import RedirectResponse

from app.security.web import active_profile_id, verify_csrf

from .public_context import container, redirect, render_page, safe_float, visitor_id


router = APIRouter()


@router.get("/")
def index(request: Request):
    return render_page(request, "index.html")


@router.get("/food-now")
def food_now(
    request: Request,
    location: str = "",
    urgency: str = "today",
    latitude: str = "",
    longitude: str = "",
    feedback: str = "",
):
    """Show no-account food resources and genuinely local direct sites."""
    app = container(request)
    lat = safe_float(latitude)
    lon = safe_float(longitude)
    clean_location = location.strip()
    zip_code = app.resources.extract_zip(clean_location)

    # Short-lived routing context only. Full addresses and exact coordinates are
    # never copied into a profile automatically.
    request.session["last_food_location"] = clean_location
    request.session["last_food_zip"] = zip_code
    request.session["last_food_urgency"] = urgency if urgency in {"now", "today", "next_days"} else "today"
    request.session["last_food_had_coordinates"] = lat is not None and lon is not None

    profile_id = active_profile_id(request)
    matches = app.resources.find_food(
        actor_id=visitor_id(request),
        zip_code=clean_location or None,
        journey_stage="immediate_food",
        profile_id=str(profile_id) if profile_id else None,
        latitude=lat,
        longitude=lon,
    )
    map_resources = [item for item in matches if item["service_mode"] == "external_locator"]
    direct_sites = [item for item in matches if item["service_mode"] == "direct_service"]
    guide_resources = [
        item for item in matches if item["service_mode"] not in {"external_locator", "direct_service"}
    ]
    location_label = clean_location or ("Current location" if lat is not None and lon is not None else "")
    searched = bool(request.url.query)

    return render_page(
        request,
        "food_now.html",
        {
            "location": clean_location,
            "location_label": location_label,
            "urgency": request.session["last_food_urgency"],
            "latitude": latitude,
            "longitude": longitude,
            "map_resources": map_resources,
            "direct_sites": direct_sites,
            "guide_resources": guide_resources,
            "searched": searched,
            "direct_site_count": len(direct_sites),
            "search_radius_miles": direct_sites[0].get("search_radius_miles") if direct_sites else None,
            "feedback": feedback,
        },
    )


@router.get("/go/{service_id}")
def open_public_resource(request: Request, service_id: str, location: str = ""):
    """Record a public handoff, then redirect to the provider-owned resource."""
    profile_id = active_profile_id(request)
    try:
        target = container(request).resources.record_open(
            visitor_id=visitor_id(request),
            profile_id=str(profile_id) if profile_id else None,
            service_id=service_id,
            location_text=location.strip(),
        )
    except KeyError as exc:
        raise HTTPException(404, "Resource not found.") from exc
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    return RedirectResponse(url=target, status_code=302)


@router.post("/resource-feedback")
def resource_feedback(
    request: Request,
    csrf: str = Form(...),
    service_id: str = Form(...),
    outcome: str = Form(...),
    location: str = Form(""),
    note: str = Form(""),
):
    verify_csrf(request, csrf)
    profile_id = active_profile_id(request)
    app = container(request)
    try:
        app.resources.record_feedback(
            visitor_id=visitor_id(request),
            profile_id=str(profile_id) if profile_id else None,
            service_id=service_id,
            outcome=outcome,
            location_text=location.strip(),
            note=note.strip(),
        )
    except KeyError as exc:
        raise HTTPException(404, "Resource not found.") from exc
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc

    if profile_id:
        return redirect(f"/p/{profile_id}/results?feedback=thanks")
    query = urlencode({"location": location.strip(), "feedback": "thanks"})
    return redirect(f"/food-now?{query}")
