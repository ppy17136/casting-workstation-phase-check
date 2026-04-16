from __future__ import annotations

import math
import sys
from dataclasses import dataclass
from pathlib import Path

import comtypes.client
from comtypes.gen import SwConst

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

SLDWORKS_TLB = r"E:\Program Files\SOLIDWORKS Corp\SOLIDWORKS\sldworks.tlb"
PART_TEMPLATE = r"C:\ProgramData\SOLIDWORKS\SOLIDWORKS 2024\templates\Part.PRTDOT"


@dataclass(slots=True)
class Params:
    total_thickness_mm: float = 53.0

    outer_reference_dia_mm: float = 176.0
    top_flat_width_mm: float = 72.5
    bottom_flat_width_mm: float = 115.0
    side_height_ref_mm: float = 57.0
    shoulder_width_mm: float = 57.5

    front_pocket_dia_mm: float = 140.0
    front_pocket_depth_mm: float = 3.5
    center_step_dia_mm: float = 92.0
    center_step_depth_mm: float = 6.0
    center_bore_dia_mm: float = 42.0
    center_bore_depth_mm: float = 15.0
    center_through_hole_dia_mm: float = 20.0

    aa_outer_boss_dia_mm: float = 85.0
    aa_middle_boss_dia_mm: float = 75.0
    aa_inner_boss_dia_mm: float = 35.0
    aa_outer_boss_depth_mm: float = 5.5
    aa_middle_boss_depth_mm: float = 12.0
    aa_inner_boss_depth_mm: float = 15.0
    aa_back_cavity_dia_mm: float = 154.0
    aa_back_cavity_inner_dia_mm: float = 54.0
    aa_back_cavity_depth_mm: float = 37.0

    outer_hole_dia_mm: float = 9.0
    outer_hole_radius_mm: float = 77.0

    corner_hole_dia_mm: float = 9.0
    corner_hole_center_offset_x_mm: float = 78.0
    corner_hole_center_offset_y_mm: float = 80.0
    corner_pad_width_mm: float = 20.0
    corner_pad_height_mm: float = 16.0


def mm(value_mm: float) -> float:
    return value_mm / 1000.0


def _get_solidworks():
    from comtypes.gen import SldWorks

    try:
        sw = comtypes.client.GetActiveObject(
            "SldWorks.Application",
            interface=SldWorks.ISldWorks,
        )
    except OSError:
        sw = comtypes.client.CreateObject(
            "SldWorks.Application",
            interface=SldWorks.ISldWorks,
        )
    try:
        _ = sw.RevisionNumber()
    except Exception:
        sw = comtypes.client.CreateObject(
            "SldWorks.Application",
            interface=SldWorks.ISldWorks,
        )
    sw.Visible = True
    return sw


def _close_doc_safely(sw, doc) -> None:
    if doc is None:
        return
    try:
        title = doc.GetTitle() if callable(doc.GetTitle) else doc.GetTitle
    except Exception:
        title = None
    if title:
        try:
            sw.CloseDoc(title)
        except Exception:
            pass


def _visible_solid_bodies(model) -> list:
    from comtypes.gen import SldWorks

    part = model.QueryInterface(SldWorks.IPartDoc)
    enum = part.EnumBodies3(0, True)
    bodies = []
    while True:
        result = enum.Next(1)
        if result[1] == 0:
            break
        bodies.append(result[0])
    return bodies


def _select_front_plane(model) -> None:
    model.ClearSelection2(True)
    model.SelectByName(0, "前视基准面")


def _open_sketch(model) -> None:
    _select_front_plane(model)
    model.InsertSketch2(True)


def _close_sketch(model) -> None:
    model.InsertSketch2(True)


def _open_outer_front_face_sketch(model) -> None:
    model.ClearSelection2(True)
    extension = model.Extension
    candidates = [
        (0.080, 0.000, -0.020),
        (-0.080, 0.000, -0.020),
        (0.000, 0.080, -0.020),
        (0.000, -0.080, -0.020),
    ]
    selected = False
    for x_m, y_m, z_m in candidates:
        selected = extension.SelectByRay(x_m, y_m, z_m, 0.0, 0.0, 1.0, 0.02, 2, False, 0, 0)
        if selected:
            break
    if not selected:
        raise RuntimeError("Failed to select outer front face ring region.")
    model.InsertSketch2(True)


def _open_outer_back_face_sketch(model) -> None:
    model.ClearSelection2(True)
    extension = model.Extension
    candidates = [
        (0.070, 0.000, 0.090),
        (-0.070, 0.000, 0.090),
        (0.000, 0.070, 0.090),
        (0.000, -0.070, 0.090),
    ]
    selected = False
    for x_m, y_m, z_m in candidates:
        selected = extension.SelectByRay(x_m, y_m, z_m, 0.0, 0.0, -1.0, 0.02, 2, False, 0, 0)
        if selected:
            break
    if not selected:
        raise RuntimeError("Failed to select outer back face ring region.")
    model.InsertSketch2(True)


