import json
import os
import tempfile
import unittest
from unittest.mock import patch

from auth import hash_password
from database import AccountDatabase
from models import Account
from progress_store import MOVED_PROFILE_FIELDS, ProgressStore
import save_system


class ProgressDatabaseTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.database = AccountDatabase(os.path.join(self.folder.name, "edupy.db"))
        self.database.create_tables()
        self.database.create_account(Account(username="learner", password_hash=hash_password("StudentPass123"), role="student", year_group=9))
        self.database.create_account(Account(username="teacher", password_hash=hash_password("TeacherPass123"), role="teacher", year_group=7))
        self.store = ProgressStore(self.database.engine)
        self.store.create_tables()

    def tearDown(self):
        save_system.set_profile_sync(None)
        self.database.engine.dispose()
        self.folder.cleanup()

    def sample_data(self):
        learner = save_system.default_user(role="student")
        learner.update({
            "xp": 45,
            "level": 2,
            "total_xp": 145,
            "questions_answered": 20,
            "maths_completed": 4,
            "english_completed": 3,
            "tokens": 27,
            "themes_unlocked": ["Default", "Ocean"],
            "current_theme": "Ocean",
            "achievements_unlocked": ["first_steps", "100_xp"],
            "reward_history": [
                {"date": "2026-07-13", "amount": 3, "reason": "Maths"},
                {"date": "2026-07-14", "amount": -25, "reason": "Unlocked Ocean theme"},
            ],
            "mastery": {
                "Maths": {
                    "algebra": {"attempts": 2, "earned": 1.5, "possible": 2.0, "recent": 0.8, "updated": "2026-07-14"}
                }
            },
            "recent_topics": [{"subject": "Maths", "topic": "algebra", "score": 80, "date": "2026-07-14"}],
            "linked_accounts": ["teacher"],
        })
        return {
            "users": {
                "learner": learner,
                "teacher": save_system.default_user(role="teacher"),
            }
        }

    def test_progress_rewards_and_mastery_round_trip(self):
        data = self.sample_data()
        result = self.store.migrate_or_load(data)
        restored = self.store.load_profiles()["learner"]

        self.assertTrue(result.successful)
        self.assertTrue(result.migrated)
        self.assertEqual(restored["tokens"], 27)
        self.assertEqual(restored["total_xp"], 145)
        self.assertEqual(restored["current_theme"], "Ocean")
        self.assertEqual(len(restored["reward_history"]), 2)
        self.assertEqual(restored["mastery"]["Maths"]["algebra"]["attempts"], 2)
        self.assertEqual(restored["recent_topics"][0]["score"], 80)
        self.assertEqual(restored["linked_accounts"], ["teacher"])

    def test_existing_database_wins_over_stale_json(self):
        data = self.sample_data()
        self.store.migrate_or_load(data)
        stale = self.sample_data()
        stale["users"]["learner"]["tokens"] = 0
        result = self.store.migrate_or_load(stale)
        self.assertFalse(result.migrated)
        self.assertEqual(stale["users"]["learner"]["tokens"], 27)

    def test_negative_balance_and_unowned_active_theme_are_rejected(self):
        data = self.sample_data()
        data["users"]["learner"]["tokens"] = -1
        with self.assertRaises(ValueError):
            self.store.save_snapshot(data)
        data["users"]["learner"]["tokens"] = 1
        data["users"]["learner"]["current_theme"] = "Matrix"
        with self.assertRaises(ValueError):
            self.store.save_snapshot(data)

    def test_profile_save_hook_cleans_json_and_updates_database(self):
        data = self.sample_data()
        self.store.migrate_or_load(data)
        active_path = os.path.join(self.folder.name, "save_data.json")
        backup_path = os.path.join(self.folder.name, "save_backup.json")
        save_system.set_profile_sync(self.store.save_snapshot, MOVED_PROFILE_FIELDS)
        data["users"]["learner"]["tokens"] = 31
        with patch.object(save_system, "SAVE_FILE", active_path), patch.object(save_system, "BACKUP_FILE", backup_path):
            save_system.save_save(data)
        with open(active_path, encoding="utf-8") as file:
            saved_json = json.load(file)
        self.assertNotIn("tokens", saved_json["users"]["learner"])
        self.assertNotIn("mastery", saved_json["users"]["learner"])
        self.assertEqual(self.store.load_profiles()["learner"]["tokens"], 31)


class RewardRuleTests(unittest.TestCase):
    def setUp(self):
        self.data = {"users": {"learner": save_system.default_user(role="student")}}

    @patch("save_system.save_save", lambda data: None)
    def test_duplicate_event_is_not_awarded_twice(self):
        first = save_system.award_tokens(self.data, "learner", 5, "Completed task", event_id="task:1")
        second = save_system.award_tokens(self.data, "learner", 5, "Completed task", event_id="task:1")
        self.assertEqual(first, 5)
        self.assertEqual(second, 0)
        self.assertEqual(self.data["users"]["learner"]["tokens"], 5)

    @patch("save_system.save_save", lambda data: None)
    def test_daily_activity_cap_is_enforced(self):
        self.assertEqual(save_system.award_tokens(self.data, "learner", 15, "Activity one"), 15)
        self.assertEqual(save_system.award_tokens(self.data, "learner", 10, "Activity two"), 5)
        self.assertEqual(save_system.award_tokens(self.data, "learner", 3, "Activity three"), 0)
        self.assertEqual(self.data["users"]["learner"]["tokens"], 20)

    @patch("save_system.save_save", lambda data: None)
    def test_theme_purchase_is_single_and_never_goes_negative(self):
        user = self.data["users"]["learner"]
        self.assertFalse(save_system.purchase_theme(self.data, "learner", "Ocean", 25))
        user["tokens"] = 30
        self.assertTrue(save_system.purchase_theme(self.data, "learner", "Ocean", 25))
        self.assertFalse(save_system.purchase_theme(self.data, "learner", "Ocean", 25))
        self.assertEqual(user["tokens"], 5)
        self.assertEqual(user["themes_unlocked"].count("Ocean"), 1)


if __name__ == "__main__":
    unittest.main()
