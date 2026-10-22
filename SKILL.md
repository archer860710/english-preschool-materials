---
name: english-preschool-materials
slug: english-preschool-materials
version: 1.0.1
displayName: 英语幼教素材批量生成器
summary: 一份 Excel 词表，批量生成 kawaii 英语单词闪卡与歌谣场景插图
author: archer860710
license: MIT
homepage: https://github.com/archer860710/english-preschool-materials
tags:
  - 单词卡
  - 闪卡
  - 英语启蒙
  - 幼教
  - chant
  - 场景插图
description: 英语幼教素材批量生成器（两条流水线）：① 单词闪卡——按 xlsx 三列（英文单词 / 重点字母 / 中文释义）批量生成 kawaii 扁平风插画单词卡并导出 PNG；② Chant 场景插图——按歌词生成横版多角色场景图，并把单词表中的词以橙色胶囊标注到图上。当用户提到：单词卡、闪卡、flashcard、英语单词卡、学龄前英语素材、chant、歌谣插图、场景配图时使用。适用于 WorkBuddy 等具备文生图能力的 Agent 环境，核心提示词模板与排版规格同样适用于任何 AI 生图工作流。
---

# 英语幼教素材 · 批量生成器（单词闪卡 + Chant 场景插图）

把一份简单的 Excel 词表，批量变成风格统一、可直接打印的 kawaii 英语单词闪卡和歌谣场景插图。

**两条流水线，一套素材体系：**

| | 流水线 A：单词闪卡 | 流水线 B：Chant 场景插图 |
|---|---|---|
| 数据源 | `单词.xlsx`（A 英文 / B 重点 / C 中文） | `Chant.xlsx`（A 歌词 / B 备注） |
| 产出 | 1080×1440 竖版卡 → `card-exports/` | 1536×1024 横版场景图 → `generated-images/chant/` |
| 画面 | 单一主体，禁止任何配角与场景 | 多角色场景（谁在床上 / 床下等） |
| 文字 | 单词 + 重点字母徽章 | 底图无字，后期合成单词胶囊标注 |

---

## 1. 快速开始

### 1.1 准备数据源

`单词.xlsx`（Sheet1）三列，第 1 行为表头：

| A 列：单词 | B 列：重点字母 | C 列：插画内容参考 |
|---|---|---|
| apple | Aa | 苹果 |
| cup | Cc | 茶杯 |

`Chant.xlsx`（Sheet1）两列：A 列歌词（一行一条），B 列备注（可选）。

### 1.2 目录结构（建议）

```
你的项目根/
├── 单词.xlsx
├── Chant.xlsx
├── assets/fonts/              # Baloo 2 字体（见 1.4）
├── scripts/                   # 合成脚本（见 §6）
├── generated-images/          # 生图原图与 subject-* 角色底图
│   └── chant/                 # Chant 场景图
└── card-exports/              # 成品卡片 PNG
```

### 1.3 能力要求

- **文生图**：需要能按提示词生成图片的工具（WorkBuddy 的 ImageGen、或其他任何文生图服务）。提示词模板见 §4，为通用英文提示词
- **图像合成**：Python 3.x + Pillow（本地合成卡片、后期标注单词）
- **读表**：Python + openpyxl（读取 xlsx）

### 1.4 字体

- 英文：**Baloo 2 ExtraBold**（`assets/fonts/baloo2-extrabold.ttf`）
- 获取：从 Google Fonts 下载 Baloo 2 的 TTF。若网络受限，可用旧版 Android User-Agent 请求 `fonts.googleapis.com/css2` API，可拿到直链 TTF（现代 UA 只返回 woff2）
- 中文备用：Sarasa Gothic SC Bold（本流程默认不上中文）

---

## 2. 硬性原则（不可违反）

