# SANDI v4.4.1 team handoff

## Run it

```bash
cp .env.example .env             # PowerShell: Copy-Item .env.example .env
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## Start here

1. `README.md` — run the app and understand the product boundary.
2. `docs/CODE_MAP.md` — find the correct module for a change.
3. `docs/QUESTIONS_AND_ELIGIBILITY_GUIDE.md` — edit questions/rules safely.
4. `docs/V4_4_READABILITY_AND_UI_FIXES.md` — understand the newest UI/refactor decisions.

## What teammates should edit

| Goal | Source of truth |
|---|---|
| Change question wording/options | `config/questions.json` |
| Change eligibility | `config/rules/*.json` |
| Add/update providers | `config/provider_catalog.csv` or provider import |
| Change question ordering strategy | `app/application/screening_service.py` |
| Change answer normalization | `app/application/answer_parser.py` |
| Change deterministic rule evaluation | `app/domain/eligibility.py` |
| Add/change a derived reusable fact | `app/domain/fields.py` |
| Change result grouping/presentation behavior | `app/presentation/web/eligibility_view.py` + templates |
| Change food/resource matching | `app/application/resource_service.py` |
| Change provider data-quality scoring | `app/domain/provider_quality.py` |

## Public route map

- `home_routes.py` — home, immediate food, public handoffs/feedback
- `profile_routes.py` — guest profile, recovery, dashboard
- `screening_routes.py` — questions + results
- `referral_routes.py` — referral tickets
- `document_routes.py` — optional documents
- `public_routes.py` — only composes those routers

Do not move eligibility decisions into a route handler.

## Stable question contract

```text
question ID
   ↓
profile_answers.question_id
   ↓
rule predicate field
   ↓
question planner
   ↓
result explanation
```

Do not rename a question ID after real/saved profiles have used it unless you also perform a data migration.

## Rule freshness

A program can be in `RULE_UNDER_REVIEW` because its configured effective/review dates are no longer current. That is a **system state**, not a failed user answer.

Do not “fix” this by casually moving a review date forward. Update/validate the real program rule and source, then create/update the correct versioned rule definition.

## Provider model

```text
Provider organization
  └── Service
      └── Location
          └── Availability snapshots
```

Do not create a duplicate provider organization just because it operates another service.

## Before merging

```bash
python scripts/validate_project.py
python scripts/export_eligibility_matrix.py
python -m pytest -q
python -m compileall -q app tests scripts
```

Current package: **45 tests passing**.
