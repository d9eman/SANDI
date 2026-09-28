from __future__ import annotations

import mimetypes
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from app.ports.repositories import AuditRepository, DocumentMetadataRepository
from app.ports.services import SecureObjectStore


class DocumentValidationError(ValueError):
    pass


class DocumentService:
    _allowed = {
        "application/pdf": b"%PDF-",
        "image/png": b"\x89PNG\r\n\x1a\n",
        "image/jpeg": b"\xff\xd8\xff",
    }

    def __init__(
        self,
        metadata: DocumentMetadataRepository,
        vault: SecureObjectStore,
        audit: AuditRepository,
        signing_secret: str,
        max_upload_bytes: int,
    ):
        self.metadata = metadata
        self.vault = vault
        self.audit = audit
        self.serializer = URLSafeTimedSerializer(signing_secret, salt="sandi-document-download")
        self.max_upload_bytes = max_upload_bytes

    def upload(self, profile_id: str, filename: str, content_type: str | None, content: bytes, document_type: str, purpose: str) -> str:
        if not content or len(content) > self.max_upload_bytes:
            raise DocumentValidationError(f"File must be between 1 byte and {self.max_upload_bytes // (1024*1024)} MB.")
        mime = content_type or mimetypes.guess_type(filename)[0] or "application/octet-stream"
        signature = self._allowed.get(mime)
        if signature is None or not content.startswith(signature):
            raise DocumentValidationError("Only valid PDF, PNG, and JPEG files are accepted in this demo.")
        object_ref = self.vault.put(content)
        expires_at = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
        document_id = self.metadata.create(
            {
                "profile_id": profile_id,
                "document_type": document_type,
                "object_ref": object_ref,
                "original_name": Path(filename).name,
                "mime_type": mime,
                "size_bytes": len(content),
                "purpose": purpose,
                "expires_at": expires_at,
            }
        )
        self.audit.record("user", profile_id, "upload", "secure_document", document_id, purpose, "success", {"mime_type": mime, "size_bytes": len(content)})
        return document_id

    def list_for_profile(self, profile_id: str) -> list[dict[str, Any]]:
        documents = self.metadata.list_for_profile(profile_id)
        for document in documents:
            document["download_token"] = self.serializer.dumps({"document_id": document["id"], "profile_id": profile_id})
        return documents

    def download(self, profile_id: str, document_id: str, token: str) -> tuple[dict[str, Any], bytes]:
        try:
            payload = self.serializer.loads(token, max_age=300)
        except SignatureExpired as exc:
            raise PermissionError("The download link expired. Refresh the documents page.") from exc
        except BadSignature as exc:
            raise PermissionError("Invalid document download link.") from exc
        if payload != {"document_id": document_id, "profile_id": profile_id}:
            raise PermissionError("Document link does not match this profile.")
        metadata = self.metadata.get(document_id)
        if metadata is None or metadata["profile_id"] != profile_id:
            raise PermissionError("Document is not available to this profile.")
        content = self.vault.get(metadata["object_ref"])
        self.audit.record("user", profile_id, "download", "secure_document", document_id, metadata["purpose"], "success")
        return metadata, content

    def delete(self, profile_id: str, document_id: str) -> None:
        metadata = self.metadata.get(document_id)
        if metadata is None or metadata["profile_id"] != profile_id:
            raise PermissionError("Document is not available to this profile.")
        self.vault.delete(metadata["object_ref"])
        self.metadata.mark_deleted(document_id)
        self.audit.record("user", profile_id, "delete", "secure_document", document_id, "user-requested deletion", "success")
