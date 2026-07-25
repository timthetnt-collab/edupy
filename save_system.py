# save_system.py
"""
Save system with extended support:
- default_user includes role and linked accounts
- content packs storage (lesson editor)
- achievements storage and audit log
- import/export helpers
"""

import json
import os
import datetime
import shutil
import tempfile
import copy
import uuid

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SAVE_FILE = os.path.join(BASE_DIR, "save_data.json")
BACKUP_FILE = os.path.join(BASE_DIR, "save_backup.json")
_EDUCATION_SYNC = None
_PROFILE_SYNC = None
_PROFILE_FIELDS = set()


def set_education_sync(callback):
    """Register database persistence after the education migration succeeds."""
    global _EDUCATION_SYNC
    _EDUCATION_SYNC = callback


def set_profile_sync(callback, moved_fields=None):
    """Register database persistence for progress and reward profile fields."""
    global _PROFILE_SYNC, _PROFILE_FIELDS
    _PROFILE_SYNC = callback
    _PROFILE_FIELDS = set(moved_fields or ())


def default_user(password=None, role="student"):
    """Create a learning profile. Passwords now live only in edupy.db.

    ``password`` remains as an ignored compatibility argument so older learning
    modules and third-party content do not break during the account upgrade.
    """
    return {
        "role": role,                       # student | teacher | parent | admin
        "linked_accounts": [],              # for parents/teachers: list of usernames
        "xp": 0,
        "level": 1,
        "questions_answered": 0,
        "english_completed": 0,
        "maths_completed": 0,
        "tokens": 0,
        "last_daily_claim": None,
        "daily_reward_streak": 0,
        "reward_history": [],
        "token_earn_day": None,
        "tokens_earned_today": 0,
        "themes_unlocked": ["Default"],
        "current_theme": "Default",
        "school_safe_mode": False,
        "admin": role == "admin",
        "achievements_unlocked": [],        # list of achievement ids
        "selected_year": 7,
        "total_xp": 0,
        "mastery": {},
        "recent_topics": [],
        "game": {
            "stars": 0,
            "daily": {
                "date": None,
                "correct_answers": 0,
                "learning_sessions": 0,
                "minigames": 0,
                "claimed": [],
            },
        },
    }


def ensure_user_schema(user):
    """Add new fields to an older account without replacing its progress."""
    defaults = default_user(role=user.get("role", "student"))
    for key, value in defaults.items():
        user.setdefault(key, copy.deepcopy(value))
    try:
        year = int(user.get("selected_year", 7))
    except (TypeError, ValueError):
        year = 7
    user["selected_year"] = min(11, max(7, year))
    user["total_xp"] = max(int(user.get("total_xp", 0)), int(user.get("xp", 0)))
    # Remove fields from the retired real-money/subscription prototype.
    user.pop("subscription", None)
    user.pop("purchase_history", None)
    return user


def ensure_data_schema(data):
    """Migrate save data in memory to the current shape."""
    data.setdefault("users", {})
    data.setdefault("content_packs", [])
    data.setdefault("audit_log", [])
    data.setdefault("classes", {})
    data.setdefault("assignments", {})
    data.setdefault("assignment_templates", {})
    for user in data["users"].values():
        ensure_user_schema(user)
    return data


def load_save():
    if not os.path.exists(SAVE_FILE):
        data = ensure_data_schema({})
        save_save(data)
        return data

    try:
        with open(SAVE_FILE, "r") as f:
            data = json.load(f)
        return ensure_data_schema(data)
    except Exception:
        if os.path.exists(BACKUP_FILE):
            try:
                with open(BACKUP_FILE, "r") as f:
                    data = json.load(f)
                data = ensure_data_schema(data)
                save_save(data)
                return data
            except Exception:
                pass
        data = ensure_data_schema({})
        save_save(data)
        return data


def save_save(data):
    """Save atomically and retain the previous valid file as a backup."""
    ensure_data_schema(data)
    if _EDUCATION_SYNC is not None:
        _EDUCATION_SYNC(data)
    if _PROFILE_SYNC is not None:
        _PROFILE_SYNC(data)
    serializable = copy.deepcopy(data)
    if _EDUCATION_SYNC is not None:
        serializable.pop("classes", None)
        serializable.pop("assignments", None)
        serializable.pop("assignment_templates", None)
    if _PROFILE_SYNC is not None:
        for profile in serializable.get("users", {}).values():
            for field in _PROFILE_FIELDS:
                profile.pop(field, None)
    fd, temp_path = tempfile.mkstemp(prefix="edupy_", suffix=".json", dir=BASE_DIR)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(serializable, f, indent=4, ensure_ascii=False)
        if os.path.exists(SAVE_FILE):
            shutil.copy2(SAVE_FILE, BACKUP_FILE)
        os.replace(temp_path, SAVE_FILE)
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def ensure_user_exists(data, username, password="changeme", role="student"):
    """Retired: account creation must use account_service.create_account."""
    del password, role
    return username in data.get("users", {})


def get_user(data, username):
    user = data.get("users", {}).get(username)
    return ensure_user_schema(user) if user else None


