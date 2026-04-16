from __future__ import annotations

from dataclasses import dataclass
from math import cos, radians, sin
from pathlib import Path
import sys

import comtypes.client

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


SLDWORKS_TLB = r"E:\Program Files\SOLIDWORKS Corp\SOLIDWORKS\sldworks.tlb"
PART_TEMPLATE = r"C:\ProgramData\SOLIDWORKS\SOLIDWORKS 2024\templates\Part.PRTDOT"


@dataclass(slots=True)
class KCoverParameters:
    outer_width_mm: float = 176.0
    outer_height_mm: float = 176.0
    thickness_mm: float = 53.0
    center_hole_dia_mm: float = 20.0
    inner_hole_dia_mm: float = 42.0
    outer_hole_dia_mm: float = 9.0
    inner_bolt_hole_dia_mm: float = 6.6
    outer_hole_offset_mm: float = 78.0
    outer_bolt_circle_radius_mm: float = 72.0
    inner_bolt_circle_radius_mm: float = 32.0
    front_pocket_dia_mm: float = 140.0
    front_pocket_depth_mm: float = 3.5


def mm(value_mm: float) -> float:
    return value_mm / 1000.0


def main() -> None:
    comtypes.client.GetModule(SLDWORKS_TLB)
    from comtypes.gen import SldWorks

    output_dir = Path(r"E:\zhuzaochuangxin\generated_models\K_汽油机端盖_YL112")
    output_dir.mkdir(parents=True, exist_ok=True)

    sldprt_path = output_dir / "K_汽油机端盖_YL112_v1_initial.SLDPRT"
    step_path = output_dir / "K_汽油机端盖_YL112_v1_initial.step"

    params = KCoverParameters()
    sw = comtypes.client.CreateObject("SldWorks.Application", interface=SldWorks.ISldWorks)
    sw.Visible = False
    sw.NewDocument(PART_TEMPLATE, 0, 0.0, 0.0)
    model = sw.IActiveDoc2

    _create_base_block(model, params)
    _create_front_pocket(model, params)
    _create_center_hole(model, params)
    _create_outer_holes(model, params)
    _create_outer_bolt_circle_holes(model, params)
    _create_inner_bolt_circle_holes(model, params)

    model.SaveAs3(str(sldprt_path), 0, 0)
    model.SaveAs3(str(step_path), 0, 0)

    print(f"Generated SLDPRT: {sldprt_path}")
    print(f"Generated STEP:   {step_path}")


def _create_base_block(model, params: KCoverParameters) -> None:
    model.ClearSelection2(True)
    model.SelectByName(0, "前视基准面")
    model.InsertSketch2(True)
    model.SketchRectangle(
        -mm(params.outer_width_mm / 2),
        -mm(params.outer_height_mm / 2),
        0.0,
        mm(params.outer_width_mm / 2),
        mm(params.outer_height_mm / 2),
        0.0,
        True,
    )
    model.InsertSketch2(True)
    model.ClearSelection2(True)
    model.FeatureBoss2(
        True,
        False,
        False,
        0,
        0,
        mm(params.thickness_mm),
        0.0,
        False,
        False,
        False,
        False,
        0.0,
        0.0,
        False,
        False,
        False,
        False,
    )


def _create_front_pocket(model, params: KCoverParameters) -> None:
    model.ClearSelection2(True)
    model.SelectByName(0, "前视基准面")
    model.InsertSketch2(True)
    model.SketchManager.CreateCircleByRadius(0.0, 0.0, 0.0, mm(params.front_pocket_dia_mm / 2))
    model.InsertSketch2(True)
    model.ClearSelection2(True)
    model.FeatureCut2(
        True,
        False,
        False,
        0,
        0,
        mm(params.front_pocket_depth_mm),
        0.0,
        False,
        False,
        False,
        False,
        0.0,
        0.0,
        False,
        False,
        0,
    )


def _create_center_hole(model, params: KCoverParameters) -> None:
    model.ClearSelection2(True)
    model.SelectByName(0, "前视基准面")
    model.InsertSketch2(True)
    model.SketchManager.CreateCircleByRadius(0.0, 0.0, 0.0, mm(params.center_hole_dia_mm / 2))
    model.InsertSketch2(True)
    model.ClearSelection2(True)
    model.FeatureCut2(
        True,
        False,
        False,
        0,
        0,
        mm(params.thickness_mm),
        0.0,
        False,
        False,
        False,
        False,
        0.0,
        0.0,
        False,
        False,
        0,
    )


def _create_outer_holes(model, params: KCoverParameters) -> None:
    model.ClearSelection2(True)
    model.SelectByName(0, "前视基准面")
    model.InsertSketch2(True)
    radius = mm(params.outer_hole_dia_mm / 2)
    offset = mm(params.outer_hole_offset_mm)
    for x_sign in (-1, 1):
        for y_sign in (-1, 1):
            model.SketchManager.CreateCircleByRadius(x_sign * offset, y_sign * offset, 0.0, radius)
    model.InsertSketch2(True)
    model.ClearSelection2(True)
    model.FeatureCut2(
        True,
        False,
        False,
        0,
        0,
        mm(params.thickness_mm),
        0.0,
        False,
        False,
        False,
        False,
        0.0,
        0.0,
        False,
        False,
        0,
    )


def _create_outer_bolt_circle_holes(model, params: KCoverParameters) -> None:
    model.ClearSelection2(True)
    model.SelectByName(0, "前视基准面")
    model.InsertSketch2(True)
    radius = mm(params.outer_hole_dia_mm / 2)
    bolt_radius = mm(params.outer_bolt_circle_radius_mm)
    for angle_deg in (90.0, 210.0, 330.0):
        angle = radians(angle_deg)
        x = bolt_radius * cos(angle)
        y = bolt_radius * sin(angle)
        model.SketchManager.CreateCircleByRadius(x, y, 0.0, radius)
    model.InsertSketch2(True)
    model.ClearSelection2(True)
    model.FeatureCut2(
        True,
        False,
        False,
        0,
        0,
        mm(params.thickness_mm),
        0.0,
        False,
        False,
        False,
        False,
        0.0,
        0.0,
        False,
        False,
        0,
    )


def _create_inner_bolt_circle_holes(model, params: KCoverParameters) -> None:
    model.ClearSelection2(True)
    model.SelectByName(0, "前视基准面")
    model.InsertSketch2(True)
    radius = mm(params.inner_bolt_hole_dia_mm / 2)
    bolt_radius = mm(params.inner_bolt_circle_radius_mm)
    for angle_deg in (45.0, 135.0, 225.0, 315.0):
        angle = radians(angle_deg)
        x = bolt_radius * cos(angle)
        y = bolt_radius * sin(angle)
        model.SketchManager.CreateCircleByRadius(x, y, 0.0, radius)
    model.InsertSketch2(True)
    model.ClearSelection2(True)
    model.FeatureCut2(
        True,
        False,
        False,
        0,
        0,
        mm(params.thickness_mm),
        0.0,
        False,
        False,
        False,
        False,
        0.0,
        0.0,
        False,
        False,
        0,
    )


if __name__ == "__main__":
    main()
