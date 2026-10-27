#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成「公子输入法」图标：PNG 预览 + 多尺寸 ICO。

风格：极简线描（line art）。
  - 单一线宽，圆头圆角，不用任何填充色块
  - 白底纯黑线，留白充足，内容约占直径的一半
  - 曲线用三次贝塞尔，避免折线感

形象：圆脸 + 两眉 + 两点眼 + Z 形主体。不加任何附加装饰——
        输入法的含义靠「这是谁」而不是靠画个键盘来讲。
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

BASE = 320          # 设计坐标系边长
SS = 5              # 超采样倍数
W = BASE * SS       # 实际绘制画布边长

# 线宽与尺寸（设计坐标系单位）
STROKE = 10.0
EYE_R = 8.0
RING_W = 2.0

# 配色：白底黑线为主，深色版备用
LIGHT = {"bg": (255, 255, 255, 255), "ink": (10, 10, 10, 255), "ring": (232, 232, 232, 255)}
DARK = {"bg": (24, 24, 23, 255), "ink": (250, 250, 249, 255), "ring": (58, 58, 56, 255)}


def s(v: float) -> float:
    """设计坐标 → 绘制坐标。"""
    return v * SS


def cubic(p0, p1, p2, p3, n: int = 24):
    """三次贝塞尔采样。

    采样点不能太密：`joint="curve"` 在密集点上会叠出毛刺，24 段足够平滑。
    """
    pts = []
    for i in range(n + 1):
        t = i / n
        u = 1 - t
        a, b, c, d = u * u * u, 3 * u * u * t, 3 * u * t * t, t * t * t
        pts.append((
            a * p0[0] + b * p1[0] + c * p2[0] + d * p3[0],
            a * p0[1] + b * p1[1] + c * p2[1] + d * p3[1],
        ))
    return pts


def stroke(draw: ImageDraw.ImageDraw, pts, color, width: float = STROKE) -> None:
    """带圆头的折线：线体 + 两端补圆点（Pillow 的 line 没有 round cap）。"""
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
    ink, ring = palette["ink"], palette["ring"]

    # 圆底 + 极淡描边
    d.ellipse([s(17), s(17), s(303), s(303)], fill=palette["bg"])
    d.ellipse(
        [s(17), s(17), s(303), s(303)],
        outline=ring, width=int(round(s(RING_W))),
    )

    # 左眉：独立一段短弧，上凸
    stroke(d, cubic((92, 122), (110, 100), (136, 99), (148, 108)), ink)
    # 右眉：长弧，先平后缓降。末端刻意压低一点，
    # 让「眉梢 → 斜杠」的转折接近 120°，折角才不会像箭头。
    stroke(d, cubic((162, 111), (192, 104), (224, 124), (233, 158)), ink)
    # Z 斜杠
    stroke(d, [(233, 158), (108, 208)], ink)
    # Z 底横
    stroke(d, [(108, 208), (208, 208)], ink)

    # 眼睛
    dot(d, 126, 146, EYE_R, ink)
    dot(d, 200, 139, EYE_R, ink)

    return img.resize((BASE, BASE), Image.LANCZOS)


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    out = root / "assets"
    out.mkdir(parents=True, exist_ok=True)

    sizes = [16, 24, 32, 48, 64, 128, 256]
    # 白底版就是主图标（与手绘原作一致），深色版另存备用
    for stem, palette in (("gongzi", LIGHT), ("icon-dark", DARK)):
        big = draw_icon(palette)
        big.resize((1024, 1024), Image.LANCZOS).save(out / f"{stem}.png")
        frames = [big.resize((n, n), Image.LANCZOS) for n in sizes]
        frames[-1].save(
            out / f"{stem}.ico",
            format="ICO",
            sizes=[(n, n) for n in sizes],
            append_images=frames[:-1],
        )
        print(f"已生成 {stem}.png / {stem}.ico")

    print("主图标：assets/gongzi.ico + assets/gongzi.png（白底版）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
