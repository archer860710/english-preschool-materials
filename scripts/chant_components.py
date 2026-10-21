# -*- coding: utf-8 -*-
"""非背景连通域分析：找出插图中各主体（1/8 缩放做标记，纯 numpy）"""
import os
import sys
import numpy as np
from PIL import Image

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(BASE, "generated-images", "chant", "chant-ant-cat-alligator-bed.png")
S = 8
img = np.array(Image.open(path).convert("RGB")).astype(int)
H, W, _ = img.shape
small = img[::S, ::S]
h, w, _ = small.shape
bg = np.array([249, 237, 225])
dist = np.abs(small - bg).sum(axis=2)
mask = dist > 60  # 非背景

# 8 邻域连通域（BFS）
lab = np.zeros((h, w), dtype=int)
cur = 0
from collections import deque
for i in range(h):
    for j in range(w):
        if mask[i, j] and lab[i, j] == 0:
            cur += 1
            q = deque([(i, j)])
            lab[i, j] = cur
            while q:
                y, x = q.popleft()
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        ny, nx = y + dy, x + dx
                        if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and lab[ny, nx] == 0:
                            lab[ny, nx] = cur
                            q.append((ny, nx))

print("components:")
comps = []
for c in range(1, cur + 1):
    ys, xs = np.nonzero(lab == c)
    area = len(xs)
    if area < 12:
        continue
    mean = small[ys, xs].mean(axis=0).astype(int)
    # 原图坐标
    bx0, bx1 = xs.min() * S, (xs.max() + 1) * S
    by0, by1 = ys.min() * S, (ys.max() + 1) * S
    cx, cy = xs.mean() * S, ys.mean() * S
    comps.append((area, (bx0, by0, bx1, by1), (int(cx), int(cy)), tuple(mean)))
comps.sort(reverse=True)
for area, bb, cen, mean in comps:
    print(f"area~{area * S * S:>7}  bbox={bb}  centroid={cen}  meanRGB={mean}")
