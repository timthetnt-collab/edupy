import os
import tempfile
import unittest
import json
from unittest.mock import patch

from auth import hash_password
from database import AccountDatabase
from education_store import EducationStore
from models import Account
import save_system


class EducationDatabaseTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.database = AccountDatabase(os.path.join(self.folder.name, "edupy.db"))
        self.database.create_tables()
        self.database.create_account(Account(username="teacher", password_hash=hash_password("TeacherPass123"), role="teacher", year_group=7))
        self.database.create_account(Account(username="student", password_hash=hash_password("StudentPass123"), role="student", year_group=9))
        self.store = EducationStore(self.database.engine)
        self.store.create_tables()

    def tearDown(self):
        self.database.engine.dispose()
        self.folder.cleanup()

    def sample_data(self):
        return {
            "classes": {
                "english-9": {
                    "id": "english-9",
                    "title": "English 9",
                    "subject": "English",
                    "year_group": 9,
                    "teacher_usernames": ["teacher"],
                    "student_usernames": ["student"],
                    "join_code": "ABC123",
                    "created_at": "2026-07-13T12:00:00+00:00",
                    "archived": False,
                    "metadata": {},
                }
            },
            "assignments": {
                "work-1": {
                    "id": "work-1",
                    "title": "Language analysis",
                    "class_id": "english-9",
                    "subject": "English",
                    "instructions": "Analyse the extract.",
                    "created_by": "teacher",
                    "created_at": "2026-07-13T12:00:00+00:00",
                    "due_date": "2026-07-20",
                    "max_marks": 20,
                    "reward_tokens": 5,
                    "status": "published",
                    "publish_at": None,
                    "allow_late": True,
                    "resubmissions_allowed": True,
                    "rubric": [{"name": "Analysis", "marks": 20}],
                    "auto_grade": {},
                    "extensions": {"student": "2026-07-22"},
                    "private_comments": {"student": "Check paragraph structure."},
                    "submissions": {
                        "student": {
                            "submitted_at": "2026-07-14T12:00:00+00:00",
                            "answer": "My analysis",
                            "attachment": None,
                            "grade": 16,
                            "feedback": "Good explanation.",
                            "auto_graded": False,
                            "reward_awarded": True,
                            "late": False,
                            "marked_by": "teacher",
                            "marked_at": "2026-07-15T12:00:00+00:00",
                        }
                    },
                }
            },
            "assignment_templates": {
                "template-1": {
                    "id": "template-1",
                    "name": "Analysis task",
                    "owner": "teacher",
                    "created_at": "2026-07-13T12:00:00+00:00",
                    "fields": {"subject": "English", "max_marks": 20},
                }
            },
        }

    def test_complete_round_trip_and_verified_counts(self):
        original = self.sample_data()
        result = self.store.migrate_or_load(original)
        restored = self.store.load_snapshot()

        self.assertTrue(result.successful)
        self.assertTrue(result.migrated)
        self.assertEqual(restored["classes"]["english-9"]["teacher_usernames"], ["teacher"])
        self.assertEqual(restored["classes"]["english-9"]["student_usernames"], ["student"])
        submission = restored["assignments"]["work-1"]["submissions"]["student"]
        self.assertEqual(submission["grade"], 16)
        self.assertEqual(submission["marked_by"], "teacher")
        self.assertEqual(restored["assignments"]["work-1"]["extensions"]["student"], "2026-07-22")
        self.assertEqual(restored["assignment_templates"]["template-1"]["owner"], "teacher")

    def test_existing_database_wins_over_stale_json(self):
        original = self.sample_data()
        self.store.migrate_or_load(original)
        stale = {"classes": {}, "assignments": {}, "assignment_templates": {}}
        result = self.store.migrate_or_load(stale)
        self.assertFalse(result.migrated)
        self.assertEqual(result.actual["classes"], 1)
        self.assertEqual(result.actual["assignments"], 1)

    def test_database_rejects_student_as_class_teacher(self):
        invalid = self.sample_data()
        invalid["classes"]["english-9"]["teacher_usernames"] = ["student"]
        with self.assertRaises(ValueError):
            self.store.save_snapshot(invalid)
        self.assertEqual(self.store.database_counts()["classes"], 0)

    def test_database_rejects_submission_from_non_member(self):
        invalid = self.sample_data()
        invalid["classes"]["english-9"]["student_usernames"] = []
        with self.assertRaises(ValueError):
            self.store.save_snapshot(invalid)

    def test_save_hook_persists_database_and_removes_nested_json(self):
        data = self.sample_data()
        self.store.migrate_or_load(data)
        active_path = os.path.join(self.folder.name, "save_data.json")
        backup_path = os.path.join(self.folder.name, "save_backup.json")
        try:
            save_system.set_education_sync(self.store.save_snapshot)
            data["assignments"]["work-1"]["status"] = "archived"
            with patch.object(save_system, "SAVE_FILE", active_path), patch.object(save_system, "BACKUP_FILE", backup_path):
                save_system.save_save(data)
            with open(active_path, encoding="utf-8") as file:
                saved_json = json.load(file)
            self.assertNotIn("classes", saved_json)
            self.assertNotIn("assignments", saved_json)
            self.assertEqual(self.store.load_snapshot()["assignments"]["work-1"]["status"], "archived")
        finally:
            save_system.set_education_sync(None)


if __name__ == "__main__":
    unittest.main()
