# Testing and GitHub guide

## What is tested

The suite contains unit, integration, web-flow, configuration-integrity, and resilience tests.

Resilience coverage includes:

- empty and malformed food-search inputs;
- invalid/geolocation coordinate strings;
- stale profile cookies;
- all-unknown/all-skip survey completion;
- valid-answer survey completion;
- invalid question IDs;
- `NaN`, invalid selections, and malformed answers;
- missing provider resources and invalid feedback;
- invalid referral service IDs;
- provider/staff login;
- encrypted document validation;
- referral state-machine transitions.

No test suite can prove a web app can **never** fail, but the objective is that user-controlled inputs produce a useful 2xx/3xx/4xx response rather than an unhandled 500.

## Local verification

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
python -m compileall -q app tests scripts
```

## GitHub

The repository includes `.github/workflows/tests.yml`. Every push/PR runs the test and compile checks on Python 3.11 and 3.12.

Do not commit:

- `.env`
- `data/*.sqlite3`
- `data/notifications.log`
- `data/vault/*`
- real identity documents or user exports

## Recommended first GitHub setup

```bash
git init
git add .
git commit -m "Initial SANDI food and eligibility prototype"
git branch -M main
git remote add origin <your-repository-url>
git push -u origin main
```

Before making the repository public, the team should explicitly choose a software license and confirm that provider-derived data/documents are permitted to be redistributed.
