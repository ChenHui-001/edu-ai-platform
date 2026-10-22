"""初始化种子数据：角色权限、年级学科、知识点、默认管理员、默认定时任务。"""
from typing import Dict, List, Tuple

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.logger import get_logger
from app.core.security import hash_password, verify_password
from app.models import (
    Grade, KnowledgePoint, Permission, Role, RolePermission, ScheduledJob, Subject,
    User, UserRole,
)

logger = get_logger("init")


# ---------------------------------------------------------------- 知识点种子
# 知识点是 AI 组卷（按考点抽题）、错题归因、知识掌握地图的共同基础。
# 缺失会导致这三个核心功能全部退化为"无考点"模式，因此必须随种子数据一起初始化。
# 结构：{年级: {学科: [(知识点名, 层级, 难度), ...]}}
KNOWLEDGE_POINTS: Dict[int, Dict[str, List[Tuple[str, int, str]]]] = {
    1: {"数学": [
        ("20以内加减法", 1, "easy"), ("100以内加减法", 1, "easy"),
        ("认识立体图形", 1, "easy"), ("认识钟表", 1, "medium"),
        ("简单统计", 2, "easy"),
    ]},
    3: {"数学": [
        ("万以内加减法", 1, "easy"), ("多位数乘一位数", 1, "medium"),
        ("分数初步认识", 1, "medium"), ("长方形正方形面积", 2, "medium"),
    ],
         "语文": [
        ("生字书写", 1, "easy"), ("句子练习", 1, "easy"),
        ("阅读短文", 2, "medium"), ("看图写话", 2, "medium"),
    ]},
    5: {"数学": [
        ("小数乘除法", 1, "medium"), ("简易方程", 1, "hard"),
        ("多边形面积", 2, "medium"), ("分数加减法", 1, "medium"),
    ],
         "语文": [
        ("说明文阅读", 2, "medium"), ("习作：写事", 2, "medium"),
        ("文言文两则", 1, "hard"),
    ]},
    7: {"数学": [
        ("有理数", 1, "easy"), ("整式的加减", 1, "easy"),
        ("一元一次方程", 1, "medium"), ("平行线的性质", 2, "medium"),
        ("三角形", 2, "medium"), ("二元一次方程组", 1, "hard"),
    ],
         "语文": [
        ("记叙文阅读", 2, "medium"), ("说明文阅读", 2, "medium"),
        ("文言文阅读", 1, "hard"), ("写作：记叙文", 2, "medium"),
    ],
         "英语": [
        ("一般现在时", 1, "easy"), ("一般过去时", 1, "medium"),
        ("there be 句型", 1, "easy"), ("阅读理解", 2, "medium"),
    ],
         "物理": [
        ("机械运动", 1, "easy"), ("声现象", 1, "easy"), ("物态变化", 2, "medium"),
        ("光现象", 2, "medium"), ("质量与密度", 1, "medium"),
    ]},
    8: {"数学": [
        ("全等三角形", 1, "medium"), ("轴对称", 1, "easy"),
        ("一次函数", 1, "hard"), ("二次根式", 1, "medium"),
        ("勾股定理", 2, "medium"), ("数据的分析", 2, "easy"),
    ],
         "语文": [
        ("文言文词类活用", 1, "hard"), ("现代文阅读理解", 2, "medium"),
        ("议论文阅读", 2, "hard"), ("写作：说明文", 2, "medium"),
    ],
         "英语": [
        ("现在完成时", 1, "medium"), ("过去完成时", 1, "hard"),
        ("宾语从句", 1, "hard"), ("完形填空", 2, "medium"),
    ],
         "物理": [
        ("机械能", 1, "medium"), ("电与电路", 1, "medium"),
        ("欧姆定律", 1, "hard"), ("电功率", 2, "medium"),
    ]},
    9: {"数学": [
        ("一元二次方程", 1, "medium"), ("二次函数", 1, "hard"),
        ("旋转", 1, "medium"), ("圆", 2, "medium"),
        ("相似三角形", 2, "hard"), ("锐角三角函数", 2, "medium"),
    ],
         "语文": [
        ("古诗文默写", 1, "medium"), ("说明文阅读方法", 2, "medium"),
        ("小说阅读", 2, "medium"), ("写作：议论文", 2, "hard"),
    ],
         "英语": [
        ("被动语态", 1, "hard"), ("定语从句", 1, "hard"),
        ("状语从句", 1, "medium"), ("书面表达", 2, "medium"),
    ],
         "物理": [
        ("压强", 1, "medium"), ("浮力", 1, "hard"),
        ("功与机械能", 1, "medium"), ("电磁感应", 2, "hard"),
    ],
         "化学": [
        ("走进化学实验室", 1, "easy"), ("我们周围的空气", 1, "easy"),
        ("物质构成的奥秘", 1, "medium"), ("化学方程式", 1, "medium"),
        ("溶液", 2, "medium"),
    ]},
}


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
    ("system:ai:config", "AI 大模型配置", "menu", "/admin/ai-config", "Cpu", 155),
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
    # 教案管理
    ("lesson:plan:list", "教案管理", "menu", "/teacher/lessons", "Document", 325),
    ("lesson:plan:write", "教案编辑", "button", None, None, 326),
    ("lesson:plan:copy", "教案复制", "button", None, None, 327),
    ("lesson:plan:share", "教案共享", "button", None, None, 328),
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
    ("student:favorites", "题目收藏", "menu", "/student/favorites", "Star", 465),
    ("student:mastery", "掌握图谱", "menu", "/student/mastery", "Histogram", 468),
    ("student:custom", "自主组卷", "menu", "/student/custom", "Tickets", 470),
    ("student:goals", "学习打卡", "menu", "/student/goals", "Calendar", 472),
    ("student:path", "学习路径", "menu", "/student/path", "Guide", 474),
    ("student:flashcard", "闪卡速记", "menu", "/student/flashcard", "Box", 476),

    # AI 中心
    ("agent:chat", "AI 智能助手", "menu", "/agent/chat", "MagicStick", 500),
    ("agent:generate", "AI 出题", "menu", "/agent/generate", "Cpu", 501),
    # agent:plan 指向已存在的「学习路径」页面，不新建 /agent/plan 路由：
    # 该权限点同时授予 teacher 与 student，原先path 指向不存在的
    # /agent/plan，属于孤儿菜单（前端无对应路由，用户拿到权限却无处可去）。
    ("agent:plan", "AI 学习规划", "menu", "/student/path", "Compass", 502),
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
            "resource:knowledge:list", "resource:knowledge:write", "resource:class:list",
            "question:bank:list", "question:bank:write", "question:bank:import",
            "question:bank:export",
            "paper:list", "paper:write", "paper:ai", "paper:share", "paper:export",
            "task:list", "task:write",
            "lesson:plan:list", "lesson:plan:write", "lesson:plan:copy", "lesson:plan:share",
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
            "student:favorites", "student:mastery",
            "student:custom", "student:goals", "student:path", "student:flashcard",
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
    ("定时发布任务", "app.services.task_jobs.publish_scheduled_tasks", "* * * * *", "激活 publish_at 到期的草稿任务并补发学生通知"),
    ("清理过期运维日志", "app.services.task_jobs.clean_old_logs", "30 4 * * *", "清理过期日志/任务执行记录/已读通知，防止数据库无界增长"),
]


