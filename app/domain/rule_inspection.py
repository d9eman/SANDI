from __future__ import annotations
from typing import Any

from .fields import question_field_for

def collect_fields(node: dict[str, Any]) -> set[str]:
    """Return every raw or derived field referenced by a rule expression."""
    fields: set[str] = set()
    if node.get("field"):
        fields.add(str(node["field"]))
    for field in node.get("left_fields", []): fields.add(str(field))
    for field in node.get("right_fields", []): fields.add(str(field))
    if isinstance(node.get("when"), dict): fields.update(collect_fields(node["when"]))
    if isinstance(node.get("then"), dict): fields.update(collect_fields(node["then"]))
    for child in node.get("conditions", []): fields.update(collect_fields(child))
    return fields

def collect_question_fields(node: dict[str, Any]) -> set[str]:
    """Return the stored question IDs needed to supply a rule's fields."""
    return {question_field_for(field) for field in collect_fields(node)}
