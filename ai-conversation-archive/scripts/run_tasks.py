#!/usr/bin/env python3
"""
Process pending/updating records: fetch conversation, save JSON, generate summary MD, update index and log.
For platforms without API, prints REQUIRES_BROWSER_FETCH so agent can save JSON and re-run.
"""
import argparse
import json
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
from config import (
    get_data_dir,
    get_summary_command,
    ensure_data_dir,
    get_action_log_path,
    raw_json_basename,
    abstract_md_basename,
)
from db import load_db, save_db, find_by_global_id


def iso_now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def log_action(task_type: str, global_id: str, session_id: str, platform: str, status: str, err: str = "", duration_sec: float = 0):
    ensure_data_dir()
    line = f"[{iso_now()}] [{task_type}] {global_id} {session_id} {platform} {status}"
    if err:
        line += f" {err}"
    if duration_sec:
        line += f" {duration_sec:.2f}s"
    line += "\n"
    with open(get_action_log_path(), "a", encoding="utf-8") as f:
        f.write(line)


def parse_md_for_abstract_and_tags(md_path: Path) -> tuple[str, str]:
    """Extract session_abstract and session_tags from generated .md. Convention: first line or ## 摘要; 标签: x,y,z or ## 标签."""
    text = md_path.read_text(encoding="utf-8")
    abstract = ""
    tags = ""
    lines = [ln.strip() for ln in text.strip().split("\n")]
    for i, line in enumerate(lines):
        if line.startswith("## 摘要") or line.startswith("## 总结"):
            abstract = "\n".join(lines[i + 1 : i + 6]).strip()[:500]
            break
    if not abstract and lines:
        abstract = lines[0].lstrip("#").strip()[:500]
    tag_match = re.search(r"标签[：:]\s*(.+)", text) or re.search(r"## 标签\s*\n(.+)", text, re.MULTILINE)
    if tag_match:
        tags = re.sub(r"\s+", ",", tag_match.group(1).strip()).strip()[:200]
    return abstract, tags


def run_summary(input_json: Path, output_md: Path) -> bool:
    cmd_tpl = get_summary_command()
    if cmd_tpl:
        cmd = cmd_tpl.format(input_json=str(input_json), output_md=str(output_md))
        try:
            subprocess.run(cmd, shell=True, check=True, timeout=120, cwd=str(input_json.parent))
            return True
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            return False
    # Fallback: write minimal .md so index can be updated
    output_md.write_text(
        f"# 摘要\n\n（未配置 summary_command，请于 data/config.json 中配置 summary_command 或由总结 skill 生成）\n\n标签: \n",
        encoding="utf-8",
    )
    return True


def get_conversation_via_api(platform: str, session_id: str, data_dir: Path) -> tuple[dict | None, str]:
    """Fetch full conversation via platform API. Returns (payload, error_message). None payload = need browser."""
    # Placeholder: no API implemented here; config could wire to platform adapters.
    return None, "REQUIRES_BROWSER_FETCH"