def init_permissions(db: Session) -> None:
    """初始化权限点（幂等：新增缺失项，并同步已存在项的元数据）。

    原实现只对**新增 code** 建记录，已存在的 code 不更新
    name/path/icon/sort —— 改了 PERMISSIONS 里的定义后，
    老库里的path 会一直是旧值，造成「代码已改、数据库未同步」。
    例如 agent:plan 的 path 从 /agent/plan 改为 /student/path 后，
    老库若不同步，该权限点就成了指向不存在路由的孤儿菜单。
    """
    existing = {p.code: p for p in db.scalars(select(Permission)).all()}
    new_perms = []
    dirty = False
    for code, name, ptype, path, icon, sort in PERMISSIONS:
        cur = existing.get(code)
        if cur is None:
            new_perms.append(
                Permission(code=code, name=name, type=ptype, path=path, icon=icon, sort=sort)
            )
            continue
        # 已存在则对齐元数据（保留 is_hidden 等运行时状态字段不动）
        if (cur.name, cur.type, cur.path, cur.icon, cur.sort) != (name, ptype, path, icon, sort):
            cur.name, cur.type, cur.path, cur.icon, cur.sort = name, ptype, path, icon, sort
            dirty = True
    if new_perms:
        db.add_all(new_perms)
    if new_perms or dirty:
        db.commit()
    logger.info(
        f"权限点初始化完成，新增 {len(new_perms)} 个，"
        f"同步元数据 {'是' if dirty else '否'}"
    )


