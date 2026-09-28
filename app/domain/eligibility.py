from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Callable

from .enums import EligibilityStatus, TriState
from .fields import question_field_for
from .models import EligibilityAssessment, PredicateResult, ProfileSnapshot


@dataclass(frozen=True)
class ProgramRuleVersion:
    program_id: str
    program_name: str
    program_description: str
    rule_version_id: str
    effective_from: str
    effective_to: str | None
    review_due: str | None
    source_label: str
    source_url: str
    notice: str
    pass_status: EligibilityStatus
    unknown_status: EligibilityStatus
    fail_status: EligibilityStatus
    expression: dict[str, Any]
    next_steps: dict[str, str]
    result_summaries: dict[str, str]
    display_priority: int = 100
    access_score: int = 50
    actions: tuple[dict[str, Any], ...] = ()

    @property
    def question_weight(self) -> int:
        """Higher means an unanswered field is more valuable to ask next."""
        return max(1, 120 - self.display_priority) + max(0, self.access_score)

    def effective_issue(self, on_date: date) -> str | None:
        """Return why this rule version is outside its effective window.

        Review dates are governance metadata only. Passing ``review_due`` does
        not change a user's eligibility result or deactivate the rule.
        """
        if date.fromisoformat(self.effective_from) > on_date:
            return "not_yet_effective"
        if self.effective_to and date.fromisoformat(self.effective_to) < on_date:
            return "expired"
        return None

    def review_overdue(self, on_date: date) -> bool:
        """Return whether an internal rule review date has passed."""
        return bool(self.review_due and date.fromisoformat(self.review_due) < on_date)

    def effective_state(self, on_date: date) -> str:
        """Small internal status used by staff rule-management screens."""
        issue = self.effective_issue(on_date)
        if issue == "not_yet_effective":
            return "upcoming"
        if issue == "expired":
            return "expired"
        return "active"


