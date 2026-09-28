from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from .enums import AnswerState, EligibilityStatus, ReferralState, TriState
from .fields import derived_value


@dataclass(frozen=True)
class Answer:
    question_id: str
    state: AnswerState
    value: Any = None


@dataclass
class ProfileSnapshot:
    profile_id: str
    language: str
    created_at: datetime
    answers: dict[str, Answer] = field(default_factory=dict)

    def answer(self, field_name: str) -> Answer | None:
        return self.answers.get(field_name)

    def value(self, field_name: str) -> Any | None:
        answer = self.answer(field_name)
        if answer is None or answer.state is not AnswerState.KNOWN:
            return None
        return answer.value

    def has_answered(self, field_name: str) -> bool:
        return field_name in self.answers

    def derived_value(self, field_name: str) -> Any | None:
        direct = self.value(field_name)
        return direct if direct is not None else derived_value(field_name, self.value)


@dataclass(frozen=True)
class PredicateResult:
    """One explainable requirement evaluation.

    `expected` and `actual` are deliberately stored separately so a user can
    see the gap instead of receiving only a generic pass/fail sentence.
    """

    state: TriState
    field_name: str | None = None
    reason: str | None = None
    missing_field: str | None = None
    requirement: str = ""
    expected: str = ""
    actual: str = ""
    branch: str = ""


@dataclass(frozen=True)
class EligibilityAssessment:
    program_id: str
    program_name: str
    program_description: str
    rule_version_id: str
    status: EligibilityStatus
    summary: str
    reasons: tuple[str, ...]
    requirements: tuple[PredicateResult, ...]
    missing_fields: tuple[str, ...]
    source_label: str
    source_url: str
    effective_from: str
    effective_to: str | None
    notice: str
    next_step: str
    display_priority: int
    access_score: int
    actions: tuple[dict[str, Any], ...]
    assessed_at: datetime


@dataclass(frozen=True)
class Question:
    question_id: str
    text_en: str
    text_es: str
    help_en: str
    help_es: str
    answer_type: str
    options: tuple[dict[str, Any], ...]
    sensitivity: int
    priority: int
    stage: str = ""
    group: str = ""
    why_asked: str = ""
    conditional_note: str = ""
    source_refs: tuple[str, ...] = ()
    placeholder: str = ""
    unit: str = ""
    ask_after: tuple[str, ...] = ()

    def text(self, language: str) -> str:
        return self.text_es if language == "es" and self.text_es else self.text_en

    def help_text(self, language: str) -> str:
        return self.help_es if language == "es" and self.help_es else self.help_en


@dataclass(frozen=True)
class ReferralTicket:
    ticket_id: str
    profile_id: str
    provider_id: str | None
    service_id: str | None
    need_type: str
    urgency: str
    zip_code: str | None
    state: ReferralState
    scheduled_for: str | None
    outcome: str | None
    decline_reason: str | None
    created_at: datetime
    updated_at: datetime
