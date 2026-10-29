"""初始化种子数据：角色权限、年级学科、知识点、默认管理员、默认定时任务。"""
from typing import Dict, List, Tuple

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logger import get_logger
from app.core.security import hash_password, verify_password
from app.models import (
    Grade, KnowledgePoint, Permission, Role, RolePermission, ScheduledJob, Subject,
    User, UserRole,
)
from app.utils.common import now_local

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
    ("resource:grade:write", "年级维护", "button", None, None, 201),
    ("resource:subject:list", "学科管理", "menu", "/admin/subjects", "Collection", 210),
    ("resource:subject:write", "学科维护", "button", None, None, 211),
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
    ("student:knowledge", "知识资料", "menu", "/student/knowledge", "Reading", 478),

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
            "resource:subject:write",
            "resource:knowledge:write", "resource:class:list", "resource:class:write",
            "question:bank:list", "question:bank:write", "question:bank:audit",
            "question:bank:export",
            "paper:list", "paper:write", "paper:export", "task:list",
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
            "student:knowledge",
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
        # 必须强制改密：出厂口令是公开写在 README/QUICKSTART 里的常量，
        # 而本系统公网可达、承载未成年人真实数据。原实现置 False，意味着
        # 「部署完不改密就一直可用公开口令登入 sys_admin」——等于后门。
        # 置 True 后 deps.get_current_user 会拦下除白名单（改密/资料/登出/
        # 健康检查/文档）外的一切请求，管理员登录后第一件事必须改密。
        must_change_password=True,
    )
    db.add(admin)
    db.flush()
    role = db.scalar(select(Role).where(Role.code == "sys_admin"))
    if role:
        db.add(UserRole(user_id=admin.id, role_id=role.id))
    db.commit()
    logger.info(
        "默认管理员已创建：账号 admin / 密码 Admin@123456"
        "（已标记强制改密，首登必须修改后才能使用其他接口）"
    )


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
    """创建演示用班级、教师、学生，便于快速体验。

    生产部署可通过 SEED_DEMO_DATA=false 关闭，避免空库自动生成
    teacher1/Teacher@123、stu731/Student@123 等已知口令账号。
    """
    from app.models import Class, TeachingAssignment

    if not settings.SEED_DEMO_DATA:
        logger.info("SEED_DEMO_DATA=false，跳过演示数据初始化")
        return
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
    """初始化各年级各学科的知识点树（年级 → 学科 → 单元 → 知识点）。

    V2 起不再播种平铺数据：每个学科按 4 条一组生成「第 N 单元」，
    原知识点作为单元子级，parent_id/path/level 由种子直接维护。
    知识点是 AI 组卷、错题归因、掌握地图的共同基础；空表才播种，
    已有数据（管理员/教师维护或导入）一律不覆盖。
    """
    if db.scalar(select(func.count()).select_from(KnowledgePoint)) or 0:
        return
    grades = {g.grade_num: g for g in db.scalars(select(Grade)).all()}
    subjects = db.scalars(select(Subject)).all()
    sub_map = {(s.grade_id, s.name): s for s in subjects}

    total = 0
    for grade_num, subj_map in KNOWLEDGE_POINTS.items():
        g = grades.get(grade_num)
        if not g:
            continue
        for subj_name, items in subj_map.items():
            s = sub_map.get((g.id, subj_name))
            if not s:
                continue
            # 每组最多 4 个知识点组成一个单元；不足 2 个时补一条综合练习，
            # 保证每个学科至少有「单元 + 2 个知识点」，避免树退化成单链。
            names = list(items)
            if len(names) < 2:
                names.append((f"{subj_name}综合应用", 2, "medium"))
            groups = [names[i:i + 4] for i in range(0, len(names), 4)]
            for gidx, group in enumerate(groups, start=1):
                unit = KnowledgePoint(
                    name=f"{subj_name}·第{gidx}单元",
                    grade_id=g.id, subject_id=s.id, level=1, parent_id=None,
                    term=1, difficulty="medium", sort=gidx * 10,
                    code=f"G{grade_num}-S{s.id}-U{gidx}",
                    description=f"{g.name}{subj_name}第{gidx}单元",
                    status="published", source="seed",
                )
                db.add(unit)
                db.flush()  # 需要 unit.id 作为 path 前缀与子级 parent_id
                unit.path = str(unit.id)
                for i, (name, _level, difficulty) in enumerate(group):
                    child = KnowledgePoint(
                        name=name, grade_id=g.id, subject_id=s.id, level=2,
                        parent_id=unit.id, term=1, difficulty=difficulty,
                        sort=i, code=f"G{grade_num}-S{s.id}-U{gidx}-K{i + 1}",
                        description=f"{g.name}{subj_name}「{name}」知识点",
                        keywords=name, status="published", source="seed",
                    )
                    db.add(child)
                    db.flush()
                    child.path = f"{unit.path}/{child.id}"
                    total += 1
                total += 1
    if total:
        db.commit()
        logger.info(f"知识点树初始化完成（{total} 个节点，含单元）")


