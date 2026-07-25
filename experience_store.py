"""Direct database operations for diagnostics, revision, preferences and safety."""

import datetime
import json
import math
import uuid

from sqlalchemy import delete
from sqlmodel import Session, SQLModel, select

from models import (
    AccessibilityProfileRecord,
    AdaptiveStateRecord,
    Account,
    AssignmentRecord,
    AssessmentPaperRecord,
    CertificateRecord,
    ClassMembership,
    ClassroomActivityRecord,
    ClassroomResponseRecord,
    ContentReportRecord,
    CurriculumBookmarkRecord,
    CustomQuestionRecord,
    DiagnosticResultRecord,
    LessonProgressRecord,
    LearningGoalRecord,
    LinkedAccountRecord,
    MistakeRecord,
    MockExamAttemptRecord,
    NotificationRecord,
    PortfolioItemRecord,
    PrivacyRequestRecord,
    RevisionPlanRecord,
    RevisionTaskRecord,
    SafetyReportRecord,
    SafeguardingActionRecord,
    PathwayEnrollmentRecord,
    TopicAssessmentRecord,
    TeacherResourceRecord,
    UserPreferenceRecord,
    WellbeingCheckInRecord,
)


def _now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def _safe_int(value):
    """Return an integer for service inputs, or None instead of leaking a UI error."""
    try:
        return int(value)
    except (TypeError, ValueError, OverflowError):
        return None


