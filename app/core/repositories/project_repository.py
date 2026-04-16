from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.core.db.connection import create_connection


@dataclass(slots=True)
class ProjectRecord:
    id: str
    project_code: str
    project_name: str
    project_type: str
    casting_method: str
    status: str
    owner: str
    root_dir: str


class ProjectRepository:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path

    def list_projects(self) -> list[ProjectRecord]:
        with create_connection(self.database_path) as connection:
            rows = connection.execute(
                """
                SELECT id, project_code, project_name,
                       COALESCE(project_type, '') AS project_type,
                       COALESCE(casting_method, '') AS casting_method,
                       COALESCE(status, '') AS status,
                       COALESCE(owner, '') AS owner,
                       COALESCE(root_dir, '') AS root_dir
                FROM projects
                WHERE is_deleted = 0
                ORDER BY updated_at DESC, created_at DESC;
                """
            ).fetchall()
        return [
            ProjectRecord(
                id=row["id"],
                project_code=row["project_code"],
                project_name=row["project_name"],
                project_type=row["project_type"],
                casting_method=row["casting_method"],
                status=row["status"],
                owner=row["owner"],
                root_dir=row["root_dir"],
            )
            for row in rows
        ]

    def get_project(self, project_id: str) -> ProjectRecord | None:
        with create_connection(self.database_path) as connection:
            row = connection.execute(
                """
                SELECT id, project_code, project_name,
                       COALESCE(project_type, '') AS project_type,
                       COALESCE(casting_method, '') AS casting_method,
                       COALESCE(status, '') AS status,
                       COALESCE(owner, '') AS owner,
                       COALESCE(root_dir, '') AS root_dir
                FROM projects
                WHERE id = ? AND is_deleted = 0
                LIMIT 1;
                """,
                (project_id,),
            ).fetchone()
        if row is None:
            return None
        return ProjectRecord(
            id=row["id"],
            project_code=row["project_code"],
            project_name=row["project_name"],
            project_type=row["project_type"],
            casting_method=row["casting_method"],
            status=row["status"],
            owner=row["owner"],
            root_dir=row["root_dir"],
        )

    def create_project(
        self,
        project_code: str,
        project_name: str,
        owner: str,
        root_dir: str,
        project_type: str = "创新训练项目",
        casting_method: str = "砂型铸造",
        status: str = "草稿",
    ) -> str:
        with create_connection(self.database_path) as connection:
            project_id = connection.execute("SELECT lower(hex(randomblob(16)))").fetchone()[0]
            connection.execute(
                """
                INSERT INTO projects (
                    id, project_code, project_name, project_type, casting_method, status,
                    owner, root_dir, created_at, updated_at, created_by, updated_by,
                    is_deleted, remark
                ) VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'),
                    'system', 'system', 0, ''
                );
                """,
                (
                    project_id,
                    project_code,
                    project_name,
                    project_type,
                    casting_method,
                    status,
                    owner,
                    root_dir,
                ),
            )
            connection.commit()
            return project_id

    def update_project(
        self,
        project_id: str,
        *,
        project_name: str,
        project_type: str,
        casting_method: str,
        status: str,
        owner: str,
        root_dir: str,
    ) -> None:
        with create_connection(self.database_path) as connection:
            connection.execute(
                """
                UPDATE projects
                SET project_name = ?, project_type = ?, casting_method = ?, status = ?,
                    owner = ?, root_dir = ?, updated_at = datetime('now'),
                    updated_by = 'system'
                WHERE id = ?;
                """,
                (
                    project_name,
                    project_type,
                    casting_method,
                    status,
                    owner,
                    root_dir,
                    project_id,
                ),
            )
            connection.commit()

    def count_projects(self) -> int:
        with create_connection(self.database_path) as connection:
            row = connection.execute(
                "SELECT COUNT(*) AS count_value FROM projects WHERE is_deleted = 0;"
            ).fetchone()
        return int(row["count_value"])

    def latest_environment_status(self) -> dict[str, str]:
        with create_connection(self.database_path) as connection:
            row = connection.execute(
                """
                SELECT solidworks_found, solidworks_version, procast_found, procast_version, llm_mode
                FROM environment_checks
                WHERE is_deleted = 0
                ORDER BY last_checked_at DESC, created_at DESC
                LIMIT 1;
                """
            ).fetchone()

        if row is None:
            return {"solidworks": "未知", "procast": "未知", "llm": "未知"}

        solidworks_status = "未检测"
        if row["solidworks_found"]:
            solidworks_status = "已检测"
            if row["solidworks_version"]:
                solidworks_status = f"已检测 {row['solidworks_version']}"

        procast_status = "未检测"
        if row["procast_found"]:
            procast_status = "已检测"
            if row["procast_version"]:
                procast_status = f"已检测 {row['procast_version']}"

        return {
            "solidworks": solidworks_status,
            "procast": procast_status,
            "llm": row["llm_mode"] or "disabled",
        }