def _sys_admin_candidates(db: Session) -> List[User]:
    """找出所有**事实上的**系统管理员（identity 或角色任一命中）。

    为什么不能只查 `username == "admin"`：出厂账号叫 `admin`，但真实部署
    里的超级管理员往往改过名（如生产库的 `sysadmin`），`admin` 只是另一个
    账号。只按 username 判会漏掉真正的超级管理员 —— 而漏掉的那个恰恰是
    风险最高的一个。判据因此用"权限归属"而不是"账号名"。
    """
    admin_role_ids = select(Role.id).where(Role.code == "sys_admin")
    by_role = select(UserRole.user_id).where(UserRole.role_id.in_(admin_role_ids))
    stmt = select(User).where(
        (User.identity == "sys_admin") | User.id.in_(by_role)
    ).order_by(User.id)
    return list(db.scalars(stmt).all())


def _log_admin_default_password(db: Session, users: List[User], auto_fixed: int) -> None:
    """按 DEBUG 分级记录「超级管理员仍在用出厂口令」这一事件。

    - DEBUG=True（本地体验）：`logger.warning`，只提醒。本地库普遍是
      `Admin@123456`，写 ErrorLog 只会把后台错误日志页刷成噪音。
    - DEBUG=False（生产）：`logger.error` **并写一条 ErrorLog**，让管理员
      能在后台「错误日志」页看到，而不是只沉在容器日志里 —— 容器日志通常
      没人看，等于没告警。

    幂等由 `_upsert_error_log` 保证：每次启动都会走到这里，若直接 `db.add`
    则每天重启 N 次就堆 N 条重复记录。

    **本函数自身保证不抛异常。** 它的本职就是"安全告警"：如果它因为写库
    失败而抛出去，调用方看到的是 `种子数据初始化失败: <db error>` ——
    一条指向错误方向的诊断，而真正的安全告警彻底丢失。告警机制不能因为
    告警通道坏了就静默消失，所以 DB 通道失败时降级到日志通道
    （日志与 DB 互为备份，DB 坏了至少日志还在）。
    """
    names = "、".join(u.username for u in users)
    msg = (
        f"安全告警：{len(users)} 个超级管理员账号仍在使用公开的出厂口令 "
        f"Admin@123456（账号：{names}）。该口令公开写在 README/QUICKSTART 中，"
        f"任何知道文档的人都能以 sys_admin 身份登入。"
    )
    if auto_fixed:
        msg += f"本次启动已自动为其中 {auto_fixed} 个账号标记「首次登录强制改密」。"
    msg += "请立即登录修改密码。"

    if settings.DEBUG:
        logger.warning(msg)
        return
    # 先走日志通道：它一定成功，且即使下面落库失败，告警内容也已经留痕。
    logger.error(msg)
    try:
        _upsert_error_log(
            db,
            module="init_db",
            path="/startup/enforce_default_admin_password",
            message=msg,
        )
    except Exception as exc:  # noqa: BLE001 告警落库失败不能打断启动，降级到日志
        logger.error("安全告警落库失败（已降级为日志输出）：{}", exc)
        # 必须 rollback：`_upsert_error_log` 内部自己 commit，失败后 session
        # 可能停在不可用状态。不收拾干净的话，调用方复用这个 session 会继续
        # 报 `PendingRollbackError` —— 把局部故障放大成整个 session 报废。
        try:
            db.rollback()
        except Exception:  # noqa: BLE001
            pass


