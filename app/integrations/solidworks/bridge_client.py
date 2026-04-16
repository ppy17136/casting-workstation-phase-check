from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
import subprocess

from app.core.config import AppPaths
from app.core.runtime import executable_root, is_frozen


@dataclass(slots=True)
class BridgeResult:
    ok: bool
    payload: dict
    raw_output: str


class SolidWorksBridgeClient:
    def __init__(self, app_paths: AppPaths) -> None:
        self.app_paths = app_paths

    def bridge_executable(self) -> Path:
        if is_frozen():
            packaged_candidate = executable_root().parent / "SolidWorksBridge" / "SolidWorksBridge.exe"
            if packaged_candidate.exists():
                return packaged_candidate

        local_candidate = Path(__file__).resolve().parents[3] / "bridge" / "solidworks-bridge" / "bin" / "SolidWorksBridge.exe"
        installed_candidate = self.app_paths.app_data_dir / "SolidWorksBridge" / "SolidWorksBridge.exe"
        if local_candidate.exists():
            return local_candidate
        return installed_candidate

    def is_available(self) -> bool:
        return self.bridge_executable().exists()

    def ping(self) -> BridgeResult:
        return self._run(["ping"])

    def info(self) -> BridgeResult:
        return self._run(["info"])

    def export_file(self, input_path: Path, output_path: Path, export_type: str) -> BridgeResult:
        return self._run(
            [
                "export",
                "--input",
                str(input_path),
                "--output",
                str(output_path),
                "--format",
                export_type,
            ]
        )

    def _run(self, arguments: list[str]) -> BridgeResult:
        executable = self.bridge_executable()
        if not executable.exists():
            return BridgeResult(
                ok=False,
                payload={"error": "bridge_not_found", "path": str(executable)},
                raw_output="",
            )

        completed = subprocess.run(
            [str(executable), *arguments],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        stdout = completed.stdout.strip()
        try:
            payload = json.loads(stdout) if stdout else {}
        except json.JSONDecodeError:
            payload = {"stdout": stdout}

        return BridgeResult(
            ok=completed.returncode == 0,
            payload=payload,
            raw_output=stdout,
        )
