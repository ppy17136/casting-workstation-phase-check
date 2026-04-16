from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.core.db.connection import create_connection


@dataclass(slots=True)
class SchemeRecord:
    id: str
    project_id: str
    part_id: str
    scheme_code: str
    scheme_name: str
    version_no: str
    scheme_status: str
    mold_type: str
    parting_method: str
    pouring_position: str
    gating_type: str
    notes: str


class SchemeRepository:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path

    def list_schemes(self, project_id: str) -> list[SchemeRecord]:
        with create_connection(self.database_path) as connection:
            rows = connection.execute(
                """
                SELECT id, project_id, part_id, scheme_code, scheme_name, version_no,
                       COALESCE(scheme_status, '') AS scheme_status,
                       COALESCE(mold_type, '') AS mold_type,
                       COALESCE(parting_method, '') AS parting_method,
                       COALESCE(pouring_position, '') AS pouring_position,
                       COALESCE(gating_type, '') AS gating_type,
                       COALESCE(notes, '') AS notes
                FROM process_schemes
                WHERE project_id = ? AND is_deleted = 0
                ORDER BY updated_at DESC, created_at DESC;
                """,
                (project_id,),
            ).fetchall()
        return [self._row_to_record(row) for row in rows]

    def get_scheme(self, scheme_id: str) -> SchemeRecord | None:
        with create_connection(self.database_path) as connection:
            row = connection.execute(
                """
                SELECT id, project_id, part_id, scheme_code, scheme_name, version_no,
                       COALESCE(scheme_status, '') AS scheme_status,
                       COALESCE(mold_type, '') AS mold_type,
                       COALESCE(parting_method, '') AS parting_method,
                       COALESCE(pouring_position, '') AS pouring_position,
                       COALESCE(gating_type, '') AS gating_type,
                       COALESCE(notes, '') AS notes
                FROM process_schemes
                WHERE id = ? AND is_deleted = 0
                LIMIT 1;
                """,
                (scheme_id,),
            ).fetchone()
        return self._row_to_record(row)

    def create_scheme(
        self,
        *,
        project_id: str,
        part_id: str,
        scheme_code: str,
        scheme_name: str,
        version_no: str,
    ) -> str:
        with create_connection(self.database_path) as connection:
            scheme_id = connection.execute("SELECT lower(hex(randomblob(16)))").fetchone()[0]
            connection.execute(
                """
                INSERT INTO process_schemes (
                    id, project_id, part_id, scheme_code, scheme_name, version_no,
                    scheme_status, mold_type, parting_method, pouring_position,
                    gating_type, notes, created_at, updated_at, created_by, updated_by,
                    is_deleted, remark
                ) VALUES (
                    ?, ?, ?, ?, ?, ?, 'draft', '', '', '', '', '',
                    datetime('now'), datetime('now'), 'system', 'system', 0, ''
                );
                """,
                (scheme_id, project_id, part_id, scheme_code, scheme_name, version_no),
            )
            connection.commit()
        return scheme_id

    def update_scheme(
        self,
        scheme_id: str,
        *,
        scheme_name: str,
        version_no: str,
        scheme_status: str,
        mold_type: str,
        parting_method: str,
        pouring_position: str,
        gating_type: str,
        notes: str,
    ) -> None:
        with create_connection(self.database_path) as connection:
            connection.execute(
                """
                UPDATE process_schemes
                SET scheme_name = ?, version_no = ?, scheme_status = ?, mold_type = ?,
                    parting_method = ?, pouring_position = ?, gating_type = ?, notes = ?,
                    updated_at = datetime('now'), updated_by = 'system'
                WHERE id = ?;
                """,
                (
                    scheme_name,
                    version_no,
                    scheme_status,
                    mold_type,
                    parting_method,
                    pouring_position,
                    gating_type,
                    notes,
                    scheme_id,
                ),
            )
            connection.commit()

    def _row_to_record(self, row) -> SchemeRecord | None:
        if row is None:
            return None
        return SchemeRecord(
            id=row["id"],
            project_id=row["project_id"],
            part_id=row["part_id"],
            scheme_code=row["scheme_code"],
            scheme_name=row["scheme_name"],
            version_no=row["version_no"],
            scheme_status=row["scheme_status"],
            mold_type=row["mold_type"],
            parting_method=row["parting_method"],
            pouring_position=row["pouring_position"],
            gating_type=row["gating_type"],
            notes=row["notes"],
        )
