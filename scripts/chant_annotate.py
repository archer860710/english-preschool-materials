# -*- coding: utf-8 -*-
"""
Chant 插画英文单词标注器
--------------------------------------------------
规则（用户 2026-10-15 定义）：
  1) 单词出现在 单词.xlsx A 列 -> 必须在图上标注
  2) 单词不在 单词.xlsx A 列 -> 严禁标注

用法：
  python chant_annotate.py <输入图> <输出图> <labels.json>
labels.json 结构：
  {
    "font_size": 60,
    "labels": [
      {"word": "cat",       "anchor": [545, 195], "pill": [545, 90]},
      {"word": "ant",       "anchor": [695, 300], "pill": [880, 300]},
      {"word": "bed",       "anchor": [835, 470], "pill": [1000, 470]},
      {"word": "alligator", "anchor": [390, 555], "pill": [390, 700]}
    ]
  }
  anchor = 指向主体的小圆点坐标；pill = 标签胶囊中心坐标（原图 1536x1024 坐标系）
"""
import json
import os
import sys
from PIL import Image, ImageDraw, ImageFont

# 项目根目录 = scripts 的上一级（搬迁后自动跟随，不要再写绝对路径）
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT_PATH = os.path.join(BASE, "assets", "fonts", "baloo2-extrabold.ttf")
PILL_COLOR = (255, 122, 69)   # #FF7A45 暖橙（与单词卡徽章同色）
TEXT_COLOR = (255, 255, 255)
SS = 2                        # 超采样倍数，保证圆角/文字边缘平滑
LINE_W = 9
DOT_R = 13


def render(img_path, out_path, spec):
    img = Image.open(img_path).convert("RGBA")
    W, H = img.size
    canvas = img.resize((W * SS, H * SS), Image.LANCZOS)
    d = ImageDraw.Draw(canvas)
    base_fs = spec.get("font_size", 60)

    items = []
    for lb in spec["labels"]:
        fs = int(lb.get("size", base_fs)) * SS
        font = ImageFont.truetype(FONT_PATH, fs)
        bb = d.textbbox((0, 0), lb["word"], font=font)
        tw, th = bb[2] - bb[0], bb[3] - bb[1]
        pad_x = int(fs * 0.60)
        pad_y = int(fs * 0.26)
        w = tw + 2 * pad_x
        h = max(th + 2 * pad_y, int(fs * 1.45))
        cx, cy = lb["pill"][0] * SS, lb["pill"][1] * SS
        x0, y0 = cx - w // 2, cy - h // 2
        ax, ay = lb["anchor"][0] * SS, lb["anchor"][1] * SS
        items.append(dict(word=lb["word"], font=font, bb=bb, box=(x0, y0, x0 + w, y0 + h),
                          anchor=(ax, ay), center=(cx, cy), tw=tw, th=th, pad_x=pad_x))

    # 1) 引线 + 端点圆点
    for it in items:
        d.line([it["center"], it["anchor"]], fill=PILL_COLOR + (255,), width=LINE_W * SS)
        r = DOT_R * SS
        ax, ay = it["anchor"]
        d.ellipse([ax - r, ay - r, ax + r, ay + r], fill=PILL_COLOR + (255,))

    # 2) 胶囊底
    for it in items:
        x0, y0, x1, y1 = it["box"]
        d.rounded_rectangle([x0, y0, x1, y1], radius=(y1 - y0) // 2, fill=PILL_COLOR + (255,))

    # 3) 文字（居中，按 bbox 偏移校正）
    for it in items:
        x0, y0, x1, y1 = it["box"]
        tx = x0 + it["pad_x"] - it["bb"][0]
        ty = y0 + (y1 - y0 - it["th"]) // 2 - it["bb"][1]
        d.text((tx, ty), it["word"], font=it["font"], fill=TEXT_COLOR + (255,))

    out = canvas.resize((W, H), Image.LANCZOS)
    out.convert("RGB").save(out_path)
    print("saved:", out_path, out.size, "labels:", [i["word"] for i in items])


if __name__ == "__main__":
    inp, outp, js = sys.argv[1], sys.argv[2], sys.argv[3]
    with open(js, "r", encoding="utf-8") as f:
        spec = json.load(f)
    render(inp, outp, spec)
