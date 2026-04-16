from __future__ import annotations

from dataclasses import dataclass

from app.core.repositories.part_repository import PartRecord
from app.core.repositories.scheme_repository import SchemeRecord


@dataclass(slots=True)
class CalculatedParameter:
    param_group: str
    param_code: str
    param_name: str
    param_value: str
    param_unit: str
    value_type: str
    source_type: str
    calc_formula: str


class CalculationService:
    def calculate(self, part: PartRecord, scheme: SchemeRecord) -> list[CalculatedParameter]:
        net_weight = part.net_weight or 0.0
        blank_weight = part.blank_weight or 0.0
        max_wall = part.max_wall_thickness or 0.0

        pouring_time = 6.0 + (net_weight ** 0.5) * 1.8 if net_weight > 0 else 0.0
        choke_area = (net_weight * 0.95 / pouring_time) if pouring_time > 0 else 0.0
        riser_diameter = max(40.0, max_wall * 1.8) if max_wall > 0 else 40.0
        yield_ratio = (net_weight / blank_weight * 100.0) if blank_weight > 0 else 0.0

        return [
            CalculatedParameter(
                param_group="gating",
                param_code="pouring_time_s",
                param_name="浇注时间",
                param_value=f"{pouring_time:.2f}",
                param_unit="s",
                value_type="number",
                source_type="calculated",
                calc_formula="t = 6 + 1.8 * sqrt(net_weight)",
            ),
            CalculatedParameter(
                param_group="gating",
                param_code="choke_area_cm2",
                param_name="阻流截面积",
                param_value=f"{choke_area:.2f}",
                param_unit="cm²",
                value_type="number",
                source_type="calculated",
                calc_formula="A = 0.95 * net_weight / pouring_time",
            ),
            CalculatedParameter(
                param_group="feeding",
                param_code="riser_diameter_mm",
                param_name="冒口直径",
                param_value=f"{riser_diameter:.2f}",
                param_unit="mm",
                value_type="number",
                source_type="rule",
                calc_formula="D = max(40, 1.8 * max_wall_thickness)",
            ),
            CalculatedParameter(
                param_group="economy",
                param_code="yield_ratio_pct",
                param_name="出品率",
                param_value=f"{yield_ratio:.2f}",
                param_unit="%",
                value_type="number",
                source_type="calculated",
                calc_formula="yield = net_weight / blank_weight * 100",
            ),
            CalculatedParameter(
                param_group="scheme",
                param_code="gating_type",
                param_name="浇注系统",
                param_value=scheme.gating_type or "-",
                param_unit="",
                value_type="text",
                source_type="manual",
                calc_formula="来自工艺方案",
            ),
        ]
