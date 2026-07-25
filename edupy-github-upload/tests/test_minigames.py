import unittest

import minigames


class _Store:
    def __init__(self, extra): self.extra = extra
    def preferences(self, username): return {"extra_time_percent": self.extra}


class _App:
    current_user = "student"
    def __init__(self, extra): self.experience_store = _Store(extra)


class MinigameRulesTests(unittest.TestCase):
    def test_quick_maths_applies_and_limits_extra_time(self):
        self.assertEqual(minigames.quick_maths_time_limit(_App(0)), 30)
        self.assertEqual(minigames.quick_maths_time_limit(_App(50)), 45)
        self.assertEqual(minigames.quick_maths_time_limit(_App(500)), 60)

    def test_each_year_has_distinct_vocabulary(self):
        self.assertEqual(set(minigames.WORDS_BY_YEAR), set(range(7, 12)))
        self.assertTrue(all(len(words) >= 5 for words in minigames.WORDS_BY_YEAR.values()))

    def test_memory_match_reward_values_efficiency_without_excess(self):
        self.assertEqual(minigames.memory_match_xp(6), 16)
        self.assertEqual(minigames.memory_match_xp(9), 13)
        self.assertEqual(minigames.memory_match_xp(30), 10)


if __name__ == "__main__":
    unittest.main()
