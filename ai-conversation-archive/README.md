# ai-conversation-archive

将各 AI 平台（如 DeepSeek、ChatGPT、Kimi）的对话记录同步到本地，维护索引并产出原始 JSON 与摘要 MD。供 OpenClaw 等通过脚本执行批处理，浏览器抓取单则会话时需先下拉加载更早历史。

## 结构

- `SKILL.md`：技能说明与脚本用法
- `scripts/`：sync_index、run_tasks、precheck_stale、summarize
- `references/`：database 结构、平台与配置示例
- `data/`：运行时生成（database.json、*_raw.json、*_abstract.md 等，已通过 .gitignore 排除）

## 使用

在技能根目录执行：

```bash
python scripts/sync_index.py
python scripts/run_tasks.py   # 或 --once
python scripts/precheck_stale.py --days 7
```

数据目录默认为本技能下的 `data/`；可在 `data/config.json` 中配置 `summary_command`。

## 安装到 OpenClaw

将本目录放到 OpenClaw 的 skills 目录下，例如：

`~/.openclaw/workspace/skills/ai-conversation-archive/`
