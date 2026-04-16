from __future__ import annotations

import json
from pathlib import Path
import sys

WORKSPACE = Path(__file__).resolve().parents[1]
if str(WORKSPACE) not in sys.path:
    sys.path.insert(0, str(WORKSPACE))

from app.core.config import AppPaths
from app.core.repositories import (
    AiRepository,
    CadRepository,
    DocumentRepository,
    MaterialRepository,
    ParameterRepository,
    PartRepository,
    ProjectRepository,
    SchemeRepository,
    SettingsRepository,
    SimulationRepository,
)
from app.core.services import (
    DocumentGenerationService,
    ExportBundleService,
    SuggestionGenerationService,
)
from scripts.prepare_demo_case import seed_materials, seed_settings


def main() -> None:
    workspace = Path(__file__).resolve().parents[1]
    artifacts_dir = workspace / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = artifacts_dir / "demo_case.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    paths = AppPaths.default()
    paths.ensure_directories()

    project_repository = ProjectRepository(paths.database_path)
    part_repository = PartRepository(paths.database_path)
    scheme_repository = SchemeRepository(paths.database_path)
    parameter_repository = ParameterRepository(paths.database_path)
    simulation_repository = SimulationRepository(paths.database_path)
    document_repository = DocumentRepository(paths.database_path)
    ai_repository = AiRepository(paths.database_path)
    material_repository = MaterialRepository(paths.database_path)
    settings_repository = SettingsRepository(paths.database_path)

    document_service = DocumentGenerationService(document_repository)
    suggestion_service = SuggestionGenerationService()
    export_service = ExportBundleService(
        document_repository=document_repository,
        cad_repository=CadRepository(paths.database_path),
        simulation_repository=simulation_repository,
    )

    seed_materials(material_repository)
    seed_settings(settings_repository, paths)

    project = project_repository.get_project(manifest["project_id"])
    part = part_repository.get_part(manifest["part_id"])
    scheme = scheme_repository.get_scheme(manifest["scheme_id"])
    parameters = parameter_repository.list_by_scheme(manifest["scheme_id"])
    jobs = simulation_repository.list_jobs(manifest["scheme_id"])
    latest_job = jobs[0] if jobs else None
    results = simulation_repository.list_results(latest_job.id) if latest_job else []

    if project is None or part is None or scheme is None:
        raise RuntimeError("Demo case records are incomplete.")

    part_repository.update_part(
        part.id,
        part_name=part.part_name or "圆盖铝合金件",
        part_no=part.part_no or "ROUND-COVER-01",
        drawing_no=part.drawing_no or "ROUND-COVER-YL112",
        material_name=part.material_name or "YL112",
        net_weight=part.net_weight or 2.85,
        blank_weight=part.blank_weight or 5.65,
        length_mm=part.length_mm or 176.0,
        width_mm=part.width_mm or 176.0,
        height_mm=part.height_mm or 53.0,
        max_wall_thickness=part.max_wall_thickness or 24.0,
        min_wall_thickness=part.min_wall_thickness or 6.0,
        production_qty=part.production_qty or 50,
        quality_grade=part.quality_grade or "CT8 / Ra12.5",
        heat_treatment=part.heat_treatment or "T5",
        surface_requirement=part.surface_requirement or "非加工面喷砂，分型面打磨去毛刺。",
        internal_quality_requirement=part.internal_quality_requirement
        or "关键热节区域不得出现缩孔缩松，X 射线抽检 II 级。",
    )
    part = part_repository.get_part(part.id)
    assert part is not None

    document_bundle = document_service.generate_bundle(
        project=project,
        part=part,
        scheme=scheme,
        parameters=parameters,
    )

    suggestions = suggestion_service.generate(
        scheme=scheme,
        parameters=parameters,
        results=results,
    )
    ai_repository.replace_generated_suggestions(
        scheme_id=scheme.id,
        job_id=latest_job.id if latest_job else None,
        suggestions=suggestions,
    )
    stored_cards = ai_repository.list_suggestions(scheme.id)
    approved_card_id = ""
    if stored_cards:
        approved_card_id = stored_cards[0].id
        ai_repository.review_suggestion(
            suggestion_id=approved_card_id,
            reviewer="demo",
            decision="approve",
            comment="阶段演示流程中已完成首条辅助建议的人工确认。",
        )
    pending_cards = ai_repository.list_pending_reviews(scheme.id)

    export_result = export_service.export_scheme_bundle(
        project=project,
        scheme_id=scheme.id,
        bundle_name=f"{project.project_code}_{scheme.id}",
    )

    summary = {
        "project_code": project.project_code,
        "project_name": project.project_name,
        "project_root": project.root_dir,
        "scheme_id": scheme.id,
        "scheme_code": scheme.scheme_code,
        "document_card_path": str(document_bundle.card_path),
        "document_markdown_path": str(document_bundle.markdown_card_path),
        "checklist_path": str(document_bundle.checklist_path),
        "suggestion_count": len(stored_cards),
        "approved_card_id": approved_card_id,
        "pending_review_count": len(pending_cards),
        "export_bundle_dir": str(export_result.bundle_dir),
        "export_zip_path": str(export_result.zip_path),
        "exported_files": [str(path) for path in export_result.copied_files],
    }

    summary_json = artifacts_dir / "demo_workflow_summary.json"
    summary_md = artifacts_dir / "demo_workflow_summary.md"
    summary_json.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    summary_md.write_text(
        "\n".join(
            [
                "# 阶段演示工作流摘要",
                "",
                f"- 项目编号：{summary['project_code']}",
                f"- 项目名称：{summary['project_name']}",
                f"- 项目目录：{summary['project_root']}",
                f"- 方案编号：{summary['scheme_code']}",
                f"- 工艺卡：{summary['document_card_path']}",
                f"- 工艺卡 Markdown：{summary['document_markdown_path']}",
                f"- 质检/缺陷预防清单：{summary['checklist_path']}",
                f"- 辅助建议数：{summary['suggestion_count']}",
                f"- 已审核建议 ID：{summary['approved_card_id'] or '-'}",
                f"- 待审核建议数：{summary['pending_review_count']}",
                f"- 成果包目录：{summary['export_bundle_dir']}",
                f"- 成果包 ZIP：{summary['export_zip_path']}",
                "",
                "## 成果包文件",
                *[f"- {item}" for item in summary["exported_files"]],
                "",
            ]
        ),
        encoding="utf-8",
    )

    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
