from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.core.db.connection import create_connection


@dataclass(slots=True)
class ParameterRecord:
    id: str
    scheme_id: str
    param_group: str
    param_code: str
    param_name: str
    param_value: str
    param_unit: str
    value_type: str
    source_type: str
    calc_formula: str


class ParameterRepository:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path

    def list_by_scheme(self, scheme_id: str) -> list[ParameterRecord]:
        with create_connection(self.database_path) as connection:
            rows = connection.execute(
                """
                SELECT id, scheme_id, param_group, param_code, param_name,
                       COALESCE(param_value, '') AS param_value,
                       COALESCE(param_unit, '') AS param_unit,
                       COALESCE(value_type, '') AS value_type,
                       COALESCE(source_type, '') AS source_type,
                       COALESCE(calc_formula, '') AS calc_formula
                FROM process_parameters
                WHERE scheme_id = ? AND is_deleted = 0
                ORDER BY param_group, param_code;
                """,
                (scheme_id,),
            ).fetchall()
        return [
            ParameterRecord(
                id=row["id"],
                scheme_id=row["scheme_id"],
                param_group=row["param_group"],
                param_code=row["param_code"],
                param_name=row["param_name"],
                param_value=row["param_value"],
                param_unit=row["param_unit"],
                value_type=row["value_type"],
                source_type=row["source_type"],
                calc_formula=row["calc_formula"],
            )
            for row in rows
        ]

    def replace_for_scheme(self, scheme_id: str, parameters: list[dict[str, str]]) -> None:
        with create_connection(self.database_path) as connection:
            connection.execute(
                """
                UPDATE process_parameters
                SET is_deleted = 1, updated_at = datetime('now'), updated_by = 'system'
                WHERE scheme_id = ? AND is_deleted = 0;
                """,
                (scheme_id,),
            )
            for parameter in parameters:
                parameter_id = connection.execute(
                    "SELECT lower(hex(randomblob(16)))"
                ).fetchone()[0]
                connection.execute(
                    """
                    INSERT INTO process_parameters (
                        id, scheme_id, param_group, param_code, param_name, param_value,
                        param_unit, value_type, source_type, source_ref, calc_formula,
                        is_key_param, created_at, updated_at, created_by, updated_by,
                        is_deleted, remark
                    ) VALUES (
                        ?, ?, ?, ?, ?, ?, ?, ?, ?, '', ?, 0,
                        datetime('now'), datetime('now'), 'system', 'system', 0, ''
                    );
                    """,
                    (
                        parameter_id,
                        scheme_id,
                        parameter["param_group"],
                        parameter["param_code"],
                        parameter["param_name"],
                        parameter["param_value"],
                        parameter["param_unit"],
                        parameter["value_type"],
                        parameter["source_type"],
                        parameter["calc_formula"],
                    ),
                )
            connection.commit()
