# SANDI Food & Eligibility Demo v4.4.1

SANDI is a low-barrier prototype with two intentionally separate public paths:

1. **Find food now** without creating a profile.
2. **Check multiple programs with one reusable profile** using deterministic, explainable pre-screening.


> **Demo boundary:** use synthetic/test personal information. Eligibility results are pre-screening only. Public provider information changes, and direct referral is disabled until a provider explicitly participates.

## Quick start

### Windows
```powershell
Copy-Item .env.example .env
.\run_demo.bat
```

### macOS / Linux
```bash
cp .env.example .env
./run_demo.sh
```

Open `http://127.0.0.1:8000`.

### Docker
```bash
docker compose up --build
```

## Demo logins

- Provider: `provider / sandi-demo`
- Staff: `staff / sandi-demo`

Change these in `.env` and restart the app.

## Public flow

```text
Home
├── Find food near me
│   ├── ZIP/area OR browser location
│   ├── Up to 5 nearest verified direct sites
│   ├── live countywide provider maps
│   └── optional invitation to create an eligibility profile
│
└── Check what I qualify for
    ├── anonymous guest profile + recovery phrase
    ├── Profile → Answer → Match → Connect timeline
    ├── one high-value question at a time
    ├── saved-answer + match feedback
    └── ranked results with optional “Why?” detail
```

## Source-of-truth files

- Questions: `config/questions.json`
- Eligibility rules: `config/rules/*.json`
- Providers/services: `config/provider_catalog.csv`
- Generated review matrix: `docs/SANDI_Eligibility_Requirements_and_Questions.csv`

Do not put eligibility logic in HTML, JavaScript, or route handlers. Update the JSON rule/question configuration and run validation/tests.

## Architecture

```text
presentation/   FastAPI routes + HTML; channel-specific only
application/    profile, screening, resource, referral, document use cases
 domain/        deterministic rules, state machines, reusable policy helpers
ports/          repository/service interfaces
adapters/       SQLite, JSON rules, vault, notifications
security/       sessions, CSRF, access helpers
config/         questions, rules, provider catalog
```

For a file-by-file map, start with `docs/CODE_MAP.md`.

## Validate before a pull request

```bash
python scripts/validate_project.py
python scripts/export_eligibility_matrix.py
python -m pytest -q
python -m compileall -q app tests scripts
```

Current v4.4.1 package: **45 automated tests passing**.

## Read next

- `TEAM_HANDOFF.md`
- `docs/CODE_MAP.md`
- `docs/V4_4_READABILITY_AND_UI_FIXES.md`
- `docs/APP_ARCHITECTURE_GUIDE.md`
- `docs/QUESTIONS_AND_ELIGIBILITY_GUIDE.md`
- `docs/TESTING_AND_GITHUB_GUIDE.md`
- `docs/RAG_SMS_INTEGRATION_PLAN.md`
