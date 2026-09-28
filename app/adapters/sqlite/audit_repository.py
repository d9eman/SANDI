from __future__ import annotations

import json
from typing import Any

from app.db import Database
from app.ports.repositories import AuditRepository

from .common import utcnow


class SqliteAuditRepository(AuditRepository):
    def __init__(self,database:Database): self.database=database

    def record(self,actor_type:str,actor_id:str,action:str,target_type:str,target_id:str,purpose:str,outcome:str,metadata:dict[str,Any]|None=None)->None:
        with self.database.transaction() as connection:
            connection.execute(
                "INSERT INTO audit_events(actor_type,actor_id,action,target_type,target_id,purpose,outcome,metadata_json,created_at) VALUES(?,?,?,?,?,?,?,?,?)",
                (actor_type,actor_id,action,target_type,target_id,purpose,outcome,json.dumps(metadata or {}),utcnow())
            )

    def metrics(self) -> dict[str, Any]:
        with self.database.connect() as connection:
            profile_count = connection.execute("SELECT COUNT(*) FROM profiles").fetchone()[0]
            referral_count = connection.execute("SELECT COUNT(*) FROM referral_tickets").fetchone()[0]
            open_count = connection.execute(
                "SELECT COUNT(*) FROM referral_tickets "
                "WHERE state NOT IN ('CLOSED','CANCELLED','DECLINED','EXPIRED')"
            ).fetchone()[0]
            provider_count = connection.execute("SELECT COUNT(*) FROM providers").fetchone()[0]
            completion = connection.execute(
                "SELECT COUNT(*) FROM referral_tickets WHERE state='CLOSED'"
            ).fetchone()[0]
            resource_opens = connection.execute(
                "SELECT COUNT(*) FROM resource_interactions WHERE action='open'"
            ).fetchone()[0]
            feedback_yes = connection.execute(
                "SELECT COUNT(*) FROM resource_interactions "
                "WHERE action='feedback' AND outcome='yes'"
            ).fetchone()[0]
            feedback_no = connection.execute(
                "SELECT COUNT(*) FROM resource_interactions "
                "WHERE action='feedback' AND outcome='no'"
            ).fetchone()[0]
            by_state = [dict(row) for row in connection.execute(
                "SELECT state,COUNT(*) AS count FROM referral_tickets GROUP BY state ORDER BY state"
            ).fetchall()]
            by_zip = [dict(row) for row in connection.execute(
                "SELECT COALESCE(zip_code,'Unknown') AS zip_code,COUNT(*) AS count "
                "FROM referral_tickets GROUP BY zip_code ORDER BY count DESC LIMIT 10"
            ).fetchall()]
            resource_usage = [dict(row) for row in connection.execute(
                """
                SELECT s.name AS service_name, p.name AS provider_name,
                       SUM(CASE WHEN ri.action='open' THEN 1 ELSE 0 END) AS opens,
                       SUM(CASE WHEN ri.action='feedback' AND ri.outcome='yes' THEN 1 ELSE 0 END) AS helped,
                       SUM(CASE WHEN ri.action='feedback' AND ri.outcome='no' THEN 1 ELSE 0 END) AS did_not_help
                FROM resource_interactions ri
                LEFT JOIN services s ON s.id=ri.service_id
                LEFT JOIN providers p ON p.id=s.provider_id
                WHERE ri.service_id IS NOT NULL
                GROUP BY ri.service_id, s.name, p.name
                ORDER BY opens DESC, helped DESC
                LIMIT 10
                """
            ).fetchall()]
        return {
            "profiles": profile_count,
            "referrals": referral_count,
            "open_referrals": open_count,
            "providers": provider_count,
            "closed_referrals": completion,
            "resource_opens": resource_opens,
            "feedback_yes": feedback_yes,
            "feedback_no": feedback_no,
            "by_state": by_state,
            "by_zip": by_zip,
            "resource_usage": resource_usage,
        }
