from __future__ import annotations

import json
import shutil
from pathlib import Path
import sys
import zipfile


WORKSPACE = Path(__file__).resolve().parents[1]
if str(WORKSPACE) not in sys.path:
    sys.path.insert(0, str(WORKSPACE))


def main() -> None:
    artifacts_dir = WORKSPACE / "artifacts"
    bundle_dir = artifacts_dir / "最终提交包"
    if not bundle_dir.exists():
        raise FileNotFoundError(f"未找到最终提交包目录: {bundle_dir}")

    summary = json.loads((artifacts_dir / "demo_workflow_summary.json").read_text(encoding="utf-8"))
    nav_md = bundle_dir / "05_清单与说明" / "先看这个_答辩导航.md"
    nav_txt = bundle_dir / "05_清单与说明" / "先看这个_答辩导航.txt"
    zip_path = artifacts_dir / "最终提交包.zip"

    navigation_text = build_navigation(summary, bundle_dir)
    nav_md.write_text(navigation_text, encoding="utf-8")
    nav_txt.write_text(navigation_text, encoding="utf-8")

    if zip_path.exists():
        zip_path.unlink()
    zip_directory(bundle_dir, zip_path)


def build_navigation(summary: dict, bundle_dir: Path) -> str:
    return "\n".join(
        [
            "# 先看这个：答辩导航",
            "",
            "如果你只剩几分钟准备，请按下面顺序打开：",
            "",
            "## 一、优先打开的文件",
            f"1. 8 页答辩版 PPT：{bundle_dir / '02_申报与答辩材料' / '砂型铸造本地智能工作站_8页答辩版.pptx'}",
            f"2. 5 分钟答辩讲稿：{bundle_dir / '02_申报与答辩材料' / '砂型铸造本地智能工作站_5分钟答辩讲稿.docx'}",
            f"3. 答辩问答提纲：{bundle_dir / '02_申报与答辩材料' / '砂型铸造本地智能工作站_答辩问答提纲.docx'}",
            f"4. 答辩当天操作手册：{bundle_dir / '02_申报与答辩材料' / '砂型铸造本地智能工作站_答辩当天操作手册.docx'}",
            "",
            "## 二、如果老师要求看软件演示",
            f"- 先开便携版：{bundle_dir / '01_软件安装与运行' / 'CastingWorkstation_便携版'}",
            f"- 再准备工艺卡：{summary['document_card_path']}",
            f"- 再准备成果包：{summary['export_zip_path']}",
            "",
            "## 三、如果老师要求看书面材料",
            f"- 图文说明书：{bundle_dir / '02_申报与答辩材料' / '砂型铸造本地智能工作站_创新训练项目图文说明书.docx'}",
            f"- 申请书正文素材：{bundle_dir / '02_申报与答辩材料' / '砂型铸造本地智能工作站_申请书正文素材.docx'}",
            "",
            "## 四、如果时间特别紧",
            f"- 直接使用 3 分钟极简汇报稿：{bundle_dir / '02_申报与答辩材料' / '砂型铸造本地智能工作站_3分钟极简汇报稿.docx'}",
            "",
            "## 五、演示案例信息",
            f"- 项目编号：{summary['project_code']}",
            f"- 项目名称：{summary['project_name']}",
            f"- AI 建议数：{summary['suggestion_count']}",
            f"- 待审核建议数：{summary['pending_review_count']}",
            "",
        ]
    )


def zip_directory(source_dir: Path, zip_path: Path) -> None:
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(source_dir.rglob("*")):
            archive.write(path, arcname=path.relative_to(source_dir.parent))


if __name__ == "__main__":
    main()
