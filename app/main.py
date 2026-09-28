from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from app.bootstrap import build_container
from app.config import Settings
from app.presentation.web import provider_routes, public_routes, staff_routes


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved_settings = settings or Settings.from_env()
    container = build_container(resolved_settings)

    app = FastAPI(
        title="SANDI Food and Eligibility Demo",
        description="Separate immediate-food navigation and low-barrier, explainable multi-program eligibility screening.",
        version="0.4.4",
    )
    app.state.container = container
    app.add_middleware(
        SessionMiddleware,
        secret_key=resolved_settings.session_secret,
        same_site="lax",
        https_only=False,  # set True behind HTTPS in deployment
        max_age=60 * 60 * 24 * 30,
    )

    web_dir = resolved_settings.base_dir / "app" / "presentation" / "web"
    templates = Jinja2Templates(directory=str(web_dir / "templates"))
    public_routes.setup_templates(templates)
    provider_routes.setup_templates(templates)
    staff_routes.setup_templates(templates)

    app.mount("/static", StaticFiles(directory=str(web_dir / "static")), name="static")
    app.include_router(public_routes.router)
    app.include_router(provider_routes.router)
    app.include_router(staff_routes.router)

    @app.get("/health")
    def health():
        return {"status": "ok", "demo_mode": resolved_settings.demo_mode}

    return app


app = create_app()
