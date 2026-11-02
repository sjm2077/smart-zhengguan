from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont
from pptx import Presentation


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_PATH = Path(
    r"D:/xwechat_files/wxid_52uyd7qozaie22_83c0/msg/file/2026-06/001重点研发计划（太赫兹运用 蓝色）(1)(1).pptx"
)
OUTPUT_DIR = ROOT / "dist" / "graduate_defense_ppt"
SLIDE_DIR = OUTPUT_DIR / "slides"
PPT_PATH = OUTPUT_DIR / "graduate_management_defense.pptx"

WIDTH = 1920
HEIGHT = 1080

BLUE = (27, 91, 187, 255)
BLUE_DARK = (10, 51, 120, 255)
BLUE_LIGHT = (233, 243, 255, 255)
BLUE_EDGE = (80, 131, 210, 255)
TEXT = (20, 28, 45, 255)
TEXT_MUTED = (92, 104, 124, 255)
TEXT_LIGHT = (248, 250, 255, 255)
LINE = (202, 219, 242, 255)
CARD = (250, 252, 255, 255)
RED = (198, 44, 44, 255)
GREEN = (29, 140, 84, 255)
ORANGE = (231, 126, 35, 255)
PURPLE = (111, 76, 177, 255)
TEAL = (37, 150, 190, 255)
GRAY = (242, 245, 250, 255)
SHADOW = (22, 58, 120, 42)

FONT_REG = "C:/Windows/Fonts/msyh.ttc"
FONT_BOLD = "C:/Windows/Fonts/msyhbd.ttc"
FONT_HEI = "C:/Windows/Fonts/simhei.ttf"


def ensure_dirs() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    SLIDE_DIR.mkdir(parents=True, exist_ok=True)


def font(size: int, bold: bool = False, heavy: bool = False) -> ImageFont.FreeTypeFont:
    if heavy:
        path = FONT_HEI
    else:
        path = FONT_BOLD if bold else FONT_REG
    return ImageFont.truetype(path, size=size)


def text_size(draw: ImageDraw.ImageDraw, text: str, ft: ImageFont.FreeTypeFont) -> tuple[int, int]:
    box = draw.textbbox((0, 0), text, font=ft)
    return box[2] - box[0], box[3] - box[1]


def wrap_text(draw: ImageDraw.ImageDraw, text: str, ft: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    lines: list[str] = []
    for paragraph in text.split("\n"):
        if not paragraph:
            lines.append("")
            continue
        current = ""
        for ch in paragraph:
            candidate = current + ch
            width = draw.textbbox((0, 0), candidate, font=ft)[2]
            if width <= max_width or not current:
                current = candidate
            else:
                lines.append(current)
                current = ch
        if current:
            lines.append(current)
    return lines


def draw_multiline(
    draw: ImageDraw.ImageDraw,
    text: str,
    xy: tuple[int, int],
    ft: ImageFont.FreeTypeFont,
    fill: tuple[int, int, int, int],
    max_width: int,
    line_gap: int = 10,
) -> int:
    lines = wrap_text(draw, text, ft, max_width)
    x, y = xy
    line_height = draw.textbbox((0, 0), "测试Ag", font=ft)[3] + line_gap
    for line in lines:
        draw.text((x, y), line, font=ft, fill=fill)
        y += line_height
    return y


def rounded_card(
    canvas: Image.Image,
    box: tuple[int, int, int, int],
    fill: tuple[int, int, int, int] = CARD,
    outline: tuple[int, int, int, int] | None = LINE,
    width: int = 2,
    radius: int = 26,
    shadow: bool = True,
) -> None:
    if shadow:
        shadow_layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        sd = ImageDraw.Draw(shadow_layer)
        shadow_box = (box[0] + 8, box[1] + 12, box[2] + 8, box[3] + 12)
        sd.rounded_rectangle(shadow_box, radius=radius, fill=SHADOW)
        shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(16))
        canvas.alpha_composite(shadow_layer)
    draw = ImageDraw.Draw(canvas)
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def badge(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    label: str,
    fill: tuple[int, int, int, int],
    text_fill: tuple[int, int, int, int] = TEXT_LIGHT,
    size: int = 26,
) -> None:
    draw.rounded_rectangle(box, radius=18, fill=fill)
    ft = font(size, bold=True)
    tw, th = text_size(draw, label, ft)
    x = box[0] + (box[2] - box[0] - tw) / 2
    y = box[1] + (box[3] - box[1] - th) / 2 - 2
    draw.text((x, y), label, font=ft, fill=text_fill)


def add_background(canvas: Image.Image) -> ImageDraw.ImageDraw:
    canvas.paste((255, 255, 255, 255), (0, 0, WIDTH, HEIGHT))
    draw = ImageDraw.Draw(canvas)

    bg = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(bg)

    for i in range(6):
        alpha = 20 - i * 2
        gd.arc(
            (WIDTH - 760 - i * 80, -220 - i * 30, WIDTH + 360 + i * 60, 640 + i * 30),
            start=190,
            end=315,
            fill=(194, 209, 230, max(alpha, 8)),
            width=3,
        )
    for i in range(4):
        gd.arc(
            (-120, HEIGHT - 340 - i * 36, 720 + i * 60, HEIGHT + 180 + i * 36),
            start=190,
            end=310,
            fill=(210, 222, 242, 18),
            width=3,
        )
    canvas.alpha_composite(bg)
    return draw


def add_content_header(draw: ImageDraw.ImageDraw, index: int, title: str) -> None:
    big = font(66, heavy=True)
    title_ft = font(62, heavy=True)
    label = f"{index}.0" if index < 10 else str(index)
    draw.text((88, 42), label, font=big, fill=BLUE)
    draw.text((212, 40), title, font=title_ft, fill=BLUE)
    draw.line((0, 120, WIDTH, 120), fill=BLUE_EDGE, width=6)


