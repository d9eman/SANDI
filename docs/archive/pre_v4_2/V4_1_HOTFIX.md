# SANDI v4.1 hotfix

## Failures fixed

### `/food-now` returned HTTP 500

A browser cookie still contained a profile ID from an older local database. The food finder attached that optional profile ID to a `resource_interactions` row. SQLite correctly rejected it because the profile no longer existed.

Version 4.1 validates the profile cookie before use, clears stale profile state, and defensively removes invalid optional analytics references instead of interrupting food access.

### Eligibility routes returned HTTP 500

The URL and cookie referenced a deleted profile. `ProfileService.require()` raised `KeyError`. Version 4.1 redirects stale bookmarks to `/profile/start?notice=profile_not_found` and explains what happened.

## Homepage behavior

- No active profile: **Start eligibility check**
- Existing valid profile: **Continue my eligibility check**
- The homepage no longer shows **See my matches**.

## Files changed

- `app/security/web.py`
- `app/presentation/web/helpers.py`
- `app/presentation/web/public_routes.py`
- `app/adapters/sqlite/repositories.py`
- `app/presentation/web/templates/index.html`
- `app/presentation/web/templates/profile_start.html`
- `app/presentation/web/templates/base.html`
- `app/main.py`
- `run_demo.bat`
- `tests/test_web_smoke.py`
