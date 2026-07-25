import datetime
import os
import tempfile
import unittest
from unittest.mock import patch

from auth import hash_password
from database import AccountDatabase
from experience_store import ExperienceStore
import curriculum
import learning_experience
from models import Account
import save_system
import assignments
import classes
import teacher_dashboard


class ExperienceStoreTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.database = AccountDatabase(os.path.join(self.folder.name, "edupy.db"))
        self.database.create_tables()
        for username, role in (("student", "student"), ("teacher", "teacher"), ("admin", "admin")):
            self.database.create_account(Account(username=username, password_hash=hash_password("SecurePass123"), role=role, year_group=9))
        self.store = ExperienceStore(self.database.engine)

    def tearDown(self):
        self.database.engine.dispose()
        self.folder.cleanup()

    def test_preferences_are_saved_and_safely_limited(self):
        self.assertTrue(self.store.update_preferences("student", reduced_motion=True, high_contrast=True, font_scale=999, extra_time_percent=-5))
        preferences = self.store.preferences("student")
        self.assertTrue(preferences["reduced_motion"])
        self.assertTrue(preferences["high_contrast"])
        self.assertEqual(preferences["font_scale"], 140)
        self.assertEqual(preferences["extra_time_percent"], 0)

    def test_diagnostic_and_lesson_progress_round_trip(self):
        results = [
            {"subject": "Maths", "topic": "algebra", "earned": 1, "possible": 1},
            {"subject": "English", "topic": "analysis", "earned": 0, "possible": 1},
        ]
        self.assertIsNotNone(self.store.record_diagnostic("student", 9, results))
        latest = self.store.latest_diagnostic("student")
        self.assertEqual(len(latest), 2)
        self.assertEqual(sum(item["earned"] for item in latest), 1)
        self.assertTrue(self.store.record_lesson_view("student", "Maths", "algebra"))
        self.assertTrue(self.store.record_lesson_view("student", "Maths", "algebra", completed=True))
        self.assertEqual(self.store.counts()["lesson_progress"], 1)
        recent = self.store.recent_lessons("student")
        self.assertEqual(recent[0]["topic"], "algebra")
        self.assertTrue(recent[0]["completed"])

    def test_revision_plan_creation_and_task_completion(self):
        date = (datetime.date.today() + datetime.timedelta(days=21)).isoformat()
        tasks = [{"subject": "Maths", "topic": "algebra", "due_date": date}]
        self.assertTrue(self.store.create_revision_plan("student", "Mock exam", date, tasks))
        plan = self.store.revision_plan("student")
        self.assertEqual(plan["title"], "Mock exam")
        self.assertTrue(self.store.set_revision_task("student", plan["tasks"][0]["id"]))
        self.assertTrue(self.store.revision_plan("student")["tasks"][0]["completed"])
        self.assertFalse(self.store.set_revision_task("teacher", plan["tasks"][0]["id"]))
        self.assertTrue(self.store.delete_revision_plan("student"))
        self.assertIsNone(self.store.revision_plan("student"))

    def test_safety_and_privacy_records_are_admin_only(self):
        self.assertTrue(self.store.submit_safety_report("student", "Content concern", "This content needs an adult review."))
        self.assertEqual(self.store.my_safety_reports("student")[0]["status"], "open")
        self.assertEqual(self.store.safety_reports("student"), [])
        reports = self.store.safety_reports("admin")
        self.assertEqual(len(reports), 1)
        self.assertFalse(self.store.resolve_safety_report("teacher", reports[0]["id"]))
        self.assertTrue(self.store.resolve_safety_report("admin", reports[0]["id"]))
        self.assertEqual(self.store.my_safety_reports("student")[0]["status"], "resolved")

        self.assertTrue(self.store.create_privacy_request("student", "export"))
        self.assertFalse(self.store.create_privacy_request("student", "export"))
        self.assertEqual(self.store.my_privacy_requests("student")[0]["request_type"], "export")
        self.assertEqual(self.store.privacy_requests("teacher"), [])
        requests = self.store.privacy_requests("admin")
        self.assertEqual(len(requests), 1)
        self.assertTrue(self.store.resolve_privacy_request("admin", requests[0]["id"]))


