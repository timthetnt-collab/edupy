"""Compatibility wrappers for the retired profile-only login screens.

All account creation and authentication must go through App, which uses the
secure account database. Keeping these small wrappers prevents an old import
from accidentally reintroducing password-free login.
"""


def has_users(save_data):
    return bool(save_data.get("users"))


def show_login_screen(root, app, callback=None):
    del root, callback
    app.show_login_screen()


def show_create_user_screen(root, app, callback=None):
    del root, callback
    app.show_create_account_screen()
