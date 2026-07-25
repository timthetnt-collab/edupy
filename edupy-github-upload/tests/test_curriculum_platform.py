import os
import tempfile
import unittest

import curriculum
import english
import maths
import assignments
from auth import hash_password
from database import AccountDatabase
from experience_store import ExperienceStore
from models import Account


class UniversalCatalogueTests(unittest.TestCase):
    def test_every_year_and_subject_uses_chapters_units_and_subskills(self):
        for year in range(7, 12):
            for subject in ("Maths", "English"):
                chapters = curriculum.chapters_for(year, subject)
                self.assertGreaterEqual(len(chapters), 5)
                units = [unit for chapter in chapters for unit in chapter["units"]]
                self.assertEqual(len({unit["id"] for unit in units}), len(curriculum.topics_for(year, subject)))
                for unit in units:
                    self.assertGreaterEqual(len(unit["subskills"]), 1 if year == 8 and subject == "Maths" else 3)
                    self.assertEqual(unit["question_categories"], ["Fluency", "Applied", "Reasoning", "Exam-style"])
                    self.assertTrue(unit["resources"])
                    for prerequisite in unit["prerequisites"]:
                        self.assertTrue(curriculum.topic_details(year, subject, prerequisite))

    def test_search_filters_titles_subskills_year_subject_and_chapter(self):
        algebra = curriculum.curriculum_search("substitution", 7, "Maths", "algebra")
        self.assertTrue(algebra)
        self.assertTrue(all(item["year"] == 7 and item["subject"] == "Maths" and item["chapter_id"] == "algebra" for item in algebra))
        self.assertEqual(curriculum.curriculum_search("substitution", 7, "English"), [])

    def test_all_guided_pathways_have_ordered_units(self):
        self.assertGreaterEqual(len(curriculum.pathways()), 7)
        for pathway in curriculum.pathways():
            units = curriculum.pathway_units(pathway["id"])
            self.assertTrue(units, pathway["title"])
            self.assertTrue(all("subskills" in unit for unit in units))

    def test_every_unit_exposes_four_modes_and_uses_its_own_progress_id(self):
        for year in range(7, 12):
            for topic_id, _ in curriculum.topics_for(year, "Maths"):
                question = maths.generate_question_data(year, topic_id, difficulty=4, category="Exam-style")
                self.assertEqual(question["topic"], topic_id)
                self.assertEqual(question["difficulty"], 4)
                self.assertEqual(question["category"], "Exam-style")
            for topic_id, _ in curriculum.topics_for(year, "English"):
                self.assertIn((year, topic_id), english.EXTRA_QUESTIONS)
                self.assertEqual(english.EXTRA_QUESTIONS[(year, topic_id)]["topic"], topic_id)

    def test_curriculum_assignment_targets_round_trip_through_pack_ids(self):
        target = assignments.curriculum_target("curriculum:10:Maths:algebra_reasoning")
        self.assertEqual(target["year"], 10)
        self.assertEqual(target["subject"], "Maths")
        self.assertEqual(target["id"], "algebra_reasoning")
        self.assertIsNone(assignments.curriculum_target("ordinary-pack"))


class CurriculumExperienceTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.database = AccountDatabase(os.path.join(self.folder.name, "curriculum.db"))
        self.database.create_tables()
        self.database.create_account(Account(username="student", password_hash=hash_password("SecurePass123"), role="student", year_group=9))
        self.store = ExperienceStore(self.database.engine)

    def tearDown(self):
        self.database.engine.dispose(); self.folder.cleanup()

    def test_bookmarks_pathways_adaptation_and_assessments_round_trip(self):
        self.assertTrue(self.store.toggle_bookmark("student", 9, "Maths", "algebra"))
        self.assertEqual(self.store.bookmarks("student")[0]["topic"], "algebra")
        self.assertFalse(self.store.toggle_bookmark("student", 9, "Maths", "algebra"))
        self.assertEqual(self.store.bookmarks("student"), [])

        self.assertTrue(self.store.enroll_pathway("student", "catch_up_maths"))
        self.assertIn("catch_up_maths", self.store.active_pathways("student"))
        self.assertTrue(self.store.enroll_pathway("student", "catch_up_maths", False))
        self.assertNotIn("catch_up_maths", self.store.active_pathways("student"))

        first = self.store.record_adaptive_result("student", "Maths", "algebra", True, 1)
        second = self.store.record_adaptive_result("student", "Maths", "algebra", True, 1)
        self.assertEqual(first["difficulty"], 1)
        self.assertEqual(second["difficulty"], 2)
        easier = self.store.record_adaptive_result("student", "Maths", "algebra", False, 1)
        self.assertEqual(easier["difficulty"], 1)

        self.assertTrue(self.store.record_topic_assessment("student", 9, "Maths", "algebra", "starting", 3, 5))
        self.assertTrue(self.store.record_topic_assessment("student", 9, "Maths", "algebra", "end", 4, 5))
        records = self.store.topic_assessments("student", "algebra")
        self.assertEqual(len(records), 2)
        end = next(item for item in records if item["type"] == "end")
        self.assertIsNotNone(end["retention_due"])


if __name__ == "__main__":
    unittest.main()
