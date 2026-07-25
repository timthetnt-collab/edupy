import datetime
import unittest
from unittest.mock import patch

import achievements
import save_system
import shop


class _App:
    current_user = "learner"
    def __init__(self):
        self.save_data = {"users": {"learner": save_system.default_user(role="student")}}


class RewardExperienceTests(unittest.TestCase):
    @patch("save_system.save_save", lambda data: None)
    def test_streak_bonus_requires_learning_and_can_only_be_claimed_once(self):
        app = _App()
        self.assertEqual(shop.claim_daily_reward(app), 0)
        user = app.save_data["users"]["learner"]
        user["token_earn_day"] = datetime.date.today().isoformat(); user["tokens_earned_today"] = 3
        self.assertEqual(shop.claim_daily_reward(app), 2)
        self.assertEqual(shop.claim_daily_reward(app), 0)
        self.assertEqual(user["tokens"], 2)

    @patch("save_system.save_save", lambda data: None)
    def test_achievements_reflect_real_activity(self):
        app = _App(); user = app.save_data["users"]["learner"]
        self.assertNotIn("first_steps", achievements.check_unlocks(app))
        user["maths_completed"] = 3; user["english_completed"] = 3
        unlocked = achievements.check_unlocks(app)
        self.assertIn("first_steps", unlocked); self.assertIn("balanced_learner", unlocked)


if __name__ == "__main__":
    unittest.main()
