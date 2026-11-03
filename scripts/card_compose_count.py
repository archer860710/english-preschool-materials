# -*- coding: utf-8 -*-
"""数数卡（单词.xlsx Sheet「不带字母」）：N 个相同可爱物按网格排列，数量精确可控。
用法: python card_compose_count.py <word> <N> [subject.png]
默认素材 generated-images/subject-apple.png（红苹果）。

规格(2x)：卡 2160x2880 r96 #FFF9F0
插画区 1920x2080 @(120,120) r72  ← 1x: 960x1040 @ (60,60)，方案 B（比带字母版高）
单词 Baloo2 ExtraBold 320px #33322E 基线 y=2668 居中，字距 -2px
无徽章（「不带字母」版定义）。

实现要点：
- 素材先做色键抠图（背景→透明，含边缘羽化），贴在插画区纯底上 → 无方块接缝、无阴影
- 网格：cols = ceil(sqrt(N))，N=10 时 5x2；行距紧凑、整体在插画区内水平垂直居中
- 底色取素材四角中值
"""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from card_compose import (  # noqa: E402
    W, H, CARD_R, CARD_BG, INK, WORD_SIZE, LETTER_SPACING,
    load_font, draw_tracked, rounded_mask, remove_watermark,
)
from PIL import Image, ImageDraw, ImageFilter  # noqa: E402

PANEL = (120, 120, 2040, 2200)  # l, t, r, b（2x）
PANEL_R = 72
BASELINE_Y = 2668
DEFAULT_SUBJECT = "generated-images/subject-apple.png"
CELL_FILL = 0.85   # 每格素材最大占比
ROW_GAP = 1.30     # 行高 = 素材高 × 该系数
BG_KEYS = 6        # 四角+边缘中点采样数


def extract_bg_color(img: Image.Image) -> tuple:
    """四角与边缘中点采样取中值，得到背景色。"""
    w, h = img.size
    pts = [(6, 6), (w - 7, 6), (6, h - 7), (w - 7, h - 7),
           (w // 2, 6), (w // 2, h - 7)]
    px = np.array([img.getpixel(p) for p in pts], dtype=np.float64)
    return tuple(int(v) for v in np.median(px, axis=0))


def cutout(img: Image.Image) -> Image.Image:
    """HSV 抠图：背景 = 高亮度+低饱和（浅色纸纹/渐晕/阴影全清掉），主体 = 高饱和或深色。
    苹果内部高光（白，低饱和）也会被判为背景 → 后续用形态学闭运算尽量填回。"""
    arr = np.asarray(img, dtype=np.float64) / 255.0
    mx, mn = arr.max(axis=2), arr.min(axis=2)
    sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-9), 0.0)
    val = mx
    bg = (sat < 0.42) & (val > 0.70)
    fg = (~bg).astype(np.uint8)
    # 闭运算填内部小洞（高光斑）：膨胀3轮→腐蚀3轮，numpy roll 实现
    def dilate(m):
        out = m.copy()
        for dx, dy in ((1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)):
            out |= np.roll(np.roll(m, dx, 0), dy, 1)
        return out
    def erode(m):
        out = m.copy()
        for dx, dy in ((1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)):
            out &= np.roll(np.roll(m, dx, 0), dy, 1)
        return out
    fg = dilate(fg); fg = dilate(fg); fg = dilate(fg)
    fg = erode(fg); fg = erode(fg); fg = erode(fg)
    alpha = (fg * 255).astype(np.uint8)
    mask = Image.fromarray(alpha, "L").filter(ImageFilter.GaussianBlur(1.5))
    out = img.convert("RGBA")
    out.putalpha(mask)
    return out


def grid_cols(n: int) -> int:
    return max(1, math.ceil(math.sqrt(n)))


def main(word: str, n: int, subject: str) -> None:
    img = Image.open(subject).convert("RGB")
    img = remove_watermark(img)
    bg = extract_bg_color(img)
    item = cutout(img)

    card = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(card)
    d.rounded_rectangle([0, 0, W - 1, H - 1], radius=CARD_R, fill=CARD_BG + (255,))
    d.rounded_rectangle(list(PANEL), radius=PANEL_R, fill=bg + (255,))

    pw, ph = PANEL[2] - PANEL[0], PANEL[3] - PANEL[1]
    cols = grid_cols(n)
    rows = math.ceil(n / cols)
    scale = min(pw * CELL_FILL / cols / item.width, ph * CELL_FILL / rows / item.height)
    tw, th = round(item.width * scale), round(item.height * scale)
    small = item.resize((tw, th), Image.LANCZOS)

    row_h = th * ROW_GAP
    y0 = PANEL[1] + (ph - rows * row_h) / 2 + row_h / 2  # 整体垂直居中
    col_step = pw / cols
    for r in range(rows):
        cnt = min(cols, n - r * cols)
        x0 = PANEL[0] + (pw - cnt * col_step) / 2  # 末行不满时居中
        for c in range(cnt):
            cx = x0 + c * col_step + col_step / 2
            cy = y0 + r * row_h
            card.paste(small, (round(cx - tw / 2), round(cy - th / 2)), small)

    # 插画区内容裁圆角后贴上卡面
    panel_img = Image.new("RGBA", (pw, ph), (0, 0, 0, 0))
    panel_img.paste(card.crop(PANEL), (0, 0))
    card.paste(panel_img, (PANEL[0], PANEL[1]), rounded_mask((pw, ph), PANEL_R))

    f_word = load_font(WORD_SIZE)
    draw_tracked(ImageDraw.Draw(card), (W // 2, BASELINE_Y), word, f_word, INK)

    out_dir = os.path.join("card-exports", "单词（不带字母）")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, f"单词卡-{word}.png")
    card.convert("RGB").save(out)
    print("saved", out, card.size, f"({cols}x{rows} grid, bg={bg})")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit("用法: python card_compose_count.py <word> <N> [subject.png]")
    main(sys.argv[1], int(sys.argv[2]), sys.argv[3] if len(sys.argv) > 3 else DEFAULT_SUBJECT)
