# v4.4.1 — Rule review behavior

## Principle

`effective_from` and `effective_to` control whether a rule version may be used for eligibility screening.

`review_due` is internal governance metadata only. Passing the review date does **not** deactivate a rule, alter a user's result, or create a user-facing warning.

## Public UI

Public eligibility cards show the official source and the user-specific explanation, but do not display internal effective/review dates.

## Staff UI

`/staff/rules` shows effective dates and review dates. An overdue review date gets a small red dot with a hover tooltip and a `Needs review` label.

## Rule update workflow

1. Keep the current `review_due` value in the JSON file.
2. Let the red staff warning remind the team that the rule should be checked.
3. Do not change eligibility behavior merely because the review date passes.
4. When official policy changes, add/update the appropriate version with correct effective dates and tests.
