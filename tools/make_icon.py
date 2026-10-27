#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成「公子输入法」图标：PNG 预览 + 多尺寸 ICO。

形象沿用原始手绘：圆脸 + Z 形主体 + 右上角简笔猫。
新增一条候选条（三个小圆点），点出「输入法」这个用途。

坐标系固定为 320×320，先按 SS 倍超采样绘制再缩到目标尺寸，
避免小尺寸锯齿。
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

BASE = 320          # 设计坐标系边长
SS = 4              # 超采样倍数
W = BASE * SS       # 实际绘制画布边长

# 配色
LIGHT = {"bg": (255, 255, 255, 255), "ink": (26, 26, 26, 255), "dot": (55, 138, 221, 255)}
DARK = {"bg": (28, 28, 27, 255), "ink": (255, 255, 255, 255), "dot": (93, 202, 165, 255)}


def s(v: float) -> float:
    """设计坐标 → 绘制坐标。"""
    return v * SS


def quad(p0, p1, p2, n: int = 14):
    """二次贝塞尔采样，用来画眉毛的弧度（Pillow 没有曲线原语）。

    采样点不能太密：`joint="curve"` 在密集点上会叠出毛刺，14 段足够平滑。
    """
    pts = []
    for i in range(n + 1):
        t = i / n
        u = 1 - t
        pts.append((
            u * u * p0[0] + 2 * u * t * p1[0] + t * t * p2[0],
            u * u * p0[1] + 2 * u * t * p1[1] + t * t * p2[1],
        ))
    return pts


def stroke(draw: ImageDraw.ImageDraw, pts, color, width: float) -> None:
    """带圆头的折线：线体 + 两端补圆点。"""
    w = s(width)
    scaled = [(s(x), s(y)) for x, y in pts]
    draw.line(scaled, fill=color, width=int(round(w)), joint="curve")
    r = w / 2
    for x, y in (scaled[0], scaled[-1]):
        draw.ellipse([x - r, y - r, x + r, y + r], fill=color)


def dot(draw, cx, cy, r, color):
    draw.ellipse([s(cx - r), s(cy - r), s(cx + r), s(cy + r)], fill=color)


def draw_icon(palette: dict) -> Image.Image:
    img = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    ink, dotc = palette["ink"], palette["dot"]

    # 圆底
    d.ellipse([s(18), s(18), s(302), s(302)], fill=palette["bg"])

    # 左眉
    stroke(d, quad((100, 80), (120, 62), (142, 74)), ink, 9)
    # 右眉（同时是 Z 的上横）
    stroke(d, quad((146, 82), (180, 78), (200, 108)), ink, 9)
    # Z 的斜杠
    stroke(d, [(200, 108), (115, 180)], ink, 9)
    # Z 的下横
    stroke(d, [(115, 180), (196, 180)], ink, 9)

    # 眼睛
    dot(d, 116, 114, 8, ink)
    dot(d, 180, 107, 8, ink)

    # 候选条：三个小点 = 候选列表，第一个高亮 = 当前选中
    d.rounded_rectangle(
        [s(88), s(198), s(218), s(228)],
        radius=s(15), outline=ink, width=int(round(s(6))),
    )
    dot(d, 116, 213, 5, dotc)
    dot(d, 142, 213, 5, ink)
    dot(d, 168, 213, 5, ink)

    # 猫：头 + 两只尖耳 + 眼睛 + 尾巴。整体收在圆内，避免白线落到透明区看不见。
    # 线宽要比脸细一档（5 vs 9），否则圆头内径被线宽吃掉，看上去像实心白球。
    d.ellipse([s(210), s(68), s(242), s(100)], outline=ink, width=int(round(s(5))))
    stroke(d, [(214, 74), (216, 56), (228, 70)], ink, 5)
    stroke(d, [(232, 68), (242, 54), (248, 70)], ink, 5)
    dot(d, 220, 84, 2.8, ink)
    dot(d, 234, 84, 2.8, ink)
    stroke(d, quad((242, 90), (256, 90), (250, 70)), ink, 5)

    return img.resize((BASE, BASE), Image.LANCZOS)


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    out = root / "assets"
    out.mkdir(parents=True, exist_ok=True)

    sizes = [16, 24, 32, 48, 64, 128, 256]
    for name, palette in (("light", LIGHT), ("dark", DARK)):
        big = draw_icon(palette)
        # 1024 预览图
        big.resize((1024, 1024), Image.LANCZOS).save(out / f"icon-{name}.png")
        # 多尺寸 ico
        frames = [big.resize((n, n), Image.LANCZOS) for n in sizes]
        frames[-1].save(
            out / f"icon-{name}.ico",
            format="ICO",
            sizes=[(n, n) for n in sizes],
            append_images=frames[:-1],
        )
        print(f"已生成 icon-{name}.png / icon-{name}.ico")

    # 语言栏用的主图标：深色版在小尺寸下对比度更好
    (out / "icon-dark.ico").replace(out / "gongzi.ico")
    (out / "icon-dark.png").replace(out / "gongzi.png")
    print("主图标：assets/gongzi.ico + assets/gongzi.png")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
