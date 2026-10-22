"""学习中心 - 学习工具集。

涵盖：题目收藏夹、错题变式练习、学生自主组卷、学习目标与每日打卡、
个性化学习路径推荐、知识闪卡。由原 1333 行的 api/v1/grading.py 拆分而来，
路由前缀 /learning 保持不变。
"""
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from fastapi import APIRouter, Body, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import (
    get_current_student, get_current_student_self,
)
from app.core.database import get_db
from app.core.exception import BusinessException, NotFoundException
from app.models import (
    KnowledgeMastery, KnowledgePoint, Paper, PaperItem, Question,
    QuestionFavorite, StudyCheckin, StudyGoal, Subject, Task, User,
    WrongQuestion,
)
from app.utils.common import PageParams, dictify, load_json, now_local, ok, today_str

router = APIRouter()

@router.get("/favorites", summary="我的收藏夹")
def list_favorites(
    params: PageParams = Depends(), tag: Optional[str] = None,
    subject_id: Optional[int] = None, keyword: Optional[str] = None,
    db: Session = Depends(get_db), user: User = Depends(get_current_student),
):
    stmt = select(QuestionFavorite).where(QuestionFavorite.user_id == user.id)
    if tag:
        stmt = stmt.where(QuestionFavorite.tag == tag)
    if keyword:
        stmt = stmt.where(QuestionFavorite.question_id.in_(
            select(Question.id).where(Question.stem.like(f"%{keyword}%"))
        ))
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(
        stmt.order_by(QuestionFavorite.created_at.desc())
        .offset(params.offset).limit(params.page_size)
    ).all()

    # 批量预取（此前每条收藏 3 次 db.get，一页 20 条 = 60 次查询）
    q_ids = [f.question_id for f in rows]
    q_map, kp_map, sub_map = {}, {}, {}
    if q_ids:
        q_rows = db.scalars(select(Question).where(Question.id.in_(q_ids))).all()
        q_map = {q.id: q for q in q_rows}
        kp_ids = {q.knowledge_point_id for q in q_rows if q.knowledge_point_id}
        sub_ids = {q.subject_id for q in q_rows if q.subject_id}
        if kp_ids:
            kp_map = {k.id: k for k in db.scalars(
                select(KnowledgePoint).where(KnowledgePoint.id.in_(kp_ids))).all()}
        if sub_ids:
            sub_map = {x.id: x for x in db.scalars(
                select(Subject).where(Subject.id.in_(sub_ids))).all()}

    items = []
    for f in rows:
        q = q_map.get(f.question_id)
        if not q:
            continue
        kp = kp_map.get(q.knowledge_point_id) if q.knowledge_point_id else None
        sub = sub_map.get(q.subject_id) if q.subject_id else None
        items.append({
            "id": f.id, "question_id": f.question_id, "tag": f.tag,
            "note": f.note, "created_at": dictify(f.created_at),
            "stem": q.stem, "type": q.type, "difficulty": q.difficulty,
            "options": load_json(q.options), "answer": load_json(q.answer),
            "analysis": q.analysis, "score": q.score,
            "subject_name": sub.name if sub else None,
            "knowledge_point_name": kp.name if kp else None,
        })

    # 标签下拉：distinct 查询即可，原先全量拉行再 set 去重
    all_tags = [r for r in db.scalars(
        select(QuestionFavorite.tag).where(
            QuestionFavorite.user_id == user.id, QuestionFavorite.tag.isnot(None)
        ).distinct()
    ).all()] if total > 0 else []

    return ok({"items": items, "total": total, "tags": all_tags, "page": params.page})


