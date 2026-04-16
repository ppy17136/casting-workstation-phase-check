from __future__ import annotations

from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.core.config import AppPaths
from app.core.db.initializer import initialize_database


def main() -> None:
    paths = AppPaths.default()
    paths.ensure_directories()
    initialize_database(paths.database_path)
    print(f"Database initialized at: {paths.database_path}")


if __name__ == "__main__":
    main()
