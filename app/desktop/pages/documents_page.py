from __future__ import annotations

from PySide6.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.core.config import AppPaths
from app.core.repositories.document_repository import DocumentRepository
from app.core.repositories.parameter_repository import ParameterRepository
from app.core.repositories.part_repository import PartRepository
from app.core.repositories.project_repository import ProjectRepository
from app.core.repositories.scheme_repository import SchemeRepository
from app.core.services import DocumentGenerationService
from app.core.session import AppSession


class DocumentsPage(QWidget):
    def __init__(self, paths: AppPaths, session: AppSession) -> None:
        super().__init__()
        self.paths = paths
        self.session = session
        self.project_repository = ProjectRepository(paths.database_path)
        self.part_repository = PartRepository(paths.database_path)
        self.scheme_repository = SchemeRepository(paths.database_path)
        self.parameter_repository = ParameterRepository(paths.database_path)
        self.document_repository = DocumentRepository(paths.database_path)
        self.document_service = DocumentGenerationService(self.document_repository)
        self.current_project_id: str | None = None
        self.current_part_id: str | None = None
        self.current_scheme_id: str | None = None

        layout = QVBoxLayout(self)
        layout.addWidget(self._build_context_box())
        layout.addWidget(self._build_result_box())
        layout.addWidget(self._build_checklist_box(), 1)

        self.session.project_changed.connect(self._on_project_changed)
        self.session.scheme_changed.connect(self._on_scheme_changed)

    def _build_context_box(self) -> QWidget:
        box = QGroupBox("工艺文件输出", self)
        layout = QVBoxLayout(box)

        form = QFormLayout()
        self.context_label = QLabel("请先选择项目与工艺方案。", box)
        self.card_path_label = QLabel("-", box)
        self.checklist_path_label = QLabel("-", box)
        form.addRow("当前上下文", self.context_label)
        form.addRow("工艺卡文件", self.card_path_label)
        form.addRow("质检清单文件", self.checklist_path_label)
        layout.addLayout(form)

        actions = QHBoxLayout()
        generate_button = QPushButton("生成工艺卡与质检清单", box)
        generate_button.clicked.connect(self._generate_documents)
        refresh_button = QPushButton("刷新记录", box)
        refresh_button.clicked.connect(self._refresh_latest_card)
        actions.addWidget(generate_button)
        actions.addWidget(refresh_button)
        actions.addStretch(1)
        layout.addLayout(actions)
        return box

    def _build_result_box(self) -> QWidget:
        box = QGroupBox("工艺卡摘要", self)
        layout = QVBoxLayout(box)
        self.summary_view = QTextEdit(box)
        self.summary_view.setReadOnly(True)
        layout.addWidget(self.summary_view)
        return box

    def _build_checklist_box(self) -> QWidget:
        box = QGroupBox("质检与缺陷预防清单", self)
        layout = QVBoxLayout(box)
        self.checklist_table = QTableWidget(0, 6, box)
        self.checklist_table.setHorizontalHeaderLabels(
            ["类别", "项目", "控制阶段", "控制方法", "验收规则", "风险说明"]
        )
        layout.addWidget(self.checklist_table)
        return box

    def _on_project_changed(self, current_project) -> None:
        if current_project is None:
            self.current_project_id = None
            self.current_part_id = None
            self.context_label.setText("请先选择项目与工艺方案。")
            return
        self.current_project_id = current_project.project_id
        self.current_part_id = current_project.part_id
        self._refresh_context()

    def _on_scheme_changed(self, scheme_id: str | None) -> None:
        self.current_scheme_id = scheme_id
        self._refresh_context()
        self._refresh_latest_card()

    def _refresh_context(self) -> None:
        if not self.current_project_id:
            self.context_label.setText("请先选择项目与工艺方案。")
            return
        if not self.current_scheme_id:
            self.context_label.setText(f"当前项目：{self.current_project_id}，尚未选择工艺方案。")
            return
        self.context_label.setText(
            f"当前项目：{self.current_project_id} | 当前方案：{self.current_scheme_id}"
        )

    def _refresh_latest_card(self) -> None:
        self.card_path_label.setText("-")
        self.checklist_path_label.setText("-")
        self.summary_view.clear()
        self.checklist_table.setRowCount(0)
        if not self.current_scheme_id:
            return

        latest_card = self.document_repository.get_latest_process_card(self.current_scheme_id)
        if latest_card is not None:
            self.card_path_label.setText(latest_card.docx_path or "-")
            checklist_path = latest_card.docx_path.replace(
                "_process_card.docx",
                "_inspection_checklist.md",
            )
            self.checklist_path_label.setText(checklist_path)
            self.summary_view.setPlainText(
                "\n".join(
                    [
                        f"卡号：{latest_card.card_no}",
                        f"模板：{latest_card.template_name}",
                        f"状态：{latest_card.card_status}",
                        f"生成时间：{latest_card.generated_at}",
                    ]
                )
            )

        for item in self.document_repository.list_inspection_items(self.current_scheme_id):
            row = self.checklist_table.rowCount()
            self.checklist_table.insertRow(row)
            values = [
                item.item_type,
                item.item_name,
                item.control_stage,
                item.control_method,
                item.acceptance_rule,
                item.risk_reason,
            ]
            for column, value in enumerate(values):
                self.checklist_table.setItem(row, column, QTableWidgetItem(value))

    def _generate_documents(self) -> None:
        if not self.current_project_id or not self.current_part_id or not self.current_scheme_id:
            QMessageBox.warning(self, "无法生成", "请先在项目中心和工艺方案页完成项目上下文选择。")
            return

        project = self.project_repository.get_project(self.current_project_id)
        part = self.part_repository.get_part(self.current_part_id)
        scheme = self.scheme_repository.get_scheme(self.current_scheme_id)
        parameters = self.parameter_repository.list_by_scheme(self.current_scheme_id)
        if project is None or part is None or scheme is None:
            QMessageBox.warning(self, "无法生成", "当前项目、零件或方案数据不完整。")
            return

        bundle = self.document_service.generate_bundle(
            project=project,
            part=part,
            scheme=scheme,
            parameters=parameters,
        )
        self.card_path_label.setText(str(bundle.card_path))
        self.checklist_path_label.setText(str(bundle.checklist_path))
        self._refresh_latest_card()
        QMessageBox.information(
            self,
            "生成完成",
            f"已生成阶段工艺卡：\n{bundle.card_path}\n\n已生成缺陷预防/质检清单：\n{bundle.checklist_path}",
        )
