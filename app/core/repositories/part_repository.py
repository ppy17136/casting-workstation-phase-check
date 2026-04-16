from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.core.db.connection import create_connection


@dataclass(slots=True)
class PartRecord:
    id: str
    project_id: str
    part_name: str
    part_no: str
    drawing_no: str
    material_name: str
    net_weight: float | None
    blank_weight: float | None
    length_mm: float | None
    width_mm: float | None
    height_mm: float | None
    max_wall_thickness: float | None
    min_wall_thickness: float | None
    production_qty: int | None
    quality_grade: str
    heat_treatment: str
    surface_requirement: str
    internal_quality_requirement: str


class PartRepository:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path

    def get_primary_part(self, project_id: str) -> PartRecord | None:
        with create_connection(self.database_path) as connection:
            row = connection.execute(
                """
                SELECT id, project_id, part_name,
                       COALESCE(part_no, '') AS part_no,
                       COALESCE(drawing_no, '') AS drawing_no,
                       COALESCE(material_name, '') AS material_name,
                       net_weight, blank_weight,
                       length_mm, width_mm, height_mm,
                       max_wall_thickness, min_wall_thickness,
                       production_qty,
                       COALESCE(quality_grade, '') AS quality_grade,
                       COALESCE(heat_treatment, '') AS heat_treatment,
                       COALESCE(surface_requirement, '') AS surface_requirement,
                       COALESCE(internal_quality_requirement, '') AS internal_quality_requirement
                FROM parts
                WHERE project_id = ? AND is_deleted = 0
                ORDER BY updated_at DESC, created_at DESC
                LIMIT 1;
                """,
                (project_id,),
            ).fetchone()
        return self._row_to_record(row)

    def get_part(self, part_id: str) -> PartRecord | None:
        with create_connection(self.database_path) as connection:
            row = connection.execute(
                """
                SELECT id, project_id, part_name,
                       COALESCE(part_no, '') AS part_no,
                       COALESCE(drawing_no, '') AS drawing_no,
                       COALESCE(material_name, '') AS material_name,
                       net_weight, blank_weight,
                       length_mm, width_mm, height_mm,
                       max_wall_thickness, min_wall_thickness,
                       production_qty,
                       COALESCE(quality_grade, '') AS quality_grade,
                       COALESCE(heat_treatment, '') AS heat_treatment,
                       COALESCE(surface_requirement, '') AS surface_requirement,
                       COALESCE(internal_quality_requirement, '') AS internal_quality_requirement
                FROM parts
                WHERE id = ? AND is_deleted = 0
                LIMIT 1;
                """,
                (part_id,),
            ).fetchone()
        return self._row_to_record(row)

    def create_default_part(self, project_id: str, part_name: str) -> str:
        with create_connection(self.database_path) as connection:
            part_id = connection.execute("SELECT lower(hex(randomblob(16)))").fetchone()[0]
            connection.execute(
                """
                INSERT INTO parts (
                    id, project_id, part_name, part_no, drawing_no, material_name,
                    created_at, updated_at, created_by, updated_by, is_deleted, remark
                ) VALUES (
                    ?, ?, ?, '', '', '', datetime('now'), datetime('now'),
                    'system', 'system', 0, ''
                );
                """,
                (part_id, project_id, part_name),
            )
            connection.commit()
        return part_id

    def update_part(
        self,
        part_id: str,
        *,
        part_name: str,
        part_no: str,
        drawing_no: str,
        material_name: str,
        net_weight: float | None,
        blank_weight: float | None,
        length_mm: float | None,
        width_mm: float | None,
        height_mm: float | None,
        max_wall_thickness: float | None,
        min_wall_thickness: float | None,
        production_qty: int | None,
        quality_grade: str,
        heat_treatment: str,
        surface_requirement: str,
        internal_quality_requirement: str,
    ) -> None:
        with create_connection(self.database_path) as connection:
            connection.execute(
                """
                UPDATE parts
                SET part_name = ?, part_no = ?, drawing_no = ?, material_name = ?,
                    net_weight = ?, blank_weight = ?, length_mm = ?, width_mm = ?,
                    height_mm = ?, max_wall_thickness = ?, min_wall_thickness = ?,
                    production_qty = ?, quality_grade = ?, heat_treatment = ?,
                    surface_requirement = ?, internal_quality_requirement = ?,
                    updated_at = datetime('now'), updated_by = 'system'
                WHERE id = ?;
                """,
                (
                    part_name,
                    part_no,
                    drawing_no,
                    material_name,
                    net_weight,
                    blank_weight,
                    length_mm,
                    width_mm,
                    height_mm,
                    max_wall_thickness,
                    min_wall_thickness,
                    production_qty,
                    quality_grade,
                    heat_treatment,
                    surface_requirement,
                    internal_quality_requirement,
                    part_id,
                ),
            )
            connection.commit()

    def _row_to_record(self, row) -> PartRecord | None:
        if row is None:
            return None
        return PartRecord(
            id=row["id"],
            project_id=row["project_id"],
            part_name=row["part_name"],
            part_no=row["part_no"],
            drawing_no=row["drawing_no"],
            material_name=row["material_name"],
            net_weight=row["net_weight"],
            blank_weight=row["blank_weight"],
            length_mm=row["length_mm"],
            width_mm=row["width_mm"],
            height_mm=row["height_mm"],
            max_wall_thickness=row["max_wall_thickness"],
            min_wall_thickness=row["min_wall_thickness"],
            production_qty=row["production_qty"],
            quality_grade=row["quality_grade"],
            heat_treatment=row["heat_treatment"],
            surface_requirement=row["surface_requirement"],
            internal_quality_requirement=row["internal_quality_requirement"],
        )
