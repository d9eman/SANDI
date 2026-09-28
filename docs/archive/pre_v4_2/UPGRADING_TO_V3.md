# Upgrade v2 to v3

## Recommended: replace application files and preserve data

1. Stop the old server or run `docker compose down`.
2. Back up `data/sandi_demo.sqlite3` and `data/vault/`.
3. Copy the v3 application/configuration files over v2, but keep the backed-up `data/` directory.
4. Copy `.env.example` to `.env` if needed and set new local passwords.
5. Start the app.

At startup:

- `schema.sql` creates new tables when absent.
- `Database._migrate_demo_schema()` adds only missing columns.
- the provider catalog is upserted by stable IDs.
- profiles, answers, referrals, assessments, and documents are not deleted.

The updated home page is `/`; the no-profile path is `/food-now`.

## Optional: apply the source patch

`V2_TO_V3.patch` is a standard Git patch with paths relative to the project root. From an unchanged v2 project folder:

```powershell
git apply --check V2_TO_V3.patch
git apply V2_TO_V3.patch
```

The patch intentionally excludes the `data/` directory. Back up the database and vault before starting the updated application. The full v3 replacement package is safer when the local v2 source has already been edited.
