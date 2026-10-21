# -*- coding: utf-8 -*-
"""
Chant 插画自动标注（颜色分类定位 + 背景空白自动选位）
规则：单词在 单词.xlsx A 列 -> 必标；不在 -> 严禁标。
用法：python chant_annotate_auto.py <输入图> <输出图> <词1,词2,...>
"""
import os
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from collections import deque

# 项目根目录 = scripts 的上一级（搬迁后自动跟随，不要再写绝对路径）
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT_PATH = os.path.join(BASE, "assets", "fonts", "baloo2-extrabold.ttf")
ORANGE = (255, 122, 69)
SS = 2
FONT_SIZE = 60

# ---------- 1. 读取与颜色分类 ----------
src = Image.open(sys.argv[1]).convert("RGB")
img = np.array(src).astype(int)
H, W, _ = img.shape
r, g, b = img[..., 0], img[..., 1], img[..., 2]

bg = np.array([249, 237, 221])
bgdist = np.abs(img - bg).sum(axis=2)
is_bg = bgdist < 60

def comps(mask, min_area=300):
    m = mask.copy()
    h, w = m.shape
    out = []
    seen = np.zeros_like(m, dtype=bool)
    for i in range(0, h, 4):
        for j in range(0, w, 4):
            if m[i, j] and not seen[i, j]:
                q = deque([(i, j)]); seen[i, j] = True
                pix = []
                while q:
                    y, x = q.popleft(); pix.append((y, x))
                    for dy in (-2, -1, 0, 1, 2):
                        for dx in (-2, -1, 0, 1, 2):
                            ny, nx = y + dy, x + dx
                            if 0 <= ny < h and 0 <= nx < w and m[ny, nx] and not seen[ny, nx]:
                                seen[ny, nx] = True; q.append((ny, nx))
                if len(pix) >= min_area:
                    ys = np.array([p[0] for p in pix]); xs = np.array([p[1] for p in pix])
                    out.append(dict(area=len(pix), bbox=(int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())),
                                    centroid=(float(xs.mean()), float(ys.mean()))))
    return out

cat_mask = (r > 225) & (g > 135) & (g < 200) & (b > 60) & (b < 135) & ((r - g) > 55) & ((r - b) > 100)
wood_mask = (r > 165) & (r < 228) & (g > 100) & (g < 165) & (b > 55) & (b < 115) & ((r - g) > 45) & ((g - b) > 20)
green_mask = ((g - r) > 45) & ((g - b) > 60)
pink_mask = (r > 220) & (g > 135) & (g < 200) & (b > 145) & (b < 210) & ((b - g) > 5)
# 蚂蚁：右半区最暗棕色簇
dark_mask = (r + g + b < 330) & (r > g) & (g > b)
ant_region = np.zeros_like(dark_mask); ant_region[280:560, 880:1120] = True
ant_mask = dark_mask & ant_region

cat_c = max(comps(cat_mask), key=lambda c: c["area"])
wood_cs = comps(wood_mask, 800)
wood_cs.sort(key=lambda c: -c["area"])
bed_c = wood_cs[0]  # 最大木头块
gat_c = max(comps(green_mask), key=lambda c: c["area"])
ant_c = max(comps(ant_mask, 40), key=lambda c: c["area"])

print("cat:", cat_c)
print("bed(wood max):", bed_c)
print("alligator:", gat_c)
print("ant:", ant_c)

# ---------- 2. 锚点 ----------
bx0, by0, bx1, by1 = bed_c["bbox"]
anchors = {
    "cat": (int((cat_c["bbox"][0] + cat_c["bbox"][2]) / 2), cat_c["bbox"][1] + 40),   # 猫头顶
    "ant": (int(ant_c["centroid"][0]), int(ant_c["centroid"][1])),
    "bed": (int(bed_c["bbox"][2]) - 70, int(bed_c["centroid"][1]) - 120),             # 右床柱
    "alligator": (gat_c["bbox"][0] + 90, gat_c["bbox"][1] + 60),  # 鳄鱼头
}

