from __future__ import annotations

from dataclasses import dataclass

from app.adapters.notifications.log_service import LogNotificationService
from app.adapters.rules.json_repository import JsonRuleRepository
from app.adapters.sqlite.repositories import (
    SqliteAssessmentRepository,
    SqliteAuditRepository,
    SqliteDocumentMetadataRepository,
    SqliteProfileRepository,
    SqliteReferralRepository,
    SqliteResourceRepository,
)
from app.adapters.vault.local_encrypted import LocalEncryptedObjectStore
from app.application.document_service import DocumentService
from app.application.profile_service import ProfileService
from app.application.referral_service import ReferralService
from app.application.resource_service import ResourceService
from app.application.screening_service import ScreeningService
from app.config import Settings
from app.db import Database
from app.domain.eligibility import EligibilityEngine


@dataclass
class AppContainer:
    settings: Settings
    database: Database
    profiles: ProfileService
    screening: ScreeningService
    resources: ResourceService
    referrals: ReferralService
    documents: DocumentService
    profile_repository: SqliteProfileRepository
    assessment_repository: SqliteAssessmentRepository
    resource_repository: SqliteResourceRepository
    referral_repository: SqliteReferralRepository
    audit_repository: SqliteAuditRepository


def build_container(settings: Settings) -> AppContainer:
    settings.prepare_directories()
    database = Database(settings.database_path, settings.base_dir / "app" / "adapters" / "sqlite" / "schema.sql")
    database.initialize()

    profile_repo = SqliteProfileRepository(database)
    assessment_repo = SqliteAssessmentRepository(database)
    resource_repo = SqliteResourceRepository(database)
    referral_repo = SqliteReferralRepository(database)
    document_repo = SqliteDocumentMetadataRepository(database)
    audit_repo = SqliteAuditRepository(database)
    rule_repo = JsonRuleRepository(settings.rules_dir, settings.questions_path)
    notification_service = LogNotificationService(settings.data_dir / "notifications.log")
    vault = LocalEncryptedObjectStore(settings.vault_dir, settings.vault_key)

    container = AppContainer(
        settings=settings,
        database=database,
        profiles=ProfileService(profile_repo, audit_repo),
        screening=ScreeningService(rule_repo, assessment_repo, EligibilityEngine()),
        resources=ResourceService(resource_repo, audit_repo),
        referrals=ReferralService(referral_repo, resource_repo, audit_repo, notification_service),
        documents=DocumentService(document_repo, vault, audit_repo, settings.session_secret, settings.max_upload_bytes),
        profile_repository=profile_repo,
        assessment_repository=assessment_repo,
        resource_repository=resource_repo,
        referral_repository=referral_repo,
        audit_repository=audit_repo,
    )
    _seed_providers_if_empty(container)
    return container


def _seed_providers_if_empty(container: AppContainer) -> None:
    # V2 upgrade behavior: hide the old fictional public seed and add the real,
    # source-linked catalog once. Manual/provider-imported records are preserved.
    with container.database.transaction() as connection:
        connection.execute(
            "UPDATE providers SET public_visibility='RESTRICTED', data_quality_status='demo_only' "
            "WHERE source_type='demo_seed'"
        )
    # Stable provider/service/location IDs make the seed idempotent. Import it
    # on every startup so catalog corrections and new fields update existing
    # demo databases without deleting profiles or referrals.
    if container.settings.provider_seed_path.exists():
        container.resources.import_csv(
            container.settings.provider_seed_path.read_bytes(),
            "bootstrap",
        )
