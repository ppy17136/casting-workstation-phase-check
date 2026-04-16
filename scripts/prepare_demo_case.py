from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
import json
from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.core.config import AppPaths
from app.core.db.initializer import initialize_database
from app.core.repositories.cad_repository import CadRepository
from app.core.repositories.material_repository import MaterialRepository
from app.core.repositories.parameter_repository import ParameterRepository
from app.core.repositories.part_repository import PartRepository
from app.core.repositories.project_repository import ProjectRepository
from app.core.repositories.scheme_repository import SchemeRepository
from app.core.repositories.settings_repository import SettingsRepository
from app.core.repositories.simulation_repository import SimulationRepository
from app.core.services.calculation_service import CalculationService


@dataclass(slots=True)
class DemoCaseInfo:
    project_id: str
    project_code: str
    project_name: str
    project_root: str
    part_id: str
    scheme_id: str
    scheme_code: str
    simulation_job_id: str
    simulation_job_code: str


def seed_materials(material_repository: MaterialRepository) -> None:
    material_repository.upsert_material(
        material_code="YL112",
        material_name="YL112",
        category="铝合金铸造",
        density=2.68,
        liquidus_temp=615.0,
        solidus_temp=555.0,
        pouring_temp_min=690.0,
        pouring_temp_max=730.0,
        shrinkage_ratio=0.013,
        standard_ref="GB/T 1173-2013",
    )
    material_repository.upsert_material(
        material_code="HT250",
        material_name="HT250",
        category="灰铸铁",
        density=7.20,
        liquidus_temp=1200.0,
        solidus_temp=1140.0,
        pouring_temp_min=1360.0,
        pouring_temp_max=1420.0,
        shrinkage_ratio=0.010,
        standard_ref="GB/T 9439-2010",
    )
    material_repository.upsert_material(
        material_code="ZL101A",
        material_name="ZL101A",
        category="铝硅镁合金",
        density=2.67,
        liquidus_temp=610.0,
        solidus_temp=555.0,
        pouring_temp_min=700.0,
        pouring_temp_max=740.0,
        shrinkage_ratio=0.012,
        standard_ref="GB/T 1173-2013",
    )


def seed_settings(settings_repository: SettingsRepository, paths: AppPaths) -> None:
    settings_repository.set_setting(
        setting_key="llm.mode",
        setting_value="disabled",
        setting_group="llm",
    )
    settings_repository.set_setting(
        setting_key="llm.base_url",
        setting_value="",
        setting_group="llm",
    )
    settings_repository.set_setting(
        setting_key="llm.model",
        setting_value="casting-demo-assistant",
        setting_group="llm",
    )
    settings_repository.set_setting(
        setting_key="llm.api_key",
        setting_value="",
        setting_group="llm",
    )
    settings_repository.set_setting(
        setting_key="integration.solidworks_bridge_path",
        setting_value=str(ROOT_DIR / "dist" / "SolidWorksBridge" / "SolidWorksBridge.exe"),
        setting_group="integration",
    )
    settings_repository.set_setting(
        setting_key="integration.procast_install_dir",
        setting_value=r"E:\Program Files\ESI Group",
        setting_group="integration",
    )
    settings_repository.set_setting(
        setting_key="integration.default_project_root",
        setting_value=str(paths.projects_dir),
        setting_group="integration",
    )


