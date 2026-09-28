from __future__ import annotations

import secrets
from typing import Any

from app.domain.enums import AnswerState
from app.domain.models import ProfileSnapshot
from app.ports.repositories import AuditRepository, ProfileRepository
from app.security.recovery import generate_recovery_phrase, hash_recovery_phrase, verify_recovery_phrase


class ProfileService:
    def __init__(self, profiles: ProfileRepository, audit: AuditRepository):
        self.profiles = profiles
        self.audit = audit

    def create_guest(self, language: str = "en") -> tuple[ProfileSnapshot, str]:
        profile_id = f"SAN-{secrets.token_hex(4).upper()}"
        recovery_phrase = generate_recovery_phrase()
        self.profiles.create(profile_id, language if language in {"en", "es"} else "en", hash_recovery_phrase(recovery_phrase))
        profile = self.require(profile_id)
        self.audit.record("user", profile_id, "create", "profile", profile_id, "guest profile creation", "success")
        return profile, recovery_phrase

    def authenticate(self, profile_id: str, recovery_phrase: str) -> bool:
        encoded = self.profiles.recovery_hash(profile_id.strip().upper())
        success = bool(encoded and verify_recovery_phrase(recovery_phrase, encoded))
        self.audit.record(
            "user",
            profile_id.strip().upper(),
            "authenticate",
            "profile",
            profile_id.strip().upper(),
            "resume saved profile",
            "success" if success else "denied",
        )
        return success

    def require(self, profile_id: str) -> ProfileSnapshot:
        profile = self.profiles.get(profile_id)
        if profile is None:
            raise KeyError(profile_id)
        return profile

    def save_answer(self, profile_id: str, question_id: str, state: AnswerState, value: Any = None) -> ProfileSnapshot:
        if state is not AnswerState.KNOWN:
            value = None
        self.profiles.save_answer(profile_id, question_id, state.value, value)
        self.audit.record(
            "user",
            profile_id,
            "update_answer",
            "profile",
            profile_id,
            "progressive eligibility screening",
            "success",
            {"question_id": question_id, "answer_state": state.value},
        )
        return self.require(profile_id)
