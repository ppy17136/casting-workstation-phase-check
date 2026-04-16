from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os
import platform
import re
import shutil

from app.core.db.connection import create_connection


@dataclass(slots=True)
class EnvironmentCheck:
    machine_name: str
    os_version: str
    solidworks_found: int
    solidworks_version: str
    procast_found: int
    procast_version: str
    llm_mode: str


def detect_environment() -> EnvironmentCheck:
    solidworks_path = _find_solidworks_path()
    procast_path = _find_procast_path()
    return EnvironmentCheck(
        machine_name=platform.node(),
        os_version=f"{platform.system()} {platform.release()}",
        solidworks_found=int(solidworks_path is not None),
        solidworks_version=_extract_solidworks_version(solidworks_path) if solidworks_path else "",
        procast_found=int(procast_path is not None),
        procast_version=_extract_procast_version(procast_path) if procast_path else "",
        llm_mode=os.environ.get("CASTING_WORKSTATION_LLM_MODE", "disabled"),
    )


def record_environment_check(database_path: Path) -> None:
    check = detect_environment()
    with create_connection(database_path) as connection:
        connection.execute(
            """
            INSERT INTO environment_checks (
                id, machine_name, os_version, solidworks_found, solidworks_version,
                procast_found, procast_version, llm_mode, last_checked_at,
                created_at, updated_at, created_by, updated_by, is_deleted, remark
            ) VALUES (
                lower(hex(randomblob(16))), ?, ?, ?, ?, ?, ?, ?, datetime('now'),
                datetime('now'), datetime('now'), 'system', 'system', 0, ''
            );
            """,
            (
                check.machine_name,
                check.os_version,
                check.solidworks_found,
                check.solidworks_version,
                check.procast_found,
                check.procast_version,
                check.llm_mode,
            ),
        )
        connection.commit()


def _find_solidworks_path() -> Path | None:
    direct = shutil.which("SLDWORKS.exe")
    if direct:
        return Path(direct)

    candidates = [
        Path("C:/Program Files/SOLIDWORKS Corp/SOLIDWORKS/SLDWORKS.exe"),
        Path("C:/Program Files (x86)/SOLIDWORKS Corp/SOLIDWORKS/SLDWORKS.exe"),
        Path("E:/Program Files/SOLIDWORKS Corp/SOLIDWORKS/SLDWORKS.exe"),
        Path("E:/Program Files (x86)/SOLIDWORKS Corp/SOLIDWORKS/SLDWORKS.exe"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate

    common_roots = [
        Path("C:/Program Files/SOLIDWORKS Corp"),
        Path("C:/Program Files (x86)/SOLIDWORKS Corp"),
        Path("E:/Program Files/SOLIDWORKS Corp"),
        Path("E:/Program Files (x86)/SOLIDWORKS Corp"),
    ]
    for root in common_roots:
        if not root.exists():
            continue
        for match in root.rglob("SLDWORKS.exe"):
            return match
    return None


def _find_procast_path() -> Path | None:
    common_executables = [
        shutil.which("Visual-Environment.exe"),
        shutil.which("VisualEnvironment.exe"),
        shutil.which("VisualEnv.exe"),
        shutil.which("procast.exe"),
        shutil.which("esi_procast.exe"),
    ]
    for executable in common_executables:
        if executable:
            return Path(executable)

    common_roots = [
        Path("C:/Program Files/ESI Group"),
        Path("C:/Program Files/ESI-Group"),
        Path("C:/Program Files (x86)/ESI Group"),
        Path("E:/Program Files/ESI Group"),
        Path("E:/Program Files/ESI-Group"),
        Path("E:/Program Files (x86)/ESI Group"),
    ]
    for root in common_roots:
        if not root.exists():
            continue
        for pattern in ("esi_procast.exe", "VisualEnv.exe", "Visual-Environment.exe", "VisualEnvironment.exe", "procast.exe"):
            matches = list(root.rglob(pattern))
            if matches:
                return matches[0]
    return None


def _extract_solidworks_version(executable: Path) -> str:
    version_pattern = re.compile(r"\d{4}(?:\.\d+)?")
    for part in executable.parts:
        if version_pattern.fullmatch(part):
            return part
    return executable.parent.name


def _extract_procast_version(executable: Path) -> str:
    version_pattern = re.compile(r"\d+(?:\.\d+)+")
    parts = executable.parts

    if "ProCAST" in parts:
        index = parts.index("ProCAST")
        if index + 1 < len(parts) and version_pattern.fullmatch(parts[index + 1]):
            return parts[index + 1]

    if "Visual-Environment" in parts:
        index = parts.index("Visual-Environment")
        if index + 1 < len(parts) and version_pattern.fullmatch(parts[index + 1]):
            return parts[index + 1]

    for part in parts:
        if version_pattern.fullmatch(part):
            return part

    return executable.parent.name
