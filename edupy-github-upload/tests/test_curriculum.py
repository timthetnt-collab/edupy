import unittest
from unittest.mock import patch

import curriculum
import save_system


class CurriculumTests(unittest.TestCase):
    def setUp(self):
        self.data = save_system.ensure_data_schema({"users": {"learner": save_system.default_user("secret")}})
        self.data["users"]["learner"]["selected_year"] = 9

    def test_every_year_has_maths_and_english_topics(self):
        for year in range(7, 12):
            self.assertGreaterEqual(len(curriculum.topics_for(year, "Maths")), 5)
            self.assertGreaterEqual(len(curriculum.topics_for(year, "English")), 5)

    @patch("save_system.save_save", lambda data: None)
    def test_mastery_and_recommendation_update(self):
        before = curriculum.recommend_next(self.data, "learner", "Maths")
        curriculum.record_mastery(self.data, "learner", "Maths", before["topic"], 1, 1)
        self.assertEqual(curriculum.mastery_percent(self.data["users"]["learner"], "Maths", before["topic"]), 100)
        after = curriculum.recommend_next(self.data, "learner", "Maths")
        self.assertNotEqual(before["topic"], after["topic"])


if __name__ == "__main__":
    unittest.main()