def draw_metric_card(
    canvas: Image.Image,
    box: tuple[int, int, int, int],
    value: str,
    label: str,
    accent: tuple[int, int, int, int] = BLUE,
) -> None:
    rounded_card(canvas, box)
    draw = ImageDraw.Draw(canvas)
    draw.rectangle((box[0], box[1], box[0] + 14, box[3]), fill=accent)
    draw.text((box[0] + 36, box[1] + 28), value, font=font(48, bold=True), fill=accent)
    draw.text((box[0] + 38, box[1] + 96), label, font=font(24), fill=TEXT_MUTED)


def draw_bullets(
    draw: ImageDraw.ImageDraw,
    items: list[tuple[str, str]],
    x: int,
    y: int,
    width: int,
    gap: int = 20,
) -> int:
    title_ft = font(27, bold=True)
    body_ft = font(23)
    for lead, body in items:
        draw.ellipse((x, y + 8, x + 16, y + 24), fill=BLUE)
        draw.text((x + 28, y), lead, font=title_ft, fill=TEXT)
        y = draw_multiline(draw, body, (x + 28, y + 38), body_ft, TEXT_MUTED, width - 28, line_gap=8)
        y += gap
    return y


def draw_layer_box(
    canvas: Image.Image,
    box: tuple[int, int, int, int],
    title: str,
    lines: list[str],
    fill: tuple[int, int, int, int],
    text_fill: tuple[int, int, int, int] = TEXT_LIGHT,
) -> None:
    rounded_card(canvas, box, fill=fill, outline=None, shadow=False, radius=24)
    draw = ImageDraw.Draw(canvas)
    draw.text((box[0] + 28, box[1] + 18), title, font=font(28, bold=True), fill=text_fill)
    body_ft = font(22)
    y = box[1] + 64
    for line in lines:
        draw.text((box[0] + 30, y), line, font=body_ft, fill=text_fill)
        y += 34


def draw_arrow(draw: ImageDraw.ImageDraw, start: tuple[int, int], end: tuple[int, int], fill=BLUE_EDGE, width: int = 6) -> None:
    draw.line((start, end), fill=fill, width=width)
    angle = math.atan2(end[1] - start[1], end[0] - start[0])
    size = 14
    left = (
        end[0] - size * math.cos(angle) + size * 0.8 * math.sin(angle),
        end[1] - size * math.sin(angle) - size * 0.8 * math.cos(angle),
    )
    right = (
        end[0] - size * math.cos(angle) - size * 0.8 * math.sin(angle),
        end[1] - size * math.sin(angle) + size * 0.8 * math.cos(angle),
    )
    draw.polygon([end, left, right], fill=fill)


def draw_radar(
    canvas: Image.Image,
    center: tuple[int, int],
    radius: int,
    labels: list[str],
    values: list[float],
) -> None:
    draw = ImageDraw.Draw(canvas)
    overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    steps = len(labels)

    for ring in range(1, 5):
        points = []
        r = radius * ring / 4
        for i in range(steps):
            angle = -math.pi / 2 + 2 * math.pi * i / steps
            points.append((center[0] + r * math.cos(angle), center[1] + r * math.sin(angle)))
        draw.polygon(points, outline=(205, 219, 239, 255))

    axis_ft = font(18)
    for i, label in enumerate(labels):
        angle = -math.pi / 2 + 2 * math.pi * i / steps
        ax = center[0] + radius * math.cos(angle)
        ay = center[1] + radius * math.sin(angle)
        draw.line((center[0], center[1], ax, ay), fill=(205, 219, 239, 255), width=2)
        lx = center[0] + (radius + 36) * math.cos(angle)
        ly = center[1] + (radius + 34) * math.sin(angle)
        tw, th = text_size(draw, label, axis_ft)
        draw.text((lx - tw / 2, ly - th / 2), label, font=axis_ft, fill=TEXT_MUTED)

    points = []
    for i, value in enumerate(values):
        angle = -math.pi / 2 + 2 * math.pi * i / steps
        r = radius * max(0.08, min(value, 1.0))
        points.append((center[0] + r * math.cos(angle), center[1] + r * math.sin(angle)))
    od.polygon(points, fill=(42, 109, 220, 76), outline=(42, 109, 220, 255))
    for pt in points:
        od.ellipse((pt[0] - 5, pt[1] - 5, pt[0] + 5, pt[1] + 5), fill=BLUE)
    canvas.alpha_composite(overlay)


def draw_trend_chart(
    canvas: Image.Image,
    box: tuple[int, int, int, int],
    series_a: list[int],
    series_b: list[int],
    labels: list[str],
) -> None:
    rounded_card(canvas, box, fill=(255, 255, 255, 255), shadow=False)
    draw = ImageDraw.Draw(canvas)
    left, top, right, bottom = box
    chart_left = left + 54
    chart_top = top + 58
    chart_right = right - 34
    chart_bottom = bottom - 50
    draw.text((left + 24, top + 18), "发展趋势预测", font=font(26, bold=True), fill=TEXT)

    for i in range(5):
        y = chart_top + (chart_bottom - chart_top) * i / 4
        draw.line((chart_left, y, chart_right, y), fill=(224, 231, 241, 255), width=2)

    all_values = series_a + series_b
    vmin, vmax = min(all_values), max(all_values)
    scale = lambda v: chart_bottom - (v - vmin) / (vmax - vmin + 1e-6) * (chart_bottom - chart_top)

    def points(values: list[int]) -> list[tuple[float, float]]:
        pts = []
        for idx, value in enumerate(values):
            x = chart_left + idx * (chart_right - chart_left) / max(1, len(values) - 1)
            y = scale(value)
            pts.append((x, y))
        return pts

    pts_a = points(series_a)
    pts_b = points(series_b)

    draw.line(pts_a, fill=BLUE, width=6)
    draw.line(pts_b, fill=ORANGE, width=5)
    for pts, color in [(pts_a, BLUE), (pts_b, ORANGE)]:
        for x, y in pts:
            draw.ellipse((x - 5, y - 5, x + 5, y + 5), fill=color)

    legend_y = top + 18
    draw.rectangle((right - 230, legend_y + 10, right - 200, legend_y + 16), fill=BLUE)
    draw.text((right - 190, legend_y), "目标对象", font=font(18), fill=TEXT_MUTED)
    draw.rectangle((right - 110, legend_y + 10, right - 80, legend_y + 16), fill=ORANGE)
    draw.text((right - 70, legend_y), "同年级均值", font=font(18), fill=TEXT_MUTED)

    axis_ft = font(16)
    for idx, label in enumerate(labels):
        x = chart_left + idx * (chart_right - chart_left) / max(1, len(labels) - 1)
        tw, th = text_size(draw, label, axis_ft)
        draw.text((x - tw / 2, chart_bottom + 12), label, font=axis_ft, fill=TEXT_MUTED)


