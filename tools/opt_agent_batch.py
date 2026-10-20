# -*- coding: utf-8 -*-
"""AI 模块 5 项优化（后端）。

1. LLM max_tokens 默认 4096 → 2048（输出 token 是主要耗时来源）
2. 按用户限流（LLM 类接口每分钟 N 次）
3. /agent/chat 的 student_id 按身份取值（教师可指定，学生强制自己）
4. Agent 写库（save=True）记录 OperationLog 审计
5. 慢调用告警日志（>20s 记 warning，便于运维定位）
"""
import io

# ============================================================
# 1) max_tokens 默认值
# ============================================================
f = "backend/app/core/config.py"
s = io.open(f, encoding="utf-8").read()
OLD = "    LLM_MAX_TOKENS: int = 4096"
NEW = """    # 输出 token 是 LLM 耗时的主要来源：4096 会让单次调用接近 60s 超时边界。
    # 实测出题 5 题 / 笔记整理 / 组卷等任务输出均在 2k token 以内，
    # 故默认调整为 2048（可通过系统配置 llm_max_tokens 覆盖）。
    LLM_MAX_TOKENS: int = 2048"""
assert OLD in s, "max_tokens"
s = s.replace(OLD, NEW)

# 限流配置
if "AGENT_RATE_LIMIT_PER_MIN" not in s:
    s = s.replace("    LLM_MAX_TOKENS: int = 2048",
                  """    LLM_MAX_TOKENS: int = 2048
    # AI 接口按用户限流（每分钟），防止高频触发生成刷 token
    AGENT_RATE_LIMIT_PER_MIN: int = 12""")
io.open(f, "w", encoding="utf-8", newline="\n").write(s)
print("[1] max_tokens → 2048 + 限流配置")

# ============================================================
# 2) 限流实现（进程内滑动窗口）
# ============================================================
rl = '''# -*- coding: utf-8 -*-
"""AI 接口轻量限流（进程内固定窗口）。

部署形态是单机 SQLite，不引入 Redis：按 user_id 维护每分钟计数即可。
多实例部署时需替换为共享存储（Redis / DB），否则限流按实例独立生效。
"""
import threading
import time
from typing import Dict, Tuple

from app.core.config import settings
from app.core.exception import BusinessException

_lock = threading.Lock()
# {user_id: (window_start_epoch_minute, count)}
_buckets: Dict[int, Tuple[int, int]] = {}


def check_agent_rate(user_id: int, cost: int = 1) -> None:
    """校验并累加调用次数；超限抛 BusinessException。

    只在会触发 LLM 的接口上调用（出题/组卷/批改/规划/答疑/整理/对话），
    纯查询接口不限流。
    """
    limit = max(1, int(settings.AGENT_RATE_LIMIT_PER_MIN or 12))
    minute = int(time.time() // 60)
    with _lock:
        start, count = _buckets.get(user_id, (minute, 0))
        if start != minute:
            start, count = minute, 0
        count += cost
        _buckets[user_id] = (start, count)
        # 避免字典无限增长：条目超过 5000 时清理过期窗口
        if len(_buckets) > 5000:
            for uid in [u for u, (st, _) in _buckets.items() if st != minute]:
                _buckets.pop(uid, None)
    if count > limit:
        raise BusinessException(
            f"AI 调用过于频繁（每分钟上限 {limit} 次），请稍后再试")
'''
io.open("backend/app/core/rate_limit.py", "w", encoding="utf-8", newline="\n").write(rl)
print("[2] rate_limit.py 新建")

# ============================================================
# 3-5) agent.py：限流 + chat student_id + 写库审计 + 慢调用告警
# ============================================================
f2 = "backend/app/api/v1/agent.py"
s2 = io.open(f2, encoding="utf-8").read()

# 导入
s2 = s2.replace("from app.core.config import settings",
                "from app.core.config import settings\nfrom app.core.rate_limit import check_agent_rate")

# 慢调用阈值常量
s2 = s2.replace("router = APIRouter()",
'''router = APIRouter()

# 单次 Agent 调用超过该耗时记 warning，便于运维定位模型变慢/网络抖动
SLOW_CALL_MS = 20_000


def _audit_write(db: Session, user: User, action: str, detail: str) -> None:
    """Agent 写库审计：save=True 属于「AI 直接改数据」的高风险操作。"""
    try:
        from app.models import OperationLog

        db.add(OperationLog(
            user_id=user.id, username=user.username,
            module="AI智能", action=action, method="POST",
            path="/api/v1/agent", params=detail[:1000], status="success",
        ))
        db.commit()
    except Exception:  # noqa: BLE001
        db.rollback()


def _warn_if_slow(res: dict, agent: str) -> None:
    ms = (res or {}).get("duration_ms") or 0
    if ms >= SLOW_CALL_MS:
        logger.warning("Agent %s 调用耗时 %.1fs（阈值 %.0fs）",
                       agent, ms / 1000, SLOW_CALL_MS / 1000)''')

# logger 导入
if "logger = logging.getLogger" not in s2:
    s2 = s2.replace("from app.core.rate_limit import check_agent_rate",
                    "from app.core.rate_limit import check_agent_rate\nimport logging\n\nlogger = logging.getLogger(__name__)")

# ---- chat：限流 + student_id 按身份 ----
OLD_CHAT = '''    request = data.get("message") or data.get("request")
    if not request:
        raise BusinessException("请输入你的需求")

    orch = get_orchestrator()
    result = orch.run(
        db, user_id=user.id, request=request,
        args={
            "grade_id": data.get("grade_id"), "subject_id": data.get("subject_id"),
            "student_id": user.id,
        },
    )'''