def _extrude_current_sketch(
    model,
    depth_mm: float,
    start_offset_mm: float = 0.0,
    reverse_direction: bool = False,
    merge_result: bool = True,
):
    feature_manager = model.FeatureManager
    start_condition = 3 if start_offset_mm > 0.0 else 0
    feature = feature_manager.FeatureExtrusion2(
        True,
        False,
        reverse_direction,
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
        merge_result,
        True,
        True,
        start_condition,
        mm(start_offset_mm),
        False,
    )
    if feature is None:
        raise RuntimeError(
            f"Extrusion failed: depth={depth_mm}, start_offset={start_offset_mm}, reverse={reverse_direction}, merge={merge_result}"
        )
    return feature


def _subtract_tool_bodies(model) -> None:
    bodies = _visible_solid_bodies(model)
    if len(bodies) < 2:
        raise RuntimeError(f"Subtract requires at least 2 bodies, got {len(bodies)}")
    main_body = bodies[0]
    tool_bodies = bodies[1:]
    feature = model.FeatureManager.InsertCombineFeature(
        SwConst.swCombineBodiesOperationSubtract,
        main_body,
        tool_bodies,
    )
    if feature is None:
        raise RuntimeError("Combine subtract failed for outer tool bodies")


def _cut_current_sketch(model, depth_mm: float):
    feature = model.FeatureCut4(
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
        0,
        False,
    )
    if feature == 0:
        raise RuntimeError(f"Cut failed: depth={depth_mm}")
    return feature


def _cut_current_sketch_with_start_offset(model, depth_mm: float, start_offset_mm: float):
    feature_manager = model.FeatureManager
    feature = feature_manager.FeatureCut4(
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
        False,
        False,
        False,
        False,
        3,
        mm(start_offset_mm),
        False,
        True,
    )
    if feature is None:
        raise RuntimeError(
            f"Offset cut failed: depth={depth_mm}, start_offset={start_offset_mm}"
        )
    return feature


def _outer_profile_points(p: Params) -> list[tuple[float, float]]:
    """
    Simplified dimension-driven front profile.
    Points come from front-view width/height annotations rather than image tracing.
    """
    half_total = p.outer_reference_dia_mm / 2
    half_top_flat = p.top_flat_width_mm / 2
    half_bottom_flat = p.bottom_flat_width_mm / 2
    side_y = p.side_height_ref_mm

    return [
        (-half_bottom_flat, -half_total),
        (half_bottom_flat, -half_total),
        (72.0, -82.0),
        (82.0, -72.0),
        (half_total, -side_y),
        (half_total, side_y),
        (82.0, 72.0),
        (72.0, 82.0),
        (half_top_flat, half_total),
        (-half_top_flat, half_total),
        (-72.0, 82.0),
        (-82.0, 72.0),
        (-half_total, side_y),
        (-half_total, -side_y),
        (-82.0, -72.0),
        (-72.0, -82.0),
    ]


def _sketch_outer_profile_with_circles(model, p: Params, circle_dias_mm: list[float]) -> None:
    _open_sketch(model)

    points = _outer_profile_points(p)
    for start, end in zip(points, points[1:] + points[:1]):
        model.SketchManager.CreateLine(
            mm(start[0]),
            mm(start[1]),
            0.0,
            mm(end[0]),
            mm(end[1]),
            0.0,
        )

    for dia_mm in circle_dias_mm:
        model.SketchManager.CreateCircleByRadius(0.0, 0.0, 0.0, mm(dia_mm / 2))

    _close_sketch(model)


def _sketch_circle_ring(model, outer_dia_mm: float, inner_dia_mm: float) -> None:
    _open_sketch(model)
    model.SketchManager.CreateCircleByRadius(0.0, 0.0, 0.0, mm(outer_dia_mm / 2))
    model.SketchManager.CreateCircleByRadius(0.0, 0.0, 0.0, mm(inner_dia_mm / 2))
    _close_sketch(model)


def _sketch_front_face_ring(model, outer_dia_mm: float, inner_dia_mm: float) -> None:
    _open_outer_front_face_sketch(model)
    model.SketchManager.CreateCircleByRadius(0.0, 0.0, 0.0, mm(outer_dia_mm / 2))
    model.SketchManager.CreateCircleByRadius(0.0, 0.0, 0.0, mm(inner_dia_mm / 2))
    _close_sketch(model)


def _sketch_back_face_ring(model, outer_dia_mm: float, inner_dia_mm: float) -> None:
    _open_outer_back_face_sketch(model)
    model.SketchManager.CreateCircleByRadius(0.0, 0.0, 0.0, mm(outer_dia_mm / 2))
    model.SketchManager.CreateCircleByRadius(0.0, 0.0, 0.0, mm(inner_dia_mm / 2))
    _close_sketch(model)


