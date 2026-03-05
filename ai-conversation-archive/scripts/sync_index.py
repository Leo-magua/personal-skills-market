#!/usr/bin/env python3
"""
Sync conversation list from platforms into database.json.
Reads list per platform from data/<platform>_list.json (or calls API if configured).
New sessions -> pending; existing with newer last_message_timestamp -> updating.
"""
import argparse
import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
from config import get_data_dir, load_config, get_database_path, ensure_data_dir
from db import load_db, save_db, find_by_platform_and_session_id


def iso_now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def fetch_platform_list(platform: str, data_dir: Path) -> list[dict]:
    """Get session list for one platform. Prefer list file data/<platform>_list.json."""
    list_path = data_dir / f"{platform}_list.json"
    if list_path.exists():
        with open(list_path, "r", encoding="utf-8") as f:
            return json.load(f)
    cfg = load_config()
    # Optional: call platform API via cfg["platforms"][platform]["list_api"]
    return []


def build_record(platform: str, raw: dict) -> dict:
    now = iso_now()
    return {
        "global_session_id": str(uuid.uuid4()),
        "session_id": str(raw.get("session_id", "")),
        "session_sourceplatform": platform,
        "session_title": str(raw.get("title", raw.get("session_title", ""))),
        "session_status": "pending",
        "update_num": 0,
        "session_abstract": "",
        "session_tags": "",
        "create_date": now,
        "update_date": now,
        "dateinfo": raw.get("dateinfo", ""),
        "last_message_timestamp": raw.get("last_message_timestamp", ""),
        "original_data_url": raw.get("original_data_url", ""),
    }


def main():
    ap = argparse.ArgumentParser(description="Sync platform session lists into database.json")
    ap.add_argument("--data-dir", type=Path, default=None, help="Data directory (default: skill data/)")
    ap.add_argument("--platform", type=str, default=None, help="Only sync this platform (default: all)")
    args = ap.parse_args()
    if args.data_dir is not None:
        import os
        os.environ["AI_ARCHIVE_DATA_DIR"] = str(args.data_dir.resolve())
    data_dir = get_data_dir()
    ensure_data_dir()
    cfg = load_config()
    platforms = cfg.get("platforms", {})
    if not platforms:
        # Default: discover from list files
        for f in data_dir.glob("*_list.json"):
            platforms[f.stem.replace("_list", "")] = {}
    if args.platform:
        platforms = {k: v for k, v in platforms.items() if k == args.platform}
    if not platforms:
        platforms = {"default": {}}
        list_file = data_dir / "default_list.json"
        if not list_file.exists():
            print("No platform list files (e.g. data/<platform>_list.json) or config.platforms; create one to sync.")
            return 0
    records = load_db()
    seen_platform_id = set()
    for platform in platforms:
        list_data = fetch_platform_list(platform, data_dir)
        for raw in list_data:
            sid = str(raw.get("session_id", ""))
            if not sid:
                continue
            idx, existing = find_by_platform_and_session_id(records, platform, sid)
            new_ts = raw.get("last_message_timestamp") or raw.get("update_time") or ""
            if idx is None:
                rec = build_record(platform, raw)
                rec["last_message_timestamp"] = new_ts
                records.append(rec)
                seen_platform_id.add((platform, sid))
                print(f"Added: {platform} {sid} -> {rec['global_session_id']}")
            else:
                rec = records[idx]
                seen_platform_id.add((platform, sid))
                old_ts = rec.get("last_message_timestamp") or rec.get("update_date") or ""
                if new_ts and (not old_ts or new_ts > old_ts):
                    rec["session_status"] = "updating"
                    rec["update_date"] = iso_now()
                    if "title" in raw:
                        rec["session_title"] = str(raw["title"])
                    if new_ts:
                        rec["last_message_timestamp"] = new_ts
                    print(f"Mark updating: {platform} {sid} (newer timestamp)")
    save_db(records)
    print(f"database.json saved with {len(records)} records at {get_database_path()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
