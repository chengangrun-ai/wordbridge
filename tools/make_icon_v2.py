#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把用户手绘的「公子举牌」图做成应用图标。

原图 1024×1024、纯黑白、内容占 78%。直接缩到 16px 会糊成一团黑块，
所以分两档处理：

  · 大尺寸（48 以上）—— LANCZOS 缩放，保留灰度抗锯齿，线条自然
  · 小尺寸（16/24/32）—— 缩放后**二值化**。黑白稿缩小时中间调会糊成灰雾，
    二值化把墨点重新压回纯黑，轮廓反而更清楚（代价是细节丢失，但这个尺寸
    本来也放不下细节）

底色用圆角方形白底：原图黑线在深色任务栏上会看不见，垫一层白底才稳。
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

SRC = Path(r"C:\Users\Administrator\Downloads\gongzi_icon_v2_rounded_1024.png")
OUT = Path(__file__).resolve().parent.parent / "assets"

SIZES = [16, 24, 32, 48, 64, 128, 256]

CANVAS = 1024          # 母版画布
MARGIN_RATIO = 0.08    # 内容四周留白比例
RADIUS_RATIO = 0.22    # 圆角半径 / 边长


def load_content() -> Image.Image:
    """读原图 → 裁到内容边界 → 转成带 alpha 的白底图。"""
    img = Image.open(SRC).convert("L")
    a = np.array(img)
    ys, xs = np.where(a < 200)
    box = (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1)
    return img.crop(box)


def make_master() -> Image.Image:
    content = load_content()
    canvas = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))

    # 圆角方形白底
    r = int(CANVAS * RADIUS_RATIO)
    ImageDraw.Draw(canvas).rounded_rectangle(
        [0, 0, CANVAS - 1, CANVAS - 1], radius=r, fill=(255, 255, 255, 255)
    )

    # 内容等比缩放到画布内
    inner = int(CANVAS * (1 - 2 * MARGIN_RATIO))
    w, h = content.size
    scale = min(inner / w, inner / h)
    nw, nh = max(1, int(w * scale)), max(1, int(h * scale))
    resized = content.resize((nw, nh), Image.LANCZOS)

    # 白底 → 黑线，其余透明（叠在白底上就是原样）
    rgba = Image.new("RGBA", (nw, nh), (255, 255, 255, 255))
    rgba.putalpha(255)
    gray = np.array(resized)
    # 让白保持白、黑保持黑，中间调保留（白底本身已铺好，这里只贴墨）
    ink = np.full((nh, nw, 4), 255, dtype=np.uint8)
    ink[..., 0] = gray
    ink[..., 1] = gray
    ink[..., 2] = gray
    ink[..., 3] = 255
    resized_rgba = Image.fromarray(ink, "RGBA")

    canvas.paste(resized_rgba, ((CANVAS - nw) // 2, (CANVAS - nh) // 2))
    return canvas


def draw_simple(size: int) -> Image.Image:
    """小尺寸专用简化版：只保留三个大形——头发、脸、两块牌子。

    原图有头发纹理、手指分缝、脸颊斜线、牌子上的字，16px 一个都放不下。
    与其硬缩成黑块，不如重新画：上部一团黑（头发）、中部白脸带两点眼、
    下部两个白块（牌子）。这个尺寸只要「看得出是个人举着两块牌」就够了。
    """
    S = size * 8          # 超采样，缩回去才不锯齿
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    # 圆角白底
    d.rounded_rectangle([0, 0, S - 1, S - 1], radius=int(S * 0.22), fill=(255, 255, 255, 255))
    # 头发：上半部的大黑块
    d.ellipse([S * 0.09, S * 0.04, S * 0.91, S * 0.64], fill=(0, 0, 0, 255))
    # 脸：白色椭圆压在上面
    d.ellipse([S * 0.19, S * 0.24, S * 0.81, S * 0.70], fill=(255, 255, 255, 255))
    # 两只闭着的眼
    r = S * 0.028
    for cx in (0.38, 0.62):
        d.ellipse([S * cx - r, S * 0.44 - r, S * cx + r, S * 0.44 + r], fill=(0, 0, 0, 255))
    # 两块牌子
    lw = int(S * 0.028)
    for x0, x1 in ((0.05, 0.47), (0.53, 0.95)):
        d.rounded_rectangle(
            [S * x0, S * 0.68, S * x1, S * 0.94],
            radius=int(S * 0.055),
            fill=(255, 255, 255, 255),
            outline=(0, 0, 0, 255),
            width=lw,
        )
    return img.resize((size, size), Image.LANCZOS)


def resize_one(master: Image.Image, size: int) -> Image.Image:
    # 32 及以下走重绘简化版：原图缩到这个尺寸只剩黑块
    if size <= 32:
        return draw_simple(size)
    return master.resize((size, size), Image.LANCZOS)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    master = make_master()
    master.save(OUT / "gongzi-v2.png")
    print(f"母版: gongzi-v2.png {master.size}")

    frames = [resize_one(master, n) for n in SIZES]
    frames[-1].save(
        OUT / "gongzi-v2.ico",
        format="ICO",
        sizes=[(n, n) for n in SIZES],
        append_images=frames[:-1],
    )
    print(f"图标: gongzi-v2.ico（{', '.join(map(str, SIZES))}）")

    # 16/32 单独导出，方便肉眼验收小尺寸效果
    for n in (16, 32):
        resize_one(master, n).resize((n * 8, n * 8), Image.NEAREST).save(
            OUT / f"_check-{n}.png"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