def _upsert_error_log(db: Session, *, module: str, path: str,
                      message: str, level: str = "ERROR") -> None:
    """写入或刷新一条 ErrorLog（同 module+path 只保留一条，覆盖内容）。

    用固定 `path` 作为逻辑主键做幂等：重启 N 次也只留最新的一条，
    不会把「错误日志」页刷爆。
    """
    from app.models import ErrorLog

    row = db.scalar(
        select(ErrorLog).where(ErrorLog.module == module, ErrorLog.path == path)
        .order_by(ErrorLog.id.desc())
    )
    if row is None:
        db.add(ErrorLog(level=level, module=module, path=path, message=message))
    else:
        row.level = level
        row.message = message
        row.created_at = now_local()
    db.commit()


def enforce_default_admin_password(db: Session) -> int:
    """把「仍在用出厂口令」的超级管理员标记为必须改密，返回处置账号数。

    ## 这个函数修的是一处「新库已修、存量库未修」的不一致

    `init_admin`（本文件 :379）创建**新**管理员时已置
    `must_change_password=True`，注释写明了理由：出厂口令 `Admin@123456`
    公开写在 README/QUICKSTART 里，而本系统公网可达、承载未成年人真实数据。
    但那只覆盖"空库首次初始化"这一条路径。**存量库/老部署**不走 `init_admin`
    （它开头就 `return`），于是同一个风险在存量库里完好无损：
    admin 仍是 `Admin@123456` 且 `must_change_password=False`，
    可以永久用公开口令登入 sys_admin。原 `warn_default_admin_password`
    只打一行 warning、不改变任何行为，等于只把风险写进没人看的日志。

    ## 为什么现在可以真的处置（原注释的顾虑已不成立）

    原实现不敢置 True，理由是"会把存量本地体验环境与自动化测试全部锁死"。
    这个理由**已经过期**：

    - 干预点是精确的：`MUST_CHANGE_PASSWORD_ENFORCED` 默认 true，
      被标记的账号下次登录会被 `deps` 拦到 `/auth/password`，
      `deps._FORCE_PWD_WHITELIST` 含 `/api/v1/auth/password` 与
      `/api/v1/auth/profile`，改密闭环本身不被拦，不会锁死。
    - `auth_service.change_password` 现在**明确拒绝 new == old**
      （见该函数「新密码不能与原密码相同」）。这意味着被标记的账号
      必须真正换成一个新口令才能继续，出厂口令不会被"改回自己"绕过 ——
      这正是本函数敢直接置 True 的前提。
    - 前端闭环存在：`Login.vue` 在 `must_change_password` 为真时跳
      `/profile`，`Profile.vue` 有改密警示条优先展示。

    ⚠️ 维护提示：上述两条是**代码级约束**，改动
    `_FORCE_PWD_WHITELIST` 或撤销「拒绝 old==new」都会让本函数的
    处置变成把用户锁在门外。改那两处前先回来读这段。

    ## 关键约束：绝不误伤已改密的账号

    只有 `verify_password("Admin@123456", user.password)` 命中才处置。
    已经改过密码的账号口令不匹配，`must_change_password` 保持原值 ——
    否则就是把正常用户锁在门外。同理，已经是 True 的不重复 commit。
    """
    users = _sys_admin_candidates(db)
    offenders = [u for u in users if verify_password("Admin@123456", u.password)]

    auto_fixed = 0
    for user in offenders:
        if not user.must_change_password:
            user.must_change_password = True
            auto_fixed += 1
    # commit 自身也必须护住：这是收尾步骤，一个 commit 失败（锁超时、
    # 磁盘满）不该让整个启动链炸掉。失败就回滚 —— 下一轮启动会重试，
    # 语义上退化成原 warn 版（只告警不处置），不是更糟。
    if auto_fixed:
        try:
            db.commit()
        except Exception as exc:  # noqa: BLE001  收尾步骤失败不阻断启动
            logger.error("标记强制改密失败（已回滚，下次启动重试）：{}", exc)
            try:
                db.rollback()
            except Exception:  # noqa: BLE001
                pass
            auto_fixed = 0
        else:
            # 注意：项目 logger 是 **Loguru**（app/core/logger.get_logger），
            # 占位符是 `{}` 而不是 stdlib logging 的 `%s`。用 `%s` 会把字面量
            # "%s" 打进日志（已实测踩到），看起来像模板没渲染。
            logger.warning(
                "已将 {} 个仍在使用出厂口令 Admin@123456 的超级管理员标记为强制改密：{}",
                auto_fixed, "、".join(u.username for u in offenders),
            )

    # 告警/落库那步单独护住。`_log_admin_default_password` 里的 ErrorLog 写入
    # 依赖 `sys_error_log` 表；如果库结构异常或表被删，这里抛出去会被
    # `main.py` 启动流程的 try/except 吞掉 —— 但那是**整个 init_all** 的兜底，
    # 而本函数位于 init_all 的最末一步，吞掉只影响"少一条告警"。
    # 真正的理由是：告警是观测手段，绝不能成为启动失败的原因。
    if offenders:
        try:
            _log_admin_default_password(db, offenders, auto_fixed)
        except Exception as exc:  # noqa: BLE001  告警失败降级为日志
            logger.error("记录默认口令安全告警失败（已降级）：{}", exc)
            try:
                db.rollback()
            except Exception:  # noqa: BLE001
                pass
    return auto_fixed


