"""Database models for secure EduPy accounts."""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, SQLModel


def utc_now():
    return datetime.now(timezone.utc)


class Account(SQLModel, table=True):
    """Secure login identity linked to relational learning records."""

    __tablename__ = "accounts"

    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True, min_length=1, max_length=32)
    password_hash: str
    role: str = Field(default="student", max_length=16)
    year_group: int = Field(default=7, ge=7, le=11)
    is_active: bool = True
    force_password_change: bool = False
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class ClassRecord(SQLModel, table=True):
    __tablename__ = "classes"

    id: str = Field(primary_key=True, max_length=64)
    title: str
    subject: str = "General"
    year_group: int = Field(default=7, ge=7, le=11)
    join_code: str = Field(index=True, unique=True, max_length=12)
    created_at: str
    archived: bool = False
    metadata_json: str = "{}"


class ClassMembership(SQLModel, table=True):
    __tablename__ = "class_memberships"
    __table_args__ = (UniqueConstraint("class_id", "account_id", "membership_role"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    class_id: str = Field(foreign_key="classes.id", index=True)
    account_id: int = Field(foreign_key="accounts.id", index=True)
    membership_role: str = Field(max_length=12)


class AssignmentRecord(SQLModel, table=True):
    __tablename__ = "assignments"

    id: str = Field(primary_key=True, max_length=64)
    class_id: str = Field(foreign_key="classes.id", index=True)
    pack_id: Optional[str] = None
    title: str
    subject: str = "General"
    instructions: str = ""
    created_by_account_id: Optional[int] = Field(default=None, foreign_key="accounts.id")
    created_at: str
    due_date: Optional[str] = None
    max_marks: int = 100
    reward_tokens: int = 5
    status: str = Field(default="published", index=True)
    publish_at: Optional[str] = None
    allow_late: bool = True
    resubmissions_allowed: bool = True
    rubric_json: str = "[]"
    auto_grade_json: str = "{}"


class SubmissionRecord(SQLModel, table=True):
    __tablename__ = "submissions"
    __table_args__ = (UniqueConstraint("assignment_id", "student_account_id"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    assignment_id: str = Field(foreign_key="assignments.id", index=True)
    student_account_id: int = Field(foreign_key="accounts.id", index=True)
    submitted_at: str
    answer: str = ""
    attachment: Optional[str] = None
    grade: Optional[float] = None
    feedback: Optional[str] = None
    auto_graded: bool = False
    reward_awarded: bool = False
    late: bool = False
    marked_by_account_id: Optional[int] = Field(default=None, foreign_key="accounts.id")
    marked_at: Optional[str] = None


class AssignmentExtension(SQLModel, table=True):
    __tablename__ = "assignment_extensions"
    __table_args__ = (UniqueConstraint("assignment_id", "student_account_id"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    assignment_id: str = Field(foreign_key="assignments.id", index=True)
    student_account_id: int = Field(foreign_key="accounts.id", index=True)
    due_date: str


class PrivateTeacherNote(SQLModel, table=True):
    __tablename__ = "private_teacher_notes"
    __table_args__ = (UniqueConstraint("assignment_id", "student_account_id"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    assignment_id: str = Field(foreign_key="assignments.id", index=True)
    student_account_id: int = Field(foreign_key="accounts.id", index=True)
    comment: str = ""


class AssignmentTemplateRecord(SQLModel, table=True):
    __tablename__ = "assignment_templates"

    id: str = Field(primary_key=True, max_length=64)
    name: str
    owner_account_id: Optional[int] = Field(default=None, foreign_key="accounts.id")
    shared: bool = False
    created_at: str
    fields_json: str = "{}"


class EducationSetting(SQLModel, table=True):
    __tablename__ = "education_settings"

    key: str = Field(primary_key=True, max_length=64)
    value: str


class LearnerProgressRecord(SQLModel, table=True):
    __tablename__ = "learner_progress"

    account_id: int = Field(primary_key=True, foreign_key="accounts.id")
    xp: int = 0
    level: int = 1
    total_xp: int = 0
    questions_answered: int = 0
    english_completed: int = 0
    maths_completed: int = 0
    tokens: int = 0
    last_daily_claim: Optional[str] = None
    daily_reward_streak: int = 0
    token_earn_day: Optional[str] = None
    tokens_earned_today: int = 0
    current_theme: str = "Default"
    school_safe_mode: bool = False


class RewardTransaction(SQLModel, table=True):
    __tablename__ = "reward_transactions"
    __table_args__ = (UniqueConstraint("account_id", "event_id"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    account_id: int = Field(foreign_key="accounts.id", index=True)
    event_id: str = Field(index=True, max_length=96)
    date: str
    amount: int
    reason: str


class ThemeUnlock(SQLModel, table=True):
    __tablename__ = "theme_unlocks"
    __table_args__ = (UniqueConstraint("account_id", "theme_name"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    account_id: int = Field(foreign_key="accounts.id", index=True)
    theme_name: str = Field(max_length=32)


class AchievementUnlock(SQLModel, table=True):
    __tablename__ = "achievement_unlocks"
    __table_args__ = (UniqueConstraint("account_id", "achievement_id"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    account_id: int = Field(foreign_key="accounts.id", index=True)
    achievement_id: str = Field(max_length=64)


class MasteryRecord(SQLModel, table=True):
    __tablename__ = "mastery_records"
    __table_args__ = (UniqueConstraint("account_id", "subject", "topic_id"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    account_id: int = Field(foreign_key="accounts.id", index=True)
    subject: str = Field(max_length=32)
    topic_id: str = Field(max_length=64)
    attempts: int = 0
    earned: float = 0.0
    possible: float = 0.0
    recent: float = 0.0
    updated: Optional[str] = None


class RecentTopicRecord(SQLModel, table=True):
    __tablename__ = "recent_topic_records"
    __table_args__ = (UniqueConstraint("account_id", "position"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    account_id: int = Field(foreign_key="accounts.id", index=True)
    position: int
    subject: str = Field(max_length=32)
    topic_id: str = Field(max_length=64)
    score: int = 0
    date: Optional[str] = None


class LinkedAccountRecord(SQLModel, table=True):
    __tablename__ = "linked_accounts"
    __table_args__ = (UniqueConstraint("owner_account_id", "linked_account_id"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    owner_account_id: int = Field(foreign_key="accounts.id", index=True)
    linked_account_id: int = Field(foreign_key="accounts.id", index=True)


class ProgressSetting(SQLModel, table=True):
    __tablename__ = "progress_settings"

    key: str = Field(primary_key=True, max_length=64)
    value: str


class DiagnosticResultRecord(SQLModel, table=True):
    __tablename__ = "diagnostic_results"

    id: Optional[int] = Field(default=None, primary_key=True)
    account_id: int = Field(foreign_key="accounts.id", index=True)
    batch_id: str = Field(index=True, max_length=64)
    year_group: int
    subject: str = Field(max_length=32)
    topic_id: str = Field(max_length=64)
    earned: float
    possible: float
    completed_at: str


class LessonProgressRecord(SQLModel, table=True):
    __tablename__ = "lesson_progress"
    __table_args__ = (UniqueConstraint("account_id", "subject", "topic_id"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    account_id: int = Field(foreign_key="accounts.id", index=True)
    subject: str = Field(max_length=32)
    topic_id: str = Field(max_length=64)
    views: int = 0
    completed: bool = False
    last_viewed_at: str


class RevisionPlanRecord(SQLModel, table=True):
    __tablename__ = "revision_plans"

    id: Optional[int] = Field(default=None, primary_key=True)
    account_id: int = Field(foreign_key="accounts.id", unique=True, index=True)
    title: str
    exam_date: str
    created_at: str


class RevisionTaskRecord(SQLModel, table=True):
    __tablename__ = "revision_tasks"

    id: Optional[int] = Field(default=None, primary_key=True)
    plan_id: int = Field(foreign_key="revision_plans.id", index=True)
    subject: str = Field(max_length=32)
    topic_id: str = Field(max_length=64)
    due_date: str
    completed: bool = False


class UserPreferenceRecord(SQLModel, table=True):
    __tablename__ = "user_preferences"

    account_id: int = Field(primary_key=True, foreign_key="accounts.id")
    reduced_motion: bool = False
    high_contrast: bool = False
    focus_mode: bool = False
    font_scale: int = 100
    extra_time_percent: int = 0


class SafetyReportRecord(SQLModel, table=True):
    __tablename__ = "safety_reports"

    id: Optional[int] = Field(default=None, primary_key=True)
    reporter_account_id: int = Field(foreign_key="accounts.id", index=True)
    category: str = Field(max_length=48)
    description: str
    status: str = Field(default="open", index=True)
    created_at: str
    resolved_at: Optional[str] = None


class PrivacyRequestRecord(SQLModel, table=True):
    __tablename__ = "privacy_requests"

    id: Optional[int] = Field(default=None, primary_key=True)
    account_id: int = Field(foreign_key="accounts.id", index=True)
    request_type: str = Field(max_length=32)
    status: str = Field(default="open", index=True)
    created_at: str
    resolved_at: Optional[str] = None


class CurriculumBookmarkRecord(SQLModel, table=True):
    __tablename__ = "curriculum_bookmarks"
    __table_args__ = (UniqueConstraint("account_id", "subject", "topic_id"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    account_id: int = Field(foreign_key="accounts.id", index=True)
    year_group: int
    subject: str = Field(max_length=32)
    topic_id: str = Field(max_length=64)
    created_at: str


class PathwayEnrollmentRecord(SQLModel, table=True):
    __tablename__ = "pathway_enrollments"
    __table_args__ = (UniqueConstraint("account_id", "pathway_id"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    account_id: int = Field(foreign_key="accounts.id", index=True)
    pathway_id: str = Field(max_length=64)
    active: bool = True
    enrolled_at: str


class TopicAssessmentRecord(SQLModel, table=True):
    __tablename__ = "topic_assessments"

    id: Optional[int] = Field(default=None, primary_key=True)
    account_id: int = Field(foreign_key="accounts.id", index=True)
    year_group: int
    subject: str = Field(max_length=32)
    topic_id: str = Field(max_length=64, index=True)
    assessment_type: str = Field(max_length=24)
    earned: float
    possible: float
    completed_at: str
    retention_due: Optional[str] = None


class AdaptiveStateRecord(SQLModel, table=True):
    __tablename__ = "adaptive_states"
    __table_args__ = (UniqueConstraint("account_id", "subject", "topic_id"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    account_id: int = Field(foreign_key="accounts.id", index=True)
    subject: str = Field(max_length=32)
    topic_id: str = Field(max_length=64)
    difficulty: int = 1
    correct_streak: int = 0
    updated_at: str


class CustomQuestionRecord(SQLModel, table=True):
    __tablename__ = "custom_questions"

    id: Optional[int] = Field(default=None, primary_key=True)
    owner_account_id: int = Field(foreign_key="accounts.id", index=True)
    year_group: int = Field(ge=7, le=11)
    subject: str = Field(max_length=32, index=True)
    topic_id: str = Field(max_length=64, index=True)
    question_type: str = Field(default="short", max_length=24)
    prompt: str
    choices_json: str = "[]"
    answer: str = ""
    marks: int = 1
    status: str = Field(default="draft", max_length=16, index=True)
    moderation_note: str = ""
    created_at: str
    reviewed_at: Optional[str] = None


class MockExamAttemptRecord(SQLModel, table=True):
    __tablename__ = "mock_exam_attempts"

    id: Optional[int] = Field(default=None, primary_key=True)
    account_id: int = Field(foreign_key="accounts.id", index=True)
    year_group: int
    subject: str = Field(max_length=32)
    earned: float
    possible: float
    duration_seconds: int = 0
    flagged_count: int = 0
    completed_at: str


class PortfolioItemRecord(SQLModel, table=True):
    __tablename__ = "portfolio_items"

    id: Optional[int] = Field(default=None, primary_key=True)
    account_id: int = Field(foreign_key="accounts.id", index=True)
    title: str
    subject: str = Field(max_length=32)
    description: str = ""
    evidence: str = ""
    created_at: str


class NotificationRecord(SQLModel, table=True):
    __tablename__ = "notifications"

    id: Optional[int] = Field(default=None, primary_key=True)
    account_id: int = Field(foreign_key="accounts.id", index=True)
    title: str
    message: str
    category: str = Field(default="Learning", max_length=32)
    read: bool = False
    created_at: str


class WellbeingCheckInRecord(SQLModel, table=True):
    __tablename__ = "wellbeing_checkins"

    id: Optional[int] = Field(default=None, primary_key=True)
    account_id: int = Field(foreign_key="accounts.id", index=True)
    mood: int = Field(ge=1, le=5)
    note: str = ""
    created_at: str


class AccessibilityProfileRecord(SQLModel, table=True):
    __tablename__ = "accessibility_profiles"

    account_id: int = Field(primary_key=True, foreign_key="accounts.id")
    dyslexia_friendly: bool = False
    reading_ruler: bool = False
    generous_spacing: bool = False
    calm_palette: bool = False


class MistakeRecord(SQLModel, table=True):
    __tablename__ = "mistake_notebook"

    id: Optional[int] = Field(default=None, primary_key=True)
    account_id: int = Field(foreign_key="accounts.id", index=True)
    year_group: int
    subject: str = Field(max_length=32)
    topic_id: str = Field(max_length=64, index=True)
    prompt: str
    response: str = ""
    expected: str = ""
    mastered: bool = False
    created_at: str


class CertificateRecord(SQLModel, table=True):
    __tablename__ = "certificates"

    id: Optional[int] = Field(default=None, primary_key=True)
    account_id: int = Field(foreign_key="accounts.id", index=True)
    certificate_key: str = Field(max_length=96, index=True)
    title: str
    detail: str = ""
    issued_at: str


class ClassroomActivityRecord(SQLModel, table=True):
    __tablename__ = "classroom_activities"

    id: Optional[int] = Field(default=None, primary_key=True)
    class_id: str = Field(foreign_key="classes.id", index=True)
    creator_account_id: int = Field(foreign_key="accounts.id", index=True)
    title: str
    activity_type: str = Field(default="poll", max_length=24)
    prompt: str
    options_json: str = "[]"
    status: str = Field(default="live", max_length=16, index=True)
    created_at: str


class ClassroomResponseRecord(SQLModel, table=True):
    __tablename__ = "classroom_responses"
    __table_args__ = (UniqueConstraint("activity_id", "account_id"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    activity_id: int = Field(foreign_key="classroom_activities.id", index=True)
    account_id: int = Field(foreign_key="accounts.id", index=True)
    response: str
    created_at: str


class ContentReportRecord(SQLModel, table=True):
    __tablename__ = "content_reports"

    id: Optional[int] = Field(default=None, primary_key=True)
    reporter_account_id: int = Field(foreign_key="accounts.id", index=True)
    question_id: Optional[int] = Field(default=None, foreign_key="custom_questions.id", index=True)
    reason: str
    status: str = Field(default="open", max_length=16, index=True)
    created_at: str


class AssessmentPaperRecord(SQLModel, table=True):
    __tablename__ = "assessment_papers"

    id: str = Field(primary_key=True, max_length=64)
    creator_account_id: int = Field(foreign_key="accounts.id", index=True)
    title: str = Field(max_length=180)
    year_group: int
    subject: str = Field(max_length=32)
    duration_minutes: int = 45
    topics_json: str = "[]"
    questions_json: str = "[]"
    created_at: str


class TeacherResourceRecord(SQLModel, table=True):
    __tablename__ = "teacher_resources"

    id: Optional[int] = Field(default=None, primary_key=True)
    owner_account_id: int = Field(foreign_key="accounts.id", index=True)
    title: str = Field(max_length=180)
    year_group: int
    subject: str = Field(max_length=32)
    topic_id: str = Field(max_length=96)
    summary: str = ""
    content: str
    status: str = Field(default="draft", index=True, max_length=24)
    created_at: str
    updated_at: str


class LearningGoalRecord(SQLModel, table=True):
    __tablename__ = "learning_goals"

    id: Optional[int] = Field(default=None, primary_key=True)
    account_id: int = Field(foreign_key="accounts.id", index=True)
    title: str = Field(max_length=220)
    subject: str = Field(default="General", max_length=32)
    target_date: Optional[str] = None
    status: str = Field(default="active", index=True, max_length=24)
    reflection: str = ""
    created_at: str
    completed_at: Optional[str] = None


class SafeguardingActionRecord(SQLModel, table=True):
    __tablename__ = "safeguarding_actions"

    id: Optional[int] = Field(default=None, primary_key=True)
    report_id: int = Field(foreign_key="safety_reports.id", index=True)
    actor_account_id: int = Field(foreign_key="accounts.id", index=True)
    action: str = Field(max_length=32)
    note: str = ""
    created_at: str
