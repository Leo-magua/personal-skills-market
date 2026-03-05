# Shared config and paths for ai-conversation-archive scripts.
# Data dir: database.json, action.log, {platform}_{session_id}_raw.json, {platform}_{session_id}_abstract.md
import json
import os
import re
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
DEFAULT_DATA_DIR = SKILL_DIR / "data"

def get_data_dir():
    env = os.environ.get("AI_ARCHIVE_DATA_DIR")
    if env:
        return Path(env).expanduser().resolve()
    return DEFAULT_DATA_DIR

def load_config():
    data_dir = get_data_dir()
    config_path = data_dir / "config.json"
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def get_database_path():
    return get_data_dir() / "database.json"

def get_action_log_path():
    return get_data_dir() / "action.log"

def get_summary_command():
    """Command template to generate .md from .json. Placeholders: {input_json} {output_md}."""
    cfg = load_config()
    return cfg.get("summary_command") or ""

def ensure_data_dir():
    get_data_dir().mkdir(parents=True, exist_ok=True)


def _sanitize_fname(s: str) -> str:
    """Keep only alphanumeric, underscore, hyphen for safe filenames."""
    return re.sub(r"[^\w\-]", "_", str(s))


def raw_json_basename(platform: str, session_id: str) -> str:
    """e.g. deepseek_4846a5df-491e-4923-b31c-fe2e57f63c94_raw.json"""
    return f"{_sanitize_fname(platform)}_{_sanitize_fname(session_id)}_raw.json"


def abstract_md_basename(platform: str, session_id: str) -> str:
    """e.g. deepseek_4846a5df-491e-4923-b31c-fe2e57f63c94_abstract.md"""
    return f"{_sanitize_fname(platform)}_{_sanitize_fname(session_id)}_abstract.md"