def draw_ui_mock_dashboard(canvas: Image.Image, box: tuple[int, int, int, int], title: str) -> None:
    rounded_card(canvas, box, fill=(255, 255, 255, 255))
    draw = ImageDraw.Draw(canvas)
    left, top, right, bottom = box
    draw.rounded_rectangle((left + 18, top + 18, right - 18, bottom - 18), radius=20, outline=(222, 230, 240, 255), width=2)
    draw.rectangle((left + 18, top + 18, left + 110, bottom - 18), fill=(14, 60, 131, 255))
    draw.text((left + 35, top + 34), "GM", font=font(22, bold=True), fill=TEXT_LIGHT)
    for i, txt in enumerate(["首页", "招生", "学籍", "培养", "预测"]):
        y = top + 88 + i * 50
        draw.rounded_rectangle((left + 28, y, left + 100, y + 28), radius=10, fill=(255, 255, 255, 34) if i != 0 else (255, 255, 255, 70))
        draw.text((left + 42, y + 4), txt, font=font(16), fill=TEXT_LIGHT)
    draw.text((left + 134, top + 30), title, font=font(22, bold=True), fill=TEXT)
    draw.rounded_rectangle((left + 132, top + 70, right - 40, top + 118), radius=12, fill=BLUE_LIGHT)
    for i in range(3):
        x = left + 134 + i * 146
        rounded_card(canvas, (x, top + 138, x + 130, top + 220), fill=(248, 250, 254, 255), shadow=False, radius=18)
        draw.text((x + 18, top + 156), ["在读规模", "本年毕业", "奖助覆盖"][i], font=font(17), fill=TEXT_MUTED)
        draw.text((x + 18, top + 186), ["1,268", "214", "82.6%"][i], font=font(28, bold=True), fill=BLUE)
    rounded_card(canvas, (left + 134, top + 242, left + 464, bottom - 38), fill=(248, 251, 255, 255), shadow=False, radius=18)
    rounded_card(canvas, (left + 486, top + 138, right - 40, bottom - 38), fill=(248, 251, 255, 255), shadow=False, radius=18)
    chart = ImageDraw.Draw(canvas)
    pts = [(left + 170, bottom - 100), (left + 240, top + 340), (left + 310, top + 290), (left + 380, top + 330), (left + 430, top + 280)]
    chart.line(pts, fill=BLUE, width=5)
    for x, y in pts:
        chart.ellipse((x - 4, y - 4, x + 4, y + 4), fill=BLUE)
    chart.text((left + 166, top + 258), "近年趋势", font=font(18, bold=True), fill=TEXT)
    cx = left + 604
    cy = top + 268
    r = 86
    chart.ellipse((cx - r, cy - r, cx + r, cy + r), outline=(220, 228, 240, 255), width=26)
    chart.arc((cx - r, cy - r, cx + r, cy + r), start=215, end=320, fill=BLUE, width=26)
    chart.text((left + 518, top + 156), "结构分布", font=font(18, bold=True), fill=TEXT)
    chart.text((cx - 20, cy - 18), "72%", font=font(28, bold=True), fill=TEXT)


