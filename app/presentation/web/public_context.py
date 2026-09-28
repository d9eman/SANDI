from __future__ import annotations

import math
import uuid
from typing import Any

from fastapi import Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from .helpers import render


_templates: Jinja2Templates | None = None


def set_templates(value: Jinja2Templates) -> None:
    global _templates
    _templates = value


def render_page(
    request: Request,
    name: str,
    context: dict[str, Any] | None = None,
    status_code: int = 200,
):
    if _templates is None:
        raise RuntimeError("Public templates have not been configured.")
    return render(_templates, request, name, context, status_code)


def container(request: Request):
    return request.app.state.container


def redirect(url: str) -> RedirectResponse:
    return RedirectResponse(url=url, status_code=303)


def visitor_id(request: Request) -> str:
    """Return a random browser-session identifier without requiring a profile."""
    value = request.session.get("visitor_id")
    if not value:
        value = f"VIS-{uuid.uuid4().hex[:16].upper()}"
        request.session["visitor_id"] = value
    return str(value)


def safe_float(value: str | None) -> float | None:
    if value in (None, ""):
        return None
    try:
        number = float(value)
        return number if math.isfinite(number) else None
    except (TypeError, ValueError):
        return None
