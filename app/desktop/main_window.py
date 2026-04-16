from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QSplitter,
    QStackedWidget,
    QStatusBar,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from app.core.config import AppPaths
from app.core.session import AppSession
from app.desktop.pages.ai_page import AiPage
from app.desktop.pages.dashboard_page import DashboardPage
from app.desktop.pages.documents_page import DocumentsPage
from app.desktop.pages.export_page import ExportPage
from app.desktop.pages.parameter_page import ParameterPage
from app.desktop.pages.part_material_page import PartMaterialPage
from app.desktop.pages.project_center_page import ProjectCenterPage
from app.desktop.pages.results_page import ResultsPage
from app.desktop.pages.review_page import ReviewPage
from app.desktop.pages.scheme_page import SchemePage
from app.desktop.pages.settings_page import SettingsPage
from app.desktop.pages.simulation_page import SimulationPage
from app.desktop.pages.solidworks_page import SolidWorksPage


@dataclass(frozen=True, slots=True)
class NavigationItem:
    label: str
    page_name: str


class MainWindow(QMainWindow):
    def __init__(self, paths: AppPaths) -> None:
        super().__init__()
        self.paths = paths
        self.session = AppSession()
        self._page_index_by_name: dict[str, int] = {}
        self._navigation_items = [
            NavigationItem("仪表盘", "dashboard"),
            NavigationItem("项目中心", "projects"),
            NavigationItem("零件与材质", "parts"),
            NavigationItem("工艺方案", "schemes"),
            NavigationItem("参数计算", "parameters"),
            NavigationItem("SolidWorks 协同", "solidworks"),
            NavigationItem("ProCAST 仿真", "simulation"),
            NavigationItem("结果对比", "results"),
            NavigationItem("工艺卡与质检", "documents"),
            NavigationItem("辅助建议", "ai"),
            NavigationItem("人工审核", "review"),
            NavigationItem("成果导出", "export"),
            NavigationItem("系统设置", "settings"),
        ]
        self.setWindowTitle("砂型铸造工艺图—工艺卡—仿真校核辅助工作站")
        self.resize(1440, 900)
        self._setup_ui()

    def _setup_ui(self) -> None:
        self._setup_toolbar()
        self._setup_status_bar()

        central = QWidget(self)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)

        splitter = QSplitter(Qt.Orientation.Horizontal, central)
        splitter.setChildrenCollapsible(False)
        splitter.addWidget(self._build_navigation_panel())
        splitter.addWidget(self._build_content_panel())
        splitter.setSizes([260, 1180])

        layout.addWidget(splitter)
        self.setCentralWidget(central)

    def _setup_toolbar(self) -> None:
        toolbar = QToolBar("主工具栏", self)
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        open_project_action = QAction("打开项目目录", self)
        open_project_action.triggered.connect(self._show_not_implemented)
        toolbar.addAction(open_project_action)

        database_action = QAction("数据库状态", self)
        database_action.triggered.connect(self._show_database_location)
        toolbar.addAction(database_action)

    def _setup_status_bar(self) -> None:
        status_bar = QStatusBar(self)
        status_bar.showMessage(f"数据库：{self.paths.database_path}")
        self.setStatusBar(status_bar)

    def _build_navigation_panel(self) -> QWidget:
        panel = QFrame(self)
        panel.setFrameShape(QFrame.Shape.StyledPanel)
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(12, 12, 12, 12)

        title = QLabel("项目功能导航", panel)
        title.setObjectName("navTitle")
        panel_layout.addWidget(title)

        self.nav_list = QListWidget(panel)
        for item in self._navigation_items:
            QListWidgetItem(item.label, self.nav_list)
        self.nav_list.currentRowChanged.connect(self._on_nav_changed)
        panel_layout.addWidget(self.nav_list, 1)
        return panel

    def _build_content_panel(self) -> QWidget:
        panel = QWidget(self)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(12, 12, 12, 12)

        self.page_title = QLabel("仪表盘", panel)
        self.page_title.setObjectName("pageTitle")
        layout.addWidget(self.page_title)

        self.stack = QStackedWidget(panel)
        layout.addWidget(self.stack, 1)

        self._add_page("dashboard", DashboardPage(self.paths))
        self._add_page("projects", ProjectCenterPage(self.paths, self.session))
        self._add_page("parts", PartMaterialPage(self.paths, self.session))
        self._add_page("schemes", SchemePage(self.paths, self.session))
        self._add_page("parameters", ParameterPage(self.paths, self.session))
        self._add_page("solidworks", SolidWorksPage(self.paths, self.session))
        self._add_page("simulation", SimulationPage(self.paths, self.session))
        self._add_page("results", ResultsPage(self.paths, self.session))
        self._add_page("documents", DocumentsPage(self.paths, self.session))
        self._add_page("ai", AiPage(self.paths, self.session))
        self._add_page("review", ReviewPage(self.paths, self.session))
        self._add_page("export", ExportPage(self.paths, self.session))
        self._add_page("settings", SettingsPage(self.paths))

        self.session.replay()
        self.nav_list.setCurrentRow(0)
        return panel

    def _add_page(self, name: str, widget: QWidget) -> None:
        index = self.stack.addWidget(widget)
        self._page_index_by_name[name] = index

    def _on_nav_changed(self, row: int) -> None:
        if row < 0 or row >= len(self._navigation_items):
            return
        item = self._navigation_items[row]
        self.page_title.setText(item.label)
        self.stack.setCurrentIndex(self._page_index_by_name[item.page_name])

    def _show_database_location(self) -> None:
        QMessageBox.information(
            self,
            "数据库状态",
            f"当前数据库位置：\n{self.paths.database_path}",
        )

    def _show_not_implemented(self) -> None:
        QMessageBox.information(self, "提示", "该操作将在后续版本实现。")
