from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DB = DATA / "sandi_demo.sqlite3"
VAULT = DATA / "vault"
LOG = DATA / "notifications.log"

for path in [DB, DB.with_suffix(DB.suffix + "-shm"), DB.with_suffix(DB.suffix + "-wal"), LOG]:
    path.unlink(missing_ok=True)
if VAULT.exists():
    shutil.rmtree(VAULT)
VAULT.mkdir(parents=True, exist_ok=True)
(VAULT / ".gitkeep").touch()
print("Demo data reset. It will be re-created and seeded on the next app start.")
