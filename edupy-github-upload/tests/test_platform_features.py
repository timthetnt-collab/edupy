import os
import tempfile
import unittest

from sqlmodel import Session, select

import platform_features
from settings import THEMES
from auth import hash_password
from database import AccountDatabase
from experience_store import ExperienceStore
from models import Account, ClassMembership, ClassRecord


class PlatformFeatureStoreTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.database = AccountDatabase(os.path.join(self.folder.name, "platform.db"))
        self.database.create_tables()
        for username, role in (("student", "student"), ("teacher", "teacher"), ("admin", "admin")):
            self.database.create_account(Account(username=username, password_hash=hash_password("SecurePass123"), role=role, year_group=8))
        self.store = ExperienceStore(self.database.engine)
        with Session(self.database.engine) as session:
            accounts = {row.username: row for row in session.exec(select(Account)).all()}
            session.add(ClassRecord(id="8a", title="8A", subject="General", year_group=8, join_code="ABC123", created_at="now"))
            session.flush()
            session.add(ClassMembership(class_id="8a", account_id=accounts["teacher"].id, membership_role="teacher"))
            session.add(ClassMembership(class_id="8a", account_id=accounts["student"].id, membership_role="student"))
            session.commit()

    def tearDown(self):
        self.database.engine.dispose(); self.folder.cleanup()

    def test_question_builder_and_admin_moderation(self):
        question_id = self.store.create_custom_question(
            "teacher", 8, "Maths", "number", "multiple_choice",
            "Which value is the square of four?", "16", ["8", "12", "16"], 1, True,
        )
        self.assertIsNotNone(question_id)
        self.assertEqual(self.store.custom_questions("teacher")[0]["status"], "pending")
        self.assertEqual(self.store.custom_questions("student"), [])
        self.assertFalse(self.store.moderate_question("teacher", question_id, "approved"))
        self.assertTrue(self.store.moderate_question("admin", question_id, "approved"))
        self.assertEqual(self.store.custom_questions("student")[0]["answer"], "16")
        self.assertTrue(self.store.report_content("student", "The wording is unclear", question_id))
        self.assertEqual(len(self.store.content_reports("admin")), 1)

    def test_question_builder_rejects_malformed_content(self):
        self.assertIsNone(self.store.create_custom_question(
            "teacher", "not-a-year", "Maths", "number", "short",
            "Explain how you found the answer.", "4",
        ))
        self.assertIsNone(self.store.create_custom_question(
            "teacher", 8, "Maths", "number", "short",
            "Explain how you found the answer.", "",
        ))
        self.assertIsNone(self.store.create_custom_question(
            "teacher", 8, "Maths", "number", "multiple_choice",
            "Which option is correct here?", "A", ["A", "A"], submit=True,
        ))

    def test_question_moderation_is_single_use_and_reports_need_real_content(self):
        draft_id = self.store.create_custom_question(
            "teacher", 8, "English", "reading", "short",
            "What impression does the writer create?", "A tense atmosphere.",
        )
        self.assertFalse(self.store.moderate_question("admin", draft_id, "approved"))
        submitted_id = self.store.create_custom_question(
            "teacher", 8, "English", "reading", "short",
            "What impression does the writer create?", "A tense atmosphere.", submit=True,
        )
        self.assertTrue(self.store.moderate_question("admin", submitted_id, "approved"))
        self.assertFalse(self.store.moderate_question("admin", submitted_id, "rejected"))
        self.assertFalse(self.store.report_content("student", "This is not valid", 999999))
        self.assertFalse(self.store.report_content("student", "This is not valid", "bad-id"))

    def test_student_owned_tools_round_trip(self):
        self.assertTrue(self.store.record_mock_exam("student", 8, "Maths", 8, 10, 320, 2))
        self.assertFalse(self.store.record_mock_exam("student", 8, "Science", 8, 10, 320, 2))
        self.assertFalse(self.store.record_mock_exam("student", "bad-year", "Maths", 8, 10, 320, 2))
        self.assertFalse(self.store.record_mock_exam("student", 8, "Maths", 12, 10, 320, 2))
        self.assertEqual(self.store.mock_exams("student")[0]["flagged"], 2)
        item = self.store.add_portfolio_item("student", "My best analysis", "English", "A comparison", "Opening paragraph")
        self.assertIsNotNone(item)
        self.assertEqual(self.store.portfolio("student")[0]["subject"], "English")
        self.assertTrue(self.store.notify("student", "Feedback ready", "Your response was marked."))
        notification = self.store.notifications("student")[0]
        self.assertFalse(notification["read"])
        self.assertTrue(self.store.notifications("student", notification["id"])[0]["read"])
        self.assertTrue(self.store.wellbeing_checkin("student", 4, "Ready to learn"))
        self.assertFalse(self.store.wellbeing_checkin("student", "not-a-mood"))
        self.assertEqual(self.store.my_wellbeing("student")[0]["mood"], 4)

    def test_accessibility_mistakes_and_certificates(self):
        self.assertTrue(self.store.update_accessibility_profile("student", dyslexia_friendly=True, reading_ruler=True))
        preferences = self.store.preferences("student")
        self.assertTrue(preferences["dyslexia_friendly"])
        self.assertTrue(preferences["reading_ruler"])
        mistake = self.store.add_mistake("student", 8, "Maths", "number", "2 + 2", "5", "4")
        self.assertEqual(self.store.mistakes("student")[0]["id"], mistake)
        self.store.mistakes("student", master_id=mistake)
        self.assertEqual(self.store.mistakes("student"), [])
        self.assertTrue(self.store.award_certificate("student", "first", "First milestone", "Completed."))
        self.assertFalse(self.store.award_certificate("student", "first", "Duplicate", "No."))
        self.assertEqual(len(self.store.certificates("student")), 1)

    def test_repeated_unresolved_mistakes_are_updated_not_duplicated(self):
        first = self.store.add_mistake("student", 8, "Maths", "number", "2 + 2", "5", "4")
        second = self.store.add_mistake("student", 8, "Maths", "number", "2 + 2", "6", "4")
        self.assertEqual(first, second)
        rows = self.store.mistakes("student")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["response"], "6")

    def test_live_classroom_permissions_and_responses(self):
        self.assertIsNone(self.store.create_activity("student", "8a", "Poll", "poll", "Ready?", ["Yes", "No"]))
        activity = self.store.create_activity("teacher", "8a", "Poll", "poll", "Ready?", ["Yes", "No"])
        self.assertIsNotNone(activity)
        self.assertTrue(self.store.respond_activity("student", activity, "Yes"))
        self.assertEqual(self.store.activities("teacher")[0]["responses"], ["Yes"])
        self.assertTrue(self.store.close_activity("teacher", activity))
        self.assertEqual(self.store.activities("student"), [])

    def test_classroom_activities_validate_options_and_responses(self):
        self.assertIsNone(self.store.create_activity("teacher", "8a", "Poll", "poll", "Ready?", ["Yes", "Yes"]))
        activity = self.store.create_activity("teacher", "8a", "Quiz", "quiz", "Choose one", ["A", "B"])
        self.assertIsNotNone(activity)
        self.assertFalse(self.store.respond_activity("student", activity, "forged-option"))
        self.assertFalse(self.store.respond_activity("student", "bad-id", "B"))
        self.assertTrue(self.store.respond_activity("student", activity, "B"))


