from __future__ import annotations

import json
import shutil
from pathlib import Path
import sys


WORKSPACE = Path(__file__).resolve().parents[1]
if str(WORKSPACE) not in sys.path:
    sys.path.insert(0, str(WORKSPACE))


def main() -> None:
    artifacts_dir = WORKSPACE / "artifacts"
    release_dir = WORKSPACE / "release"
    dist_dir = WORKSPACE / "dist"
    summary = json.loads((artifacts_dir / "demo_workflow_summary.json").read_text(encoding="utf-8"))

    bundle_root = artifacts_dir / "最终提交包"
    if bundle_root.exists():
        shutil.rmtree(bundle_root)
    bundle_root.mkdir(parents=True, exist_ok=True)

    software_dir = bundle_root / "01_软件安装与运行"
    docs_dir = bundle_root / "02_申报与答辩材料"
    demo_dir = bundle_root / "03_演示案例与成果包"
    media_dir = bundle_root / "04_视频与截图"
    refs_dir = bundle_root / "05_清单与说明"

    for directory in (software_dir, docs_dir, demo_dir, media_dir, refs_dir):
        directory.mkdir(parents=True, exist_ok=True)

    copy_if_exists(release_dir / "installer" / "CastingWorkstationSetup.exe", software_dir / "CastingWorkstationSetup.exe")
    copy_tree_if_exists(dist_dir / "CastingWorkstation", software_dir / "CastingWorkstation_便携版")
    copy_tree_if_exists(dist_dir / "SolidWorksBridge", software_dir / "SolidWorksBridge")

    document_files = [
        "砂型铸造本地智能工作站_创新训练项目图文说明书.docx",
        "砂型铸造本地智能工作站_创新训练项目图文说明书.md",
        "砂型铸造本地智能工作站_创新训练项目答辩材料.pptx",
        "砂型铸造本地智能工作站_创新训练项目答辩提纲.md",
        "砂型铸造本地智能工作站_8页答辩版.pptx",
        "砂型铸造本地智能工作站_8页答辩版提纲.md",
        "砂型铸造本地智能工作站_5分钟答辩讲稿.docx",
        "砂型铸造本地智能工作站_5分钟答辩讲稿.md",
        "砂型铸造本地智能工作站_3分钟极简汇报稿.docx",
        "砂型铸造本地智能工作站_3分钟极简汇报稿.md",
        "砂型铸造本地智能工作站_答辩问答提纲.docx",
        "砂型铸造本地智能工作站_答辩问答提纲.md",
        "砂型铸造本地智能工作站_逐页讲解词.docx",
        "砂型铸造本地智能工作站_逐页讲解词.md",
        "砂型铸造本地智能工作站_申请书正文素材.docx",
        "砂型铸造本地智能工作站_申请书正文素材.md",
        "砂型铸造本地智能工作站_最终提交清单.docx",
        "砂型铸造本地智能工作站_最终提交清单.md",
        "砂型铸造本地智能工作站_答辩当天操作手册.docx",
        "砂型铸造本地智能工作站_答辩当天操作手册.md",
    ]
    for name in document_files:
        copy_if_exists(artifacts_dir / name, docs_dir / name)

    export_zip = Path(summary["export_zip_path"])
    process_card = Path(summary["document_card_path"])
    checklist = Path(summary["checklist_path"])
    copy_if_exists(process_card, demo_dir / process_card.name)
    copy_if_exists(checklist, demo_dir / checklist.name)
    copy_if_exists(export_zip, demo_dir / export_zip.name)

    demo_summary_files = [
        "demo_workflow_summary.md",
        "demo_workflow_summary.json",
        "demo_materials_manifest.md",
        "创新训练项目材料清单.md",
    ]
    for name in demo_summary_files:
        copy_if_exists(artifacts_dir / name, refs_dir / name)

    copy_if_exists(artifacts_dir / "demo_walkthrough.mp4", media_dir / "demo_walkthrough.mp4")
    copy_tree_if_exists(artifacts_dir / "walkthrough", media_dir / "walkthrough")

    readme_path = refs_dir / "提交包说明.txt"
    readme_path.write_text(build_readme(summary), encoding="utf-8")


def copy_if_exists(source: Path, target: Path) -> None:
    if source.exists():
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)


def copy_tree_if_exists(source: Path, target: Path) -> None:
    if source.exists():
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(source, target)


def build_readme(summary: dict) -> str:
    return "\n".join(
        [
            "砂型铸造本地智能工作站最终提交包说明",
            "",
            "目录说明：",
            "01_软件安装与运行：安装包、便携版、SolidWorksBridge。",
            "02_申报与答辩材料：说明书、PPT、讲稿、问答提纲、申请书正文素材。",
            "03_演示案例与成果包：工艺卡、质检清单、案例成果包 ZIP。",
            "04_视频与截图：录屏视频与关键页面截图。",
            "05_清单与说明：材料清单、流程摘要和本说明文件。",
            "",
            f"演示项目编号：{summary['project_code']}",
            f"演示项目名称：{summary['project_name']}",
            f"工艺卡：{summary['document_card_path']}",
            f"成果包 ZIP：{summary['export_zip_path']}",
            "",
            "建议提交方式：",
            "1. 将“最终提交包”整体复制到 U 盘或网盘。",
            "2. 答辩现场优先使用 02_申报与答辩材料 中的精简版 PPT 与讲稿。",
            "3. 若需软件实机演示，使用 01_软件安装与运行 中的便携版或安装包。",
            "",
        ]
    )


if __name__ == "__main__":
    main()
