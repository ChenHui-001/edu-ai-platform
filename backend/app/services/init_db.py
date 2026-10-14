"""初始化种子数据：角色权限、年级学科、知识点、默认管理员、默认定时任务。"""
from typing import Dict, List, Tuple

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logger import get_logger
from app.core.security import hash_password
from app.models import (
    Grade, Permission, Role, RolePermission, ScheduledJob, Subject, User, UserRole,
)

logger = get_logger("init")


# ---------------------------------------------------------------- 权限点定义
# (code, name, type, path, icon, sort)
PERMISSIONS: List[Tuple[str, str, str, str, str, int]] = [
    # 系统管理
    ("system:user:list", "用户管理", "menu", "/admin/users", "User", 100),
    ("system:user:create", "新增用户", "button", None, None, 101),
    ("system:user:update", "编辑用户", "button", None, None, 102),
    ("system:user:delete", "删除用户", "button", None, None, 103),
    ("system:user:reset", "重置密码", "button", None, None, 104),
    ("system:role:list", "角色管理", "menu", "/admin/roles", "Avatar", 110),
    ("system:role:write", "角色增删改", "button", None, None, 111),
    ("system:audit:list", "注册审批", "menu", "/admin/registrations", "Stamp", 120),
    ("system:log:list", "日志审计", "menu", "/admin/logs", "Document", 130),
    ("system:job:list", "定时任务", "menu", "/admin/jobs", "Clock", 140),
    ("system:job:write", "任务管理", "button", None, None, 141),
    ("system:config:list", "系统配置", "menu", "/admin/settings", "Setting", 150),
    ("system:attachment:list", "附件管理", "menu", "/admin/attachments", "Paperclip", 160),

    # 教学资源
    ("resource:grade:list", "年级管理", "menu", "/admin/grades", "School", 200),
    ("resource:subject:list", "学科管理", "menu", "/admin/subjects", "Collection", 210),
    ("resource:knowledge:list", "知识点管理", "menu", "/admin/knowledge", "Share", 220),
    ("resource:knowledge:write", "知识点维护", "button", None, None, 221),
    ("resource:class:list", "班级管理", "menu", "/admin/classes", "OfficeBuilding", 230),
    ("resource:class:write", "班级维护", "button", None, None, 231),

    # 题库
    ("question:bank:list", "题库管理", "menu", "/teacher/questions", "Notebook", 300),
    ("question:bank:write", "题目增删改", "button", None, None, 301),
    ("question:bank:import", "批量导入", "button", None, None, 302),
    ("question:bank:audit", "公共题库审核", "button", None, None, 303),
    ("question:bank:export", "题目导出", "button", None, None, 304),

    # 试卷组卷
    ("paper:list", "试卷管理", "menu", "/teacher/papers", "Tickets", 310),
    ("paper:write", "组卷编辑", "button", None, None, 311),
    ("paper:ai", "AI 智能组卷", "button", None, None, 312),
    ("paper:share", "试卷分享", "button", None, None, 313),
    ("paper:export", "导出打印", "button", None, None, 314),

    # 作业考试
    ("task:list", "作业考试管理", "menu", "/teacher/tasks", "List", 320),
    ("task:write", "发布作业考试", "button", None, None, 321),
    ("grading:list", "批改中心", "menu", "/teacher/grading", "EditPen", 330),
    ("grading:do", "执行批改", "button", None, None, 331),
    ("grading:publish", "发布成绩", "button", None, None, 332),

    # 学情分析
    ("analysis:class", "班级学情分析", "menu", "/teacher/analysis", "TrendCharts", 340),
    ("analysis:student", "学生个体分析", "menu", "/teacher/students", "UserFilled", 341),
    ("report:teacher", "教师端报表", "menu", "/teacher/reports", "PieChart", 350),

    # 学生端
    ("student:practice", "随机练习", "menu", "/student/practice", "Edit", 400),
    ("student:exam", "模拟考试", "menu", "/student/exams", "Timer", 410),
    ("student:wrong", "错题本", "menu", "/student/wrong", "Warning", 420),
    ("student:note", "学习笔记", "menu", "/student/notes", "Notebook", 430),
    ("student:review", "智能复习", "menu", "/student/review", "Refresh", 440),
    ("student:report", "个人报表", "menu", "/student/report", "DataLine", 450),
    ("student:score", "成绩中心", "menu", "/student/scores", "Medal", 460),

    # AI 中心
    ("agent:chat", "AI 智能助手", "menu", "/agent/chat", "MagicStick", 500),
    ("agent:generate", "AI 出题", "menu", "/agent/generate", "Cpu", 501),
    ("agent:plan", "AI 学习规划", "menu", "/agent/plan", "Compass", 502),
    ("agent:logs", "AI 调用日志", "menu", "/admin/agent-logs", "Cpu", 510),

    # 管理员报表
    ("report:admin", "系统总览报表", "menu", "/admin/reports", "DataAnalysis", 600),
]