def draw_ui_mock_intelligent(canvas: Image.Image, box: tuple[int, int, int, int], title: str) -> None:
    rounded_card(canvas, box, fill=(255, 255, 255, 255))
    draw = ImageDraw.Draw(canvas)
    left, top, right, bottom = box
    draw.rounded_rectangle((left + 18, top + 18, right - 18, bottom - 18), radius=20, outline=(222, 230, 240, 255), width=2)
    draw.text((left + 34, top + 30), title, font=font(22, bold=True), fill=TEXT)
    rounded_card(canvas, (left + 34, top + 74, right - 34, top + 132), fill=BLUE_LIGHT, shadow=False, radius=16)
    for i, chip in enumerate(["专业", "年级", "范围", "风险"]):
        x = left + 58 + i * 120
        draw.rounded_rectangle((x, top + 88, x + 92, top + 116), radius=12, fill=(255, 255, 255, 255))
        draw.text((x + 18, top + 92), chip, font=font(16), fill=TEXT_MUTED)
    rounded_card(canvas, (left + 34, top + 154, left + 214, bottom - 34), fill=(248, 251, 255, 255), shadow=False, radius=16)
    rounded_card(canvas, (left + 230, top + 154, right - 34, top + 286), fill=(248, 251, 255, 255), shadow=False, radius=16)
    rounded_card(canvas, (left + 230, top + 302, right - 34, bottom - 34), fill=(248, 251, 255, 255), shadow=False, radius=16)

    center = (left + 124, top + 286)
    radius = 66
    labels = ["学", "研", "管", "导", "群", "实", "健"]
    values = [0.78, 0.68, 0.72, 0.81, 0.65, 0.74, 0.62]
    steps = len(labels)
    for ring in range(1, 4):
        points = []
        r = radius * ring / 3
        for i in range(steps):
            angle = -math.pi / 2 + 2 * math.pi * i / steps
            points.append((center[0] + r * math.cos(angle), center[1] + r * math.sin(angle)))
        draw.polygon(points, outline=(205, 219, 239, 255))
    poly = []
    for i, value in enumerate(values):
        angle = -math.pi / 2 + 2 * math.pi * i / steps
        r = radius * value
        poly.append((center[0] + r * math.cos(angle), center[1] + r * math.sin(angle)))
    overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    od.polygon(poly, fill=(42, 109, 220, 78), outline=BLUE)
    for x, y in poly:
        od.ellipse((x - 4, y - 4, x + 4, y + 4), fill=BLUE)
    canvas.alpha_composite(overlay)
    draw.text((left + 62, top + 166), "雷达画像", font=font(18, bold=True), fill=TEXT)
    for idx, label in enumerate(labels):
        lx = center[0] + (radius + 22) * math.cos(-math.pi / 2 + 2 * math.pi * idx / steps)
        ly = center[1] + (radius + 20) * math.sin(-math.pi / 2 + 2 * math.pi * idx / steps)
        draw.text((lx - 8, ly - 8), label, font=font(14), fill=TEXT_MUTED)

    draw.text((left + 252, top + 170), "趋势预测", font=font(18, bold=True), fill=TEXT)
    chart_left = left + 252
    chart_top = top + 198
    chart_right = right - 54
    chart_bottom = top + 252
    for i in range(3):
        y = chart_top + i * 26
        draw.line((chart_left, y, chart_right, y), fill=(224, 231, 241, 255), width=2)
    pts_a = [(chart_left + 8, chart_bottom - 30), (chart_left + 54, chart_bottom - 42), (chart_left + 100, chart_bottom - 26), (chart_left + 146, chart_bottom - 14), (chart_left + 192, chart_bottom - 6)]
    pts_b = [(chart_left + 8, chart_bottom - 18), (chart_left + 54, chart_bottom - 12), (chart_left + 100, chart_bottom - 8), (chart_left + 146, chart_bottom - 4), (chart_left + 192, chart_bottom)]
    draw.line(pts_a, fill=BLUE, width=4)
    draw.line(pts_b, fill=ORANGE, width=4)
    for pts, color in [(pts_a, BLUE), (pts_b, ORANGE)]:
        for x, y in pts:
            draw.ellipse((x - 3, y - 3, x + 3, y + 3), fill=color)
    draw.rectangle((left + 344, top + 170, left + 370, top + 176), fill=BLUE)
    draw.text((left + 378, top + 160), "目标", font=font(14), fill=TEXT_MUTED)
    draw.rectangle((left + 420, top + 170, left + 446, top + 176), fill=ORANGE)
    draw.text((left + 454, top + 160), "均值", font=font(14), fill=TEXT_MUTED)

    draw.text((left + 236, top + 318), "风险预警", font=font(18, bold=True), fill=TEXT)
    for i, (label, color, tip) in enumerate([
        ("高风险", RED, "学分偏低"),
        ("中风险", ORANGE, "沟通不足"),
        ("建议", GREEN, "辅导与跟踪"),
    ]):
        y = top + 346 + i * 54
        badge(draw, (left + 236, y, left + 316, y + 30), label, color, size=15)
        draw.text((left + 330, y + 2), tip, font=font(16), fill=TEXT)
    draw.rounded_rectangle((left + 236, bottom - 72, right - 54, bottom - 44), radius=12, fill=(233, 243, 255, 255))
    draw.text((left + 248, bottom - 66), "AI 问答：检索优先，生成辅助", font=font(14), fill=TEXT_MUTED)


def draw_data_pipeline(canvas: Image.Image, box: tuple[int, int, int, int]) -> None:
    rounded_card(canvas, box)
    draw = ImageDraw.Draw(canvas)
    draw.text((box[0] + 30, box[1] + 22), "数据整理与导入链路", font=font(28, bold=True), fill=TEXT)
    steps = [
        ("Excel 样本", BLUE, "招生 / 学籍 / 培养 / 课程"),
        ("导入脚本", TEAL, "Excel 导入 + 初始化脚本"),
        ("Django 模型", PURPLE, "19 个核心模型承载业务数据"),
        ("分析结果", GREEN, "查询画像 / 预测分析 / 风险预警"),
    ]
    y = box[1] + 98
    for idx, (title, color, desc) in enumerate(steps):
        item_box = (box[0] + 36, y, box[2] - 36, y + 106)
        rounded_card(canvas, item_box, fill=(255, 255, 255, 255), shadow=False, radius=20)
        draw.rectangle((item_box[0], item_box[1], item_box[0] + 16, item_box[3]), fill=color)
        draw.text((item_box[0] + 34, item_box[1] + 18), title, font=font(24, bold=True), fill=color)
        draw.text((item_box[0] + 34, item_box[1] + 56), desc, font=font(20), fill=TEXT_MUTED)
        if idx < len(steps) - 1:
            draw_arrow(draw, (box[0] + 260, y + 110), (box[0] + 260, y + 148), fill=BLUE_EDGE, width=5)
        y += 144
    draw.text((box[0] + 36, box[3] - 48), "基础口径统一维护：学院、年级、专业、层次", font=font(20), fill=TEXT_MUTED)


def draw_heatmap(canvas: Image.Image, box: tuple[int, int, int, int], rows: int = 4, cols: int = 5) -> None:
    draw = ImageDraw.Draw(canvas)
    left, top, right, bottom = box
    cell_w = (right - left) / cols
    cell_h = (bottom - top) / rows
    palette = [
        (222, 235, 255, 255),
        (176, 210, 249, 255),
        (123, 172, 236, 255),
        (71, 129, 220, 255),
        (29, 91, 187, 255),
    ]
    values = [
        [4, 3, 2, 4, 3],
        [2, 4, 3, 3, 2],
        [3, 2, 4, 2, 4],
        [4, 4, 3, 2, 3],
    ]
    for r in range(rows):
        for c in range(cols):
            x1 = left + c * cell_w
            y1 = top + r * cell_h
            x2 = x1 + cell_w - 8
            y2 = y1 + cell_h - 8
            color = palette[values[r][c] - 1]
            draw.rounded_rectangle((x1, y1, x2, y2), radius=12, fill=color)


