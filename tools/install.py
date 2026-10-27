#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把词桥英文注释库装进清风输入法（Windows）。

做三件事，全程可回滚：
  1. 把 wordbridge_comment.dict.yaml 复制到 <数据目录>\\schemas\\comments\\
  2. 在 config.toml 里追加一条 [[ui.comment_dicts]]（幂等，重复跑不会重复加）
  3. 在 [ui.candidate] 段内设置注释模板为 ${dict}（只改这两个键，其余原样保留）

改 config.toml 之前一律先备份成 config.toml.bak-<时间戳>。
"""

from __future__ import annotations

import os
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

DICT_NAME = "wordbridge_comment.dict.yaml"
DICT_ID = "wordbridge"
DICT_LABEL = "词桥英文释义"
TEMPLATE = "${dict}"

# config.toml 里要保证存在的内容
COMMENT_DICT_BLOCK = f"""
[[ui.comment_dicts]]
id = "{DICT_ID}"
label = "{DICT_LABEL}"
path = "comments/{DICT_NAME}"
enabled = true
schemas = []
"""


def find_data_dir() -> Path:
    """清风 Windows 版用户数据目录：%APPDATA%\\WindInput。"""
    appdata = os.environ.get("APPDATA")
    if appdata:
        cand = Path(appdata) / "WindInput"
        if cand.is_dir():
            return cand
    # 便携版：程序目录下 userdata
    for base in (Path.home() / "AppData" / "Roaming",):
        cand = base / "WindInput"
        if cand.is_dir():
            return cand
    return Path(appdata or ".") / "WindInput"


def set_key_in_section(text: str, section: str, key: str, raw: str) -> str:
    """在 [section] 段内设置 key = <raw>，保留文件其余内容与顺序。

    raw 是已经序列化好的 TOML 右值（字符串要自带引号，数组写成 ["a","b"]）。
    段不存在时在文件末尾追加该段。段内已有该键则替换，没有则插到段首。
    """
    lines = text.splitlines()
    header = f"[{section}]"
    start = None
    for i, line in enumerate(lines):
        if line.strip() == header:
            start = i
            break

    new_line = f"{key} = {raw}"

    if start is None:
        # 段不存在：追加
        if lines and lines[-1].strip():
            lines.append("")
        lines.append(header)
        lines.append(new_line)
        return "\n".join(lines) + "\n"

    # 找段尾（下一个以 [ 开头的行）
    end = len(lines)
    for j in range(start + 1, len(lines)):
        if lines[j].lstrip().startswith("["):
            end = j
            break

    # 段内已有该键 → 替换
    for j in range(start + 1, end):
        if re.match(rf"\s*{re.escape(key)}\s*=", lines[j]):
            lines[j] = new_line
            return "\n".join(lines) + "\n"

    # 没有 → 插到段首之后
    lines.insert(start + 1, new_line)
    return "\n".join(lines) + "\n"


def ensure_pinyin_schema(text: str) -> str:
    """确保「全拼」方案被启用并设为当前方案。

    出厂 config 的 schema.available 只有 ["wubi86", "wubi86_pinyin"]，
    拼音方案（id = pinyin）虽然随安装包提供，却不在可用列表里，
    于是方案菜单里根本看不到它 —— 这是「只能用五笔」的直接原因。
    """
    # 读出已有的 available，保持原有方案不丢
    existing: list[str] = []
    m = re.search(r"^\s*available\s*=\s*\[(.*?)\]", text, re.M | re.S)
    if m:
        existing = re.findall(r'"([^"]+)"', m.group(1))

    ordered = ["pinyin"] + [s for s in existing if s != "pinyin"]
    raw = "[" + ", ".join(f'"{s}"' for s in ordered) + "]"

    text = set_key_in_section(text, "schema", "available", raw)
    text = set_key_in_section(text, "schema", "active", '"pinyin"')
    return text


def has_comment_dict(text: str) -> bool:
    """判断是否已经挂过词桥注释库（按 id 认，避免重复追加）。"""
    return re.search(rf'^\s*id\s*=\s*"{re.escape(DICT_ID)}"', text, re.M) is not None


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    src_dict = root / "data" / DICT_NAME
    if not src_dict.is_file():
        print(f"[!] 找不到注释库：{src_dict}", file=sys.stderr)
        print("    请先运行 tools/build_comment_dict.py 生成。", file=sys.stderr)
        return 1

    data_dir = find_data_dir()
    print(f"数据目录 : {data_dir}")
    if not data_dir.is_dir():
        print("[!] 数据目录不存在，请先安装并运行一次清风输入法。", file=sys.stderr)
        print(f"    期望位置：{data_dir}", file=sys.stderr)
        return 1

    # 1) 复制注释库
    comments_dir = data_dir / "schemas" / "comments"
    comments_dir.mkdir(parents=True, exist_ok=True)
    dst_dict = comments_dir / DICT_NAME
    shutil.copy2(src_dict, dst_dict)
    print(f"注释库   : 已写入 {dst_dict}")

    # 2) 改 config.toml
    cfg = data_dir / "config.toml"
    if not cfg.is_file():
        print(f"[!] 找不到 {cfg}，请先运行一次清风输入法让它生成配置。", file=sys.stderr)
        return 1

    original = cfg.read_text(encoding="utf-8")
    backup = cfg.with_suffix(f".toml.bak-{datetime.now():%Y%m%d-%H%M%S}")
    backup.write_text(original, encoding="utf-8")
    print(f"已备份   : {backup.name}")

    text = original
    if has_comment_dict(text):
        print("注释词库 : 已存在，跳过追加")
    else:
        if text and not text.endswith("\n"):
            text += "\n"
        text += COMMENT_DICT_BLOCK
        print("注释词库 : 已追加 [[ui.comment_dicts]]")

    text = set_key_in_section(text, "ui.candidate", "comment_template_vertical", f'"{TEMPLATE}"')
    text = set_key_in_section(text, "ui.candidate", "comment_template_horizontal", f'"{TEMPLATE}"')
    # 竖排：横排下每个候选都带一长串英文，窗口会撑到超出屏幕，第一个候选的释义被裁掉
    text = set_key_in_section(text, "ui.candidate", "layout", '"vertical"')
    print(f"注释模板 : 已设为 {TEMPLATE}（竖排）")

    text = ensure_pinyin_schema(text)
    print("输入方案 : 已启用「全拼」并设为当前方案")

    cfg.write_text(text, encoding="utf-8")

    print("\n完成。请重启输入法让配置生效：")
    print("  运行 wind_cli.bat restart，或注销后重新登录")
    print("\n验收：打 diannao，候选「电脑」右侧应出现")
    print("      computer /kəmˈpjuːtə/ 〔高考〕")
    print(f"\n想还原：把 {backup.name} 改名回 config.toml 即可。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
