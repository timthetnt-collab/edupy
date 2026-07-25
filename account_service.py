"""One safe entry point for login, account creation, and legacy migration."""

from dataclasses import dataclass
import re

import save_system
from auth import hash_password, verify_password
from database import AccountDatabase
from models import Account, ClassMembership
from sqlalchemy import delete
from sqlmodel import Session, select


USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_.-]{3,32}$")
VALID_ROLES = {"student", "teacher", "admin", "parent"}
MINIMUM_PASSWORD_LENGTH = 8


@dataclass
class MigrationResult:
    total_profiles: int
    created_accounts: int
    existing_accounts: int
    missing_passwords: tuple
    cleaned_plaintext_passwords: bool

    @property
    def successful(self):
        return not self.missing_passwords


def create_default_database():
    database = AccountDatabase()
    database.create_tables()
    return database


def validate_new_account(username, password, role, year_group):
    username = username.strip()
    if not USERNAME_PATTERN.fullmatch(username):
        return False, "Use 3–32 letters, numbers, dots, dashes, or underscores for the username."
    if role not in VALID_ROLES:
        return False, "Choose a valid account type."
    if len(password) < MINIMUM_PASSWORD_LENGTH:
        return False, f"Use a password with at least {MINIMUM_PASSWORD_LENGTH} characters."
    try:
        year = min(11, max(7, int(year_group)))
    except (TypeError, ValueError):
        return False, "Choose a year group from Year 7 to Year 11."
    return True, year


def create_account(data, database, username, password, role="student", year_group=7, force_password_change=False):
    valid, result = validate_new_account(username, password, role, year_group)
    if not valid:
        return False, result
    username = username.strip()
    year = result
    if username in data.get("users", {}) or database.get_account(username):
        return False, "That username already exists."

    account = Account(
        username=username,
        password_hash=hash_password(password),
        role=role,
        year_group=year,
        force_password_change=bool(force_password_change),
    )
    if not database.create_account(account):
        return False, "That username already exists."

    try:
        profile = save_system.default_user(role=role)
        profile["selected_year"] = year
        data.setdefault("users", {})[username] = profile
        save_system.append_audit(
            data,
            admin=None,
            action="create_school_account",
            target=username,
            details={"role": role},
        )
    except Exception:
        database.delete_account(username)
        data.get("users", {}).pop(username, None)
        raise
    return True, "Account created successfully."


def authenticate(database, username, password):
    account = database.get_account(username.strip())
    if not account or not account.is_active:
        return None
    if not verify_password(password, account.password_hash):
        return None
    return account


def change_password(database, username, new_password):
    if len(new_password) < MINIMUM_PASSWORD_LENGTH:
        return False, f"Use a password with at least {MINIMUM_PASSWORD_LENGTH} characters."
    account = database.update_account(
        username,
        password_hash=hash_password(new_password),
        force_password_change=False,
    )
    if not account:
        return False, "The account could not be found."
    return True, "Your password has been changed securely."


def reset_managed_password(data, database, actor_username, target_username, temporary_password):
    """Reset a managed account after checking school-role and class ownership."""
    actor = database.get_account(actor_username)
    target = database.get_account(target_username)
    if not actor or not target or actor_username == target_username:
        return False, "The account could not be reset."
    allowed = actor.role == "admin" and target.role in ("student", "teacher", "parent")
    if actor.role == "teacher" and target.role == "student":
        allowed = any(
            actor_username in item.get("teacher_usernames", []) and target_username in item.get("student_usernames", [])
            for item in data.get("classes", {}).values() if not item.get("archived")
        )
    if not allowed:
        return False, "You do not manage this account."
    if len(temporary_password) < MINIMUM_PASSWORD_LENGTH:
        return False, f"Use a temporary password with at least {MINIMUM_PASSWORD_LENGTH} characters."
    database.update_account(target_username, password_hash=hash_password(temporary_password), force_password_change=True)
    save_system.append_audit(data, admin=actor_username, action="reset_managed_password", target=target_username)
    return True, "Temporary password saved. The user must replace it at next sign-in."


def account_summaries(database):
    """Return admin-safe account details and never expose password hashes."""
    with Session(database.engine) as session:
        rows = session.exec(select(Account).order_by(Account.username)).all()
        return [{
            "username": row.username, "role": row.role, "year_group": row.year_group,
            "active": row.is_active, "force_password_change": row.force_password_change,
            "created_at": row.created_at.isoformat() if hasattr(row.created_at, "isoformat") else str(row.created_at),
        } for row in rows]


def sync_profile_roles(data, database):
    """Make secure account roles/year groups authoritative before school data loads."""
    corrected = []
    users = data.setdefault("users", {})
    for account in account_summaries(database):
        username = account["username"]
        profile = users.get(username)
        if profile is None:
            profile = save_system.default_user(role=account["role"])
            users[username] = profile
            corrected.append(username)
        before = (profile.get("role"), profile.get("admin"), profile.get("selected_year"))
        profile["role"] = account["role"]
        profile["admin"] = account["role"] == "admin"
        profile["selected_year"] = account["year_group"]
        after = (profile["role"], profile["admin"], profile["selected_year"])
        if before != after and username not in corrected:
            corrected.append(username)
    if corrected:
        data.setdefault("system", {})["account_profiles_synchronised"] = True
    return corrected