def slide_cover() -> Image.Image:
    canvas = Image.new("RGBA", (WIDTH, HEIGHT), (255, 255, 255, 255))
    draw = add_background(canvas)

    photo_band = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    pd = ImageDraw.Draw(photo_band)
    pd.rectangle((0, 590, WIDTH, 830), fill=(32, 86, 176, 18))
    for i in range(22):
        x = 50 + i * 86
        h = 90 + (i % 4) * 32
        pd.rectangle((x, 650 - h, x + 44, 760), fill=(255, 255, 255, 12))
    canvas.alpha_composite(photo_band)

    title_box = (282, 96, 1644, 186)
    rounded_card(canvas, title_box, fill=(255, 255, 255, 220), outline=None, shadow=False, radius=12)
    draw.text((460, 120), "研究生管理系统答辩汇报", font=font(42, bold=True), fill=TEXT)

    title_ft = font(112, heavy=True)
    sub_ft = font(68, heavy=True)
    draw.text((216, 264), "研究生管理系统", font=title_ft, fill=BLUE)
    draw.text((360, 486), "的设计与实现", font=sub_ft, fill=BLUE)

    draw.text((610, 676), "答辩人：待补充", font=font(34, bold=True), fill=BLUE)
    draw.text((610, 728), "专业：待补充    指导教师：待补充", font=font(28), fill=TEXT_MUTED)

    footer = (0, 802, WIDTH, HEIGHT)
    footer_img = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    fd = ImageDraw.Draw(footer_img)
    fd.rectangle(footer, fill=BLUE_DARK)
    for i in range(8):
        fd.arc((-120 + i * 120, 816, 520 + i * 120, 1160), start=210, end=332, fill=(56, 129, 219, 42), width=3)
    canvas.alpha_composite(footer_img)

    labels = ["统一业务管理", "跨模块画像分析", "趋势预测与预警", "知识问答辅助"]
    x = 120
    for idx, label in enumerate(labels):
        draw.text((x, 898), label, font=font(30), fill=TEXT_LIGHT)
        x += 336
        if idx != len(labels) - 1:
            draw.line((x - 28, 892, x - 28, 962), fill=(255, 255, 255, 90), width=3)
    return canvas


def slide_background_goal() -> Image.Image:
    canvas = Image.new("RGBA", (WIDTH, HEIGHT), (255, 255, 255, 255))
    draw = add_background(canvas)
    add_content_header(draw, 2, "项目背景与目标")

    left = (86, 170, 888, 934)
    right = (1028, 170, 1834, 934)
    rounded_card(canvas, left)
    rounded_card(canvas, right)
    draw.text((126, 204), "背景痛点", font=font(32, bold=True), fill=BLUE)
    draw.text((1068, 204), "系统目标", font=font(32, bold=True), fill=BLUE)

    bullet_items = [
        ("业务数据分散", "招生、学籍、培养、课程、学位、奖助、就业等数据分散在不同模块，横向查看成本高。"),
        ("全程画像不足", "现有系统更偏向事务录入，难以从年级、专业、学生群体等维度形成综合画像。"),
        ("智能支撑薄弱", "缺少发展趋势预测、风险预警、治理建议和政策问答等辅助决策能力。"),
    ]
    draw_bullets(draw, bullet_items, 126, 270, 680)

    goal_cards = [
        ((1068, 276, 1420, 432), BLUE, "统一管理", "围绕研究生培养全过程构建一体化管理平台"),
        ((1450, 276, 1794, 432), TEAL, "综合画像", "按年级、专业等条件联动查看跨模块结果"),
        ((1068, 478, 1420, 634), PURPLE, "智能预测", "提供趋势分析、风险识别和治理建议"),
        ((1450, 478, 1794, 634), GREEN, "知识辅助", "支持制度检索、政策问答与安全控制"),
    ]
    for box, color, title, desc in goal_cards:
        rounded_card(canvas, box, fill=(255, 255, 255, 255), shadow=False, radius=24)
        draw.rectangle((box[0], box[1], box[2], box[1] + 16), fill=color)
        draw.text((box[0] + 24, box[1] + 34), title, font=font(28, bold=True), fill=color)
        draw_multiline(draw, desc, (box[0] + 24, box[1] + 82), font(22), TEXT_MUTED, box[2] - box[0] - 48, line_gap=8)

    summary = (1068, 700, 1794, 884)
    rounded_card(canvas, summary, fill=(247, 250, 255, 255), outline=(186, 206, 236, 255), radius=26)
    draw.text((1100, 732), "核心定位", font=font(28, bold=True), fill=BLUE_DARK)
    draw_multiline(
        draw,
        "将研究生管理系统从“信息录入与查询工具”升级为“学院培养治理的辅助决策平台”。",
        (1100, 784),
        font(27, bold=True),
        TEXT,
        640,
        line_gap=10,
    )
    return canvas