# ---------- 3. 自动选胶囊位置（纯背景区，离锚点最近） ----------
d = ImageDraw.Draw(src)
font = ImageFont.truetype(FONT_PATH, FONT_SIZE)
pills = []
occupied = []  # 已占用的胶囊矩形，后续标签避开
for word, anchor in anchors.items():
    bb = d.textbbox((0, 0), word, font=font)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    pw = tw + int(FONT_SIZE * 1.2)
    ph = max(th + int(FONT_SIZE * 0.5), int(FONT_SIZE * 1.45))
    hx, hy = pw // 2 + 8, ph // 2 + 8
    best = None
    for cy in range(hy + 6, H - hy - 6, 12):
        for cx in range(hx + 6, W - hx - 6, 12):
            if cx > 1300 and cy > 940:   # 避开水印角
                continue
            if not is_bg[cy - hy:cy + hy, cx - hx:cx + hx].all():
                continue
            if any(cx - hx < oc[2] and oc[0] < cx + hx and cy - hy < oc[3] and oc[1] < cy + hy for oc in occupied):
                continue
            # 引线路径也必须走背景（终点 30px 内除外）
            n = 24
            ok_line = True
            for t in range(n + 1):
                px = cx + (anchor[0] - cx) * t / n
                py = cy + (anchor[1] - cy) * t / n
                if ((px - anchor[0]) ** 2 + (py - anchor[1]) ** 2) ** 0.5 < 90:
                    continue
                xi, yi = int(px), int(py)
                if 0 <= yi < H and 0 <= xi < W and not is_bg[yi, xi]:
                    ok_line = False
                    break
            if not ok_line:
                continue
            dist = ((cx - anchor[0]) ** 2 + (cy - anchor[1]) ** 2) ** 0.5
            if dist < 60 or dist > 460:
                continue
            if best is None or dist < best[0]:
                best = (dist, cx, cy)
    if best is None:
        raise SystemExit(f"no bg spot for {word}")
    _, cx, cy = best
    occupied.append((cx - hx, cy - hy, cx + hx, cy + hy))
    pills.append(dict(word=word, anchor=anchor, pill=(cx, cy), box=(cx - pw // 2, cy - ph // 2, cx + pw // 2, cy + ph // 2)))
    print(f"{word}: anchor={anchor} pill=({cx},{cy}) size=({pw},{ph})")

# ---------- 4. 渲染（超采样） ----------
canvas = src.resize((W * SS, H * SS), Image.LANCZOS)
dd = ImageDraw.Draw(canvas)
font_ss = ImageFont.truetype(FONT_PATH, FONT_SIZE * SS)
for p in pills:
    c = tuple(v * SS for v in p["pill"]); a = tuple(v * SS for v in p["anchor"])
    dd.line([c, a], fill=ORANGE + (255,), width=9 * SS)
    rr = 13 * SS
    dd.ellipse([a[0] - rr, a[1] - rr, a[0] + rr, a[1] + rr], fill=ORANGE + (255,))
for p in pills:
    x0, y0, x1, y1 = [v * SS for v in p["box"]]
    dd.rounded_rectangle([x0, y0, x1, y1], radius=(y1 - y0) // 2, fill=ORANGE + (255,))
    bb = dd.textbbox((0, 0), p["word"], font=font_ss)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    pad_x = int(FONT_SIZE * SS * 0.6)
    tx = x0 + pad_x - bb[0]
    ty = y0 + (y1 - y0 - th) // 2 - bb[1]
    dd.text((tx, ty), p["word"], font=font_ss, fill=(255, 255, 255, 255))
out = canvas.resize((W, H), Image.LANCZOS)
out.save(sys.argv[2])
print("saved:", sys.argv[2], out.size)
