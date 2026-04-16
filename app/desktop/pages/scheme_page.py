from __future__ import annotations

from PySide6.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QInputDialog,
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
from app.core.repositories.scheme_repository import SchemeRecord, SchemeRepository
from app.core.session import AppSession


class SchemePage(QWidget):
    def __init__(self, paths: AppPaths, session: AppSession) -> None:
        super().__init__()
        self.paths = paths
        self.session = session
        self.repository = SchemeRepository(paths.database_path)
        self.schemes: list[SchemeRecord] = []
        self.current_scheme_id: str | None = None

        layout = QHBoxLayout(self)
        layout.addWidget(self._build_list_panel(), 2)
        layout.addWidget(self._build_form_panel(), 4)
        layout.addWidget(self._build_notes_panel(), 2)

        self.session.project_changed.connect(self._on_project_changed)

    def _build_list_panel(self) -> QWidget:
        box = QGroupBox("工艺方案", self)
        wrapper = QVBoxLayout(box)
        self.project_hint = QLabel("请先在项目中心选择项目。", box)
        wrapper.addWidget(self.project_hint)
        self.scheme_list = QListWidget(box)
        self.scheme_list.currentRowChanged.connect(self._on_scheme_selected)
        wrapper.addWidget(self.scheme_list)

        create_button = QPushButton("新建方案", box)
        create_button.clicked.connect(self._create_scheme)
        wrapper.addWidget(create_button)
        return box

    def _build_form_panel(self) -> QWidget:
        box = QGroupBox("方案属性", self)
        form = QFormLayout(box)
        self.scheme_code_label = QLabel("-", box)
        self.scheme_name_edit = QLineEdit(box)
        self.version_edit = QLineEdit(box)
        self.status_edit = QLineEdit(box)
        self.mold_type_edit = QLineEdit(box)
        self.parting_method_edit = QLineEdit(box)
        self.pouring_position_edit = QLineEdit(box)
        self.gating_type_edit = QLineEdit(box)
        self.notes_edit = QTextEdit(box)
        self.notes_edit.setMaximumHeight(120)

        form.addRow("方案编号", self.scheme_code_label)
        form.addRow("方案名称", self.scheme_name_edit)
        form.addRow("版本号", self.version_edit)
        form.addRow("方案状态", self.status_edit)
        form.addRow("型腔形式", self.mold_type_edit)
        form.addRow("分型方式", self.parting_method_edit)
        form.addRow("浇注位置", self.pouring_position_edit)
        form.addRow("浇注系统", self.gating_type_edit)
        form.addRow("方案说明", self.notes_edit)

        save_button = QPushButton("保存方案", box)
        save_button.clicked.connect(self._save_scheme)
        form.addRow("", save_button)
        return box

    def _build_notes_panel(self) -> QWidget:
        box = QGroupBox("版本差异", self)
        layout = QVBoxLayout(box)
        self.compare_label = QLabel("当前用于记录方案说明，后续可扩展版本差异对比。", box)
        self.compare_label.setWordWrap(True)
        layout.addWidget(self.compare_label)
        return box

    def _on_project_changed(self, current_project) -> None:
        self.scheme_list.clear()
        self.schemes = []
        self.current_scheme_id = None
        if current_project is None:
            self.project_hint.setText("请先在项目中心选择项目。")
            self._clear_form()
            return

        self.project_hint.setText(f"当前项目：{current_project.project_id}")
        self.schemes = self.repository.list_schemes(current_project.project_id)
        for scheme in self.schemes:
            item = QListWidgetItem(f"{scheme.scheme_code} | {scheme.scheme_name} | {scheme.version_no}")
            item.setData(1, scheme.id)
            self.scheme_list.addItem(item)
        if self.schemes:
            self.scheme_list.setCurrentRow(0)
        else:
            self._clear_form()

    def _create_scheme(self) -> None:
        current_project = self.session.current_project
        if current_project is None or not current_project.part_id:
            QMessageBox.warning(self, "无法创建", "请先在项目中心保存项目和零件信息。")
            return

        scheme_code, ok = QInputDialog.getText(self, "新建方案", "请输入方案编号：", text="A")
        if not ok or not scheme_code.strip():
            return
        scheme_name, ok = QInputDialog.getText(
            self,
            "新建方案",
            "请输入方案名称：",
            text="圆盖基准工艺方案",
        )
        if not ok or not scheme_name.strip():
            return

        scheme_id = self.repository.create_scheme(
            project_id=current_project.project_id,
            part_id=current_project.part_id,
            scheme_code=scheme_code.strip(),
            scheme_name=scheme_name.strip(),
            version_no="V1",
        )
        self._on_project_changed(current_project)
        for row, scheme in enumerate(self.schemes):
            if scheme.id == scheme_id:
                self.scheme_list.setCurrentRow(row)
                break

    def _on_scheme_selected(self, row: int) -> None:
        if row < 0 or row >= len(self.schemes):
            self._clear_form()
            return
        scheme = self.schemes[row]
        self.current_scheme_id = scheme.id
        self.scheme_code_label.setText(scheme.scheme_code)
        self.scheme_name_edit.setText(scheme.scheme_name)
        self.version_edit.setText(scheme.version_no)
        self.status_edit.setText(scheme.scheme_status or "draft")
        self.mold_type_edit.setText(scheme.mold_type)
        self.parting_method_edit.setText(scheme.parting_method)
        self.pouring_position_edit.setText(scheme.pouring_position)
        self.gating_type_edit.setText(scheme.gating_type)
        self.notes_edit.setPlainText(scheme.notes)
        self.compare_label.setText(scheme.notes or "当前方案暂无差异说明。")
        self.session.set_current_scheme(scheme.id)

    def _save_scheme(self) -> None:
        if not self.current_scheme_id:
            return
        self.repository.update_scheme(
            self.current_scheme_id,
            scheme_name=self.scheme_name_edit.text().strip(),
            version_no=self.version_edit.text().strip(),
            scheme_status=self.status_edit.text().strip(),
            mold_type=self.mold_type_edit.text().strip(),
            parting_method=self.parting_method_edit.text().strip(),
            pouring_position=self.pouring_position_edit.text().strip(),
            gating_type=self.gating_type_edit.text().strip(),
            notes=self.notes_edit.toPlainText().strip(),
        )
        if self.session.current_project is not None:
            self._on_project_changed(self.session.current_project)
        QMessageBox.information(self, "已保存", "工艺方案已更新。")

    def _clear_form(self) -> None:
        self.current_scheme_id = None
        self.scheme_code_label.setText("-")
        self.scheme_name_edit.clear()
        self.version_edit.clear()
        self.status_edit.clear()
        self.mold_type_edit.clear()
        self.parting_method_edit.clear()
        self.pouring_position_edit.clear()
        self.gating_type_edit.clear()
        self.notes_edit.clear()
        self.compare_label.setText("当前用于记录方案说明，后续可扩展版本差异对比。")