def slide_architecture() -> Image.Image:
    canvas = Image.new("RGBA", (WIDTH, HEIGHT), (255, 255, 255, 255))
    draw = add_background(canvas)
    add_content_header(draw, 3, "整体系统架构")

    center_box = (760, 320, 1160, 774)
    rounded_card(canvas, center_box, fill=(247, 250, 255, 255), outline=(166, 197, 236, 255), radius=28)
    draw.text((812, 356), "业务数据模型", font=font(34, bold=True), fill=BLUE_DARK)
    for i, text in enumerate(["账户模型", "招生 / 学籍 / 培养", "课程 / 学位 / 答辩", "奖助 / 就业 / 预测"]):
        y = 430 + i * 70
        rounded_card(canvas, (798, y, 1124, y + 48), fill=(255, 255, 255, 255), shadow=False, radius=16)
        draw.text((822, y + 10), text, font=font(22), fill=TEXT_MUTED)

    boxes = [
        ((164, 266, 620, 470), "前端页面展示", ["17 个页面模块", "7 个复用组件", "查询、可视化、交互"], BLUE),
        ((1300, 266, 1756, 470), "后端接口服务", ["Django 三个应用模块", "17 个业务接口视图", "认证、业务逻辑、返回结构"], TEAL),
        ((164, 566, 620, 770), "智能预测分析", ["趋势预测", "雷达评分", "风险预警与治理建议"], PURPLE),
        ((1300, 566, 1756, 770), "知识问答辅助", ["制度文件检索", "政策问答", "知识库优先引用"], GREEN),
        ((420, 812, 860, 972), "安全控制", ["请求限制 / 限流 / 参数校验", "LLM 开关与 JSON 结构化输出"], ORANGE),
        ((1060, 812, 1500, 972), "系统目标", ["统一管理 + 综合画像 + 辅助决策"], BLUE_DARK),
    ]
    for box, title, lines, fill in boxes:
        draw_layer_box(canvas, box, title, lines, fill)

    arrows = [
        ((620, 368), (760, 430)),
        ((1300, 368), (1160, 430)),
        ((620, 668), (760, 610)),
        ((1300, 668), (1160, 610)),
        ((860, 812), (900, 774)),
        ((1280, 812), (1020, 774)),
    ]
    for start, end in arrows:
        draw_arrow(draw, start, end)

    draw.text((604, 1010), "实现从页面展示、业务处理到智能分析和安全控制的完整链路", font=font(24), fill=TEXT_MUTED)
    return canvas


def slide_frontend() -> Image.Image:
    canvas = Image.new("RGBA", (WIDTH, HEIGHT), (255, 255, 255, 255))
    draw = add_background(canvas)
    add_content_header(draw, 4, "前端功能实现")

    left_box = (88, 168, 690, 930)
    rounded_card(canvas, left_box)
    draw.text((126, 208), "建设内容", font=font(32, bold=True), fill=BLUE)
    draw_metric_card(canvas, (126, 280, 310, 430), "17", "页面模块")
    draw_metric_card(canvas, (338, 280, 522, 430), "7", "复用组件", accent=TEAL)
    draw_metric_card(canvas, (126, 454, 310, 604), "2", "核心页面", accent=PURPLE)
    draw_metric_card(canvas, (338, 454, 522, 604), "1", "统一路由 / 登录拦截", accent=GREEN)

    items = [
        ("页面覆盖", "首页总览、招生、学籍、培养、课程、学位、答辩、奖助、就业、搜索与个人中心等主要流程。"),
        ("组件复用", "封装图表卡片、仪表盘卡片、全局查询栏、顶部导航、侧边栏等组件，保证风格统一。"),
        ("关键页面", "智能预测页面集成雷达图、趋势预测、风险预警与 AI 解读；跨模块查询页面支持学生画像联动分析。"),
    ]
    draw_bullets(draw, items, 126, 650, 500, gap=18)

    draw_ui_mock_dashboard(canvas, (760, 188, 1366, 542), "首页总览")
    draw_ui_mock_intelligent(canvas, (1380, 188, 1836, 542), "智能预测")
    rounded_card(canvas, (760, 578, 1836, 930))
    draw.text((796, 614), "跨模块查询示意", font=font(30, bold=True), fill=BLUE)
    draw.rounded_rectangle((796, 668, 1800, 718), radius=16, fill=BLUE_LIGHT)
    for i, chip in enumerate(["年级：2024级", "专业：公共管理", "模式：群体画像"]):
        draw.rounded_rectangle((818 + i * 220, 678, 996 + i * 220, 708), radius=12, fill=(255, 255, 255, 255))
        draw.text((836 + i * 220, 683), chip, font=font(17), fill=TEXT_MUTED)
    for idx, label in enumerate(["画像总览", "指标对比", "结构分布", "明细结果"]):
        x1 = 804 + idx * 250
        rounded_card(canvas, (x1, 746, x1 + 220, 840), fill=(248, 251, 255, 255), shadow=False, radius=18)
        draw.text((x1 + 18, 766), label, font=font(22, bold=True), fill=TEXT)
        draw.text((x1 + 18, 804), ["综合评分 84.6", "奖助 / 就业 / 培养", "性别 / 年级 / 去向", "支持下钻到学生群体"][idx], font=font(18), fill=TEXT_MUTED)
    draw_heatmap(canvas, (1370, 760, 1788, 892))
    return canvas


