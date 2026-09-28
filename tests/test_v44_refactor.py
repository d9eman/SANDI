from __future__ import annotations

from datetime import date, datetime, timezone

from fastapi.testclient import TestClient

from app.adapters.rules.json_repository import JsonRuleRepository
from app.domain.eligibility import EligibilityEngine
from app.domain.enums import AnswerState, EligibilityStatus
from app.domain.models import Answer, ProfileSnapshot
from app.main import create_app
from app.presentation.web.eligibility_view import group_assessments


def _profile(**values):
    return ProfileSnapshot(
        profile_id="SAN-TEST",
        language="en",
        created_at=datetime.now(timezone.utc),
        answers={key: Answer(key, AnswerState.KNOWN, value) for key, value in values.items()},
    )


def test_overdue_review_date_does_not_change_user_result(settings):
    repo = JsonRuleRepository(settings.rules_dir, settings.questions_path)
    rule = next(rule for rule in repo.active_rules(date(2026, 9, 28)) if rule.program_id == "calfresh")
    assert rule.review_overdue(date(2026, 9, 28)) is True
    result = EligibilityEngine(today_provider=lambda: date(2026, 9, 28)).evaluate(
        _profile(zip_code="92101", household_size=1, monthly_income=1200, student_half_time="no"),
        rule,
    )
    assert result.status is EligibilityStatus.LIKELY_ELIGIBLE
    assert result.requirements


def test_overdue_review_date_is_not_a_user_maintenance_group(settings):
    app = create_app(settings)
    app.state.container.screening.engine.today_provider = lambda: date(2026, 9, 28)
    profile, _ = app.state.container.profiles.create_guest("en")
    assessments = app.state.container.screening.evaluate(profile)
    groups = group_assessments(assessments)
    assert all(item.program_id != "calfresh" for item in groups["updating"])


def test_public_results_hide_internal_rule_dates(settings):
    app = create_app(settings)
    app.state.container.screening.engine.today_provider = lambda: date(2026, 9, 28)
    client = TestClient(app)
    start = client.get("/profile/start")
    import re

    csrf = re.search(r'name="csrf" value="([^"]+)"', start.text).group(1)
    response = client.post(
        "/start",
        data={"csrf": csrf, "need": "food", "danger": "no", "language": "en", "source": "direct"},
        follow_redirects=False,
    )
    profile_id = response.headers["location"].split("/")[2]
    page = client.get(f"/p/{profile_id}/results")
    assert page.status_code == 200
    assert "review due" not in page.text.lower()
    assert "effective 2025" not in page.text.lower()


def test_staff_rules_show_internal_review_warning(settings):
    client = TestClient(create_app(settings))
    login = client.get("/staff/login")
    import re

    csrf = re.search(r'name="csrf" value="([^"]+)"', login.text).group(1)
    auth = client.post(
        "/staff/login",
        data={"csrf": csrf, "username": settings.staff_username, "password": settings.staff_password},
        follow_redirects=True,
    )
    assert auth.status_code == 200
    page = client.get("/staff/rules")
    assert page.status_code == 200
    assert "Review due" in page.text
    assert "review-dot" in page.text


def test_timeline_connector_sits_between_dots_not_through_labels(settings):
    client = TestClient(create_app(settings))
    css = client.get("/static/styles.css").text
    assert ".journey-step::after" in css
    assert "flex-direction:column" in css
    assert ".journey-step::before" not in css


def test_answer_parser_is_channel_independent(settings):
    questions = JsonRuleRepository(settings.rules_dir, settings.questions_path).questions()
    from app.application.answer_parser import parse_question_answer

    assert parse_question_answer(questions["zip_code"], "92101") == "92101"
    assert parse_question_answer(questions["household_size"], "2") == 2
