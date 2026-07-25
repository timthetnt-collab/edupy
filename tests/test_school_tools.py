import os
import tempfile
import unittest

from sqlmodel import Session, select

import assignments
import school_tools
import ui
from auth import hash_password
from database import AccountDatabase
from experience_store import ExperienceStore
from models import Account, AssignmentRecord, ClassMembership, ClassRecord
from settings import THEMES


class SchoolToolStoreTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.database = AccountDatabase(os.path.join(self.folder.name, "school-tools.db"))
        self.database.create_tables()
        for username, role in (("student", "student"), ("teacher", "teacher"),
                               ("parent", "parent"), ("otherparent", "parent"), ("admin", "admin")):
            self.database.create_account(Account(username=username, password_hash=hash_password("SecurePass123"), role=role, year_group=8))
        with Session(self.database.engine) as session:
            accounts = {row.username: row for row in session.exec(select(Account)).all()}
            session.add(ClassRecord(id="8a", title="8A", subject="Maths", year_group=8, join_code="TOOLS8", created_at="now"))
            session.flush()
            session.add(ClassMembership(class_id="8a", account_id=accounts["teacher"].id, membership_role="teacher"))
            session.add(ClassMembership(class_id="8a", account_id=accounts["student"].id, membership_role="student"))
            session.commit()
        self.store = ExperienceStore(self.database.engine)

    def tearDown(self):
        self.database.engine.dispose(); self.folder.cleanup()

    def test_family_links_are_admin_controlled_and_read_only(self):
        self.assertFalse(self.store.set_family_link("teacher", "parent", "student"))
        self.assertFalse(self.store.set_family_link("admin", "teacher", "student"))
        self.assertTrue(self.store.set_family_link("admin", "parent", "student"))
        self.assertEqual(self.store.family_links("parent"), [{"parent": "parent", "student": "student"}])
        self.assertEqual(self.store.family_links("otherparent"), [])

    def test_goals_have_owner_and_linked_adult_permissions(self):
        goal = self.store.create_goal("student", "Complete two algebra practices", "Maths", "2026-12-01")
        self.assertIsNotNone(goal)
        self.assertEqual(self.store.goals("student", actor_username="otherparent"), [])
        self.assertTrue(self.store.set_family_link("admin", "parent", "student"))
        self.assertEqual(self.store.goals("student", actor_username="parent")[0]["id"], goal)
        self.assertEqual(self.store.goals("student", actor_username="teacher")[0]["id"], goal)
        self.assertTrue(self.store.complete_goal("student", goal, "Breaking it into two short sessions helped."))
        self.assertEqual(self.store.goals("student")[0]["status"], "completed")

    def test_assessment_papers_and_resources_enforce_roles(self):
        questions = school_tools.generate_assessment_questions(8, "Maths", ["power_notation", "prime_numbers"], 6, 2)
        self.assertEqual(len(questions), 6)
        self.assertTrue(all(item["prompt"] and item["answer"] for item in questions))
        self.assertIsNone(self.store.create_assessment_paper("student", "Number check", 8, "Maths", 45, ["number"], questions))
        paper = self.store.create_assessment_paper("teacher", "Number check", 8, "Maths", 45, ["number"], questions)
        self.assertIsNotNone(paper)
        self.assertEqual(self.store.assessment_papers("teacher")[0]["id"], paper)
        with Session(self.database.engine) as session:
            session.add(AssignmentRecord(id="paper-work", class_id="8a", pack_id=f"assessment:{paper}",
                title="Number check", subject="Maths", created_at="now", status="published"))
            session.commit()
        student_paper = self.store.assessment_papers_for_student("student")[0]
        self.assertNotIn("answer", student_paper["questions"][0])

        draft = self.store.create_teacher_resource("teacher", "Index laws guide", 8, "Maths", "power_notation", "A worked guide", "Explanation and worked example with enough detail.", False)
        published = self.store.create_teacher_resource("teacher", "Prime guide", 8, "Maths", "prime_numbers", "Prime number guide", "Explanation and worked example with enough detail.", True)
        self.assertIsNotNone(draft); self.assertIsNotNone(published)
        visible = self.store.teacher_resources("student")
        self.assertEqual([item["id"] for item in visible], [published])

    def test_safeguarding_workflow_preserves_restricted_history(self):
        self.assertTrue(self.store.submit_safety_report("student", "Content concern", "A detailed concern that needs review."))
        report = self.store.safety_reports("admin")[0]
        self.assertFalse(self.store.add_safeguarding_action("teacher", report["id"], "assigned", "Reviewing"))
        self.assertTrue(self.store.add_safeguarding_action("admin", report["id"], "assigned", "Assigned to the safeguarding lead."))
        active = self.store.safety_reports("admin", "active")[0]
        self.assertEqual(active["status"], "in_progress")
        self.assertTrue(self.store.add_safeguarding_action("admin", report["id"], "resolved", "Actions completed."))
        history = self.store.safeguarding_actions("admin", report["id"])
        self.assertEqual([item["action"] for item in history], ["assigned", "resolved"])


class SchoolToolLogicTests(unittest.TestCase):
    def test_structured_feedback_is_clear_and_actionable(self):
        result = assignments.structured_feedback("Accurate quotation", "Explain the verb", "The verb suggests urgency.", "Analyse another verb")
        for heading in ("What went well", "Your next step", "Corrected example", "Try this next"):
            self.assertIn(heading, result)

    def test_intervention_rows_explain_the_evidence(self):
        data = {
            "users": {"learner": {"recent_topics": [], "mastery": {"Maths": {"algebra": {"earned": 1, "possible": 4}}}}},
            "classes": {"8a": {"id": "8a", "student_usernames": ["learner"]}},
            "assignments": {
                "one": {"id": "one", "class_id": "8a", "status": "published", "submissions": {}},
                "two": {"id": "two", "class_id": "8a", "status": "published", "submissions": {}},
            },
        }
        rows = school_tools.intervention_rows(data, [data["classes"]["8a"]])
        self.assertEqual(rows[0]["student"], "learner")
        self.assertTrue(any("assignments submitted" in reason for reason in rows[0]["reasons"]))
        self.assertIn("Check in", rows[0]["suggestion"])

    def test_every_theme_meets_core_aa_contrast_checks(self):
        failures = {name: ui.theme_accessibility_report(theme)["checks"] for name, theme in THEMES.items()
                    if not ui.theme_accessibility_report(theme)["passes_aa"]}
        self.assertEqual(failures, {})


if __name__ == "__main__":
    unittest.main()
