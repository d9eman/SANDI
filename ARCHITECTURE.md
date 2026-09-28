# Architecture and Code Walkthrough

## Why a modular monolith

The first SANDI release needs several coordinated capabilities but does not yet need the operational burden of microservices. This project therefore runs as one FastAPI process and one relational database while maintaining module boundaries and interface-based dependencies.

## Request lifecycle

A typical screening request follows this path:

```text
Browser form
  → presentation/web/public_routes.py
  → application/profile_service.py or screening_service.py
  → domain/eligibility.py
  → ports/repositories.py
  → adapters/sqlite/repositories.py or adapters/rules/json_repository.py
  → application result
  → Jinja template
```

A provider update follows a different use case but reuses the same infrastructure:

```text
Provider portal
  → application/resource_service.py
  → ResourceRepository port
  → SQLite adapter
  → append availability snapshot
  → AuditRepository
```

## Domain layer

### `domain/models.py`

Contains profile answers, profile snapshots, eligibility assessments, questions, and referral-ticket data structures. `ProfileSnapshot.derived_value()` centralizes derived facts such as `age_60_plus`, `no_fixed_address`, and the demo ZIP-to-county heuristic.

### `domain/eligibility.py`

Contains the deterministic rule evaluator. The evaluator supports expression trees with:

- `always`
- `all`
- `any`
- `predicate`

Predicates are tri-state: `PASS`, `FAIL`, or `UNKNOWN`. `all` fails when any child fails and remains unknown when no child fails but one is unknown. `any` passes when any child passes and remains unknown when no child passes but one is unknown. That prevents missing information from being silently interpreted as ineligibility.

The evaluator also checks effective/review dates before applying a rule. A stale/out-of-window rule becomes `RULE_UNDER_REVIEW`.

### `domain/referrals.py`

Owns the referral transition map. Route handlers cannot directly set arbitrary states. They must request a transition through `ReferralService`, which validates the state machine first.

## Application layer

### `ProfileService`

Creates guest profiles, hashes recovery phrases, authenticates returning users, saves individual answers, and emits audit events.

### `ScreeningService`

Loads active rules, evaluates the profile, stores current assessments, and chooses the next question based on impact, sensitivity, priority, and whether the user already answered/skipped it.

### `ResourceService`

Searches public food services, imports provider CSV rows, adds provider records, and appends availability snapshots.

### `ReferralService`

Creates consented food tickets and transitions them through the domain state machine. Notifications are sent through a replaceable port.

### `DocumentService`

Validates file signature/size, encrypts bytes through the object-store port, stores metadata separately, creates short-lived signed download tokens, and audits operations.

## Ports

`ports/repositories.py` and `ports/services.py` are the seams that allow infrastructure replacement. Application code sees `ProfileRepository`, not `sqlite3`; `SecureObjectStore`, not a filesystem path; and `NotificationService`, not Twilio.

## Adapters

### SQLite

SQLite is appropriate for a local demonstration because it requires no separate server. The schema already separates:

- profiles and answers;
- current assessment snapshots;
- stable provider/service/location records;
- append-only availability snapshots;
- referrals and ticket events;
- document metadata;
- audit events.

A production PostgreSQL adapter can implement the same ports.

### JSON rule repository

Each program file contains program metadata and one or more immutable rule versions. The adapter chooses the version effective on the current date; the domain engine independently marks stale/out-of-window versions under review.

### Encrypted local vault

The demo vault encrypts bytes with Fernet and stores random names outside the static web directory. The browser cannot construct a public object URL.

### Notification log

The demo app writes notifications to `data/notifications.log`. An SMS/email adapter can replace it without modifying referral logic.

## Presentation layer

The mobile-first interface uses server-rendered Jinja templates and small vanilla JavaScript. This keeps the prototype deployable and easy to understand. A future React/mobile/SMS channel can call the same application services or a JSON API built above them.

## Security helpers

- profile sessions authorize a guest user to one profile;
- recovery phrases use PBKDF2 with a random salt;
- state-changing HTML forms use session-bound CSRF tokens;
- provider/staff demonstrations use role-specific session login forms;
- sensitive actions emit audit events;
- documents are not mounted as static content.

## What to extract later

Do not extract services merely because the folder boundaries exist. Extract only when scale, ownership, security boundaries, or deployment independence justify it. Likely first candidates are notifications, provider-data ingestion, and document processing—not the deterministic eligibility engine.

## Version 3 journey-stage and visibility refinement

The organization hierarchy is now explicit in both data and presentation:

```text
providers (one organization identity)
  -> services (different purposes and journey stages)
      -> service_locations (different sites and schedules)
          -> availability_snapshots (time-varying status)
```

`services.journey_stage` controls where a service appears:

- `immediate_food`
- `more_help`
- `direct_help`

`services.public_visibility` is separate from organization visibility. This allows, for example, a public provider information page and a restricted, not-yet-approved direct referral under the same organization ID.

Public handoffs are recorded in `resource_interactions`. This table is deliberately separate from `referral_tickets`: opening a map or application is not equivalent to receiving service.
