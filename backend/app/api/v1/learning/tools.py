"""学习中心 - 学习工具集。

涵盖：题目收藏夹、错题变式练习、学生自主组卷、学习目标与每日打卡、
个性化学习路径推荐、知识闪卡。由原 1333 行的 api/v1/grading.py 拆分而来，
路由前缀 /learning 保持不变。
"""
from typing import Any, Dict, Optional

from fastapi import APIRouter, Body, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.exception import BusinessException, NotFoundException
from app.models import (
    KnowledgeMastery, KnowledgePoint, Paper, PaperItem, Question,
    QuestionFavorite, StudyCheckin, StudyGoal, Subject, Task, User,
    WrongQuestion,
)
from app.utils.common import PageParams, dictify, load_json, ok, utcnow

router = APIRouter()

@router.get("/favorites", summary="我的收藏夹")
def list_favorites(
    params: PageParams = Depends(), tag: Optional[str] = None,
    subject_id: Optional[int] = None, keyword: Optional[str] = None,
    db: Session = Depends(get_db), user: User = Depends(get_current_user),
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

    items = []
    for f in rows:
        q = db.get(Question, f.question_id)
        if not q:
            continue
        kp = db.get(KnowledgePoint, q.knowledge_point_id) if q.knowledge_point_id else None
        sub = db.get(Subject, q.subject_id) if q.subject_id else None
        items.append({
            "id": f.id, "question_id": f.question_id, "tag": f.tag,
            "note": f.note, "created_at": dictify(f.created_at),
            "stem": q.stem, "type": q.type, "difficulty": q.difficulty,
            "options": load_json(q.options), "answer": load_json(q.answer),
            "analysis": q.analysis, "score": q.score,
            "subject_name": sub.name if sub else None,
            "knowledge_point_name": kp.name if kp else None,
        })

    # 收集所有标签供前端筛选
    all_tags = list(set(
        f.tag for f in db.scalars(
            select(QuestionFavorite).where(
                QuestionFavorite.user_id == user.id, QuestionFavorite.tag.isnot(None)
            )
        ).all()
    )) if total > 0 else []

    return ok({"items": items, "total": total, "tags": all_tags, "page": params.page})


@router.post("/favorites", summary="收藏题目")
def add_favorite(
    data: Dict[str, Any] = Body(...), db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
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
    fav_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user),
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
    user: User = Depends(get_current_user),
):
    fav = db.scalar(select(QuestionFavorite).where(
        QuestionFavorite.user_id == user.id, QuestionFavorite.question_id == question_id
    ))
    if fav:
        db.delete(fav)
        db.commit()
    return ok(message="已取消收藏")


