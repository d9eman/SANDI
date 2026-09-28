from __future__ import annotations

import base64
import hashlib
import os
from dataclasses import dataclass
from pathlib import Path

from cryptography.fernet import Fernet
from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    """Runtime configuration.

    The demo defaults are intentionally convenient for local testing. Replace every
    secret and move to managed services before using real personal information.
    """

    base_dir: Path
    data_dir: Path
    database_path: Path
    vault_dir: Path
    rules_dir: Path
    questions_path: Path
    provider_seed_path: Path
    session_secret: str
    vault_key: str
    staff_username: str
    staff_password: str
    provider_username: str
    provider_password: str
    max_upload_bytes: int = 5 * 1024 * 1024
    demo_mode: bool = True

    @classmethod
    def from_env(cls, base_dir: Path | None = None) -> "Settings":
        load_dotenv()
        resolved_base = (base_dir or Path(__file__).resolve().parents[1]).resolve()
        data_dir = Path(os.getenv("SANDI_DATA_DIR", resolved_base / "data")).resolve()
        session_secret = os.getenv("SANDI_SESSION_SECRET", "change-this-demo-session-secret")
        vault_key = os.getenv("SANDI_VAULT_KEY")
        if not vault_key:
            digest = hashlib.sha256(session_secret.encode("utf-8")).digest()
            vault_key = base64.urlsafe_b64encode(digest).decode("ascii")
        Fernet(vault_key.encode("ascii"))  # fail fast if malformed
        return cls(
            base_dir=resolved_base,
            data_dir=data_dir,
            database_path=Path(os.getenv("SANDI_DATABASE_PATH", data_dir / "sandi_demo.sqlite3")).resolve(),
            vault_dir=Path(os.getenv("SANDI_VAULT_DIR", data_dir / "vault")).resolve(),
            rules_dir=Path(os.getenv("SANDI_RULES_DIR", resolved_base / "config" / "rules")).resolve(),
            questions_path=Path(os.getenv("SANDI_QUESTIONS_PATH", resolved_base / "config" / "questions.json")).resolve(),
            provider_seed_path=Path(os.getenv("SANDI_PROVIDER_SEED", resolved_base / "config" / "provider_catalog.csv")).resolve(),
            session_secret=session_secret,
            vault_key=vault_key,
            staff_username=os.getenv("SANDI_STAFF_USERNAME", "staff"),
            staff_password=os.getenv("SANDI_STAFF_PASSWORD", "sandi-demo"),
            provider_username=os.getenv("SANDI_PROVIDER_USERNAME", "provider"),
            provider_password=os.getenv("SANDI_PROVIDER_PASSWORD", "sandi-demo"),
            max_upload_bytes=int(os.getenv("SANDI_MAX_UPLOAD_BYTES", str(5 * 1024 * 1024))),
            demo_mode=os.getenv("SANDI_DEMO_MODE", "true").lower() in {"1", "true", "yes", "y"},
        )

    def prepare_directories(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.vault_dir.mkdir(parents=True, exist_ok=True)
