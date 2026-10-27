#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把词桥的 82 个 Lua 分片转成清风输入法（WindInput）能直接吃的注释词库。

输入：rime/lua/wb_shards/*.lua
  格式：["中文词"] = "释义~音标!等级 / 释义~音标!等级"

输出：data/wordbridge_comment.dict.yaml
  头部必须同时声明 text 与 comment 两列，清风才会把它认作注释源
  （判定见 wind-reverse::declares_comment_column）。

注释只做展示、不参与召回，所以 weight 一律给 0，不占候选位。
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ENTRY_RE = re.compile(r'^\s*\["(.*?)"\]\s*=\s*"(.*)"\s*,?\s*$')
UNESCAPE = {"\\": "\\", '"': '"', "n": "\n", "t": "\t", "r": "\r"}


def lua_unescape(s: str) -> str:
    """还原 Lua 字符串里的转义序列（数据里只有 75 行含转义，但不能漏）。"""
    if "\\" not in s:
        return s
    out, i = [], 0
    while i < len(s):
        ch = s[i]
        if ch == "\\" and i + 1 < len(s):
            nxt = s[i + 1]
            out.append(UNESCAPE.get(nxt, nxt))
            i += 2
        else:
            out.append(ch)
            i += 1
    return "".join(out)


def build_comment(value: str) -> str:
    """把词桥的义项串压成一条候选注释。

    词桥默认 show_glosses: 1，只展示最贴切的那一个义项，这里取第一个。
    输出形如：computer /kəmˈpjuːtə/ 〔高考〕
    """
    first = value.split(" / ", 1)[0].strip()
    if not first:
        return ""

    level = ""
    if "!" in first:
        first, level = first.rsplit("!", 1)
        level = level.strip()

    ipa = ""
    if "~" in first:
        first, ipa = first.rsplit("~", 1)
        ipa = ipa.strip()

    gloss = first.strip()
    if not gloss:
        return ""

    parts = [gloss]
    if ipa:
        parts.append(f"/{ipa}/")
    if level:
        parts.append(f"〔{level}〕")
    return " ".join(parts)


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    if src is None:
        src = Path(
            r"C:\Users\Administrator\.zcode\workspace"
            r"\draft-29ed19cd-f7d9-405f-9ec9-e7b4ccd637c0\wordbridge\rime\lua\wb_shards"
        )
    if not src.is_dir():
        print(f"[!] 分片目录不存在: {src}", file=sys.stderr)
        return 1

    shards = sorted(src.glob("*.lua"))
    if not shards:
        print(f"[!] 目录里没有 .lua 分片: {src}", file=sys.stderr)
        return 1

    # 用 dict 去重：同一词可能在多个分片出现，先到的胜出（分片按文件名排序，稳定）
    table: dict[str, str] = {}
    parsed = skipped = 0

    for shard in shards:
        for line in shard.read_text(encoding="utf-8").splitlines():
            m = ENTRY_RE.match(line)
            if not m:
                continue
            parsed += 1
            word = lua_unescape(m.group(1))
            comment = build_comment(lua_unescape(m.group(2)))
            if not word or not comment:
                skipped += 1
                continue
            table.setdefault(word, comment)

    out = root / "data" / "wordbridge_comment.dict.yaml"
    out.parent.mkdir(parents=True, exist_ok=True)

    with out.open("w", encoding="utf-8", newline="\n") as f:
        f.write("# 词桥 WordBridge · 候选英文注释库\n")
        f.write("# 由 tools/build_comment_dict.py 自动生成，请勿手改\n")
        f.write("# 数据来源：CC-CEDICT (CC-BY-SA 4.0) + ECDICT (MIT)\n")
        f.write("---\n")
        f.write("name: wordbridge_comment\n")
        f.write('version: "1.0"\n')
        f.write("columns:\n")
        f.write("  - text\n")
        f.write("  - comment\n")
        f.write("...\n")
        for word in sorted(table):
            comment = table[word].replace("\t", " ").replace("\n", " ")
            f.write(f"{word}\t{comment}\n")

    size_mb = out.stat().st_size / 1024 / 1024
    print(f"分片数      : {len(shards)}")
    print(f"解析条目    : {parsed}")
    print(f"跳过(无注释): {skipped}")
    print(f"去重后词条  : {len(table)}")
    print(f"输出        : {out}")
    print(f"体积        : {size_mb:.2f} MB")

    print("\n--- 抽样 ---")
    for w in ("电脑", "学习", "苹果", "米", "你", "一"):
        if w in table:
            print(f"  {w}\t{table[w]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