class LearningContentTests(unittest.TestCase):
    def test_diagnostic_banks_match_each_year_and_have_valid_answers(self):
        for year in range(7, 12):
            questions = learning_experience.DIAGNOSTIC_BANK[year]
            self.assertEqual(len(questions), 8)
            self.assertEqual(sum(item[0] == "Maths" for item in questions), 4)
            self.assertEqual(sum(item[0] == "English" for item in questions), 4)
            for _subject, _topic, _prompt, choices, answer in questions:
                self.assertIn(answer, choices)

    def test_every_curriculum_topic_has_a_complete_lesson(self):
        for year in range(7, 12):
            for subject in ("Maths", "English"):
                for topic_id, _title in curriculum.topics_for(year, subject):
                    guide = learning_experience.lesson_guide(year, subject, topic_id)
                    for field in ("title", "explanation", "steps", "example", "mistake", "vocabulary"):
                        self.assertTrue(guide[field])

    @patch("save_system.save_save", lambda data: None)
    def test_learning_plan_prioritises_recorded_weakness(self):
        profile = save_system.default_user(role="student")
        profile["selected_year"] = 9
        data = {"users": {"student": profile}}
        curriculum.record_mastery(data, "student", "Maths", "algebra", 0, 1)
        plan = learning_experience.learning_plan(data, "student", 1)
        self.assertEqual(plan[0]["subject"], "Maths")
        self.assertEqual(plan[0]["topic"], "algebra")

    def test_revision_tasks_are_spaced_before_the_exam(self):
        profile = save_system.default_user(role="student")
        profile["selected_year"] = 8
        data = {"users": {"student": profile}}
        exam = datetime.date.today() + datetime.timedelta(days=30)
        tasks = learning_experience.generate_revision_tasks(data, "student", exam.isoformat(), 10)
        self.assertEqual(len(tasks), 10)
        self.assertTrue(all(datetime.date.today() < datetime.date.fromisoformat(task["due_date"]) < exam for task in tasks))
        with self.assertRaises(ValueError):
            learning_experience.generate_revision_tasks(data, "student", datetime.date.today().isoformat())

    def test_diagnostic_summary_groups_subject_scores(self):
        summary = learning_experience.diagnostic_summary([
            {"subject": "Maths", "earned": 1, "possible": 1},
            {"subject": "Maths", "earned": 0, "possible": 1},
            {"subject": "English", "earned": 3, "possible": 4},
        ])
        self.assertEqual(summary, {"Maths": 50, "English": 75})

    @patch("save_system.save_save", lambda data: None)
    def test_teacher_insights_flag_evidence_without_labelling_students(self):
        data = save_system.ensure_data_schema({"users": {}})
        data["users"]["teacher"] = save_system.default_user(role="teacher")
        data["users"]["student"] = save_system.default_user(role="student")
        classes.create_class(data, "class-9", "Class 9", ["teacher"], ["student"], year_group=9, actor="teacher")
        due = (datetime.date.today() - datetime.timedelta(days=2)).isoformat()
        assignments.create_assignment(data, "Overdue", "class-9", due_date=due, created_by="teacher", status="published")
        insights = teacher_dashboard.class_insights(data, classes.get_classes(data, "teacher", "teacher"))
        self.assertTrue(any(title == "Missing overdue work" for title, *_ in insights))

    @patch("save_system.save_save", lambda data: None)
    def test_student_snapshot_summarises_work_and_weak_topics(self):
        data = save_system.ensure_data_schema({"users": {}})
        data["users"]["teacher"] = save_system.default_user(role="teacher")
        data["users"]["student"] = save_system.default_user(role="student")
        classes.create_class(data, "class-9", "Class 9", ["teacher"], ["student"], year_group=9, actor="teacher")
        aid = assignments.create_assignment(data, "Task", "class-9", created_by="teacher", status="published")
        assignments.submit_assignment(data, aid, "student", "work")
        assignments.grade_submission(data, aid, "student", 40, "Review this", "teacher")
        curriculum.record_mastery(data, "student", "Maths", "algebra", 0, 1)
        snapshot = teacher_dashboard.student_snapshot(data, "student", classes.get_classes(data, "teacher", "teacher"))
        self.assertEqual(snapshot["submitted"], 1)
        self.assertEqual(snapshot["average_grade"], 40)
        self.assertEqual(snapshot["weakest_topics"][0]["topic"], "algebra")


if __name__ == "__main__":
    unittest.main()
