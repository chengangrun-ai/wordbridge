#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""用组合法给词库里没有的词条生成英文注释。

背景：CC-CEDICT 是**词典**，只收固定词条，不收「我爱你」这类主谓短语。
但输入法候选里会出这类词（来自雾凇词库），于是候选右侧一片空白。

做法：把词条切成已知的最小单元（优先匹配长词），各自取英文第一义项，
按中文语序拼起来。中文的主谓宾顺序和英文基本一致，所以常用短语能拼对。

局限（必须知道）：
  · 语序颠倒的短语会翻错（「饭吃我」→ eat rice I）
  · 虚词（的/了/是/在）没有对应，直接丢掉
  · 成语、专名基本翻不对
所以生成的条目标记为「组合」，只作为兜底，不覆盖已有的词典释义。
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

# 这些虚词没有实义，组合时直接跳过
STOP = set("的了着过是在和与及或而就都也还又很太更最不没别被把给让对从向于以")

TO_PREFIX = re.compile(r"^to\s+", re.I)
PAREN = re.compile(r"[（(][^）)]*[）)]?")


def clean_gloss(comment: str) -> str:
    """从词库注释里取出可拼接的英文片段。

    注释形如 `you (informal, as opposed to courteous 您[nin2]) /juː/ 〔高考〕`。
    处理顺序有讲究：**先去括号**，否则括号里的 `/` 会被当成音标分隔符，
    截出 `cooked) rice` 这种半截字符串。
    """
    s = PAREN.sub("", comment)              # 去括号（含未闭合的残括号）
    s = s.split(" /", 1)[0]                 # 去音标
    s = s.split("〔", 1)[0]                  # 去等级标签
    s = s.split(";", 1)[0].strip()          # 只留第一个义项
    s = s.split(",", 1)[0].strip()
    s = TO_PREFIX.sub("", s)
    return s.strip(" ()（）,.;、")


def build_units(table: dict[str, str], max_len: int = 4) -> list[str]:
    """按长度降序排好的词表，切分时优先匹配长词。"""
    return sorted(table, key=len, reverse=True)


def segment(word: str, table: dict[str, str]) -> list[str] | None:
    """把词条切成已知单元。切不开返回 None。

    贪心最长匹配：先试 4 字、3 字…，命中就切走。
    虚词单独成段但会被跳过，保证「我的书」→ 我 / 的 / 书 能切出来。
    """
    out: list[str] = []
    i = 0
    n = len(word)
    while i < n:
        hit = None
        for size in range(min(4, n - i), 0, -1):
            piece = word[i:i + size]
            if piece in table:
                hit = piece
                break
        if hit is None:
            return None
        out.append(hit)
        i += len(hit)
    return out


def pick_gloss(word: str, unit: str, table: dict[str, str],
               ctx: dict[str, list[dict]]) -> str | None:
    """给一个单元选英文释义，优先用语境规则。

    ctx 来自词桥的 context.json：`{"米": [{"g": "meter", "t": ["一","二","三"]}, ...]}`。
    匹配方式是「整词里出现了某个触发词」——比如 `三米` 里出现了 `三`，
    于是 `米` 取 meter 而不是 rice。这比死取第一个义项准得多。
    """
    rules = ctx.get(unit)
    if rules:
        for rule in rules:
            for trigger in rule.get("t", []):
                if trigger and trigger in word and trigger != unit:
                    return rule["g"]
    base = table.get(unit)
    return clean_gloss(base) if base else None


def compose(word: str, table: dict[str, str], ctx: dict[str, list[dict]] | None = None) -> str | None:
    """生成组合释义。"""
    ctx = ctx or {}
    units = segment(word, table)
    if not units:
        return None

    parts: list[str] = []
    for u in units:
        if len(u) == 1 and u in STOP:
            continue
        g = pick_gloss(word, u, table, ctx)
        if not g:
            return None
        parts.append(g)

    if not parts:
        return None
    return " ".join(parts)


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    dict_path = root / "data" / "wordbridge_comment.dict.yaml"
    if not dict_path.is_file():
        print(f"[!] 找不到 {dict_path}", file=sys.stderr)
        return 1

    # 读现有词库
    table: dict[str, str] = {}
    for line in dict_path.read_text(encoding="utf-8").splitlines():
        if line.startswith("#") or "\t" not in line or line.startswith("---"):
            continue
        if line in ("...",) or line.startswith("name:") or line.startswith("version:"):
            continue
        parts = line.split("\t")
        if len(parts) >= 2:
            table[parts[0]] = parts[1]

    print(f"现有词条: {len(table)}")

    # 只做单字与双字表（组合的原子）
    atoms = {w: c for w, c in table.items() if len(w) <= 2}
    print(f"可用原子（≤2字）: {len(atoms)}")

    # 语境规则：词桥挖出来的 2348 词 / 2516 条
    ctx: dict[str, list[dict]] = {}
    ctx_path = Path(
        r"C:\Users\Administrator\.zcode\workspace"
        r"\draft-29ed19cd-f7d9-405f-9ec9-e7b4ccd637c0\wordbridge\tools\data\context.json"
    )
    if ctx_path.is_file():
        import json
        ctx = json.loads(ctx_path.read_text(encoding="utf-8"))
        total = sum(len(v) for v in ctx.values())
        print(f"语境规则: {len(ctx)} 词 / {total} 条")
    else:
        print("语境规则: 未找到 context.json，仅用第一义项")

    print("\n--- 组合效果 ---")
    for w in ("我爱你", "我爱", "我吃饭", "三米", "吃米饭", "开汽车", "一杯水", "打电话"):
        r = compose(w, atoms, ctx)
        print(f"  {w:6} → {r}" if r else f"  {w:6} → （切不开）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
