from __future__ import annotations

import json

from PySide6.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.core.config import AppPaths
from app.core.repositories.ai_repository import AiRepository, SuggestionCardRecord
from app.core.repositories.parameter_repository import ParameterRepository
from app.core.repositories.scheme_repository import SchemeRepository
from app.core.repositories.simulation_repository import SimulationRepository
from app.core.services import SuggestionGenerationService
from app.core.session import AppSession


class AiPage(QWidget):
    def __init__(self, paths: AppPaths, session: AppSession) -> None:
        super().__init__()
        self.paths = paths
        self.session = session
        self.ai_repository = AiRepository(paths.database_path)
        self.parameter_repository = ParameterRepository(paths.database_path)
        self.scheme_repository = SchemeRepository(paths.database_path)
        self.simulation_repository = SimulationRepository(paths.database_path)
        self.generator = SuggestionGenerationService()
        self.current_scheme_id: str | None = None
        self.cards: list[SuggestionCardRecord] = []

        layout = QHBoxLayout(self)
        layout.addWidget(self._build_list_box(), 2)
        layout.addWidget(self._build_detail_box(), 4)

        self.session.scheme_changed.connect(self._on_scheme_changed)

    def _build_list_box(self) -> QWidget:
        box = QGroupBox("仿真辅助建议", self)
        layout = QVBoxLayout(box)
        self.context_label = QLabel("请先选择工艺方案。", box)
        layout.addWidget(self.context_label)
        self.card_list = QListWidget(box)
        self.card_list.currentRowChanged.connect(self._on_card_selected)
        layout.addWidget(self.card_list)

        actions = QHBoxLayout()
        generate_button = QPushButton("生成建议", box)
        generate_button.clicked.connect(self._generate_cards)
        refresh_button = QPushButton("刷新", box)
        refresh_button.clicked.connect(self._reload_cards)
        actions.addWidget(generate_button)
        actions.addWidget(refresh_button)
        layout.addLayout(actions)
        return box

    def _build_detail_box(self) -> QWidget:
        box = QGroupBox("建议详情与依据", self)
        layout = QVBoxLayout(box)

        form = QFormLayout()
        self.title_label = QLabel("-", box)
        self.status_label = QLabel("-", box)
        self.confidence_label = QLabel("-", box)
        self.target_params_label = QLabel("-", box)
        form.addRow("标题", self.title_label)
        form.addRow("建议状态", self.status_label)
        form.addRow("置信度", self.confidence_label)
        form.addRow("关注参数", self.target_params_label)
        layout.addLayout(form)

        self.detail_view = QTextEdit(box)
        self.detail_view.setReadOnly(True)
        layout.addWidget(self.detail_view)

        self.evidence_view = QTextEdit(box)
        self.evidence_view.setReadOnly(True)
        self.evidence_view.setMaximumHeight(180)
        layout.addWidget(self.evidence_view)
        return box

    def _on_scheme_changed(self, scheme_id: str | None) -> None:
        self.current_scheme_id = scheme_id
        self.context_label.setText(f"当前方案：{scheme_id}" if scheme_id else "请先选择工艺方案。")
        self._reload_cards()

    def _reload_cards(self) -> None:
        self.card_list.clear()
        self.cards = []
        self._clear_detail()
        if not self.current_scheme_id:
            return
        self.cards = self.ai_repository.list_suggestions(self.current_scheme_id)
        for card in self.cards:
            QListWidgetItem(
                f"{card.title} | {card.validation_status} | {card.human_review_status or 'pending'}",
                self.card_list,
            )
        if self.cards:
            self.card_list.setCurrentRow(0)

    def _generate_cards(self) -> None:
        if not self.current_scheme_id:
            QMessageBox.warning(self, "无法生成", "请先选择工艺方案。")
            return
        scheme = self.scheme_repository.get_scheme(self.current_scheme_id)
        if scheme is None:
            QMessageBox.warning(self, "无法生成", "当前方案不存在。")
            return
        parameters = self.parameter_repository.list_by_scheme(self.current_scheme_id)
        jobs = self.simulation_repository.list_jobs(self.current_scheme_id)
        latest_job_id = jobs[0].id if jobs else None
        results = self.simulation_repository.list_results(latest_job_id) if latest_job_id else []
        suggestions = self.generator.generate(
            scheme=scheme,
            parameters=parameters,
            results=results,
        )
        self.ai_repository.replace_generated_suggestions(
            scheme_id=self.current_scheme_id,
            job_id=latest_job_id,
            suggestions=suggestions,
        )
        self._reload_cards()
        QMessageBox.information(self, "生成完成", f"已生成 {len(suggestions)} 条仿真辅助建议。")

    def _on_card_selected(self, row: int) -> None:
        if row < 0 or row >= len(self.cards):
            self._clear_detail()
            return
        card = self.cards[row]
        self.title_label.setText(card.title)
        self.status_label.setText(card.human_review_status or "pending")
        self.confidence_label.setText(f"{card.confidence_score:.2f}")
        try:
            target_params = json.loads(card.target_params_json) if card.target_params_json else []
        except json.JSONDecodeError:
            target_params = [card.target_params_json]
        self.target_params_label.setText(", ".join(target_params) if target_params else "-")
        self.detail_view.setPlainText(
            "\n".join(
                [
                    f"建议内容：{card.suggestion_text}",
                    f"前置条件：{card.preconditions or '-'}",
                    f"风险提示：{card.risk_notice or '-'}",
                    f"校验状态：{card.validation_status or '-'}",
                ]
            )
        )
        evidences = self.ai_repository.list_evidence(card.id)
        if evidences:
            self.evidence_view.setPlainText(
                "\n\n".join(
                    [
                        f"[{item.evidence_code}] {item.title}\n类型：{item.evidence_type}\n来源：{item.source_path}\n摘要：{item.excerpt}"
                        for item in evidences
                    ]
                )
            )
        else:
            self.evidence_view.setPlainText("暂无证据记录。")

    def _clear_detail(self) -> None:
        self.title_label.setText("-")
        self.status_label.setText("-")
        self.confidence_label.setText("-")
        self.target_params_label.setText("-")
        self.detail_view.clear()
        self.evidence_view.clear()
