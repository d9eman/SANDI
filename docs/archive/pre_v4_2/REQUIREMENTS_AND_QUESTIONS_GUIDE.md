# Requirements and questions guide

## Authoritative files

```text
config/questions.json       approved user-facing questions
config/rules/*.json         versioned program requirements and actions
```

The generated CSV is for review and sharing. It is not a second rule source.

## View or share the complete matrix

From the staff portal:

```text
Staff tools -> Rules -> Download current requirements/question CSV
```

Direct route after staff login:

```text
/staff/eligibility-matrix.csv
```

Generate a file locally:

```powershell
python scripts/export_eligibility_matrix.py
```

Output:

```text
docs/SANDI_Eligibility_Requirements_and_Questions.csv
```

## Add a question

Add one object to `config/questions.json`:

```json
{
  "id": "example_field",
  "text_en": "Approved question text",
  "text_es": "Approved Spanish text",
  "answer_type": "single_select",
  "options": [
    {"value": "yes", "label_en": "Yes", "label_es": "Sí"},
    {"value": "no", "label_en": "No", "label_es": "No"}
  ],
  "stage": 3,
  "group": "example",
  "sensitivity": 1,
  "priority": 50,
  "allow_unknown": true,
  "allow_skip": true,
  "ask_after": [],
  "why_en": "Why this answer can change a program match.",
  "why_es": "Por qué esta respuesta puede cambiar una coincidencia."
}
```

Use a stable `id`. Do not rename an ID after profiles have stored answers under it.

## Add or update a requirement

Create a new immutable version inside the relevant `config/rules/*.json` file rather than changing the meaning of an old version already used for assessments.

A predicate should include:

```json
{
  "type": "predicate",
  "field": "example_field",
  "operator": "equals",
  "value": "yes",
  "requirement": "Plain-language requirement name",
  "expected_text": "What the program expects",
  "pass_reason": "Why the answer met the requirement.",
  "fail_reason": "Why the answer did not meet the requirement.",
  "unknown_reason": "Why this answer is still needed."
}
```

The `field` normally matches a question `id`. Derived fields such as county from ZIP are mapped centrally in `app/domain/rule_inspection.py` and the profile model.

## Add an action link

Program-level action metadata belongs beside the program definition:

```json
"actions": [
  {
    "service_id": "svc_example_application",
    "label": "Start the official application",
    "kind": "primary"
  }
]
```

The `service_id` must exist in the provider/service catalog and be public. The result page resolves it through the resource service so openings are tracked consistently.

## Prevent unnecessary questions

Use:

- `if_then` for program-specific branches;
- `any` for alternative qualifying routes;
- `ask_after` when one question only makes sense after another;
- low sensitivity values for easy routing questions;
- higher sensitivity values for financial or legal questions;
- program `display_priority` and `access_score` to prioritize useful pathways.

The engine short-circuits an `all` group after a known failure and an `any` group after a known pass. Therefore, questions from branches that cannot change the current result are not asked.

## Validation checklist

After a rule/question edit:

```powershell
python scripts/export_eligibility_matrix.py
python -m pytest -q
```

Then inspect:

- `/staff/questions`
- `/staff/rules`
- `/staff/eligibility-matrix.csv`
- a known passing profile;
- a known failing profile;
- unknown and skipped answers;
- action links and effective/review dates.
