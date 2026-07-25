import unittest
from unittest.mock import Mock, patch

from main import App


class QuitButtonTests(unittest.TestCase):
    def make_app(self):
        app = App.__new__(App)
        app.root = Mock()
        app.save_data = {"users": {}}
        return app

    @patch("main.save_system.save_save")
    @patch("main.messagebox.askyesno", return_value=False)
    def test_cancelling_quit_keeps_edupy_open(self, _confirm, save):
        app = self.make_app()
        app.quit_app()
        save.assert_not_called()
        app.root.destroy.assert_not_called()

    @patch("main.save_system.save_save")
    @patch("main.messagebox.askyesno", return_value=True)
    def test_confirming_quit_saves_then_closes(self, _confirm, save):
        app = self.make_app()
        app.quit_app()
        save.assert_called_once_with(app.save_data)
        app.root.destroy.assert_called_once_with()

    @patch("main.admin_dashboard.show_admin_dashboard")
    @patch("main.clear")
    def test_admin_home_uses_the_dedicated_dashboard(self, _clear, dashboard):
        app = self.make_app()
        app.current_user = "admin"
        app.save_data = {"users": {"admin": {"role": "admin"}}}
        app.main_menu()
        dashboard.assert_called_once_with(app.root, app)

    @patch("main.parent_portal.show_parent_dashboard")
    @patch("main.clear")
    def test_parent_home_uses_the_read_only_family_dashboard(self, _clear, dashboard):
        app = self.make_app()
        app.current_user = "parent"
        app.save_data = {"users": {"parent": {"role": "parent"}}}
        app.main_menu()
        dashboard.assert_called_once_with(app.root, app)


if __name__ == "__main__":
    unittest.main()
