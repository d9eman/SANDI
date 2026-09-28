CREATE TABLE IF NOT EXISTS profiles (
    id TEXT PRIMARY KEY, language TEXT NOT NULL DEFAULT 'en', recovery_hash TEXT NOT NULL,
    created_at TEXT NOT NULL, updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS profile_answers (
    id INTEGER PRIMARY KEY AUTOINCREMENT, profile_id TEXT NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    question_id TEXT NOT NULL, answer_state TEXT NOT NULL, value_json TEXT, created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL, UNIQUE(profile_id, question_id)
);
CREATE TABLE IF NOT EXISTS eligibility_assessments (
    id INTEGER PRIMARY KEY AUTOINCREMENT, profile_id TEXT NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    program_id TEXT NOT NULL, program_name TEXT NOT NULL, program_description TEXT NOT NULL DEFAULT '',
    rule_version_id TEXT NOT NULL, status TEXT NOT NULL, summary TEXT NOT NULL DEFAULT '',
    reasons_json TEXT NOT NULL, requirements_json TEXT NOT NULL DEFAULT '[]', missing_fields_json TEXT NOT NULL,
    source_label TEXT NOT NULL, source_url TEXT NOT NULL, effective_from TEXT NOT NULL, effective_to TEXT,
    notice TEXT NOT NULL, next_step TEXT NOT NULL, display_priority INTEGER NOT NULL DEFAULT 100,
    access_score INTEGER NOT NULL DEFAULT 50, actions_json TEXT NOT NULL DEFAULT '[]', assessed_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_assessments_profile ON eligibility_assessments(profile_id);
CREATE TABLE IF NOT EXISTS providers (
    id TEXT PRIMARY KEY, name TEXT NOT NULL, legal_name TEXT NOT NULL DEFAULT '', description TEXT NOT NULL DEFAULT '', website TEXT NOT NULL DEFAULT '',
    phone TEXT NOT NULL DEFAULT '', source_type TEXT NOT NULL DEFAULT 'manual', source_url TEXT NOT NULL DEFAULT '',
    data_quality_status TEXT NOT NULL DEFAULT 'under_review', last_verified_at TEXT, public_visibility TEXT NOT NULL DEFAULT 'PUBLIC',
    organization_type TEXT NOT NULL DEFAULT 'community_provider', partner_status TEXT NOT NULL DEFAULT 'not_contacted',
    created_at TEXT NOT NULL, updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS services (
    id TEXT PRIMARY KEY, provider_id TEXT NOT NULL REFERENCES providers(id) ON DELETE CASCADE, name TEXT NOT NULL,
    service_type TEXT NOT NULL, service_category TEXT NOT NULL DEFAULT 'food', service_mode TEXT NOT NULL DEFAULT 'direct_service',
    journey_stage TEXT NOT NULL DEFAULT 'direct_help', public_visibility TEXT NOT NULL DEFAULT 'PUBLIC',
    description TEXT NOT NULL DEFAULT '', eligibility_summary TEXT NOT NULL DEFAULT '', eligibility_group TEXT NOT NULL DEFAULT '',
    documentation_notes TEXT NOT NULL DEFAULT '', call_first INTEGER NOT NULL DEFAULT 0, referral_enabled INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL, updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS service_locations (
    id TEXT PRIMARY KEY, service_id TEXT NOT NULL REFERENCES services(id) ON DELETE CASCADE, name TEXT NOT NULL,
    address TEXT NOT NULL DEFAULT '', city TEXT NOT NULL DEFAULT '', state TEXT NOT NULL DEFAULT 'CA', zip_code TEXT NOT NULL DEFAULT '',
    hours_text TEXT NOT NULL DEFAULT '', service_area TEXT NOT NULL DEFAULT 'San Diego County', languages TEXT NOT NULL DEFAULT '',
    accessibility TEXT NOT NULL DEFAULT '', schedule_exceptions TEXT NOT NULL DEFAULT '', transport_notes TEXT NOT NULL DEFAULT '',
    latitude REAL, longitude REAL,
    created_at TEXT NOT NULL, updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS availability_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT, service_id TEXT NOT NULL REFERENCES services(id) ON DELETE CASCADE,
    status TEXT NOT NULL, visibility TEXT NOT NULL, details TEXT NOT NULL DEFAULT '', source TEXT NOT NULL DEFAULT 'manual',
    observed_at TEXT NOT NULL, expires_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_availability_service ON availability_snapshots(service_id, observed_at DESC);
CREATE TABLE IF NOT EXISTS resource_interactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    visitor_id TEXT NOT NULL,
    profile_id TEXT REFERENCES profiles(id) ON DELETE SET NULL,
    service_id TEXT REFERENCES services(id) ON DELETE SET NULL,
    action TEXT NOT NULL,
    location_text TEXT NOT NULL DEFAULT '',
    outcome TEXT NOT NULL DEFAULT '',
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_resource_interactions_service ON resource_interactions(service_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_resource_interactions_profile ON resource_interactions(profile_id, created_at DESC);
CREATE TABLE IF NOT EXISTS referral_tickets (
    id TEXT PRIMARY KEY, profile_id TEXT NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    provider_id TEXT REFERENCES providers(id), service_id TEXT REFERENCES services(id), need_type TEXT NOT NULL,
    urgency TEXT NOT NULL, zip_code TEXT, state TEXT NOT NULL, consent_scope TEXT NOT NULL, scheduled_for TEXT,
    outcome TEXT, decline_reason TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_referrals_profile ON referral_tickets(profile_id);
CREATE INDEX IF NOT EXISTS idx_referrals_provider ON referral_tickets(provider_id, state);
CREATE TABLE IF NOT EXISTS ticket_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT, ticket_id TEXT NOT NULL REFERENCES referral_tickets(id) ON DELETE CASCADE,
    from_state TEXT, to_state TEXT NOT NULL, actor_type TEXT NOT NULL, actor_id TEXT NOT NULL,
    note TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS consent_grants (
    id TEXT PRIMARY KEY, profile_id TEXT NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    recipient_type TEXT NOT NULL, recipient_id TEXT, purpose TEXT NOT NULL, data_scope_json TEXT NOT NULL,
    issued_at TEXT NOT NULL, expires_at TEXT, revoked_at TEXT
);
CREATE TABLE IF NOT EXISTS secure_documents (
    id TEXT PRIMARY KEY, profile_id TEXT NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    document_type TEXT NOT NULL, object_ref TEXT NOT NULL, original_name TEXT NOT NULL, mime_type TEXT NOT NULL,
    size_bytes INTEGER NOT NULL, purpose TEXT NOT NULL, created_at TEXT NOT NULL, expires_at TEXT, deleted_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_documents_profile ON secure_documents(profile_id);
CREATE TABLE IF NOT EXISTS audit_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT, actor_type TEXT NOT NULL, actor_id TEXT NOT NULL, action TEXT NOT NULL,
    target_type TEXT NOT NULL, target_id TEXT NOT NULL, purpose TEXT NOT NULL, outcome TEXT NOT NULL,
    metadata_json TEXT NOT NULL DEFAULT '{}', created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_audit_target ON audit_events(target_type, target_id, created_at DESC);
