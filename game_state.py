"""Small, local game-state layer for the student adventure.

The educational records remain the source of truth.  This module only turns
real learning activity into daily quests, stars, and a visible adventure loop.
"""

import datetime


DAILY_QUESTS = (
    {
        "id": "warm_up",
        "title": "Warm-up Warrior",
        "description": "Answer 3 questions correctly",
        "counter": "correct_answers",
        "target": 3,
        "stars": 1,
        "tokens": 2,
    },
    {
        "id": "complete_mission",
        "title": "Quest Complete",
        "description": "Finish a Maths or English mission",
        "counter": "learning_sessions",
        "target": 1,
        "stars": 2,
        "tokens": 3,
    },
    {
        "id": "brain_break",
        "title": "Arcade Adventurer",
        "description": "Finish one brain-game challenge",
        "counter": "minigames",
        "target": 1,
        "stars": 1,
        "tokens": 2,
    },
)


def default_game_state():
    return {
        "stars": 0,
        "daily": {
            "date": None,
            "correct_answers": 0,
            "learning_sessions": 0,
            "minigames": 0,
            "claimed": [],
        },
    }


def ensure_game_state(user, today=None):
    state = user.setdefault("game", default_game_state())
    state.setdefault("stars", 0)
    daily = state.setdefault("daily", {})
    current_date = today or datetime.date.today().isoformat()
    if daily.get("date") != current_date:
        state["daily"] = {
            "date": current_date,
            "correct_answers": 0,
            "learning_sessions": 0,
            "minigames": 0,
            "claimed": [],
        }
    else:
        for key in ("correct_answers", "learning_sessions", "minigames"):
            daily.setdefault(key, 0)
        daily.setdefault("claimed", [])
    return state


def record_event(user, event, amount=1):
    if not user:
        return
    daily = ensure_game_state(user)["daily"]
    if event in ("correct_answers", "learning_sessions", "minigames"):
        daily[event] = max(0, int(daily.get(event, 0)) + max(0, int(amount)))


def quest_progress(user, quest):
    value = int(ensure_game_state(user)["daily"].get(quest["counter"], 0))
    return min(value, quest["target"]), quest["target"]


def claim_quest(app, quest_id):
    """Claim a completed quest once. Returns (success, message)."""
    import save_system

    user = save_system.get_user(app.save_data, app.current_user)
    quest = next((item for item in DAILY_QUESTS if item["id"] == quest_id), None)
    if not user or not quest:
        return False, "That quest is unavailable."
    state = ensure_game_state(user)
    claimed = state["daily"]["claimed"]
    current, target = quest_progress(user, quest)
    if quest_id in claimed:
        return False, "You have already claimed this quest."
    if current < target:
        return False, "Complete the quest first."
    claimed.append(quest_id)
    state["stars"] += quest["stars"]
    save_system.award_tokens(
        app.save_data,
        app.current_user,
        quest["tokens"],
        f"Daily quest: {quest['title']}",
        daily_cap=None,
        count_toward_cap=False,
        event_id=f"quest:{app.current_user}:{state['daily']['date']}:{quest_id}",
    )
    return True, f"Quest claimed: +{quest['stars']} star(s) and +{quest['tokens']} tokens!"


def hero_title(level):
    level = max(1, int(level))
    if level >= 10:
        return "Master Mind"
    if level >= 7:
        return "Knowledge Knight"
    if level >= 4:
        return "Puzzle Ranger"
    if level >= 2:
        return "Rising Explorer"
    return "New Adventurer"

