from __future__ import annotations

import pytest

from app.application.document_service import DocumentValidationError
from app.bootstrap import build_container


def test_document_is_encrypted_and_profile_scoped(settings):
    app = build_container(settings)
    profile, _ = app.profiles.create_guest("en")
    content = b"%PDF-1.4\nDemo only\n%%EOF"
    document_id = app.documents.upload(profile.profile_id, "demo.pdf", "application/pdf", content, "identity", "unit test")
    metadata = app.documents.list_for_profile(profile.profile_id)[0]
    stored = (settings.vault_dir / metadata["object_ref"]).read_bytes()
    assert content not in stored
    returned_metadata, returned_content = app.documents.download(profile.profile_id, document_id, metadata["download_token"])
    assert returned_metadata["original_name"] == "demo.pdf"
    assert returned_content == content


def test_document_signature_validation(settings):
    app = build_container(settings)
    profile, _ = app.profiles.create_guest("en")
    with pytest.raises(DocumentValidationError):
        app.documents.upload(profile.profile_id, "fake.pdf", "application/pdf", b"not-a-pdf", "identity", "unit test")
