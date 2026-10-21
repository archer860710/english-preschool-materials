# -*- coding: utf-8 -*-
"""按项目权威规格本地合成单词卡（与画布导出 2160x2880 同规格）。
用法: python card_compose.py <word> <illustration.png>
规格(2x): 卡 2160x2880 r96 #FFF9F0 | 插画区 1920x1760 @(120,120) r72
单词 Baloo2 ExtraBold 320px #33322E 基线 y=2348 居中, 字距 -2px
徽章 520x260 @(820,2420) r130 #FF7A45, 白字 160px 居中
"""
import sys
from PIL import Image, ImageDraw, ImageFont

W, H = 2160, 2880
CARD_R = 96
PANEL = (120, 120, 2040, 1880)  # l, t, r, b
PANEL_R = 72
CARD_BG = (0xFF, 0xF9, 0xF0)
INK = (0x33, 0x32, 0x2E)
ORANGE = (0xFF, 0x7A, 0x45)
BASELINE_Y = 2348
WORD_SIZE = 320
BADGE = (820, 2420, 820 + 520, 2420 + 260)
BADGE_R = 130
BADGE_TEXT_SIZE = 160
LETTER_SPACING = -2  # 2x 下对应 1x 的 -1px

FONT_PATH = "assets/fonts/baloo2-extrabold.ttf"
FONT_BOLD_PATH = "assets/fonts/baloo2-bold.ttf"


def load_font(size, bold=False):
    import os
    path = FONT_BOLD_PATH if bold and os.path.exists(FONT_BOLD_PATH) else FONT_PATH
    return ImageFont.truetype(path, size)


def remove_watermark(img):
    """右下角 'AI生成' 水印：用同图左侧的纯底纹补丁盖住，保留纸纹质感。"""
    w, h = img.size
    box_l, box_t = w - 320, h - 115
    patch = img.crop((box_l - 320, box_t, box_l, h))  # 左侧同高度纯背景
    img.paste(patch, (box_l, box_t))
    return img


def cover_crop(img, tw, th):
    """铺满裁切，竖直方向居中略偏上（保主体）。"""
    w, h = img.size
    scale = max(tw / w, th / h)
    nw, nh = round(w * scale), round(h * scale)
    img = img.resize((nw, nh), Image.LANCZOS)
    x = (nw - tw) // 2
    y = (nh - th) // 3  # 偏上裁切，避免切掉主体底部
    return img.crop((x, y, x + tw, y + th))


def rounded_mask(size, radius):
    m = Image.new("L", size, 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, size[0] - 1, size[1] - 1], radius=radius, fill=255)
    return m


def draw_tracked(draw, pos, text, font, fill, anchor_x="center"):
    """带字距的文字绘制，返回实际 ink 宽度。"""
    widths = []
    for ch in text:
        bb = draw.textbbox((0, 0), ch, font=font)
        widths.append(bb[2] - bb[0])
    total = sum(widths) + LETTER_SPACING * (len(text) - 1)
    x = pos[0] - total / 2 if anchor_x == "center" else pos[0]
    for ch, cw in zip(text, widths):
        bb = draw.textbbox((0, 0), ch, font=font)
        draw.text((x - bb[0], pos[1]), ch, font=font, fill=fill, anchor="ls")
        x += cw + LETTER_SPACING
    return total


def main(word, illus_path):
    img = Image.open(illus_path).convert("RGB")
    img = remove_watermark(img)
    panel_img = cover_crop(img, PANEL[2] - PANEL[0], PANEL[3] - PANEL[1])

    card = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(card)
    d.rounded_rectangle([0, 0, W - 1, H - 1], radius=CARD_R, fill=CARD_BG + (255,))

    # 插画区
    mask = rounded_mask(panel_img.size, PANEL_R)
    card.paste(panel_img, (PANEL[0], PANEL[1]), mask)

    # 单词（基线对齐，水平居中）
    f_word = load_font(WORD_SIZE)
    draw_tracked(d, (W // 2, BASELINE_Y), word, f_word, INK)

    # 徽章
    d.rounded_rectangle(list(BADGE), radius=BADGE_R, fill=ORANGE + (255,))
    f_badge = load_font(BADGE_TEXT_SIZE, bold=True)
    bbox = d.textbbox((0, 0), word and "Ee", font=f_badge)  # 文本由参数外固定为 B 列
    d.text(((BADGE[0] + BADGE[2]) / 2, (BADGE[1] + BADGE[3]) / 2), sys.argv[3] if len(sys.argv) > 3 else "Ee",
           font=f_badge, fill=(255, 255, 255, 255), anchor="mm")

    out = f"card-exports/单词卡-{word}.png"
    card.save(out)
    print("saved", out, card.size)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
