from __future__ import annotations

import uuid
from typing import Any

from app.db import Database
from app.ports.repositories import DocumentMetadataRepository

from .common import utcnow


class SqliteDocumentMetadataRepository(DocumentMetadataRepository):
    def __init__(self,database:Database): self.database=database

    def create(self,values:dict[str,Any])->str:
        document_id=values.get('id') or f"DOC-{uuid.uuid4().hex[:12].upper()}"
        with self.database.transaction() as connection:
            connection.execute(
                """
                INSERT INTO secure_documents(id,profile_id,document_type,object_ref,original_name,mime_type,size_bytes,purpose,created_at,expires_at)
                VALUES(?,?,?,?,?,?,?,?,?,?)
                """,
                (document_id,values['profile_id'],values['document_type'],values['object_ref'],values['original_name'],values['mime_type'],values['size_bytes'],values['purpose'],utcnow(),values.get('expires_at'))
            )
        return document_id

    def get(self,document_id:str)->dict[str,Any]|None:
        with self.database.connect() as connection:
            row=connection.execute("SELECT * FROM secure_documents WHERE id=? AND deleted_at IS NULL",(document_id,)).fetchone()
        return None if row is None else dict(row)

    def list_for_profile(self,profile_id:str)->list[dict[str,Any]]:
        with self.database.connect() as connection:
            rows=connection.execute("SELECT * FROM secure_documents WHERE profile_id=? AND deleted_at IS NULL ORDER BY created_at DESC",(profile_id,)).fetchall()
        return [dict(row) for row in rows]

    def mark_deleted(self,document_id:str)->None:
        with self.database.transaction() as connection:
            connection.execute("UPDATE secure_documents SET deleted_at=? WHERE id=?",(utcnow(),document_id))
