from __future__ import annotations

import json
from typing import Any

from app.db import Database
from app.domain.enums import AnswerState
from app.domain.models import Answer, ProfileSnapshot
from app.ports.repositories import ProfileRepository

from .common import parse_dt, utcnow


class SqliteProfileRepository(ProfileRepository):
    def __init__(self, database: Database):
        self.database = database

    def create(self, profile_id: str, language: str, recovery_hash: str) -> None:
        now = utcnow()
        with self.database.transaction() as connection:
            connection.execute(
                "INSERT INTO profiles(id, language, recovery_hash, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                (profile_id, language, recovery_hash, now, now),
            )

    def get(self, profile_id: str) -> ProfileSnapshot | None:
        with self.database.connect() as connection:
            profile_row = connection.execute("SELECT * FROM profiles WHERE id = ?", (profile_id,)).fetchone()
            if profile_row is None:
                return None
            answer_rows = connection.execute(
                "SELECT question_id, answer_state, value_json FROM profile_answers WHERE profile_id = ?",
                (profile_id,),
            ).fetchall()
        answers: dict[str, Answer] = {}
        for row in answer_rows:
            value = json.loads(row["value_json"]) if row["value_json"] is not None else None
            answers[row["question_id"]] = Answer(
                question_id=row["question_id"],
                state=AnswerState(row["answer_state"]),
                value=value,
            )
        return ProfileSnapshot(
            profile_id=profile_row["id"],
            language=profile_row["language"],
            created_at=parse_dt(profile_row["created_at"]),
            answers=answers,
        )

    def recovery_hash(self, profile_id: str) -> str | None:
        with self.database.connect() as connection:
            row = connection.execute("SELECT recovery_hash FROM profiles WHERE id = ?", (profile_id,)).fetchone()
        return None if row is None else str(row["recovery_hash"])

    def save_answer(self, profile_id: str, question_id: str, state: str, value: Any) -> None:
        now = utcnow()
        value_json = None if value is None else json.dumps(value)
        with self.database.transaction() as connection:
            connection.execute(
                """
                INSERT INTO profile_answers(profile_id, question_id, answer_state, value_json, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(profile_id, question_id) DO UPDATE SET
                    answer_state = excluded.answer_state,
                    value_json = excluded.value_json,
                    updated_at = excluded.updated_at
                """,
                (profile_id, question_id, state, value_json, now, now),
            )
            connection.execute("UPDATE profiles SET updated_at = ? WHERE id = ?", (now, profile_id))

    def list_recent(self, limit: int = 50) -> list[dict[str, Any]]:
        with self.database.connect() as connection:
            rows = connection.execute(
                """
                SELECT p.id, p.language, p.created_at, p.updated_at,
                       COUNT(DISTINCT pa.id) AS answer_count,
                       COUNT(DISTINCT rt.id) AS referral_count
                FROM profiles p
                LEFT JOIN profile_answers pa ON pa.profile_id = p.id
                LEFT JOIN referral_tickets rt ON rt.profile_id = p.id
                GROUP BY p.id
                ORDER BY p.updated_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [dict(row) for row in rows]
