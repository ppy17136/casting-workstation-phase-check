from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from app.core.config import AppPaths
from app.core.db.initializer import initialize_database
from app.core.environment import record_environment_check
from app.desktop.main_window import MainWindow


def main() -> int:
    """Application entry point."""
    paths = AppPaths.default()
    paths.ensure_directories()
    initialize_database(paths.database_path)
    record_environment_check(paths.database_path)

    app = QApplication(sys.argv)
    app.setApplicationName("砂型铸造工艺图—工艺卡—仿真校核辅助工作站")
    app.setOrganizationName("Liaoning Petrochemical University")

    window = MainWindow(paths)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
