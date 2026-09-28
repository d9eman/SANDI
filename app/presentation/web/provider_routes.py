from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.domain.enums import AvailabilityStatus, ReferralState, Visibility
from app.domain.referrals import InvalidTransition
from app.domain.provider_quality import service_quality
from app.security.web import login_role, logout_role, require_role, verify_credentials, verify_csrf
from .helpers import render

router = APIRouter(prefix="/provider", tags=["provider"])
templates: Jinja2Templates | None = None


def setup_templates(value: Jinja2Templates) -> None:
    global templates
    templates = value


def container(request: Request): return request.app.state.container

def provider_actor(request: Request) -> str: return require_role(request, "provider", "/provider/login")

def redirect(url: str) -> RedirectResponse: return RedirectResponse(url, status_code=303)

@router.get("/login")
def login_form(request: Request):
    settings=container(request).settings
    demo={"username":settings.provider_username,"password":"sandi-demo"} if settings.demo_mode and settings.provider_password=="sandi-demo" else None
    return render(templates,request,"role_login.html",{"role_title":"Provider","action":"/provider/login","explanation":"Update provider services, availability, and referral tickets.","demo_credentials":demo})

@router.post("/login")
def login(request:Request,csrf:str=Form(...),username:str=Form(...),password:str=Form(...)):
    verify_csrf(request,csrf); settings=container(request).settings
    if not verify_credentials(username,password,settings.provider_username,settings.provider_password):
        return render(templates,request,"role_login.html",{"role_title":"Provider","action":"/provider/login","explanation":"Update provider services, availability, and referral tickets.","error":"Invalid provider credentials. Restart the app after changing .env."},401)
    login_role(request,"provider",username); return redirect("/provider")

@router.post("/logout")
def logout(request:Request,csrf:str=Form(...)):
    verify_csrf(request,csrf); logout_role(request,"provider"); return redirect("/provider/login")

@router.get("")
def dashboard(request: Request, provider_id: str | None = None, actor: str = Depends(provider_actor)):
    app=container(request); providers=app.resource_repository.list_providers(); unique={}
    for item in providers: unique[item["id"]]=item["name"]
    selected=provider_id or (next(iter(unique)) if unique else None); tickets=app.referral_repository.list_for_provider(selected)
    selected_services=[]
    for item in providers:
        if item["id"] == selected:
            item["quality"] = service_quality(item)
            selected_services.append(item)
    quality_average = round(sum(item["quality"]["score"] for item in selected_services) / len(selected_services)) if selected_services else 0
    for ticket in tickets:
        try: ticket["allowed_targets"]=[state.value for state in app.referrals.allowed_targets(ticket["id"])]
        except KeyError: ticket["allowed_targets"]=[]
        ticket["summary"] = f"Food request · {ticket.get('urgency') or 'planning'} · ZIP {ticket.get('zip_code') or 'not provided'}"
    return render(templates,request,"provider_dashboard.html",{"actor":actor,"providers":providers,"unique_providers":unique,"selected_provider_id":selected,"selected_services":selected_services,"quality_average":quality_average,"tickets":tickets,"availability_statuses":[x.value for x in AvailabilityStatus],"visibility_options":[x.value for x in Visibility]})

@router.post("/availability")
def update_availability(request:Request,csrf:str=Form(...),service_id:str=Form(...),status:str=Form(...),visibility:str=Form("PUBLIC"),details:str=Form(""),provider_id:str=Form(""),actor:str=Depends(provider_actor)):
    verify_csrf(request,csrf)
    try: AvailabilityStatus(status); Visibility(visibility)
    except ValueError as exc: raise HTTPException(400,"Invalid availability status or visibility.") from exc
    try:
        container(request).resources.update_availability(service_id,status,visibility,details,actor)
    except KeyError as exc:
        raise HTTPException(404,"Service not found.") from exc
    return redirect(f"/provider?provider_id={provider_id}")

@router.post("/tickets/{ticket_id}/transition")
def transition_ticket(request:Request,ticket_id:str,csrf:str=Form(...),target_state:str=Form(...),note:str=Form(""),scheduled_for:str=Form(""),outcome:str=Form(""),decline_reason:str=Form(""),provider_id:str=Form(""),actor:str=Depends(provider_actor)):
    verify_csrf(request,csrf)
    try: container(request).referrals.transition(ticket_id,ReferralState(target_state),"provider",actor,note=note,scheduled_for=scheduled_for or None,outcome=outcome or None,decline_reason=decline_reason or None)
    except KeyError as exc: raise HTTPException(404,"Referral not found.") from exc
    except (ValueError,InvalidTransition) as exc: raise HTTPException(400,str(exc)) from exc
    return redirect(f"/provider?provider_id={provider_id}#{ticket_id}")

@router.get("/new")
def new_provider_form(request:Request,actor:str=Depends(provider_actor)):
    return render(templates,request,"provider_form.html",{"actor":actor})

