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
class RefinedParams:
    width_mm: float = 176.0
    height_mm: float = 176.0
    thickness_mm: float = 53.0
    front_pocket_dia_mm: float = 140.0
    front_pocket_depth_mm: float = 3.5
    front_counterbore_dia_mm: float = 92.0
    front_counterbore_depth_mm: float = 6.0
    center_bore_dia_mm: float = 42.0
    center_bore_depth_mm: float = 15.0
    through_hole_dia_mm: float = 20.0
    corner_hole_dia_mm: float = 9.0
    corner_hole_center_offset_mm: float = 78.0
    outer_ring_hole_dia_mm: float = 9.0
    outer_ring_hole_radius_mm: float = 77.0
    inner_bolt_hole_dia_mm: float = 6.6
    inner_bolt_circle_radius_mm: float = 46.0


def mm(value_mm: float) -> float:
    return value_mm / 1000.0


def main() -> None:
    comtypes.client.GetModule(SLDWORKS_TLB)
    from comtypes.gen import SldWorks

    output_dir = Path(r"E:\zhuzaochuangxin\generated_models\K_汽油机端盖_YL112")
    output_dir.mkdir(parents=True, exist_ok=True)

    sldprt_path = output_dir / "K_汽油机端盖_YL112_v2_refined.SLDPRT"
    step_path = output_dir / "K_汽油机端盖_YL112_v2_refined.step"

    p = RefinedParams()
    sw = comtypes.client.CreateObject("SldWorks.Application", interface=SldWorks.ISldWorks)
    sw.Visible = False
    sw.NewDocument(PART_TEMPLATE, 0, 0.0, 0.0)
    model = sw.IActiveDoc2

    _sketch_on_front_plane(model)
    model.SketchRectangle(
        -mm(p.width_mm / 2),
        -mm(p.height_mm / 2),
        0.0,
        mm(p.width_mm / 2),
        mm(p.height_mm / 2),
        0.0,
        True,
    )
    _close_sketch(model)
    model.FeatureBoss2(
        True, False, False, 0, 0,
        mm(p.thickness_mm), 0.0,
        False, False, False, False,
        0.0, 0.0,
        False, False, False, False
    )

    _circular_cut(model, p.front_pocket_dia_mm, p.front_pocket_depth_mm)
    _circular_cut(model, p.front_counterbore_dia_mm, p.front_counterbore_depth_mm)
    _circular_cut(model, p.center_bore_dia_mm, p.center_bore_depth_mm)
    _circular_cut(model, p.through_hole_dia_mm, p.thickness_mm)

    _multi_hole_cut(
        model,
        hole_dia_mm=p.corner_hole_dia_mm,
        centers_mm=[
            ( p.corner_hole_center_offset_mm,  p.corner_hole_center_offset_mm),
            (-p.corner_hole_center_offset_mm,  p.corner_hole_center_offset_mm),
            ( p.corner_hole_center_offset_mm, -p.corner_hole_center_offset_mm),
            (-p.corner_hole_center_offset_mm, -p.corner_hole_center_offset_mm),
        ],
        depth_mm=p.thickness_mm,
    )

    _polar_hole_cut(
        model,
        hole_dia_mm=p.outer_ring_hole_dia_mm,
        radius_mm=p.outer_ring_hole_radius_mm,
        angles_deg=(90.0, 210.0, 330.0),
        depth_mm=p.thickness_mm,
    )

    _polar_hole_cut(
        model,
        hole_dia_mm=p.inner_bolt_hole_dia_mm,
        radius_mm=p.inner_bolt_circle_radius_mm,
        angles_deg=(45.0, 135.0, 225.0, 315.0),
        depth_mm=p.thickness_mm,
    )

    model.SaveAs3(str(sldprt_path), 0, 0)
    model.SaveAs3(str(step_path), 0, 0)

    print(f"Generated SLDPRT: {sldprt_path}")
    print(f"Generated STEP:   {step_path}")


def _sketch_on_front_plane(model) -> None:
    model.ClearSelection2(True)
    model.SelectByName(0, "前视基准面")
    model.InsertSketch2(True)


def _close_sketch(model) -> None:
    model.InsertSketch2(True)
    model.ClearSelection2(True)


def _circular_cut(model, diameter_mm: float, depth_mm: float) -> None:
    _sketch_on_front_plane(model)
    model.SketchManager.CreateCircleByRadius(0.0, 0.0, 0.0, mm(diameter_mm / 2))
    _close_sketch(model)
    model.FeatureCut2(
        True, False, False, 0, 0,
        mm(depth_mm), 0.0,
        False, False, False, False,
        0.0, 0.0,
        False, False, 0
    )


def _multi_hole_cut(model, hole_dia_mm: float, centers_mm: list[tuple[float, float]], depth_mm: float) -> None:
    _sketch_on_front_plane(model)
    radius = mm(hole_dia_mm / 2)
    for x_mm, y_mm in centers_mm:
        model.SketchManager.CreateCircleByRadius(mm(x_mm), mm(y_mm), 0.0, radius)
    _close_sketch(model)
    model.FeatureCut2(
        True, False, False, 0, 0,
        mm(depth_mm), 0.0,
        False, False, False, False,
        0.0, 0.0,
        False, False, 0
    )


def _polar_hole_cut(model, hole_dia_mm: float, radius_mm: float, angles_deg: tuple[float, ...], depth_mm: float) -> None:
    centers = []
    for angle_deg in angles_deg:
        angle = radians(angle_deg)
        centers.append((radius_mm * cos(angle), radius_mm * sin(angle)))
    _multi_hole_cut(model, hole_dia_mm, centers, depth_mm)


if __name__ == "__main__":
    main()