def slide_backend() -> Image.Image:
    canvas = Image.new("RGBA", (WIDTH, HEIGHT), (255, 255, 255, 255))
    draw = add_background(canvas)
    add_content_header(draw, 5, "后端功能实现")

    left = (88, 168, 742, 930)
    right = (794, 168, 1834, 930)
    rounded_card(canvas, left)
    rounded_card(canvas, right)

    draw.text((126, 206), "模块与数据建模", font=font(32, bold=True), fill=BLUE)
    for box, title, desc, color in [
        ((126, 274, 700, 392), "accounts", "账户认证、当前用户信息、Token 获取与刷新", BLUE),
        ((126, 416, 700, 534), "common", "共享选项、通用接口与基础配置支持", TEAL),
        ((126, 558, 700, 676), "graduate", "研究生业务主模块，承载招生到预测的核心逻辑", PURPLE),
    ]:
        rounded_card(canvas, box, fill=(255, 255, 255, 255), shadow=False, radius=24)
        draw.rectangle((box[0], box[1], box[0] + 16, box[3]), fill=color)
        draw.text((box[0] + 34, box[1] + 18), title, font=font(28, bold=True), fill=color)
        draw.text((box[0] + 34, box[1] + 60), desc, font=font(21), fill=TEXT_MUTED)

    draw_metric_card(canvas, (126, 728, 340, 872), "19", "核心数据模型", accent=BLUE_DARK)
    draw_metric_card(canvas, (366, 728, 580, 872), "17", "业务接口视图", accent=ORANGE)
    draw.text((126, 892), "认证接口：登录获取 token / 刷新 token / 获取当前用户信息", font=font(20), fill=TEXT_MUTED)

    draw.text((836, 206), "接口与服务链路", font=font(32, bold=True), fill=BLUE)
    stages = [
        ((840, 300, 1044, 390), "前端请求", BLUE),
        ((1080, 300, 1284, 390), "API View", TEAL),
        ((1320, 300, 1524, 390), "Service", PURPLE),
        ((1560, 300, 1764, 390), "Model", GREEN),
    ]
    for box, title, color in stages:
        rounded_card(canvas, box, fill=(255, 255, 255, 255), shadow=False, radius=22)
        draw.text((box[0] + 48, box[1] + 28), title, font=font(28, bold=True), fill=color)
    for idx in range(len(stages) - 1):
        draw_arrow(draw, (stages[idx][0][2] + 10, 346), (stages[idx + 1][0][0] - 18, 346))

    service_area = (838, 452, 1786, 884)
    rounded_card(canvas, service_area, fill=(248, 251, 255, 255), shadow=False, radius=26)
    draw.text((872, 486), "智能预测服务重点能力", font=font(30, bold=True), fill=BLUE_DARK)
    skills = [
        ("预测数据构建", "基于结构化样本生成趋势分析上下文"),
        ("雷达评分与趋势预测", "计算多维综合发展结果与阶段性变化"),
        ("风险解释与治理建议", "围绕课程、科研、导师反馈等字段生成预警"),
        ("知识检索联动", "制度文件检索 + 问答辅助 + 结构化输出控制"),
    ]
    y = 546
    for title, desc in skills:
        rounded_card(canvas, (872, y, 1748, y + 74), fill=(255, 255, 255, 255), shadow=False, radius=18)
        draw.text((900, y + 16), title, font=font(24, bold=True), fill=BLUE)
        draw.text((1140, y + 20), desc, font=font(20), fill=TEXT_MUTED)
        y += 96
    return canvas


def slide_data_portrait() -> Image.Image:
    canvas = Image.new("RGBA", (WIDTH, HEIGHT), (255, 255, 255, 255))
    draw = add_background(canvas)
    add_content_header(draw, 6, "数据与跨模块画像")

    draw_data_pipeline(canvas, (88, 168, 760, 930))

    right = (804, 168, 1834, 930)
    rounded_card(canvas, right)
    draw.text((842, 206), "跨模块查询与学生画像", font=font(32, bold=True), fill=BLUE)
    rounded_card(canvas, (842, 272, 1794, 340), fill=BLUE_LIGHT, shadow=False, radius=18)
    for i, text in enumerate(["年级：2024级", "专业：公共管理", "结果：群体画像"]):
        x = 870 + i * 260
        draw.rounded_rectangle((x, 286, x + 200, 324), radius=14, fill=(255, 255, 255, 255))
        draw.text((x + 18, 292), text, font=font(18), fill=TEXT_MUTED)

    rounded_card(canvas, (842, 378, 1266, 618), fill=(248, 251, 255, 255), shadow=False, radius=20)
    rounded_card(canvas, (1290, 378, 1794, 618), fill=(248, 251, 255, 255), shadow=False, radius=20)
    draw.text((872, 410), "学生画像总览", font=font(26, bold=True), fill=TEXT)
    draw.text((1320, 410), "跨模块指标热力", font=font(26, bold=True), fill=TEXT)
    draw_radar(canvas, (1054, 520), 108, ["奖助", "就业", "培养", "学位", "基础画像", "课程", "科研"], [0.82, 0.76, 0.74, 0.70, 0.85, 0.78, 0.68])
    draw_heatmap(canvas, (1324, 458, 1740, 584), rows=4, cols=4)
    rounded_card(canvas, (842, 652, 1794, 894), fill=(248, 251, 255, 255), shadow=False, radius=20)
    draw.text((872, 684), "功能价值", font=font(26, bold=True), fill=TEXT)
    bullets = [
        ("横向整合", "把奖助、就业、培养、学位与基础画像等分散模块整合到同一查询结果。"),
        ("联动分析", "支持按年级、专业等维度切换对象，从群体视角观察研究生发展状态。"),
        ("画像升级", "系统从“单模块信息展示”扩展为“跨模块综合画像分析”。"),
    ]
    draw_bullets(draw, bullets, 878, 736, 850, gap=16)
    return canvas


def slide_prediction() -> Image.Image:
    canvas = Image.new("RGBA", (WIDTH, HEIGHT), (255, 255, 255, 255))
    draw = add_background(canvas)
    add_content_header(draw, 7, "智能预测与风险预警")

    left = (88, 168, 980, 934)
    right = (1030, 168, 1832, 934)
    rounded_card(canvas, left)
    rounded_card(canvas, right)

    draw.text((126, 206), "七维雷达与趋势预测", font=font(32, bold=True), fill=BLUE)
    draw_radar(
        canvas,
        (364, 490),
        200,
        ["学业投入", "科研训练", "自我管理", "导师支持", "共同体融入", "实践服务", "身心发展"],
        [0.82, 0.70, 0.76, 0.74, 0.68, 0.72, 0.63],
    )
    draw_trend_chart(canvas, (566, 316, 942, 566), [62, 65, 69, 73, 77], [60, 61, 63, 64, 66], ["1月", "2月", "3月", "4月", "预测"])
    note_font = font(18)
    for idx, text in enumerate([
        "指标体系覆盖课程成绩、学分完成、科研任务、活动参与、导师反馈、心理测评等多维数据。",
        "评分方法综合使用直接取值、线性换算与反向计分，统一不同类型指标的比较口径。",
        "输出结果包括趋势指数、月度序列、风险等级、风险领域与治理建议。",
    ]):
        y = 636 + idx * 88
        rounded_card(canvas, (566, y, 942, y + 70), fill=(248, 251, 255, 255), shadow=False, radius=18)
        draw_multiline(draw, text, (590, y + 12), note_font, TEXT_MUTED, 320, line_gap=6)

    draw.text((1068, 206), "风险预警与智能问答", font=font(32, bold=True), fill=BLUE)
    badges = [
        ("输入指标", BLUE, "课程 / 培养 / 科研 / 导师反馈 / 心理测评"),
        ("风险识别", RED, "低学分完成率 / 科研不足 / 沟通频率低"),
        ("治理建议", GREEN, "学业辅导 / 导师沟通 / 心理关注 / 跟踪复盘"),
        ("智能问答", PURPLE, "政策制度检索优先，AI 生成仅作辅助"),
    ]
    y = 278
    for title, color, body in badges:
        rounded_card(canvas, (1070, y, 1790, y + 108), fill=(255, 255, 255, 255), shadow=False, radius=20)
        draw.rectangle((1070, y, 1090, y + 108), fill=color)
        draw.text((1112, y + 18), title, font=font(28, bold=True), fill=color)
        draw_multiline(draw, body, (1112, y + 58), font(21), TEXT_MUTED, 620, line_gap=8)
        y += 132
    rounded_card(canvas, (1070, 820, 1790, 902), fill=(246, 249, 255, 255), outline=(177, 203, 238, 255), radius=18)
    draw.text((1100, 846), "模块特色：趋势预测 + 风险预警 + 治理建议 + 知识问答形成组合能力", font=font(22, bold=True), fill=BLUE_DARK)
    return canvas


