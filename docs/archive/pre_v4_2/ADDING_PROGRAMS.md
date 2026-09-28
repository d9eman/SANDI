# Adding questions and programs in SANDI v2

## Add a question

Edit `config/questions.json` and add a stable question ID with:

- English/Spanish wording
- help text
- answer type and options
- sensitivity and priority
- stage and reusable group
- why it is asked
- conditional note
- source references

Do not rename an ID after profiles have used it. Add a replacement ID and a new rule version.

## Add a program or rule version

Create a JSON file in `config/rules/`. A version must include:

- program ID/name/description
- rule-version ID
- effective and review dates
- source label/URL
- pre-screen notice
- pass/unknown/fail statuses
- deterministic expression
- next steps for every status

Supported expression nodes include `all`, `any`, `if_then`, `sum_compare`, `predicate`, and `always`. Supported predicate operators include equality/list/numeric comparisons, `contains_any`, and household-size income tables.

## How conditional questions work

The engine reports missing fields. `ScreeningService.next_question` ranks only unanswered fields referenced by active rules. An `if_then` branch does not request its follow-up fields when the trigger fails.

## Test before use

Add known profiles and expected outcomes under `tests/`. A production rule owner must approve sources, effective dates, wording, and test cases. The app moves overdue rules to `RULE_UNDER_REVIEW`.