def _sketch_corner_pads_with_holes(model, p: Params) -> None:
    _open_sketch(model)

    pad_half_x = p.corner_pad_width_mm / 2
    pad_half_y = p.corner_pad_height_mm / 2
    hole_radius = p.corner_hole_dia_mm / 2
    centers = [
        (p.corner_hole_center_offset_x_mm, p.corner_hole_center_offset_y_mm),
        (-p.corner_hole_center_offset_x_mm, p.corner_hole_center_offset_y_mm),
        (p.corner_hole_center_offset_x_mm, -p.corner_hole_center_offset_y_mm),
        (-p.corner_hole_center_offset_x_mm, -p.corner_hole_center_offset_y_mm),
    ]

    for x_mm, y_mm in centers:
        model.SketchRectangle(
            mm(x_mm - pad_half_x),
            mm(y_mm - pad_half_y),
            0.0,
            mm(x_mm + pad_half_x),
            mm(y_mm + pad_half_y),
            0.0,
            True,
        )
        model.SketchManager.CreateCircleByRadius(mm(x_mm), mm(y_mm), 0.0, mm(hole_radius))

    _close_sketch(model)


def _sketch_outer_holes(model, p: Params) -> None:
    _open_sketch(model)

    for angle_deg in (90.0, 210.0, 330.0):
        angle = math.radians(angle_deg)
        model.SketchManager.CreateCircleByRadius(
            mm(p.outer_hole_radius_mm * math.cos(angle)),
            mm(p.outer_hole_radius_mm * math.sin(angle)),
            0.0,
            mm(p.outer_hole_dia_mm / 2),
        )

    _close_sketch(model)


def main() -> None:
    p = Params()
    output_dir = Path(r"E:\zhuzaochuangxin\generated_models\K_汽油机端盖_YL112")
    output_dir.mkdir(parents=True, exist_ok=True)

    sldprt_path = output_dir / "K_汽油机端盖_YL112_v4_dim_refine_r3_core.SLDPRT"
    step_path = output_dir / "K_汽油机端盖_YL112_v4_dim_refine_r3_core.step"

    comtypes.client.GetModule(SLDWORKS_TLB)
    sw = _get_solidworks()
    model = None
    try:
        sw.NewDocument(PART_TEMPLATE, 0, 0.0, 0.0)
        model = sw.IActiveDoc2

        back_floor_mm = p.total_thickness_mm - p.aa_back_cavity_depth_mm

        _sketch_outer_profile_with_circles(model, p, [p.aa_back_cavity_dia_mm])
        _extrude_current_sketch(model, p.total_thickness_mm)

        _sketch_circle_ring(model, p.aa_back_cavity_dia_mm, p.front_pocket_dia_mm)
        _extrude_current_sketch(model, back_floor_mm)

        _sketch_circle_ring(model, p.front_pocket_dia_mm, p.center_step_dia_mm)
        _extrude_current_sketch(model, back_floor_mm - p.front_pocket_depth_mm, p.front_pocket_depth_mm)

        _sketch_circle_ring(model, p.center_step_dia_mm, p.aa_back_cavity_inner_dia_mm)
        _extrude_current_sketch(model, back_floor_mm - p.center_step_depth_mm, p.center_step_depth_mm)

        _sketch_circle_ring(model, p.aa_back_cavity_inner_dia_mm, p.center_bore_dia_mm)
        _extrude_current_sketch(model, p.total_thickness_mm - p.center_step_depth_mm, p.center_step_depth_mm)

        _sketch_circle_ring(model, p.center_bore_dia_mm, p.center_through_hole_dia_mm)
        _extrude_current_sketch(model, p.total_thickness_mm - p.center_bore_depth_mm, p.center_bore_depth_mm)

        _sketch_circle_ring(model, p.aa_outer_boss_dia_mm, p.center_through_hole_dia_mm)
        _extrude_current_sketch(
            model,
            p.aa_outer_boss_depth_mm,
            start_offset_mm=p.aa_outer_boss_depth_mm,
            reverse_direction=True,
        )

        _sketch_circle_ring(model, p.aa_middle_boss_dia_mm, p.center_through_hole_dia_mm)
        _extrude_current_sketch(
            model,
            p.aa_middle_boss_depth_mm,
            start_offset_mm=p.aa_middle_boss_depth_mm,
            reverse_direction=True,
        )

        _sketch_circle_ring(model, p.aa_inner_boss_dia_mm, p.center_through_hole_dia_mm)
        _extrude_current_sketch(
            model,
            p.aa_inner_boss_depth_mm,
            start_offset_mm=p.aa_inner_boss_depth_mm,
            reverse_direction=True,
        )

        _sketch_corner_pads_with_holes(model, p)
        _extrude_current_sketch(model, p.total_thickness_mm)

        model.SaveAs3(str(sldprt_path), 0, 0)
        model.SaveAs3(str(step_path), 0, 0)

        print(f"Generated SLDPRT: {sldprt_path}")
        print(f"Generated STEP:   {step_path}")
    finally:
        _close_doc_safely(sw, model)


if __name__ == "__main__":
    main()
