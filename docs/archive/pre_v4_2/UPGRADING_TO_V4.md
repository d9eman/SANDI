# Upgrade v3 to v4

## Recommended method

1. Stop the v3 server or container.
2. Back up:

```text
data/sandi_demo.sqlite3
data/vault/
.env
```

3. Copy the v4 application and configuration files over the v3 source tree, or apply `V3_TO_V4.patch` from the v3 project root.
4. Keep the backed-up `data/` directory.
5. Preserve your `.env` values.
6. Start v4.

The database initialization is additive. It adds richer eligibility-assessment fields while retaining existing profiles, answers, provider records, referrals, audit events, and document metadata.

## Apply the patch

From an unmodified v3 source tree:

```powershell
git apply V3_TO_V4.patch
```

The full v4 package is safer when local v3 files were already edited.

## Regenerate the team matrix

```powershell
python scripts/export_eligibility_matrix.py
```

## Verify

```powershell
python -m pytest -q
```

Manual checks:

1. `/food-now?location=92101` shows both official maps but not the Vista direct pantry.
2. `/food-now?location=92081` can show the Vista direct pantry.
3. Direct profile creation reaches ZIP/question flow, not food maps.
4. Profile creation from the food page reuses the ZIP.
5. Results show green/yellow/red ordering, expected-versus-actual comparisons, and action links.
6. `/staff/eligibility-matrix.csv` downloads the active rule/question matrix.
