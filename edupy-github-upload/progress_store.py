"""Relational persistence for learner progress, rewards, mastery and cosmetics."""

from dataclasses import dataclass
import hashlib

from sqlalchemy import delete
from sqlmodel import Session, SQLModel, select

from models import (
    Account,
    AchievementUnlock,
    LearnerProgressRecord,
    LinkedAccountRecord,
    MasteryRecord,
    ProgressSetting,
    RecentTopicRecord,
    RewardTransaction,
    ThemeUnlock,
)


SCHEMA_VERSION = "1"
MOVED_PROFILE_FIELDS = {
    "linked_accounts",
    "xp",
    "level",
    "questions_answered",
    "english_completed",
    "maths_completed",
    "tokens",
    "last_daily_claim",
    "daily_reward_streak",
    "reward_history",
    "token_earn_day",
    "tokens_earned_today",
    "themes_unlocked",
    "current_theme",
    "school_safe_mode",
    "achievements_unlocked",
    "total_xp",
    "mastery",
    "recent_topics",
}


def default_progress():
    return {
        "linked_accounts": [],
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
        "achievements_unlocked": [],
        "total_xp": 0,
        "mastery": {},
        "recent_topics": [],
    }


@dataclass
class ProgressMigrationResult:
    expected: dict
    actual: dict
    migrated: bool

    @property
    def successful(self):
        return self.expected == self.actual