1. **中文释义绝不印上卡片**——C 列只用于让 AI 理解「画什么」。有些英文单词对应多个中文意思，卡片只放主体物。
2. **A 列、B 列内容严禁修改**——卡片上的单词必须逐字符照抄 A 列，徽章文字逐字符照抄 B 列。**严禁根据 C 列（或语义推断）反向扩写 A 列**。例：A 列 `cup`、C 列「茶杯」→ 卡上只能印 `cup`，绝不能写成 `teacup`。插画内容才跟着 C 列语义走。
3. **插画面只出现 C 列内容本身**，禁止任何无关配角（草地、地面、阴影、太阳、云、蝴蝶、花、场景、文字、字母、水印）。
4. **画风锁定**：kawaii 扁平矢量绘本风，无描边，纯色圆润色块，主体带 dot eyes + smile + blush cheeks，纯色暖底。
5. **批量前先确认数量与消耗**——逐张生图有成本（按所用服务计），先报「X 张、约 Y 额度」，经确认再开跑。
6. **单词标注判定（流水线 B）**：主体出现在 `单词.xlsx` A 列 → 必须标注英文单词；不在 A 列 → 严禁标注。

---

## 3. 配色与字体规格

**配色（≤4 角色）：**

| 角色 | 色值 | 用途 |
|---|---|---|
| 主导 | `#FFF9F0` | 卡片底色（奶白） |
| 次主 | — | 插画区暖底（由生图提示词自带 cream background） |
| 强调 | `#FF7A45` | Aa 徽章 / Chant 单词胶囊（暖橙） |
| 墨色 | `#33322E` | 单词文字 |

**字体（≤2 族）：** Baloo 2（ExtraBold / Bold），正文字号底线 ≥28px。

---

## 4. 生图提示词模板

### 4.1 单词卡主体（固定结构，替换 [主体物]）

```
Kawaii children's picture-book flat vector illustration of ONE single
cute smiling [主体物] with [必要细节], simple happy face with dot eyes
and smile, soft blush cheeks, solid flat colors, simple rounded shapes,
plain solid soft cream background, the [主体物] is the only object in
the image, centered, absolutely no grass, no ground, no shadow, no sun,
no clouds, no butterfly, no flowers, no other objects, no text, no
letters, no words, no watermark.
```

主体细节用 B 列信息补充（如 B 列 `Aa` → 主体是字母 A + 字母 a；`apple-red` → 红色苹果）。**A 列、C 列不要拼进提示词**，C 列只用来挑主体。

### 4.2 ⚠️ 身体部位类主体的坑

arm / hand / leg 类主体极易跑成「描边 + 张嘴露齿」风格，提示词必须显式加：

```
solid flat colors with absolutely no outline, no border, no stroke,
no contour line, small closed smile curve, no teeth, no open mouth
```

### 4.3 Chant 场景图（image-to-image）

- 从 `generated-images/subject-<word>.png` 挑出歌词中的角色作为参考图（最多 3 张 + 高保真参数），第 4 个角色用文字描述
- 提示词 = §4.1 的画风锁定词 + 场景化改写（谁在床上 / 床下），保留「纯色奶油底、无多余配角、no text」硬约束
- 尺寸 1536×1024 横版

---

## 5. 排版规格（单词卡 P02 主体英雄式）

| 元素 | 规格 |
|---|---|
| 画布 | 1080 × 1440 圆角 48，底色 `#FFF9F0` |
| 插画区 | 960 × 880 @ (60, 60)，圆角 36，图片填充（生图用 1024×1024，画面填满裁切） |
| 单词（A 列） | Baloo 2 ExtraBold 160px，`#33322E`，居中 @ y=1000，字距 -1px |
| 重点徽章（B 列） | 260 × 130 @ (410, 1210)，底色 `#FF7A45`，圆角 65，Baloo 2 Bold 80px 白字居中 |
| 中文 | **不放** |

---

## 6. 流水线 A：单词闪卡（每张标准步骤）

1. 生成主体插画（串行生成，一次一张，存 `generated-images/batch-<word>/`）
2. 出图后**逐张查看验证**内容与单词对应，再复制为 `generated-images/subject-<word>.png` 统一命名（这批图同时是流水线 B 的角色底图）
3. 合成卡片：`python scripts/card_compose.py <word> <illus.png> <Aa>`
   - 输出 2160×2880（2x），落 `card-exports/单词卡-<word>.png`
   - 合成前自动抹除生图水印（若有，见 §8.1）
4. 每 10 张抽查 1 张成品