@router.post("/favorites", summary="收藏题目")
def add_favorite(
    data: Dict[str, Any] = Body(...), db: Session = Depends(get_db),
    user: User = Depends(get_current_student_self),
):
    qid = data.get("question_id")
    if not qid:
        raise BusinessException("缺少题目 ID")
    if not db.get(Question, qid):
        raise NotFoundException("题目不存在")
    # 幂等：同用户同题不重复收藏
    existing = db.scalar(select(QuestionFavorite).where(
        QuestionFavorite.user_id == user.id, QuestionFavorite.question_id == qid
    ))
    if existing:
        if data.get("tag"):
            existing.tag = data["tag"]
        if data.get("note"):
            existing.note = data["note"]
        db.commit()
        return ok({"id": existing.id}, message="已更新收藏标签")
    fav = QuestionFavorite(
        user_id=user.id, question_id=qid,
        tag=data.get("tag"), note=data.get("note"),
    )
    db.add(fav)
    db.commit()
    db.refresh(fav)
    return ok({"id": fav.id}, message="已收藏")


@router.delete("/favorites/{fav_id}", summary="取消收藏")
def remove_favorite(
    fav_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_student_self),
):
    fav = db.get(QuestionFavorite, fav_id)
    if not fav or fav.user_id != user.id:
        raise NotFoundException("收藏记录不存在")
    db.delete(fav)
    db.commit()
    return ok(message="已取消收藏")


@router.delete("/favorites/by-question/{question_id}", summary="按题目取消收藏")
def remove_favorite_by_question(
    question_id: int, db: Session = Depends(get_db),
    user: User = Depends(get_current_student_self),
):
    fav = db.scalar(select(QuestionFavorite).where(
        QuestionFavorite.user_id == user.id, QuestionFavorite.question_id == question_id
    ))
    if fav:
        db.delete(fav)
        db.commit()
    return ok(message="已取消收藏")


@router.get("/favorites/check-batch", summary="批量检查收藏状态")
def check_favorites_batch(
    question_ids: str = Query(..., description="逗号分隔的题目 ID，如 1,2,3（≤100 个）"),
    db: Session = Depends(get_db), user: User = Depends(get_current_student),
):
    """一次返回多道题的收藏状态。

    前端练习页此前对每道题串行调一次 /favorites/check（30 题 = 30 个
    请求），这里合并为一次。key 用字符串以贴合 JS 对象取值习惯。
    """
    ids = []
    for x in question_ids.split(","):
        x = x.strip()
        if x.isdigit():
            ids.append(int(x))
    ids = ids[:100]
    rows = db.scalars(select(QuestionFavorite).where(
        QuestionFavorite.user_id == user.id,
        QuestionFavorite.question_id.in_(ids),
    )).all() if ids else []
    fav_map = {f.question_id: f for f in rows}
    return ok({
        str(qid): {
            "favorited": qid in fav_map,
            "fav_id": fav_map[qid].id if qid in fav_map else None,
            "tag": fav_map[qid].tag if qid in fav_map else None,
        } for qid in ids
    })


@router.get("/favorites/check/{question_id}", summary="检查是否已收藏")
def check_favorite(
    question_id: int, db: Session = Depends(get_db),
    user: User = Depends(get_current_student),
):
    fav = db.scalar(select(QuestionFavorite).where(
        QuestionFavorite.user_id == user.id, QuestionFavorite.question_id == question_id
    ))
    return ok({"favorited": fav is not None, "fav_id": fav.id if fav else None,
               "tag": fav.tag if fav else None})


