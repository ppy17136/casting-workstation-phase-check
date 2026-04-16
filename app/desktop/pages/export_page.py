from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.core.config import AppPaths
from app.core.repositories.cad_repository import CadRepository
from app.core.repositories.document_repository import DocumentRepository
from app.core.repositories.project_repository import ProjectRepository
from app.core.repositories.simulation_repository import SimulationRepository
from app.core.services import ExportBundleService
from app.core.session import AppSession


class ExportPage(QWidget):
    def __init__(self, paths: AppPaths, session: AppSession) -> None:
        super().__init__()
        self.paths = paths
        self.session = session
        self.project_repository = ProjectRepository(paths.database_path)
        self.document_repository = DocumentRepository(paths.database_path)
        self.cad_repository = CadRepository(paths.database_path)
        self.simulation_repository = SimulationRepository(paths.database_path)
        self.export_service = ExportBundleService(
            document_repository=self.document_repository,
            cad_repository=self.cad_repository,
            simulation_repository=self.simulation_repository,
        )
        self.current_project_id: str | None = None
        self.current_scheme_id: str | None = None

        layout = QVBoxLayout(self)
        layout.addWidget(self._build_context_box())
        layout.addWidget(self._build_summary_box())

        self.session.project_changed.connect(self._on_project_changed)
        self.session.scheme_changed.connect(self._on_scheme_changed)

    def _build_context_box(self) -> QWidget:
        box = QGroupBox("阶段成果包导出", self)
        layout = QVBoxLayout(box)

        form = QFormLayout()
        self.context_label = QLabel("请先选择项目与工艺方案。", box)
        self.output_dir_label = QLabel("-", box)
        self.zip_path_label = QLabel("-", box)
        form.addRow("当前上下文", self.context_label)
        form.addRow("导出目录", self.output_dir_label)
        form.addRow("压缩包", self.zip_path_label)
        layout.addLayout(form)

        actions = QHBoxLayout()
        export_button = QPushButton("生成阶段成果包", box)
        export_button.clicked.connect(self._export_bundle)
        actions.addWidget(export_button)
        actions.addStretch(1)
        layout.addLayout(actions)
        return box

    def _build_summary_box(self) -> QWidget:
        box = QGroupBox("导出摘要", self)
        layout = QVBoxLayout(box)
        self.summary_view = QTextEdit(box)
        self.summary_view.setReadOnly(True)
        layout.addWidget(self.summary_view)
        return box

    def _on_project_changed(self, current_project) -> None:
        self.current_project_id = None if current_project is None else current_project.project_id
        self._refresh_context()

    def _on_scheme_changed(self, scheme_id: str | None) -> None:
        self.current_scheme_id = scheme_id
        self._refresh_context()

    def _refresh_context(self) -> None:
        self.output_dir_label.setText("-")
        self.zip_path_label.setText("-")
        self.summary_view.clear()
        if not self.current_project_id:
            self.context_label.setText("请先选择项目与工艺方案。")
            return
        if not self.current_scheme_id:
            self.context_label.setText(f"当前项目：{self.current_project_id}，尚未选择工艺方案。")
            return
        self.context_label.setText(
            f"当前项目：{self.current_project_id} | 当前方案：{self.current_scheme_id}"
        )
        self._load_latest_bundle()

    def _load_latest_bundle(self) -> None:
        if not self.current_project_id or not self.current_scheme_id:
            return
        project = self.project_repository.get_project(self.current_project_id)
        if project is None or not project.root_dir:
            return

        export_root = Path(project.root_dir) / "generated_exports"
        if not export_root.exists():
            return

        candidates = sorted(
            [
                path
                for path in export_root.iterdir()
                if path.is_dir() and (self.current_scheme_id in path.name or project.project_code in path.name)
            ],
            key=lambda item: item.stat().st_mtime,
            reverse=True,
        )
        if not candidates:
            return

        bundle_dir = candidates[0]
        zip_path = bundle_dir.with_suffix(".zip")
        copied_files = [path for path in bundle_dir.rglob("*") if path.is_file()]
        self.output_dir_label.setText(str(bundle_dir))
        self.zip_path_label.setText(str(zip_path) if zip_path.exists() else "-")
        self.summary_view.setPlainText(
            "\n".join(
                [
                    f"导出目录：{bundle_dir}",
                    f"压缩包：{zip_path if zip_path.exists() else '-'}",
                    "",
                    "已收集文件：",
                    *[str(path) for path in copied_files],
                ]
            )
        )

    def _export_bundle(self) -> None:
        if not self.current_project_id or not self.current_scheme_id:
            QMessageBox.warning(self, "无法导出", "请先选择项目与工艺方案。")
            return
        project = self.project_repository.get_project(self.current_project_id)
        if project is None:
            QMessageBox.warning(self, "无法导出", "当前项目不存在。")
            return

        result = self.export_service.export_scheme_bundle(
            project=project,
            scheme_id=self.current_scheme_id,
            bundle_name=f"{project.project_code}_{self.current_scheme_id}",
        )
        self.output_dir_label.setText(str(result.bundle_dir))
        self.zip_path_label.setText(str(result.zip_path))
        self.summary_view.setPlainText(
            "\n".join(
                [
                    f"导出目录：{result.bundle_dir}",
                    f"压缩包：{result.zip_path}",
                    "",
                    "已收集文件：",
                    *[str(path) for path in result.copied_files],
                ]
            )
        )
        QMessageBox.information(self, "导出完成", f"阶段成果包已生成：\n{result.zip_path}")
