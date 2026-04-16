from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.core.db.connection import create_connection


@dataclass(slots=True)
class SimulationJobRecord:
    id: str
    scheme_id: str
    job_code: str
    job_name: str
    solver: str
    template_name: str
    input_dir: str
    output_dir: str
    job_status: str
    run_mode: str
    operator: str
    submit_time: str
    finish_time: str


@dataclass(slots=True)
class SimulationResultRecord:
    id: str
    job_id: str
    result_type: str
    result_name: str
    file_path: str
    image_path: str
    summary: str
    compare_group: str


class SimulationRepository:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path

    def list_jobs(self, scheme_id: str) -> list[SimulationJobRecord]:
        with create_connection(self.database_path) as connection:
            rows = connection.execute(
                """
                SELECT id, scheme_id, job_code, job_name,
                       COALESCE(solver, '') AS solver,
                       COALESCE(template_name, '') AS template_name,
                       COALESCE(input_dir, '') AS input_dir,
                       COALESCE(output_dir, '') AS output_dir,
                       COALESCE(job_status, '') AS job_status,
                       COALESCE(run_mode, '') AS run_mode,
                       COALESCE(operator, '') AS operator,
                       COALESCE(submit_time, '') AS submit_time,
                       COALESCE(finish_time, '') AS finish_time
                FROM simulation_jobs
                WHERE scheme_id = ? AND is_deleted = 0
                ORDER BY updated_at DESC, created_at DESC;
                """,
                (scheme_id,),
            ).fetchall()
        return [self._job_from_row(row) for row in rows]

    def get_job(self, job_id: str) -> SimulationJobRecord | None:
        with create_connection(self.database_path) as connection:
            row = connection.execute(
                """
                SELECT id, scheme_id, job_code, job_name,
                       COALESCE(solver, '') AS solver,
                       COALESCE(template_name, '') AS template_name,
                       COALESCE(input_dir, '') AS input_dir,
                       COALESCE(output_dir, '') AS output_dir,
                       COALESCE(job_status, '') AS job_status,
                       COALESCE(run_mode, '') AS run_mode,
                       COALESCE(operator, '') AS operator,
                       COALESCE(submit_time, '') AS submit_time,
                       COALESCE(finish_time, '') AS finish_time
                FROM simulation_jobs
                WHERE id = ? AND is_deleted = 0
                LIMIT 1;
                """,
                (job_id,),
            ).fetchone()
        return self._job_from_row(row) if row is not None else None

    def create_job(
        self,
        *,
        scheme_id: str,
        job_code: str,
        job_name: str,
        solver: str,
        template_name: str,
        input_dir: str,
        output_dir: str,
        job_status: str,
        run_mode: str,
        operator: str,
    ) -> str:
        with create_connection(self.database_path) as connection:
            job_id = connection.execute("SELECT lower(hex(randomblob(16)))").fetchone()[0]
            connection.execute(
                """
                INSERT INTO simulation_jobs (
                    id, scheme_id, job_code, job_name, solver, template_name, input_dir,
                    output_dir, submit_time, finish_time, job_status, run_mode, operator,
                    created_at, updated_at, created_by, updated_by, is_deleted, remark
                ) VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, '', '', ?, ?, ?,
                    datetime('now'), datetime('now'), 'system', 'system', 0, ''
                );
                """,
                (
                    job_id,
                    scheme_id,
                    job_code,
                    job_name,
                    solver,
                    template_name,
                    input_dir,
                    output_dir,
                    job_status,
                    run_mode,
                    operator,
                ),
            )
            connection.commit()
        return job_id

    def update_job(
        self,
        job_id: str,
        *,
        job_name: str,
        solver: str,
        template_name: str,
        input_dir: str,
        output_dir: str,
        job_status: str,
        run_mode: str,
        operator: str,
        submit_time: str,
        finish_time: str,
    ) -> None:
        with create_connection(self.database_path) as connection:
            connection.execute(
                """
                UPDATE simulation_jobs
                SET job_name = ?, solver = ?, template_name = ?, input_dir = ?, output_dir = ?,
                    job_status = ?, run_mode = ?, operator = ?, submit_time = ?, finish_time = ?,
                    updated_at = datetime('now'), updated_by = 'system'
                WHERE id = ?;
                """,
                (
                    job_name,
                    solver,
                    template_name,
                    input_dir,
                    output_dir,
                    job_status,
                    run_mode,
                    operator,
                    submit_time,
                    finish_time,
                    job_id,
                ),
            )
            connection.commit()

    def list_results(self, job_id: str) -> list[SimulationResultRecord]:
        with create_connection(self.database_path) as connection:
            rows = connection.execute(
                """
                SELECT id, job_id, result_type, result_name,
                       COALESCE(file_path, '') AS file_path,
                       COALESCE(image_path, '') AS image_path,
                       COALESCE(summary, '') AS summary,
                       COALESCE(compare_group, '') AS compare_group
                FROM simulation_results
                WHERE job_id = ? AND is_deleted = 0
                ORDER BY created_at DESC;
                """,
                (job_id,),
            ).fetchall()
        return [
            SimulationResultRecord(
                id=row["id"],
                job_id=row["job_id"],
                result_type=row["result_type"],
                result_name=row["result_name"],
                file_path=row["file_path"],
                image_path=row["image_path"],
                summary=row["summary"],
                compare_group=row["compare_group"],
            )
            for row in rows
        ]

    def create_result(
        self,
        *,
        job_id: str,
        result_type: str,
        result_name: str,
        file_path: str,
        image_path: str = "",
        summary: str = "",
        compare_group: str = "",
    ) -> str:
        with create_connection(self.database_path) as connection:
            result_id = connection.execute("SELECT lower(hex(randomblob(16)))").fetchone()[0]
            connection.execute(
                """
                INSERT INTO simulation_results (
                    id, job_id, result_type, result_name, file_path, image_path, view_angle,
                    legend_range, summary, is_baseline, compare_group, created_at, updated_at,
                    created_by, updated_by, is_deleted, remark
                ) VALUES (
                    ?, ?, ?, ?, ?, ?, '', '', ?, 0, ?, datetime('now'), datetime('now'),
                    'system', 'system', 0, ''
                );
                """,
                (result_id, job_id, result_type, result_name, file_path, image_path, summary, compare_group),
            )
            connection.commit()
        return result_id

    def count_jobs(self) -> int:
        with create_connection(self.database_path) as connection:
            row = connection.execute(
                "SELECT COUNT(*) AS count_value FROM simulation_jobs WHERE is_deleted = 0;"
            ).fetchone()
        return int(row["count_value"])

    def _job_from_row(self, row) -> SimulationJobRecord:
        return SimulationJobRecord(
            id=row["id"],
            scheme_id=row["scheme_id"],
            job_code=row["job_code"],
            job_name=row["job_name"],
            solver=row["solver"],
            template_name=row["template_name"],
            input_dir=row["input_dir"],
            output_dir=row["output_dir"],
            job_status=row["job_status"],
            run_mode=row["run_mode"],
            operator=row["operator"],
            submit_time=row["submit_time"],
            finish_time=row["finish_time"],
        )
