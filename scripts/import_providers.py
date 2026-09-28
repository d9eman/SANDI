from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.bootstrap import build_container
from app.config import Settings

parser = argparse.ArgumentParser(description="Import provider/service rows into the SANDI demo catalog.")
parser.add_argument("csv_path", type=Path)
args = parser.parse_args()

container = build_container(Settings.from_env())
count, _ = container.resources.import_csv(args.csv_path.read_bytes(), "cli-import")
print(f"Imported {count} provider-service rows from {args.csv_path}")