@router.get("/favorites/check/{question_id}", summary="检查是否已收藏")
def check_favorite(
    question_id: int, db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    fav = db.scalar(select(QuestionFavorite).where(
        QuestionFavorite.user_id == user.id, QuestionFavorite.question_id == question_id
    ))
    return ok({"favorited": fav is not None, "fav_id": fav.id if fav else None,
               "tag": fav.tag if fav else None})


@router.post("/favorites/practice", summary="收藏题目生成专项练习")
def favorites_practice(
    data: Dict[str, Any] = Body(default={}), db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """从收藏的题目中选取，生成一份专项练习卷。"""
    question_ids = data.get("question_ids", [])
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

    paper = Paper(name=f"收藏专项练习 {utcnow():%m-%d}", creator_id=user.id,
                  subject_id=valid[0].subject_id, grade_id=valid[0].grade_id,
                  total_score=sum(q.score for q in valid))
    db.add(paper)
    db.flush()
    for i, q in enumerate(valid, 1):
        db.add(PaperItem(paper_id=paper.id, question_id=q.id, sort_order=i, score=q.score))
    task = Task(title=paper.name, type="practice", paper_id=paper.id,
                creator_id=user.id, total_score=paper.total_score, status="published",
                subject_id=valid[0].subject_id, grade_id=valid[0].grade_id or 0)
    db.add(task)
    db.commit()
    return ok({"task_id": task.id, "paper_id": paper.id, "total": len(valid)},
              message=f"已从 {len(valid)} 道收藏题生成练习")


# ================================================================ P1-1 错题变式练习
@router.post("/wrong-questions/{wid}/variant", summary="错题变式练习（AI 生成同类题）")
def wrong_variant(
    wid: int, db: Session = Depends(get_db), user: User = Depends(get_current_user),
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
            kp = db.get(KnowledgePoint, w.knowledge_point_id) if w.knowledge_point_id else None
            res = agent.execute(
                db, user_id=user.id, subject_id=w.subject_id,
                knowledge_point_id=w.knowledge_point_id,
                question_type=q.type, count=3, difficulty=q.difficulty or "medium",
                save=False,
            )
            ai_questions = (res.get("data") or {}).get("questions", [])
        except Exception:
            ai_questions = []

    # 组合：AI 变式题 + 题库相似题，最多取 5 道
    all_qs = similar[:5]
    used_ids = {q.id for q in all_qs}
    for ai_q in ai_questions[:5]:
        if ai_q.get("id") and ai_q["id"] not in used_ids:
            db_q = db.get(Question, ai_q["id"])
            if db_q and db_q.status == "published":
                all_qs.append(db_q)
                used_ids.add(ai_q["id"])

    if not all_qs:
        raise BusinessException("暂无可用的变式题目，请稍后重试或练习其他错题")

    # 生成练习卷
    paper = Paper(name=f"变式练习-{q.stem[:15]}...", creator_id=user.id,
                  subject_id=w.subject_id, grade_id=q.grade_id,
                  total_score=sum(qq.score for qq in all_qs))
    db.add(paper)
    db.flush()
    for i, qq in enumerate(all_qs, 1):
        db.add(PaperItem(paper_id=paper.id, question_id=qq.id, sort_order=i, score=qq.score))
    task = Task(title=paper.name, type="practice", paper_id=paper.id,
                creator_id=user.id, total_score=paper.total_score, status="published",
                subject_id=w.subject_id, grade_id=q.grade_id or 0)
    db.add(task)
    db.commit()
    return ok({"task_id": task.id, "paper_id": paper.id, "total": len(all_qs),
               "source": "ai" if ai_questions else "bank"},
              message=f"已生成 {len(all_qs)} 道变式练习题")


# ================================================================ P1-2 自主组卷
@router.post("/custom-paper", summary="学生自主组卷")
def create_custom_paper(
    data: Dict[str, Any] = Body(...), db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """学生按知识点/难度/题型自定义练习卷，可命名保存。"""
    name = data.get("name") or f"我的自测卷 {utcnow():%m-%d}"
    subject_id = data.get("subject_id")
    if not subject_id:
        raise BusinessException("请选择学科")

    question_ids = data.get("question_ids", [])
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
        count = min(int(data.get("count", 10)), 30)
        qs = list(db.scalars(stmt.order_by(func.random()).limit(count)).all())

    if not qs:
        raise BusinessException("没有符合条件的题目")

    total_score = sum(q.score for q in qs)
    paper = Paper(name=name, creator_id=user.id, subject_id=subject_id,
                  grade_id=data.get("grade_id", 0), total_score=total_score)
    db.add(paper)
    db.flush()
    for i, q in enumerate(qs, 1):
        db.add(PaperItem(paper_id=paper.id, question_id=q.id, sort_order=i, score=q.score))
    task = Task(title=name, type="practice", paper_id=paper.id,
                creator_id=user.id, total_score=total_score, status="published",
                subject_id=subject_id, grade_id=data.get("grade_id") or qs[0].grade_id or 0)
    db.add(task)
    db.commit()
    return ok({"task_id": task.id, "paper_id": paper.id, "total": len(qs),
               "total_score": total_score},
              message=f"组卷成功，共 {len(qs)} 题")


# ================================================================ P2-1 学习目标与打卡
@router.get("/goals", summary="我的学习目标")
def list_goals(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    goals = db.scalars(select(StudyGoal).where(
        StudyGoal.user_id == user.id, StudyGoal.is_active.is_(True)
    ).order_by(StudyGoal.created_at.desc())).all()
    today = utcnow().strftime("%Y-%m-%d")
    items = []
    for g in goals:
        # 今日打卡状态
        today_checkin = db.scalar(select(StudyCheckin).where(
            StudyCheckin.user_id == user.id, StudyCheckin.goal_id == g.id,
            StudyCheckin.checkin_date == today
        ))
        # 连续天数
        latest = db.scalar(select(StudyCheckin).where(
            StudyCheckin.user_id == user.id, StudyCheckin.goal_id == g.id
        ).order_by(StudyCheckin.checkin_date.desc()))
        items.append({
            "id": g.id, "title": g.title, "target_type": g.target_type,
            "target_value": g.target_value, "unit": g.unit,
            "subject_id": g.subject_id, "start_date": g.start_date,
            "end_date": g.end_date, "is_active": g.is_active,
            "today_checked": today_checkin is not None,
            "today_value": today_checkin.actual_value if today_checkin else 0,
            "streak": latest.streak if latest else 0,
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
    user: User = Depends(get_current_user),
):
    goal = StudyGoal(
        user_id=user.id, title=data.get("title", "每日学习"),
        target_type=data.get("target_type", "daily"),
        target_value=int(data.get("target_value", 10)),
        unit=data.get("unit", "questions"),
        subject_id=data.get("subject_id"),
        start_date=utcnow().strftime("%Y-%m-%d"),
        end_date=data.get("end_date"),
    )
    db.add(goal)
    db.commit()
    return ok(dictify(goal), message="目标已创建")


@router.put("/goals/{goal_id}", summary="更新目标")
def update_goal(
    goal_id: int, data: Dict[str, Any] = Body(...), db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
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
    goal_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user),
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
    user: User = Depends(get_current_user),
):
    g = db.get(StudyGoal, goal_id)
    if not g or g.user_id != user.id:
        raise NotFoundException("目标不存在")
    today = utcnow().strftime("%Y-%m-%d")
    existing = db.scalar(select(StudyCheckin).where(
        StudyCheckin.user_id == user.id, StudyCheckin.goal_id == goal_id,
        StudyCheckin.checkin_date == today
    ))
    actual = int(data.get("actual_value", 0))
    if existing:
        existing.actual_value = max(existing.actual_value, actual)
        db.commit()
        return ok({"streak": existing.streak, "actual_value": existing.actual_value,
                   "is_completed": existing.actual_value >= g.target_value},
                  message="今日已打卡，已更新完成量")
    # 计算连续天数
    yesterday = (utcnow().replace(hour=0) - __import__("datetime").timedelta(days=1)).strftime("%Y-%m-%d")
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
    user: User = Depends(get_current_user),
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
    db: Session = Depends(get_db), user: User = Depends(get_current_user),
):
    """从知识点库生成闪卡：正面知识点名称，背面定义/关键词。"""
    stmt = select(KnowledgePoint).where(
        KnowledgePoint.is_active.is_(True),
        KnowledgePoint.level >= 3,
    )
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

    cards = []
    for kp in all_kps:
        sub = db.get(Subject, kp.subject_id)
        cards.append({
            "id": kp.id, "front": kp.name, "back": kp.description or kp.keywords or kp.name,
            "subject_id": kp.subject_id, "subject_name": sub.name if sub else "",
            "difficulty": kp.difficulty, "keywords": kp.keywords,
            "is_weak": kp.id in weak_kp_ids,
        })
    return ok({"items": cards, "total": len(cards)})
