from __future__ import annotations

import uuid
from typing import Any

from app.db import Database
from app.domain.enums import ReferralState
from app.domain.models import ReferralTicket
from app.ports.repositories import ReferralRepository

from .common import parse_dt, utcnow


class SqliteReferralRepository(ReferralRepository):
    def __init__(self,database:Database):
        self.database=database

    def _row_to_ticket(self,row:Any)->ReferralTicket:
        return ReferralTicket(
            ticket_id=row['id'], profile_id=row['profile_id'], provider_id=row['provider_id'],
            service_id=row['service_id'], need_type=row['need_type'], urgency=row['urgency'],
            zip_code=row['zip_code'], state=ReferralState(row['state']), scheduled_for=row['scheduled_for'],
            outcome=row['outcome'], decline_reason=row['decline_reason'], created_at=parse_dt(row['created_at']),
            updated_at=parse_dt(row['updated_at'])
        )

    def create(self, values: dict[str, Any]) -> ReferralTicket:
        ticket_id=values.get('id') or f"TKT-{uuid.uuid4().hex[:10].upper()}"
        now=utcnow()
        with self.database.transaction() as connection:
            connection.execute(
                """
                INSERT INTO referral_tickets(id,profile_id,provider_id,service_id,need_type,urgency,zip_code,state,consent_scope,created_at,updated_at)
                VALUES(?,?,?,?,?,?,?,?,?,?,?)
                """,
                (ticket_id,values['profile_id'],values.get('provider_id'),values.get('service_id'),values.get('need_type','food'),
                 values.get('urgency','today'),values.get('zip_code'),values['state'],values.get('consent_scope','food referral summary'),now,now)
            )
            connection.execute(
                "INSERT INTO ticket_events(ticket_id,from_state,to_state,actor_type,actor_id,note,created_at) VALUES(?,?,?,?,?,?,?)",
                (ticket_id,None,values['state'],values.get('actor_type','user'),values.get('actor_id',values['profile_id']),values.get('note','Referral created'),now)
            )
            row=connection.execute("SELECT * FROM referral_tickets WHERE id=?",(ticket_id,)).fetchone()
        return self._row_to_ticket(row)

    def get(self,ticket_id:str)->ReferralTicket|None:
        with self.database.connect() as connection:
            row=connection.execute("SELECT * FROM referral_tickets WHERE id=?",(ticket_id,)).fetchone()
        return None if row is None else self._row_to_ticket(row)

    def list_for_profile(self,profile_id:str)->list[dict[str,Any]]:
        with self.database.connect() as connection:
            rows=connection.execute(
                """
                SELECT rt.*, p.name AS provider_name, s.name AS service_name
                FROM referral_tickets rt
                LEFT JOIN providers p ON p.id=rt.provider_id
                LEFT JOIN services s ON s.id=rt.service_id
                WHERE rt.profile_id=? ORDER BY rt.updated_at DESC
                """,(profile_id,)
            ).fetchall()
        return [dict(row) for row in rows]

    def list_for_provider(self,provider_id:str|None=None)->list[dict[str,Any]]:
        with self.database.connect() as connection:
            if provider_id:
                rows=connection.execute(
                    """
                    SELECT rt.*, p.name AS provider_name, s.name AS service_name
                    FROM referral_tickets rt LEFT JOIN providers p ON p.id=rt.provider_id LEFT JOIN services s ON s.id=rt.service_id
                    WHERE rt.provider_id=? OR (rt.provider_id IS NULL AND rt.state='OPEN')
                    ORDER BY rt.updated_at DESC
                    """,(provider_id,)
                ).fetchall()
            else:
                rows=connection.execute(
                    """
                    SELECT rt.*, p.name AS provider_name, s.name AS service_name
                    FROM referral_tickets rt LEFT JOIN providers p ON p.id=rt.provider_id LEFT JOIN services s ON s.id=rt.service_id
                    ORDER BY rt.updated_at DESC
                    """
                ).fetchall()
        return [dict(row) for row in rows]

    def transition(self,ticket_id:str,target_state:str,actor_type:str,actor_id:str,note:str='',scheduled_for:str|None=None,outcome:str|None=None,decline_reason:str|None=None)->ReferralTicket:
        now=utcnow()
        with self.database.transaction() as connection:
            row=connection.execute("SELECT * FROM referral_tickets WHERE id=?",(ticket_id,)).fetchone()
            if row is None:
                raise KeyError(ticket_id)
            old=row['state']
            connection.execute(
                """
                UPDATE referral_tickets SET state=?, scheduled_for=COALESCE(?,scheduled_for), outcome=COALESCE(?,outcome),
                    decline_reason=COALESCE(?,decline_reason), updated_at=? WHERE id=?
                """,(target_state,scheduled_for,outcome,decline_reason,now,ticket_id)
            )
            connection.execute(
                "INSERT INTO ticket_events(ticket_id,from_state,to_state,actor_type,actor_id,note,created_at) VALUES(?,?,?,?,?,?,?)",
                (ticket_id,old,target_state,actor_type,actor_id,note,now)
            )
            updated=connection.execute("SELECT * FROM referral_tickets WHERE id=?",(ticket_id,)).fetchone()
        return self._row_to_ticket(updated)
