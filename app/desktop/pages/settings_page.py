from __future__ import annotations

from PySide6.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.core.config import AppPaths
from app.core.repositories.project_repository import ProjectRepository
from app.core.repositories.settings_repository import SettingsRepository


class SettingsPage(QWidget):
    def __init__(self, paths: AppPaths) -> None:
        super().__init__()
        self.paths = paths
        self.settings_repository = SettingsRepository(paths.database_path)
        self.project_repository = ProjectRepository(paths.database_path)

        layout = QVBoxLayout(self)
        layout.addWidget(self._build_llm_box())
        layout.addWidget(self._build_integration_box())
        layout.addWidget(self._build_runtime_box())
        layout.addStretch(1)

        self._load_settings()

    def _build_llm_box(self) -> QWidget:
        box = QGroupBox("LLM 配置", self)
        form = QFormLayout(box)
        self.llm_mode_edit = QLineEdit(box)
        self.llm_mode_edit.setPlaceholderText("local / remote / disabled")
        self.llm_base_url_edit = QLineEdit(box)
        self.llm_model_edit = QLineEdit(box)
        self.llm_api_key_edit = QLineEdit(box)
        self.llm_api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        save_button = QPushButton("保存 LLM 配置", box)
        save_button.clicked.connect(self._save_llm_settings)

        form.addRow("模式", self.llm_mode_edit)
        form.addRow("服务地址", self.llm_base_url_edit)
        form.addRow("模型名称", self.llm_model_edit)
        form.addRow("API Key", self.llm_api_key_edit)
        form.addRow("", save_button)
        return box

    def _build_integration_box(self) -> QWidget:
        box = QGroupBox("本地集成配置", self)
        form = QFormLayout(box)
        self.bridge_path_edit = QLineEdit(box)
        self.procast_path_edit = QLineEdit(box)
        self.project_root_edit = QLineEdit(box)
        save_button = QPushButton("保存集成配置", box)
        save_button.clicked.connect(self._save_integration_settings)

        form.addRow("SolidWorksBridge 路径", self.bridge_path_edit)
        form.addRow("ProCAST 安装目录", self.procast_path_edit)
        form.addRow("默认项目目录", self.project_root_edit)
        form.addRow("", save_button)
        return box

    def _build_runtime_box(self) -> QWidget:
        box = QGroupBox("运行信息", self)
        layout = QVBoxLayout(box)
        self.runtime_label = QLabel(box)
        self.runtime_label.setWordWrap(True)
        layout.addWidget(self.runtime_label)

        button_bar = QHBoxLayout()
        reload_button = QPushButton("刷新配置", box)
        reload_button.clicked.connect(self._load_settings)
        show_all_button = QPushButton("显示所有设置", box)
        show_all_button.clicked.connect(self._show_all_settings)
        button_bar.addWidget(reload_button)
        button_bar.addWidget(show_all_button)
        button_bar.addStretch(1)
        layout.addLayout(button_bar)

        self.settings_dump = QTextEdit(box)
        self.settings_dump.setReadOnly(True)
        self.settings_dump.setMaximumHeight(180)
        layout.addWidget(self.settings_dump)
        return box

    def _load_settings(self) -> None:
        self.llm_mode_edit.setText(self.settings_repository.get_setting("llm.mode", "disabled"))
        self.llm_base_url_edit.setText(self.settings_repository.get_setting("llm.base_url", ""))
        self.llm_model_edit.setText(self.settings_repository.get_setting("llm.model", ""))
        self.llm_api_key_edit.setText(self.settings_repository.get_setting("llm.api_key", ""))
        self.bridge_path_edit.setText(self.settings_repository.get_setting("integration.solidworks_bridge_path", ""))
        self.procast_path_edit.setText(self.settings_repository.get_setting("integration.procast_install_dir", ""))
        self.project_root_edit.setText(
            self.settings_repository.get_setting("integration.default_project_root", str(self.paths.projects_dir))
        )
        self.runtime_label.setText(
            "\n".join(
                [
                    f"数据库：{self.paths.database_path}",
                    f"应用数据目录：{self.paths.app_data_dir}",
                    f"项目目录：{self.paths.projects_dir}",
                    f"环境状态：{self.project_repository.latest_environment_status()}",
                ]
            )
        )
        self._show_all_settings()

    def _save_llm_settings(self) -> None:
        self.settings_repository.set_setting(
            setting_key="llm.mode",
            setting_value=self.llm_mode_edit.text().strip(),
            setting_group="llm",
        )
        self.settings_repository.set_setting(
            setting_key="llm.base_url",
            setting_value=self.llm_base_url_edit.text().strip(),
            setting_group="llm",
        )
        self.settings_repository.set_setting(
            setting_key="llm.model",
            setting_value=self.llm_model_edit.text().strip(),
            setting_group="llm",
        )
        self.settings_repository.set_setting(
            setting_key="llm.api_key",
            setting_value=self.llm_api_key_edit.text().strip(),
            setting_group="llm",
        )
        self._show_all_settings()
        QMessageBox.information(self, "已保存", "LLM 配置已更新。")

    def _save_integration_settings(self) -> None:
        self.settings_repository.set_setting(
            setting_key="integration.solidworks_bridge_path",
            setting_value=self.bridge_path_edit.text().strip(),
            setting_group="integration",
        )
        self.settings_repository.set_setting(
            setting_key="integration.procast_install_dir",
            setting_value=self.procast_path_edit.text().strip(),
            setting_group="integration",
        )
        self.settings_repository.set_setting(
            setting_key="integration.default_project_root",
            setting_value=self.project_root_edit.text().strip(),
            setting_group="integration",
        )
        self._show_all_settings()
        QMessageBox.information(self, "已保存", "本地集成配置已更新。")

    def _show_all_settings(self) -> None:
        records = self.settings_repository.list_settings()
        if not records:
            self.settings_dump.setPlainText("当前还没有保存任何设置。")
            return
        self.settings_dump.setPlainText(
            "\n".join(
                [
                    f"[{item.setting_group}] {item.setting_key} = {item.setting_value}"
                    for item in records
                ]
            )
        )
