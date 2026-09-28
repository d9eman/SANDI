from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


class Database:
    """SQLite adapter for the modular-monolith demo."""

    def __init__(self, path: Path, schema_path: Path):
        self.path = path
        self.schema_path = schema_path

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=30, check_same_thread=False)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA journal_mode = WAL")
        return connection

    def initialize(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as connection:
            connection.executescript(self.schema_path.read_text(encoding="utf-8"))
            self._migrate_demo_schema(connection)

    @staticmethod
    def _migrate_demo_schema(connection: sqlite3.Connection) -> None:
        """Small additive migration so v1 demo databases can be opened by v2."""
        additions = {
            "providers": {
                "legal_name": "TEXT NOT NULL DEFAULT ''",
                "organization_type": "TEXT NOT NULL DEFAULT 'community_provider'",
                "partner_status": "TEXT NOT NULL DEFAULT 'not_contacted'",
            },
            "services": {
                "service_category": "TEXT NOT NULL DEFAULT 'food'",
                "service_mode": "TEXT NOT NULL DEFAULT 'direct_service'",
                "journey_stage": "TEXT NOT NULL DEFAULT 'direct_help'",
                "public_visibility": "TEXT NOT NULL DEFAULT 'PUBLIC'",
                "eligibility_group": "TEXT NOT NULL DEFAULT ''",
                "referral_enabled": "INTEGER NOT NULL DEFAULT 1",
            },
            "eligibility_assessments": {
                "program_description": "TEXT NOT NULL DEFAULT ''",
                "summary": "TEXT NOT NULL DEFAULT ''",
                "requirements_json": "TEXT NOT NULL DEFAULT '[]'",
                "display_priority": "INTEGER NOT NULL DEFAULT 100",
                "access_score": "INTEGER NOT NULL DEFAULT 50",
                "actions_json": "TEXT NOT NULL DEFAULT '[]'",
            },
            "service_locations": {
                "schedule_exceptions": "TEXT NOT NULL DEFAULT ''",
                "transport_notes": "TEXT NOT NULL DEFAULT ''",
                "latitude": "REAL",
                "longitude": "REAL",
            },
        }
        for table, columns in additions.items():
            existing = {row[1] for row in connection.execute(f"PRAGMA table_info({table})")}
            for name, definition in columns.items():
                if name not in existing:
                    connection.execute(f"ALTER TABLE {table} ADD COLUMN {name} {definition}")

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        connection = self.connect()
        try:
            connection.execute("BEGIN")
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()