def _active_admin_count(database):
    return sum(item["role"] == "admin" and item["active"] for item in account_summaries(database))


def change_managed_role(data, database, actor_username, target_username, new_role):
    """Change a school role while preserving class and last-admin integrity."""
    if new_role not in VALID_ROLES:
        return False, "Choose student, teacher, parent, or admin."
    actor = database.get_account(actor_username)
    target = database.get_account(target_username)
    if not actor or actor.role != "admin" or not actor.is_active or not target:
        return False, "Only an active administrator can change roles."
    if target.role == new_role:
        return True, "The account already has that role."
    if target.role == "admin" and new_role != "admin" and target.is_active and _active_admin_count(database) <= 1:
        return False, "EduPy must always keep at least one active administrator."
    if new_role == "student":
        sole_teacher = [item.get("title", item.get("id", "class")) for item in data.get("classes", {}).values()
                        if target_username in item.get("teacher_usernames", []) and len(item.get("teacher_usernames", [])) <= 1 and not item.get("archived")]
        if sole_teacher:
            return False, "Assign another teacher to these classes first: " + ", ".join(sole_teacher[:3])

    # Keep relational memberships consistent with the account's new role.
    with Session(database.engine) as session:
        if new_role != "student":
            session.exec(delete(ClassMembership).where(
                ClassMembership.account_id == target.id,
                ClassMembership.membership_role == "student",
            ))
        if new_role not in ("teacher", "admin"):
            session.exec(delete(ClassMembership).where(
                ClassMembership.account_id == target.id,
                ClassMembership.membership_role == "teacher",
            ))
        session.commit()
    for item in data.get("classes", {}).values():
        if new_role != "student":
            item["student_usernames"] = [name for name in item.get("student_usernames", []) if name != target_username]
        if new_role not in ("teacher", "admin"):
            item["teacher_usernames"] = [name for name in item.get("teacher_usernames", []) if name != target_username]

    database.update_account(target_username, role=new_role)
    profile = data.setdefault("users", {}).setdefault(target_username, save_system.default_user(role=new_role))
    profile["role"] = new_role; profile["admin"] = new_role == "admin"
    save_system.append_audit(data, admin=actor_username, action="change_account_role", target=target_username,
                             details={"from": target.role, "to": new_role})
    return True, f"{target_username} is now a {new_role}."


def set_managed_account_active(data, database, actor_username, target_username, active):
    """Enable or disable a login without deleting linked school records."""
    actor = database.get_account(actor_username); target = database.get_account(target_username)
    if not actor or actor.role != "admin" or not actor.is_active or not target:
        return False, "Only an active administrator can manage accounts."
    if actor_username == target_username and not active:
        return False, "You cannot disable the account you are currently using."
    if target.role == "admin" and target.is_active and not active and _active_admin_count(database) <= 1:
        return False, "EduPy must always keep at least one active administrator."
    database.update_account(target_username, is_active=bool(active))
    save_system.append_audit(data, admin=actor_username,
        action="enable_account" if active else "disable_account", target=target_username)
    return True, f"{target_username} has been {'enabled' if active else 'disabled'}."


def migrate_legacy_accounts(data, database, clean_plaintext=True):
    """Copy JSON logins to SQLite, verify them, then remove readable passwords."""
    database.create_tables()
    users = data.setdefault("users", {})
    created = existing = 0
    missing_passwords = []

    for username, profile in users.items():
        current = database.get_account(username)
        if current:
            existing += 1
            continue
        password = profile.get("password")
        if not isinstance(password, str) or not password:
            missing_passwords.append(username)
            continue
        role = profile.get("role", "student")
        if role not in VALID_ROLES:
            role = "student"
        try:
            year = min(11, max(7, int(profile.get("selected_year", 7))))
        except (TypeError, ValueError):
            year = 7
        account = Account(
            username=username,
            password_hash=hash_password(password),
            role=role,
            year_group=year,
            force_password_change=password.lower() == "changeme",
        )
        if database.create_account(account):
            created += 1
        else:
            missing_passwords.append(username)

    all_present = set(users).issubset(database.usernames())
    cleaned = False
    if clean_plaintext and all_present and not missing_passwords:
        for profile in users.values():
            profile.pop("password", None)
        data.setdefault("system", {})["secure_accounts_migrated"] = True
        # Saving twice ensures both the main automatic save and its rolling backup
        # contain the cleaned form rather than an earlier readable password.
        save_system.save_save(data)
        save_system.save_save(data)
        cleaned = True

    return MigrationResult(len(users), created, existing, tuple(missing_passwords), cleaned)
