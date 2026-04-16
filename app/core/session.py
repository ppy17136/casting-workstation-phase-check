from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import QObject, Signal


@dataclass(slots=True)
class SessionProject:
    project_id: str
    part_id: str | None = None


class AppSession(QObject):
    project_changed = Signal(object)
    scheme_changed = Signal(object)

    def __init__(self) -> None:
        super().__init__()
        self._current_project: SessionProject | None = None
        self._current_scheme_id: str | None = None

    @property
    def current_project(self) -> SessionProject | None:
        return self._current_project

    @property
    def current_scheme_id(self) -> str | None:
        return self._current_scheme_id

    def set_current_project(self, project_id: str, part_id: str | None = None) -> None:
        self._current_project = SessionProject(project_id=project_id, part_id=part_id)
        self._current_scheme_id = None
        self.project_changed.emit(self._current_project)
        self.scheme_changed.emit(None)

    def set_current_scheme(self, scheme_id: str | None) -> None:
        self._current_scheme_id = scheme_id
        self.scheme_changed.emit(scheme_id)

    def replay(self) -> None:
        self.project_changed.emit(self._current_project)
        self.scheme_changed.emit(self._current_scheme_id)
