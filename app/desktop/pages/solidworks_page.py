from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QPlainTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.core.config import AppPaths
from app.core.repositories.cad_repository import CadRepository
from app.core.repositories.project_repository import ProjectRepository
from app.core.session import AppSession
from app.integrations.solidworks.bridge_client import SolidWorksBridgeClient


class SolidWorksPage(QWidget):
    def __init__(self, paths: AppPaths, session: AppSession) -> None:
        super().__init__()
        self.paths = paths
        self.session = session
        self.bridge_client = SolidWorksBridgeClient(paths)
        self.project_repository = ProjectRepository(paths.database_path)
        self.cad_repository = CadRepository(paths.database_path)
        self.input_file: Path | None = None
        self.output_file: Path | None = None
        self.current_project_id: str | None = None
        self.current_scheme_id: str | None = None
        self.current_project_root: Path | None = None
        self._setup_ui()
        self.refresh_status()
        self.session.project_changed.connect(self._on_project_changed)
        self.session.scheme_changed.connect(self._on_scheme_changed)

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        status_box = QGroupBox("桥接状态", self)
        status_layout = QFormLayout(status_box)
        self.bridge_path_label = QLabel("-", status_box)
        self.bridge_available_label = QLabel("-", status_box)
        self.solidworks_found_label = QLabel("-", status_box)
        self.com_available_label = QLabel("-", status_box)
        self.context_label = QLabel("请先选择项目和工艺方案。", status_box)
        status_layout.addRow("桥接程序", self.bridge_path_label)
        status_layout.addRow("桥接可用", self.bridge_available_label)
        status_layout.addRow("SolidWorks 检测", self.solidworks_found_label)
        status_layout.addRow("COM 可用", self.com_available_label)
        status_layout.addRow("当前上下文", self.context_label)
        layout.addWidget(status_box)

        actions_box = QGroupBox("操作", self)
        actions_layout = QHBoxLayout(actions_box)
        refresh_button = QPushButton("刷新状态", actions_box)
        refresh_button.clicked.connect(self.refresh_status)
        select_input_button = QPushButton("选择输入文件", actions_box)
        select_input_button.clicked.connect(self.select_input_file)
        select_output_button = QPushButton("选择输出文件", actions_box)
        select_output_button.clicked.connect(self.select_output_file)
        export_step_button = QPushButton("导出 STEP", actions_box)
        export_step_button.clicked.connect(lambda: self.export_current_file("step"))
        export_pdf_button = QPushButton("导出 PDF", actions_box)
        export_pdf_button.clicked.connect(lambda: self.export_current_file("pdf"))
        actions_layout.addWidget(refresh_button)
        actions_layout.addWidget(select_input_button)
        actions_layout.addWidget(select_output_button)
        actions_layout.addWidget(export_step_button)
        actions_layout.addWidget(export_pdf_button)
        layout.addWidget(actions_box)

        file_box = QGroupBox("当前文件", self)
        file_layout = QFormLayout(file_box)
        self.input_label = QLabel("-", file_box)
        self.output_label = QLabel("-", file_box)
        self.linked_model_label = QLabel("-", file_box)
        file_layout.addRow("输入", self.input_label)
        file_layout.addRow("输出", self.output_label)
        file_layout.addRow("方案关联模型", self.linked_model_label)
        layout.addWidget(file_box)

        log_box = QGroupBox("桥接输出", self)
        log_layout = QVBoxLayout(log_box)
        self.log_edit = QPlainTextEdit(log_box)
        self.log_edit.setReadOnly(True)
        log_layout.addWidget(self.log_edit)
        layout.addWidget(log_box, 1)

    def refresh_status(self) -> None:
        bridge_path = self.bridge_client.bridge_executable()
        self.bridge_path_label.setText(str(bridge_path))
        self.bridge_available_label.setText("是" if self.bridge_client.is_available() else "否")

        result = self.bridge_client.info()
        if result.ok:
            self.solidworks_found_label.setText("是" if result.payload.get("solidworks_found") else "否")
            self.com_available_label.setText("是" if result.payload.get("com_available") else "否")
        else:
            self.solidworks_found_label.setText("未知")
            self.com_available_label.setText("未知")
        self.log_edit.setPlainText(result.raw_output or str(result.payload))

    def _on_project_changed(self, current_project) -> None:
        if current_project is None:
            self.current_project_id = None
            self.current_project_root = None
            self.context_label.setText("请先选择项目和工艺方案。")
            return
        self.current_project_id = current_project.project_id
        project = self.project_repository.get_project(current_project.project_id)
        if project is not None and project.root_dir:
            self.current_project_root = Path(project.root_dir)
        else:
            self.current_project_root = self.paths.projects_dir
        self._refresh_context()

    def _on_scheme_changed(self, scheme_id: str | None) -> None:
        self.current_scheme_id = scheme_id
        self._refresh_context()
        self._load_linked_model()

    def _refresh_context(self) -> None:
        if not self.current_project_id:
            self.context_label.setText("请先选择项目和工艺方案。")
            return
        if not self.current_scheme_id:
            self.context_label.setText(f"当前项目：{self.current_project_id}，尚未选择方案。")
            return
        self.context_label.setText(
            f"当前项目：{self.current_project_id} | 当前方案：{self.current_scheme_id}"
        )

    def _load_linked_model(self) -> None:
        self.linked_model_label.setText("-")
        if not self.current_scheme_id:
            return
        model = self.cad_repository.get_model_for_scheme(self.current_scheme_id)
        if model is not None:
            self.linked_model_label.setText(model.file_path)
            self.input_file = Path(model.file_path)
            self.input_label.setText(model.file_path)

    def select_input_file(self) -> None:
        start_dir = str(self.current_project_root or self.paths.projects_dir)
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择 SolidWorks 文件",
            start_dir,
            "SolidWorks Files (*.sldprt *.sldasm *.slddrw)",
        )
        if not file_path:
            return
        self.input_file = Path(file_path)
        self.input_label.setText(str(self.input_file))
        if self.current_scheme_id:
            model_id = self.cad_repository.upsert_model(
                scheme_id=self.current_scheme_id,
                cad_system="SolidWorks",
                file_type=self.input_file.suffix.lower().lstrip("."),
                file_path=str(self.input_file),
            )
            self.linked_model_label.setText(str(self.input_file))
            self.log_edit.setPlainText(f"已绑定方案 CAD 模型，模型记录 ID：{model_id}")

    def select_output_file(self) -> None:
        start_dir = str(self.current_project_root or self.paths.projects_dir)
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "选择导出文件",
            start_dir,
            "All Files (*.*)",
        )
        if not file_path:
            return
        self.output_file = Path(file_path)
        self.output_label.setText(str(self.output_file))

    def export_current_file(self, export_type: str) -> None:
        if self.input_file is None:
            QMessageBox.warning(self, "缺少输入", "请先选择输入文件。")
            return

        if self.output_file is None:
            output_dir = self.current_project_root or self.paths.projects_dir
            self.output_file = Path(output_dir) / f"{self.input_file.stem}.{export_type}"
            self.output_label.setText(str(self.output_file))

        result = self.bridge_client.export_file(self.input_file, self.output_file, export_type)
        self.log_edit.setPlainText(result.raw_output or str(result.payload))
        if result.ok:
            if self.current_scheme_id:
                model = self.cad_repository.get_model_for_scheme(self.current_scheme_id)
                if model is not None:
                    self.cad_repository.create_export_record(
                        cad_model_id=model.id,
                        export_type=export_type,
                        export_path=str(self.output_file),
                        export_status="success",
                        bridge_version="bridge_cli",
                    )
            QMessageBox.information(self, "导出成功", f"文件已导出到：\n{self.output_file}")
        else:
            QMessageBox.critical(self, "导出失败", str(result.payload))
