from __future__ import annotations

from app.core.repositories.parameter_repository import ParameterRecord
from app.core.repositories.scheme_repository import SchemeRecord
from app.core.repositories.simulation_repository import SimulationResultRecord


class SuggestionGenerationService:
    def generate(
        self,
        *,
        scheme: SchemeRecord,
        parameters: list[ParameterRecord],
        results: list[SimulationResultRecord],
    ) -> list[dict]:
        suggestions: list[dict] = []
        parameter_map = {item.param_name: item for item in parameters}

        gating_type = (scheme.gating_type or "").strip()
        if not gating_type:
            suggestions.append(
                self._card(
                    title="补全浇注系统定义",
                    suggestion_text="当前方案未明确浇注系统类型，建议先固定浇注系统形式后再继续仿真与工艺卡定稿。",
                    target_params=["浇注系统"],
                    preconditions="工艺方案中浇注系统字段为空",
                    risk_notice="浇注系统未定义会导致参数计算和仿真边界条件缺失。",
                    confidence_score=0.86,
                    evidence_items=[
                        self._evidence("scheme", "工艺方案字段", scheme.scheme_code, "浇注系统字段为空"),
                    ],
                )
            )

        yield_item = parameter_map.get("出品率")
        if yield_item and self._to_float(yield_item.param_value) < 60:
            suggestions.append(
                self._card(
                    title="优化出品率",
                    suggestion_text="当前出品率偏低，建议复核冒口体积、内浇道截面和工艺补缩方案，压缩无效金属消耗。",
                    target_params=["出品率", "冒口直径", "阻流截面积"],
                    preconditions="已完成关键参数计算",
                    risk_notice="盲目缩小补缩系统可能引入缩孔缩松，需要结合仿真结果同步校核。",
                    confidence_score=0.78,
                    evidence_items=[
                        self._evidence("parameter", "参数计算", "出品率", f"当前出品率={yield_item.param_value}{yield_item.param_unit}"),
                    ],
                )
            )

        riser_item = parameter_map.get("冒口直径")
        if riser_item and self._to_float(riser_item.param_value) <= 45:
            suggestions.append(
                self._card(
                    title="复核补缩系统尺寸",
                    suggestion_text="当前冒口直径接近经验下限，建议结合热节位置和最大壁厚进一步复核补缩能力。",
                    target_params=["冒口直径"],
                    preconditions="存在厚大截面或热点区域",
                    risk_notice="补缩不足时更容易在厚大截面形成缩孔或缩松。",
                    confidence_score=0.74,
                    evidence_items=[
                        self._evidence("parameter", "参数计算", "冒口直径", f"当前冒口直径={riser_item.param_value}{riser_item.param_unit}"),
                    ],
                )
            )

        if not results:
            suggestions.append(
                self._card(
                    title="建立基准仿真任务",
                    suggestion_text="当前方案尚无仿真结果，建议先建立基准充型/凝固仿真任务，用于后续优化前后对比。",
                    target_params=["仿真任务", "结果对比"],
                    preconditions="方案已形成基础参数",
                    risk_notice="缺少基准仿真会削弱后续建议的证据充分性。",
                    confidence_score=0.92,
                    evidence_items=[
                        self._evidence("simulation", "仿真中心", "当前方案", "未找到结果记录"),
                    ],
                )
            )
            return suggestions

        shrinkage_hits = [
            item for item in results
            if "缩" in item.result_name or "shrink" in item.result_type.lower() or "缩" in item.summary
        ]
        if shrinkage_hits:
            suggestions.append(
                self._card(
                    title="针对缩孔缩松结果优化补缩路径",
                    suggestion_text="仿真结果已出现缩孔/缩松相关信号，建议优先调整冒口位置、补缩通道或局部冷铁方案。",
                    target_params=["冒口直径", "浇注位置", "冷铁/补缩措施"],
                    preconditions="已有缩孔缩松类仿真结果",
                    risk_notice="仅放大冒口可能改善有限，需同时考虑热节迁移与补缩通道连续性。",
                    confidence_score=0.9,
                    evidence_items=[
                        self._evidence(
                            "simulation_result",
                            hit.result_name,
                            hit.file_path or hit.result_type,
                            hit.summary or "检测到缩孔缩松相关结果",
                        )
                        for hit in shrinkage_hits[:3]
                    ],
                )
            )

        temperature_hits = [
            item for item in results
            if "temp" in item.result_type.lower() or "温" in item.result_name or "温" in item.summary
        ]
        if temperature_hits:
            suggestions.append(
                self._card(
                    title="基于温度场复核浇注时间",
                    suggestion_text="建议结合温度场和充型结果复核浇注时间与阻流面积，避免浇注过慢导致温降过大。",
                    target_params=["浇注时间", "阻流截面积"],
                    preconditions="已有温度场或凝固时间类结果",
                    risk_notice="单纯放大阻流面积可能引入紊流与卷气风险。",
                    confidence_score=0.73,
                    evidence_items=[
                        self._evidence(
                            "simulation_result",
                            temperature_hits[0].result_name,
                            temperature_hits[0].file_path or temperature_hits[0].result_type,
                            temperature_hits[0].summary or "存在温度场相关结果",
                        )
                    ],
                )
            )

        if not suggestions:
            suggestions.append(
                self._card(
                    title="结果总体可用，建议进入人工复核",
                    suggestion_text="当前参数与仿真结果未发现明显高风险项，建议进入人工评审并核对工艺卡完整性。",
                    target_params=["工艺卡", "人工评审"],
                    preconditions="参数与结果记录完整",
                    risk_notice="该结论不替代教师或工艺工程师的最终确认。",
                    confidence_score=0.68,
                    evidence_items=[
                        self._evidence("simulation", "结果汇总", scheme.scheme_code, "未识别到高风险规则命中"),
                    ],
                )
            )
        return suggestions

    def _card(
        self,
        *,
        title: str,
        suggestion_text: str,
        target_params: list[str],
        preconditions: str,
        risk_notice: str,
        confidence_score: float,
        evidence_items: list[dict],
    ) -> dict:
        return {
            "title": title,
            "suggestion_text": suggestion_text,
            "target_params": target_params,
            "preconditions": preconditions,
            "risk_notice": risk_notice,
            "confidence_score": confidence_score,
            "validation_status": "rule_checked",
            "human_review_status": "pending",
            "evidence_items": evidence_items,
        }

    def _evidence(self, evidence_type: str, title: str, source_path: str, excerpt: str) -> dict:
        return {
            "evidence_type": evidence_type,
            "title": title,
            "source_path": source_path,
            "excerpt": excerpt,
            "link_role": "support",
            "match_status": "derived",
        }

    def _to_float(self, value: str) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0
