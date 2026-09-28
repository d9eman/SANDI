from __future__ import annotations

from typing import Any

from fastapi import Request
from fastapi.templating import Jinja2Templates

from app.security.web import active_profile_id, csrf_token


STATUS_LABELS = {
    "DIRECT_RESOURCE": "Available to everyone",
    "LIKELY_ELIGIBLE": "Strong match",
    "MAY_QUALIFY": "May qualify",
    "NEEDS_INFORMATION": "More information needed",
    "LIKELY_NOT_ELIGIBLE": "Likely not eligible",
    "RULE_UNDER_REVIEW": "Screening update",
}


def render(templates: Jinja2Templates, request: Request, name: str, context: dict[str, Any] | None = None, status_code: int = 200):
    base = {
        "request": request,
        "csrf_token": csrf_token(request),
        "demo_mode": request.app.state.container.settings.demo_mode,
        "current_profile_id": active_profile_id(request),
        "provider_logged_in": bool(request.session.get("provider_actor")),
        "staff_logged_in": bool(request.session.get("staff_actor")),
        "status_labels": STATUS_LABELS,
    }
    base.update(context or {})
    return templates.TemplateResponse(request=request, name=name, context=base, status_code=status_code)
