from __future__ import annotations

from PySide6.QtWidgets import (
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
from app.core.repositories.parameter_repository import ParameterRepository
from app.core.repositories.part_repository import PartRepository
from app.core.repositories.scheme_repository import SchemeRepository
from app.core.services import CalculationService
from app.core.session import AppSession


class ParameterPage(QWidget):
    def __init__(self, paths: AppPaths, session: AppSession) -> None:
        super().__init__()
        self.paths = paths
        self.session = session
        self.parameter_repository = ParameterRepository(paths.database_path)
        self.part_repository = PartRepository(paths.database_path)
        self.scheme_repository = SchemeRepository(paths.database_path)
        self.calculation_service = CalculationService()

        self.current_project_id: str | None = None
        self.current_part_id: str | None = None
        self.current_scheme_id: str | None = None

        layout = QVBoxLayout(self)
        self.header_label = QLabel("请先选择项目和工艺方案。", self)
        layout.addWidget(self.header_label)

        table_box = QGroupBox("关键参数", self)
        table_layout = QVBoxLayout(table_box)
        self.table = QTableWidget(0, 5, table_box)
        self.table.setHorizontalHeaderLabels(["分组", "参数", "值", "单位", "来源"])
        table_layout.addWidget(self.table)

        button_bar = QHBoxLayout()
        calculate_button = QPushButton("自动计算", table_box)
        calculate_button.clicked.connect(self._calculate_parameters)
        save_button = QPushButton("保存参数", table_box)
        save_button.clicked.connect(self._save_parameters)
        button_bar.addWidget(calculate_button)
        button_bar.addWidget(save_button)
        button_bar.addStretch(1)
        table_layout.addLayout(button_bar)
        layout.addWidget(table_box, 3)

        lower_layout = QHBoxLayout()
        layout.addLayout(lower_layout, 2)

        formula_box = QGroupBox("公式与依据", self)
        formula_layout = QVBoxLayout(formula_box)
        self.formula_view = QTextEdit(formula_box)
        self.formula_view.setReadOnly(True)
        formula_layout.addWidget(self.formula_view)
        lower_layout.addWidget(formula_box, 1)

        note_box = QGroupBox("备注", self)
        note_layout = QVBoxLayout(note_box)
        self.note_view = QTextEdit(note_box)
        self.note_view.setPlaceholderText("记录人工修订原因、工艺标准或阶段检查说明。")
        note_layout.addWidget(self.note_view)
        lower_layout.addWidget(note_box, 1)

        self.session.project_changed.connect(self._on_project_changed)
        self.session.scheme_changed.connect(self._on_scheme_changed)

    def _on_project_changed(self, current_project) -> None:
        if current_project is None:
            self.current_project_id = None
            self.current_part_id = None
            self.header_label.setText("请先选择项目和工艺方案。")
            self._clear_table()
            return
        self.current_project_id = current_project.project_id
        self.current_part_id = current_project.part_id
        self._refresh_header()

    def _on_scheme_changed(self, scheme_id: str | None) -> None:
        self.current_scheme_id = scheme_id
        self._refresh_header()
        self._load_saved_parameters()

    def _refresh_header(self) -> None:
        if not self.current_project_id:
            self.header_label.setText("请先选择项目和工艺方案。")
            return
        if not self.current_scheme_id:
            self.header_label.setText("已选择项目，尚未选择工艺方案。")
            return
        self.header_label.setText(
            f"当前项目：{self.current_project_id} | 当前方案：{self.current_scheme_id}"
        )

    def _load_saved_parameters(self) -> None:
        self._clear_table()
        self.formula_view.clear()
        if not self.current_scheme_id:
            return
        rows = self.parameter_repository.list_by_scheme(self.current_scheme_id)
        for row in rows:
            self._append_table_row(
                row.param_group,
                row.param_name,
                row.param_value,
                row.param_unit,
                row.source_type or row.value_type,
            )
            if row.calc_formula:
                self.formula_view.append(f"{row.param_name}: {row.calc_formula}")

    def _calculate_parameters(self) -> None:
        if not self.current_project_id or not self.current_part_id or not self.current_scheme_id:
            QMessageBox.warning(self, "无法计算", "请先选择项目并创建工艺方案。")
            return
        part = self.part_repository.get_primary_part(self.current_project_id)
        schemes = self.scheme_repository.list_schemes(self.current_project_id)
        scheme = next((item for item in schemes if item.id == self.current_scheme_id), None)
        if part is None or scheme is None:
            QMessageBox.warning(self, "无法计算", "项目零件或工艺方案不存在。")
            return

        parameters = self.calculation_service.calculate(part, scheme)
        self._clear_table()
        self.formula_view.clear()
        for parameter in parameters:
            self._append_table_row(
                parameter.param_group,
                parameter.param_name,
                parameter.param_value,
                parameter.param_unit,
                parameter.source_type,
            )
            self.formula_view.append(f"{parameter.param_name}: {parameter.calc_formula}")

    def _save_parameters(self) -> None:
        if not self.current_scheme_id:
            return
        payload: list[dict[str, str]] = []
        for row in range(self.table.rowCount()):
            payload.append(
                {
                    "param_group": self.table.item(row, 0).text(),
                    "param_code": f"row_{row + 1}",
                    "param_name": self.table.item(row, 1).text(),
                    "param_value": self.table.item(row, 2).text(),
                    "param_unit": self.table.item(row, 3).text(),
                    "value_type": "text",
                    "source_type": self.table.item(row, 4).text(),
                    "calc_formula": self._formula_for_name(self.table.item(row, 1).text()),
                }
            )
        self.parameter_repository.replace_for_scheme(self.current_scheme_id, payload)
        QMessageBox.information(self, "已保存", "参数结果已写入数据库。")

    def _formula_for_name(self, param_name: str) -> str:
        lines = self.formula_view.toPlainText().splitlines()
        for line in lines:
            if line.startswith(f"{param_name}:"):
                return line.split(":", 1)[1].strip()
        return ""

    def _append_table_row(
        self,
        group_name: str,
        param_name: str,
        value: str,
        unit: str,
        source: str,
    ) -> None:
        row = self.table.rowCount()
        self.table.insertRow(row)
        values = [group_name, param_name, value, unit, source]
        for column, item_value in enumerate(values):
            self.table.setItem(row, column, QTableWidgetItem(item_value))

    def _clear_table(self) -> None:
        self.table.setRowCount(0)
