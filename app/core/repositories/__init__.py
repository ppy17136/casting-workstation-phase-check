"""Database repositories."""

from app.core.repositories.ai_repository import AiRepository, EvidenceRecord, SuggestionCardRecord
from app.core.repositories.cad_repository import CadExportRecord, CadModelRecord, CadRepository
from app.core.repositories.document_repository import (
    DocumentRepository,
    InspectionItemRecord,
    ProcessCardRecord,
)
from app.core.repositories.material_repository import MaterialRecord, MaterialRepository
from app.core.repositories.parameter_repository import ParameterRecord, ParameterRepository
from app.core.repositories.part_repository import PartRecord, PartRepository
from app.core.repositories.project_repository import ProjectRecord, ProjectRepository
from app.core.repositories.scheme_repository import SchemeRecord, SchemeRepository
from app.core.repositories.settings_repository import SettingRecord, SettingsRepository
from app.core.repositories.simulation_repository import (
    SimulationJobRecord,
    SimulationRepository,
    SimulationResultRecord,
)

__all__ = [
    "AiRepository",
    "CadExportRecord",
    "CadModelRecord",
    "CadRepository",
    "DocumentRepository",
    "EvidenceRecord",
    "InspectionItemRecord",
    "MaterialRecord",
    "MaterialRepository",
    "ParameterRecord",
    "ParameterRepository",
    "PartRecord",
    "PartRepository",
    "ProcessCardRecord",
    "ProjectRecord",
    "ProjectRepository",
    "SchemeRecord",
    "SchemeRepository",
    "SettingRecord",
    "SettingsRepository",
    "SimulationJobRecord",
    "SimulationRepository",
    "SimulationResultRecord",
    "SuggestionCardRecord",
]
