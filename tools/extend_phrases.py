#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""给输入法候选补「组合释义」兜底库。

为什么需要：CC-CEDICT 是词典，只收固定词条。输入法候选来自雾凇词库（62 万条），
其中 85% 在词典里没有——「我爱你」「我爱」这种主谓短语必然空白。

做法：把词条切成已知单元（优先长词），各自选英文义项，按中文语序拼。
选义项时**优先查语境规则**（词桥挖的 2529 条），所以「三米」得 three meter
而不是 three rice。

产出独立的 `wordbridge_composed.dict.yaml`，在配置里排在主库**后面**：
主库命中就用主库，查不到才落到这里，词典的精准释义永远不会被组合结果盖掉。
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

from compose_phrases import STOP, clean_gloss, segment

CN = re.compile(r"^[\u4e00-\u9fff]+$")

# 组合只做 2~4 字。5 字以上多是成语、俗语、专名，机械拼出来基本是错的，
# 与其给个错答案，不如留空。
MIN_LEN, MAX_LEN = 2, 4

# 词频门槛：低于这个数的词一天也用不上，不值得为它撑大词库
MIN_FREQ = 100


def load_context() -> dict[str, list[dict]]:
    base = Path(
        r"C:\Users\Administrator\.zcode\workspace"
        r"\draft-29ed19cd-f7d9-405f-9ec9-e7b4ccd637c0\wordbridge\tools"
    )
    merged: dict[str, list[dict]] = {}
    auto_p, manual_p = base / "data" / "context.json", base / "curated_context.json"
    auto = json.loads(auto_p.read_text(encoding="utf-8")) if auto_p.is_file() else {}
    manual = json.loads(manual_p.read_text(encoding="utf-8")) if manual_p.is_file() else {}
    for k in set(auto) | set(manual):
        # 人工校订的规则排前面，命中即用
        merged[k] = (manual.get(k) or []) + (auto.get(k) or [])
    return merged


def pick(word: str, unit: str, table: dict[str, str], ctx: dict[str, list[dict]]) -> str | None:
    for rule in ctx.get(unit, []):
        for t in rule.get("t", []):
            if t and t in word and t != unit:
                return rule["g"]
    base = table.get(unit)
    return clean_gloss(base) if base else None


def compose(word: str, table: dict[str, str], ctx: dict[str, list[dict]]) -> str | None:
    units = segment(word, table)
    if not units:
        return None
    parts = []
    for u in units:
        if len(u) == 1 and u in STOP:
            continue
        g = pick(word, u, table, ctx)
        if not g:
            return None
        parts.append(g)
    return " ".join(parts) if parts else None


def read_dict(path: Path) -> dict[str, str]:
    out = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if "\t" not in line or line.startswith("#"):
            continue
        p = line.split("\t")
        if len(p) >= 2:
            out[p[0]] = p[1]
    return out


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    main_dict = root / "data" / "wordbridge_comment.dict.yaml"
    if not main_dict.is_file():
        print(f"[!] 找不到主库 {main_dict}", file=sys.stderr)
        return 1

    table = read_dict(main_dict)
    atoms = {w: c for w, c in table.items() if len(w) <= 2}
    ctx = load_context()
    print(f"主库词条   : {len(table)}")
    print(f"可组合原子 : {len(atoms)}")
    print(f"语境规则   : {len(ctx)} 词 / {sum(len(v) for v in ctx.values())} 条")

    # 读雾凇词库：词 → 最大词频
    cn_dir = Path(
        r"C:\Cami chan\公子输入法\WindInput\data\schemas\pinyin\cn_dicts"
    )
    if not cn_dir.is_dir():
        print(f"[!] 找不到词库目录 {cn_dir}", file=sys.stderr)
        return 1

    freq: dict[str, int] = {}
    for f in cn_dir.glob("*.dict.yaml"):
        for line in f.read_text(encoding="utf-8", errors="ignore").splitlines():
            if not line or line.startswith("#"):
                continue
            p = line.split("\t")
            if len(p) < 3 or not CN.match(p[0]):
                continue
            w = p[0]
            if not (MIN_LEN <= len(w) <= MAX_LEN):
                continue
            try:
                n = int(p[2])
            except ValueError:
                continue
            if n > freq.get(w, -1):
                freq[w] = n
    print(f"候选词条   : {len(freq)}（{MIN_LEN}~{MAX_LEN} 字）")

    # 只补主库没有的，且词频达标的
    targets = [w for w, n in freq.items() if w not in table and n >= MIN_FREQ]
    targets.sort(key=lambda w: -freq[w])
    print(f"待组合     : {len(targets)}（词频 ≥ {MIN_FREQ}）")

    composed: dict[str, str] = {}
    fail = 0
    for w in targets:
        g = compose(w, atoms, ctx)
        if g:
            composed[w] = g
        else:
            fail += 1
    print(f"组合成功   : {len(composed)}")
    print(f"切不开     : {fail}")

    out = root / "data" / "wordbridge_composed.dict.yaml"
    with out.open("w", encoding="utf-8", newline="\n") as f:
        f.write("# 词桥 WordBridge · 组合释义兜底库\n")
        f.write("# 由 tools/extend_phrases.py 自动生成，请勿手改\n")
        f.write("# 用途：词典没有的词条（多为短语），按已知单元拼出英文\n")
        f.write("# 注意：机器拼合，准确率低于词典，仅供兜底\n")
        f.write("---\n")
        f.write("name: wordbridge_composed\n")
        f.write('version: "1.0"\n')
        f.write("columns:\n  - text\n  - comment\n...\n")
        for w in sorted(composed):
            f.write(f"{w}\t{composed[w]}\n")

    size = out.stat().st_size / 1024 / 1024
    print(f"\n输出       : {out}")
    print(f"体积       : {size:.2f} MB")

    print("\n--- 抽样 ---")
    for w in list(composed)[:12]:
        print(f"  {w:8} {composed[w]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
