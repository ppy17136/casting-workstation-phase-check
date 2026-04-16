from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
WALKTHROUGH_DIR = ROOT / "artifacts" / "walkthrough"
SHOWCASE_DIR = ROOT / "artifacts" / "showcase"
PPT_DIR = SHOWCASE_DIR / "ppt"
README_DIR = SHOWCASE_DIR / "readme"

TARGETS = [
    ("project_center.png", "项目中心"),
    ("parameters.png", "参数计算"),
    ("simulation.png", "仿真结果"),
    ("documents.png", "工艺卡与质检"),
    ("export.png", "成果导出"),
]


def load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        Path(r"C:\Windows\Fonts\msyh.ttc"),
        Path(r"C:\Windows\Fonts\msyhbd.ttc"),
        Path(r"C:\Windows\Fonts\simhei.ttf"),
    ]
    for path in candidates:
        if path.exists():
            try:
                return ImageFont.truetype(str(path), size)
            except OSError:
                continue
    return ImageFont.load_default()


def crop_to_16_9(image: Image.Image) -> Image.Image:
    width, height = image.size
    target_height = int(width * 9 / 16)
    if target_height >= height:
        return image.copy()
    top = max((height - target_height) // 2 - 10, 0)
    bottom = top + target_height
    return image.crop((0, top, width, bottom))


def make_card(image: Image.Image, title: str) -> Image.Image:
    canvas = Image.new("RGB", (1280, 860), "#f5f1e8")
    draw = ImageDraw.Draw(canvas)
    title_font = load_font(36)
    body_font = load_font(18)

    draw.rounded_rectangle((30, 24, 1250, 836), radius=24, fill="#fffdf8", outline="#d6cfc2", width=2)
    draw.text((60, 48), title, fill="#1f2a44", font=title_font)
    draw.text((60, 96), "砂型铸造工艺图—工艺卡—仿真校核辅助工作站", fill="#6c6f73", font=body_font)

    preview = image.resize((1180, 664))
    canvas.paste(preview, (50, 140))
    return canvas


def build_overview(images: list[tuple[Image.Image, str]]) -> Image.Image:
    canvas = Image.new("RGB", (1600, 980), "#f2efe7")
    draw = ImageDraw.Draw(canvas)
    title_font = load_font(44)
    sub_font = load_font(22)
    caption_font = load_font(24)

    draw.text((60, 36), "圆盖案例软件展示", fill="#17324d", font=title_font)
    draw.text((60, 98), "项目主线：工艺图—工艺卡—仿真校核一体化辅助工作站", fill="#5f646b", font=sub_font)

    slots = [
        (60, 160),
        (830, 160),
        (60, 560),
        (830, 560),
    ]
    for (image, title), (x, y) in zip(images[:4], slots):
        draw.rounded_rectangle((x, y, x + 710, y + 330), radius=20, fill="#fffdf8", outline="#d8d2c7", width=2)
        thumb = image.resize((670, 250))
        canvas.paste(thumb, (x + 20, y + 18))
        draw.text((x + 24, y + 280), title, fill="#21344a", font=caption_font)
    return canvas


def main() -> None:
    PPT_DIR.mkdir(parents=True, exist_ok=True)
    README_DIR.mkdir(parents=True, exist_ok=True)

    prepared: list[tuple[Image.Image, str]] = []

    for filename, title in TARGETS:
        source_path = WALKTHROUGH_DIR / filename
        if not source_path.exists():
            continue
        with Image.open(source_path) as source:
            cropped = crop_to_16_9(source)
            ppt_image = cropped.resize((1280, 720))
            ppt_path = PPT_DIR / filename
            ppt_image.save(ppt_path, quality=95)

            card = make_card(ppt_image, title)
            card_path = README_DIR / f"card_{filename}"
            card.save(card_path, quality=95)
            prepared.append((ppt_image.copy(), title))

    if prepared:
        overview = build_overview(prepared)
        overview.save(README_DIR / "overview_grid.png", quality=95)


if __name__ == "__main__":
    main()
