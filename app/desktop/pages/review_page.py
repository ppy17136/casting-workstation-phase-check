from __future__ import annotations

from PySide6.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
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
from app.core.session import AppSession


class ReviewPage(QWidget):
    def __init__(self, paths: AppPaths, session: AppSession) -> None:
        super().__init__()
        self.paths = paths
        self.session = session
        self.repository = AiRepository(paths.database_path)
        self.current_scheme_id: str | None = None
        self.cards: list[SuggestionCardRecord] = []
        self.current_card_id: str | None = None

        layout = QHBoxLayout(self)
        layout.addWidget(self._build_list_box(), 2)
        layout.addWidget(self._build_review_box(), 4)

        self.session.scheme_changed.connect(self._on_scheme_changed)

    def _build_list_box(self) -> QWidget:
        box = QGroupBox("待审核辅助建议", self)
        layout = QVBoxLayout(box)
        self.context_label = QLabel("请先选择工艺方案。", box)
        layout.addWidget(self.context_label)
        self.card_list = QListWidget(box)
        self.card_list.currentRowChanged.connect(self._on_card_selected)
        layout.addWidget(self.card_list)
        refresh_button = QPushButton("刷新", box)
        refresh_button.clicked.connect(self._reload_cards)
        layout.addWidget(refresh_button)
        return box

    def _build_review_box(self) -> QWidget:
        box = QGroupBox("人工审核记录", self)
        layout = QVBoxLayout(box)

        form = QFormLayout()
        self.title_label = QLabel("-", box)
        self.reviewer_edit = QLineEdit(box)
        self.reviewer_edit.setText("system")
        form.addRow("建议标题", self.title_label)
        form.addRow("审核人", self.reviewer_edit)
        layout.addLayout(form)

        self.detail_view = QTextEdit(box)
        self.detail_view.setReadOnly(True)
        layout.addWidget(self.detail_view)

        self.comment_edit = QTextEdit(box)
        self.comment_edit.setPlaceholderText("填写通过、暂缓或退回的原因。")
        self.comment_edit.setMaximumHeight(120)
        layout.addWidget(self.comment_edit)

        actions = QHBoxLayout()
        approve_button = QPushButton("通过", box)
        approve_button.clicked.connect(lambda: self._review("approve"))
        reject_button = QPushButton("退回", box)
        reject_button.clicked.connect(lambda: self._review("reject"))
        actions.addWidget(approve_button)
        actions.addWidget(reject_button)
        layout.addLayout(actions)
        return box

    def _on_scheme_changed(self, scheme_id: str | None) -> None:
        self.current_scheme_id = scheme_id
        self.context_label.setText(f"当前方案：{scheme_id}" if scheme_id else "请先选择工艺方案。")
        self._reload_cards()

    def _reload_cards(self) -> None:
        self.card_list.clear()
        self.cards = self.repository.list_pending_reviews(self.current_scheme_id)
        self.current_card_id = None
        self.title_label.setText("-")
        self.detail_view.clear()
        self.comment_edit.clear()
        for card in self.cards:
            QListWidgetItem(f"{card.title} | {card.validation_status}", self.card_list)
        if self.cards:
            self.card_list.setCurrentRow(0)

    def _on_card_selected(self, row: int) -> None:
        if row < 0 or row >= len(self.cards):
            self.current_card_id = None
            self.title_label.setText("-")
            self.detail_view.clear()
            return
        card = self.cards[row]
        self.current_card_id = card.id
        self.title_label.setText(card.title)
        self.detail_view.setPlainText(
            "\n".join(
                [
                    f"建议内容：{card.suggestion_text}",
                    f"前置条件：{card.preconditions or '-'}",
                    f"风险提示：{card.risk_notice or '-'}",
                    f"置信度：{card.confidence_score:.2f}",
                ]
            )
        )

    def _review(self, decision: str) -> None:
        if not self.current_card_id:
            QMessageBox.warning(self, "无法审核", "请先选择一条建议。")
            return
        reviewer = self.reviewer_edit.text().strip() or "system"
        comment = self.comment_edit.toPlainText().strip()
        self.repository.review_suggestion(
            suggestion_id=self.current_card_id,
            reviewer=reviewer,
            decision=decision,
            comment=comment,
        )
        QMessageBox.information(self, "审核完成", "辅助建议状态已更新。")
        self._reload_cards()
