#!/usr/bin/env python3
"""裁剪截图的指定行带并放大，用于回查 OCR 可疑字符的原始像素。

用途：ic-ocr-fix 技能中，判定 l/1/I、O/0、S/5、Z/2 这类混淆字符时，
正则只能给出候选，最终依据必须是原图像素。本脚本把目标行带裁出并放大，
再由Read 工具直接查看像素判定，不靠正则猜。

用法：
    python crop.py <截图.png> <输出目录> <起始行> <结束行> [放大倍数]

示例：
    python crop.py shot.png tmp_crop 120 140 4
    python crop.py shot.png tmp_crop 120 140 4 --first-line 57
    python crop.py shot.png tmp_crop --list

参数：
    截图.png   源图片路径
    输出目录   裁剪结果存放目录，不存在则创建
    起始行    1-based 行号，与编辑器左侧行号一致
    结束行    1-based 行号，闭区间
    放大倍数  默认 3
    --first-line N  截图内第一行代码对应的编辑器行号（滚动时用），默认 1
    --list           只打印检测到的行带及其行号，不裁剪

输出：
    <输出目录>/crop_L<起始行>-L<结束行>.png
"""

import argparse
import os
import sys

try:
    from PIL import Image, ImageDraw
except ImportError:
    print("缺少依赖 Pillow，请先安装：pip install Pillow", file=sys.stderr)
    sys.exit(1)


def dominant_color(img):
    """估算图像主背景色（按缩略图取众数，够用且快）。"""
    thumb = img.convert("RGB").resize((160, 160))
    counts = {}
    for px in thumb.get_flattened_data() if hasattr(
            thumb, "get_flattened_data") else thumb.getdata():
        counts[px] = counts.get(px, 0) + 1
    return max(counts.items(), key=lambda kv: kv[1])[0]


def color_distance(a, b):
    return sum((x - y) ** 2 for x, y in zip(a, b)) ** 0.5


def row_fill_ratios(img, bg):
    """每行中「非背景色像素」占比。编辑器标题栏/标签栏是全宽实心条，占比≈1。"""
    width, height = img.size
    rgb = img.convert("RGB")
    data = rgb.load()
    ratios = []
    for y in range(height):
        off = 0
        for x in range(0, width, 2):  # 抽样加速
            if color_distance(data[x, y], bg) > 40:
                off += 1
        ratios.append(off / max(1, len(range(0, width, 2))))
    return ratios


def detect_text_bands(img, bg):
    """返回文本行带列表 [(y_top, y_bottom), ...]，按行号顺序。

    跳过开头的实心填充条（编辑器标题栏、标签栏）——它们不是代码行，
    否则后续所有行号都会整体偏移一行。
    """
    width, height = img.size
    gray = img.convert("L")
    pixel = gray.load()

    rows = []
    for y in range(height):
        dark = 0
        for x in range(0, width, 3):  # 抽样加速
            if pixel[x, y] < 128:
                dark += 1
        rows.append(dark)

    bands = []
    in_text = False
    start = 0
    for y, dark in enumerate(rows):
        if dark > 0:
            if not in_text:
                in_text = True
                start = y
        else:
            if in_text:
                if y - start >= 3:
                    bands.append((start, y))
                in_text = False
    if in_text and height - start >= 3:
        bands.append((start, height))

    if not bands:
        return bands

    # 找出从图像顶端开始的连续实心条区域（标题栏/标签栏）
    fill = row_fill_ratios(img, bg)
    bar_bottom = 0
    for y, r in enumerate(fill):
        if r > 0.8:
            bar_bottom = y + 1
        elif y > 0 and r < 0.3:
            break  # 实心条结束
    if bar_bottom <= 0:
        return bands

    # 落在实心条内的文本带（如标题栏里的文件名）不是代码行
    kept = []
    for top, bot in bands:
        if top < bar_bottom:
            continue
        kept.append((top, bot))
    return kept


def crop_lines(img, start_line, end_line, scale, out_dir, first_line, draw_grid):
    bg = dominant_color(img)
    bands = detect_text_bands(img, bg)
    if not bands:
        raise SystemExit("未在图中检测到文本行带，无法定位行号")

    # 第 i 条带（0-based）对应的编辑器行号 = first_line + i
    offset = first_line - 1
    lo = start_line - offset
    hi = end_line - offset
    if lo < 1 or hi > len(bands) or lo > hi:
        raise SystemExit(
            f"行号 {start_line}-{end_line} 超出检测范围"
            f"（图内可映射行号 {first_line}-{first_line + len(bands) - 1}）。"
            f"请检查行号，或用 --first-line 指定首行对应行号。"
        )

    y_top = bands[lo - 1][0]
    y_bottom = bands[hi - 1][1]
    width = img.size[0]

    cropped = img.crop((0, y_top, width, y_bottom))
    cropped = cropped.resize((int(cropped.width * scale),
                              int(cropped.height * scale)), Image.LANCZOS)

    if draw_grid:
        draw = ImageDraw.Draw(cropped)
        band_h = cropped.height / (hi - lo + 1)
        for i in range(start_line, end_line + 1):
            y = (i - start_line) * band_h
            draw.line([(0, y), (cropped.width, y)], fill=(255, 0, 0), width=1)
            draw.text((4, max(0, y + 2)), str(i), fill=(255, 0, 0))

    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"crop_L{start_line}-L{end_line}.png")
    cropped.save(out_path)
    print(out_path)
    return out_path


def list_bands(img, first_line):
    bg = dominant_color(img)
    bands = detect_text_bands(img, bg)
    print(f"检测到 {len(bands)} 个文本行带")
    for i, (top, bot) in enumerate(bands):
        print(f"  行 {first_line + i:>5}  y={top}-{bot}")
    return bands


def main():
    p = argparse.ArgumentParser(
        description="裁剪并放大截图中的指定行带，用于 OCR 字符回查")
    p.add_argument("image", help="源截图路径")
    p.add_argument("out_dir", help="裁剪结果输出目录（--list 时可填 -）")
    p.add_argument("start_line", type=int, nargs="?", help="起始行号（1-based）")
    p.add_argument("end_line", type=int, nargs="?", help="结束行号（1-based）")
    p.add_argument("scale", type=float, nargs="?", default=3, help="放大倍数，默认 3")
    p.add_argument("--first-line", type=int, default=1,
                   help="图内第一行代码对应的编辑器行号（滚动时用），默认 1")
    p.add_argument("--grid", action="store_true", help="叠加行号网格")
    p.add_argument("--list", action="store_true", help="只打印行带映射，不裁剪")
    args = p.parse_args()

    if not os.path.isfile(args.image):
        raise SystemExit(f"文件不存在：{args.image}")

    with Image.open(args.image) as img:
        if args.list:
            list_bands(img, args.first_line)
            return
        if args.start_line is None or args.end_line is None:
            raise SystemExit("需要同时给出起始行号与结束行号（或使用 --list）")
        crop_lines(img, args.start_line, args.end_line, args.scale,
                   args.out_dir, args.first_line, args.grid)


if __name__ == "__main__":
    main()
