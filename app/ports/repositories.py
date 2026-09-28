from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date
from typing import Any, Iterable

from app.domain.eligibility import ProgramRuleVersion
from app.domain.models import EligibilityAssessment, ProfileSnapshot, Question, ReferralTicket


class ProfileRepository(ABC):
    @abstractmethod
    def create(self, profile_id: str, language: str, recovery_hash: str) -> None: ...

    @abstractmethod
    def get(self, profile_id: str) -> ProfileSnapshot | None: ...

    @abstractmethod
    def recovery_hash(self, profile_id: str) -> str | None: ...

    @abstractmethod
    def save_answer(self, profile_id: str, question_id: str, state: str, value: Any) -> None: ...

    @abstractmethod
    def list_recent(self, limit: int = 50) -> list[dict[str, Any]]: ...


class RuleRepository(ABC):
    @abstractmethod
    def active_rules(self, on_date: date | None = None) -> list[ProgramRuleVersion]: ...

    @abstractmethod
    def questions(self) -> dict[str, Question]: ...


class AssessmentRepository(ABC):
    @abstractmethod
    def replace_for_profile(self, profile_id: str, assessments: Iterable[EligibilityAssessment]) -> None: ...

    @abstractmethod
    def list_for_profile(self, profile_id: str) -> list[dict[str, Any]]: ...


class ResourceRepository(ABC):
    @abstractmethod
    def search_food(
        self,
        zip_code: str | None,
        journey_stage: str | None = None,
        limit: int = 30,
    ) -> list[dict[str, Any]]: ...

    @abstractmethod
    def get_public_service(self, service_id: str) -> dict[str, Any] | None: ...

    @abstractmethod
    def get_service_identity(self, service_id: str) -> dict[str, Any] | None: ...

    @abstractmethod
    def list_providers(self) -> list[dict[str, Any]]: ...

    @abstractmethod
    def upsert_provider_record(self, record: dict[str, Any]) -> None: ...

    @abstractmethod
    def add_availability(self, service_id: str, status: str, visibility: str, details: str, source: str) -> None: ...

    @abstractmethod
    def record_interaction(
        self,
        visitor_id: str,
        profile_id: str | None,
        service_id: str | None,
        action: str,
        location_text: str = "",
        outcome: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> None: ...


class ReferralRepository(ABC):
    @abstractmethod
    def create(self, values: dict[str, Any]) -> ReferralTicket: ...

    @abstractmethod
    def get(self, ticket_id: str) -> ReferralTicket | None: ...

    @abstractmethod
    def list_for_profile(self, profile_id: str) -> list[dict[str, Any]]: ...

    @abstractmethod
    def list_for_provider(self, provider_id: str | None = None) -> list[dict[str, Any]]: ...

    @abstractmethod
    def transition(self, ticket_id: str, target_state: str, actor_type: str, actor_id: str, note: str = "", scheduled_for: str | None = None, outcome: str | None = None, decline_reason: str | None = None) -> ReferralTicket: ...


class DocumentMetadataRepository(ABC):
    @abstractmethod
    def create(self, values: dict[str, Any]) -> str: ...

    @abstractmethod
    def get(self, document_id: str) -> dict[str, Any] | None: ...

    @abstractmethod
    def list_for_profile(self, profile_id: str) -> list[dict[str, Any]]: ...

    @abstractmethod
    def mark_deleted(self, document_id: str) -> None: ...


class AuditRepository(ABC):
    @abstractmethod
    def record(self, actor_type: str, actor_id: str, action: str, target_type: str, target_id: str, purpose: str, outcome: str, metadata: dict[str, Any] | None = None) -> None: ...

    @abstractmethod
    def metrics(self) -> dict[str, Any]: ...
