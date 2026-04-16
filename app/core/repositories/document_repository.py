from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.core.db.connection import create_connection


@dataclass(slots=True)
class ProcessCardRecord:
    id: str
    scheme_id: str
    card_no: str
    template_name: str
    docx_path: str
    pdf_path: str
    card_status: str
    generated_at: str


@dataclass(slots=True)
class InspectionItemRecord:
    id: str
    scheme_id: str
    item_type: str
    item_name: str
    control_stage: str
    control_method: str
    acceptance_rule: str
    risk_reason: str


class DocumentRepository:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path

    def get_latest_process_card(self, scheme_id: str) -> ProcessCardRecord | None:
        with create_connection(self.database_path) as connection:
            row = connection.execute(
                """
                SELECT id, scheme_id, card_no,
                       COALESCE(template_name, '') AS template_name,
                       COALESCE(docx_path, '') AS docx_path,
                       COALESCE(pdf_path, '') AS pdf_path,
                       COALESCE(card_status, '') AS card_status,
                       COALESCE(generated_at, '') AS generated_at
                FROM process_cards
                WHERE scheme_id = ? AND is_deleted = 0
                ORDER BY generated_at DESC, created_at DESC
                LIMIT 1;
                """,
                (scheme_id,),
            ).fetchone()
        if row is None:
            return None
        return ProcessCardRecord(
            id=row["id"],
            scheme_id=row["scheme_id"],
            card_no=row["card_no"],
            template_name=row["template_name"],
            docx_path=row["docx_path"],
            pdf_path=row["pdf_path"],
            card_status=row["card_status"],
            generated_at=row["generated_at"],
        )

    def create_process_card(
        self,
        *,
        scheme_id: str,
        card_no: str,
        template_name: str,
        docx_path: str,
        pdf_path: str = "",
        card_status: str = "generated",
    ) -> str:
        with create_connection(self.database_path) as connection:
            card_id = connection.execute("SELECT lower(hex(randomblob(16)))").fetchone()[0]
            connection.execute(
                """
                INSERT INTO process_cards (
                    id, scheme_id, card_no, template_name, docx_path, pdf_path, card_status,
                    generated_at, created_at, updated_at, created_by, updated_by, is_deleted, remark
                ) VALUES (
                    ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'), datetime('now'),
                    'system', 'system', 0, ''
                );
                """,
                (card_id, scheme_id, card_no, template_name, docx_path, pdf_path, card_status),
            )
            connection.commit()
        return card_id

    def list_inspection_items(self, scheme_id: str) -> list[InspectionItemRecord]:
        with create_connection(self.database_path) as connection:
            rows = connection.execute(
                """
                SELECT id, scheme_id, item_type, item_name,
                       COALESCE(control_stage, '') AS control_stage,
                       COALESCE(control_method, '') AS control_method,
                       COALESCE(acceptance_rule, '') AS acceptance_rule,
                       COALESCE(risk_reason, '') AS risk_reason
                FROM inspection_items
                WHERE scheme_id = ? AND is_deleted = 0
                ORDER BY created_at ASC;
                """,
                (scheme_id,),
            ).fetchall()
        return [
            InspectionItemRecord(
                id=row["id"],
                scheme_id=row["scheme_id"],
                item_type=row["item_type"],
                item_name=row["item_name"],
                control_stage=row["control_stage"],
                control_method=row["control_method"],
                acceptance_rule=row["acceptance_rule"],
                risk_reason=row["risk_reason"],
            )
            for row in rows
        ]

    def replace_inspection_items(self, scheme_id: str, items: list[dict[str, str]]) -> None:
        with create_connection(self.database_path) as connection:
            connection.execute(
                """
                UPDATE inspection_items
                SET is_deleted = 1, updated_at = datetime('now'), updated_by = 'system'
                WHERE scheme_id = ? AND is_deleted = 0;
                """,
                (scheme_id,),
            )
            for item in items:
                item_id = connection.execute("SELECT lower(hex(randomblob(16)))").fetchone()[0]
                connection.execute(
                    """
                    INSERT INTO inspection_items (
                        id, scheme_id, item_type, item_name, control_stage, control_method,
                        acceptance_rule, risk_reason, created_at, updated_at, created_by, updated_by,
                        is_deleted, remark
                    ) VALUES (
                        ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'),
                        'system', 'system', 0, ''
                    );
                    """,
                    (
                        item_id,
                        scheme_id,
                        item["item_type"],
                        item["item_name"],
                        item["control_stage"],
                        item["control_method"],
                        item["acceptance_rule"],
                        item["risk_reason"],
                    ),
                )
            connection.commit()