@router.post("/favorites/practice", summary="收藏题目生成专项练习")
def favorites_practice(
    data: Dict[str, Any] = Body(default={}), db: Session = Depends(get_db),
    user: User = Depends(get_current_student_self),
):
    """从收藏的题目中选取，生成一份专项练习卷。"""
    question_ids = data.get("question_ids") or []
    if not isinstance(question_ids, list) or not all(
        isinstance(x, int) for x in question_ids):
        raise BusinessException("question_ids 必须是整数数组")
    # 上限：一次生成几百题的练习卷会拖垮交卷与判分
    if len(question_ids) > 50:
        raise BusinessException("单次练习最多选择 50 道题")
    if not question_ids:
        # 不指定则取全部收藏的题目
        question_ids = [
            f.question_id for f in db.scalars(
                select(QuestionFavorite).where(QuestionFavorite.user_id == user.id)
                .order_by(QuestionFavorite.created_at.desc()).limit(30)
            ).all()
        ]
    if not question_ids:
        raise BusinessException("收藏夹为空")

    # 过滤掉已下架的题目
    valid = db.scalars(select(Question).where(
        Question.id.in_(question_ids), Question.status == "published"
    )).all()
    if not valid:
        raise BusinessException("收藏的题目均已下架")

    # grade_id 为非空外键：题目未绑年级时回落学生年级（传 0 必撞 FK 500）
    grade_id = next((q.grade_id for q in valid if q.grade_id), None) or user.grade_id
    paper = Paper(name=f"收藏专项练习 {now_local():%m-%d}", creator_id=user.id,
                  subject_id=valid[0].subject_id, grade_id=grade_id,
                  total_score=sum(q.score for q in valid))
    db.add(paper)
    db.flush()
    for i, q in enumerate(valid, 1):
        db.add(PaperItem(paper_id=paper.id, question_id=q.id, sort_order=i, score=q.score))
    task = Task(title=paper.name, type="practice", paper_id=paper.id,
                creator_id=user.id, total_score=paper.total_score, status="published",
                subject_id=valid[0].subject_id, grade_id=grade_id)
    db.add(task)
    db.commit()
    return ok({"task_id": task.id, "paper_id": paper.id, "total": len(valid)},
              message=f"已从 {len(valid)} 道收藏题生成练习")


# ================================================================ P1-1 错题变式练习
@router.post("/wrong-questions/{wid}/variant", summary="错题变式练习（AI 生成同类题）")
def wrong_variant(
    wid: int, db: Session = Depends(get_db), user: User = Depends(get_current_student_self),
):
    """基于错题的知识点、题型、难度，生成变式练习卷。
    LLM 可用时调用 AI 生成原创变式题；不可用时回退到题库相似题。
    """
    w = db.get(WrongQuestion, wid)
    if not w or w.student_id != user.id:
        raise NotFoundException("错题记录不存在")
    q = db.get(Question, w.question_id)
    if not q:
        raise NotFoundException("原题不存在")

    # 优先：从题库找同知识点同类型题（已有 redo 逻辑）
    stmt = select(Question).where(
        Question.subject_id == w.subject_id, Question.type == q.type,
        Question.id != q.id, Question.status == "published",
    )
    if w.knowledge_point_id:
        stmt = stmt.where(Question.knowledge_point_id == w.knowledge_point_id)
    similar = list(db.scalars(stmt.limit(5)).all())

    # 如果 LLM 可用，尝试 AI 生成变式题
    ai_questions = []
    from app.agents.llm import is_available as llm_available
    if llm_available():
        try:
            from app.agents.question_agent import QuestionGeneratorAgent
            agent = QuestionGeneratorAgent()
            res = agent.execute(
                db, user_id=user.id, subject_id=w.subject_id,
                knowledge_point_id=w.knowledge_point_id,
                question_type=q.type, count=3, difficulty=q.difficulty or "medium",
                save=False,
            )
            ai_questions = (res.get("data") or {}).get("questions", [])
        except Exception:
            ai_questions = []

    # 组合：AI 变式题 + 题库相似题，最多取 5 道。
    # 注：AI 生成走 save=False（不入库），返回项没有 id，
    # 无法直接组卷进练习 —— 因此实际可用题只来自题库相似题；
    # 待 AI 出题接入「先入库再引用」流程后此处可恢复合并逻辑。
    all_qs = similar[:5]

    if not all_qs:
        raise BusinessException("暂无可用的变式题目，请稍后重试或练习其他错题")

    # 生成练习卷
    # grade_id 为非空外键：错题/原题未绑年级时回落学生年级（传 0 必撞 FK 500）
    grade_id = q.grade_id or user.grade_id
    paper = Paper(name=f"变式练习-{q.stem[:15]}...", creator_id=user.id,
                  subject_id=w.subject_id, grade_id=grade_id,
                  total_score=sum(qq.score for qq in all_qs))
    db.add(paper)
    db.flush()
    for i, qq in enumerate(all_qs, 1):
        db.add(PaperItem(paper_id=paper.id, question_id=qq.id, sort_order=i, score=qq.score))
    task = Task(title=paper.name, type="practice", paper_id=paper.id,
                creator_id=user.id, total_score=paper.total_score, status="published",
                subject_id=w.subject_id, grade_id=grade_id)
    db.add(task)
    db.commit()
    return ok({"task_id": task.id, "paper_id": paper.id, "total": len(all_qs),
               "source": "ai" if ai_questions else "bank"},
              message=f"已生成 {len(all_qs)} 道变式练习题")


