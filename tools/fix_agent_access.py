# -*- coding: utf-8 -*-
"""AI 智能模块权限修复。

问题（实测确认）：
1. [高] /agent/note-organizer 无 note 归属校验 → 任意用户可读+覆写他人私密笔记
2. [高] /agent/question-generator、/paper-composer、/grading 仅 login 校验
        → 学生可写题库、建试卷、调用批改
3. [中] /agent/study-planner 的 student_id 客户端可控 → 学生可读他人学情生成规划
4. [中] /agent/logs 的 summary/by_agent 未按权限过滤 → 学生可见全站 AI 调用统计
5. [低] /agent/list 的 llm_provider 硬编码 None
"""
import io

f = "backend/app/api/v1/agent.py"
s = io.open(f, encoding="utf-8").read()

# ---- 导入依赖 ----
OLD_IMPORT = "from app.api.deps import get_current_user"
NEW_IMPORT = """from app.api.deps import (
    get_current_student,
    get_current_student_self,
    get_current_teacher,
    get_current_user,
)"""
assert OLD_IMPORT in s, "import"
s = s.replace(OLD_IMPORT, NEW_IMPORT)

# ---- 1) 出题：仅教师及以上 ----
s = s.replace('''def question_generator(
    data: Dict[str, Any] = Body(...), db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):''',
'''def question_generator(
    data: Dict[str, Any] = Body(...), db: Session = Depends(get_db),
    user: User = Depends(get_current_teacher),
):''')

# ---- 2) 组卷：仅教师及以上 ----
s = s.replace('''def paper_composer(
    data: Dict[str, Any] = Body(...), db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):''',
'''def paper_composer(
    data: Dict[str, Any] = Body(...), db: Session = Depends(get_db),
    user: User = Depends(get_current_teacher),
):''')

# ---- 3) 批改：仅教师及以上 ----
s = s.replace('''def agent_grading(
    data: Dict[str, Any] = Body(...), db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):''',
'''def agent_grading(
    data: Dict[str, Any] = Body(...), db: Session = Depends(get_db),
    user: User = Depends(get_current_teacher),
):''')

# ---- 4) study-planner：学生只能给自己 ----
OLD_PLAN = '''def study_planner(
    data: Dict[str, Any] = Body(...), db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    from app.agents.study_agent import StudyPlannerAgent

    res = StudyPlannerAgent().run(
        db, user_id=user.id,
        student_id=data.get("student_id") or user.id,'''
NEW_PLAN = '''def study_planner(
    data: Dict[str, Any] = Body(...), db: Session = Depends(get_db),
    user: User = Depends(get_current_student),
):
    from app.agents.study_agent import StudyPlannerAgent

    # 目标学生：学生身份只能为自己生成；教师/管理员可指定（学情分析场景）。
    # 此前 student_id 完全由客户端决定，学生可传他人 id 读取他人学情。
    is_staff = bool({"teacher", "grade_admin", "sys_admin"} & set(user.role_codes))
    target_sid = user.id
    if is_staff and data.get("student_id"):
        target_sid = int(data["student_id"])

    res = StudyPlannerAgent().run(
        db, user_id=user.id,
        student_id=target_sid,'''
assert OLD_PLAN in s, "study planner"
s = s.replace(OLD_PLAN, NEW_PLAN)

# ---- 5) note-organizer：归属校验 ----
OLD_NOTE = '''def note_organizer(
    data: Dict[str, Any] = Body(...), db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    from app.agents.note_agent import NoteOrganizerAgent

    res = NoteOrganizerAgent().run(
        db, user_id=user.id,
        note_id=data.get("note_id"), content=data.get("content"),
        title=data.get("title"), save=bool(data.get("save", False)),
    )'''
NEW_NOTE = '''def note_organizer(
    data: Dict[str, Any] = Body(...), db: Session = Depends(get_db),
    user: User = Depends(get_current_student),
):
    """笔记整理。

    ⚠️ 安全边界：note_id 必须校验归属。此前直接把客户端传入的 note_id
    交给 Agent，Agent 内部 `db.get(Note, note_id)` 不做归属判断，
    导致任意用户可读取（并 save=True 覆写）他人私密笔记。
    管理员仅允许「读取整理结果」，不允许写回他人笔记。
    """
    from app.agents.note_agent import NoteOrganizerAgent
    from app.models import Note

    note_id = data.get("note_id")
    save = bool(data.get("save", False))
    if note_id:
        note = db.get(Note, note_id)
        if not note:
            raise NotFoundException("笔记不存在")
        owner = note.student_id == user.id
        is_admin = "sys_admin" in user.role_codes
        if not owner:
            if not is_admin:
                raise PermissionException("无权整理他人笔记")
            if save:
                raise PermissionException("管理员不可覆写他人笔记")

    res = NoteOrganizerAgent().run(
        db, user_id=user.id,
        note_id=note_id, content=data.get("content"),
        title=data.get("title"), save=save,
    )'''
assert OLD_NOTE in s, "note organizer"
s = s.replace(OLD_NOTE, NEW_NOTE)

# ---- 6) logs：统计按权限过滤 ----
OLD_LOG = '''    stats = db.execute(
        select(
            func.count(),
            func.avg(AgentCallLog.duration_ms),
            func.sum(AgentCallLog.input_tokens),
            func.sum(AgentCallLog.output_tokens),
        ).select_from(AgentCallLog)
    ).one()

    by_agent = db.execute(
        select(AgentCallLog.agent_name, func.count()).group_by(AgentCallLog.agent_name)
    ).all()'''
NEW_LOG = '''    # 统计必须与明细同权：非管理员只看自己的汇总，
    # 否则 items 只有自己 14 条、summary 却是全站 38 次（实测泄漏）。
    stat_stmt = select(
        func.count(),
        func.avg(AgentCallLog.duration_ms),
        func.sum(AgentCallLog.input_tokens),
        func.sum(AgentCallLog.output_tokens),
    ).select_from(AgentCallLog)
    by_stmt = select(AgentCallLog.agent_name, func.count()).group_by(
        AgentCallLog.agent_name)
    if not is_admin:
        stat_stmt = stat_stmt.where(AgentCallLog.user_id == user.id)
        by_stmt = by_stmt.where(AgentCallLog.user_id == user.id)
    stats = db.execute(stat_stmt).one()
    by_agent = db.execute(by_stmt).all()'''
assert OLD_LOG in s, "logs stats"
s = s.replace(OLD_LOG, NEW_LOG)

# ---- 7) llm_provider 不再是 None ----
OLD_PROV = '''        "llm_enabled": is_available(),
        "llm_provider": None,
    })'''
NEW_PROV = '''        "llm_enabled": is_available(),
        # 此前硬编码 None，前端状态页拿不到实际供应商
        "llm_provider": settings.LLM_PROVIDER if is_available() else None,
    })'''
assert OLD_PROV in s, "llm provider"
s = s.replace(OLD_PROV, NEW_PROV)

# 确保 settings 与异常导入
if "from app.core.config import settings" not in s.split("\n\n")[0]:
    s = s.replace("from app.core.database import get_db",
                  "from app.core.config import settings\nfrom app.core.database import get_db")
s = s.replace("from app.core.exception import BusinessException",
              "from app.core.exception import BusinessException, NotFoundException, PermissionException")

io.open(f, "w", encoding="utf-8", newline="\n").write(s)
print("agent.py 修复完成")
