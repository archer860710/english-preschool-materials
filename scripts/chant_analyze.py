# -*- coding: utf-8 -*-
"""按颜色分类测量 chant 插画中各主体位置（cat/ant/bed/alligator）"""
import os
import sys
from PIL import Image
import numpy as np

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(BASE, "generated-images", "chant", "chant-ant-cat-alligator-bed.png")
img = np.array(Image.open(path).convert("RGB")).astype(int)
H, W, _ = img.shape
r, g, b = img[..., 0], img[..., 1], img[..., 2]
print("size:", W, H, "corner bg:", img[5, 5], img[H - 5, 5])

def report(name, mask, min_area=400):
    n = int(mask.sum())
    if n < min_area:
        print(f"{name}: too few px ({n})")
        return
    ys, xs = np.nonzero(mask)
    print(f"{name}: px={n} bbox x[{xs.min()},{xs.max()}] y[{ys.min()},{ys.max()}] centroid=({xs.mean():.0f},{ys.mean():.0f})")

# 绿色 = 鳄鱼
report("alligator(green)", (g > r + 30) & (g > b + 30))
# 粉色 = 床的毯子/枕头（也含腮红）
report("pink", (r > 210) & (g > 130) & (g < 205) & (b > 150) & (b < 220) & (b < g))
# 深棕 = 蚂蚁（最暗的棕色）
report("ant(darkbrown)", (r > 55) & (r < 135) & (g > 40) & (g < 105) & (b > 20) & (b < 80) & (r > g) & (g > b))
# 橙色 = 猫
report("cat(orange)", (r > 215) & (g > 115) & (g < 195) & (b < 125) & (g > b + 40))
# 中棕木头 = 床架
report("bed(wood)", (r > 140) & (r < 215) & (g > 85) & (g < 150) & (b > 50) & (b < 115) & (r > g + 30) & (g > b + 15))

# 蚂蚁精细：在最右侧 1/4 且深棕
report("ant-right-half", ((g > r + 30) & (g > b + 30)) * 0 + ((r > 55) & (r < 135) & (g > 40) & (g < 105) & (b > 20) & (b < 80) & (xs_ok := (np.arange(W)[None, :] > 600) & (np.arange(W)[None, :] < 900) & (np.arange(H)[:, None] > 200) & (np.arange(H)[:, None] < 420))))
