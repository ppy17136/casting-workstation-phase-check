from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.core.db.connection import create_connection


@dataclass(slots=True)
class SettingRecord:
    id: str
    setting_key: str
    setting_value: str
    setting_group: str


class SettingsRepository:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path

    def list_settings(self, setting_group: str | None = None) -> list[SettingRecord]:
        sql = """
            SELECT id, setting_key, COALESCE(setting_value, '') AS setting_value,
                   COALESCE(setting_group, '') AS setting_group
            FROM app_settings
            WHERE is_deleted = 0
        """
        args: tuple = ()
        if setting_group:
            sql += " AND setting_group = ?"
            args = (setting_group,)
        sql += " ORDER BY setting_group, setting_key;"
        with create_connection(self.database_path) as connection:
            rows = connection.execute(sql, args).fetchall()
        return [
            SettingRecord(
                id=row["id"],
                setting_key=row["setting_key"],
                setting_value=row["setting_value"],
                setting_group=row["setting_group"],
            )
            for row in rows
        ]

    def get_setting(self, setting_key: str, default: str = "") -> str:
        with create_connection(self.database_path) as connection:
            row = connection.execute(
                """
                SELECT COALESCE(setting_value, '') AS setting_value
                FROM app_settings
                WHERE setting_key = ? AND is_deleted = 0
                LIMIT 1;
                """,
                (setting_key,),
            ).fetchone()
        return row["setting_value"] if row is not None else default

    def set_setting(self, *, setting_key: str, setting_value: str, setting_group: str) -> str:
        with create_connection(self.database_path) as connection:
            existing = connection.execute(
                """
                SELECT id
                FROM app_settings
                WHERE setting_key = ? AND is_deleted = 0
                LIMIT 1;
                """,
                (setting_key,),
            ).fetchone()
            if existing is None:
                setting_id = connection.execute("SELECT lower(hex(randomblob(16)))").fetchone()[0]
                connection.execute(
                    """
                    INSERT INTO app_settings (
                        id, setting_key, setting_value, setting_group, created_at, updated_at,
                        created_by, updated_by, is_deleted, remark
                    ) VALUES (
                        ?, ?, ?, ?, datetime('now'), datetime('now'),
                        'system', 'system', 0, ''
                    );
                    """,
                    (setting_id, setting_key, setting_value, setting_group),
                )
            else:
                setting_id = existing["id"]
                connection.execute(
                    """
                    UPDATE app_settings
                    SET setting_value = ?, setting_group = ?, updated_at = datetime('now'),
                        updated_by = 'system'
                    WHERE id = ?;
                    """,
                    (setting_value, setting_group, setting_id),
                )
            connection.commit()
        return setting_id