# 角色 -> 权限前缀匹配
ROLES: List[Dict] = [
    {
        "code": "sys_admin", "name": "系统管理员", "data_scope": "all", "sort": 1,
        "description": "全校全部数据，用户/角色/审批/配置/日志/任务/全量报表",
        "perms": ["*"],
    },
    {
        "code": "grade_admin", "name": "年级管理员", "data_scope": "grade", "sort": 2,
        "description": "本年级所有数据，师生管理、资源审核、学情报表",
        "perms": [
            "system:user:list", "system:user:create", "system:user:update",
            "system:log:list", "system:attachment:list",
            "resource:grade:list", "resource:subject:list", "resource:knowledge:list",
            "resource:knowledge:write", "resource:class:list", "resource:class:write",
            "question:bank:list", "question:bank:audit", "question:bank:export",
            "paper:list", "paper:export", "task:list",
            "analysis:class", "analysis:student", "report:teacher",
            "agent:chat", "agent:generate", "report:admin", "agent:logs",
        ],
    },
    {
        "code": "teacher", "name": "任课教师", "data_scope": "taught_class", "sort": 3,
        "description": "所授班级学生数据，出题组卷、发布作业考试、批改、学情分析",
        "perms": [
            "resource:knowledge:list", "resource:class:list",
            "question:bank:list", "question:bank:write", "question:bank:import",
            "question:bank:export",
            "paper:list", "paper:write", "paper:ai", "paper:share", "paper:export",
            "task:list", "task:write",
            "grading:list", "grading:do", "grading:publish",
            "analysis:class", "analysis:student", "report:teacher",
            "agent:chat", "agent:generate", "agent:plan",
        ],
    },
    {
        "code": "student", "name": "学生", "data_scope": "self", "sort": 4,
        "description": "仅个人学习数据，练习/考试/错题本/笔记/报表/AI 答疑",
        "perms": [
            "student:practice", "student:exam", "student:wrong", "student:note",
            "student:review", "student:report", "student:score",
            "agent:chat", "agent:plan",
        ],
    },
    {
        "code": "guest", "name": "访客", "data_scope": "none", "sort": 5,
        "description": "无业务数据，注册申请、系统公告查看",
        "perms": [],
    },
]

# 9 个年级
GRADES = [
    ("一年级", "primary", 1), ("二年级", "primary", 2), ("三年级", "primary", 3),
    ("四年级", "primary", 4), ("五年级", "primary", 5), ("六年级", "primary", 6),
    ("七年级", "junior", 7), ("八年级", "junior", 8), ("九年级", "junior", 9),
]

