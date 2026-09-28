# Security, Privacy, and Production Boundary

## What the demo already demonstrates

- data minimization and guest access;
- salted recovery-phrase hashes;
- CSRF protection for state-changing browser forms;
- separated document metadata and encrypted object bytes;
- random object names outside the static directory;
- short-lived signed document-download tokens;
- profile-session authorization;
- provider/staff route protection;
- append-oriented audit events;
- deterministic versioned rules;
- no document bytes in staff view.

## What the demo does not guarantee

It has not undergone independent penetration testing, threat modeling, privacy/legal review, accessibility certification, partner security review, or operational readiness testing. Shared demo usernames/passwords and cookie sessions are not sufficient for real users. Local Fernet encryption is not a managed key system. File signature validation is not malware scanning.

## Required production controls

### Identity and authorization

- individual staff/provider accounts;
- MFA;
- least-privilege role and attribute policies;
- provider-tenant isolation;
- service-relationship/purpose checks before staff profile access;
- periodic access review and immediate revocation.

### Documents

- managed private object storage;
- managed encryption keys and rotation;
- malware scanning/quarantine;
- approved MIME/signature validation;
- per-purpose consent and recipient scope;
- retention/deletion jobs;
- legal-hold handling only when required;
- abnormal-access alerts.

### Application and infrastructure

- HTTPS and secure cookies;
- trusted hosts/proxies;
- rate limits and bot/abuse controls;
- input validation and output encoding;
- dependency scanning and patching;
- central logs, metrics, alerts, and incident response;
- encrypted backups and tested restoration;
- separate environments and synthetic test data;
- database migrations and transactional integrity.

### Governance

- assigned program-rule owners;
- source and freshness review;
- consent language approval;
- data-sharing agreements;
- user correction/deletion procedures;
- ticket escalation and no-response ownership;
- emergency disclaimers and operational boundaries;
- de-identified analytics standards;
- prohibition on using AI to make or silently change eligibility decisions.

## Do not use real IDs in the demo

The document vault exists to demonstrate the interface boundary and lifecycle. Use only synthetic files during engineering and team demonstrations.
