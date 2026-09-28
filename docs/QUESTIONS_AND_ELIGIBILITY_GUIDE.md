# Questions and eligibility guide

## The three source-of-truth pieces

### Questions — `config/questions.json`
Defines approved wording, answer type, sensitivity, ordering hints, explanation, dependencies, and source references.

### Rules — `config/rules/*.json`
Defines program/version metadata, predicates, statuses, explanations, and action service IDs.

### Provider catalog — `config/provider_catalog.csv`
Defines where a rule action sends the user.

The rule says **what action is appropriate**; the provider catalog says **where that action currently goes**.

## Adding a question

Add one object with a new stable `id`. Prefer a generic reusable fact such as `household_size` rather than a program-specific duplicate such as `calfresh_household_size`.

## Reusing derived fields

Derived rule fields such as `county_residence` are mapped to their stored question fields in one place:

`app/domain/fields.py`

Both eligibility explanations and config validation use that same mapping.

## Adding a rule

Do not edit templates. Add a version to a program JSON file. The same version automatically feeds:

- evaluator;
- next-question planner;
- green/yellow/red results;
- “why did I get this result?”;
- live team CSV export.

## Safe update checklist

```bash
python scripts/export_eligibility_matrix.py
python -m pytest -q
```

`tests/test_config_integrity.py` catches missing question IDs and broken action service IDs.

## v4.3: future-ready sensitive/profile questions

`veteran_status` and `foster_care_history` now exist as canonical question definitions. They are deliberately **not** part of a fixed questionnaire. The adaptive planner will only surface them after an approved active rule references those fields.

The current catalog already contains `disability` and SSI/SSP in `current_benefits`. Do not ask for diagnoses or documents during pre-screening unless a specific official action requires them.

Do not add criminal-background questions “just in case.” Add a sensitive field only when a verified program/provider requirement needs it, then document the purpose, source, sensitivity, consent/skip behavior, and retention boundary.
