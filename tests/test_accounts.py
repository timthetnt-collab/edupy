import os
import tempfile
import unittest
from unittest.mock import patch

import account_service
import save_system
import classes
from auth import hash_password
from database import AccountDatabase
from models import Account


class SecureAccountTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.database = AccountDatabase(os.path.join(self.folder.name, "accounts.db"))
        self.database.create_tables()

    def tearDown(self):
        self.database.engine.dispose()
        self.folder.cleanup()

    @patch("save_system.save_save", lambda data: None)
    def test_legacy_accounts_are_hashed_verified_and_cleaned(self):
        data = {
            "users": {
                "learner": {
                    "password": "Learning123",
                    "role": "student",
                    "selected_year": 9,
                }
            }
        }
        result = account_service.migrate_legacy_accounts(data, self.database)
        account = self.database.get_account("learner")

        self.assertTrue(result.successful)
        self.assertTrue(result.cleaned_plaintext_passwords)
        self.assertNotIn("password", data["users"]["learner"])
        self.assertNotEqual(account.password_hash, "Learning123")
        self.assertTrue(account.password_hash.startswith("$argon2"))
        self.assertIsNotNone(account_service.authenticate(self.database, "learner", "Learning123"))
        self.assertIsNone(account_service.authenticate(self.database, "learner", "wrong-password"))

    @patch("save_system.save_save", lambda data: None)
    def test_new_accounts_reject_duplicates_and_weak_passwords(self):
        data = {"users": {}}
        ok, _ = account_service.create_account(
            data, self.database, "student.one", "StrongPass123", "student", 8
        )
        duplicate, _ = account_service.create_account(
            data, self.database, "student.one", "AnotherPass123", "student", 8
        )
        weak, _ = account_service.create_account(
            data, self.database, "student.two", "short", "student", 8
        )

        self.assertTrue(ok)
        self.assertFalse(duplicate)
        self.assertFalse(weak)
        self.assertNotIn("password", data["users"]["student.one"])

    @patch("save_system.save_save", lambda data: None)
    def test_disabled_account_cannot_log_in(self):
        data = {"users": {}}
        account_service.create_account(
            data, self.database, "teacher.one", "TeacherPass123", "teacher", 7
        )
        self.database.update_account("teacher.one", is_active=False)
        self.assertIsNone(account_service.authenticate(self.database, "teacher.one", "TeacherPass123"))

    @patch("save_system.save_save", lambda data: None)
    def test_temporary_password_must_be_replaced(self):
        data = {"users": {}}
        account_service.create_account(
            data, self.database, "managed.student", "Temporary123", "student", 7,
            force_password_change=True,
        )
        account = account_service.authenticate(self.database, "managed.student", "Temporary123")
        self.assertTrue(account.force_password_change)

        ok, _ = account_service.change_password(self.database, "managed.student", "MyNewPassword123")
        refreshed = account_service.authenticate(self.database, "managed.student", "MyNewPassword123")
        self.assertTrue(ok)
        self.assertFalse(refreshed.force_password_change)
        self.assertIsNone(account_service.authenticate(self.database, "managed.student", "Temporary123"))

    @patch("save_system.save_save", lambda data: None)
    def test_migration_does_not_clean_if_an_account_cannot_be_migrated(self):
        data = {
            "users": {
                "ready": {"password": "ReadyPass123", "role": "student"},
                "missing": {"role": "student"},
            }
        }
        result = account_service.migrate_legacy_accounts(data, self.database)
        self.assertFalse(result.successful)
        self.assertFalse(result.cleaned_plaintext_passwords)
        self.assertIn("password", data["users"]["ready"])

    def test_legacy_json_account_and_full_save_routes_are_disabled(self):
        data = {"users": {}}
        self.assertFalse(save_system.create_user(data, "unsafe", "Password123"))
        self.assertNotIn("unsafe", data["users"])
        with self.assertRaises(RuntimeError): save_system.export_save(data, "unused.json")
        with self.assertRaises(RuntimeError): save_system.import_save("unused.json")

    @patch("save_system.save_save", lambda data: None)
    def test_password_characters_are_matched_exactly(self):
        data = {"users": {}}
        password = " Secure phrase 123 "
        self.assertTrue(account_service.create_account(data, self.database, "exact.password", password, "student", 8)[0])
        self.assertIsNotNone(account_service.authenticate(self.database, "exact.password", password))
        self.assertIsNone(account_service.authenticate(self.database, "exact.password", password.strip()))

    @patch("save_system.save_save", lambda data: None)
    def test_teacher_can_reset_only_students_they_manage(self):
        data = {"users": {}}
        for username, role in (("teacher", "teacher"), ("other", "teacher"), ("student", "student")):
            self.assertTrue(account_service.create_account(data, self.database, username, "OriginalPass123", role, 9)[0])
        self.assertTrue(classes.create_class(data, "managed", "Managed", ["teacher"], ["student"], actor="teacher"))
        ok, _ = account_service.reset_managed_password(data, self.database, "teacher", "student", "TemporaryPass123")
        denied, _ = account_service.reset_managed_password(data, self.database, "other", "student", "AnotherPass123")
        self.assertTrue(ok); self.assertFalse(denied)
        self.assertIsNone(account_service.authenticate(self.database, "student", "OriginalPass123"))
        refreshed = account_service.authenticate(self.database, "student", "TemporaryPass123")
        self.assertTrue(refreshed.force_password_change)

    @patch("save_system.save_save", lambda data: None)
    def test_admin_role_changes_are_audited_and_keep_class_roles_consistent(self):
        data = {"users": {}}
        for username, role in (("admin", "admin"), ("learner", "student")):
            self.assertTrue(account_service.create_account(data, self.database, username, "OriginalPass123", role, 8)[0])
        data["classes"] = {"8a": {"id":"8a","title":"8A","student_usernames":["learner"],"teacher_usernames":["admin"],"archived":False}}
        ok, message = account_service.change_managed_role(data, self.database, "admin", "learner", "teacher")
        self.assertTrue(ok, message)
        self.assertEqual(self.database.get_account("learner").role, "teacher")
        self.assertEqual(data["users"]["learner"]["role"], "teacher")
        self.assertNotIn("learner", data["classes"]["8a"]["student_usernames"])
        self.assertEqual(data["audit_log"][-1]["action"], "change_account_role")

    @patch("save_system.save_save", lambda data: None)
    def test_last_active_admin_cannot_be_demoted_or_disabled(self):
        data = {"users": {}}
        self.assertTrue(account_service.create_account(data, self.database, "admin", "OriginalPass123", "admin", 7)[0])
        demoted, _ = account_service.change_managed_role(data, self.database, "admin", "admin", "teacher")
        disabled, _ = account_service.set_managed_account_active(data, self.database, "admin", "admin", False)
        self.assertFalse(demoted)
        self.assertFalse(disabled)
        self.assertEqual(self.database.get_account("admin").role, "admin")
        self.assertTrue(self.database.get_account("admin").is_active)

    @patch("save_system.save_save", lambda data: None)
    def test_account_directory_never_returns_password_material(self):
        data = {"users": {}}
        self.assertTrue(account_service.create_account(data, self.database, "admin", "OriginalPass123", "admin", 7)[0])
        record = account_service.account_summaries(self.database)[0]
        self.assertNotIn("password_hash", record)
        self.assertNotIn("OriginalPass123", record.values())
        self.assertEqual(record["role"], "admin")

    @patch("save_system.save_save", lambda data: None)
    def test_secure_database_repairs_stale_or_missing_profile_roles(self):
        data = {"users": {"teacher": {"role": "student", "admin": False, "selected_year": 11}}}
        self.assertTrue(account_service.create_account(data, self.database, "admin", "OriginalPass123", "admin", 9)[0])
        # Re-introduce a deliberately stale role after secure account creation.
        data["users"]["admin"].update({"role":"student","admin":False,"selected_year":7})
        self.database.create_account(Account(
            username="teacher", password_hash=hash_password("TeacherPass123"),
            role="teacher", year_group=8,
        ))
        repairs = account_service.sync_profile_roles(data, self.database)
        self.assertCountEqual(repairs, ["admin", "teacher"])
        self.assertEqual(data["users"]["admin"]["role"], "admin")
        self.assertTrue(data["users"]["admin"]["admin"])
        self.assertEqual(data["users"]["admin"]["selected_year"], 9)
        self.assertEqual(data["users"]["teacher"]["role"], "teacher")
        self.assertEqual(data["users"]["teacher"]["selected_year"], 8)

    @patch("save_system.save_save", lambda data: None)
    def test_parent_accounts_are_valid_but_cannot_hold_class_memberships(self):
        data = {"users": {}}
        for username, role in (("admin", "admin"), ("learner", "student")):
            self.assertTrue(account_service.create_account(data, self.database, username, "OriginalPass123", role, 8)[0])
        data["classes"] = {"8a": {"id":"8a","title":"8A","student_usernames":["learner"],"teacher_usernames":["admin"],"archived":False}}
        ok, message = account_service.change_managed_role(data, self.database, "admin", "learner", "parent")
        self.assertTrue(ok, message)
        self.assertEqual(self.database.get_account("learner").role, "parent")
        self.assertNotIn("learner", data["classes"]["8a"]["student_usernames"])


if __name__ == "__main__":
    unittest.main()
