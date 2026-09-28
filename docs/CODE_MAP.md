# SANDI code map

This is the shortest path for a new engineer to understand where a change belongs.

## Dependency direction

```text
web / future SMS / future chat
            ↓
application services
            ↓
domain rules and state
            ↓
ports (interfaces)
            ↑
adapters (SQLite, JSON rules, vault, notifications)
```

A layer may depend on the layer below it. Domain code never imports FastAPI, HTML, SQLite, or a messaging vendor.

## Public web routes

The former large `public_routes.py` is now only a composition root. Public routes are grouped by user concern:

- `presentation/web/home_routes.py` — homepage, immediate food search, public resource handoffs/feedback.
- `presentation/web/profile_routes.py` — guest-profile creation, recovery, emergency return, profile dashboard, legacy URL redirects.
- `presentation/web/screening_routes.py` — adaptive questions, answer submission, ranked eligibility results.
- `presentation/web/referral_routes.py` — closed-loop referral tickets and user confirmation.
- `presentation/web/document_routes.py` — optional document upload/download/delete.
- `presentation/web/public_context.py` — tiny shared web helpers only (container, redirect, visitor ID, rendering).
- `presentation/web/eligibility_view.py` — result grouping and resolution of rule-configured action links.

Routes should orchestrate. Business decisions belong in `application/` or `domain/`.

## Eligibility path

```text
config/questions.json
        ↓ stable question IDs
ProfileService.save_answer
        ↓
profile_answers
        ↓
ScreeningService.evaluate
        ↓
EligibilityEngine.evaluate
        ↓
ScreeningService.next_question
        ↓
question.html / results.html
```

- Question wording/options: `config/questions.json`
- Program rules: `config/rules/*.json`
- Generic answer normalization: `application/answer_parser.py`
- Which question to ask next: `application/screening_service.py`
- Deterministic pass/fail/unknown logic: `domain/eligibility.py`
- Derived reusable facts: `domain/fields.py`
- Result UI grouping: `presentation/web/eligibility_view.py`
- One result card: `templates/_assessment_card.html`

## Provider/resource path

```text
provider_catalog.csv / provider portal
        ↓
ResourceService
        ↓ ResourceRepository interface
SQLite resource adapter
        ↓
provider → service → location → availability snapshot
```

Provider data is in `config/provider_catalog.csv` for source-controlled demo seed data. Do not hard-code providers in templates.

## SQLite adapters

The previous 800-line adapter file is split by concern while preserving the old import path:

- `profile_repository.py`
- `assessment_repository.py`
- `resource_repository.py`
- `referral_repository.py`
- `document_repository.py`
- `audit_repository.py`
- `common.py`
- `repositories.py` only re-exports those classes for compatibility.

A future PostgreSQL implementation can implement the same interfaces in `ports/repositories.py` without changing application/domain code.

## Rule freshness

`ProgramRuleVersion.lifecycle_issue()` determines whether a rule is not yet effective, expired, or past its review date. `EligibilityEngine` converts any of those states to `RULE_UNDER_REVIEW`.

Important: this is a **system-maintenance state**, not a failed user requirement. The results UI therefore keeps it in a separate "screening rules being updated" section instead of the red/non-match group.

## Editing checklist

Before a pull request:

```bash
python scripts/validate_project.py
python scripts/export_eligibility_matrix.py
python -m pytest -q
python -m compileall -q app tests scripts
```

If you change a question ID, rule field, provider service ID, or repository contract, add a regression test in the same pull request.
