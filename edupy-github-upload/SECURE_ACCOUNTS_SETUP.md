# EduPy secure accounts

EduPy now keeps login details, classes, memberships, assignments, submissions,
extensions, private teacher notes, assignment templates, learner progress, XP,
tokens, reward history, themes, achievements, and curriculum mastery in
`edupy.db`.
Passwords are protected with Argon2 hashes and are no longer written into
`save_data.json`.

## Starting EduPy

Double-click **Start EduPy.bat** in the EduPy folder. This starts the app with
its private Python environment and the correct security packages.

## Setting up a copied project or a new computer

1. Install Python if the computer does not already have it.
2. Double-click **Setup EduPy.bat** while connected to the internet.
3. Wait for the message saying EduPy is ready.
4. Double-click **Start EduPy.bat**.

The `.venv` folder is private project machinery. Do not edit it or copy it to
another computer; run the setup file on that computer instead.

## What happens to older accounts

On the first secure start, EduPy copies each older account into `edupy.db`,
checks that every account arrived, and only then removes readable passwords
from the active JSON save and rolling backup. If any account cannot be copied,
the cleanup is cancelled to prevent lockouts.

The migration can also be checked manually with:

```powershell
.\.venv\Scripts\python.exe migrate_accounts.py
```

Classes and assignments can be checked manually with:

```powershell
.\.venv\Scripts\python.exe migrate_education.py
```

Progress and rewards can be checked manually with:

```powershell
.\.venv\Scripts\python.exe migrate_progress.py
```

After a successful migration, the database becomes the source of truth. The app
temporarily loads those records into memory so the existing screens keep working,
then every class or assignment change is written back in one database transaction.
The nested education and learner-progress records are no longer duplicated in
the active JSON save.

## Creating accounts

- Students can create an account from the sign-in screen.
- Teachers and administrators can create managed accounts in Class Management.
- Managed accounts receive a temporary password and must replace it after their
  first successful sign-in.
- Teachers can reset a temporary password only for students in their own active
  classes. Administrators can reset managed student or teacher accounts.
- New passwords must contain at least eight characters.
- Older profile-only account helpers and full JSON save imports are disabled;
  they cannot be used to bypass the secure account database.

Never share `edupy.db`, old save files, exported rosters containing temporary
passwords, or complete project backups publicly.

## Private local backups

After a successful start, EduPy creates one integrity-checked local backup per
day in the ignored `backups` folder. It keeps the seven newest database/JSON
pairs. These backups contain school and account data, including protected
password hashes, so treat the entire folder as private and never upload it.

## Running the checks

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

These checks cover secure migration, password verification, duplicate and weak
password rejection, disabled accounts, forced password changes, relational
classes and memberships, submissions and marking, permissions, archive safety,
curriculum questions, and scrolling behaviour.

Reward checks also prevent duplicate event rewards, enforce the daily activity
cap, reject negative balances, and ensure a theme can only be purchased once.

## Teacher workspace

Class Management now includes **Overview**, **Students**, **Teachers**,
**Assignments**, **Activity**, and **Settings** tabs. Teachers can manage only
their own classes; administrators can manage every class. A class is archived
rather than physically deleted so its assignments, submissions, marks, and
feedback remain connected for school records.

The wider learning, revision, marking, insight, accessibility, privacy, and
safeguarding workflow is documented in `LEARNING_EXPERIENCE_GUIDE.md`.
