from __future__ import annotations

import math
from typing import Any

from app.domain.models import Question


def parse_question_answer(
    question: Question,
    raw_value: str | None,
    raw_values: list[str] | None = None,
) -> Any:
    """Validate and normalize one answer before it enters the profile domain.

    This parser is intentionally independent from FastAPI. Web forms, SMS, or a
    future RAG conversation adapter can all normalize answers through the same
    rules instead of re-implementing question validation in each channel.
    """
    if question.question_id == "zip_code":
        value = "".join(character for character in str(raw_value or "") if character.isdigit())[:5]
        if len(value) != 5:
            raise ValueError("Enter a five-digit ZIP code, or choose I do not know / Skip.")
        return value

    if question.answer_type == "number":
        if raw_value in (None, ""):
            raise ValueError("Enter a number or choose I do not know / Skip.")
        value = float(raw_value)
        if not math.isfinite(value) or value < 0:
            raise ValueError("Enter zero or a positive finite number.")
        return int(value) if value.is_integer() else value

    allowed = {str(option.get("value")) for option in question.options}
    if question.answer_type == "single_select":
        if raw_value not in allowed:
            raise ValueError("Choose one of the listed answers, or choose I do not know / Skip.")
        return raw_value

    if question.answer_type == "multi_select":
        values = raw_values or []
        if any(value not in allowed for value in values):
            raise ValueError("One or more selected answers are not valid for this question.")
        return values

    if question.answer_type == "text":
        value = str(raw_value or "").strip()
        if not value:
            raise ValueError("Enter an answer or choose I do not know / Skip.")
        return value[:500]

    return raw_value
