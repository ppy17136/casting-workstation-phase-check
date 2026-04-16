from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json

from app.core.db.connection import create_connection


@dataclass(slots=True)
class SuggestionCardRecord:
    id: str
    scheme_id: str
    job_id: str
    title: str
    suggestion_text: str
    target_params_json: str
    preconditions: str
    risk_notice: str
    confidence_score: float
    validation_status: str
    human_review_status: str


@dataclass(slots=True)
class EvidenceRecord:
    id: str
    evidence_code: str
    evidence_type: str
    title: str
    source_path: str
    excerpt: str


class AiRepository:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path

    def list_suggestions(self, scheme_id: str) -> list[SuggestionCardRecord]:
        with create_connection(self.database_path) as connection:
            rows = connection.execute(
                """
                SELECT id, scheme_id, COALESCE(job_id, '') AS job_id, title, suggestion_text,
                       COALESCE(target_params_json, '') AS target_params_json,
                       COALESCE(preconditions, '') AS preconditions,
                       COALESCE(risk_notice, '') AS risk_notice,
                       COALESCE(confidence_score, 0) AS confidence_score,
                       COALESCE(validation_status, '') AS validation_status,
                       COALESCE(human_review_status, '') AS human_review_status
                FROM ai_suggestion_cards
                WHERE scheme_id = ? AND is_deleted = 0
                ORDER BY updated_at DESC, created_at DESC;
                """,
                (scheme_id,),
            ).fetchall()
        return [self._row_to_suggestion(row) for row in rows]

    def list_pending_reviews(self, scheme_id: str | None = None) -> list[SuggestionCardRecord]:
        sql = """
            SELECT id, scheme_id, COALESCE(job_id, '') AS job_id, title, suggestion_text,
                   COALESCE(target_params_json, '') AS target_params_json,
                   COALESCE(preconditions, '') AS preconditions,
                   COALESCE(risk_notice, '') AS risk_notice,
                   COALESCE(confidence_score, 0) AS confidence_score,
                   COALESCE(validation_status, '') AS validation_status,
                   COALESCE(human_review_status, '') AS human_review_status
            FROM ai_suggestion_cards
            WHERE is_deleted = 0 AND COALESCE(human_review_status, 'pending') = 'pending'
        """
        args: tuple = ()
        if scheme_id:
            sql += " AND scheme_id = ?"
            args = (scheme_id,)
        sql += " ORDER BY updated_at DESC, created_at DESC;"
        with create_connection(self.database_path) as connection:
            rows = connection.execute(sql, args).fetchall()
        return [self._row_to_suggestion(row) for row in rows]

    def replace_generated_suggestions(
        self,
        *,
        scheme_id: str,
        job_id: str | None,
        suggestions: list[dict],
    ) -> list[str]:
        created_ids: list[str] = []
        with create_connection(self.database_path) as connection:
            if job_id:
                connection.execute(
                    """
                    UPDATE ai_suggestion_cards
                    SET is_deleted = 1, updated_at = datetime('now'), updated_by = 'system'
                    WHERE scheme_id = ? AND COALESCE(job_id, '') = ? AND is_deleted = 0;
                    """,
                    (scheme_id, job_id),
                )
            else:
                connection.execute(
                    """
                    UPDATE ai_suggestion_cards
                    SET is_deleted = 1, updated_at = datetime('now'), updated_by = 'system'
                    WHERE scheme_id = ? AND is_deleted = 0;
                    """,
                    (scheme_id,),
                )

            for suggestion in suggestions:
                suggestion_id = connection.execute("SELECT lower(hex(randomblob(16)))").fetchone()[0]
                connection.execute(
                    """
                    INSERT INTO ai_suggestion_cards (
                        id, scheme_id, job_id, title, suggestion_text, target_params_json,
                        preconditions, risk_notice, confidence_score, validation_status,
                        human_review_status, created_at, updated_at, created_by, updated_by,
                        is_deleted, remark
                    ) VALUES (
                        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'),
                        'system', 'system', 0, ''
                    );
                    """,
                    (
                        suggestion_id,
                        scheme_id,
                        job_id or "",
                        suggestion["title"],
                        suggestion["suggestion_text"],
                        json.dumps(suggestion.get("target_params", []), ensure_ascii=False),
                        suggestion.get("preconditions", ""),
                        suggestion.get("risk_notice", ""),
                        suggestion.get("confidence_score", 0.0),
                        suggestion.get("validation_status", "rule_checked"),
                        suggestion.get("human_review_status", "pending"),
                    ),
                )
                for evidence in suggestion.get("evidence_items", []):
                    evidence_id = connection.execute("SELECT lower(hex(randomblob(16)))").fetchone()[0]
                    evidence_code = connection.execute(
                        "SELECT 'EV-' || upper(substr(hex(randomblob(8)), 1, 8))"
                    ).fetchone()[0]
                    connection.execute(
                        """
                        INSERT INTO evidence_sources (
                            id, evidence_code, evidence_type, title, source_path, page_no,
                            section_name, excerpt, hash_value, created_at, updated_at,
                            created_by, updated_by, is_deleted, remark
                        ) VALUES (
                            ?, ?, ?, ?, ?, '', '', ?, '', datetime('now'), datetime('now'),
                            'system', 'system', 0, ''
                        );
                        """,
                        (
                            evidence_id,
                            evidence_code,
                            evidence.get("evidence_type", "derived"),
                            evidence.get("title", "证据"),
                            evidence.get("source_path", ""),
                            evidence.get("excerpt", ""),
                        ),
                    )
                    link_id = connection.execute("SELECT lower(hex(randomblob(16)))").fetchone()[0]
                    connection.execute(
                        """
                        INSERT INTO suggestion_evidence_links (
                            id, suggestion_id, evidence_id, link_role, match_status, created_at,
                            updated_at, created_by, updated_by, is_deleted, remark
                        ) VALUES (
                            ?, ?, ?, ?, ?, datetime('now'), datetime('now'),
                            'system', 'system', 0, ''
                        );
                        """,
                        (
                            link_id,
                            suggestion_id,
                            evidence_id,
                            evidence.get("link_role", "support"),
                            evidence.get("match_status", "derived"),
                        ),
                    )
                created_ids.append(suggestion_id)
            connection.commit()
        return created_ids

    def list_evidence(self, suggestion_id: str) -> list[EvidenceRecord]:
        with create_connection(self.database_path) as connection:
            rows = connection.execute(
                """
                SELECT es.id, es.evidence_code, es.evidence_type, es.title, es.source_path,
                       COALESCE(es.excerpt, '') AS excerpt
                FROM evidence_sources es
                JOIN suggestion_evidence_links sel ON sel.evidence_id = es.id
                WHERE sel.suggestion_id = ? AND es.is_deleted = 0 AND sel.is_deleted = 0
                ORDER BY es.created_at ASC;
                """,
                (suggestion_id,),
            ).fetchall()
        return [
            EvidenceRecord(
                id=row["id"],
                evidence_code=row["evidence_code"],
                evidence_type=row["evidence_type"],
                title=row["title"],
                source_path=row["source_path"],
                excerpt=row["excerpt"],
            )
            for row in rows
        ]

    def review_suggestion(
        self,
        *,
        suggestion_id: str,
        reviewer: str,
        decision: str,
        comment: str,
    ) -> str:
        new_status = "approved" if decision == "approve" else "rejected"
        with create_connection(self.database_path) as connection:
            connection.execute(
                """
                UPDATE ai_suggestion_cards
                SET human_review_status = ?, updated_at = datetime('now'), updated_by = ?
                WHERE id = ?;
                """,
                (new_status, reviewer, suggestion_id),
            )
            approval_id = connection.execute("SELECT lower(hex(randomblob(16)))").fetchone()[0]
            connection.execute(
                """
                INSERT INTO approval_records (
                    id, biz_type, biz_id, reviewer, decision, comment, reviewed_at, created_at,
                    updated_at, created_by, updated_by, is_deleted, remark
                ) VALUES (
                    ?, 'ai_suggestion_card', ?, ?, ?, ?, datetime('now'), datetime('now'),
                    datetime('now'), ?, ?, 0, ''
                );
                """,
                (approval_id, suggestion_id, reviewer, decision, comment, reviewer, reviewer),
            )
            connection.commit()
        return approval_id

    def _row_to_suggestion(self, row) -> SuggestionCardRecord:
        return SuggestionCardRecord(
            id=row["id"],
            scheme_id=row["scheme_id"],
            job_id=row["job_id"],
            title=row["title"],
            suggestion_text=row["suggestion_text"],
            target_params_json=row["target_params_json"],
            preconditions=row["preconditions"],
            risk_notice=row["risk_notice"],
            confidence_score=float(row["confidence_score"] or 0.0),
            validation_status=row["validation_status"],
            human_review_status=row["human_review_status"],
        )
