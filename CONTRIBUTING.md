# Contributing to the SANDI prototype

## Branch workflow

Use a short branch per change, for example:

- `feature/wic-rule-update`
- `feature/provider-import-feeding-sd`
- `fix/food-search-location`

Open a pull request rather than pushing large changes directly to `main`.

## Keep dependency direction intact

Presentation may call application services. Application/domain code may depend on ports. Adapters implement ports. Domain code must not import FastAPI, Jinja, SQLite, Twilio, or a RAG model.

## Rule changes

1. Confirm the source and effective/review date.
2. Reuse an existing question ID where possible.
3. Add a new rule version instead of rewriting historical policy silently.
4. Add/update tests.
5. Regenerate the eligibility matrix.

## Provider changes

Keep provider, service, location, and availability separate. `referral_enabled=true` means an actual operational agreement exists; it is not inferred from a public website.

## Tests

Required before PR:

```bash
python -m pytest -q
python -m compileall -q app tests scripts
```

Do not commit `.env`, SQLite databases, vault files, or real user documents.
