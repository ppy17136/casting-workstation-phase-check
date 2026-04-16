from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.core.db.connection import create_connection


@dataclass(slots=True)
class MaterialRecord:
    id: str
    material_code: str
    material_name: str
    category: str
    density: float | None
    liquidus_temp: float | None
    solidus_temp: float | None
    pouring_temp_min: float | None
    pouring_temp_max: float | None
    shrinkage_ratio: float | None
    standard_ref: str


class MaterialRepository:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path

    def list_materials(self) -> list[MaterialRecord]:
        with create_connection(self.database_path) as connection:
            rows = connection.execute(
                """
                SELECT id, material_code, material_name,
                       COALESCE(category, '') AS category,
                       density, liquidus_temp, solidus_temp,
                       pouring_temp_min, pouring_temp_max,
                       shrinkage_ratio,
                       COALESCE(standard_ref, '') AS standard_ref
                FROM materials
                WHERE is_deleted = 0
                ORDER BY material_code, material_name;
                """
            ).fetchall()
        return [self._row_to_record(row) for row in rows]

    def get_by_code(self, material_code: str) -> MaterialRecord | None:
        with create_connection(self.database_path) as connection:
            row = connection.execute(
                """
                SELECT id, material_code, material_name,
                       COALESCE(category, '') AS category,
                       density, liquidus_temp, solidus_temp,
                       pouring_temp_min, pouring_temp_max,
                       shrinkage_ratio,
                       COALESCE(standard_ref, '') AS standard_ref
                FROM materials
                WHERE material_code = ? AND is_deleted = 0
                LIMIT 1;
                """,
                (material_code,),
            ).fetchone()
        return self._row_to_record(row)

    def get_by_name(self, material_name: str) -> MaterialRecord | None:
        with create_connection(self.database_path) as connection:
            row = connection.execute(
                """
                SELECT id, material_code, material_name,
                       COALESCE(category, '') AS category,
                       density, liquidus_temp, solidus_temp,
                       pouring_temp_min, pouring_temp_max,
                       shrinkage_ratio,
                       COALESCE(standard_ref, '') AS standard_ref
                FROM materials
                WHERE material_name = ? AND is_deleted = 0
                LIMIT 1;
                """,
                (material_name,),
            ).fetchone()
        return self._row_to_record(row)

    def upsert_material(
        self,
        *,
        material_code: str,
        material_name: str,
        category: str,
        density: float | None,
        liquidus_temp: float | None,
        solidus_temp: float | None,
        pouring_temp_min: float | None,
        pouring_temp_max: float | None,
        shrinkage_ratio: float | None,
        standard_ref: str,
    ) -> str:
        with create_connection(self.database_path) as connection:
            existing = connection.execute(
                """
                SELECT id
                FROM materials
                WHERE material_code = ? AND is_deleted = 0
                LIMIT 1;
                """,
                (material_code,),
            ).fetchone()
            if existing is None:
                material_id = connection.execute("SELECT lower(hex(randomblob(16)))").fetchone()[0]
                connection.execute(
                    """
                    INSERT INTO materials (
                        id, material_code, material_name, category, density, liquidus_temp,
                        solidus_temp, pouring_temp_min, pouring_temp_max, shrinkage_ratio,
                        standard_ref, created_at, updated_at, created_by, updated_by,
                        is_deleted, remark
                    ) VALUES (
                        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'),
                        'system', 'system', 0, ''
                    );
                    """,
                    (
                        material_id,
                        material_code,
                        material_name,
                        category,
                        density,
                        liquidus_temp,
                        solidus_temp,
                        pouring_temp_min,
                        pouring_temp_max,
                        shrinkage_ratio,
                        standard_ref,
                    ),
                )
            else:
                material_id = existing["id"]
                connection.execute(
                    """
                    UPDATE materials
                    SET material_name = ?, category = ?, density = ?, liquidus_temp = ?,
                        solidus_temp = ?, pouring_temp_min = ?, pouring_temp_max = ?,
                        shrinkage_ratio = ?, standard_ref = ?, updated_at = datetime('now'),
                        updated_by = 'system'
                    WHERE id = ?;
                    """,
                    (
                        material_name,
                        category,
                        density,
                        liquidus_temp,
                        solidus_temp,
                        pouring_temp_min,
                        pouring_temp_max,
                        shrinkage_ratio,
                        standard_ref,
                        material_id,
                    ),
                )
            connection.commit()
        return material_id

    def _row_to_record(self, row) -> MaterialRecord | None:
        if row is None:
            return None
        return MaterialRecord(
            id=row["id"],
            material_code=row["material_code"],
            material_name=row["material_name"],
            category=row["category"],
            density=row["density"],
            liquidus_temp=row["liquidus_temp"],
            solidus_temp=row["solidus_temp"],
            pouring_temp_min=row["pouring_temp_min"],
            pouring_temp_max=row["pouring_temp_max"],
            shrinkage_ratio=row["shrinkage_ratio"],
            standard_ref=row["standard_ref"],
        )