class ProgressStore:
    def __init__(self, engine):
        self.engine = engine

    def create_tables(self):
        SQLModel.metadata.create_all(self.engine)

    def is_initialized(self):
        with Session(self.engine) as session:
            setting = session.get(ProgressSetting, "progress_schema_version")
            return bool(setting and setting.value == SCHEMA_VERSION)

    @staticmethod
    def _profile(data, username):
        merged = default_progress()
        merged.update(data.get("users", {}).get(username, {}))
        return merged

    @classmethod
    def counts_for_data(cls, data, usernames=None):
        usernames = list(usernames if usernames is not None else data.get("users", {}))
        profiles = [cls._profile(data, username) for username in usernames]
        return {
            "profiles": len(profiles),
            "reward_transactions": sum(len(profile.get("reward_history", [])) for profile in profiles),
            "theme_unlocks": sum(len(set(profile.get("themes_unlocked", [])) | {"Default"}) for profile in profiles),
            "achievements": sum(len(set(profile.get("achievements_unlocked", []))) for profile in profiles),
            "mastery_records": sum(len(topics) for profile in profiles for topics in profile.get("mastery", {}).values()),
            "recent_topics": sum(len(profile.get("recent_topics", [])) for profile in profiles),
            "linked_accounts": sum(len(set(profile.get("linked_accounts", []))) for profile in profiles),
            "total_tokens": sum(max(0, int(profile.get("tokens", 0))) for profile in profiles),
            "total_xp": sum(max(0, int(profile.get("total_xp", profile.get("xp", 0)))) for profile in profiles),
        }

    def database_counts(self):
        with Session(self.engine) as session:
            progress = session.exec(select(LearnerProgressRecord)).all()
            return {
                "profiles": len(progress),
                "reward_transactions": len(session.exec(select(RewardTransaction.id)).all()),
                "theme_unlocks": len(session.exec(select(ThemeUnlock.id)).all()),
                "achievements": len(session.exec(select(AchievementUnlock.id)).all()),
                "mastery_records": len(session.exec(select(MasteryRecord.id)).all()),
                "recent_topics": len(session.exec(select(RecentTopicRecord.id)).all()),
                "linked_accounts": len(session.exec(select(LinkedAccountRecord.id)).all()),
                "total_tokens": sum(row.tokens for row in progress),
                "total_xp": sum(row.total_xp for row in progress),
            }

    def migrate_or_load(self, data):
        self.create_tables()
        with Session(self.engine) as session:
            usernames = [account.username for account in session.exec(select(Account)).all()]

        if self.is_initialized():
            stored = self.load_profiles()
            for username, profile in stored.items():
                data.setdefault("users", {}).setdefault(username, {}).update(profile)
            # Secure accounts created immediately before a crash receive defaults.
            self.save_snapshot(data, mark_initialized=True)
            expected = self.counts_for_data(data, usernames)
            actual = self.database_counts()
            if expected != actual:
                raise RuntimeError(f"Progress database verification failed: expected {expected}, found {actual}")
            return ProgressMigrationResult(expected, actual, False)

        expected = self.counts_for_data(data, usernames)
        self.save_snapshot(data, mark_initialized=True)
        actual = self.database_counts()
        if expected != actual:
            raise RuntimeError(f"Progress migration verification failed: expected {expected}, found {actual}")
        return ProgressMigrationResult(expected, actual, True)

    @staticmethod
    def _event_id(username, position, entry):
        existing = str(entry.get("event_id", "")).strip()
        if existing:
            return existing[:96]
        raw = f"{username}|{position}|{entry.get('date')}|{entry.get('amount')}|{entry.get('reason')}"
        return "legacy-" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]

    def save_snapshot(self, data, mark_initialized=False):
        with Session(self.engine) as session:
            accounts = session.exec(select(Account)).all()
            account_by_username = {account.username: account for account in accounts}
            profiles = {username: self._profile(data, username) for username in account_by_username}

            for username, profile in profiles.items():
                numeric_fields = (
                    "xp", "total_xp", "questions_answered", "english_completed",
                    "maths_completed", "tokens", "daily_reward_streak", "tokens_earned_today",
                )
                if any(int(profile.get(field, 0)) < 0 for field in numeric_fields):
                    raise ValueError(f"Progress values cannot be negative for {username!r}.")
                if int(profile.get("level", 1)) < 1:
                    raise ValueError(f"Level must be at least one for {username!r}.")
                themes = set(profile.get("themes_unlocked", [])) | {"Default"}
                if profile.get("current_theme", "Default") not in themes:
                    raise ValueError(f"The active theme is not owned by {username!r}.")
                for linked in profile.get("linked_accounts", []):
                    if linked not in account_by_username:
                        raise ValueError(f"Linked account {linked!r} does not exist.")

            try:
                for model in (RewardTransaction, ThemeUnlock, AchievementUnlock, MasteryRecord, RecentTopicRecord, LinkedAccountRecord, LearnerProgressRecord):
                    session.exec(delete(model))

                for username, profile in profiles.items():
                    account = account_by_username[username]
                    session.add(LearnerProgressRecord(
                        account_id=account.id,
                        xp=int(profile.get("xp", 0)),
                        level=int(profile.get("level", 1)),
                        total_xp=max(int(profile.get("total_xp", 0)), int(profile.get("xp", 0))),
                        questions_answered=int(profile.get("questions_answered", 0)),
                        english_completed=int(profile.get("english_completed", 0)),
                        maths_completed=int(profile.get("maths_completed", 0)),
                        tokens=int(profile.get("tokens", 0)),
                        last_daily_claim=profile.get("last_daily_claim"),
                        daily_reward_streak=int(profile.get("daily_reward_streak", 0)),
                        token_earn_day=profile.get("token_earn_day"),
                        tokens_earned_today=int(profile.get("tokens_earned_today", 0)),
                        current_theme=profile.get("current_theme", "Default"),
                        school_safe_mode=bool(profile.get("school_safe_mode", False)),
                    ))
                session.flush()

                for username, profile in profiles.items():
                    account_id = account_by_username[username].id
                    for position, entry in enumerate(profile.get("reward_history", [])[-100:]):
                        session.add(RewardTransaction(
                            account_id=account_id,
                            event_id=self._event_id(username, position, entry),
                            date=str(entry.get("date") or ""),
                            amount=int(entry.get("amount", 0)),
                            reason=str(entry.get("reason") or "Reward"),
                        ))
                    for theme_name in sorted(set(profile.get("themes_unlocked", [])) | {"Default"}):
                        session.add(ThemeUnlock(account_id=account_id, theme_name=theme_name))
                    for achievement_id in sorted(set(profile.get("achievements_unlocked", []))):
                        session.add(AchievementUnlock(account_id=account_id, achievement_id=achievement_id))
                    for subject, topics in profile.get("mastery", {}).items():
                        for topic_id, record in topics.items():
                            session.add(MasteryRecord(
                                account_id=account_id,
                                subject=subject,
                                topic_id=topic_id,
                                attempts=max(0, int(record.get("attempts", 0))),
                                earned=max(0.0, float(record.get("earned", 0))),
                                possible=max(0.0, float(record.get("possible", 0))),
                                recent=min(1.0, max(0.0, float(record.get("recent", 0)))),
                                updated=record.get("updated"),
                            ))
                    for position, record in enumerate(profile.get("recent_topics", [])[-30:]):
                        session.add(RecentTopicRecord(
                            account_id=account_id,
                            position=position,
                            subject=str(record.get("subject") or "General"),
                            topic_id=str(record.get("topic") or "unknown"),
                            score=min(100, max(0, int(record.get("score", 0)))),
                            date=record.get("date"),
                        ))
                    for linked in sorted(set(profile.get("linked_accounts", []))):
                        session.add(LinkedAccountRecord(
                            owner_account_id=account_id,
                            linked_account_id=account_by_username[linked].id,
                        ))
                session.flush()

                if mark_initialized:
                    setting = session.get(ProgressSetting, "progress_schema_version")
                    if setting:
                        setting.value = SCHEMA_VERSION
                        session.add(setting)
                    else:
                        session.add(ProgressSetting(key="progress_schema_version", value=SCHEMA_VERSION))
                session.commit()
            except Exception:
                session.rollback()
                raise

    def load_profiles(self):
        with Session(self.engine) as session:
            accounts = session.exec(select(Account)).all()
            username_by_id = {account.id: account.username for account in accounts}
            profiles = {account.username: default_progress() for account in accounts}

            for row in session.exec(select(LearnerProgressRecord)).all():
                username = username_by_id.get(row.account_id)
                if not username:
                    continue
                profiles[username].update({
                    "xp": row.xp,
                    "level": row.level,
                    "total_xp": row.total_xp,
                    "questions_answered": row.questions_answered,
                    "english_completed": row.english_completed,
                    "maths_completed": row.maths_completed,
                    "tokens": row.tokens,
                    "last_daily_claim": row.last_daily_claim,
                    "daily_reward_streak": row.daily_reward_streak,
                    "token_earn_day": row.token_earn_day,
                    "tokens_earned_today": row.tokens_earned_today,
                    "current_theme": row.current_theme,
                    "school_safe_mode": row.school_safe_mode,
                })
            for row in session.exec(select(RewardTransaction).order_by(RewardTransaction.id)).all():
                username = username_by_id.get(row.account_id)
                if username:
                    profiles[username]["reward_history"].append({"event_id": row.event_id, "date": row.date, "amount": row.amount, "reason": row.reason})
            for row in session.exec(select(ThemeUnlock)).all():
                username = username_by_id.get(row.account_id)
                if username and row.theme_name not in profiles[username]["themes_unlocked"]:
                    profiles[username]["themes_unlocked"].append(row.theme_name)
            for row in session.exec(select(AchievementUnlock)).all():
                username = username_by_id.get(row.account_id)
                if username:
                    profiles[username]["achievements_unlocked"].append(row.achievement_id)
            for row in session.exec(select(MasteryRecord)).all():
                username = username_by_id.get(row.account_id)
                if username:
                    profiles[username].setdefault("mastery", {}).setdefault(row.subject, {})[row.topic_id] = {
                        "attempts": row.attempts, "earned": row.earned, "possible": row.possible,
                        "recent": row.recent, "updated": row.updated,
                    }
            for row in session.exec(select(RecentTopicRecord).order_by(RecentTopicRecord.position)).all():
                username = username_by_id.get(row.account_id)
                if username:
                    profiles[username]["recent_topics"].append({"subject": row.subject, "topic": row.topic_id, "score": row.score, "date": row.date})
            for row in session.exec(select(LinkedAccountRecord)).all():
                owner = username_by_id.get(row.owner_account_id)
                linked = username_by_id.get(row.linked_account_id)
                if owner and linked:
                    profiles[owner]["linked_accounts"].append(linked)
            return profiles
