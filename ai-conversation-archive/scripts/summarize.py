#!/usr/bin/env python3
"""
生成会话摘要 .md：从 _raw.json 读出对话，写出 _abstract.md（含 ## 摘要、标签:）。
供 data/config.json 的 summary_command 调用，或直接运行。
"""
import argparse
import json
from pathlib import Path


def main():
    ap = argparse.ArgumentParser(description="Generate abstract .md from conversation _raw.json")
    ap.add_argument("--input", required=True, help="Path to *_raw.json")
    ap.add_argument("--output", required=True, help="Path to *_abstract.md")
    args = ap.parse_args()
    inp = Path(args.input)
    out = Path(args.output)
    if not inp.exists():
        raise SystemExit(f"Input file not found: {inp}")
    with open(inp, "r", encoding="utf-8") as f:
        data = json.load(f)
    messages = data.get("messages", [])
    title = data.get("session_title", "").strip() or "会话摘要"
    if not title and messages:
        for m in messages:
            if m.get("role") == "user":
                content = (m.get("content") or "").strip()
                title = content[:80] + ("..." if len(content) > 80 else "") if content else "会话摘要"
                break
    if not title:
        title = "会话摘要"
    summary_parts = []
    for m in messages:
        if m.get("role") == "assistant":
            content = (m.get("content") or "").strip()
            if content:
                summary_parts.append(content[:400] + ("..." if len(content) > 400 else ""))
                break
    if not summary_parts:
        summary_parts.append(f"本对话共 {len(messages)} 条消息，暂无自动摘要。可在此处补充或由后续总结 skill 生成。")
    summary_text = "\n\n".join(summary_parts)
    md = f"# {title}\n\n## 摘要\n\n{summary_text}\n\n## 标签\n\n标签: \n"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(md, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