# 各年级学科（依需求文档 7.2 / 2.3）
SUBJECTS: Dict[int, List[Tuple[str, str]]] = {
    1: [("语文", "人教版"), ("数学", "人教版"), ("英语", "人教版"), ("科学", "教科版"), ("道德与法治", "人教版")],
    2: [("语文", "人教版"), ("数学", "人教版"), ("英语", "人教版"), ("科学", "教科版"), ("道德与法治", "人教版")],
    3: [("语文", "人教版"), ("数学", "人教版"), ("英语", "人教版"), ("科学", "教科版"), ("道德与法治", "人教版")],
    4: [("语文", "人教版"), ("数学", "人教版"), ("英语", "人教版"), ("科学", "教科版"), ("道德与法治", "人教版")],
    5: [("语文", "人教版"), ("数学", "人教版"), ("英语", "人教版"), ("科学", "教科版"), ("道德与法治", "人教版")],
    6: [("语文", "人教版"), ("数学", "人教版"), ("英语", "人教版"), ("科学", "教科版"), ("道德与法治", "人教版"), ("历史", "人教版"), ("地理", "人教版")],
    7: [("语文", "人教版"), ("数学", "人教版"), ("英语", "人教版"), ("生物", "人教版"), ("政治", "人教版"), ("历史", "人教版"), ("地理", "人教版")],
    8: [("语文", "人教版"), ("数学", "人教版"), ("英语", "人教版"), ("物理", "人教版"), ("化学", "人教版"), ("生物", "人教版"), ("政治", "人教版"), ("历史", "人教版"), ("地理", "人教版"), ("信息科技", "人教版")],
    9: [("语文", "人教版"), ("数学", "人教版"), ("英语", "人教版"), ("物理", "人教版"), ("化学", "人教版"), ("生物", "人教版"), ("政治", "人教版"), ("历史", "人教版"), ("地理", "人教版"), ("信息科技", "人教版")],
}

DEFAULT_JOBS = [
    ("清理过期考试", "app.services.task_jobs.clean_expired_exams", "0 3 * * *", "定时归档已结束的超期考试"),
    ("生成日报表", "app.services.task_jobs.generate_daily_report", "0 7 * * *", "统计前一日学习与考试数据"),
    ("清理临时附件", "app.services.task_jobs.clean_temp_attachments", "0 4 * * *", "清理超过 7 天的未绑定业务附件"),
    ("复习提醒推送", "app.services.task_jobs.push_review_reminders", "0 8 * * *", "按艾宾浩斯计划推送今日复习清单"),
    ("周报生成", "app.services.task_jobs.generate_weekly_report", "0 8 * * 1", "生成上周学情周报"),
]


def init_permissions(db: Session) -> None:
    """初始化权限点。"""
    existing = {p.code for p in db.scalars(select(Permission)).all()}
    new_perms = []
    for code, name, ptype, path, icon, sort in PERMISSIONS:
        if code not in existing:
            new_perms.append(
                Permission(code=code, name=name, type=ptype, path=path, icon=icon, sort=sort)
            )
    if new_perms:
        db.add_all(new_perms)
        db.commit()
    logger.info(f"权限点初始化完成，新增 {len(new_perms)} 个")


def init_roles(db: Session) -> None:
    """初始化 5 种预置角色及权限分配。"""
    all_perms = {p.code: p for p in db.scalars(select(Permission)).all()}
    for rdef in ROLES:
        role = db.scalar(select(Role).where(Role.code == rdef["code"]))
        if not role:
            role = Role(code=rdef["code"])
            db.add(role)
        role.name = rdef["name"]
        role.description = rdef["description"]
        role.data_scope = rdef["data_scope"]
        role.is_builtin = True
        role.is_active = True
        role.sort = rdef["sort"]
        db.flush()

        if "*" not in rdef["perms"]:
            codes = set(rdef["perms"])
            current = {p.code for p in role.permissions}
            for p in db.scalars(select(Permission)).all():
                if p.code in codes and p.code not in current:
                    db.add(RolePermission(role_id=role.id, permission_id=p.id))
                elif p.code not in codes and p.code in current:
                    db.execute(
                        RolePermission.__table__.delete().where(
                            RolePermission.role_id == role.id,
                            RolePermission.permission_id == p.id,
                        )
                    )
    db.commit()
    logger.info("预置角色初始化完成（5 种）")


