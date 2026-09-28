from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

from app.domain.eligibility import ProgramRuleVersion
from app.domain.enums import EligibilityStatus
from app.domain.models import Question
from app.ports.repositories import RuleRepository


class JsonRuleRepository(RuleRepository):
    """Loads versioned, source-linked rule definitions from JSON files."""

    def __init__(self, rules_dir: Path, questions_path: Path):
        self.rules_dir = rules_dir
        self.questions_path = questions_path

    def active_rules(self, on_date: date | None = None) -> list[ProgramRuleVersion]:
        target = on_date or date.today()
        rules: list[ProgramRuleVersion] = []
        for path in sorted(self.rules_dir.glob("*.json")):
            payload = json.loads(path.read_text(encoding="utf-8"))
            program = payload["program"]
            versions = payload.get("versions", [])
            version = self._select_version(versions, target)
            if version is None and versions:
                # Return the most recent rule definition; the engine will mark it under review.
                version = sorted(versions, key=lambda item: item["effective_from"])[-1]
            if version is None:
                continue
            rules.append(
                ProgramRuleVersion(
                    program_id=program["id"],
                    program_name=program["name"],
                    program_description=program.get("description", ""),
                    rule_version_id=version["id"],
                    effective_from=version["effective_from"],
                    effective_to=version.get("effective_to"),
                    review_due=version.get("review_due"),
                    source_label=version.get("source_label", "Source not recorded"),
                    source_url=version.get("source_url", ""),
                    notice=version.get("notice", "Pre-screen only."),
                    pass_status=EligibilityStatus(version["pass_status"]),
                    unknown_status=EligibilityStatus(version["unknown_status"]),
                    fail_status=EligibilityStatus(version["fail_status"]),
                    expression=version["expression"],
                    next_steps=version.get("next_steps", {}),
                    result_summaries=version.get("result_summaries", {}),
                    display_priority=int(program.get("display_priority", 100)),
                    access_score=int(program.get("access_score", 50)),
                    actions=tuple(program.get("actions", [])),
                )
            )
        return rules

    def questions(self) -> dict[str, Question]:
        payload = json.loads(self.questions_path.read_text(encoding="utf-8"))
        output: dict[str, Question] = {}
        for item in payload["questions"]:
            output[item["id"]] = Question(
                question_id=item["id"],
                text_en=item["text_en"],
                text_es=item.get("text_es", ""),
                help_en=item.get("help_en", ""),
                help_es=item.get("help_es", ""),
                answer_type=item["answer_type"],
                options=tuple(item.get("options", [])),
                sensitivity=int(item.get("sensitivity", 1)),
                priority=int(item.get("priority", 100)),
                stage=item.get("stage", ""),
                group=item.get("group", ""),
                why_asked=item.get("why_asked", ""),
                conditional_note=item.get("conditional_note", ""),
                source_refs=tuple(item.get("source_refs", [])),
                placeholder=item.get("placeholder", ""),
                unit=item.get("unit", ""),
                ask_after=tuple(item.get("ask_after", [])),
            )
        return output

    @staticmethod
    def _select_version(versions: list[dict[str, Any]], target: date) -> dict[str, Any] | None:
        candidates = []
        for version in versions:
            start = date.fromisoformat(version["effective_from"])
            end = date.fromisoformat(version["effective_to"]) if version.get("effective_to") else None
            if start <= target and (end is None or target <= end):
                candidates.append(version)
        if not candidates:
            return None
        return sorted(candidates, key=lambda item: item["effective_from"])[-1]
