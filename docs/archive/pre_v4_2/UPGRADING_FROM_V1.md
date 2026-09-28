# Upgrading from the first SANDI demo

The simplest approach is to use the complete v2 folder and a new demo database.

To preserve an existing v1 database:

1. Back up `data/sandi_demo.sqlite3` and `data/vault`.
2. Replace the code/config files with v2.
3. Keep the old `data` folder.
4. Start v2. The additive migration creates the new provider/service columns.
5. The bootstrap hides records with `source_type=demo_seed` from public search and imports the v2 source-linked catalog if it is not already present.

After changing `.env`, stop and restart the process. With Docker:

```powershell
docker compose down
docker compose up --build
```

Provider and staff access now uses `/provider/login` and `/staff/login`; browser HTTP Basic Auth is no longer used.
