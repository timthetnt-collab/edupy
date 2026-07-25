"""Relational persistence for classes, memberships, assignments and submissions."""

from dataclasses import dataclass
import json

from sqlalchemy import delete
from sqlmodel import Session, SQLModel, select

from models import (
    Account,
    AssignmentExtension,
    AssignmentRecord,
    AssignmentTemplateRecord,
    ClassMembership,
    ClassRecord,
    EducationSetting,
    PrivateTeacherNote,
    SubmissionRecord,
)


SCHEMA_VERSION = "1"


@dataclass
class EducationMigrationResult:
    expected: dict
    actual: dict
    migrated: bool

    @property
    def successful(self):
        return self.expected == self.actual


class EducationStore:
    def __init__(self, engine):
        self.engine = engine

    def create_tables(self):
        SQLModel.metadata.create_all(self.engine)

    def is_initialized(self):
        with Session(self.engine) as session:
            setting = session.get(EducationSetting, "education_schema_version")
            return bool(setting and setting.value == SCHEMA_VERSION)

    @staticmethod
    def counts_for_data(data):
        classes = data.get("classes", {})
        assignments = data.get("assignments", {})
        return {
            "classes": len(classes),
            "memberships": sum(len(item.get("teacher_usernames", [])) + len(item.get("student_usernames", [])) for item in classes.values()),
            "assignments": len(assignments),
            "submissions": sum(len(item.get("submissions", {})) for item in assignments.values()),
            "extensions": sum(len(item.get("extensions", {})) for item in assignments.values()),
            "private_notes": sum(len(item.get("private_comments", {})) for item in assignments.values()),
            "templates": len(data.get("assignment_templates", {})),
        }

    def database_counts(self):
        with Session(self.engine) as session:
            return {
                "classes": len(session.exec(select(ClassRecord.id)).all()),
                "memberships": len(session.exec(select(ClassMembership.id)).all()),
                "assignments": len(session.exec(select(AssignmentRecord.id)).all()),
                "submissions": len(session.exec(select(SubmissionRecord.id)).all()),
                "extensions": len(session.exec(select(AssignmentExtension.id)).all()),
                "private_notes": len(session.exec(select(PrivateTeacherNote.id)).all()),
                "templates": len(session.exec(select(AssignmentTemplateRecord.id)).all()),
            }

    def migrate_or_load(self, data):
        self.create_tables()
        if self.is_initialized():
            snapshot = self.load_snapshot()
            return EducationMigrationResult(self.counts_for_data(snapshot), self.database_counts(), False)

        expected = self.counts_for_data(data)
        self.save_snapshot(data, mark_initialized=True)
        actual = self.database_counts()
        if expected != actual:
            raise RuntimeError(f"Education migration verification failed: expected {expected}, found {actual}")
        return EducationMigrationResult(expected, actual, True)

    def save_snapshot(self, data, mark_initialized=False):
        """Atomically replace education records from the app's in-memory view."""
        classes = data.get("classes", {})
        assignments = data.get("assignments", {})
        templates = data.get("assignment_templates", {})

        with Session(self.engine) as session:
            accounts = session.exec(select(Account)).all()
            account_by_username = {account.username: account for account in accounts}

            def account_id(username, allowed_roles=None):
                account = account_by_username.get(username)
                if not account:
                    raise ValueError(f"No secure account exists for {username!r}.")
                if allowed_roles and account.role not in allowed_roles:
                    raise ValueError(f"{username!r} does not have a permitted role.")
                return account.id

            class_ids = set(classes)
            for class_id, item in classes.items():
                for username in item.get("teacher_usernames", []):
                    account_id(username, {"teacher", "admin"})
                for username in item.get("student_usernames", []):
                    account_id(username, {"student"})
                if not item.get("join_code"):
                    raise ValueError(f"Class {class_id!r} has no join code.")

            for assignment_id, item in assignments.items():
                if item.get("class_id") not in class_ids:
                    raise ValueError(f"Assignment {assignment_id!r} is linked to a missing class.")
                class_item = classes[item["class_id"]]
                students = set(class_item.get("student_usernames", []))
                creator = item.get("created_by")
                if creator:
                    account_id(creator, {"teacher", "admin"})
                for username in set(item.get("submissions", {})) | set(item.get("extensions", {})) | set(item.get("private_comments", {})):
                    if username not in students:
                        raise ValueError(f"{username!r} is not a student in the assignment's class.")
                    account_id(username, {"student"})

            try:
                for model in (SubmissionRecord, AssignmentExtension, PrivateTeacherNote, AssignmentRecord, ClassMembership, ClassRecord, AssignmentTemplateRecord):
                    session.exec(delete(model))

                for class_id, item in classes.items():
                    session.add(ClassRecord(
                        id=class_id,
                        title=item.get("title", class_id),
                        subject=item.get("subject", "General"),
                        year_group=min(11, max(7, int(item.get("year_group", 7)))),
                        join_code=item["join_code"],
                        created_at=item.get("created_at", ""),
                        archived=bool(item.get("archived", False)),
                        metadata_json=json.dumps(item.get("metadata", {})),
                    ))
                session.flush()

                for class_id, item in classes.items():
                    for username in dict.fromkeys(item.get("teacher_usernames", [])):
                        session.add(ClassMembership(class_id=class_id, account_id=account_id(username), membership_role="teacher"))
                    for username in dict.fromkeys(item.get("student_usernames", [])):
                        session.add(ClassMembership(class_id=class_id, account_id=account_id(username), membership_role="student"))
                session.flush()

                for assignment_id, item in assignments.items():
                    creator = item.get("created_by")
                    session.add(AssignmentRecord(
                        id=assignment_id,
                        class_id=item["class_id"],
                        pack_id=item.get("pack_id"),
                        title=item.get("title", "Untitled assignment"),
                        subject=item.get("subject", "General"),
                        instructions=item.get("instructions", ""),
                        created_by_account_id=account_id(creator) if creator else None,
                        created_at=item.get("created_at", ""),
                        due_date=item.get("due_date"),
                        max_marks=int(item.get("max_marks", 100)),
                        reward_tokens=int(item.get("reward_tokens", 5)),
                        status=item.get("status", "published"),
                        publish_at=item.get("publish_at"),
                        allow_late=bool(item.get("allow_late", True)),
                        resubmissions_allowed=bool(item.get("resubmissions_allowed", True)),
                        rubric_json=json.dumps(item.get("rubric", [])),
                        auto_grade_json=json.dumps(item.get("auto_grade", {})),
                    ))
                session.flush()

                for assignment_id, item in assignments.items():
                    for username, submission in item.get("submissions", {}).items():
                        marker = submission.get("marked_by")
                        session.add(SubmissionRecord(
                            assignment_id=assignment_id,
                            student_account_id=account_id(username),
                            submitted_at=submission.get("submitted_at", ""),
                            answer=submission.get("answer", ""),
                            attachment=submission.get("attachment"),
                            grade=submission.get("grade"),
                            feedback=submission.get("feedback"),
                            auto_graded=bool(submission.get("auto_graded", False)),
                            reward_awarded=bool(submission.get("reward_awarded", False)),
                            late=bool(submission.get("late", False)),
                            marked_by_account_id=account_id(marker, {"teacher", "admin"}) if marker else None,
                            marked_at=submission.get("marked_at"),
                        ))
                    for username, due_date in item.get("extensions", {}).items():
                        session.add(AssignmentExtension(assignment_id=assignment_id, student_account_id=account_id(username), due_date=due_date))
                    for username, comment in item.get("private_comments", {}).items():
                        session.add(PrivateTeacherNote(assignment_id=assignment_id, student_account_id=account_id(username), comment=comment))
                session.flush()

                for template_id, item in templates.items():
                    owner = item.get("owner", "")
                    session.add(AssignmentTemplateRecord(
                        id=template_id,
                        name=item.get("name", "Reusable assignment"),
                        owner_account_id=None if owner == "shared" or not owner else account_id(owner, {"teacher", "admin"}),
                        shared=owner == "shared",
                        created_at=item.get("created_at", ""),
                        fields_json=json.dumps(item.get("fields", {})),
                    ))

                if mark_initialized:
                    setting = session.get(EducationSetting, "education_schema_version")
                    if setting:
                        setting.value = SCHEMA_VERSION
                        session.add(setting)
                    else:
                        session.add(EducationSetting(key="education_schema_version", value=SCHEMA_VERSION))
                session.commit()
            except Exception:
                session.rollback()
                raise

    def load_snapshot(self):
        with Session(self.engine) as session:
            accounts = session.exec(select(Account)).all()
            username_by_id = {account.id: account.username for account in accounts}
            class_rows = session.exec(select(ClassRecord)).all()
            memberships = session.exec(select(ClassMembership)).all()
            assignment_rows = session.exec(select(AssignmentRecord)).all()
            submissions = session.exec(select(SubmissionRecord)).all()
            extensions = session.exec(select(AssignmentExtension)).all()
            notes = session.exec(select(PrivateTeacherNote)).all()
            templates = session.exec(select(AssignmentTemplateRecord)).all()

            classes = {}
            for row in class_rows:
                classes[row.id] = {
                    "id": row.id,
                    "title": row.title,
                    "subject": row.subject,
                    "year_group": row.year_group,
                    "teacher_usernames": [],
                    "student_usernames": [],
                    "join_code": row.join_code,
                    "created_at": row.created_at,
                    "archived": row.archived,
                    "metadata": json.loads(row.metadata_json or "{}"),
                }
            for membership in memberships:
                username = username_by_id.get(membership.account_id)
                target = classes.get(membership.class_id)
                if username and target:
                    target[f"{membership.membership_role}_usernames"].append(username)

            assignments = {}
            for row in assignment_rows:
                assignments[row.id] = {
                    "id": row.id,
                    "title": row.title,
                    "class_id": row.class_id,
                    "pack_id": row.pack_id,
                    "subject": row.subject,
                    "instructions": row.instructions,
                    "created_by": username_by_id.get(row.created_by_account_id, ""),
                    "created_at": row.created_at,
                    "due_date": row.due_date,
                    "max_marks": row.max_marks,
                    "reward_tokens": row.reward_tokens,
                    "status": row.status,
                    "publish_at": row.publish_at,
                    "allow_late": row.allow_late,
                    "resubmissions_allowed": row.resubmissions_allowed,
                    "rubric": json.loads(row.rubric_json or "[]"),
                    "auto_grade": json.loads(row.auto_grade_json or "{}"),
                    "submissions": {},
                    "extensions": {},
                    "private_comments": {},
                }
            for row in submissions:
                username = username_by_id.get(row.student_account_id)
                if username and row.assignment_id in assignments:
                    submission = {
                        "submitted_at": row.submitted_at,
                        "answer": row.answer,
                        "attachment": row.attachment,
                        "grade": row.grade,
                        "feedback": row.feedback,
                        "auto_graded": row.auto_graded,
                        "reward_awarded": row.reward_awarded,
                        "late": row.late,
                    }
                    marker = username_by_id.get(row.marked_by_account_id)
                    if marker:
                        submission["marked_by"] = marker
                    if row.marked_at:
                        submission["marked_at"] = row.marked_at
                    assignments[row.assignment_id]["submissions"][username] = submission
            for row in extensions:
                username = username_by_id.get(row.student_account_id)
                if username and row.assignment_id in assignments:
                    assignments[row.assignment_id]["extensions"][username] = row.due_date
            for row in notes:
                username = username_by_id.get(row.student_account_id)
                if username and row.assignment_id in assignments:
                    assignments[row.assignment_id]["private_comments"][username] = row.comment

            template_data = {}
            for row in templates:
                template_data[row.id] = {
                    "id": row.id,
                    "name": row.name,
                    "owner": "shared" if row.shared else username_by_id.get(row.owner_account_id, ""),
                    "created_at": row.created_at,
                    "fields": json.loads(row.fields_json or "{}"),
                }
            return {"classes": classes, "assignments": assignments, "assignment_templates": template_data}
