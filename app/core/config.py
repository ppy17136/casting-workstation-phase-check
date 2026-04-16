from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os


APP_DIR_NAME = "CastingWorkstation"
DEFAULT_PROJECT_DIR_NAME = "CastingProjects"


@dataclass(slots=True)
class AppPaths:
    app_data_dir: Path
    templates_dir: Path
    knowledge_dir: Path
    logs_dir: Path
    projects_dir: Path
    database_path: Path

    @classmethod
    def default(cls) -> "AppPaths":
        appdata_root = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
        documents_root = Path.home() / "Documents"
        app_data_dir = appdata_root / APP_DIR_NAME
        return cls(
            app_data_dir=app_data_dir,
            templates_dir=app_data_dir / "templates",
            knowledge_dir=app_data_dir / "knowledge",
            logs_dir=app_data_dir / "logs",
            projects_dir=documents_root / DEFAULT_PROJECT_DIR_NAME,
            database_path=app_data_dir / "casting_workstation.db",
        )

    def ensure_directories(self) -> None:
        for directory in (
            self.app_data_dir,
            self.templates_dir,
            self.knowledge_dir,
            self.logs_dir,
            self.projects_dir,
        ):
            directory.mkdir(parents=True, exist_ok=True)
