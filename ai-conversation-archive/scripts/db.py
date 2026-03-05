# Load/save database.json with locking-friendly read-modify-write.
import json
from pathlib import Path

try:
    from .config import get_database_path, ensure_data_dir
except ImportError:
    from config import get_database_path, ensure_data_dir

def load_db():
    path = get_database_path()
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_db(records):
    ensure_data_dir()
    path = get_database_path()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

def find_by_platform_and_session_id(records, platform, session_id):
    for i, r in enumerate(records):
        if r.get("session_sourceplatform") == platform and r.get("session_id") == session_id:
            return i, r
    return None, None

def find_by_global_id(records, global_session_id):
    for i, r in enumerate(records):
        if r.get("global_session_id") == global_session_id:
            return i, r
    return None, None
