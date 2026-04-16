from __future__ import annotations

import math
import sys
from dataclasses import dataclass
from pathlib import Path

import comtypes.client

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

SLDWORKS_TLB = r"E:\Program Files\SOLIDWORKS Corp\SOLIDWORKS\sldworks.tlb"
PART_TEMPLATE = r"C:\ProgramData\SOLIDWORKS\SOLIDWORKS 2024\templates\Part.PRTDOT"


@dataclass(slots=True)
class Params:
    thickness_mm: float = 53.0
    front_pocket_dia_mm: float = 140.0
    front_pocket_depth_mm: float = 3.5
    front_counterbore_dia_mm: float = 92.0
    front_counterbore_depth_mm: float = 6.0
    center_bore_dia_mm: float = 42.0
    center_bore_depth_mm: float = 15.0
    through_hole_dia_mm: float = 20.0


def mm(value_mm: float) -> float:
    return value_mm / 1000.0


def _front_outline_points() -> list[tuple[float, float]]:
    """
    Build a stable closed outer contour from the front-view key dimensions.
    This is intentionally coarser than direct image tracing but generates a valid solid.
    """
    return [
        (-57.5, -88.0),
        (57.5, -88.0),
        (72.0, -80.0),
        (82.0, -70.0),
        (88.0, -57.0),
        (88.0, -20.0),
        (88.0, 20.0),
        (88.0, 57.0),
        (82.0, 70.0),
        (72.0, 80.0),
        (65.0, 88.0),
        (0.0, 88.0),
        (-65.0, 88.0),
        (-72.0, 80.0),
        (-82.0, 70.0),
        (-88.0, 57.0),
        (-88.0, 20.0),
        (-88.0, -20.0),
        (-88.0, -57.0),
        (-82.0, -70.0),
        (-72.0, -80.0),
    ]


def _select_front_plane(model) -> None:
    model.ClearSelection2(True)
    model.SelectByName(0, "前视基准面")


def _open_sketch(model) -> None:
    _select_front_plane(model)
    model.InsertSketch2(True)


def _close_sketch(model) -> None:
    model.InsertSketch2(True)


def _extrude_sketch(model, depth_mm: float, start_offset_mm: float = 0.0):
    feature_manager = model.FeatureManager
    start_condition = 3 if start_offset_mm > 0.0 else 0
    feature = feature_manager.FeatureExtrusion2(
        True,
        False,
        False,
        0,
        0,
        mm(depth_mm),
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
        True,
        True,
        True,
        start_condition,
        mm(start_offset_mm),
        False,
    )
    if feature is None:
        raise RuntimeError(f"Extrusion failed for depth={depth_mm}, start_offset={start_offset_mm}.")
    return feature


def _sketch_circle_ring(model, outer_dia_mm: float, inner_dia_mm: float) -> None:
    _open_sketch(model)
    model.SketchManager.CreateCircleByRadius(0.0, 0.0, 0.0, mm(outer_dia_mm / 2))
    model.SketchManager.CreateCircleByRadius(0.0, 0.0, 0.0, mm(inner_dia_mm / 2))
    _close_sketch(model)


def main() -> None:
    p = Params()
    output_dir = Path(r"E:\zhuzaochuangxin\generated_models\K_汽油机端盖_YL112")
    output_dir.mkdir(parents=True, exist_ok=True)
    sldprt_path = output_dir / "K_汽油机端盖_YL112_v3_outline_fit.SLDPRT"
    step_path = output_dir / "K_汽油机端盖_YL112_v3_outline_fit.step"

    comtypes.client.GetModule(SLDWORKS_TLB)
    from comtypes.gen import SldWorks

    sw = comtypes.client.GetActiveObject("SldWorks.Application", interface=SldWorks.ISldWorks)
    sw.Visible = True
    sw.NewDocument(PART_TEMPLATE, 0, 0.0, 0.0)
    model = sw.IActiveDoc2

    _open_sketch(model)
    outline_points_mm = _front_outline_points()
    for start, end in zip(outline_points_mm, outline_points_mm[1:] + outline_points_mm[:1]):
        model.SketchManager.CreateLine(
            mm(start[0]),
            mm(start[1]),
            0.0,
            mm(end[0]),
            mm(end[1]),
            0.0,
        )
    model.SketchManager.CreateCircleByRadius(0.0, 0.0, 0.0, mm(p.front_pocket_dia_mm / 2))
    _close_sketch(model)
    _extrude_sketch(model, p.thickness_mm, 0.0)

    _sketch_circle_ring(model, p.front_pocket_dia_mm, p.front_counterbore_dia_mm)
    _extrude_sketch(
        model,
        p.thickness_mm - p.front_pocket_depth_mm,
        p.front_pocket_depth_mm,
    )

    _sketch_circle_ring(model, p.front_counterbore_dia_mm, p.center_bore_dia_mm)
    _extrude_sketch(
        model,
        p.thickness_mm - p.front_counterbore_depth_mm,
        p.front_counterbore_depth_mm,
    )

    _sketch_circle_ring(model, p.center_bore_dia_mm, p.through_hole_dia_mm)
    _extrude_sketch(
        model,
        p.thickness_mm - p.center_bore_depth_mm,
        p.center_bore_depth_mm,
    )

    model.SaveAs3(str(sldprt_path), 0, 0)
    model.SaveAs3(str(step_path), 0, 0)

    print(f"Generated SLDPRT: {sldprt_path}")
    print(f"Generated STEP:   {step_path}")


if __name__ == "__main__":
    main()