def main() -> None:
    paths = AppPaths.default()
    paths.ensure_directories()
    initialize_database(paths.database_path)

    project_repository = ProjectRepository(paths.database_path)
    part_repository = PartRepository(paths.database_path)
    scheme_repository = SchemeRepository(paths.database_path)
    parameter_repository = ParameterRepository(paths.database_path)
    cad_repository = CadRepository(paths.database_path)
    simulation_repository = SimulationRepository(paths.database_path)
    material_repository = MaterialRepository(paths.database_path)
    settings_repository = SettingsRepository(paths.database_path)
    calculation_service = CalculationService()

    seed_materials(material_repository)
    seed_settings(settings_repository, paths)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    project_code = f"DEMO-RC-{timestamp}"
    project_name = "圆盖铝合金件一体化阶段演示"
    project_root = paths.projects_dir / project_code
    cad_dir = project_root / "cad"
    sim_input_dir = project_root / "simulation" / "SIM-BASE" / "input"
    sim_output_dir = project_root / "simulation" / "SIM-BASE" / "output"
    for directory in (project_root, cad_dir, sim_input_dir, sim_output_dir):
        directory.mkdir(parents=True, exist_ok=True)

    project_id = project_repository.create_project(
        project_code=project_code,
        project_name=project_name,
        owner="demo",
        root_dir=str(project_root),
        project_type="创新训练项目演示",
        casting_method="砂型铸造",
        status="演示中",
    )
    part_id = part_repository.create_default_part(project_id, "圆盖铝合金件")
    part_repository.update_part(
        part_id,
        part_name="圆盖铝合金件",
        part_no="ROUND-COVER-01",
        drawing_no="ROUND-COVER-YL112",
        material_name="YL112",
        net_weight=2.85,
        blank_weight=5.65,
        length_mm=176.0,
        width_mm=176.0,
        height_mm=53.0,
        max_wall_thickness=24.0,
        min_wall_thickness=6.0,
        production_qty=50,
        quality_grade="CT8 / Ra12.5",
        heat_treatment="T5",
        surface_requirement="非加工面喷砂，分型面打磨去毛刺。",
        internal_quality_requirement="关键热节区域不得出现缩孔缩松，X 射线抽检 II 级。",
    )

    scheme_id = scheme_repository.create_scheme(
        project_id=project_id,
        part_id=part_id,
        scheme_code="A",
        scheme_name="圆盖基准工艺方案",
        version_no="V1",
    )
    scheme_repository.update_scheme(
        scheme_id,
        scheme_name="圆盖基准工艺方案",
        version_no="V1",
        scheme_status="待评审",
        mold_type="砂型 + 砂芯",
        parting_method="水平分型",
        pouring_position="法兰面朝上",
        gating_type="底注式",
        notes=(
            "用于阶段检查演示，覆盖工艺计算、仿真结果管理、工艺卡输出与质检清单。"
            " 当前几何示例仍复用现有样例模型文件，仅作为流程演示载体。"
        ),
    )

    part = part_repository.get_part(part_id)
    scheme = scheme_repository.get_scheme(scheme_id)
    assert part is not None
    assert scheme is not None

    parameters = calculation_service.calculate(part, scheme)
    parameter_repository.replace_for_scheme(
        scheme_id,
        [
            {
                "param_group": item.param_group,
                "param_code": item.param_code,
                "param_name": item.param_name,
                "param_value": item.param_value,
                "param_unit": item.param_unit,
                "value_type": item.value_type,
                "source_type": item.source_type,
                "calc_formula": item.calc_formula,
            }
            for item in parameters
        ],
    )

    source_sldprt = Path(
        r"E:\zhuzaochuangxin\generated_models\K_汽油机端盖_YL112\K_汽油机端盖_YL112_v4_dim_refine_r3_core.SLDPRT"
    )
    source_step = Path(
        r"E:\zhuzaochuangxin\generated_models\K_汽油机端盖_YL112\K_汽油机端盖_YL112_v4_dim_refine_r3_core.step"
    )
    cad_model_path = cad_dir / "round_cover_demo_core.SLDPRT"
    cad_export_path = cad_dir / "round_cover_demo_core.step"
    if source_sldprt.exists():
        cad_model_path.write_bytes(source_sldprt.read_bytes())
    if source_step.exists():
        cad_export_path.write_bytes(source_step.read_bytes())

    cad_model_id = cad_repository.upsert_model(
        scheme_id=scheme_id,
        cad_system="SolidWorks",
        file_type="SLDPRT",
        file_path=str(cad_model_path),
    )
    cad_repository.create_export_record(
        cad_model_id=cad_model_id,
        export_type="STEP",
        export_path=str(cad_export_path),
        export_status="success",
        bridge_version="demo",
    )

    simulation_job_id = simulation_repository.create_job(
        scheme_id=scheme_id,
        job_code="SIM-BASE",
        job_name="圆盖基准充型凝固仿真",
        solver="ProCAST",
        template_name="demo_template",
        input_dir=str(sim_input_dir),
        output_dir=str(sim_output_dir),
        job_status="completed",
        run_mode="manual",
        operator="demo",
    )
    simulation_repository.update_job(
        simulation_job_id,
        job_name="圆盖基准充型凝固仿真",
        solver="ProCAST",
        template_name="demo_template",
        input_dir=str(sim_input_dir),
        output_dir=str(sim_output_dir),
        job_status="completed",
        run_mode="manual",
        operator="demo",
        submit_time="2026-04-16 18:45",
        finish_time="2026-04-16 18:58",
    )

    shrinkage_path = sim_output_dir / "shrinkage_result.txt"
    temperature_path = sim_output_dir / "temperature_result.txt"
    shrinkage_path.write_text(
        "圆盖法兰与厚大截面过渡区存在缩孔缩松风险，建议优先优化补缩路径与局部冷却条件。",
        encoding="utf-8",
    )
    temperature_path.write_text(
        "充型末端与筋板连接区温降较慢，需复核浇注时间、阻流面积与顺序凝固设计。",
        encoding="utf-8",
    )
    simulation_repository.create_result(
        job_id=simulation_job_id,
        result_type="shrinkage",
        result_name="圆盖缩孔缩松基准结果",
        file_path=str(shrinkage_path),
        summary="识别到缩孔缩松高风险区域，位于法兰与厚大截面交界处。",
        compare_group="baseline",
    )
    simulation_repository.create_result(
        job_id=simulation_job_id,
        result_type="temperature",
        result_name="圆盖温度场基准结果",
        file_path=str(temperature_path),
        summary="局部温降偏慢，需要复核浇注时间与阻流截面积。",
        compare_group="baseline",
    )

    artifact_dir = ROOT_DIR / "artifacts"
    artifact_dir.mkdir(parents=True, exist_ok=True)
    info = DemoCaseInfo(
        project_id=project_id,
        project_code=project_code,
        project_name=project_name,
        project_root=str(project_root),
        part_id=part_id,
        scheme_id=scheme_id,
        scheme_code="A",
        simulation_job_id=simulation_job_id,
        simulation_job_code="SIM-BASE",
    )
    info_path = artifact_dir / "demo_case.json"
    info_path.write_text(json.dumps(asdict(info), ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Demo case prepared: {info_path}")
    print(json.dumps(asdict(info), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
