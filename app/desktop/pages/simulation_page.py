from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QFileDialog,
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
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.core.config import AppPaths
from app.core.repositories.project_repository import ProjectRepository
from app.core.repositories.simulation_repository import (
    SimulationJobRecord,
    SimulationRepository,
)
from app.core.session import AppSession


class SimulationPage(QWidget):
    def __init__(self, paths: AppPaths, session: AppSession) -> None:
        super().__init__()
        self.paths = paths
        self.session = session
        self.project_repository = ProjectRepository(paths.database_path)
        self.repository = SimulationRepository(paths.database_path)
        self.current_project_id: str | None = None
        self.current_project_root: Path | None = None
        self.current_scheme_id: str | None = None
        self.current_job_id: str | None = None
        self.jobs: list[SimulationJobRecord] = []

        layout = QHBoxLayout(self)
        layout.addWidget(self._build_job_list_box(), 2)

        right = QVBoxLayout()
        right.addWidget(self._build_form_box(), 3)
        right.addWidget(self._build_results_box(), 3)
        layout.addLayout(right, 5)

        self.session.project_changed.connect(self._on_project_changed)
        self.session.scheme_changed.connect(self._on_scheme_changed)

    def _build_job_list_box(self) -> QWidget:
        box = QGroupBox("仿真任务", self)
        layout = QVBoxLayout(box)
        self.context_label = QLabel("请先选择项目和工艺方案。", box)
        layout.addWidget(self.context_label)
        self.job_list = QListWidget(box)
        self.job_list.currentRowChanged.connect(self._on_job_selected)
        layout.addWidget(self.job_list)

        buttons = QHBoxLayout()
        create_button = QPushButton("新建任务", box)
        create_button.clicked.connect(self._create_job)
        refresh_button = QPushButton("刷新", box)
        refresh_button.clicked.connect(self._reload_jobs)
        buttons.addWidget(create_button)
        buttons.addWidget(refresh_button)
        layout.addLayout(buttons)
        return box

    def _build_form_box(self) -> QWidget:
        box = QGroupBox("任务属性", self)
        form = QFormLayout(box)
        self.job_code_label = QLabel("-", box)
        self.job_name_edit = QLineEdit(box)
        self.solver_edit = QLineEdit(box)
        self.template_edit = QLineEdit(box)
        self.input_dir_edit = QLineEdit(box)
        self.output_dir_edit = QLineEdit(box)
        self.status_edit = QLineEdit(box)
        self.run_mode_edit = QLineEdit(box)
        self.operator_edit = QLineEdit(box)
        self.submit_time_edit = QLineEdit(box)
        self.finish_time_edit = QLineEdit(box)
        self.note_view = QTextEdit(box)
        self.note_view.setMaximumHeight(90)
        self.note_view.setPlaceholderText("记录网格、边界条件、版本差异或计算说明。")

        form.addRow("任务编号", self.job_code_label)
        form.addRow("任务名称", self.job_name_edit)
        form.addRow("求解器", self.solver_edit)
        form.addRow("模板名称", self.template_edit)
        form.addRow("输入目录", self.input_dir_edit)
        form.addRow("输出目录", self.output_dir_edit)
        form.addRow("任务状态", self.status_edit)
        form.addRow("运行模式", self.run_mode_edit)
        form.addRow("操作人", self.operator_edit)
        form.addRow("提交时间", self.submit_time_edit)
        form.addRow("完成时间", self.finish_time_edit)
        form.addRow("说明", self.note_view)

        actions = QHBoxLayout()
        pick_input_button = QPushButton("选择输入目录", box)
        pick_input_button.clicked.connect(lambda: self._pick_directory(self.input_dir_edit))
        pick_output_button = QPushButton("选择输出目录", box)
        pick_output_button.clicked.connect(lambda: self._pick_directory(self.output_dir_edit))
        save_button = QPushButton("保存任务", box)
        save_button.clicked.connect(self._save_job)
        actions.addWidget(pick_input_button)
        actions.addWidget(pick_output_button)
        actions.addWidget(save_button)
        form.addRow("", actions)
        return box

    def _build_results_box(self) -> QWidget:
        box = QGroupBox("仿真结果归档", self)
        layout = QVBoxLayout(box)
        self.results_table = QTableWidget(0, 4, box)
        self.results_table.setHorizontalHeaderLabels(["类型", "名称", "文件", "说明"])
        layout.addWidget(self.results_table)

        buttons = QHBoxLayout()
        add_result_button = QPushButton("登记结果文件", box)
        add_result_button.clicked.connect(self._add_result)
        buttons.addWidget(add_result_button)
        buttons.addStretch(1)
        layout.addLayout(buttons)
        return box

    def _on_project_changed(self, current_project) -> None:
        if current_project is None:
            self.current_project_id = None
            self.current_project_root = None
            self.context_label.setText("请先选择项目和工艺方案。")
            return
        self.current_project_id = current_project.project_id
        project = self.project_repository.get_project(current_project.project_id)
        self.current_project_root = Path(project.root_dir) if project and project.root_dir else self.paths.projects_dir
        self._refresh_context()

    def _on_scheme_changed(self, scheme_id: str | None) -> None:
        self.current_scheme_id = scheme_id
        self.current_job_id = None
        self._refresh_context()
        self._reload_jobs()

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

    def _reload_jobs(self) -> None:
        self.job_list.clear()
        self.results_table.setRowCount(0)
        self.jobs = []
        if not self.current_scheme_id:
            self._clear_form()
            return
        self.jobs = self.repository.list_jobs(self.current_scheme_id)
        for job in self.jobs:
            QListWidgetItem(f"{job.job_code} | {job.job_name} | {job.job_status}", self.job_list)
        if self.jobs:
            self.job_list.setCurrentRow(0)
        else:
            self._clear_form()

    def _create_job(self) -> None:
        if not self.current_scheme_id:
            QMessageBox.warning(self, "无法创建", "请先选择工艺方案。")
            return
        job_code, ok = QInputDialog.getText(self, "新建仿真任务", "请输入任务编号：", text="SIM-01")
        if not ok or not job_code.strip():
            return
        job_name, ok = QInputDialog.getText(self, "新建仿真任务", "请输入任务名称：", text="基准方案仿真")
        if not ok or not job_name.strip():
            return
        base_dir = self.current_project_root or self.paths.projects_dir
        input_dir = str(Path(base_dir) / "simulation" / job_code.strip() / "input")
        output_dir = str(Path(base_dir) / "simulation" / job_code.strip() / "output")
        Path(input_dir).mkdir(parents=True, exist_ok=True)
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        job_id = self.repository.create_job(
            scheme_id=self.current_scheme_id,
            job_code=job_code.strip(),
            job_name=job_name.strip(),
            solver="ProCAST",
            template_name="default",
            input_dir=input_dir,
            output_dir=output_dir,
            job_status="draft",
            run_mode="manual",
            operator="system",
        )
        self._reload_jobs()
        for row, job in enumerate(self.jobs):
            if job.id == job_id:
                self.job_list.setCurrentRow(row)
                break

    def _on_job_selected(self, row: int) -> None:
        if row < 0 or row >= len(self.jobs):
            self.current_job_id = None
            self._clear_form()
            return
        job = self.jobs[row]
        self.current_job_id = job.id
        self.job_code_label.setText(job.job_code)
        self.job_name_edit.setText(job.job_name)
        self.solver_edit.setText(job.solver)
        self.template_edit.setText(job.template_name)
        self.input_dir_edit.setText(job.input_dir)
        self.output_dir_edit.setText(job.output_dir)
        self.status_edit.setText(job.job_status)
        self.run_mode_edit.setText(job.run_mode)
        self.operator_edit.setText(job.operator)
        self.submit_time_edit.setText(job.submit_time)
        self.finish_time_edit.setText(job.finish_time)
        self.note_view.clear()
        self._reload_results(job.id)

    def _reload_results(self, job_id: str) -> None:
        self.results_table.setRowCount(0)
        for result in self.repository.list_results(job_id):
            row = self.results_table.rowCount()
            self.results_table.insertRow(row)
            values = [result.result_type, result.result_name, result.file_path, result.summary]
            for column, value in enumerate(values):
                self.results_table.setItem(row, column, QTableWidgetItem(value))

    def _save_job(self) -> None:
        if not self.current_job_id:
            return
        self.repository.update_job(
            self.current_job_id,
            job_name=self.job_name_edit.text().strip(),
            solver=self.solver_edit.text().strip(),
            template_name=self.template_edit.text().strip(),
            input_dir=self.input_dir_edit.text().strip(),
            output_dir=self.output_dir_edit.text().strip(),
            job_status=self.status_edit.text().strip(),
            run_mode=self.run_mode_edit.text().strip(),
            operator=self.operator_edit.text().strip(),
            submit_time=self.submit_time_edit.text().strip(),
            finish_time=self.finish_time_edit.text().strip(),
        )
        QMessageBox.information(self, "已保存", "仿真任务已更新。")
        self._reload_jobs()

    def _add_result(self) -> None:
        if not self.current_job_id:
            QMessageBox.warning(self, "无法登记", "请先选择仿真任务。")
            return
        start_dir = self.output_dir_edit.text().strip() or str(self.current_project_root or self.paths.projects_dir)
        file_path, _ = QFileDialog.getOpenFileName(self, "选择仿真结果文件", start_dir, "All Files (*.*)")
        if not file_path:
            return
        result_type, ok = QInputDialog.getText(self, "结果类型", "请输入结果类型：", text="temperature")
        if not ok or not result_type.strip():
            return
        result_name, ok = QInputDialog.getText(self, "结果名称", "请输入结果名称：", text=Path(file_path).stem)
        if not ok or not result_name.strip():
            return
        summary, ok = QInputDialog.getText(self, "结果摘要", "请输入结果摘要：", text="待补充")
        if not ok:
            return
        self.repository.create_result(
            job_id=self.current_job_id,
            result_type=result_type.strip(),
            result_name=result_name.strip(),
            file_path=file_path,
            summary=summary.strip(),
        )
        self._reload_results(self.current_job_id)

    def _pick_directory(self, target_edit: QLineEdit) -> None:
        start_dir = target_edit.text().strip() or str(self.current_project_root or self.paths.projects_dir)
        directory = QFileDialog.getExistingDirectory(self, "选择目录", start_dir)
        if directory:
            target_edit.setText(directory)

    def _clear_form(self) -> None:
        self.job_code_label.setText("-")
        for widget in (
            self.job_name_edit,
            self.solver_edit,
            self.template_edit,
            self.input_dir_edit,
            self.output_dir_edit,
            self.status_edit,
            self.run_mode_edit,
            self.operator_edit,
            self.submit_time_edit,
            self.finish_time_edit,
        ):
            widget.clear()
        self.note_view.clear()
        self.results_table.setRowCount(0)
