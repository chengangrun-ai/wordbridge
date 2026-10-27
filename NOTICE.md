# NOTICE · 版权与第三方声明

## 本项目

词桥 WordBridge · 候选英文注释层
Copyright (C) 2026 陈港润

本项目以 GNU 通用公共许可证第 3 版或更高版本（GPL-3.0-or-later）发布，全文见 [LICENSE](LICENSE)。

本项目包含的内容：

- `tools/build_comment_dict.py` — 注释库构建脚本
- `tools/install.py`、`install-windows.bat` — 安装工具
- `data/wordbridge_comment.dict.yaml` — 由上述脚本生成的注释词库

## 底座项目

本项目运行在 [清风输入法 WindInput](https://github.com/huanfeng/WindInput) 之上。

- 项目地址：https://github.com/huanfeng/WindInput
- 版权：Copyright (C) huanfeng 及 WindInput 贡献者
- 许可：GPL-3.0-or-later（v0.127.0 之前为 MIT）
- 本项目未修改其引擎源码，仅以其公开的注释词库挂载机制（`[[ui.comment_dicts]]`）加载数据

清风输入法的 Rust 引擎、候选系统、自绘 UI 与主题体系是本项目得以成立的基础，
在此向原作者及所有贡献者致谢。

## 第三方数据

| 数据 | 来源 | 许可 |
|---|---|---|
| 中→英释义（109,054 条） | [CC-CEDICT](https://www.mdbg.net/chinese/dictionary?page=cc-cedict)（MDBG） | CC-BY-SA 4.0 |
| 英文音标、等级标签 | [ECDICT](https://github.com/skywind3000/ECDICT) | MIT |

`data/wordbridge_comment.dict.yaml` 作为上述数据的衍生作品，适用 CC-BY-SA 4.0，
与本项目的 GPL-3.0 并存；再分发该数据文件时须保留本节署名与许可声明。

## 商标

清风输入法、WindInput 为原项目名称。本项目与其无隶属关系，亦未获得其官方背书。
