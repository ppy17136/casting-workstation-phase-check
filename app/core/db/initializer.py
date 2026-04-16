from __future__ import annotations

from pathlib import Path
import sqlite3

from app.core.db.connection import create_connection
from app.core.runtime import resource_path


SCHEMA_PATH = resource_path("app", "core", "db", "schema.sql")


def initialize_database(database_path: Path) -> None:
    """Create all tables and seed minimal configuration if missing."""
    database_path.parent.mkdir(parents=True, exist_ok=True)
    schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")

    with create_connection(database_path) as connection:
        connection.executescript(schema_sql)
        _seed_settings(connection)
        connection.commit()


def _seed_settings(connection: sqlite3.Connection) -> None:
    default_settings = {
        "app.theme": "light",
        "app.language": "zh-CN",
        "ai.mode": "disabled",
        "integration.solidworks.bridge_path": "",
        "integration.procast.executable_path": "",
    }
    for key, value in default_settings.items():
        connection.execute(
            """
            INSERT INTO app_settings (
                id, setting_key, setting_value, setting_group,
                created_at, updated_at, created_by, updated_by, is_deleted, remark
            )
            SELECT lower(hex(randomblob(16))), ?, ?, ?, datetime('now'), datetime('now'),
                   'system', 'system', 0, ''
            WHERE NOT EXISTS (
                SELECT 1 FROM app_settings WHERE setting_key = ? AND is_deleted = 0
            );
            """,
            (key, value, key.split(".", maxsplit=1)[0], key),
        )
