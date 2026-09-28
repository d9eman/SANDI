from __future__ import annotations

from collections import Counter, defaultdict

from app.domain.eligibility import EligibilityEngine
from app.domain.enums import ACTIONABLE_STATUSES, EligibilityStatus
from app.domain.models import EligibilityAssessment, ProfileSnapshot, Question
from app.ports.repositories import AssessmentRepository, RuleRepository


STATUS_ORDER = {
    EligibilityStatus.DIRECT_RESOURCE: 0,
    EligibilityStatus.LIKELY_ELIGIBLE: 1,
    EligibilityStatus.MAY_QUALIFY: 2,
    EligibilityStatus.NEEDS_INFORMATION: 3,
    EligibilityStatus.RULE_UNDER_REVIEW: 4,
    EligibilityStatus.LIKELY_NOT_ELIGIBLE: 5,
}

class ScreeningService:
    def __init__(self, rules: RuleRepository, assessments: AssessmentRepository, engine: EligibilityEngine):
        self.rules = rules
        self.assessments = assessments
        self.engine = engine

    def evaluate(self, profile: ProfileSnapshot) -> list[EligibilityAssessment]:
        output = [self.engine.evaluate(profile, rule) for rule in self.rules.active_rules()]
        output = self.sort_assessments(output)
        self.assessments.replace_for_profile(profile.profile_id, output)
        return output

    @staticmethod
    def sort_assessments(assessments: list[EligibilityAssessment]) -> list[EligibilityAssessment]:
        """Best/easiest matches first, hard failures last."""
        return sorted(
            assessments,
            key=lambda item: (
                STATUS_ORDER[item.status],
                item.display_priority,
                -item.access_score,
                item.program_name,
            ),
        )

    def _question_candidates(
        self,
        profile: ProfileSnapshot,
        assessments: list[EligibilityAssessment],
    ) -> tuple[Counter[str], dict[str, Question]]:
        """Return unresolved question impact without duplicating planner logic."""
        active_rules = {rule.program_id: rule for rule in self.rules.active_rules()}
        impact: Counter[str] = Counter()
        for assessment in assessments:
            rule = active_rules.get(assessment.program_id)
            weight = rule.question_weight if rule else 1
            for field in assessment.missing_fields:
                impact[field] += weight

        questions = self.rules.questions()
        candidates = {
            field: questions[field]
            for field in impact
            if field in questions
            and not profile.has_answered(field)
            and all(profile.has_answered(dependency) for dependency in questions[field].ask_after)
        }
        return impact, candidates

    def next_question(self, profile: ProfileSnapshot, assessments: list[EligibilityAssessment]) -> Question | None:
        """Ask the question that unlocks the most useful programs with least burden.

        The eligibility engine only reports missing fields that can still change a
        result. This planner then weights those fields by program priority and
        accessibility before considering question sensitivity and configured order.
        Unknown and skipped answers are preserved and never immediately repeated.
        """
        impact, candidates = self._question_candidates(profile, assessments)
        if not candidates:
            return None

        def value_score(question: Question) -> int:
            # High program impact matters, but each sensitivity level carries a
            # meaningful burden penalty so a single narrow branch does not jump
            # ahead of easier shared questions.
            return impact[question.question_id] - (question.sensitivity * 60)

        return sorted(
            candidates.values(),
            key=lambda question: (
                -value_score(question),
                question.priority,
                question.sensitivity,
                question.question_id,
            ),
        )[0]

    def progress_summary(self, profile: ProfileSnapshot, assessments: list[EligibilityAssessment]) -> dict[str, int]:
        """Compact, honest progress signal for the adaptive questionnaire.

        There is no fixed questionnaire length: irrelevant branches disappear as
        answers arrive. The denominator therefore uses answers already saved plus
        questions that can *currently* change an active result. This makes the UI
        satisfying without pretending the user must complete a fixed form.
        """
        questions = self.rules.questions()
        answered = sum(1 for key in profile.answers if key in questions)
        _, candidates = self._question_candidates(profile, assessments)
        remaining = len(candidates)
        total = answered + remaining
        percent = 100 if total == 0 and answered else (round((answered / total) * 100) if total else 0)
        program_assessments = [item for item in assessments if item.program_id != "direct_food"]
        strong = sum(item.status is EligibilityStatus.LIKELY_ELIGIBLE for item in program_assessments)
        possible = sum(
            item.status in {EligibilityStatus.MAY_QUALIFY, EligibilityStatus.NEEDS_INFORMATION}
            for item in program_assessments
        )
        resolved = sum(
            item.status in {EligibilityStatus.LIKELY_ELIGIBLE, EligibilityStatus.LIKELY_NOT_ELIGIBLE}
            for item in program_assessments
        )
        return {
            "answered": answered,
            "remaining": remaining,
            "percent": percent,
            "strong_matches": strong,
            "possible_matches": possible,
            "resolved_programs": resolved,
            "program_count": len(program_assessments),
        }

    def question(self, question_id: str) -> Question:
        questions = self.rules.questions()
        if question_id not in questions:
            raise KeyError(question_id)
        return questions[question_id]

    @staticmethod
    def newly_actionable(
        before: list[EligibilityAssessment],
        after: list[EligibilityAssessment],
    ) -> list[EligibilityAssessment]:
        previous = {item.program_id: item.status for item in before}
        return [
            item
            for item in after
            if item.status in ACTIONABLE_STATUSES
            and item.program_id != "direct_food"
            and previous.get(item.program_id) not in ACTIONABLE_STATUSES
        ]
