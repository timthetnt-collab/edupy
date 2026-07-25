import unittest

import curriculum
import english
import maths


class QuestionTests(unittest.TestCase):
    def test_every_maths_topic_generates_checkable_questions(self):
        for year in range(7, 12):
            for topic, _ in curriculum.topics_for(year, "Maths"):
                for _ in range(8):
                    question = maths.generate_question_data(year, topic)
                    self.assertEqual(question["topic"], topic)
                    self.assertTrue(question["prompt"])
                    self.assertTrue(maths.answer_is_correct(question, str(question["answer"])))

    def test_wrong_maths_answers_are_rejected(self):
        question = {"type":"numeric", "answer":42, "accepted":[]}
        self.assertFalse(maths.answer_is_correct(question, "41"))

    def test_year_10_quadratics_do_not_generate_ambiguous_repeated_roots(self):
        for _ in range(30):
            question = maths.generate_question_data(10, "algebra")
            roots = question["answer"].split(",")
            self.assertNotEqual(roots[0], roots[1])

    def test_english_years_have_complete_topic_coverage(self):
        for year in range(7, 12):
            built_in = {q["topic"] for text in english.texts_for_year(year) for q in text["questions"]}
            available = built_in | {topic for y, topic in english.EXTRA_QUESTIONS if y == year}
            expected = {topic for topic, _ in curriculum.topics_for(year, "English")}
            self.assertTrue(expected.issubset(available))

    def test_english_bank_has_multiple_texts_and_varied_questions_per_year(self):
        for year in range(7, 12):
            texts = english.texts_for_year(year)
            self.assertGreaterEqual(len(texts), 3)
            self.assertGreaterEqual(sum(len(item["questions"]) for item in texts), 7)
            self.assertGreaterEqual(len({question["type"] for item in texts for question in item["questions"]}), 2)

    def test_english_marking_formats(self):
        mcq = {"type":"multiple_choice","answer":"A","max_score":1,"explanation":"Good"}
        self.assertEqual(english.mark_response(mcq,"A",7)[0],1)
        extended = {"type":"extended","keywords":["metaphor","reader","fear"],"max_score":6}
        score, maximum, _ = english.mark_response(extended,'The metaphor creates fear for the reader.',10)
        self.assertGreaterEqual(score,3); self.assertEqual(maximum,6)

    def test_english_keyword_matching_uses_whole_terms(self):
        question = {"type":"short","keywords":["rain"],"max_score":4}
        unrelated = english.mark_response(question,"The train arrived.",7)[0]
        relevant = english.mark_response(question,"The rain creates a gloomy mood.",7)[0]
        self.assertGreater(relevant, unrelated)


if __name__ == "__main__":
    unittest.main()
