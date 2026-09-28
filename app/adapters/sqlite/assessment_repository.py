from __future__ import annotations

import json
from typing import Any, Iterable

from app.db import Database
from app.domain.models import EligibilityAssessment
from app.ports.repositories import AssessmentRepository


class SqliteAssessmentRepository(AssessmentRepository):
    def __init__(self, database: Database):
        self.database = database

    def replace_for_profile(self, profile_id: str, assessments: Iterable[EligibilityAssessment]) -> None:
        with self.database.transaction() as connection:
            connection.execute("DELETE FROM eligibility_assessments WHERE profile_id = ?", (profile_id,))
            for assessment in assessments:
                connection.execute(
                    """
                    INSERT INTO eligibility_assessments(
                        profile_id, program_id, program_name, program_description,
                        rule_version_id, status, summary, reasons_json, requirements_json,
                        missing_fields_json, source_label, source_url, effective_from,
                        effective_to, notice, next_step, display_priority, access_score,
                        actions_json, assessed_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        profile_id,
                        assessment.program_id,
                        assessment.program_name,
                        assessment.program_description,
                        assessment.rule_version_id,
                        assessment.status.value,
                        assessment.summary,
                        json.dumps(assessment.reasons),
                        json.dumps([{
                            "state": item.state.value,
                            "field_name": item.field_name,
                            "missing_field": item.missing_field,
                            "requirement": item.requirement,
                            "expected": item.expected,
                            "actual": item.actual,
                            "reason": item.reason,
                            "branch": item.branch,
                        } for item in assessment.requirements]),
                        json.dumps(assessment.missing_fields),
                        assessment.source_label,
                        assessment.source_url,
                        assessment.effective_from,
                        assessment.effective_to,
                        assessment.notice,
                        assessment.next_step,
                        assessment.display_priority,
                        assessment.access_score,
                        json.dumps(assessment.actions),
                        assessment.assessed_at.isoformat(),
                    ),
                )

    def list_for_profile(self, profile_id: str) -> list[dict[str, Any]]:
        with self.database.connect() as connection:
            rows = connection.execute(
                "SELECT * FROM eligibility_assessments WHERE profile_id = ? ORDER BY program_name",
                (profile_id,),
            ).fetchall()
        output=[]
        for row in rows:
            item=dict(row)
            item['reasons']=json.loads(item.pop('reasons_json'))
            item['requirements']=json.loads(item.pop('requirements_json', '[]'))
            item['missing_fields']=json.loads(item.pop('missing_fields_json'))
            item['actions']=json.loads(item.pop('actions_json', '[]'))
            output.append(item)
        return output
