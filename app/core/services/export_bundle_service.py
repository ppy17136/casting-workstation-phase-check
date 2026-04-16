from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import shutil
import zipfile

from app.core.repositories.cad_repository import CadRepository
from app.core.repositories.document_repository import DocumentRepository
from app.core.repositories.project_repository import ProjectRecord
from app.core.repositories.simulation_repository import SimulationRepository


@dataclass(slots=True)
class ExportBundleResult:
    bundle_dir: Path
    zip_path: Path
    copied_files: list[Path]


class ExportBundleService:
    def __init__(
        self,
        *,
        document_repository: DocumentRepository,
        cad_repository: CadRepository,
        simulation_repository: SimulationRepository,
    ) -> None:
        self.document_repository = document_repository
        self.cad_repository = cad_repository
        self.simulation_repository = simulation_repository

    def export_scheme_bundle(
        self,
        *,
        project: ProjectRecord,
        scheme_id: str,
        bundle_name: str,
    ) -> ExportBundleResult:
        export_root = Path(project.root_dir) / "generated_exports" / bundle_name
        if export_root.exists():
            shutil.rmtree(export_root)
        docs_dir = export_root / "documents"
        cad_dir = export_root / "cad"
        sim_dir = export_root / "simulation"
        for directory in (docs_dir, cad_dir, sim_dir):
            directory.mkdir(parents=True, exist_ok=True)

        copied_files: list[Path] = []

        latest_card = self.document_repository.get_latest_process_card(scheme_id)
        if latest_card is not None:
            copied_files.extend(
                self._copy_if_exists(
                    [
                        Path(latest_card.docx_path),
                        Path(latest_card.docx_path).with_suffix(".md"),
                        Path(latest_card.docx_path.replace("_process_card.docx", "_inspection_checklist.md")),
                    ],
                    docs_dir,
                )
            )

        cad_model = self.cad_repository.get_model_for_scheme(scheme_id)
        if cad_model is not None:
            copied_files.extend(self._copy_if_exists([Path(cad_model.file_path)], cad_dir))
            for export_record in self.cad_repository.list_exports(cad_model.id):
                copied_files.extend(self._copy_if_exists([Path(export_record.export_path)], cad_dir))

        for job in self.simulation_repository.list_jobs(scheme_id):
            job_dir = sim_dir / job.job_code
            job_dir.mkdir(parents=True, exist_ok=True)
            copied_files.extend(self._copy_if_exists([Path(job.input_dir), Path(job.output_dir)], job_dir))
            for result in self.simulation_repository.list_results(job.id):
                copied_files.extend(self._copy_if_exists([Path(result.file_path), Path(result.image_path)], job_dir))

        readme_path = export_root / "README.txt"
        readme_path.write_text(
            "\n".join(
                [
                    f"项目编号：{project.project_code}",
                    f"项目名称：{project.project_name}",
                    f"方案 ID：{scheme_id}",
                    f"成果包名称：{bundle_name}",
                    "",
                    "本成果包用于归档以下阶段性材料：",
                    "1. 工艺卡与质检/缺陷预防清单",
                    "2. CAD 模型与导出文件",
                    "3. ProCAST 仿真任务目录与结果文件",
                    "",
                    "已收集文件：",
                    *[str(path) for path in copied_files],
                ]
            ),
            encoding="utf-8",
        )
        copied_files.append(readme_path)

        zip_path = export_root.with_suffix(".zip")
        if zip_path.exists():
            zip_path.unlink()
        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for file_path in export_root.rglob("*"):
                if file_path.is_file():
                    archive.write(file_path, file_path.relative_to(export_root.parent))

        return ExportBundleResult(bundle_dir=export_root, zip_path=zip_path, copied_files=copied_files)

    def _copy_if_exists(self, paths: list[Path], target_dir: Path) -> list[Path]:
        copied: list[Path] = []
        for source in paths:
            if source is None:
                continue
            source_text = str(source).strip()
            if not source_text or source_text in {".", ".\\"}:
                continue
            if not source.is_absolute() and source_text.startswith("."):
                continue
            if not source.exists():
                continue
            destination = target_dir / source.name
            if source.is_dir():
                if destination.exists():
                    shutil.rmtree(destination)
                shutil.copytree(source, destination)
                copied.append(destination)
            else:
                shutil.copy2(source, destination)
                copied.append(destination)
        return copied