def create_user(data, username, password, role="student"):
    """Retired compatibility entry point; never create a profile-only login."""
    del data, username, password, role
    return False


def update_user(data, username, key, value):
    if username not in data["users"]:
        return
    data["users"][username][key] = value
    save_save(data)


def add_tokens(data, username, amount):
    return award_tokens(data, username, amount, "Token adjustment", daily_cap=None, count_toward_cap=False)


def award_tokens(data, username, amount, reason, daily_cap=20, count_toward_cap=True, event_id=None):
    """Award earned tokens with an optional anti-grind daily cap."""
    user = get_user(data, username)
    if not user:
        return 0
    event_id = str(event_id or uuid.uuid4())
    if any(entry.get("event_id") == event_id for entry in user.get("reward_history", [])):
        return 0
    today = datetime.date.today().isoformat()
    if user.get("token_earn_day") != today:
        user["token_earn_day"] = today
        user["tokens_earned_today"] = 0
    amount = max(0, int(amount))
    if daily_cap is not None:
        amount = min(amount, max(0, daily_cap - int(user.get("tokens_earned_today", 0))))
    if not amount:
        return 0
    user["tokens"] = user.get("tokens", 0) + amount
    if count_toward_cap:
        user["tokens_earned_today"] = user.get("tokens_earned_today", 0) + amount
    user.setdefault("reward_history", []).append({"event_id": event_id, "date": today, "amount": amount, "reason": reason})
    user["reward_history"] = user["reward_history"][-100:]
    save_save(data)
    return amount


def purchase_theme(data, username, theme_name, price):
    """Atomically spend earned tokens and record one cosmetic unlock."""
    user = get_user(data, username)
    if not user or theme_name in user.get("themes_unlocked", []):
        return False
    price = max(0, int(price))
    if int(user.get("tokens", 0)) < price:
        return False
    event_id = f"theme-purchase:{theme_name}"
    if any(entry.get("event_id") == event_id for entry in user.get("reward_history", [])):
        return False
    user["tokens"] -= price
    user.setdefault("themes_unlocked", ["Default"]).append(theme_name)
    user.setdefault("reward_history", []).append({
        "event_id": event_id,
        "date": datetime.date.today().isoformat(),
        "amount": -price,
        "reason": f"Unlocked {theme_name} theme",
    })
    user["reward_history"] = user["reward_history"][-100:]
    save_save(data)
    return True


def unlock_theme(data, username, theme_name):
    user = data["users"].get(username)
    if not user:
        return
    if theme_name not in user["themes_unlocked"]:
        user["themes_unlocked"].append(theme_name)
        save_save(data)


def set_theme_for_user(data, username, theme_name):
    user = data["users"].get(username)
    if not user:
        return
    user["current_theme"] = theme_name
    save_save(data)


# -------------------------
# Content packs (lesson editor)
# -------------------------

def add_content_pack(data, pack):
    """
    pack is a dict with keys: id, title, type ('english'|'maths'), content (text or template), metadata
    """
    data.setdefault("content_packs", [])
    # ensure id uniqueness
    existing = [p for p in data["content_packs"] if p.get("id") == pack.get("id")]
    if existing:
        # replace
        data["content_packs"] = [p for p in data["content_packs"] if p.get("id") != pack.get("id")]
    data["content_packs"].append(pack)
    save_save(data)


def get_content_packs(data, pack_type=None):
    packs = data.get("content_packs", [])
    if pack_type:
        return [p for p in packs if p.get("type") == pack_type]
    return packs


def remove_content_pack(data, pack_id):
    data["content_packs"] = [p for p in data.get("content_packs", []) if p.get("id") != pack_id]
    save_save(data)


# -------------------------
# Achievements + audit log
# -------------------------

def unlock_achievement(data, username, achievement_id):
    user = data["users"].get(username)
    if not user:
        return False
    if achievement_id not in user.get("achievements_unlocked", []):
        user.setdefault("achievements_unlocked", []).append(achievement_id)
        append_audit(data, admin=None, action="unlock_achievement", target=username, details={"achievement": achievement_id})
        save_save(data)
        return True
    return False


def has_achievement(data, username, achievement_id):
    user = data["users"].get(username)
    if not user:
        return False
    return achievement_id in user.get("achievements_unlocked", [])


def append_audit(data, admin, action, target=None, details=None):
    entry = {
        "time": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "admin": admin,
        "action": action,
        "target": target,
        "details": details or {}
    }
    data.setdefault("audit_log", []).append(entry)
    save_save(data)


def get_audit_log(data, limit=200):
    return data.get("audit_log", [])[-limit:]


# -------------------------
# Import / Export helpers
# -------------------------

def export_save(data, path):
    """Retired: a JSON-only export cannot represent the relational database."""
    del data, path
    raise RuntimeError("Full-save JSON export is retired; use EduPy's private local backups.")


def import_save(path):
    """Retired: importing JSON alone would corrupt relational account links."""
    del path
    raise RuntimeError("Full-save JSON import is disabled to protect relational data.")