@router.post("/new")
def add_provider(
    request: Request,
    csrf: str = Form(...),
    provider_name: str = Form(...),
    legal_name: str = Form(""),
    service_name: str = Form(...),
    journey_stage: str = Form("direct_help"),
    zip_code: str = Form(""),
    location_name: str = Form(""),
    address: str = Form(""),
    city: str = Form("San Diego"),
    state: str = Form("CA"),
    latitude: str = Form(""),
    longitude: str = Form(""),
    hours_text: str = Form("Call to verify"),
    service_area: str = Form("San Diego County"),
    schedule_exceptions: str = Form(""),
    transport_notes: str = Form(""),
    phone: str = Form(""),
    website: str = Form(""),
    source_url: str = Form(""),
    description: str = Form(""),
    eligibility_summary: str = Form(""),
    documentation_notes: str = Form(""),
    eligibility_group: str = Form("SITE_SPECIFIC_FOOD_DISTRIBUTION"),
    service_mode: str = Form("direct_service"),
    languages: str = Form(""),
    accessibility: str = Form(""),
    public_visibility: str = Form("PUBLIC"),
    service_public_visibility: str = Form("RESTRICTED"),
    data_quality_status: str = Form("under_review"),
    partner_status: str = Form("not_contacted"),
    last_verified_at: str = Form(""),
    call_first: str = Form("false"),
    referral_enabled: str = Form("false"),
    availability_status: str = Form("UNKNOWN"),
    availability_visibility: str = Form("PUBLIC"),
    actor: str = Depends(provider_actor),
):
    verify_csrf(request, csrf)
    if journey_stage not in {"immediate_food", "more_help", "direct_help"}:
        raise HTTPException(400, "Invalid user-journey stage.")
    try:
        AvailabilityStatus(availability_status)
        Visibility(availability_visibility)
        Visibility(public_visibility)
        Visibility(service_public_visibility)
    except ValueError as exc:
        raise HTTPException(400, "Invalid visibility or availability value.") from exc

    provider_id = f"prov_{uuid.uuid4().hex[:10]}"
    service_id = f"svc_{uuid.uuid4().hex[:10]}"
    location_id = f"loc_{uuid.uuid4().hex[:10]}"
    record = {
        "provider_id": provider_id,
        "provider_name": provider_name.strip(),
        "legal_name": legal_name.strip(),
        "provider_description": description.strip(),
        "website": website.strip(),
        "phone": phone.strip(),
        "source_type": "provider_portal",
        "source_url": source_url.strip(),
        "data_quality_status": data_quality_status,
        "last_verified_at": last_verified_at.strip(),
        "public_visibility": public_visibility,
        "organization_type": "community_provider",
        "partner_status": partner_status,
        "service_id": service_id,
        "service_name": service_name.strip(),
        "service_type": "food",
        "service_category": "food",
        "service_mode": service_mode,
        "journey_stage": journey_stage,
        "service_public_visibility": service_public_visibility,
        "service_description": description.strip(),
        "eligibility_summary": eligibility_summary.strip(),
        "eligibility_group": eligibility_group.strip(),
        "documentation_notes": documentation_notes.strip(),
        "call_first": call_first,
        "referral_enabled": referral_enabled,
        "location_id": location_id,
        "location_name": location_name.strip() or f"{service_name.strip()} location",
        "address": address.strip(),
        "city": city.strip(),
        "state": state.strip() or "CA",
        "zip_code": zip_code.strip(),
        "hours_text": hours_text.strip(),
        "service_area": service_area.strip(),
        "languages": languages.strip(),
        "accessibility": accessibility.strip(),
        "schedule_exceptions": schedule_exceptions.strip(),
        "transport_notes": transport_notes.strip(),
        "latitude": latitude.strip(),
        "longitude": longitude.strip(),
        "availability_status": availability_status,
        "availability_visibility": availability_visibility,
        "availability_details": "Entered through the provider portal.",
    }
    container(request).resources.add_provider_record(record, actor)
    return redirect(f"/provider?provider_id={provider_id}")

@router.get("/import")
def import_form(request:Request,actor:str=Depends(provider_actor)):
    return render(templates,request,"provider_import.html",{"actor":actor})

@router.post("/import")
async def import_csv(request:Request,csrf:str=Form(...),file:UploadFile=File(...),actor:str=Depends(provider_actor)):
    verify_csrf(request,csrf)
    if not (file.filename or "").lower().endswith(".csv"):
        return render(templates,request,"provider_import.html",{"actor":actor,"error":"Upload a CSV file."},400)
    try: count,_=container(request).resources.import_csv(await file.read(),actor)
    except (UnicodeDecodeError,ValueError) as exc: return render(templates,request,"provider_import.html",{"actor":actor,"error":str(exc)},400)
    return render(templates,request,"provider_import.html",{"actor":actor,"success":f"Imported {count} provider-service rows."})
