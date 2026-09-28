# Changelog

## v4.4.1

- Fixed eligibility timeline connector overlap and progress-summary spacing.
- Separated stale/out-of-review program rules from true user non-matches.
- Removed internal rule-maintenance/fixture language from user-facing results.
- Reworked result action buttons into a responsive grid.
- Added a reusable program-result template partial.
- Extracted channel-independent answer normalization into `application/answer_parser.py`.
- Extracted result grouping/action resolution into `presentation/web/eligibility_view.py`.
- Split public routes by user concern while preserving `public_routes.py` as the composition import.
- Split SQLite repositories by persistence concern while preserving backward-compatible imports.
- Centralized derived-field dependencies and derivation logic in `domain/fields.py`.
- Added regression tests for rule-maintenance UX and timeline layout; suite now has 45 tests.

## v4.3

- Simplified the public homepage/navigation and reduced visual clutter.
- Added Profile → Answer → Match → Connect timeline and adaptive progress bar.
- Added saved-answer and new-match milestone feedback.
- Simplified result cards with progressive disclosure.
- Limited geolocation results to five nearest verified sites using 1/5/15-mile progressive radius.
- Added dormant veteran/foster-care canonical questions; did not add criminal-history collection without a real rule.
- Expanded optional document categories.
- Added provider data-readiness scoring and simplified provider/referral views.
- Added provider minimum-data snapshot language and privacy boundary.
- Added four v4.3-specific tests; full suite now 40 passing.

## v4.2

- Added visible food-search result summary and automatic scroll target.
- Simplified match results by removing the large direct-food pseudo-eligibility card.
- Added stronger validation for numeric/select inputs and invalid question IDs.
- Added service/referral validation to prevent malformed IDs from causing database errors.
- Centralized derived-field dependency mapping in `app/domain/fields.py`.
- Added configuration-integrity and resilience test suites.
- Added GitHub Actions CI, contribution guide, team handoff, architecture, testing, and RAG/SMS integration docs.

Older prototype handoff documents are retained under `docs/archive/pre_v4_2/` for project history.