def init_all(db: Session) -> None:
    """按依赖顺序执行全部初始化。"""
    init_permissions(db)
    init_roles(db)
    init_grades_subjects(db)
    init_knowledge_points(db)
    # level3 考点层：必须在 level1/2 播完后再补（依赖父章节已存在）。
    # 单独一步而不是塞进 init_knowledge_points，是因为它的幂等策略不同：
    # 前者「空表才播」，后者「逐条比对、只补缺」，存量库升级也能被补齐。
    try:
        from app.services.knowledge_level3_seed import seed_knowledge_level3
        seed_knowledge_level3(db)
    except Exception as exc:  # noqa: BLE001  播种失败不能阻断启动
        logger.warning(f"知识点 level3 播种失败（不影响启动）：{exc}")
    init_admin(db)
    init_jobs(db)
    init_exam_standards(db)
    init_demo_data(db)
    enforce_default_admin_password(db)


def init_exam_standards(db: Session) -> None:
    """播种湖北命题标准（幂等，只播一次）。

    放在 init_knowledge_points 之后、init_demo_data 之前：标准本身不依赖
    知识点，但演示数据里的试卷可能引用标准，顺序上不能颠倒。
    管理员之后在后台改的标准**不会被后续升级覆盖**——播种函数有标记位。
    """
    from app.services.exam_standard_seed import seed_exam_standards

    result = seed_exam_standards(db)
    if result.get("errors"):
        # 占位符用 `{}`：本模块 logger 是 Loguru，`%s` 会被原样打进日志、
        # 参数静默丢弃（与 llm.py 同一处坑）。
        logger.warning("命题标准播种存在校验失败项：{}", result["errors"])
