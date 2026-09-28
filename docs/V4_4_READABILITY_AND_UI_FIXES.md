# v4.4 readability and UI fixes

## 1. Progress timeline overlap

### Cause
The v4.3 connector was drawn from the right edge of each circle through the same horizontal row as the text label. Because the label had a transparent background, the line visibly crossed words such as `Profile` and `Answer`.

The progress summary also mixed raw text nodes and flex children, which let the number separate visually from `useful answers saved` on wide screens.

### Fix
- Timeline steps are now vertical: circle on the first row, label below it.
- Connectors run only through the circle row.
- Progress counts are explicit `<span>` groups rather than loose flex text.
- On narrow phones the progress summary stacks instead of stretching apart.

Files: `_journey_timeline.html`, `question.html`, `static/styles.css`.

## 2. CalFresh "fixture" text

### What it was
It was not a user eligibility answer. The CalFresh rule file says:

- effective through `2026-09-30`
- internal `review_due` date `2026-09-15`

On dates after the review deadline, the engine intentionally refuses to rely on the rule and emits `RULE_UNDER_REVIEW`. The old code represented that system state as a fake requirement row (`Current rule version`) and used internal engineering wording (`fixture`). That made it look as if the user had failed an eligibility requirement.

### Fix
- Rule freshness now produces no fake expected-vs-actual requirement.
- User-facing copy never says `fixture`.
- `RULE_UNDER_REVIEW` is grouped separately from true non-matches.
- The page explicitly says the update is not caused by the user's answers.
- Official application/help links remain available.
- The rule deadline was **not silently extended**; a policy owner still needs to review/update the rule source.

Files: `domain/eligibility.py`, `presentation/web/eligibility_view.py`, `_assessment_card.html`, `results.html`.

## 3. Action-button crowding

Result actions previously used a wrapping flex row. Three long actions could compete for width and render poorly.

Actions now use a small grid:

- primary action takes the full first row;
- secondary actions share the next row when space permits;
- mobile stacks every action vertically.

This is CSS-only and does not change program behavior.

## 4. Code handoff refactor

The refactor intentionally preserves behavior and interfaces while making files easier to find:

- web input normalization → `application/answer_parser.py`
- result grouping/action resolution → `presentation/web/eligibility_view.py`
- public routes split by concern
- SQLite repositories split by entity/concern
- derived-field dependency + calculation centralized in `domain/fields.py`
- result-card markup moved to `_assessment_card.html`
- shared eligibility status categories centralized in `domain/enums.py`

See `docs/CODE_MAP.md` for the current map.