def init_grades_subjects(db: Session) -> None:
    """初始化 1-9 年级与对应学科。"""
    if db.scalar(select(func.count()).select_from(Grade)) == 0:
        for name, stage, num in GRADES:
            db.add(Grade(name=name, stage=stage, grade_num=num, sort=num))
        db.commit()
        logger.info("年级初始化完成（1-9 年级）")

    if db.scalar(select(func.count()).select_from(Subject)) == 0:
        grades = {g.grade_num: g for g in db.scalars(select(Grade)).all()}
        for num, subs in SUBJECTS.items():
            g = grades.get(num)
            if not g:
                continue
            for i, (sname, version) in enumerate(subs):
                db.add(
                    Subject(
                        name=sname, textbook_version=version,
                        grade_id=g.id, code=f"{num}_{sname}", sort=i,
                    )
                )
        db.commit()
        logger.info("学科初始化完成")


def init_admin(db: Session) -> None:
    """创建默认系统管理员。"""
    if db.scalar(select(func.count()).select_from(User).where(User.username == "admin")):
        return
    admin = User(
        username="admin",
        password=hash_password("Admin@123456"),
        real_name="系统管理员",
        identity="sys_admin",
        status="active",
        school_name="示范学校",
        must_change_password=True,
    )
    db.add(admin)
    db.flush()
    role = db.scalar(select(Role).where(Role.code == "sys_admin"))
    if role:
        db.add(UserRole(user_id=admin.id, role_id=role.id))
    db.commit()
    logger.info("默认管理员已创建：账号 admin / 密码 Admin@123456（首次登录须改密）")


def init_jobs(db: Session) -> None:
    """初始化默认定时任务。"""
    for name, func_path, cron, desc in DEFAULT_JOBS:
        exists = db.scalar(select(ScheduledJob).where(ScheduledJob.name == name))
        if not exists:
            db.add(
                ScheduledJob(
                    name=name, description=desc, func_path=func_path,
                    cron_expression=cron, is_builtin=True, is_active=True,
                )
            )
    db.commit()
    logger.info(f"默认定时任务初始化完成（{len(DEFAULT_JOBS)} 个）")


def init_demo_data(db: Session) -> None:
    """创建演示用班级、教师、学生，便于快速体验。"""
    from app.models import Class, TeachingAssignment

    if db.scalar(select(func.count()).select_from(Class)) > 0:
        return

    grades = {g.grade_num: g for g in db.scalars(select(Grade)).all()}
    teacher_role = db.scalar(select(Role).where(Role.code == "teacher"))
    student_role = db.scalar(select(Role).where(Role.code == "student"))

    demo_classes = []
    for num in (1, 7):
        g = grades.get(num)
        if not g:
            continue
        for idx in (1, 2):
            k = Class(name=f"{g.name}({idx})班", grade_id=g.id)
            db.add(k)
            demo_classes.append((k, g))
    db.flush()

    for i, (k, g) in enumerate(demo_classes):
        teacher = User(
            username=f"teacher{i + 1}", password=hash_password("Teacher@123"),
            real_name=f"教师{i + 1}", identity="teacher", status="active",
            school_name="示范学校", grade_id=g.id, class_id=k.id,
        )
        db.add(teacher)
        db.flush()
        if teacher_role:
            db.add(UserRole(user_id=teacher.id, role_id=teacher_role.id))
        k.head_teacher_id = teacher.id

        subs = db.scalars(select(Subject).where(Subject.grade_id == g.id)).all()
        for s in subs[:3]:
            db.add(
                TeachingAssignment(
                    teacher_id=teacher.id, class_id=k.id,
                    subject_id=s.id, grade_id=g.id,
                )
            )

        for j in range(1, 4):
            stu = User(
                username=f"stu{g.grade_num}{i}{j}", password=hash_password("Student@123"),
                real_name=f"学生{g.grade_num}{i}{j}", identity="student",
                status="active", school_name="示范学校",
                grade_id=g.id, class_id=k.id,
            )
            db.add(stu)
            db.flush()
            if student_role:
                db.add(UserRole(user_id=stu.id, role_id=student_role.id))
    db.commit()
    logger.info("演示数据初始化完成（4 个班级 / 4 名教师 / 12 名学生）")


def init_all(db: Session) -> None:
    """按依赖顺序执行全部初始化。"""
    init_permissions(db)
    init_roles(db)
    init_grades_subjects(db)
    init_admin(db)
    init_jobs(db)
    init_demo_data(db)