def process_one(rec: dict, data_dir: Path) -> bool:
    """Process one record: fetch/save JSON, run summary, update index. Returns True if done, False if needs browser."""
    global_id = rec["global_session_id"]
    session_id = rec["session_id"]
    platform = rec["session_sourceplatform"]
    json_path = data_dir / raw_json_basename(platform, session_id)
    md_path = data_dir / abstract_md_basename(platform, session_id)
    is_initial = rec["session_status"] == "pending"
    task_type = "初次抓取" if is_initial else "增量更新"
    start = time.perf_counter()
    # Lock
    records = load_db()
    idx, r = find_by_global_id(records, global_id)
    if idx is None or r["session_status"] not in ("pending", "updating"):
        return True
    records[idx]["session_status"] = "updating"
    save_db(records)
    # Fetch conversation: API or existing JSON (e.g. saved by agent after browser fetch)
    payload, err = get_conversation_via_api(platform, session_id, data_dir)
    payload_from_file = False
    if payload is None and json_path.exists():
        try:
            payload = json.loads(json_path.read_text(encoding="utf-8"))
            payload_from_file = True
        except Exception:
            payload = None
    if payload is None:
        if "REQUIRES_BROWSER_FETCH" in err:
            print(f"REQUIRES_BROWSER_FETCH {global_id} {session_id} {platform}")
            print(f"SAVE_AS_JSON {json_path.name}")
            log_action(task_type, global_id, session_id, platform, "REQUIRES_BROWSER_FETCH", err, time.perf_counter() - start)
            records = load_db()
            idx, _ = find_by_global_id(records, global_id)
            if idx is not None:
                records[idx]["session_status"] = "pending"
                save_db(records)
            return False
        log_action(task_type, global_id, session_id, platform, "FAIL", err or "no payload", time.perf_counter() - start)
        records = load_db()
        idx, _ = find_by_global_id(records, global_id)
        if idx is not None:
            records[idx]["session_status"] = "pending"
            save_db(records)
        return True
    # Merge if incremental (only when payload came from API, not from existing file)
    last_ts = payload.get("last_message_timestamp", "")
    if not is_initial and json_path.exists() and not payload_from_file:
        try:
            old = json.loads(json_path.read_text(encoding="utf-8"))
            old_msgs = old.get("messages", [])
            new_msgs = payload.get("messages", [])
            old_ts = old.get("last_message_timestamp", "")
            seen = {id(m) for m in old_msgs}
            for m in new_msgs:
                if id(m) not in seen:
                    old_msgs.append(m)
                    seen.add(id(m))
            payload["messages"] = old_msgs
            payload["last_message_timestamp"] = last_ts or old_ts
        except Exception as e:
            log_action(task_type, global_id, session_id, platform, "FAIL", str(e), time.perf_counter() - start)
            records = load_db()
            idx, _ = find_by_global_id(records, global_id)
            if idx is not None:
                records[idx]["session_status"] = "updating"
                save_db(records)
            return True
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    if not run_summary(json_path, md_path):
        log_action(task_type, global_id, session_id, platform, "FAIL", "summary_command failed", time.perf_counter() - start)
        records = load_db()
        idx, _ = find_by_global_id(records, global_id)
        if idx is not None:
            records[idx]["session_status"] = "updating"
            save_db(records)
        return True
    abstract, tags = parse_md_for_abstract_and_tags(md_path)
    records = load_db()
    idx, r = find_by_global_id(records, global_id)
    if idx is None:
        return True
    r = records[idx]
    r["session_status"] = "completed"
    r["session_abstract"] = abstract
    r["session_tags"] = tags
    r["update_date"] = iso_now()
    r["last_message_timestamp"] = last_ts
    if is_initial:
        r["update_num"] = 0
    else:
        r["update_num"] = r.get("update_num", 0) + 1
    save_db(records)
    log_action(task_type, global_id, session_id, platform, "SUCCESS", "", time.perf_counter() - start)
    print(f"[SUCCESS] [{task_type}] platform: {platform}, global_id: {global_id}, original_id: {session_id}")
    return True


def main():
    ap = argparse.ArgumentParser(description="Process pending/updating sessions until none left (or --once)")
    ap.add_argument("--data-dir", type=Path, default=None, help="Data directory")
    ap.add_argument("--once", action="store_true", help="Process only one task then exit")
    args = ap.parse_args()
    if args.data_dir is not None:
        import os
        os.environ["AI_ARCHIVE_DATA_DIR"] = str(args.data_dir.resolve())
    get_data_dir()
    ensure_data_dir()
    records = load_db()
    todo = [r for r in records if r.get("session_status") in ("pending", "updating")]
    if not todo:
        print("No pending or updating tasks.")
        return 0
    data_dir = get_data_dir()
    n = 0
    for r in todo:
        if args.once and n >= 1:
            break
        ok = process_one(r, data_dir)
        if ok:
            n += 1
        else:
            print("One task requires browser fetch; save JSON and re-run run_tasks.")
            return 0
    print(f"Processed {n} task(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
