# Version 4 code and flow guide

This guide follows the public journey through the existing modular-monolith architecture. Version 4 adds presentation and domain capabilities without replacing the profile, referral, provider, audit, or adapter boundaries.

## 1. Home-page choice

Route:

```text
GET /
app/presentation/web/public_routes.py -> index()
app/presentation/web/templates/index.html
```

The page links to `/food-now` and `/profile/start`. It does not create a profile or submit hidden onboarding data.

## 2. Immediate food without a profile

```text
GET /food-now?location=92101&urgency=today
        ↓
public_routes.food_now()
        ↓
ResourceService.find_food()
        ↓
SqliteResourceRepository.search_food()
        ↓
food_now.html
```

`ResourceService` separates:

- countywide external locators;
- verified direct sites;
- optional public guides.

Direct sites are filtered by exact ZIP or distance from browser coordinates. The service logs only a coarse ZIP for anonymous metrics, not a typed street address or coordinates.

## 3. Browser location

Files:

```text
app/presentation/web/templates/food_now.html
app/presentation/web/static/app.js
```

The location button uses `navigator.geolocation.getCurrentPosition`. The hidden coordinates are sent in the search request. A visible status element reports permission, timeout, unsupported-browser, or insecure-context errors.

## 4. Tracked external handoff

```text
GET /go/{service_id}
        ↓
validate public service and URL
        ↓
record resource_interaction(action="open")
        ↓
302 redirect to provider-owned page
```

A click is not treated as completed service. `/resource-feedback` stores the user’s optional `yes`, `not_yet`, or `no` outcome separately.

## 5. Optional profile after food search

The food page links to:

```text
/profile/start?source=food
```

The anonymous session may contain:

```text
last_food_zip
last_food_urgency
```

`POST /start` creates the guest profile and copies only those intentionally reusable routing fields. It does not copy the exact typed address or browser coordinates.

## 6. Direct profile start

```text
GET /profile/start
POST /start
GET /p/{profile_id}/created
GET /p/{profile_id}/questions
```

No food-map page is part of this path. The recovery phrase is shown once. The first unanswered high-value field is normally ZIP.

## 7. One question at a time

Question definitions:

```text
config/questions.json
```

Selection logic:

```text
app/application/screening_service.py -> next_question()
```

The planner:

1. evaluates every active program;
2. collects only missing fields that can still change an outcome;
3. combines cross-program impact;
4. applies program priority and access score;
5. penalizes sensitive questions;
6. respects `ask_after` dependencies;
7. excludes known, unknown, and skipped answers;
8. returns one approved question.

## 8. Saving an answer

```text
POST /p/{profile_id}/questions/{question_id}
        ↓
ProfileService.save_answer()
        ↓
SqliteProfileRepository.save_answer()
        ↓
profile_answers
```

Each answer stores:

```text
profile_id
question_id
answer_state = known | unknown | skipped
value_json
created_at
updated_at
```

After saving, the route evaluates the profile again and compares the old and new assessments. A newly actionable program is shown immediately above the next question with its official action link.

## 9. Deterministic eligibility evaluation

Rules:

```text
config/rules/*.json
```

Loader:

```text
app/adapters/rules/json_repository.py
```

Evaluator:

```text
app/domain/eligibility.py
```

The evaluator returns a structured `EligibilityAssessment`, including status, summary, missing fields, source dates, actions, and `PredicateResult` comparisons with expected and actual values.

The rule engine does not depend on FastAPI, HTML, SQLite, or a language model.

## 10. Ranked result page

```text
GET /p/{profile_id}/results
        ↓
ScreeningService.sort_assessments()
        ↓
resolve rule actions to provider catalog routes
        ↓
results.html
```

Sort order:

1. direct resources;
2. likely eligible;
3. may qualify;
4. needs information;
5. rule under review;
6. likely not eligible.

Within a status, program display priority and access score control ordering. The red section is collapsed by default.

## 11. Dynamic rule/question export

```text
GET /staff/eligibility-matrix.csv
        ↓
app/domain/rule_export.py
        ↓
active rule objects + active question objects
        ↓
CSV response
```

Command-line equivalent:

```powershell
python scripts/export_eligibility_matrix.py
```

The export is derived from the same source files used during evaluation, avoiding a manually maintained duplicate requirements table.
