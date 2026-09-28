from __future__ import annotations

import csv
import io
import json
from typing import Any, Iterable

from app.domain.eligibility import ProgramRuleVersion
from app.domain.models import Question
from app.domain.fields import question_field_for


MATRIX_COLUMNS = [
    "program_id",
    "program_name",
    "rule_version_id",
    "display_priority",
    "access_score",
    "branch",
    "logic_group",
    "requirement",
    "rule_field",
    "question_id",
    "question_text",
    "answer_type",
    "operator",
    "expected",
    "pass_reason",
    "fail_reason",
    "unknown_reason",
    "pass_status",
    "unknown_status",
    "fail_status",
    "effective_from",
    "effective_to",
    "review_due",
    "source_label",
    "source_url",
    "actions",
]


def _expected(node: dict[str, Any]) -> str:
    if node.get("expected_text"):
        return str(node["expected_text"])
    operator = node.get("operator", "")
    if operator in {"equals", "not_equals", "gte", "lte", "gt", "lt"}:
        return json.dumps(node.get("value"), ensure_ascii=False)
    if operator in {"one_of", "not_one_of", "contains_any"}:
        return json.dumps(node.get("values", []), ensure_ascii=False)
    if operator == "income_below_table":
        return json.dumps(
            {
                "household_size_field": node.get("household_size_field", "household_size"),
                "table": node.get("table", {}),
                "additional_member_increment": node.get("additional_member_increment", 0),
            },
            ensure_ascii=False,
        )
    return ""


def requirement_rows(rule: ProgramRuleVersion, questions: dict[str, Question]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    actions = "; ".join(str(action.get("label") or action.get("service_id") or action.get("url")) for action in rule.actions)

    def add(node: dict[str, Any], branch: str, logic_group: str) -> None:
        node_type = node.get("type")
        current_branch = str(node.get("label") or branch)
        if node_type == "predicate":
            field = str(node.get("field", ""))
            question_id = question_field_for(field)
            question = questions.get(question_id)
            rows.append({
                "program_id": rule.program_id,
                "program_name": rule.program_name,
                "rule_version_id": rule.rule_version_id,
                "display_priority": rule.display_priority,
                "access_score": rule.access_score,
                "branch": current_branch,
                "logic_group": logic_group,
                "requirement": node.get("requirement", field.replace("_", " ").title()),
                "rule_field": field,
                "question_id": question_id,
                "question_text": question.text_en if question else "Derived/system field",
                "answer_type": question.answer_type if question else "derived",
                "operator": node.get("operator", ""),
                "expected": _expected(node),
                "pass_reason": node.get("pass_reason", ""),
                "fail_reason": node.get("fail_reason", ""),
                "unknown_reason": node.get("unknown_reason", ""),
                "pass_status": rule.pass_status.value,
                "unknown_status": rule.unknown_status.value,
                "fail_status": rule.fail_status.value,
                "effective_from": rule.effective_from,
                "effective_to": rule.effective_to or "",
                "review_due": rule.review_due or "",
                "source_label": rule.source_label,
                "source_url": rule.source_url,
                "actions": actions,
            })
            return
        if node_type == "sum_compare":
            fields = [str(item) for item in node.get("left_fields", []) + node.get("right_fields", [])]
            question_ids = [question_field_for(field) for field in fields]
            rows.append({
                "program_id": rule.program_id,
                "program_name": rule.program_name,
                "rule_version_id": rule.rule_version_id,
                "display_priority": rule.display_priority,
                "access_score": rule.access_score,
                "branch": current_branch,
                "logic_group": logic_group,
                "requirement": node.get("requirement", "Combined comparison"),
                "rule_field": ";".join(fields),
                "question_id": ";".join(question_ids),
                "question_text": "; ".join(questions[q].text_en if q in questions else q for q in question_ids),
                "answer_type": "calculated",
                "operator": node.get("operator", ""),
                "expected": node.get("expected_text", ""),
                "pass_reason": node.get("pass_reason", ""),
                "fail_reason": node.get("fail_reason", ""),
                "unknown_reason": node.get("unknown_reason", ""),
                "pass_status": rule.pass_status.value,
                "unknown_status": rule.unknown_status.value,
                "fail_status": rule.fail_status.value,
                "effective_from": rule.effective_from,
                "effective_to": rule.effective_to or "",
                "review_due": rule.review_due or "",
                "source_label": rule.source_label,
                "source_url": rule.source_url,
                "actions": actions,
            })
            return
        if node_type == "always":
            rows.append({
                "program_id": rule.program_id,
                "program_name": rule.program_name,
                "rule_version_id": rule.rule_version_id,
                "display_priority": rule.display_priority,
                "access_score": rule.access_score,
                "branch": current_branch,
                "logic_group": logic_group,
                "requirement": node.get("requirement", "No formal eligibility screen"),
                "rule_field": "",
                "question_id": "",
                "question_text": "No question required",
                "answer_type": "none",
                "operator": "always",
                "expected": node.get("expected_text", "Available to everyone"),
                "pass_reason": node.get("pass_reason", ""),
                "fail_reason": "",
                "unknown_reason": "",
                "pass_status": rule.pass_status.value,
                "unknown_status": rule.unknown_status.value,
                "fail_status": rule.fail_status.value,
                "effective_from": rule.effective_from,
                "effective_to": rule.effective_to or "",
                "review_due": rule.review_due or "",
                "source_label": rule.source_label,
                "source_url": rule.source_url,
                "actions": actions,
            })
            return
        if node_type == "if_then":
            add(node["when"], current_branch, "IF")
            add(node["then"], current_branch, "THEN")
            return
        if node_type in {"all", "any"}:
            group = "ALL requirements" if node_type == "all" else "AT LEAST ONE route"
            for child in node.get("conditions", []):
                add(child, current_branch, group)

    add(rule.expression, "", "")
    return rows


def all_requirement_rows(rules: Iterable[ProgramRuleVersion], questions: dict[str, Question]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for rule in rules:
        rows.extend(requirement_rows(rule, questions))
    return rows


def requirement_matrix_csv(rules: Iterable[ProgramRuleVersion], questions: dict[str, Question]) -> str:
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=MATRIX_COLUMNS, extrasaction="ignore", lineterminator="\n")
    writer.writeheader()
    writer.writerows(all_requirement_rows(rules, questions))
    return output.getvalue()