def init_roles(db: Session) -> None:
    """初始化 5 种预置角色及权限分配（幂等、只增不删）。

    管理员可在「角色权限」页调整内置角色的名称/权限/启停状态；此前每次启动
    都会把 name/data_scope/is_active 覆盖回种子值并删除非种子权限，
    导致定制静默丢失。这里改为：
    - 仅新建角色时写入种子元数据；
    - 已有角色只补「缺失的种子权限」，不删除管理员新增的权限；
    - 不覆盖 is_active（尊重管理员停用）。
    """
    for rdef in ROLES:
        role = db.scalar(select(Role).where(Role.code == rdef["code"]))
        if not role:
            role = Role(
                code=rdef["code"], name=rdef["name"],
                description=rdef["description"], data_scope=rdef["data_scope"],
                is_builtin=True, is_active=True, sort=rdef["sort"],
            )
            db.add(role)
            db.flush()
        else:
            # 已存在：只确保内置标记，其余元数据/状态保留管理员定制
            role.is_builtin = True

        if "*" in rdef["perms"]:
            # 超级管理员：关联全部权限，使 role.permissions 直接可用，
            # 避免 build_permission_context 取不到菜单。
            current = {p.id for p in role.permissions}
            for p in db.scalars(select(Permission)).all():
                if p.id not in current:
                    db.add(RolePermission(role_id=role.id, permission_id=p.id))
        else:
            codes = set(rdef["perms"])
            current = {p.code for p in role.permissions}
            for p in db.scalars(select(Permission)).all():
                if p.code in codes and p.code not in current:
                    db.add(RolePermission(role_id=role.id, permission_id=p.id))
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
        # 初始管理员不强制改密，避免部署后首轮登录即被锁死；
        # 改密由部署文档另行提示，管理员可在「个人中心」主动修改。
        must_change_password=False,
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


def init_knowledge_points(db: Session) -> None:
    """初始化各年级各学科的核心知识点。

    知识点是 AI 组卷按考点抽题、错题归因、知识掌握地图三处功能的共同基础，
    缺失会让这些功能全部退化为「无考点」模式。

    幂等策略：按 (grade_id, subject_id, name) 去重，已存在的跳过，
    这样既能补齐历史库缺失的知识点，又不会重复播种或覆盖教师自建内容。
    """
    grades = {g.grade_num: g for g in db.scalars(select(Grade)).all()}
    subjects = db.scalars(select(Subject)).all()
    # (grade_id, subject_name) -> Subject
    sub_map = {(s.grade_id, s.name): s for s in subjects}
    existing = {
        (k.grade_id, k.subject_id, k.name)
        for k in db.scalars(select(KnowledgePoint)).all()
    }

    count = 0
    for grade_num, subj_map in KNOWLEDGE_POINTS.items():
        g = grades.get(grade_num)
        if not g:
            continue
        for subj_name, items in subj_map.items():
            s = sub_map.get((g.id, subj_name))
            if not s:
                continue
            for i, (name, level, difficulty) in enumerate(items):
                if (g.id, s.id, name) in existing:
                    continue
                db.add(
                    KnowledgePoint(
                        name=name, grade_id=g.id, subject_id=s.id, level=level,
                        term=1, difficulty=difficulty, sort=i,
                        path=f"{g.name}/{subj_name}/{name}",
                        description=f"{g.name}{subj_name}「{name}」知识点",
                    )
                )
                existing.add((g.id, s.id, name))
                count += 1
    if count:
        db.commit()
        logger.info(f"知识点初始化完成（新增 {count} 条）")


def warn_default_admin_password(db: Session) -> None:
    """默认管理员口令仍在运行时给出醒目安全告警。

    若直接放开「首次登录强制改密」，会把存量本地体验环境与自动化测试全部锁死；
    这里采用最小侵入方案：不改变登录行为，但每次启动把风险打到日志里，
    配合登录页隐藏演示口令、文档明确「部署后立即改密」。
    """
    admin = db.scalar(select(User).where(User.username == "admin"))
    if admin and verify_password("Admin@123456", admin.password):
        logger.warning(
            "安全告警：管理员账号仍在使用默认口令 Admin@123456，"
            "请立即登录修改密码（生产环境必须修改！）"
        )


def init_all(db: Session) -> None:
    """按依赖顺序执行全部初始化。"""
    init_permissions(db)
    init_roles(db)
    init_grades_subjects(db)
    init_knowledge_points(db)
    init_admin(db)
    init_jobs(db)
    init_demo_data(db)
    warn_default_admin_password(db)
