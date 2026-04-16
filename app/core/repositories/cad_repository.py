from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.core.db.connection import create_connection


@dataclass(slots=True)
class CadModelRecord:
    id: str
    scheme_id: str
    cad_system: str
    file_type: str
    file_path: str


@dataclass(slots=True)
class CadExportRecord:
    id: str
    cad_model_id: str
    export_type: str
    export_path: str
    export_status: str
    bridge_version: str


class CadRepository:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path

    def get_model_for_scheme(self, scheme_id: str) -> CadModelRecord | None:
        with create_connection(self.database_path) as connection:
            row = connection.execute(
                """
                SELECT id, scheme_id, cad_system, file_type, file_path
                FROM cad_models
                WHERE scheme_id = ? AND is_deleted = 0
                ORDER BY updated_at DESC, created_at DESC
                LIMIT 1;
                """,
                (scheme_id,),
            ).fetchone()
        if row is None:
            return None
        return CadModelRecord(
            id=row["id"],
            scheme_id=row["scheme_id"],
            cad_system=row["cad_system"],
            file_type=row["file_type"],
            file_path=row["file_path"],
        )

    def upsert_model(
        self,
        *,
        scheme_id: str,
        cad_system: str,
        file_type: str,
        file_path: str,
    ) -> str:
        existing = self.get_model_for_scheme(scheme_id)
        with create_connection(self.database_path) as connection:
            if existing is None:
                model_id = connection.execute("SELECT lower(hex(randomblob(16)))").fetchone()[0]
                connection.execute(
                    """
                    INSERT INTO cad_models (
                        id, scheme_id, cad_system, file_type, file_path, created_at, updated_at,
                        created_by, updated_by, is_deleted, remark
                    ) VALUES (
                        ?, ?, ?, ?, ?, datetime('now'), datetime('now'),
                        'system', 'system', 0, ''
                    );
                    """,
                    (model_id, scheme_id, cad_system, file_type, file_path),
                )
            else:
                model_id = existing.id
                connection.execute(
                    """
                    UPDATE cad_models
                    SET cad_system = ?, file_type = ?, file_path = ?, last_sync_at = datetime('now'),
                        updated_at = datetime('now'), updated_by = 'system'
                    WHERE id = ?;
                    """,
                    (cad_system, file_type, file_path, model_id),
                )
            connection.commit()
        return model_id

    def create_export_record(
        self,
        *,
        cad_model_id: str,
        export_type: str,
        export_path: str,
        export_status: str,
        bridge_version: str = "",
    ) -> str:
        with create_connection(self.database_path) as connection:
            export_id = connection.execute("SELECT lower(hex(randomblob(16)))").fetchone()[0]
            connection.execute(
                """
                INSERT INTO cad_exports (
                    id, cad_model_id, export_type, export_path, export_status, bridge_version,
                    created_at, updated_at, created_by, updated_by, is_deleted, remark
                ) VALUES (
                    ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'),
                    'system', 'system', 0, ''
                );
                """,
                (export_id, cad_model_id, export_type, export_path, export_status, bridge_version),
            )
            connection.commit()
        return export_id

    def list_exports(self, cad_model_id: str) -> list[CadExportRecord]:
        with create_connection(self.database_path) as connection:
            rows = connection.execute(
                """
                SELECT id, cad_model_id, export_type, export_path,
                       COALESCE(export_status, '') AS export_status,
                       COALESCE(bridge_version, '') AS bridge_version
                FROM cad_exports
                WHERE cad_model_id = ? AND is_deleted = 0
                ORDER BY created_at DESC;
                """,
                (cad_model_id,),
            ).fetchall()
        return [
            CadExportRecord(
                id=row["id"],
                cad_model_id=row["cad_model_id"],
                export_type=row["export_type"],
                export_path=row["export_path"],
                export_status=row["export_status"],
                bridge_version=row["bridge_version"],
            )
            for row in rows
        ]
