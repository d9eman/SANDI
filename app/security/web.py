from __future__ import annotations

import secrets

from fastapi import HTTPException, Request, status


class CsrfError(HTTPException):
    def __init__(self) -> None:
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid or expired form token.")


def csrf_token(request: Request) -> str:
    token = request.session.get("csrf_token")
    if not token:
        token = secrets.token_urlsafe(24)
        request.session["csrf_token"] = token
    return token


def verify_csrf(request: Request, submitted: str) -> None:
    expected = request.session.get("csrf_token", "")
    if not expected or not secrets.compare_digest(expected, submitted or ""):
        raise CsrfError()


def clear_profile_session(request: Request) -> None:
    """Remove only user-profile state while preserving anonymous and staff/provider sessions."""
    for key in (
        "profile_id",
        "recovery_phrase_once",
        "new_match_programs",
        "return_after_emergency",
    ):
        request.session.pop(key, None)


def active_profile_id(request: Request) -> str | None:
    """Return the current profile only when it still exists in the active database.

    Browser session cookies can outlive a local demo database.  Without this
    check, a cookie from an earlier installation can point to a profile that no
    longer exists and cause foreign-key or KeyError failures.
    """
    raw = request.session.get("profile_id")
    if not raw:
        return None
    profile_id = str(raw).strip().upper()
    repository = request.app.state.container.profile_repository
    if repository.get(profile_id) is None:
        clear_profile_session(request)
        return None
    if raw != profile_id:
        request.session["profile_id"] = profile_id
    return profile_id


def authorize_profile(request: Request, profile_id: str) -> None:
    requested = profile_id.strip().upper()
    current = active_profile_id(request)
    if current is None:
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            detail="That saved profile is not available in this installation.",
            headers={"Location": "/profile/start?notice=profile_not_found"},
        )
    if current != requested:
        raise HTTPException(status_code=403, detail="Open this profile with its recovery phrase first.")


def verify_credentials(username: str, password: str, expected_username: str, expected_password: str) -> bool:
    return secrets.compare_digest(username or "", expected_username) and secrets.compare_digest(password or "", expected_password)


def login_role(request: Request, role: str, actor: str) -> None:
    request.session[f"{role}_actor"] = actor


def logout_role(request: Request, role: str) -> None:
    request.session.pop(f"{role}_actor", None)


def require_role(request: Request, role: str, login_path: str) -> str:
    actor = request.session.get(f"{role}_actor")
    if not actor:
        raise HTTPException(status_code=303, detail="Login required.", headers={"Location": login_path})
    return str(actor)
