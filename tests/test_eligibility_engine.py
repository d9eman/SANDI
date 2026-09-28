from __future__ import annotations

from datetime import date, datetime, timezone

from app.adapters.rules.json_repository import JsonRuleRepository
from app.domain.eligibility import EligibilityEngine
from app.domain.enums import AnswerState, EligibilityStatus, TriState
from app.domain.models import Answer, ProfileSnapshot


def profile(**values):
    return ProfileSnapshot(
        profile_id="SAN-TEST",
        language="en",
        created_at=datetime.now(timezone.utc),
        answers={key: Answer(key, AnswerState.KNOWN, value) for key, value in values.items()},
    )


def rule_for(settings, program_id: str, on_date: date = date(2026, 8, 2)):
    repo = JsonRuleRepository(settings.rules_dir, settings.questions_path)
    return next(rule for rule in repo.active_rules(on_date) if rule.program_id == program_id)


def test_calfresh_fixture_is_deterministic_and_strong_match(settings):
    result = EligibilityEngine(today_provider=lambda: date(2026, 8, 2)).evaluate(
        profile(zip_code="92101", household_size=1, monthly_income=1200, student_half_time="no"),
        rule_for(settings, "calfresh"),
    )
    assert result.status == EligibilityStatus.LIKELY_ELIGIBLE
    assert result.rule_version_id == "calfresh-sd-2025-10-v2"
    assert not result.missing_fields


def test_unknown_does_not_become_denial(settings):
    result = EligibilityEngine(today_provider=lambda: date(2026, 8, 2)).evaluate(
        profile(zip_code="92101"),
        rule_for(settings, "calfresh"),
    )
    assert result.status == EligibilityStatus.NEEDS_INFORMATION
    assert "household_size" in result.missing_fields
    assert "monthly_income" in result.missing_fields


def test_student_branch_is_conditional(settings):
    result = EligibilityEngine(today_provider=lambda: date(2026, 8, 2)).evaluate(
        profile(
            zip_code="92101",
            household_size=1,
            monthly_income=1200,
            student_half_time="yes",
            student_meal_plan_majority="no",
            student_exemptions=["work_20_hours"],
        ),
        rule_for(settings, "calfresh"),
    )
    assert result.status == EligibilityStatus.LIKELY_ELIGIBLE


def test_known_failure_short_circuits_irrelevant_missing_questions(settings):
    result = EligibilityEngine(today_provider=lambda: date(2026, 8, 2)).evaluate(
        profile(current_calfresh="no"),
        rule_for(settings, "restaurant_meals"),
    )
    assert result.status == EligibilityStatus.LIKELY_NOT_ELIGIBLE
    assert not result.missing_fields
    assert all(item.state is not TriState.UNKNOWN for item in result.requirements)


def test_failure_explains_expected_and_actual(settings):
    result = EligibilityEngine(today_provider=lambda: date(2026, 8, 2)).evaluate(
        profile(
            monthly_income=500,
            liquid_resources=50,
            monthly_shelter_cost=100,
            monthly_utility_cost=50,
            migrant_seasonal_farmworker="no",
        ),
        rule_for(settings, "calfresh_expedited"),
    )
    assert result.status == EligibilityStatus.LIKELY_NOT_ELIGIBLE
    income = next(item for item in result.requirements if item.field_name == "monthly_income")
    assert income.expected == "Less than $150"
    assert income.actual == "$500"


def test_rule_outside_window_is_under_review(settings):
    rule = rule_for(settings, "calfresh", date(2027, 1, 1))
    result = EligibilityEngine(today_provider=lambda: date(2027, 1, 1)).evaluate(
        profile(zip_code="92101", household_size=1, monthly_income=1000, student_half_time="no"),
        rule,
    )
    assert result.status == EligibilityStatus.RULE_UNDER_REVIEW
