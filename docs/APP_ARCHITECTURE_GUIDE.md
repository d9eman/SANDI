# App architecture guide

## Why a modular monolith

SANDI currently benefits from one deployable backend, but code boundaries are explicit so future SMS, RAG, PostgreSQL, queues, and partner APIs do not require rewriting eligibility logic.

## Dependency direction

```text
web / future SMS / future chat
            ↓
application services
            ↓
domain objects + deterministic policy
            ↓
ports / interfaces
            ↑
adapters (SQLite, JSON rules, vault, notifications)
```

Domain code does not import FastAPI, Jinja, SQLite, or a messaging provider.

## Composition root

`app/bootstrap.py` creates concrete adapters and injects them into application services. This is the main place that knows which database/object store/notification implementation is active.

## Public presentation layer

Public routes are split by concern rather than placed in one large controller:

```text
presentation/web/
├── home_routes.py
├── profile_routes.py
├── screening_routes.py
├── referral_routes.py
├── document_routes.py
├── public_context.py
├── eligibility_view.py
└── public_routes.py      # router composition only
```

`answer_parser.py` is in the application layer because normalization should be reusable by future SMS/chat channels, not tied to an HTML form.

## Eligibility path

`ScreeningService` loads active rule definitions, evaluates the current profile, stores assessments, and chooses the next useful question.

`EligibilityEngine` is deterministic. Missing information produces `UNKNOWN`, not automatic denial.

`domain/fields.py` is the single source for derived-field dependencies *and* calculations. For example, rules can use `age_60_plus` while the profile stores the reusable fact `age`.

### Rule lifecycle

`ProgramRuleVersion.lifecycle_issue()` checks:

- not yet effective;
- effective period expired;
- scheduled review overdue.

Any such state becomes `RULE_UNDER_REVIEW`. It produces no fake user requirement row. The presentation layer groups it under **screening rules being updated**, separate from true non-matches.

## Result presentation

`presentation/web/eligibility_view.py` converts domain statuses into user-facing result groups and resolves action links. It never changes an eligibility decision.

`templates/_assessment_card.html` contains the reusable program-card markup. Technical source/version detail remains expandable.

## Resource/provider path

`ResourceService` contains location filtering, public service lookup, handoff tracking, provider import, and availability use cases. It depends on the `ResourceRepository` interface rather than SQLite directly.

## SQLite adapters

SQLite remains appropriate for the local demo. Persistence is now split by concern:

```text
adapters/sqlite/
├── profile_repository.py
├── assessment_repository.py
├── resource_repository.py
├── referral_repository.py
├── document_repository.py
├── audit_repository.py
├── common.py
└── repositories.py   # compatibility re-exports
```

A future PostgreSQL implementation can implement the same ports without changing application/domain code.

## Referrals

`domain/referrals.py` owns valid referral state transitions. `ReferralService` validates transitions before repositories persist them.

## Documents

`DocumentService` validates file type/size, delegates encrypted byte storage to the secure-object-store port, stores metadata separately, and audits access. Documents are optional and are not part of ordinary public resource browsing.

## What to extract later

Do not create microservices simply because folders are separated. Extract only when deployment scale, ownership, security boundaries, or availability requirements justify it. Likely first candidates are provider-data ingestion, messaging/notifications, and document processing.