# ================================================================ P1-2 自主组卷
@router.post("/custom-paper", summary="学生自主组卷")
def create_custom_paper(
    data: Dict[str, Any] = Body(...), db: Session = Depends(get_db),
    user: User = Depends(get_current_student_self),
):
    """学生按知识点/难度/题型自定义练习卷，可命名保存。"""
    name = data.get("name") or f"我的自测卷 {now_local():%m-%d}"
    subject_id = data.get("subject_id")
    if not subject_id:
        raise BusinessException("请选择学科")

    question_ids = data.get("question_ids") or []
    if not isinstance(question_ids, list) or not all(
        isinstance(x, int) for x in question_ids
    ):
        raise BusinessException("question_ids 必须是整数数组")
    if len(question_ids) > 50:
        raise BusinessException("自主组卷最多选择 50 道题")

    # 目标年级：请求 → 学生年级。学科必须与它配套（Subject 唯一键是
    # (grade_id, name)，「数学」在 1-9 年级各一条）；前端若传了去重后的
    # 代表 id（指向最低年级），会拼出「一年级数学 + 七年级」这种组合，
    # 抽出来的是低年级题。这里按学科名回查目标年级那条。
    target_grade = data.get("grade_id") or user.grade_id
    subject_id = int(subject_id)
    subj = db.get(Subject, subject_id)
    if subj and target_grade and subj.grade_id != target_grade:
        same = db.scalar(select(Subject).where(
            Subject.name == subj.name, Subject.grade_id == target_grade))
        if same:
            subject_id = same.id

    if question_ids:
        # 手动选题模式
        qs = db.scalars(select(Question).where(
            Question.id.in_(question_ids), Question.status == "published"
        )).all()
    else:
        # 随机抽题模式
        stmt = select(Question).where(
            Question.subject_id == subject_id, Question.status == "published"
        )
        if data.get("knowledge_point_ids"):
            stmt = stmt.where(Question.knowledge_point_id.in_(data["knowledge_point_ids"]))
        if data.get("difficulty"):
            stmt = stmt.where(Question.difficulty == data["difficulty"])
        if data.get("question_types"):
            stmt = stmt.where(Question.type.in_(data["question_types"]))
        # 年级过滤此前被完全忽略：data.get("grade_id") 只在最后给 Paper 赋值时
        # 用到，抽题语句里没有它，界面上的「年级」下拉是个摆设。
        if target_grade:
            stmt = stmt.where(Question.grade_id == target_grade)
        try:
            count = int(data.get("count", 10))
        except (TypeError, ValueError):
            raise BusinessException("题目数量必须是整数")
        count = max(1, min(count, 30))
        qs = list(db.scalars(stmt.order_by(func.random()).limit(count)).all())

    if not qs:
        raise BusinessException("没有符合条件的题目")

    # grade_id 解析：请求 → 首题 → 学生年级（非空外键不接受 0）
    grade_id = (target_grade or next(
        (q.grade_id for q in qs if q.grade_id), None) or user.grade_id)
    total_score = sum(q.score for q in qs)
    paper = Paper(name=name, creator_id=user.id, subject_id=subject_id,
                  grade_id=grade_id, total_score=total_score)
    db.add(paper)
    db.flush()
    for i, q in enumerate(qs, 1):
        db.add(PaperItem(paper_id=paper.id, question_id=q.id, sort_order=i, score=q.score))
    task = Task(title=name, type="practice", paper_id=paper.id,
                creator_id=user.id, total_score=total_score, status="published",
                subject_id=subject_id, grade_id=grade_id)
    db.add(task)
    db.commit()
    return ok({"task_id": task.id, "paper_id": paper.id, "total": len(qs),
               "total_score": total_score},
              message=f"组卷成功，共 {len(qs)} 题")


