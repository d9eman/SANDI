from __future__ import annotations

from datetime import date

from app.bootstrap import build_container
from app.domain.enums import AnswerState


def next_id(app, profile_id: str) -> str | None:
    profile = app.profiles.require(profile_id)
    return (question.question_id if (question := app.screening.next_question(profile, app.screening.evaluate(profile))) else None)


def test_planner_uses_shared_question_order_and_respects_skip(settings):
    app = build_container(settings)
    app.screening.engine.today_provider = lambda: date(2026, 8, 2)
    profile, _ = app.profiles.create_guest("en")
    assert next_id(app, profile.profile_id) == "zip_code"

    app.profiles.save_answer(profile.profile_id, "zip_code", AnswerState.KNOWN, "92101")
    assert next_id(app, profile.profile_id) == "household_size"

    app.profiles.save_answer(profile.profile_id, "household_size", AnswerState.SKIPPED)
    assert next_id(app, profile.profile_id) != "household_size"


def test_planner_does_not_ask_rmp_followups_after_current_calfresh_no(settings):
    app = build_container(settings)
    profile, _ = app.profiles.create_guest("en")
    for question_id, value in {
        "zip_code": "92101",
        "household_size": 1,
        "monthly_income": 1200,
        "student_half_time": "no",
        "child_under_5": "no",
        "current_calfresh": "no",
    }.items():
        app.profiles.save_answer(profile.profile_id, question_id, AnswerState.KNOWN, value)
    question_id = next_id(app, profile.profile_id)
    assert question_id not in {"age", "housing_status", "disability"}
