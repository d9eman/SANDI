"""Backward-compatible imports for SQLite repository adapters.

Each persistence concern lives in its own module. Existing imports from
``app.adapters.sqlite.repositories`` continue to work, which keeps bootstrap
and external code stable while making the adapter layer easier to navigate.
"""

from .assessment_repository import SqliteAssessmentRepository
from .audit_repository import SqliteAuditRepository
from .document_repository import SqliteDocumentMetadataRepository
from .profile_repository import SqliteProfileRepository
from .referral_repository import SqliteReferralRepository
from .resource_repository import SqliteResourceRepository

__all__ = [
    "SqliteAssessmentRepository",
    "SqliteAuditRepository",
    "SqliteDocumentMetadataRepository",
    "SqliteProfileRepository",
    "SqliteReferralRepository",
    "SqliteResourceRepository",
]
