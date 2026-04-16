from __future__ import annotations

from PySide6.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.core.config import AppPaths
from app.core.repositories.simulation_repository import (
    SimulationJobRecord,
    SimulationRepository,
    SimulationResultRecord,
)
from app.core.session import AppSession


class ResultsPage(QWidget):
    def __init__(self, paths: AppPaths, session: AppSession) -> None:
        super().__init__()
        self.paths = paths
        self.session = session
        self.repository = SimulationRepository(paths.database_path)
        self.current_scheme_id: str | None = None
        self.jobs: list[SimulationJobRecord] = []
        self.results: list[SimulationResultRecord] = []

        layout = QHBoxLayout(self)
        layout.addWidget(self._build_job_box(), 2)

        right = QVBoxLayout()
        right.addWidget(self._build_summary_box())
        right.addWidget(self._build_results_box(), 1)
        layout.addLayout(right, 5)

        self.session.scheme_changed.connect(self._on_scheme_changed)

    def _build_job_box(self) -> QWidget:
        box = QGroupBox("结果来源任务", self)
        layout = QVBoxLayout(box)
        self.context_label = QLabel("请先选择工艺方案。", box)
        layout.addWidget(self.context_label)
        self.job_list = QListWidget(box)
        self.job_list.currentRowChanged.connect(self._on_job_selected)
        layout.addWidget(self.job_list)
        return box

    def _build_summary_box(self) -> QWidget:
        box = QGroupBox("结果摘要", self)
        form = QFormLayout(box)
        self.job_info_label = QLabel("-", box)
        self.result_count_label = QLabel("0", box)
        self.compare_groups_label = QLabel("-", box)
        self.detail_view = QTextEdit(box)
        self.detail_view.setReadOnly(True)
        self.detail_view.setMaximumHeight(140)
        form.addRow("当前任务", self.job_info_label)
        form.addRow("结果数量", self.result_count_label)
        form.addRow("对比分组", self.compare_groups_label)
        form.addRow("说明", self.detail_view)
        return box

    def _build_results_box(self) -> QWidget:
        box = QGroupBox("仿真结果列表", self)
        layout = QVBoxLayout(box)
        self.results_table = QTableWidget(0, 5, box)
        self.results_table.setHorizontalHeaderLabels(["类型", "名称", "文件", "分组", "摘要"])
        layout.addWidget(self.results_table)
        return box

    def _on_scheme_changed(self, scheme_id: str | None) -> None:
        self.current_scheme_id = scheme_id
        self.job_list.clear()
        self.results_table.setRowCount(0)
        self.jobs = []
        self.results = []
        if not scheme_id:
            self.context_label.setText("请先选择工艺方案。")
            self._clear_summary()
            return
        self.context_label.setText(f"当前方案：{scheme_id}")
        self.jobs = self.repository.list_jobs(scheme_id)
        for job in self.jobs:
            QListWidgetItem(f"{job.job_code} | {job.job_name} | {job.job_status}", self.job_list)
        if self.jobs:
            self.job_list.setCurrentRow(0)
        else:
            self._clear_summary()

    def _on_job_selected(self, row: int) -> None:
        if row < 0 or row >= len(self.jobs):
            self.results = []
            self.results_table.setRowCount(0)
            self._clear_summary()
            return
        job = self.jobs[row]
        self.results = self.repository.list_results(job.id)
        self.job_info_label.setText(f"{job.job_code} | {job.job_name}")
        self.result_count_label.setText(str(len(self.results)))
        groups = sorted({item.compare_group for item in self.results if item.compare_group})
        self.compare_groups_label.setText(", ".join(groups) if groups else "-")
        self.detail_view.setPlainText(
            "\n".join(
                [
                    f"求解器：{job.solver or '-'}",
                    f"输入目录：{job.input_dir or '-'}",
                    f"输出目录：{job.output_dir or '-'}",
                    f"任务状态：{job.job_status or '-'}",
                ]
            )
        )
        self._reload_results()

    def _reload_results(self) -> None:
        self.results_table.setRowCount(0)
        for result in self.results:
            row = self.results_table.rowCount()
            self.results_table.insertRow(row)
            values = [
                result.result_type,
                result.result_name,
                result.file_path,
                result.compare_group,
                result.summary,
            ]
            for column, value in enumerate(values):
                self.results_table.setItem(row, column, QTableWidgetItem(value))

    def _clear_summary(self) -> None:
        self.job_info_label.setText("-")
        self.result_count_label.setText("0")
        self.compare_groups_label.setText("-")
        self.detail_view.clear()