class PlatformFeatureLogicTests(unittest.TestCase):
    def test_writing_feedback_is_transparent_and_actionable(self):
        report = platform_features.writing_feedback(
            "The storm arrived suddenly.\nThe windows shook; however, Maya remained calm because she had prepared carefully.", 8
        )
        self.assertIn("scores", report)
        self.assertEqual(set(report["scores"]), {"Development", "Structure", "Sentence control", "Vocabulary", "Punctuation"})
        self.assertTrue(report["feedback"])
        self.assertGreater(report["word_count"], 10)

    def test_reference_inspired_themes_have_complete_accessible_palettes(self):
        required = {"bg","fg","muted","panel","panel_alt","accent","accent_soft","border","input_bg","button_bg","button_fg","button_hover_bg"}
        for name in ("Study Paper","Academy","Focus Mint"):
            self.assertTrue(required.issubset(THEMES[name]))
            self.assertNotEqual(THEMES[name]["bg"], THEMES[name]["fg"])

    def test_coverage_map_counts_assignments_and_mastery_without_rankings(self):
        data={"users":{"student":{"mastery":{"Maths":{"power_notation":{"attempts":2,"earned":2,"possible":2}}}}},"assignments":{
            "a":{"id":"a","class_id":"8a","pack_id":"curriculum:8:Maths:power_notation","status":"published","submissions":{}}
        }}
        cls={"id":"8a","year_group":8,"student_usernames":["student"]}
        row=next(item for item in platform_features.coverage_rows(data,cls) if item["topic"]=="power_notation")
        self.assertEqual(row["assigned"],1)
        self.assertEqual(row["secure"],1)
        self.assertNotIn("student",row)


if __name__ == "__main__":
    unittest.main()
