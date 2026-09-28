# Follow one answer through SANDI v2

## 1. Where questions are defined
`config/questions.json`

Each question has an ID, wording, answer type, options, sensitivity, priority, stage, grouping, reason, condition note, and source references. The question ID is the stable field name used everywhere else.

## 2. How the next question is chosen
`app/application/screening_service.py`

1. The app evaluates every active rule.
2. Each assessment returns `missing_fields`.
3. The planner counts how many programs each missing field affects.
4. It excludes fields already answered, skipped, or marked unknown.
5. It orders candidates by sensitivity, priority, impact, and ID.

## 3. How an answer is saved
`app/presentation/web/public_routes.py` parses the form and calls `ProfileService.save_answer`.

`app/adapters/sqlite/repositories.py` writes one row to `profile_answers`:
- `profile_id`
- `question_id`
- `answer_state` (`known`, `unknown`, `skipped`)
- `value_json`
- timestamps

## 4. How rules use the answer
Rule files are in `config/rules/*.json`. A rule references the question ID under a deterministic predicate. `app/domain/eligibility.py` evaluates the expression and returns status, reasons, and missing fields.

## 5. How to see this without reading code
Log in to `/staff/login`, then open:
- `/staff/questions` for question-to-program usage
- `/staff/rules` for rule versions and referenced fields
- a profile page for saved states and assessment reasons

## 6. Where providers/services live
- Bootstrap/import data: `config/provider_catalog.csv`
- CSV schema: `config/provider_import_template.csv`
- Stable database tables: `providers`, `services`, `service_locations`
- Changeable status table: `availability_snapshots`
- Import/use case: `app/application/resource_service.py`
- SQLite adapter: `app/adapters/sqlite/repositories.py`
