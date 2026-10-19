"""ORM 模型统一导出。所有模型必须在此导入以完成 Base.metadata 注册。"""
from app.core.database import Base  # noqa: F401
from app.models.edu import (  # noqa: F401
    Class, ClassRequest, Grade, KnowledgePoint, Subject, TeachingAssignment,
)
from app.models.learning import (  # noqa: F401
    KnowledgeMastery, Note, QuestionFavorite, ReviewPlan, StudyCheckin, StudyGoal,
    StudyRecord,
)
from app.models.lesson import (  # noqa: F401
    LessonPlan, LessonStage,
)
from app.models.ops import (  # noqa: F401
    AgentCallLog, Attachment, ErrorLog, JobExecutionLog, LoginLog,
    Notification, OperationLog, ScheduledJob,
)
from app.models.question import (  # noqa: F401
    Difficulty, Paper, PaperItem, PaperShare, Question, QuestionBankType,
    QuestionKnowledge, QuestionStatus, QuestionType,
)
from app.models.system import (  # noqa: F401
    IdentityType, Permission, PermissionType, Registration, Role,
    RolePermission, SysConfig, User, UserRole, UserStatus,
)
from app.models.task import (  # noqa: F401
    Answer, GradeStatus, Submission, Task, TaskAssignment, TaskStatus, TaskType,
    WrongQuestion,
)

__all__ = [
    "Base",
    # system
    "User", "Role", "Permission", "UserRole", "RolePermission", "Registration",
    "SysConfig",
    "UserStatus", "IdentityType", "PermissionType",
    # edu
    "Grade", "Subject", "Class", "KnowledgePoint", "TeachingAssignment",
    # question
    "Question", "QuestionKnowledge", "Paper", "PaperItem", "PaperShare",
    "QuestionType", "QuestionStatus", "QuestionBankType", "Difficulty",
    # task
    "Task", "TaskAssignment", "Submission", "Answer", "WrongQuestion",
    "TaskType", "TaskStatus", "GradeStatus",
    # learning
    "Note", "KnowledgeMastery", "ReviewPlan", "StudyRecord", "QuestionFavorite",
    "StudyGoal", "StudyCheckin",
    # ops
    "LoginLog", "OperationLog", "ErrorLog", "ScheduledJob", "JobExecutionLog",
    "Attachment", "AgentCallLog", "Notification",
]
