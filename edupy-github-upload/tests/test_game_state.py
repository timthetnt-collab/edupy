import unittest

import game_state
import save_system


class GameStateTests(unittest.TestCase):
    def setUp(self):
        self.user = save_system.default_user(role="student")

    def test_daily_progress_resets_on_a_new_day(self):
        state = game_state.ensure_game_state(self.user, "2026-07-14")
        state["daily"]["correct_answers"] = 3
        state = game_state.ensure_game_state(self.user, "2026-07-15")
        self.assertEqual(state["daily"]["correct_answers"], 0)
        self.assertEqual(state["daily"]["claimed"], [])

    def test_events_advance_only_known_quest_counters(self):
        game_state.record_event(self.user, "correct_answers", 2)
        game_state.record_event(self.user, "unknown", 99)
        daily = game_state.ensure_game_state(self.user)["daily"]
        self.assertEqual(daily["correct_answers"], 2)
        self.assertNotIn("unknown", daily)

    def test_quest_progress_is_capped_at_target(self):
        game_state.record_event(self.user, "correct_answers", 50)
        current, target = game_state.quest_progress(self.user, game_state.DAILY_QUESTS[0])
        self.assertEqual((current, target), (3, 3))


if __name__ == "__main__":
    unittest.main()
