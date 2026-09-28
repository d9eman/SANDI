from __future__ import annotations

from collections import defaultdict
from datetime import date

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse, Response
from fastapi.templating import Jinja2Templates

from app.domain.rule_inspection import collect_fields, collect_question_fields
from app.domain.rule_export import requirement_matrix_csv
from app.security.web import login_role, logout_role, require_role, verify_credentials, verify_csrf
from .helpers import render

router=APIRouter(prefix="/staff",tags=["staff"]); templates:Jinja2Templates|None=None

def setup_templates(value:Jinja2Templates)->None:
    global templates; templates=value

def container(request:Request): return request.app.state.container

def staff_actor(request:Request)->str: return require_role(request,"staff","/staff/login")

def redirect(url:str)->RedirectResponse: return RedirectResponse(url,status_code=303)

@router.get("/login")
def login_form(request:Request):
    settings=container(request).settings
    demo={"username":settings.staff_username,"password":"sandi-demo"} if settings.demo_mode and settings.staff_password=="sandi-demo" else None
    return render(templates,request,"role_login.html",{"role_title":"Staff","action":"/staff/login","explanation":"Trace questions, rules, saved answers, and referrals.","demo_credentials":demo})

@router.post("/login")
def login(request:Request,csrf:str=Form(...),username:str=Form(...),password:str=Form(...)):
    verify_csrf(request,csrf); settings=container(request).settings
    if not verify_credentials(username,password,settings.staff_username,settings.staff_password):
        return render(templates,request,"role_login.html",{"role_title":"Staff","action":"/staff/login","explanation":"Trace questions, rules, saved answers, and referrals.","error":"Invalid staff credentials. Restart the app after changing .env."},401)
    login_role(request,"staff",username); return redirect("/staff")

@router.post("/logout")
def logout(request:Request,csrf:str=Form(...)):
    verify_csrf(request,csrf); logout_role(request,"staff"); return redirect("/staff/login")

@router.get("")
def dashboard(request:Request,actor:str=Depends(staff_actor)):
    app=container(request)
    return render(templates,request,"staff_dashboard.html",{"actor":actor,"metrics":app.audit_repository.metrics(),"profiles":app.profile_repository.list_recent(),"tickets":app.referral_repository.list_for_provider(None)})

@router.get("/questions")
def question_catalog(request:Request,actor:str=Depends(staff_actor)):
    app=container(request); questions=app.screening.rules.questions(); usage=defaultdict(list)
    for rule in app.screening.rules.active_rules():
        for field in collect_question_fields(rule.expression): usage[field].append(rule.program_name)
    ordered=sorted(questions.values(),key=lambda q:(q.sensitivity,q.priority,q.question_id))
    return render(templates,request,"staff_questions.html",{"actor":actor,"questions":ordered,"usage":usage})

@router.get("/rules")
def rule_catalog(request:Request,actor:str=Depends(staff_actor)):
    rules=container(request).screening.rules.active_rules()
    today=date.today()
    summaries=[
        {
            "rule":rule,
            "fields":sorted(collect_fields(rule.expression)),
            "review_overdue":rule.review_overdue(today),
            "effective_state":rule.effective_state(today),
        }
        for rule in rules
    ]
    return render(templates,request,"staff_rules.html",{"actor":actor,"summaries":summaries})


@router.get("/eligibility-matrix.csv")
def eligibility_matrix(request:Request,actor:str=Depends(staff_actor)):
    app=container(request)
    content=requirement_matrix_csv(app.screening.rules.active_rules(),app.screening.rules.questions())
    app.audit_repository.record("staff",actor,"export","eligibility_matrix","active","team rule review","success")
    return Response(
        content=content.encode("utf-8-sig"),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition":"attachment; filename=SANDI_Eligibility_Requirements_and_Questions.csv"},
    )

@router.post("/lookup")
def lookup(request:Request,csrf:str=Form(...),profile_id:str=Form(...),actor:str=Depends(staff_actor)):
    verify_csrf(request,csrf); normalized=profile_id.strip().upper()
    if container(request).profile_repository.get(normalized) is None: raise HTTPException(404,"Profile not found.")
    return redirect(f"/staff/profiles/{normalized}")

@router.get("/profiles/{profile_id}")
def profile_view(request:Request,profile_id:str,actor:str=Depends(staff_actor)):
    app=container(request); profile=app.profile_repository.get(profile_id)
    if profile is None: raise HTTPException(404,"Profile not found.")
    app.audit_repository.record("staff",actor,"view","profile",profile_id,"provider-assisted support","success")
    assessments=app.screening.evaluate(profile); tickets=app.referral_repository.list_for_profile(profile_id)
    document_count=len(app.documents.list_for_profile(profile_id)); questions=app.screening.rules.questions()
    return render(templates,request,"staff_profile.html",{"actor":actor,"profile":profile,"assessments":assessments,"tickets":tickets,"document_count":document_count,"questions":questions})