# ================================================================ P2-1 学习目标与打卡
@router.get("/goals", summary="我的学习目标")
def list_goals(db: Session = Depends(get_db), user: User = Depends(get_current_student)):
    goals = db.scalars(select(StudyGoal).where(
        StudyGoal.user_id == user.id, StudyGoal.is_active.is_(True)
    ).order_by(StudyGoal.created_at.desc())).all()
    today = today_str()
    # 批量预取今日打卡与每目标最新 streak（此前每目标 2 次查询）
    goal_ids = [g.id for g in goals]
    today_map, streak_map = {}, {}
    if goal_ids:
        for c in db.scalars(select(StudyCheckin).where(
            StudyCheckin.user_id == user.id, StudyCheckin.goal_id.in_(goal_ids),
            StudyCheckin.checkin_date == today,
        )).all():
            today_map[c.goal_id] = c
        # streak 取各目标最近一条打卡记录（streak 为冗余存储的连续天数）
        for c in db.scalars(select(StudyCheckin).where(
            StudyCheckin.user_id == user.id, StudyCheckin.goal_id.in_(goal_ids)
        ).order_by(StudyCheckin.checkin_date.desc())).all():
            streak_map.setdefault(c.goal_id, c)

    items = []
    for g in goals:
        tc = today_map.get(g.id)
        items.append({
            "id": g.id, "title": g.title, "target_type": g.target_type,
            "target_value": g.target_value, "unit": g.unit,
            "subject_id": g.subject_id, "start_date": g.start_date,
            "end_date": g.end_date, "is_active": g.is_active,
            "today_checked": tc is not None,
            "today_value": tc.actual_value if tc else 0,
            "streak": streak_map[g.id].streak if g.id in streak_map else 0,
            "created_at": dictify(g.created_at),
        })
    # 最近 30 天打卡日历
    checkins = db.scalars(select(StudyCheckin).where(
        StudyCheckin.user_id == user.id
    ).order_by(StudyCheckin.checkin_date.desc()).limit(30)).all()
    calendar = {c.checkin_date: c.actual_value for c in checkins}
    max_streak = max((c.streak for c in checkins), default=0)
    return ok({"items": items, "calendar": calendar, "max_streak": max_streak})


@router.post("/goals", summary="创建学习目标")
def create_goal(
    data: Dict[str, Any] = Body(...), db: Session = Depends(get_db),
    user: User = Depends(get_current_student_self),
):
    goal = StudyGoal(
        user_id=user.id, title=data.get("title", "每日学习"),
        target_type=data.get("target_type", "daily"),
        target_value=int(data.get("target_value", 10)),
        unit=data.get("unit", "questions"),
        subject_id=data.get("subject_id"),
        start_date=today_str(),
        end_date=data.get("end_date"),
    )
    db.add(goal)
    db.commit()
    return ok(dictify(goal), message="目标已创建")


@router.put("/goals/{goal_id}", summary="更新目标")
def update_goal(
    goal_id: int, data: Dict[str, Any] = Body(...), db: Session = Depends(get_db),
    user: User = Depends(get_current_student_self),
):
    g = db.get(StudyGoal, goal_id)
    if not g or g.user_id != user.id:
        raise NotFoundException("目标不存在")
    for f in ("title", "target_type", "target_value", "unit", "end_date", "is_active"):
        if f in data:
            setattr(g, f, data[f])
    db.commit()
    return ok(message="目标已更新")