def slide_security_summary() -> Image.Image:
    canvas = Image.new("RGBA", (WIDTH, HEIGHT), (255, 255, 255, 255))
    draw = add_background(canvas)
    add_content_header(draw, 8, "安全控制与项目总结")

    draw.text((92, 168), "安全控制", font=font(32, bold=True), fill=BLUE)
    top_cards = [
        ((88, 222, 516, 430), BLUE, "输入校验", "对 studentId、年级、专业、聊天问题、历史消息和模型参数做格式、长度、范围校验。"),
        ((552, 222, 980, 430), ORANGE, "接口保护", "对预测分析、预测对话、搜索和查询等接口设置请求大小限制与按 IP 限流。"),
        ((1016, 222, 1444, 430), PURPLE, "模型边界", "默认不开启外部模型，密钥通过环境变量管理，不暴露调试信息。"),
        ((1480, 222, 1832, 430), GREEN, "知识优先", "政策制度类问题优先依据知识库检索，降低制度性误判与 AI 幻觉风险。"),
    ]
    for box, color, title, desc in top_cards:
        rounded_card(canvas, box)
        draw.rectangle((box[0], box[1], box[2], box[1] + 18), fill=color)
        draw.text((box[0] + 24, box[1] + 44), title, font=font(28, bold=True), fill=color)
        draw_multiline(draw, desc, (box[0] + 24, box[1] + 94), font(20), TEXT_MUTED, box[2] - box[0] - 48, line_gap=8)

    lower = (88, 492, 1832, 942)
    rounded_card(canvas, lower)
    draw.text((126, 528), "项目总结", font=font(32, bold=True), fill=BLUE)
    draw_multiline(
        draw,
        "本项目完成了研究生管理系统从前端页面、复用组件、后端模型、接口服务、数据导入到智能分析与安全控制的完整实现。",
        (126, 584),
        font(28, bold=True),
        TEXT,
        1540,
        line_gap=10,
    )

    summary_cards = [
        ((126, 692, 638, 884), BLUE, "统一业务管理", "覆盖招生、学籍、培养、课程、学位、答辩、奖助和就业等主要模块。"),
        ((704, 692, 1216, 884), TEAL, "跨模块综合画像", "以年级和专业为切入点联动展示多业务数据，形成群体画像分析。"),
        ((1282, 692, 1794, 884), PURPLE, "辅助决策能力", "通过趋势预测、风险预警、治理建议和知识问答支撑学院治理。"),
    ]
    for box, color, title, desc in summary_cards:
        rounded_card(canvas, box, fill=(248, 251, 255, 255), shadow=False, radius=24)
        draw.text((box[0] + 24, box[1] + 26), title, font=font(28, bold=True), fill=color)
        draw_multiline(draw, desc, (box[0] + 24, box[1] + 82), font(21), TEXT_MUTED, box[2] - box[0] - 48, line_gap=8)

    draw.text((126, 900), "项目价值：推动研究生管理系统从“信息管理工具”走向“培养治理辅助决策平台”。", font=font(24), fill=BLUE_DARK)
    return canvas


def save_slides(slides: list[Image.Image]) -> list[Path]:
    paths = []
    for idx, slide in enumerate(slides, start=1):
        path = SLIDE_DIR / f"slide_{idx:02d}.png"
        slide.convert("RGB").save(path, "PNG", optimize=True)
        paths.append(path)
    return paths


def clear_presentation(prs: Presentation) -> None:
    slide_ids = list(prs.slides._sldIdLst)
    for slide_id in slide_ids:
        rel_id = slide_id.rId
        prs.part.drop_rel(rel_id)
        prs.slides._sldIdLst.remove(slide_id)


def build_ppt(slide_paths: list[Path]) -> None:
    prs = Presentation(str(TEMPLATE_PATH))
    clear_presentation(prs)
    blank_layout = prs.slide_layouts[6]
    for slide_path in slide_paths:
        slide = prs.slides.add_slide(blank_layout)
        slide.shapes.add_picture(str(slide_path), 0, 0, width=prs.slide_width, height=prs.slide_height)
    prs.save(str(PPT_PATH))


def main() -> None:
    ensure_dirs()
    slides = [
        slide_cover(),
        slide_background_goal(),
        slide_architecture(),
        slide_frontend(),
        slide_backend(),
        slide_data_portrait(),
        slide_prediction(),
        slide_security_summary(),
    ]
    slide_paths = save_slides(slides)
    build_ppt(slide_paths)
    print(f"Generated PPT: {PPT_PATH}")


if __name__ == "__main__":
    main()
