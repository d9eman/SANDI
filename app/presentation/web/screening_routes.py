from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from app.application.answer_parser import parse_question_answer
from app.domain.enums import AnswerState
from app.security.web import authorize_profile, verify_csrf

from .eligibility_view import group_assessments, resolve_actions
from .public_context import container, redirect, render_page


router = APIRouter()


@router.get("/p/{profile_id}/questions")
def questions(request: Request, profile_id: str, question: str | None = None):
    authorize_profile(request, profile_id)
    app = container(request)
    profile = app.profiles.require(profile_id)
    assessments = app.screening.evaluate(profile)

    if question:
        try:
            next_question = app.screening.question(question)
        except KeyError:
            next_question = app.screening.next_question(profile, assessments)
    else:
        next_question = app.screening.next_question(profile, assessments)

    if next_question is None:
        return redirect(f"/p/{profile_id}/results")

    alerts = request.session.pop("new_match_programs", [])
    new_matches = [item for item in assessments if item.program_id in alerts]
    return render_page(
        request,
        "question.html",
        {
            "profile": profile,
            "question": next_question,
            "assessments": assessments,
            "new_matches": new_matches,
            "actions_by_program": resolve_actions(
                app.resources,
                new_matches,
                str(profile.value("zip_code") or ""),
            ),
            "progress": app.screening.progress_summary(profile, assessments),
            "answer_saved": bool(request.session.pop("answer_saved_once", False)),
        },
    )


@router.post("/p/{profile_id}/questions/{question_id}")
async def answer_question(request: Request, profile_id: str, question_id: str):
    authorize_profile(request, profile_id)
    form = await request.form()
    verify_csrf(request, str(form.get("csrf", "")))
    app = container(request)

    try:
        question = app.screening.question(question_id)
    except KeyError as exc:
        raise HTTPException(404, "Question not found.") from exc

    before_profile = app.profiles.require(profile_id)
    before = app.screening.evaluate(before_profile)
    try:
        state = AnswerState(str(form.get("answer_state", "known")))
        raw_values = [str(item) for item in form.getlist("value")]
        raw_value = raw_values[0] if raw_values else None
        value = parse_question_answer(question, raw_value, raw_values) if state is AnswerState.KNOWN else None
        updated_profile = app.profiles.save_answer(profile_id, question_id, state, value)
    except (ValueError, TypeError) as exc:
        assessments = app.screening.evaluate(before_profile)
        return render_page(
            request,
            "question.html",
            {
                "profile": before_profile,
                "question": question,
                "assessments": assessments,
                "new_matches": [],
                "actions_by_program": {},
                "progress": app.screening.progress_summary(before_profile, assessments),
                "answer_saved": False,
                "error": str(exc),
            },
            400,
        )

    after = app.screening.evaluate(updated_profile)
    new_matches = app.screening.newly_actionable(before, after)
    request.session["answer_saved_once"] = True
    if new_matches:
        request.session["new_match_programs"] = [item.program_id for item in new_matches]
    return redirect(f"/p/{profile_id}/questions")


@router.get("/p/{profile_id}/results")
def results(request: Request, profile_id: str, feedback: str = ""):
    authorize_profile(request, profile_id)
    app = container(request)
    profile = app.profiles.require(profile_id)
    assessments = app.screening.evaluate(profile)
    next_question = app.screening.next_question(profile, assessments)

    return render_page(
        request,
        "results.html",
        {
            "profile": profile,
            "assessments": assessments,
            "groups": group_assessments(assessments),
            "questions": app.screening.rules.questions(),
            "actions_by_program": resolve_actions(
                app.resources,
                assessments,
                str(profile.value("zip_code") or ""),
            ),
            "next_question": next_question,
            "progress": app.screening.progress_summary(profile, assessments),
            "feedback": feedback,
        },
    )