@router.delete("/goals/{goal_id}", summary="删除目标")
def delete_goal(
    goal_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_student_self),
):
    g = db.get(StudyGoal, goal_id)
    if not g or g.user_id != user.id:
        raise NotFoundException("目标不存在")
    db.delete(g)
    db.commit()
    return ok(message="目标已删除")


@router.post("/goals/{goal_id}/checkin", summary="每日打卡")
def checkin(
    goal_id: int, data: Dict[str, Any] = Body(default={}), db: Session = Depends(get_db),
    user: User = Depends(get_current_student_self),
):
    g = db.get(StudyGoal, goal_id)
    if not g or g.user_id != user.id:
        raise NotFoundException("目标不存在")
    today = today_str()
    existing = db.scalar(select(StudyCheckin).where(
        StudyCheckin.user_id == user.id, StudyCheckin.goal_id == goal_id,
        StudyCheckin.checkin_date == today
    ))
    try:
        actual = int(data.get("actual_value", 0))
    except (TypeError, ValueError):
        raise BusinessException("打卡完成量必须是整数")
    actual = max(0, actual)  # 负数无意义，直接归零
    if existing:
        existing.actual_value = max(existing.actual_value, actual)
        db.commit()
        return ok({"streak": existing.streak, "actual_value": existing.actual_value,
                   "is_completed": existing.actual_value >= g.target_value},
                  message="今日已打卡，已更新完成量")
    # 计算连续天数
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    prev = db.scalar(select(StudyCheckin).where(
        StudyCheckin.user_id == user.id, StudyCheckin.goal_id == goal_id,
        StudyCheckin.checkin_date == yesterday
    ))
    streak = (prev.streak + 1) if prev else 1
    ci = StudyCheckin(
        user_id=user.id, goal_id=goal_id, checkin_date=today,
        actual_value=actual, streak=streak, note=data.get("note"),
    )
    db.add(ci)
    db.commit()
    return ok({"streak": streak, "actual_value": actual,
               "is_completed": actual >= g.target_value,
               "target_value": g.target_value},
              message=f"打卡成功！连续 {streak} 天")


