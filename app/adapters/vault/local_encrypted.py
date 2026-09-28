from __future__ import annotations

import uuid
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken

from app.ports.services import SecureObjectStore


class LocalEncryptedObjectStore(SecureObjectStore):
    """Encrypted local object store for the demo.

    Files are stored under random names and cannot be served directly by the web
    server. Production should replace this with private cloud object storage and
    managed encryption keys.
    """

    def __init__(self, directory: Path, key: str):
        self.directory = directory
        self.directory.mkdir(parents=True, exist_ok=True)
        self.fernet = Fernet(key.encode("ascii"))

    def put(self, plaintext: bytes) -> str:
        object_ref = f"{uuid.uuid4().hex}.vault"
        (self.directory / object_ref).write_bytes(self.fernet.encrypt(plaintext))
        return object_ref

    def get(self, object_ref: str) -> bytes:
        path = self._safe_path(object_ref)
        try:
            return self.fernet.decrypt(path.read_bytes())
        except InvalidToken as exc:
            raise ValueError("Stored document could not be decrypted.") from exc

    def delete(self, object_ref: str) -> None:
        path = self._safe_path(object_ref)
        path.unlink(missing_ok=True)

    def _safe_path(self, object_ref: str) -> Path:
        if Path(object_ref).name != object_ref or not object_ref.endswith(".vault"):
            raise ValueError("Invalid object reference.")
        return self.directory / object_ref
