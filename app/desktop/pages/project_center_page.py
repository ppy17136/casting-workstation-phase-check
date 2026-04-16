from __future__ import annotations

from PySide6.QtWidgets import (
    QDoubleSpinBox,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from app.core.config import AppPaths
from app.core.repositories.part_repository import PartRepository
from app.core.repositories.project_repository import ProjectRecord, ProjectRepository
from app.core.session import AppSession


class ProjectCenterPage(QWidget):
    def __init__(self, paths: AppPaths, session: AppSession) -> None:
        super().__init__()
        self.paths = paths
        self.session = session
        self.project_repository = ProjectRepository(paths.database_path)
        self.part_repository = PartRepository(paths.database_path)
        self.projects: list[ProjectRecord] = []
        self.current_project_id: str | None = None
        self.current_part_id: str | None = None

        layout = QHBoxLayout(self)
        layout.addWidget(self._build_list_panel(), 2)
        detail_layout = QVBoxLayout()
        detail_layout.addWidget(self._build_project_form(), 2)
        detail_layout.addWidget(self._build_part_form(), 2)
        detail_layout.addStretch(1)
        layout.addLayout(detail_layout, 5)
        self._load_projects()

    def _build_list_panel(self) -> QWidget:
        box = QGroupBox("项目列表", self)
        wrapper = QVBoxLayout(box)
        self.project_list = QListWidget(box)
        self.project_list.currentRowChanged.connect(self._on_project_selected)
        wrapper.addWidget(self.project_list)

        create_button = QPushButton("新建项目", box)
        create_button.clicked.connect(self._create_project)
        refresh_button = QPushButton("刷新", box)
        refresh_button.clicked.connect(self._load_projects)
        wrapper.addWidget(create_button)
        wrapper.addWidget(refresh_button)
        return box

    def _build_project_form(self) -> QWidget:
        box = QGroupBox("项目信息", self)
        form = QFormLayout(box)
        self.project_code_label = QLabel("-", box)
        self.project_name_edit = QLineEdit(box)
        self.project_type_edit = QLineEdit(box)
        self.casting_method_edit = QLineEdit(box)
        self.project_status_edit = QLineEdit(box)
        self.project_owner_edit = QLineEdit(box)
        self.project_root_dir_edit = QLineEdit(box)
        save_button = QPushButton("保存项目", box)
        save_button.clicked.connect(self._save_project)

        form.addRow("项目编号", self.project_code_label)
        form.addRow("项目名称", self.project_name_edit)
        form.addRow("项目类型", self.project_type_edit)
        form.addRow("铸造方法", self.casting_method_edit)
        form.addRow("项目状态", self.project_status_edit)
        form.addRow("负责人", self.project_owner_edit)
        form.addRow("项目目录", self.project_root_dir_edit)
        form.addRow("", save_button)
        return box

    def _build_part_form(self) -> QWidget:
        box = QGroupBox("零件基础信息", self)
        grid = QGridLayout(box)

        self.part_name_edit = QLineEdit(box)
        self.part_no_edit = QLineEdit(box)
        self.drawing_no_edit = QLineEdit(box)
        self.material_name_edit = QLineEdit(box)
        self.net_weight_spin = self._make_double_spin()
        self.blank_weight_spin = self._make_double_spin()
        self.max_wall_spin = self._make_double_spin()
        self.min_wall_spin = self._make_double_spin()
        self.production_qty_spin = QSpinBox(box)
        self.production_qty_spin.setRange(0, 1000000)

        fields = [
            ("零件名称", self.part_name_edit),
            ("零件编号", self.part_no_edit),
            ("图号", self.drawing_no_edit),
            ("材料", self.material_name_edit),
            ("净重(kg)", self.net_weight_spin),
            ("毛坯重(kg)", self.blank_weight_spin),
            ("最大壁厚(mm)", self.max_wall_spin),
            ("最小壁厚(mm)", self.min_wall_spin),
            ("生产数量", self.production_qty_spin),
        ]
        for row, (label, widget) in enumerate(fields):
            grid.addWidget(QLabel(label, box), row, 0)
            grid.addWidget(widget, row, 1)

        save_button = QPushButton("保存零件", box)
        save_button.clicked.connect(self._save_part)
        grid.addWidget(save_button, len(fields), 0, 1, 2)
        return box

    def _make_double_spin(self) -> QDoubleSpinBox:
        spin = QDoubleSpinBox(self)
        spin.setRange(0.0, 1000000.0)
        spin.setDecimals(3)
        return spin

    def _load_projects(self) -> None:
        self.projects = self.project_repository.list_projects()
        self.project_list.clear()
        for project in self.projects:
            item = QListWidgetItem(f"{project.project_code} | {project.project_name}", self.project_list)
            item.setData(1, project.id)
        if self.projects:
            self.project_list.setCurrentRow(0)
        else:
            self._clear_forms()

    def _create_project(self) -> None:
        code, ok = QInputDialog.getText(self, "新建项目", "请输入项目编号：")
        if not ok or not code.strip():
            return
        name, ok = QInputDialog.getText(self, "新建项目", "请输入项目名称：")
        if not ok or not name.strip():
            return
        project_root = self.paths.projects_dir / code.strip()
        project_root.mkdir(parents=True, exist_ok=True)
        try:
            project_id = self.project_repository.create_project(
                project_code=code.strip(),
                project_name=name.strip(),
                owner="system",
                root_dir=str(project_root),
            )
            self.part_repository.create_default_part(project_id, f"{name.strip()}零件")
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "创建失败", str(exc))
            return
        self._load_projects()

    def _on_project_selected(self, row: int) -> None:
        if row < 0 or row >= len(self.projects):
            self._clear_forms()
            return
        project = self.projects[row]
        part = self.part_repository.get_primary_part(project.id)
        self.current_project_id = project.id
        self.current_part_id = part.id if part else None

        self.project_code_label.setText(project.project_code)
        self.project_name_edit.setText(project.project_name)
        self.project_type_edit.setText(project.project_type or "创新训练项目")
        self.casting_method_edit.setText(project.casting_method or "砂型铸造")
        self.project_status_edit.setText(project.status or "draft")
        self.project_owner_edit.setText(project.owner or "")
        self.project_root_dir_edit.setText(project.root_dir or "")

        self._load_part_form(part)
        self.session.set_current_project(project.id, self.current_part_id)

    def _load_part_form(self, part) -> None:
        if part is None:
            self.part_name_edit.clear()
            self.part_no_edit.clear()
            self.drawing_no_edit.clear()
            self.material_name_edit.clear()
            self.net_weight_spin.setValue(0.0)
            self.blank_weight_spin.setValue(0.0)
            self.max_wall_spin.setValue(0.0)
            self.min_wall_spin.setValue(0.0)
            self.production_qty_spin.setValue(0)
            return

        self.part_name_edit.setText(part.part_name)
        self.part_no_edit.setText(part.part_no)
        self.drawing_no_edit.setText(part.drawing_no)
        self.material_name_edit.setText(part.material_name)
        self.net_weight_spin.setValue(part.net_weight or 0.0)
        self.blank_weight_spin.setValue(part.blank_weight or 0.0)
        self.max_wall_spin.setValue(part.max_wall_thickness or 0.0)
        self.min_wall_spin.setValue(part.min_wall_thickness or 0.0)
        self.production_qty_spin.setValue(part.production_qty or 0)

    def _save_project(self) -> None:
        if not self.current_project_id:
            return
        self.project_repository.update_project(
            self.current_project_id,
            project_name=self.project_name_edit.text().strip(),
            project_type=self.project_type_edit.text().strip(),
            casting_method=self.casting_method_edit.text().strip(),
            status=self.project_status_edit.text().strip(),
            owner=self.project_owner_edit.text().strip(),
            root_dir=self.project_root_dir_edit.text().strip(),
        )
        self._load_projects()

    def _save_part(self) -> None:
        if not self.current_part_id:
            return
        existing_part = self.part_repository.get_part(self.current_part_id)
        self.part_repository.update_part(
            self.current_part_id,
            part_name=self.part_name_edit.text().strip(),
            part_no=self.part_no_edit.text().strip(),
            drawing_no=self.drawing_no_edit.text().strip(),
            material_name=self.material_name_edit.text().strip(),
            net_weight=self.net_weight_spin.value() or None,
            blank_weight=self.blank_weight_spin.value() or None,
            length_mm=existing_part.length_mm if existing_part else None,
            width_mm=existing_part.width_mm if existing_part else None,
            height_mm=existing_part.height_mm if existing_part else None,
            max_wall_thickness=self.max_wall_spin.value() or None,
            min_wall_thickness=self.min_wall_spin.value() or None,
            production_qty=self.production_qty_spin.value() or None,
            quality_grade=existing_part.quality_grade if existing_part else "",
            heat_treatment=existing_part.heat_treatment if existing_part else "",
            surface_requirement=existing_part.surface_requirement if existing_part else "",
            internal_quality_requirement=existing_part.internal_quality_requirement if existing_part else "",
        )
        QMessageBox.information(self, "已保存", "项目与零件基础信息已更新。")
        if self.current_project_id:
            self.session.set_current_project(self.current_project_id, self.current_part_id)

    def _clear_forms(self) -> None:
        self.current_project_id = None
        self.current_part_id = None
        self.project_code_label.setText("-")
        for widget in (
            self.project_name_edit,
            self.project_type_edit,
            self.casting_method_edit,
            self.project_status_edit,
            self.project_owner_edit,
            self.project_root_dir_edit,
            self.part_name_edit,
            self.part_no_edit,
            self.drawing_no_edit,
            self.material_name_edit,
        ):
            widget.clear()
        for spin in (
            self.net_weight_spin,
            self.blank_weight_spin,
            self.max_wall_spin,
            self.min_wall_spin,
        ):
            spin.setValue(0.0)
        self.production_qty_spin.setValue(0)