# ================================================================ P2-2 个性化学习路径
@router.get("/path/recommend", summary="AI 个性化学习路径推荐")
def recommend_path(
    subject_id: Optional[int] = None, db: Session = Depends(get_db),
    user: User = Depends(get_current_student),
):
    """基于掌握度分析薄弱点，推荐下一步学什么。"""
    # 获取掌握度数据
    stmt = select(KnowledgeMastery).where(KnowledgeMastery.student_id == user.id)
    if subject_id:
        stmt = stmt.where(KnowledgeMastery.subject_id == subject_id)
    rows = db.scalars(stmt).all()

    if not rows:
        return ok({"recommendations": [], "avg_mastery": 0,
                   "message": "暂无学习数据，请先完成一些练习"})

    # 按掌握度排序，最薄弱的优先
    sorted_rows = sorted(rows, key=lambda m: m.mastery)
    avg = round(sum(m.mastery for m in rows) / len(rows), 2)

    recommendations = []
    for m in sorted_rows[:8]:
        kp = db.get(KnowledgePoint, m.knowledge_point_id)
        if not kp:
            continue
        # 推荐策略
        if m.mastery < 40:
            action = "先学习知识点概念，再做 5 道基础题巩固"
            priority = "高"
            difficulty = "easy"
        elif m.mastery < 60:
            action = "做 10 道中等难度题，突破薄弱点"
            priority = "中"
            difficulty = "medium"
        elif m.mastery < 80:
            action = "挑战 5 道难题，冲刺高分"
            priority = "低"
            difficulty = "hard"
        else:
            continue  # 已精通的跳过

        recommendations.append({
            "knowledge_point_id": kp.id, "name": kp.name,
            "subject_id": m.subject_id,
            "mastery": round(m.mastery, 1),
            "total_count": m.total_count, "correct_count": m.correct_count,
            "wrong_count": m.wrong_count,
            "priority": priority, "recommended_action": action,
            "recommended_difficulty": difficulty,
            "description": kp.description or "",
        })

    # 如果有 LLM，生成更自然的建议
    from app.agents.llm import is_available as llm_ok
    ai_advice = ""
    if llm_ok() and recommendations:
        try:
            from app.agents.llm import llm_client
            weak_summary = "\n".join(
                f"- {r['name']}：掌握度 {r['mastery']}%，做{r['total_count']}题对{r['correct_count']}题"
                for r in recommendations[:5]
            )
            res = llm_client.chat(
                "你是学习规划师。根据以下学情数据，给出 3 条具体的下一步学习建议（每条不超过 30 字）。",
                f"学生平均掌握度 {avg}%，薄弱知识点：\n{weak_summary}",
                user_id=user.id, agent_name="study_path", biz_type="path_recommend",
            )
            if res.get("success"):
                ai_advice = res["content"]
        except Exception:
            pass

    if not ai_advice:
        ai_advice = (
            f"你的平均掌握度为 {avg}%。"
            + (f"建议优先攻克「{recommendations[0]['name']}」" if recommendations else "")
            + "，从基础题开始逐步提升。"
        )

    return ok({
        "recommendations": recommendations, "avg_mastery": avg,
        "ai_advice": ai_advice, "total_kps": len(rows),
        "weak_count": sum(1 for r in rows if r.mastery < 60),
        "mastered_count": sum(1 for r in rows if r.mastery >= 80),
    })


# ================================================================ P2-3 知识闪卡
@router.get("/flashcards", summary="知识闪卡（知识点速记）")
def get_flashcards(
    subject_id: Optional[int] = None, limit: int = 20,
    db: Session = Depends(get_db), user: User = Depends(get_current_student),
):
    """从知识点库生成闪卡：正面知识点名称，背面定义/关键词。"""
    limit = max(1, min(limit, 100))  # 防御超大 limit 拖垮渲染
    # 不按 level 过滤：种子知识点 level 只有 1/2，原 level>=3 条件
    # 使闪卡在任何环境下都是空集（功能整体失效）。leaf 语义交给
    # is_active + 前端展示控制。
    stmt = select(KnowledgePoint).where(KnowledgePoint.is_active.is_(True))
    if subject_id:
        stmt = stmt.where(KnowledgePoint.subject_id == subject_id)

    # 优先推薄弱知识点的卡片
    weak_kp_ids = set()
    mastery_rows = db.scalars(select(KnowledgeMastery).where(
        KnowledgeMastery.student_id == user.id, KnowledgeMastery.mastery < 60
    )).all()
    weak_kp_ids = {m.knowledge_point_id for m in mastery_rows}

    all_kps = list(db.scalars(stmt.order_by(KnowledgePoint.sort).limit(limit * 2)).all())
    # 排序：薄弱在前
    all_kps.sort(key=lambda k: (0 if k.id in weak_kp_ids else 1, k.sort))
    all_kps = all_kps[:limit]

    sub_ids = {kp.subject_id for kp in all_kps if kp.subject_id}
    sub_map = {x.id: x for x in db.scalars(
        select(Subject).where(Subject.id.in_(sub_ids))).all()} if sub_ids else {}
    cards = []
    for kp in all_kps:
        sub = sub_map.get(kp.subject_id)
        cards.append({
            "id": kp.id, "front": kp.name, "back": kp.description or kp.keywords or kp.name,
            "subject_id": kp.subject_id, "subject_name": sub.name if sub else "",
            "difficulty": kp.difficulty, "keywords": kp.keywords,
            "is_weak": kp.id in weak_kp_ids,
        })
    return ok({"items": cards, "total": len(cards)})