NEW_CHAT = '''    request = data.get("message") or data.get("request")
    if not request:
        raise BusinessException("请输入你的需求")
    check_agent_rate(user.id)

    # student_id 语义：学生只能是自己；教师/管理员可指定目标学生
    # （此前恒为调用者，教师说「给张三出题」会用到教师自己的学情上下文）
    is_staff = bool({"teacher", "grade_admin", "sys_admin"} & set(user.role_codes))
    target_sid = int(data.get("student_id")) if (
        is_staff and data.get("student_id")) else user.id

    orch = get_orchestrator()
    result = orch.run(
        db, user_id=user.id, request=request,
        args={
            "grade_id": data.get("grade_id"), "subject_id": data.get("subject_id"),
            "student_id": target_sid,
        },
    )'''
assert OLD_CHAT in s2, "chat"
s2 = s2.replace(OLD_CHAT, NEW_CHAT)

# chat 兜底 tutor 也用 target_sid
s2 = s2.replace('''            grade_id=data.get("grade_id"), subject_id=data.get("subject_id"),
            student_id=user.id,
        )
        result["data"] = r.get("data")''',
'''            grade_id=data.get("grade_id"), subject_id=data.get("subject_id"),
            student_id=target_sid,
        )
        result["data"] = r.get("data")''')

# ---- question-generator：限流 + 写库审计 ----
OLD_Q = '''    from app.agents.question_agent import QuestionGeneratorAgent

    res = QuestionGeneratorAgent().run(
        db, user_id=user.id,
        grade_id=data.get("grade_id"), subject_id=int(data.get("subject_id", 0)),
        knowledge_point_id=data.get("knowledge_point_id"),
        question_type=data.get("type", "single"),
        count=int(data.get("count", 5)),
        difficulty=data.get("difficulty", "medium"),
        save=bool(data.get("save", False)),
    )'''
NEW_Q = '''    from app.agents.question_agent import QuestionGeneratorAgent

    check_agent_rate(user.id)
    res = QuestionGeneratorAgent().run(
        db, user_id=user.id,
        grade_id=data.get("grade_id"), subject_id=int(data.get("subject_id", 0)),
        knowledge_point_id=data.get("knowledge_point_id"),
        question_type=data.get("type", "single"),
        count=int(data.get("count", 5)),
        difficulty=data.get("difficulty", "medium"),
        save=bool(data.get("save", False)),
    )
    _warn_if_slow(res, "question_generator")
    if data.get("save") and res.get("success"):
        _audit_write(db, user, "AI 生成题目入库",
                     f"subject={data.get('subject_id')} count={data.get('count', 5)} "
                     f"saved={(res.get('data') or {}).get('saved')}")'''
assert OLD_Q in s2, "question"
s2 = s2.replace(OLD_Q, NEW_Q)

# ---- paper-composer ----
OLD_P = '''    from app.agents.paper_agent import PaperComposerAgent

    res = PaperComposerAgent().run('''
NEW_P = '''    from app.agents.paper_agent import PaperComposerAgent

    check_agent_rate(user.id)
    res = PaperComposerAgent().run('''
assert OLD_P in s2, "paper"
s2 = s2.replace(OLD_P, NEW_P)
s2 = s2.replace('''    if not res.get("success"):
        return fail(res.get("message", "组卷失败"))
    return ok(res.get("data"), message=res.get("message", "组卷完成"))''',
'''    _warn_if_slow(res, "paper_composer")
    if not res.get("success"):
        return fail(res.get("message", "组卷失败"))
    if data.get("save"):
        _audit_write(db, user, "AI 组卷入库",
                     f"subject={data.get('subject_id')} "
                     f"paper_id={(res.get('data') or {}).get('paper_id')}")
    return ok(res.get("data"), message=res.get("message", "组卷完成"))''')

# ---- grading ----
s2 = s2.replace('''    from app.agents.grading_agent import GradingAgent

    res = GradingAgent().run(db, user_id=user.id, items=data.get("items", []))''',
'''    from app.agents.grading_agent import GradingAgent

    check_agent_rate(user.id)
    res = GradingAgent().run(db, user_id=user.id, items=data.get("items", []))
    _warn_if_slow(res, "grading")''')

# ---- study-planner ----
s2 = s2.replace('''    res = StudyPlannerAgent().run(
        db, user_id=user.id,
        student_id=target_sid,''',
'''    check_agent_rate(user.id)
    res = StudyPlannerAgent().run(
        db, user_id=user.id,
        student_id=target_sid,''')
s2 = s2.replace('''    if not res.get("success"):
        return fail(res.get("message", "学习规划失败"))''',
'''    _warn_if_slow(res, "study_planner")
    if not res.get("success"):
        return fail(res.get("message", "学习规划失败"))''')

# ---- note-organizer：限流 + 审计 ----
s2 = s2.replace('''    res = NoteOrganizerAgent().run(
        db, user_id=user.id,
        note_id=note_id, content=data.get("content"),
        title=data.get("title"), save=save,
    )''',
'''    check_agent_rate(user.id)
    res = NoteOrganizerAgent().run(
        db, user_id=user.id,
        note_id=note_id, content=data.get("content"),
        title=data.get("title"), save=save,
    )
    _warn_if_slow(res, "note_organizer")
    if save and res.get("success"):
        _audit_write(db, user, "AI 整理笔记写回", f"note_id={note_id}")''')

# ---- tutor：限流 ----
s2 = s2.replace('''    from app.agents.tutor_agent import TutorAgent
''',
'''    from app.agents.tutor_agent import TutorAgent

    check_agent_rate(user.id)
''', 1)

io.open(f2, "w", encoding="utf-8", newline="\n").write(s2)
print("[3][4][5] agent.py 完成")
