from __future__ import annotations

import json
import os
from pathlib import Path
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "windows" if os.name == "nt" else "offscreen")

WORKSPACE = Path(__file__).resolve().parents[1]
if str(WORKSPACE) not in sys.path:
    sys.path.insert(0, str(WORKSPACE))

from PySide6.QtCore import QSize
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

from app.core.config import AppPaths
from app.core.db.initializer import initialize_database
from app.core.environment import record_environment_check
from app.desktop.main_window import MainWindow


SCREEN_TARGETS = [
    ("dashboard", "dashboard.png"),
    ("projects", "project_center.png"),
    ("parts", "parts.png"),
    ("schemes", "scheme.png"),
    ("parameters", "parameters.png"),
    ("solidworks", "solidworks.png"),
    ("simulation", "simulation.png"),
    ("results", "results.png"),
    ("documents", "documents.png"),
    ("ai", "ai.png"),
    ("review", "review.png"),
    ("export", "export.png"),
    ("settings", "settings.png"),
]


def main() -> None:
    paths = AppPaths.default()
    paths.ensure_directories()
    initialize_database(paths.database_path)
    record_environment_check(paths.database_path)

    manifest_path = WORKSPACE / "artifacts" / "demo_case.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    app = QApplication(sys.argv)
    app.setApplicationName("砂型铸造工艺图—工艺卡—仿真校核辅助工作站")
    app.setOrganizationName("Liaoning Petrochemical University")
    app.setFont(QFont("Microsoft YaHei UI", 10))

    window = MainWindow(paths)
    window.resize(QSize(1440, 900))
    window.show()
    app.processEvents()

    window.session.set_current_project(manifest["project_id"], manifest["part_id"])
    window.session.set_current_scheme(manifest["scheme_id"])
    app.processEvents()

    output_dir = WORKSPACE / "artifacts" / "walkthrough"
    output_dir.mkdir(parents=True, exist_ok=True)

    page_names = [item.page_name for item in window._navigation_items]  # noqa: SLF001
    for page_name, filename in SCREEN_TARGETS:
        try:
            row = page_names.index(page_name)
        except ValueError:
            continue
        window.nav_list.setCurrentRow(row)
        app.processEvents()
        shot_path = output_dir / filename
        window.grab().save(str(shot_path))
        print(f"captured: {shot_path}")

    window.close()
    app.quit()


if __name__ == "__main__":
    main()
