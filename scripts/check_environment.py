from __future__ import annotations

from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.core.config import AppPaths
from app.core.db.initializer import initialize_database
from app.core.environment import detect_environment, record_environment_check


def main() -> None:
    paths = AppPaths.default()
    paths.ensure_directories()
    initialize_database(paths.database_path)
    record_environment_check(paths.database_path)
    check = detect_environment()
    print("Environment check completed.")
    print(f"Machine: {check.machine_name}")
    print(f"OS: {check.os_version}")
    print(f"SolidWorks found: {bool(check.solidworks_found)}")
    print(f"ProCAST found: {bool(check.procast_found)}")
    print(f"LLM mode: {check.llm_mode}")


if __name__ == "__main__":
    main()
