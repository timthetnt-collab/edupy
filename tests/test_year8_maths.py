import unittest

import curriculum
import learning_experience
import maths
import year8_maths


class Year8MathsCurriculumTests(unittest.TestCase):
    def test_supplied_chapter_sequence_and_unit_catalogue_are_complete(self):
        self.assertEqual(
            [title for _, title, _ in year8_maths.CHAPTERS],
            [
                "Number", "Geometry", "Probability", "Percentages", "Congruent Shapes",
                "Surface Area and Volume of Prisms", "Graphs", "Number: Rounding and Standard Form",
                "Interpreting Data", "Algebra", "Shape and Ratio", "Fractions and Decimals",
                "Proportion", "Circles", "Equations and Formulae", "Comparing Data",
            ],
        )
        topics = year8_maths.topics()
        self.assertGreaterEqual(len(topics), 90)
        self.assertEqual(len(topics), len({topic_id for topic_id, _ in topics}))
        self.assertEqual(topics, curriculum.topics_for(8, "Maths"))

    def test_every_chapter_reference_has_details_and_a_real_lesson_guide(self):
        for _, _, unit_ids in year8_maths.CHAPTERS:
            for unit_id in unit_ids:
                unit = year8_maths.details(unit_id)
                self.assertTrue(unit["title"])
                self.assertGreaterEqual(len(unit["focus"]), 25)
                guide = year8_maths.guide(unit_id)
                self.assertEqual(len(guide), 5)
                self.assertTrue(all(guide))

    def test_every_unit_repeatedly_generates_checkable_year_8_work(self):
        diagram_kinds = set()
        diagram_questions = 0
        for topic_id, _ in year8_maths.topics():
            for _ in range(12):
                question = year8_maths.generate(topic_id)
                self.assertEqual(question["topic"], topic_id)
                self.assertTrue(maths.answer_is_correct(question, str(question["answer"])))
                if question.get("diagram"):
                    diagram_questions += 1
                    diagram_kinds.add(question["diagram"]["kind"])
        self.assertGreaterEqual(diagram_questions, 400)
        self.assertTrue({
            "number_line", "coordinate_grid", "bar_chart", "pie_chart", "circle_parts",
            "fraction_strip", "percentage_bar", "sample_space", "shape_scale", "triangles", "prism",
        }.issubset(diagram_kinds))

    def test_year_8_diagnostic_records_progress_in_real_units(self):
        valid = {topic_id for topic_id, _ in curriculum.topics_for(8, "Maths")}
        diagnostic_topics = {topic for subject, topic, *_ in learning_experience.DIAGNOSTIC_BANK[8] if subject == "Maths"}
        self.assertTrue(diagnostic_topics.issubset(valid))

    def test_student_friendly_fraction_and_power_notation_is_accepted(self):
        fraction_question = {"type": "text", "answer": "7/4", "accepted": []}
        self.assertTrue(maths.answer_is_correct(fraction_question, "1 3/4"))
        power_question = {"type": "text", "answer": "2^3*3", "accepted": []}
        self.assertTrue(maths.answer_is_correct(power_question, "2³ × 3"))


if __name__ == "__main__":
    unittest.main()
