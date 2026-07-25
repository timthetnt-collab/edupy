# achievements.py
"""
Achievements definitions and helper functions.
Call check_unlocks(app, event) after events like XP gain, session complete, etc.
"""

import save_system

# Achievement definitions
ACHIEVEMENTS = {
    "first_steps": {
        "id": "first_steps",
        "title": "First Steps",
        "desc": "Complete your first activity",
        "activities_required": 1
    },
    "100_xp": {
        "id": "100_xp",
        "title": "100 XP",
        "desc": "Earn 100 XP total",
        "xp_required": 100
    },
    "maths_master_10": {
        "id": "maths_master_10",
        "title": "Maths Novice",
        "desc": "Complete 10 Maths practice sessions",
        "maths_sessions_required": 10
    },
    "english_reader_5": {
        "id": "english_reader_5",
        "title": "Reader",
        "desc": "Complete 5 English texts",
        "english_completed_required": 5
    },
    "balanced_learner": {
        "id": "balanced_learner",
        "title": "Balanced Learner",
        "desc": "Complete at least 3 Maths and 3 English activities",
        "maths_sessions_required": 3,
        "english_completed_required": 3,
    },
    "question_50": {
        "id": "question_50",
        "title": "Curious Mind",
        "desc": "Answer 50 practice questions",
        "questions_required": 50,
    },
}


def get_all_achievements():
    return list(ACHIEVEMENTS.values())


def check_unlocks(app, username=None):
    """
    Check and unlock achievements for the given user.
    Returns list of newly unlocked achievement ids.
    """
    if username is None:
        username = app.current_user
    data = app.save_data
    user = data["users"].get(username)
    if not user:
        return []

    newly = []
    # total xp
    # Use lifetime XP so levelling up never makes an achievement unreachable.
    xp = user.get("total_xp", user.get("xp", 0))
    for aid, meta in ACHIEVEMENTS.items():
        if aid in user.get("achievements_unlocked", []):
            continue
        ok = True
        if meta.get("activities_required") and user.get("maths_completed", 0) + user.get("english_completed", 0) < meta["activities_required"]:
            ok = False
        if meta.get("xp_required") and xp < meta["xp_required"]:
            ok = False
        if meta.get("maths_sessions_required") and user.get("maths_completed", 0) < meta["maths_sessions_required"]:
            ok = False
        if meta.get("english_completed_required") and user.get("english_completed", 0) < meta["english_completed_required"]:
            ok = False
        if meta.get("questions_required") and user.get("questions_answered", 0) < meta["questions_required"]:
            ok = False
        if ok:
            unlocked = save_system.unlock_achievement(data, username, aid)
            if unlocked:
                newly.append(aid)
    return newly
