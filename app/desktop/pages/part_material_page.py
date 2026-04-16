from __future__ import annotations

from PySide6.QtWidgets import (
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
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
from app.core.repositories.material_repository import MaterialRecord, MaterialRepository
from app.core.repositories.part_repository import PartRepository
from app.core.session import AppSession


class PartMaterialPage(QWidget):
    def __init__(self, paths: AppPaths, session: AppSession) -> None:
        super().__init__()
        self.paths = paths
        self.session = session
        self.part_repository = PartRepository(paths.database_path)
        self.material_repository = MaterialRepository(paths.database_path)
        self.current_project_id: str | None = None
        self.current_part_id: str | None = None
        self.current_material_id: str | None = None
        self.materials: list[MaterialRecord] = []

        layout = QHBoxLayout(self)
        layout.addWidget(self._build_part_box(), 3)
        layout.addWidget(self._build_material_box(), 4)

        self.session.project_changed.connect(self._on_project_changed)
        self._load_materials()

    def _build_part_box(self) -> QWidget:
        box = QGroupBox("零件详细信息", self)
        layout = QVBoxLayout(box)
        self.context_label = QLabel("请先在项目中心选择项目。", box)
        layout.addWidget(self.context_label)

        form = QFormLayout()
        self.part_name_edit = QLineEdit(box)
        self.part_no_edit = QLineEdit(box)
        self.drawing_no_edit = QLineEdit(box)
        self.material_name_edit = QLineEdit(box)
        self.length_spin = self._make_double_spin()
        self.width_spin = self._make_double_spin()
        self.height_spin = self._make_double_spin()
        self.net_weight_spin = self._make_double_spin()
        self.blank_weight_spin = self._make_double_spin()
        self.max_wall_spin = self._make_double_spin()
        self.min_wall_spin = self._make_double_spin()
        self.production_qty_spin = QSpinBox(box)
        self.production_qty_spin.setRange(0, 1000000)
        self.quality_grade_edit = QLineEdit(box)
        self.heat_treatment_edit = QLineEdit(box)
        self.surface_requirement_edit = QLineEdit(box)
        self.internal_quality_requirement_edit = QLineEdit(box)

        for label, widget in (
            ("零件名称", self.part_name_edit),
            ("零件编号", self.part_no_edit),
            ("图号", self.drawing_no_edit),
            ("材质名称", self.material_name_edit),
            ("长度(mm)", self.length_spin),
            ("宽度(mm)", self.width_spin),
            ("高度(mm)", self.height_spin),
            ("净重(kg)", self.net_weight_spin),
            ("毛坯重(kg)", self.blank_weight_spin),
            ("最大壁厚(mm)", self.max_wall_spin),
            ("最小壁厚(mm)", self.min_wall_spin),
            ("生产数量", self.production_qty_spin),
            ("质量等级", self.quality_grade_edit),
            ("热处理", self.heat_treatment_edit),
            ("表面要求", self.surface_requirement_edit),
            ("内部质量要求", self.internal_quality_requirement_edit),
        ):
            form.addRow(label, widget)
        layout.addLayout(form)

        save_button = QPushButton("保存零件详细信息", box)
        save_button.clicked.connect(self._save_part)
        layout.addWidget(save_button)
        layout.addStretch(1)
        return box

    def _build_material_box(self) -> QWidget:
        box = QGroupBox("材质库", self)
        layout = QHBoxLayout(box)

        left = QVBoxLayout()
        self.material_list = QListWidget(box)
        self.material_list.currentRowChanged.connect(self._on_material_selected)
        left.addWidget(self.material_list)
        refresh_button = QPushButton("刷新材质库", box)
        refresh_button.clicked.connect(self._load_materials)
        left.addWidget(refresh_button)
        layout.addLayout(left, 2)

        right = QVBoxLayout()
        form = QFormLayout()
        self.material_code_edit = QLineEdit(box)
        self.material_name_lib_edit = QLineEdit(box)
        self.material_category_edit = QLineEdit(box)
        self.density_spin = self._make_double_spin()
        self.liquidus_spin = self._make_double_spin()
        self.solidus_spin = self._make_double_spin()
        self.pouring_temp_min_spin = self._make_double_spin()
        self.pouring_temp_max_spin = self._make_double_spin()
        self.shrinkage_spin = self._make_double_spin(decimals=4)
        self.standard_ref_edit = QLineEdit(box)

        for label, widget in (
            ("材质牌号", self.material_code_edit),
            ("材质名称", self.material_name_lib_edit),
            ("类别", self.material_category_edit),
            ("密度(g/cm3)", self.density_spin),
            ("液相线(℃)", self.liquidus_spin),
            ("固相线(℃)", self.solidus_spin),
            ("浇注温度下限(℃)", self.pouring_temp_min_spin),
            ("浇注温度上限(℃)", self.pouring_temp_max_spin),
            ("收缩率", self.shrinkage_spin),
            ("标准依据", self.standard_ref_edit),
        ):
            form.addRow(label, widget)
        right.addLayout(form)

        save_button = QPushButton("保存材质", box)
        save_button.clicked.connect(self._save_material)
        right.addWidget(save_button)
        right.addStretch(1)
        layout.addLayout(right, 3)
        return box

    def _make_double_spin(self, *, decimals: int = 3) -> QDoubleSpinBox:
        spin = QDoubleSpinBox(self)
        spin.setRange(0.0, 1000000.0)
        spin.setDecimals(decimals)
        return spin

    def _on_project_changed(self, current_project) -> None:
        if current_project is None:
            self.current_project_id = None
            self.current_part_id = None
            self.context_label.setText("请先在项目中心选择项目。")
            self._clear_part()
            return
        self.current_project_id = current_project.project_id
        self.context_label.setText(f"当前项目：{current_project.project_id}")
        part = self.part_repository.get_primary_part(current_project.project_id)
        self.current_part_id = part.id if part else None
        self._load_part(part)
        self._select_material_by_name(part.material_name if part else "")

    def _load_part(self, part) -> None:
        if part is None:
            self._clear_part()
            return
        self.part_name_edit.setText(part.part_name)
        self.part_no_edit.setText(part.part_no)
        self.drawing_no_edit.setText(part.drawing_no)
        self.material_name_edit.setText(part.material_name)
        self.length_spin.setValue(part.length_mm or 0.0)
        self.width_spin.setValue(part.width_mm or 0.0)
        self.height_spin.setValue(part.height_mm or 0.0)
        self.net_weight_spin.setValue(part.net_weight or 0.0)
        self.blank_weight_spin.setValue(part.blank_weight or 0.0)
        self.max_wall_spin.setValue(part.max_wall_thickness or 0.0)
        self.min_wall_spin.setValue(part.min_wall_thickness or 0.0)
        self.production_qty_spin.setValue(part.production_qty or 0)
        self.quality_grade_edit.setText(part.quality_grade)
        self.heat_treatment_edit.setText(part.heat_treatment)
        self.surface_requirement_edit.setText(part.surface_requirement)
        self.internal_quality_requirement_edit.setText(part.internal_quality_requirement)

    def _save_part(self) -> None:
        if not self.current_part_id:
            QMessageBox.warning(self, "无法保存", "当前没有可编辑的零件。")
            return
        self.part_repository.update_part(
            self.current_part_id,
            part_name=self.part_name_edit.text().strip(),
            part_no=self.part_no_edit.text().strip(),
            drawing_no=self.drawing_no_edit.text().strip(),
            material_name=self.material_name_edit.text().strip(),
            net_weight=self.net_weight_spin.value() or None,
            blank_weight=self.blank_weight_spin.value() or None,
            length_mm=self.length_spin.value() or None,
            width_mm=self.width_spin.value() or None,
            height_mm=self.height_spin.value() or None,
            max_wall_thickness=self.max_wall_spin.value() or None,
            min_wall_thickness=self.min_wall_spin.value() or None,
            production_qty=self.production_qty_spin.value() or None,
            quality_grade=self.quality_grade_edit.text().strip(),
            heat_treatment=self.heat_treatment_edit.text().strip(),
            surface_requirement=self.surface_requirement_edit.text().strip(),
            internal_quality_requirement=self.internal_quality_requirement_edit.text().strip(),
        )
        QMessageBox.information(self, "已保存", "零件详细信息已更新。")

    def _load_materials(self) -> None:
        self.materials = self.material_repository.list_materials()
        self.material_list.clear()
        for material in self.materials:
            item = QListWidgetItem(f"{material.material_code} | {material.material_name}", self.material_list)
            item.setData(1, material.id)
        if self.materials:
            self.material_list.setCurrentRow(0)
        else:
            self._clear_material()

    def _select_material_by_name(self, material_name: str) -> None:
        if not material_name:
            return
        for index, material in enumerate(self.materials):
            if material.material_name == material_name or material.material_code == material_name:
                self.material_list.setCurrentRow(index)
                return

    def _on_material_selected(self, row: int) -> None:
        if row < 0 or row >= len(self.materials):
            self.current_material_id = None
            self._clear_material()
            return
        material = self.materials[row]
        self.current_material_id = material.id
        self.material_code_edit.setText(material.material_code)
        self.material_name_lib_edit.setText(material.material_name)
        self.material_category_edit.setText(material.category)
        self.density_spin.setValue(material.density or 0.0)
        self.liquidus_spin.setValue(material.liquidus_temp or 0.0)
        self.solidus_spin.setValue(material.solidus_temp or 0.0)
        self.pouring_temp_min_spin.setValue(material.pouring_temp_min or 0.0)
        self.pouring_temp_max_spin.setValue(material.pouring_temp_max or 0.0)
        self.shrinkage_spin.setValue(material.shrinkage_ratio or 0.0)
        self.standard_ref_edit.setText(material.standard_ref)

    def _save_material(self) -> None:
        material_code = self.material_code_edit.text().strip()
        material_name = self.material_name_lib_edit.text().strip()
        if not material_code or not material_name:
            QMessageBox.warning(self, "无法保存", "材质牌号和材质名称不能为空。")
            return
        self.material_repository.upsert_material(
            material_code=material_code,
            material_name=material_name,
            category=self.material_category_edit.text().strip(),
            density=self.density_spin.value() or None,
            liquidus_temp=self.liquidus_spin.value() or None,
            solidus_temp=self.solidus_spin.value() or None,
            pouring_temp_min=self.pouring_temp_min_spin.value() or None,
            pouring_temp_max=self.pouring_temp_max_spin.value() or None,
            shrinkage_ratio=self.shrinkage_spin.value() or None,
            standard_ref=self.standard_ref_edit.text().strip(),
        )
        self._load_materials()
        self._select_material_by_name(material_name)
        QMessageBox.information(self, "已保存", "材质库已更新。")

    def _clear_part(self) -> None:
        for widget in (
            self.part_name_edit,
            self.part_no_edit,
            self.drawing_no_edit,
            self.material_name_edit,
            self.quality_grade_edit,
            self.heat_treatment_edit,
            self.surface_requirement_edit,
            self.internal_quality_requirement_edit,
        ):
            widget.clear()
        for spin in (
            self.length_spin,
            self.width_spin,
            self.height_spin,
            self.net_weight_spin,
            self.blank_weight_spin,
            self.max_wall_spin,
            self.min_wall_spin,
        ):
            spin.setValue(0.0)
        self.production_qty_spin.setValue(0)

    def _clear_material(self) -> None:
        for widget in (
            self.material_code_edit,
            self.material_name_lib_edit,
            self.material_category_edit,
            self.standard_ref_edit,
        ):
            widget.clear()
        for spin in (
            self.density_spin,
            self.liquidus_spin,
            self.solidus_spin,
            self.pouring_temp_min_spin,
            self.pouring_temp_max_spin,
            self.shrinkage_spin,
        ):
            spin.setValue(0.0)
