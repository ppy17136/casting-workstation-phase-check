from __future__ import annotations

from PySide6.QtWidgets import QGridLayout, QGroupBox, QLabel, QVBoxLayout, QWidget

from app.core.config import AppPaths
from app.core.repositories.ai_repository import AiRepository
from app.core.repositories.project_repository import ProjectRepository
from app.core.repositories.simulation_repository import SimulationRepository


class DashboardPage(QWidget):
    def __init__(self, paths: AppPaths) -> None:
        super().__init__()
        project_repository = ProjectRepository(paths.database_path)
        simulation_repository = SimulationRepository(paths.database_path)
        ai_repository = AiRepository(paths.database_path)
        project_count = project_repository.count_projects()
        simulation_count = simulation_repository.count_jobs()
        pending_review_count = len(ai_repository.list_pending_reviews())
        environment = project_repository.latest_environment_status()

        layout = QVBoxLayout(self)
        grid = QGridLayout()
        layout.addLayout(grid)

        cards = [
            ("项目数量", str(project_count)),
            ("仿真任务数", str(simulation_count)),
            ("待审核辅助建议", str(pending_review_count)),
            ("数据库", str(paths.database_path)),
            ("项目目录", str(paths.projects_dir)),
            ("模板目录", str(paths.templates_dir)),
            ("知识库目录", str(paths.knowledge_dir)),
            ("SolidWorks", environment["solidworks"]),
            ("ProCAST", environment["procast"]),
            ("LLM", environment["llm"]),
        ]
        for index, (title, value) in enumerate(cards):
            box = QGroupBox(title, self)
            box_layout = QVBoxLayout(box)
            box_layout.addWidget(QLabel(value, box))
            grid.addWidget(box, index // 3, index % 3)

        todo = QGroupBox("阶段检查主线", self)
        todo_layout = QVBoxLayout(todo)
        todo_layout.addWidget(QLabel("1. 在项目中心维护典型件、材质和项目基础信息"))
        todo_layout.addWidget(QLabel("2. 在工艺方案与参数页完成工艺设计、关键参数计算和记录"))
        todo_layout.addWidget(QLabel("3. 在 SolidWorks 与 ProCAST 页面归档建模文件、仿真任务和结果图"))
        todo_layout.addWidget(QLabel("4. 在文档页生成工艺卡、缺陷预防/质检清单等阶段成果"))
        todo_layout.addWidget(QLabel("5. 在成果导出页打包“工艺图—工艺卡—仿真校核”项目附件"))
        layout.addWidget(todo)
