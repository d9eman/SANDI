"""Composition root for public web routes.

Routes are split by user concern so new contributors can change food, profiles,
screening, referrals, or documents without navigating one large controller.
This module preserves the import used by ``app.main``.
"""

from fastapi import APIRouter
from fastapi.templating import Jinja2Templates

from . import document_routes, home_routes, profile_routes, referral_routes, screening_routes
from .public_context import set_templates


router = APIRouter()
router.include_router(home_routes.router)
router.include_router(profile_routes.router)
router.include_router(screening_routes.router)
router.include_router(referral_routes.router)
router.include_router(document_routes.router)


def setup_templates(value: Jinja2Templates) -> None:
    set_templates(value)
