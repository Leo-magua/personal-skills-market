#!/usr/bin/env python3
"""
Mark completed sessions as updating when last_message_timestamp or update_date is older than --days.
Next run_tasks will then perform incremental update.
"""
import argparse
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
from config import get_data_dir, ensure_data_dir
from db import load_db, save_db


def parse_iso(s: str) -> datetime | None:
    if not s:
        return None
    try:
        if s.endswith("Z"):
            s = s.replace("Z", "+00:00")
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        return None


def main():
    ap = argparse.ArgumentParser(description="Mark stale completed sessions as updating")
    ap.add_argument("--data-dir", type=Path, default=None, help="Data directory")
    ap.add_argument("--days", type=int, default=7, help="Threshold in days (default 7)")
    args = ap.parse_args()
    if args.data_dir is not None:
        import os
        os.environ["AI_ARCHIVE_DATA_DIR"] = str(args.data_dir.resolve())
    ensure_data_dir()
    records = load_db()
    now = datetime.now(timezone.utc)
    threshold = now - timedelta(days=args.days)
    updated = 0
    for r in records:
        if r.get("session_status") != "completed":
            continue
        ts = parse_iso(r.get("last_message_timestamp") or r.get("update_date") or "")
        if ts and ts < threshold:
            r["session_status"] = "updating"
            updated += 1
    if updated:
        save_db(records)
        print(f"Marked {updated} session(s) as updating (older than {args.days} days).")
    else:
        print("No completed sessions older than threshold.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