class ExperienceStore:
    def __init__(self, engine):
        self.engine = engine
        SQLModel.metadata.create_all(engine)

    def _account(self, session, username):
        return session.exec(select(Account).where(Account.username == username)).first()

    def preferences(self, username):
        with Session(self.engine) as session:
            account = self._account(session, username)
            row = session.get(UserPreferenceRecord, account.id) if account else None
            profile = session.get(AccessibilityProfileRecord, account.id) if account else None
            return {
                "reduced_motion": bool(row and row.reduced_motion),
                "high_contrast": bool(row and row.high_contrast),
                "focus_mode": bool(row and row.focus_mode),
                "font_scale": row.font_scale if row else 100,
                "extra_time_percent": row.extra_time_percent if row else 0,
                "dyslexia_friendly": bool(profile and profile.dyslexia_friendly),
                "reading_ruler": bool(profile and profile.reading_ruler),
                "generous_spacing": bool(profile and profile.generous_spacing),
                "calm_palette": bool(profile and profile.calm_palette),
            }

    def update_preferences(self, username, **changes):
        with Session(self.engine) as session:
            account = self._account(session, username)
            if not account:
                return False
            row = session.get(UserPreferenceRecord, account.id) or UserPreferenceRecord(account_id=account.id)
            for field in ("reduced_motion", "high_contrast", "focus_mode"):
                if field in changes:
                    setattr(row, field, bool(changes[field]))
            if "font_scale" in changes:
                row.font_scale = min(140, max(90, int(changes["font_scale"])))
            if "extra_time_percent" in changes:
                row.extra_time_percent = min(100, max(0, int(changes["extra_time_percent"])))
            session.add(row); session.commit(); return True

    def record_diagnostic(self, username, year_group, results):
        batch_id = str(uuid.uuid4())
        completed_at = _now()
        with Session(self.engine) as session:
            account = self._account(session, username)
            if not account:
                return None
            for result in results:
                session.add(DiagnosticResultRecord(
                    account_id=account.id, batch_id=batch_id, year_group=year_group,
                    subject=result["subject"], topic_id=result["topic"],
                    earned=float(result["earned"]), possible=max(1.0, float(result["possible"])),
                    completed_at=completed_at,
                ))
            session.commit()
        return batch_id

    def latest_diagnostic(self, username):
        with Session(self.engine) as session:
            account = self._account(session, username)
            if not account:
                return []
            latest = session.exec(
                select(DiagnosticResultRecord).where(DiagnosticResultRecord.account_id == account.id)
                .order_by(DiagnosticResultRecord.completed_at.desc())
            ).first()
            if not latest:
                return []
            rows = session.exec(select(DiagnosticResultRecord).where(DiagnosticResultRecord.batch_id == latest.batch_id)).all()
            return [{"subject": row.subject, "topic": row.topic_id, "earned": row.earned, "possible": row.possible, "completed_at": row.completed_at} for row in rows]

    def record_lesson_view(self, username, subject, topic_id, completed=False):
        with Session(self.engine) as session:
            account = self._account(session, username)
            if not account:
                return False
            row = session.exec(select(LessonProgressRecord).where(
                LessonProgressRecord.account_id == account.id,
                LessonProgressRecord.subject == subject,
                LessonProgressRecord.topic_id == topic_id,
            )).first()
            if not row:
                row = LessonProgressRecord(account_id=account.id, subject=subject, topic_id=topic_id, last_viewed_at=_now())
            row.views += 1; row.completed = row.completed or bool(completed); row.last_viewed_at = _now()
            session.add(row); session.commit(); return True

    def recent_lessons(self, username, limit=5):
        """Return the learner's most recently opened lessons."""
        with Session(self.engine) as session:
            account = self._account(session, username)
            if not account:
                return []
            rows = session.exec(
                select(LessonProgressRecord)
                .where(LessonProgressRecord.account_id == account.id)
                .order_by(LessonProgressRecord.last_viewed_at.desc())
                .limit(max(1, min(20, int(limit))))
            ).all()
            return [{
                "subject": row.subject,
                "topic": row.topic_id,
                "completed": row.completed,
                "views": row.views,
                "last_viewed_at": row.last_viewed_at,
            } for row in rows]

    def create_revision_plan(self, username, title, exam_date, tasks):
        with Session(self.engine) as session:
            account = self._account(session, username)
            if not account:
                return False
            old = session.exec(select(RevisionPlanRecord).where(RevisionPlanRecord.account_id == account.id)).first()
            if old:
                session.exec(delete(RevisionTaskRecord).where(RevisionTaskRecord.plan_id == old.id))
                session.delete(old); session.flush()
            plan = RevisionPlanRecord(account_id=account.id, title=title.strip() or "Revision plan", exam_date=exam_date, created_at=_now())
            session.add(plan); session.flush()
            for task in tasks:
                session.add(RevisionTaskRecord(plan_id=plan.id, subject=task["subject"], topic_id=task["topic"], due_date=task["due_date"]))
            session.commit(); return True

    def revision_plan(self, username):
        with Session(self.engine) as session:
            account = self._account(session, username)
            plan = session.exec(select(RevisionPlanRecord).where(RevisionPlanRecord.account_id == account.id)).first() if account else None
            if not plan:
                return None
            tasks = session.exec(select(RevisionTaskRecord).where(RevisionTaskRecord.plan_id == plan.id).order_by(RevisionTaskRecord.due_date)).all()
            return {"id": plan.id, "title": plan.title, "exam_date": plan.exam_date, "tasks": [{"id": task.id, "subject": task.subject, "topic": task.topic_id, "due_date": task.due_date, "completed": task.completed} for task in tasks]}

    def delete_revision_plan(self, username):
        with Session(self.engine) as session:
            account = self._account(session, username)
            plan = session.exec(select(RevisionPlanRecord).where(RevisionPlanRecord.account_id == account.id)).first() if account else None
            if not plan:
                return False
            session.exec(delete(RevisionTaskRecord).where(RevisionTaskRecord.plan_id == plan.id))
            session.delete(plan); session.commit(); return True

    def set_revision_task(self, username, task_id, completed=True):
        with Session(self.engine) as session:
            account = self._account(session, username)
            task = session.get(RevisionTaskRecord, int(task_id)) if account else None
            plan = session.get(RevisionPlanRecord, task.plan_id) if task else None
            if not task or not plan or plan.account_id != account.id:
                return False
            task.completed = bool(completed); session.add(task); session.commit(); return True

    def submit_safety_report(self, username, category, description):
        description = description.strip()
        if len(description) < 10:
            return False
        with Session(self.engine) as session:
            account = self._account(session, username)
            if not account:
                return False
            session.add(SafetyReportRecord(reporter_account_id=account.id, category=category, description=description, created_at=_now()))
            session.commit(); return True

    def my_safety_reports(self, username, limit=10):
        with Session(self.engine) as session:
            account = self._account(session, username)
            if not account:
                return []
            rows = session.exec(
                select(SafetyReportRecord)
                .where(SafetyReportRecord.reporter_account_id == account.id)
                .order_by(SafetyReportRecord.created_at.desc())
                .limit(max(1, min(50, int(limit))))
            ).all()
            return [{"id": row.id, "category": row.category, "description": row.description, "status": row.status, "created_at": row.created_at} for row in rows]

    def safety_reports(self, actor_username, status="open"):
        with Session(self.engine) as session:
            actor = self._account(session, actor_username)
            if not actor or actor.role != "admin":
                return []
            accounts = {account.id: account.username for account in session.exec(select(Account)).all()}
            statement = select(SafetyReportRecord).order_by(SafetyReportRecord.created_at.desc())
            if status == "active":
                statement = statement.where(SafetyReportRecord.status.in_(["open", "in_progress"]))
            elif status:
                statement = statement.where(SafetyReportRecord.status == status)
            rows = session.exec(statement).all()
            return [{"id": row.id, "reporter": accounts.get(row.reporter_account_id, "Unknown"), "category": row.category, "description": row.description, "status": row.status, "created_at": row.created_at} for row in rows]

    def resolve_safety_report(self, actor_username, report_id):
        with Session(self.engine) as session:
            actor = self._account(session, actor_username)
            if not actor or actor.role != "admin":
                return False
            row = session.get(SafetyReportRecord, int(report_id))
            if not row:
                return False
            row.status = "resolved"; row.resolved_at = _now(); session.add(row); session.commit(); return True

    def create_privacy_request(self, username, request_type):
        if request_type not in ("export", "correction", "deletion"):
            return False
        with Session(self.engine) as session:
            account = self._account(session, username)
            if not account:
                return False
            existing = session.exec(select(PrivacyRequestRecord).where(
                PrivacyRequestRecord.account_id == account.id,
                PrivacyRequestRecord.request_type == request_type,
                PrivacyRequestRecord.status == "open",
            )).first()
            if existing:
                return False
            session.add(PrivacyRequestRecord(account_id=account.id, request_type=request_type, created_at=_now()))
            session.commit(); return True

    def my_privacy_requests(self, username, limit=10):
        with Session(self.engine) as session:
            account = self._account(session, username)
            if not account:
                return []
            rows = session.exec(
                select(PrivacyRequestRecord)
                .where(PrivacyRequestRecord.account_id == account.id)
                .order_by(PrivacyRequestRecord.created_at.desc())
                .limit(max(1, min(50, int(limit))))
            ).all()
            return [{"id": row.id, "request_type": row.request_type, "status": row.status, "created_at": row.created_at} for row in rows]

    def privacy_requests(self, actor_username, status="open"):
        with Session(self.engine) as session:
            actor = self._account(session, actor_username)
            if not actor or actor.role != "admin":
                return []
            accounts = {account.id: account.username for account in session.exec(select(Account)).all()}
            statement = select(PrivacyRequestRecord).order_by(PrivacyRequestRecord.created_at.desc())
            if status:
                statement = statement.where(PrivacyRequestRecord.status == status)
            rows = session.exec(statement).all()
            return [{"id": row.id, "username": accounts.get(row.account_id, "Unknown"), "request_type": row.request_type, "status": row.status, "created_at": row.created_at} for row in rows]

    def resolve_privacy_request(self, actor_username, request_id):
        with Session(self.engine) as session:
            actor = self._account(session, actor_username)
            if not actor or actor.role != "admin":
                return False
            row = session.get(PrivacyRequestRecord, int(request_id))
            if not row:
                return False
            row.status = "resolved"; row.resolved_at = _now(); session.add(row); session.commit(); return True

    def bookmarks(self, username):
        with Session(self.engine) as session:
            account = self._account(session, username)
            if not account:
                return []
            rows = session.exec(select(CurriculumBookmarkRecord).where(
                CurriculumBookmarkRecord.account_id == account.id
            ).order_by(CurriculumBookmarkRecord.created_at.desc())).all()
            return [{"year": row.year_group, "subject": row.subject, "topic": row.topic_id} for row in rows]

    def toggle_bookmark(self, username, year_group, subject, topic_id):
        with Session(self.engine) as session:
            account = self._account(session, username)
            if not account:
                return False
            row = session.exec(select(CurriculumBookmarkRecord).where(
                CurriculumBookmarkRecord.account_id == account.id,
                CurriculumBookmarkRecord.subject == subject,
                CurriculumBookmarkRecord.topic_id == topic_id,
            )).first()
            if row:
                session.delete(row); session.commit(); return False
            session.add(CurriculumBookmarkRecord(
                account_id=account.id, year_group=int(year_group), subject=subject,
                topic_id=topic_id, created_at=_now(),
            ))
            session.commit(); return True

    def enroll_pathway(self, username, pathway_id, active=True):
        with Session(self.engine) as session:
            account = self._account(session, username)
            if not account:
                return False
            row = session.exec(select(PathwayEnrollmentRecord).where(
                PathwayEnrollmentRecord.account_id == account.id,
                PathwayEnrollmentRecord.pathway_id == pathway_id,
            )).first()
            if not row:
                row = PathwayEnrollmentRecord(account_id=account.id, pathway_id=pathway_id, enrolled_at=_now())
            row.active = bool(active); session.add(row); session.commit(); return True

    def active_pathways(self, username):
        with Session(self.engine) as session:
            account = self._account(session, username)
            if not account:
                return []
            rows = session.exec(select(PathwayEnrollmentRecord).where(
                PathwayEnrollmentRecord.account_id == account.id,
                PathwayEnrollmentRecord.active == True,
            )).all()
            return [row.pathway_id for row in rows]

    def adaptive_state(self, username, subject, topic_id, starting_difficulty=1):
        with Session(self.engine) as session:
            account = self._account(session, username)
            row = session.exec(select(AdaptiveStateRecord).where(
                AdaptiveStateRecord.account_id == account.id,
                AdaptiveStateRecord.subject == subject,
                AdaptiveStateRecord.topic_id == topic_id,
            )).first() if account else None
            return {"difficulty": row.difficulty, "correct_streak": row.correct_streak} if row else {"difficulty": min(4,max(1,int(starting_difficulty))), "correct_streak": 0}

    def record_adaptive_result(self, username, subject, topic_id, correct, starting_difficulty=1):
        with Session(self.engine) as session:
            account = self._account(session, username)
            if not account:
                return {"difficulty": 1, "correct_streak": 0}
            row = session.exec(select(AdaptiveStateRecord).where(
                AdaptiveStateRecord.account_id == account.id,
                AdaptiveStateRecord.subject == subject,
                AdaptiveStateRecord.topic_id == topic_id,
            )).first()
            if not row:
                row = AdaptiveStateRecord(account_id=account.id, subject=subject, topic_id=topic_id,
                    difficulty=min(4,max(1,int(starting_difficulty))), correct_streak=0, updated_at=_now())
            if correct:
                row.correct_streak += 1
                if row.correct_streak >= 2:
                    row.difficulty = min(4, row.difficulty + 1); row.correct_streak = 0
            else:
                row.correct_streak = 0; row.difficulty = max(1, row.difficulty - 1)
            row.updated_at = _now(); session.add(row); session.commit()
            return {"difficulty": row.difficulty, "correct_streak": row.correct_streak}

    def record_topic_assessment(self, username, year_group, subject, topic_id, assessment_type, earned, possible):
        if assessment_type not in ("starting", "end", "retention") or float(possible) <= 0:
            return False
        completed = datetime.date.today()
        due = (completed + datetime.timedelta(days=14)).isoformat() if assessment_type == "end" else None
        with Session(self.engine) as session:
            account = self._account(session, username)
            if not account:
                return False
            session.add(TopicAssessmentRecord(
                account_id=account.id, year_group=int(year_group), subject=subject, topic_id=topic_id,
                assessment_type=assessment_type, earned=float(earned), possible=float(possible),
                completed_at=_now(), retention_due=due,
            ))
            session.commit(); return True

    def topic_assessments(self, username, topic_id=None):
        with Session(self.engine) as session:
            account = self._account(session, username)
            if not account:
                return []
            statement = select(TopicAssessmentRecord).where(TopicAssessmentRecord.account_id == account.id)
            if topic_id:
                statement = statement.where(TopicAssessmentRecord.topic_id == topic_id)
            rows = session.exec(statement.order_by(TopicAssessmentRecord.completed_at.desc())).all()
            return [{"id":row.id,"year":row.year_group,"subject":row.subject,"topic":row.topic_id,
                "type":row.assessment_type,"earned":row.earned,"possible":row.possible,
                "completed_at":row.completed_at,"retention_due":row.retention_due} for row in rows]

    def retention_due(self, username):
        today = datetime.date.today().isoformat()
        completed = {(row["subject"],row["topic"]) for row in self.topic_assessments(username) if row["type"] == "retention"}
        return [row for row in self.topic_assessments(username) if row["type"] == "end" and row.get("retention_due") and row["retention_due"] <= today and (row["subject"],row["topic"]) not in completed]

    # EduPy 2: authored content, exams and learner-owned evidence.
    def create_custom_question(self, username, year_group, subject, topic_id, question_type,
                               prompt, answer="", choices=None, marks=1, submit=False):
        prompt, answer = str(prompt).strip(), str(answer).strip()
        choices = [str(item).strip() for item in (choices or []) if str(item).strip()]
        try:
            year_group = min(11, max(7, int(year_group)))
            marks = min(20, max(1, int(marks)))
        except (TypeError, ValueError):
            return None
        if (len(prompt) < 10 or not answer or subject not in ("Maths", "English")
                or question_type not in ("multiple_choice", "short", "extended")):
            return None
        if question_type == "multiple_choice" and (len(set(choices)) < 2 or answer not in choices):
            return None
        with Session(self.engine) as session:
            account = self._account(session, username)
            if not account or account.role not in ("teacher", "admin"):
                return None
            row = CustomQuestionRecord(
                owner_account_id=account.id, year_group=year_group,
                subject=subject, topic_id=str(topic_id), question_type=question_type,
                prompt=prompt, answer=answer, choices_json=json.dumps(choices),
                marks=marks, status="pending" if submit else "draft",
                created_at=_now(),
            )
            session.add(row); session.commit(); session.refresh(row); return row.id

    def custom_questions(self, username, status=None, year_group=None, subject=None):
        with Session(self.engine) as session:
            actor = self._account(session, username)
            if not actor:
                return []
            statement = select(CustomQuestionRecord).order_by(CustomQuestionRecord.created_at.desc())
            if actor.role == "teacher":
                statement = statement.where(CustomQuestionRecord.owner_account_id == actor.id)
            elif actor.role == "student":
                statement = statement.where(CustomQuestionRecord.status == "approved")
            if status:
                statement = statement.where(CustomQuestionRecord.status == status)
            if year_group:
                parsed_year = _safe_int(year_group)
                if parsed_year is None:
                    return []
                statement = statement.where(CustomQuestionRecord.year_group == parsed_year)
            if subject:
                statement = statement.where(CustomQuestionRecord.subject == subject)
            accounts = {row.id: row.username for row in session.exec(select(Account)).all()}
            return [{"id":row.id,"owner":accounts.get(row.owner_account_id,"Unknown"),"year":row.year_group,
                "subject":row.subject,"topic":row.topic_id,"type":row.question_type,"prompt":row.prompt,
                "answer":row.answer,"choices":json.loads(row.choices_json or "[]"),"marks":row.marks,
                "status":row.status,"note":row.moderation_note,"created_at":row.created_at} for row in session.exec(statement).all()]

    def moderate_question(self, username, question_id, decision, note=""):
        if decision not in ("approved", "rejected"):
            return False
        question_id = _safe_int(question_id)
        if question_id is None:
            return False
        with Session(self.engine) as session:
            actor = self._account(session, username); row = session.get(CustomQuestionRecord, question_id)
            if not actor or actor.role != "admin" or not row or row.status != "pending":
                return False
            row.status=decision; row.moderation_note=str(note).strip(); row.reviewed_at=_now(); session.add(row)
            owner=session.get(Account,row.owner_account_id)
            if owner:
                session.add(NotificationRecord(account_id=owner.id,title=f"Question {decision}",message=row.prompt[:120],category="Content",created_at=_now()))
            session.commit(); return True

    def report_content(self, username, reason, question_id=None):
        reason = str(reason).strip()
        with Session(self.engine) as session:
            account = self._account(session, username)
            if not account or len(reason) < 5:
                return False
            if question_id is not None:
                question_id = _safe_int(question_id)
                if question_id is None: return False
                if not session.get(CustomQuestionRecord, question_id): return False
            session.add(ContentReportRecord(reporter_account_id=account.id, question_id=question_id,
                reason=reason, created_at=_now())); session.commit(); return True

    def content_reports(self, username, resolve_id=None):
        with Session(self.engine) as session:
            actor=self._account(session,username)
            if not actor or actor.role != "admin": return []
            if resolve_id:
                resolve_id = _safe_int(resolve_id)
                row=session.get(ContentReportRecord,resolve_id) if resolve_id is not None else None
                if row: row.status="resolved";session.add(row);session.commit()
            accounts={row.id:row.username for row in session.exec(select(Account)).all()}
            rows=session.exec(select(ContentReportRecord).where(ContentReportRecord.status=="open").order_by(ContentReportRecord.created_at.desc())).all()
            return [{"id":row.id,"reporter":accounts.get(row.reporter_account_id,"Unknown"),"question_id":row.question_id,"reason":row.reason,"created_at":row.created_at} for row in rows]

    def record_mock_exam(self, username, year_group, subject, earned, possible, duration_seconds, flagged_count=0):
        if subject not in ("Maths", "English"):
            return False
        year_group = _safe_int(year_group)
        duration_seconds = _safe_int(duration_seconds)
        flagged_count = _safe_int(flagged_count)
        try:
            earned, possible = float(earned), float(possible)
        except (TypeError, ValueError, OverflowError):
            return False
        if (year_group is None or not 7 <= year_group <= 11 or duration_seconds is None
                or flagged_count is None or not math.isfinite(earned) or not math.isfinite(possible)
                or possible <= 0 or earned < 0 or earned > possible):
            return False
        with Session(self.engine) as session:
            account=self._account(session,username)
            if not account:return False
            session.add(MockExamAttemptRecord(account_id=account.id,year_group=year_group,subject=subject,
                earned=earned,possible=possible,duration_seconds=max(0,duration_seconds),
                flagged_count=max(0,flagged_count),completed_at=_now()));session.commit();return True

    def mock_exams(self, username, limit=20):
        with Session(self.engine) as session:
            account=self._account(session,username)
            if not account:return []
            rows=session.exec(select(MockExamAttemptRecord).where(MockExamAttemptRecord.account_id==account.id).order_by(MockExamAttemptRecord.completed_at.desc()).limit(limit)).all()
            return [{"id":r.id,"year":r.year_group,"subject":r.subject,"earned":r.earned,"possible":r.possible,"duration":r.duration_seconds,"flagged":r.flagged_count,"completed_at":r.completed_at} for r in rows]

    def add_portfolio_item(self, username, title, subject, description="", evidence=""):
        if len(str(title).strip()) < 3:return None
        with Session(self.engine) as session:
            account=self._account(session,username)
            if not account or account.role != "student":return None
            row=PortfolioItemRecord(account_id=account.id,title=str(title).strip(),subject=subject,
                description=str(description).strip(),evidence=str(evidence).strip(),created_at=_now())
            session.add(row);session.commit();session.refresh(row);return row.id

    def portfolio(self, username, delete_id=None):
        with Session(self.engine) as session:
            account=self._account(session,username)
            if not account:return []
            if delete_id:
                delete_id = _safe_int(delete_id)
                row=session.get(PortfolioItemRecord,delete_id) if delete_id is not None else None
                if row and row.account_id==account.id:session.delete(row);session.commit()
            rows=session.exec(select(PortfolioItemRecord).where(PortfolioItemRecord.account_id==account.id).order_by(PortfolioItemRecord.created_at.desc())).all()
            return [{"id":r.id,"title":r.title,"subject":r.subject,"description":r.description,"evidence":r.evidence,"created_at":r.created_at} for r in rows]

    def notify(self, username, title, message, category="Learning"):
        with Session(self.engine) as session:
            account=self._account(session,username)
            if not account or not str(title).strip():return False
            session.add(NotificationRecord(account_id=account.id,title=str(title).strip(),message=str(message).strip(),category=category,created_at=_now()));session.commit();return True

    def notifications(self, username, mark_read_id=None, limit=50):
        with Session(self.engine) as session:
            account=self._account(session,username)
            if not account:return []
            if mark_read_id:
                mark_read_id = _safe_int(mark_read_id)
                row=session.get(NotificationRecord,mark_read_id) if mark_read_id is not None else None
                if row and row.account_id==account.id:row.read=True;session.add(row);session.commit()
            rows=session.exec(select(NotificationRecord).where(NotificationRecord.account_id==account.id).order_by(NotificationRecord.created_at.desc()).limit(limit)).all()
            return [{"id":r.id,"title":r.title,"message":r.message,"category":r.category,"read":r.read,"created_at":r.created_at} for r in rows]

    def wellbeing_checkin(self, username, mood, note=""):
        mood = _safe_int(mood)
        if mood is None:
            return False
        with Session(self.engine) as session:
            account=self._account(session,username)
            if not account:return False
            session.add(WellbeingCheckInRecord(account_id=account.id,mood=min(5,max(1,mood)),note=str(note).strip()[:500],created_at=_now()));session.commit();return True

    def my_wellbeing(self, username, limit=14):
        with Session(self.engine) as session:
            account=self._account(session,username)
            if not account:return []
            rows=session.exec(select(WellbeingCheckInRecord).where(WellbeingCheckInRecord.account_id==account.id).order_by(WellbeingCheckInRecord.created_at.desc()).limit(limit)).all()
            return [{"mood":r.mood,"note":r.note,"created_at":r.created_at} for r in rows]

    def accessibility_profile(self, username):
        with Session(self.engine) as session:
            account=self._account(session,username);row=session.get(AccessibilityProfileRecord,account.id) if account else None
            return {"dyslexia_friendly":bool(row and row.dyslexia_friendly),"reading_ruler":bool(row and row.reading_ruler),
                "generous_spacing":bool(row and row.generous_spacing),"calm_palette":bool(row and row.calm_palette)}

    def update_accessibility_profile(self, username, **changes):
        with Session(self.engine) as session:
            account=self._account(session,username)
            if not account:return False
            row=session.get(AccessibilityProfileRecord,account.id) or AccessibilityProfileRecord(account_id=account.id)
            for field in ("dyslexia_friendly","reading_ruler","generous_spacing","calm_palette"):
                if field in changes:setattr(row,field,bool(changes[field]))
            session.add(row);session.commit();return True

    def add_mistake(self, username, year_group, subject, topic_id, prompt, response, expected):
        year_group = _safe_int(year_group)
        if year_group is None or not 7 <= year_group <= 11:
            return None
        with Session(self.engine) as session:
            account=self._account(session,username)
            if not account:return None
            existing=session.exec(select(MistakeRecord).where(
                MistakeRecord.account_id==account.id,MistakeRecord.subject==subject,
                MistakeRecord.topic_id==topic_id,MistakeRecord.prompt==str(prompt)[:1000],
                MistakeRecord.mastered==False,
            )).first()
            if existing:
                existing.response=str(response)[:1000];existing.expected=str(expected)[:1000];existing.created_at=_now()
                session.add(existing);session.commit();return existing.id
            row=MistakeRecord(account_id=account.id,year_group=year_group,subject=subject,topic_id=topic_id,
                prompt=str(prompt)[:1000],response=str(response)[:1000],expected=str(expected)[:1000],created_at=_now())
            session.add(row);session.commit();session.refresh(row);return row.id

    def mistakes(self, username, include_mastered=False, master_id=None):
        with Session(self.engine) as session:
            account=self._account(session,username)
            if not account:return []
            if master_id:
                master_id = _safe_int(master_id)
                row=session.get(MistakeRecord,master_id) if master_id is not None else None
                if row and row.account_id==account.id:row.mastered=True;session.add(row);session.commit()
            statement=select(MistakeRecord).where(MistakeRecord.account_id==account.id)
            if not include_mastered:statement=statement.where(MistakeRecord.mastered==False)
            rows=session.exec(statement.order_by(MistakeRecord.created_at.desc())).all()
            return [{"id":r.id,"year":r.year_group,"subject":r.subject,"topic":r.topic_id,"prompt":r.prompt,"response":r.response,"expected":r.expected,"mastered":r.mastered,"created_at":r.created_at} for r in rows]

    def award_certificate(self, username, key, title, detail=""):
        with Session(self.engine) as session:
            account=self._account(session,username)
            if not account:return False
            existing=session.exec(select(CertificateRecord).where(CertificateRecord.account_id==account.id,CertificateRecord.certificate_key==key)).first()
            if existing:return False
            session.add(CertificateRecord(account_id=account.id,certificate_key=key,title=title,detail=detail,issued_at=_now()))
            session.add(NotificationRecord(account_id=account.id,title="New certificate earned",message=title,category="Achievement",created_at=_now()))
            session.commit();return True

    def certificates(self, username):
        with Session(self.engine) as session:
            account=self._account(session,username)
            if not account:return []
            rows=session.exec(select(CertificateRecord).where(CertificateRecord.account_id==account.id).order_by(CertificateRecord.issued_at.desc())).all()
            return [{"id":r.id,"key":r.certificate_key,"title":r.title,"detail":r.detail,"issued_at":r.issued_at} for r in rows]

    def create_activity(self, username, class_id, title, activity_type, prompt, options=None):
        clean_options=list(dict.fromkeys(str(x).strip() for x in (options or []) if str(x).strip()))
        if (activity_type not in ("poll","quiz","discussion") or len(str(prompt).strip())<3
                or (activity_type in ("poll","quiz") and len(clean_options)<2)):return None
        with Session(self.engine) as session:
            actor=self._account(session,username)
            member=session.exec(select(ClassMembership).where(ClassMembership.class_id==class_id,ClassMembership.account_id==actor.id,ClassMembership.membership_role=="teacher")).first() if actor else None
            if not actor or (actor.role!="admin" and not member):return None
            row=ClassroomActivityRecord(class_id=class_id,creator_account_id=actor.id,title=str(title).strip() or "Class activity",
                activity_type=activity_type,prompt=str(prompt).strip(),options_json=json.dumps(clean_options),created_at=_now())
            session.add(row);session.commit();session.refresh(row);return row.id

    def activities(self, username, include_closed=False):
        with Session(self.engine) as session:
            account=self._account(session,username)
            if not account:return []
            memberships=session.exec(select(ClassMembership).where(ClassMembership.account_id==account.id)).all();class_ids=[r.class_id for r in memberships]
            if account.role=="admin":statement=select(ClassroomActivityRecord)
            elif not class_ids:return []
            else:statement=select(ClassroomActivityRecord).where(ClassroomActivityRecord.class_id.in_(class_ids))
            if not include_closed:statement=statement.where(ClassroomActivityRecord.status=="live")
            rows=session.exec(statement.order_by(ClassroomActivityRecord.created_at.desc())).all()
            responses=session.exec(select(ClassroomResponseRecord)).all();by_activity={}
            for response in responses:by_activity.setdefault(response.activity_id,[]).append(response.response)
            return [{"id":r.id,"class_id":r.class_id,"title":r.title,"type":r.activity_type,"prompt":r.prompt,
                "options":json.loads(r.options_json or "[]"),"status":r.status,"responses":by_activity.get(r.id,[]),"created_at":r.created_at} for r in rows]

    def respond_activity(self, username, activity_id, response):
        activity_id = _safe_int(activity_id)
        if activity_id is None:
            return False
        with Session(self.engine) as session:
            account=self._account(session,username);activity=session.get(ClassroomActivityRecord,activity_id)
            member=session.exec(select(ClassMembership).where(ClassMembership.class_id==activity.class_id,ClassMembership.account_id==account.id,ClassMembership.membership_role=="student")).first() if account and activity else None
            if not member or activity.status!="live" or not str(response).strip():return False
            allowed=json.loads(activity.options_json or "[]")
            if allowed and str(response).strip() not in allowed:return False
            row=session.exec(select(ClassroomResponseRecord).where(ClassroomResponseRecord.activity_id==activity.id,ClassroomResponseRecord.account_id==account.id)).first()
            if row:row.response=str(response).strip();row.created_at=_now()
            else:row=ClassroomResponseRecord(activity_id=activity.id,account_id=account.id,response=str(response).strip(),created_at=_now())
            session.add(row);session.commit();return True

    def close_activity(self, username, activity_id):
        activity_id = _safe_int(activity_id)
        if activity_id is None:
            return False
        with Session(self.engine) as session:
            actor=self._account(session,username);row=session.get(ClassroomActivityRecord,activity_id)
            if not actor or not row or (actor.role!="admin" and row.creator_account_id!=actor.id):return False
            row.status="closed";session.add(row);session.commit();return True

    # EduPy 3: assessment papers, family access, goals and school workflows.
    def create_assessment_paper(self, username, title, year_group, subject, duration_minutes, topics, questions):
        year_group, duration_minutes = _safe_int(year_group), _safe_int(duration_minutes)
        clean_title = str(title).strip()
        clean_topics = list(dict.fromkeys(str(item).strip() for item in (topics or []) if str(item).strip()))
        clean_questions = []
        for item in questions or []:
            if not isinstance(item, dict) or not str(item.get("prompt", "")).strip() or not str(item.get("answer", "")).strip():
                continue
            clean_questions.append({
                "prompt": str(item["prompt"]).strip()[:2000],
                "answer": str(item["answer"]).strip()[:1000],
                "marks": max(1, min(20, _safe_int(item.get("marks", 1)) or 1)),
                "topic": str(item.get("topic", "")).strip()[:96],
                "choices": [str(choice).strip() for choice in item.get("choices", []) if str(choice).strip()][:8],
            })
        if (len(clean_title) < 3 or year_group is None or not 7 <= year_group <= 11
                or subject not in ("Maths", "English") or duration_minutes is None
                or not 5 <= duration_minutes <= 180 or not clean_questions):
            return None
        with Session(self.engine) as session:
            actor = self._account(session, username)
            if not actor or actor.role not in ("teacher", "admin"):
                return None
            paper = AssessmentPaperRecord(
                id=str(uuid.uuid4()), creator_account_id=actor.id, title=clean_title,
                year_group=year_group, subject=subject, duration_minutes=duration_minutes,
                topics_json=json.dumps(clean_topics), questions_json=json.dumps(clean_questions), created_at=_now(),
            )
            session.add(paper); session.commit(); return paper.id

    def assessment_papers(self, username):
        with Session(self.engine) as session:
            actor = self._account(session, username)
            if not actor or actor.role not in ("teacher", "admin"):
                return []
            statement = select(AssessmentPaperRecord).order_by(AssessmentPaperRecord.created_at.desc())
            if actor.role == "teacher":
                statement = statement.where(AssessmentPaperRecord.creator_account_id == actor.id)
            accounts = {row.id: row.username for row in session.exec(select(Account)).all()}
            return [{
                "id": row.id, "owner": accounts.get(row.creator_account_id, "Unknown"), "title": row.title,
                "year": row.year_group, "subject": row.subject, "duration": row.duration_minutes,
                "topics": json.loads(row.topics_json or "[]"), "questions": json.loads(row.questions_json or "[]"),
                "created_at": row.created_at,
            } for row in session.exec(statement).all()]

    def assessment_papers_for_student(self, username):
        """Return only assigned papers, with mark-scheme answers removed."""
        with Session(self.engine) as session:
            account = self._account(session, username)
            if not account or account.role != "student":
                return []
            class_ids = [row.class_id for row in session.exec(select(ClassMembership).where(
                ClassMembership.account_id == account.id, ClassMembership.membership_role == "student")).all()]
            if not class_ids:
                return []
            today = datetime.date.today().isoformat()
            assigned_ids = set()
            for row in session.exec(select(AssignmentRecord).where(AssignmentRecord.class_id.in_(class_ids))).all():
                available = row.status == "published" or (row.status == "scheduled" and row.publish_at and row.publish_at <= today)
                if available and str(row.pack_id or "").startswith("assessment:"):
                    assigned_ids.add(row.pack_id.split(":", 1)[1])
            if not assigned_ids:
                return []
            rows = session.exec(select(AssessmentPaperRecord).where(AssessmentPaperRecord.id.in_(assigned_ids))).all()
            result = []
            for row in rows:
                questions = json.loads(row.questions_json or "[]")
                for question in questions: question.pop("answer", None)
                result.append({"id": row.id, "title": row.title, "year": row.year_group, "subject": row.subject,
                    "duration": row.duration_minutes, "topics": json.loads(row.topics_json or "[]"),
                    "questions": questions, "created_at": row.created_at})
            return result

    def create_teacher_resource(self, username, title, year_group, subject, topic_id, summary, content, publish=False):
        year_group = _safe_int(year_group)
        title, content = str(title).strip(), str(content).strip()
        if (year_group is None or not 7 <= year_group <= 11 or subject not in ("Maths", "English")
                or len(title) < 3 or len(content) < 20 or not str(topic_id).strip()):
            return None
        with Session(self.engine) as session:
            actor = self._account(session, username)
            if not actor or actor.role not in ("teacher", "admin"):
                return None
            now = _now()
            resource = TeacherResourceRecord(
                owner_account_id=actor.id, title=title[:180], year_group=year_group, subject=subject,
                topic_id=str(topic_id).strip()[:96], summary=str(summary).strip()[:500], content=content[:12000],
                status="published" if publish else "draft", created_at=now, updated_at=now,
            )
            session.add(resource); session.commit(); session.refresh(resource); return resource.id

    def teacher_resources(self, username, published_only=False):
        with Session(self.engine) as session:
            actor = self._account(session, username)
            if not actor:
                return []
            statement = select(TeacherResourceRecord).order_by(TeacherResourceRecord.updated_at.desc())
            if actor.role == "teacher":
                statement = statement.where(TeacherResourceRecord.owner_account_id == actor.id)
            elif actor.role in ("student", "parent") or published_only:
                statement = statement.where(TeacherResourceRecord.status == "published")
            accounts = {row.id: row.username for row in session.exec(select(Account)).all()}
            return [{
                "id": row.id, "owner": accounts.get(row.owner_account_id, "Unknown"), "title": row.title,
                "year": row.year_group, "subject": row.subject, "topic": row.topic_id, "summary": row.summary,
                "content": row.content, "status": row.status, "created_at": row.created_at, "updated_at": row.updated_at,
            } for row in session.exec(statement).all()]

    def create_goal(self, username, title, subject="General", target_date=None):
        title = str(title).strip()
        if len(title) < 5 or subject not in ("General", "Maths", "English"):
            return None
        if target_date:
            try: target_date = datetime.date.fromisoformat(str(target_date)).isoformat()
            except ValueError: return None
        with Session(self.engine) as session:
            account = self._account(session, username)
            if not account or account.role != "student":
                return None
            row = LearningGoalRecord(account_id=account.id, title=title[:220], subject=subject,
                target_date=target_date, created_at=_now())
            session.add(row); session.commit(); session.refresh(row); return row.id

    def goals(self, username, include_completed=True, actor_username=None):
        with Session(self.engine) as session:
            account = self._account(session, username)
            actor = self._account(session, actor_username or username)
            if not account or not actor:
                return []
            allowed = actor.id == account.id or actor.role == "admin"
            if actor.role == "parent":
                allowed = bool(session.exec(select(LinkedAccountRecord).where(
                    LinkedAccountRecord.owner_account_id == actor.id,
                    LinkedAccountRecord.linked_account_id == account.id,
                )).first())
            if actor.role == "teacher":
                teacher_classes = {row.class_id for row in session.exec(select(ClassMembership).where(
                    ClassMembership.account_id == actor.id, ClassMembership.membership_role == "teacher")).all()}
                allowed = bool(teacher_classes.intersection(row.class_id for row in session.exec(select(ClassMembership).where(
                    ClassMembership.account_id == account.id, ClassMembership.membership_role == "student")).all()))
            if not allowed:
                return []
            statement = select(LearningGoalRecord).where(LearningGoalRecord.account_id == account.id)
            if not include_completed:
                statement = statement.where(LearningGoalRecord.status == "active")
            rows = session.exec(statement.order_by(LearningGoalRecord.created_at.desc())).all()
            return [{"id": row.id, "title": row.title, "subject": row.subject, "target_date": row.target_date,
                "status": row.status, "reflection": row.reflection, "created_at": row.created_at,
                "completed_at": row.completed_at} for row in rows]

    def complete_goal(self, username, goal_id, reflection=""):
        goal_id = _safe_int(goal_id)
        if goal_id is None:
            return False
        with Session(self.engine) as session:
            account = self._account(session, username); row = session.get(LearningGoalRecord, goal_id)
            if not account or not row or row.account_id != account.id or row.status != "active":
                return False
            row.status = "completed"; row.reflection = str(reflection).strip()[:1500]; row.completed_at = _now()
            session.add(row); session.commit(); return True

    def set_family_link(self, actor_username, parent_username, student_username, linked=True):
        with Session(self.engine) as session:
            actor = self._account(session, actor_username)
            parent = self._account(session, parent_username)
            student = self._account(session, student_username)
            if (not actor or actor.role != "admin" or not parent or parent.role != "parent"
                    or not student or student.role != "student" or parent.id == student.id):
                return False
            row = session.exec(select(LinkedAccountRecord).where(
                LinkedAccountRecord.owner_account_id == parent.id,
                LinkedAccountRecord.linked_account_id == student.id,
            )).first()
            if linked and not row:
                session.add(LinkedAccountRecord(owner_account_id=parent.id, linked_account_id=student.id))
            elif not linked and row:
                session.delete(row)
            session.commit(); return True

    def family_links(self, username):
        with Session(self.engine) as session:
            actor = self._account(session, username)
            if not actor or actor.role not in ("parent", "admin"):
                return []
            statement = select(LinkedAccountRecord)
            if actor.role == "parent":
                statement = statement.where(LinkedAccountRecord.owner_account_id == actor.id)
            accounts = {row.id: row for row in session.exec(select(Account)).all()}
            return [{"parent": accounts[row.owner_account_id].username, "student": accounts[row.linked_account_id].username}
                for row in session.exec(statement).all()
                if row.owner_account_id in accounts and row.linked_account_id in accounts]

    def add_safeguarding_action(self, actor_username, report_id, action, note=""):
        report_id = _safe_int(report_id)
        if report_id is None or action not in ("note", "assigned", "escalated", "resolved", "reopened"):
            return False
        with Session(self.engine) as session:
            actor = self._account(session, actor_username); report = session.get(SafetyReportRecord, report_id)
            if not actor or actor.role != "admin" or not report:
                return False
            if action == "resolved": report.status = "resolved"; report.resolved_at = _now(); session.add(report)
            elif action == "reopened": report.status = "open"; report.resolved_at = None; session.add(report)
            elif action in ("assigned", "escalated"): report.status = "in_progress"; session.add(report)
            session.add(SafeguardingActionRecord(report_id=report.id, actor_account_id=actor.id,
                action=action, note=str(note).strip()[:3000], created_at=_now()))
            session.commit(); return True

    def safeguarding_actions(self, actor_username, report_id):
        report_id = _safe_int(report_id)
        with Session(self.engine) as session:
            actor = self._account(session, actor_username)
            if not actor or actor.role != "admin" or report_id is None:
                return []
            accounts = {row.id: row.username for row in session.exec(select(Account)).all()}
            rows = session.exec(select(SafeguardingActionRecord).where(
                SafeguardingActionRecord.report_id == report_id).order_by(SafeguardingActionRecord.created_at)).all()
            return [{"id": row.id, "actor": accounts.get(row.actor_account_id, "Unknown"), "action": row.action,
                "note": row.note, "created_at": row.created_at} for row in rows]

    def counts(self):
        with Session(self.engine) as session:
            return {
                "diagnostic_results": len(session.exec(select(DiagnosticResultRecord.id)).all()),
                "lesson_progress": len(session.exec(select(LessonProgressRecord.id)).all()),
                "revision_plans": len(session.exec(select(RevisionPlanRecord.id)).all()),
                "revision_tasks": len(session.exec(select(RevisionTaskRecord.id)).all()),
                "preferences": len(session.exec(select(UserPreferenceRecord.account_id)).all()),
                "open_safety_reports": len(session.exec(select(SafetyReportRecord.id).where(SafetyReportRecord.status == "open")).all()),
                "open_privacy_requests": len(session.exec(select(PrivacyRequestRecord.id).where(PrivacyRequestRecord.status == "open")).all()),
                "bookmarks": len(session.exec(select(CurriculumBookmarkRecord.id)).all()),
                "pathways": len(session.exec(select(PathwayEnrollmentRecord.id).where(PathwayEnrollmentRecord.active == True)).all()),
                "topic_assessments": len(session.exec(select(TopicAssessmentRecord.id)).all()),
                "adaptive_states": len(session.exec(select(AdaptiveStateRecord.id)).all()),
                "custom_questions": len(session.exec(select(CustomQuestionRecord.id)).all()),
                "mock_exams": len(session.exec(select(MockExamAttemptRecord.id)).all()),
                "portfolio_items": len(session.exec(select(PortfolioItemRecord.id)).all()),
                "notifications": len(session.exec(select(NotificationRecord.id)).all()),
                "wellbeing_checkins": len(session.exec(select(WellbeingCheckInRecord.id)).all()),
                "accessibility_profiles": len(session.exec(select(AccessibilityProfileRecord.account_id)).all()),
                "mistakes": len(session.exec(select(MistakeRecord.id)).all()),
                "certificates": len(session.exec(select(CertificateRecord.id)).all()),
                "classroom_activities": len(session.exec(select(ClassroomActivityRecord.id)).all()),
                "classroom_responses": len(session.exec(select(ClassroomResponseRecord.id)).all()),
                "content_reports": len(session.exec(select(ContentReportRecord.id)).all()),
                "assessment_papers": len(session.exec(select(AssessmentPaperRecord.id)).all()),
                "teacher_resources": len(session.exec(select(TeacherResourceRecord.id)).all()),
                "learning_goals": len(session.exec(select(LearningGoalRecord.id)).all()),
                "safeguarding_actions": len(session.exec(select(SafeguardingActionRecord.id)).all()),
            }