### 有画布 / 设计工具时的可选链路

若环境提供设计画布（如 WorkBuddy Ardot）：create_design（每卡独立文件）→ 上传图片资源 → 插入卡片 frame、插画 panel、单词 text、徽章 → 贴图 → 导出 PNG。排版参数同 §5。注意：**画布内直接生图易卡死占位图，生图务必走独立通道**。

---

## 7. 流水线 B：Chant 场景插图

1. 读取 `Chant.xlsx` A 列歌词（读前确认文件已保存，Excel 打开未保存会读到空表）
2. 按 §4.3 做 image-to-image 生成场景图，存 `generated-images/chant/`
3. **单词标注用脚本后期合成，底图保持无字**：
   `python scripts/chant_annotate_auto.py <scene.png>`
   - 自动定位主体（按颜色连通域做像素测量，**不能目测坐标**——曾因把缩略图坐标当原图坐标导致标注全偏）
   - 自动在纯背景区选胶囊位、引线避让
   - 橙色胶囊 `#FF7A45` + 白字 Baloo 2 ExtraBold
   - 产物：`<scene>-labeled.png`
4. 主体是否标注只看 `单词.xlsx` A 列（见 §2 第 6 条）

---

## 8. 踩坑备忘（每条都真实付出过成本）

### 8.1 生图水印

部分生图服务（如 WorkBuddy ImageGen）右下角自带「AI生成」水印，提示词 `no watermark` **拦不住**，裁切也不够（水印贴边）。处置：合成前用同图左侧同高度的**纯底纹补丁**盖住水印区（勿用平涂色块，纸纹底会留痕）。参考实现见 `scripts/card_compose.py` 的 `remove_watermark()`。

### 8.2 并行生图文件名碰撞

生图输出文件名常为「提示词前缀 + 秒级时间戳」。并行多张时同前缀同秒返回会**互相覆盖且难察觉**（曾导致 A 卡贴成 B 的图）。必守：

1. 每张图用独立 output_dir（如 `generated-images/batch-<word>/`）
2. 工具返回的文件路径标签可能不可信，唯一可信的是磁盘实际文件——`ls` 核对数量后**逐张查看验证**内容
3. 首选串行生成；要并行必须接受「少了就补」的成本
4. 内容有歧义（猫脸带帽檐、鸭子两张脸）宁可重生成也不硬凑——学龄前卡片必须一眼对应单词

### 8.3 其他

- 沙箱 / 脚本写盘可能是瞬态的，写完必须 `ls` 复核
- 生成结果跑偏（写实风 / 漏主体 / 添加配角）：单张最多重生成 1 次，仍不达标就停下调整提示词，不要继续烧额度
- 脚本统一用相对路径推导项目根（`BASE = dirname(dirname(abspath(__file__)))`），目录搬迁零改动

---

## 9. 脚本依赖清单

| 脚本 | 用途 | 依赖 |
|---|---|---|
| `scripts/card_compose.py` | 单词卡本地合成（含去水印） | Pillow |
| `scripts/chant_annotate_auto.py` | Chant 场景图单词胶囊标注 | Pillow、numpy |
| `scripts/chant_analyze.py` | 场景图主体定位分析 | Pillow、numpy |
| `scripts/chant_components.py` | 标注组件（胶囊 / 引线绘制） | Pillow |
| `assets/fonts/baloo2-extrabold.ttf` | 标注与卡片文字字体 | — |

> 若发布包未随附字体与示例图（部分技能平台不接受二进制资源文件），按 §1.4 自行获取字体即可；脚本参数与全部规格都在本文档内，可从零实现。

---

## 10. 设计要点回顾（为什么这么定）

- **画面极简**：学龄前儿童注意力有限，卡片上主体唯一、无干扰元素，才能一眼建立「图 ↔ 单词」关联
- **中文不上卡**：避免母语依赖，也规避多义词歧义
- **Aa 徽章**：字母大小写认知是幼教核心诉求，暖橙胶囊是全卡唯一强调色
- **同一套角色底图**：单词卡与场景图复用 `subject-*.png`，保证同一单词在不同素材里形象一致