class EligibilityEngine:
    """Deterministic, source-linked pre-screening with explainable comparisons."""

    def __init__(self, today_provider: Callable[[], date] | None = None):
        self.today_provider = today_provider or date.today

    def evaluate(self, profile: ProfileSnapshot, rule: ProgramRuleVersion) -> EligibilityAssessment:
        today = self.today_provider()
        effective_issue = rule.effective_issue(today)
        if effective_issue:
            status = EligibilityStatus.RULE_UNDER_REVIEW
            # Rule freshness is a system responsibility, not a user-answer
            # failure. Do not fabricate an expected-vs-actual requirement row.
            requirements: tuple[PredicateResult, ...] = ()
            reasons = (
                "SANDI is refreshing this program's screening rules. "
                "This status is not caused by any answer you gave.",
            )
            missing_fields: tuple[str, ...] = ()
        else:
            result, detail_list = self._evaluate_node(profile, rule.expression)
            requirements = tuple(self._deduplicate_details(detail_list))
            reasons = tuple(dict.fromkeys(item.reason for item in requirements if item.reason))
            missing_fields = tuple(dict.fromkeys(item.missing_field for item in requirements if item.missing_field))
            status = {
                TriState.PASS: rule.pass_status,
                TriState.FAIL: rule.fail_status,
                TriState.UNKNOWN: rule.unknown_status,
            }[result]

        summary = rule.result_summaries.get(
            status.value,
            {
                EligibilityStatus.DIRECT_RESOURCE.value: "This resource is available without a benefit eligibility decision.",
                EligibilityStatus.LIKELY_ELIGIBLE.value: "Your current answers are a strong pre-screen match.",
                EligibilityStatus.MAY_QUALIFY.value: "Your answers suggest this route is worth checking.",
                EligibilityStatus.NEEDS_INFORMATION.value: "One or more answers could change this result.",
                EligibilityStatus.LIKELY_NOT_ELIGIBLE.value: "At least one current answer does not meet this pre-screen.",
                EligibilityStatus.RULE_UNDER_REVIEW.value: "SANDI is refreshing this program's screening rules before showing a match result.",
            }[status.value],
        )
        return EligibilityAssessment(
            program_id=rule.program_id,
            program_name=rule.program_name,
            program_description=rule.program_description,
            rule_version_id=rule.rule_version_id,
            status=status,
            summary=summary,
            reasons=reasons,
            requirements=requirements,
            missing_fields=missing_fields,
            source_label=rule.source_label,
            source_url=rule.source_url,
            effective_from=rule.effective_from,
            effective_to=rule.effective_to,
            notice=rule.notice,
            next_step=rule.next_steps.get(status.value, rule.next_steps.get("default", "Review the official program route.")),
            display_priority=rule.display_priority,
            access_score=rule.access_score,
            actions=rule.actions,
            assessed_at=datetime.now(timezone.utc),
        )

    @staticmethod
    def _deduplicate_details(details: list[PredicateResult]) -> list[PredicateResult]:
        seen: set[tuple[Any, ...]] = set()
        output: list[PredicateResult] = []
        for item in details:
            key = (
                item.state,
                item.field_name,
                item.missing_field,
                item.requirement,
                item.expected,
                item.actual,
                item.reason,
                item.branch,
            )
            if key not in seen:
                seen.add(key)
                output.append(item)
        return output

    def _evaluate_node(self, profile: ProfileSnapshot, node: dict[str, Any]) -> tuple[TriState, list[PredicateResult]]:
        node_type = node.get("type")
        label = str(node.get("label", ""))
        if node_type == "always":
            return TriState.PASS, [
                PredicateResult(
                    TriState.PASS,
                    reason=node.get("pass_reason"),
                    requirement=node.get("requirement", "No formal eligibility screen"),
                    expected=node.get("expected_text", "Available without answering benefit questions"),
                    actual="Available",
                    branch=label,
                )
            ]
        if node_type == "predicate":
            result = self._evaluate_predicate(profile, node)
            return result.state, [replace(result, branch=result.branch or label)]
        if node_type == "sum_compare":
            state, details = self._evaluate_sum_compare(profile, node)
            return state, [replace(item, branch=item.branch or label) for item in details]
        if node_type == "if_then":
            when_state, when_details = self._evaluate_node(profile, node["when"])
            if when_state is TriState.FAIL:
                return TriState.PASS, [
                    PredicateResult(
                        TriState.PASS,
                        reason=node.get("not_applicable_reason"),
                        requirement=node.get("requirement", label or "Conditional requirement"),
                        expected=node.get("not_applicable_expected", "Only applies when the condition is true"),
                        actual="Not applicable based on your answer",
                        branch=label,
                    )
                ]
            if when_state is TriState.UNKNOWN:
                return TriState.UNKNOWN, when_details
            then_state, then_details = self._evaluate_node(profile, node["then"])
            return then_state, when_details + then_details

        children = node.get("conditions", [])
        child_results = [self._evaluate_node(profile, child) for child in children]
        states = [state for state, _ in child_results]
        details = [detail for _, detail_list in child_results for detail in detail_list]
        if label:
            details = [replace(item, branch=item.branch or label) for item in details]

        # Only retain missing answers that can still change the outcome. This is
        # the key to avoiding unnecessary questions and confusing result cards.
        if node_type == "all":
            if any(state is TriState.FAIL for state in states):
                return TriState.FAIL, [item for item in details if item.state is not TriState.UNKNOWN]
            if any(state is TriState.UNKNOWN for state in states):
                return TriState.UNKNOWN, details
            return TriState.PASS, details
        if node_type == "any":
            if any(state is TriState.PASS for state in states):
                return TriState.PASS, [item for item in details if item.state is TriState.PASS]
            if any(state is TriState.UNKNOWN for state in states):
                return TriState.UNKNOWN, details
            return TriState.FAIL, details
        raise ValueError(f"Unknown expression node type: {node_type}")

    def _evaluate_sum_compare(self, profile: ProfileSnapshot, node: dict[str, Any]) -> tuple[TriState, list[PredicateResult]]:
        left_fields = [str(item) for item in node.get("left_fields", [])]
        right_fields = [str(item) for item in node.get("right_fields", [])]
        missing = [field for field in left_fields + right_fields if profile.derived_value(field) is None]
        requirement = node.get("requirement", "Combined financial comparison")
        expected = node.get("expected_text", "The left-side total must be less than the right-side total")
        if missing:
            return TriState.UNKNOWN, [
                PredicateResult(
                    TriState.UNKNOWN,
                    field_name=field,
                    missing_field=field,
                    reason=node.get("unknown_reason", "More information is needed for this comparison."),
                    requirement=requirement,
                    expected=expected,
                    actual=f"Missing: {field.replace('_', ' ')}",
                )
                for field in missing
            ]
        left = sum(Decimal(str(profile.derived_value(field))) for field in left_fields)
        right = sum(Decimal(str(profile.derived_value(field))) for field in right_fields)
        operator = node.get("operator", "lt")
        passed = left < right if operator == "lt" else left <= right
        return (
            TriState.PASS if passed else TriState.FAIL,
            [PredicateResult(
                TriState.PASS if passed else TriState.FAIL,
                reason=node.get("pass_reason") if passed else node.get("fail_reason"),
                requirement=requirement,
                expected=expected,
                actual=node.get("actual_template", "Income/resources total: ${left}; shelter/utilities total: ${right}").format(
                    left=self._plain_number(left), right=self._plain_number(right)
                ),
            )],
        )

    def _evaluate_predicate(self, profile: ProfileSnapshot, predicate: dict[str, Any]) -> PredicateResult:
        field_name = predicate["field"]
        value = profile.derived_value(field_name)
        dependency_field = question_field_for(field_name)
        requirement = predicate.get("requirement", field_name.replace("_", " ").capitalize())
        if value is None:
            return PredicateResult(
                state=TriState.UNKNOWN,
                field_name=field_name,
                reason=predicate.get("unknown_reason", f"More information is needed about {field_name}."),
                missing_field=dependency_field,
                requirement=requirement,
                expected=self._expected_text(profile, predicate),
                actual="Not answered",
            )
        operator = predicate["operator"]
        if operator == "income_below_table":
            household_field = predicate.get("household_size_field", "household_size")
            if profile.derived_value(household_field) is None:
                return PredicateResult(
                    state=TriState.UNKNOWN,
                    field_name=household_field,
                    reason=predicate.get("household_unknown_reason", "Household size is needed for the income comparison."),
                    missing_field=household_field,
                    requirement=requirement,
                    expected="An income limit based on household size",
                    actual="Household size not answered",
                )
        expected_value = predicate.get("value")
        try:
            if operator == "equals":
                passed = value == expected_value
            elif operator == "not_equals":
                passed = value != expected_value
            elif operator == "one_of":
                passed = value in predicate.get("values", [])
            elif operator == "not_one_of":
                passed = value not in predicate.get("values", [])
            elif operator == "contains_any":
                actual = value if isinstance(value, list) else [value]
                passed = any(item in predicate.get("values", []) for item in actual)
            elif operator == "truthy":
                passed = bool(value)
            elif operator == "gte":
                passed = Decimal(str(value)) >= Decimal(str(expected_value))
            elif operator == "lte":
                passed = Decimal(str(value)) <= Decimal(str(expected_value))
            elif operator == "gt":
                passed = Decimal(str(value)) > Decimal(str(expected_value))
            elif operator == "lt":
                passed = Decimal(str(value)) < Decimal(str(expected_value))
            elif operator == "income_below_table":
                passed = self._income_below_table(profile, value, predicate)
            else:
                raise ValueError(f"Unknown predicate operator: {operator}")
        except (InvalidOperation, TypeError, ValueError):
            return PredicateResult(
                state=TriState.UNKNOWN,
                field_name=field_name,
                reason=predicate.get("unknown_reason", f"The answer for {field_name} could not be evaluated."),
                missing_field=dependency_field,
                requirement=requirement,
                expected=self._expected_text(profile, predicate),
                actual=self._display_actual(field_name, value),
            )
        return PredicateResult(
            state=TriState.PASS if passed else TriState.FAIL,
            field_name=field_name,
            reason=predicate.get("pass_reason") if passed else predicate.get("fail_reason"),
            requirement=requirement,
            expected=self._expected_text(profile, predicate),
            actual=self._display_actual(field_name, value),
        )

    def _income_limit(self, profile: ProfileSnapshot, predicate: dict[str, Any]) -> Decimal:
        household_field = predicate.get("household_size_field", "household_size")
        household_size = profile.derived_value(household_field)
        if household_size is None:
            raise ValueError("household size missing")
        size = max(1, int(household_size))
        table = {int(key): Decimal(str(value)) for key, value in predicate.get("table", {}).items()}
        if not table:
            raise ValueError("income table is empty")
        if size in table:
            return table[size]
        max_size = max(table)
        increment = Decimal(str(predicate.get("additional_member_increment", 0)))
        return table[max_size] + increment * (size - max_size)

    def _income_below_table(self, profile: ProfileSnapshot, income: Any, predicate: dict[str, Any]) -> bool:
        return Decimal(str(income)) <= self._income_limit(profile, predicate)

    def _expected_text(self, profile: ProfileSnapshot, predicate: dict[str, Any]) -> str:
        if predicate.get("expected_text"):
            return str(predicate["expected_text"])
        operator = predicate.get("operator")
        value = predicate.get("value")
        if operator == "equals":
            return self._display_value(value)
        if operator == "not_equals":
            return f"Anything except {self._display_value(value)}"
        if operator == "one_of":
            return "One of: " + ", ".join(self._display_value(item) for item in predicate.get("values", []))
        if operator == "not_one_of":
            return "Not one of: " + ", ".join(self._display_value(item) for item in predicate.get("values", []))
        if operator == "contains_any":
            return predicate.get("expected_text", "At least one listed option")
        if operator == "truthy":
            return "Yes"
        display_expected = self._display_actual(str(predicate.get("field", "")), value)
        if operator == "gte":
            return f"{display_expected} or more"
        if operator == "lte":
            return f"{display_expected} or less"
        if operator == "gt":
            return f"More than {display_expected}"
        if operator == "lt":
            return f"Less than {display_expected}"
        if operator == "income_below_table":
            try:
                limit = self._income_limit(profile, predicate)
                household_size = profile.derived_value(predicate.get("household_size_field", "household_size"))
                return f"Gross monthly income at or below ${self._plain_number(limit)} for household size {household_size}"
            except ValueError:
                return "Gross monthly income at or below the household-size limit"
        return "Program requirement"

    @staticmethod
    def _display_actual(field_name: str, value: Any) -> str:
        monetary_fields = {
            "monthly_income", "liquid_resources", "monthly_shelter_cost",
            "monthly_utility_cost",
        }
        if field_name in monetary_fields and isinstance(value, (int, float, Decimal)):
            return f"${EligibilityEngine._plain_number(Decimal(str(value)))}"
        return EligibilityEngine._display_value(value)

    @staticmethod
    def _display_value(value: Any) -> str:
        if value is True:
            return "Yes"
        if value is False:
            return "No"
        if value is None:
            return "Not answered"
        if isinstance(value, list):
            return ", ".join(str(item).replace("_", " ") for item in value) or "None selected"
        if isinstance(value, (int, float, Decimal)):
            return EligibilityEngine._plain_number(Decimal(str(value)))
        text = str(value).replace("_", " ")
        return text[:1].upper() + text[1:]

    @staticmethod
    def _plain_number(value: Decimal) -> str:
        return f"{value:,.2f}".rstrip("0").rstrip(".")
