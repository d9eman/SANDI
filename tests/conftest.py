from __future__ import annotations

import base64
import hashlib
from pathlib import Path

import pytest

from app.config import Settings


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    project_root = Path(__file__).resolve().parents[1]
    key = base64.urlsafe_b64encode(hashlib.sha256(b"test-key").digest()).decode("ascii")
    return Settings(
        base_dir=project_root,
        data_dir=tmp_path / "data",
        database_path=tmp_path / "data" / "test.sqlite3",
        vault_dir=tmp_path / "data" / "vault",
        rules_dir=project_root / "config" / "rules",
        questions_path=project_root / "config" / "questions.json",
        provider_seed_path=project_root / "config" / "provider_catalog.csv",
        session_secret="test-session-secret",
        vault_key=key,
        staff_username="staff",
        staff_password="test-password",
        provider_username="provider",
        provider_password="test-password",
        demo_mode=True,
    )
