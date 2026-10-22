"""5.4 学习规划 Agent：分析学习数据，生成个性化学习与复习计划。"""
from datetime import timedelta
from typing import Any, Dict, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.agents.base import BaseAgent
from app.core.config import settings
from app.models import (
    Answer, KnowledgeMastery, KnowledgePoint, StudyRecord, Submission,
    WrongQuestion,
)
from app.utils.common import now_local


class StudyPlannerAgent(BaseAgent):
    name = "study_planner"
    display_name = "学习规划智能体"
    description = "分析学生学习数据，定位薄弱知识点，生成个性化学习与复习计划"

    system_prompt = """你是九年义务教育的资深学习规划师，擅长基于学情数据分析薄弱环节并制定提升方案。

要求：
1. 计划必须具体可执行，精确到每天的任务量，不要空泛建议。
2. 优先补最薄弱的知识点，再巩固已有优势。
3. 考虑义务教育阶段学生的认知负荷，每日学习时长控制在合理范围（小学 60-90 分钟，初中 90-120 分钟）。
4. 语气鼓励但务实。

只输出 JSON：
{
  "summary": "学情诊断总结",
  "weak_points": [{"knowledge_point_id": 0, "name": "知识点名", "mastery": 45.0, "reason": "薄弱原因", "priority": "high"}],
  "daily_plan": [{"date": "2026-10-15", "duration": 60, "tasks": [{"type": "practice", "content": "有理数加减法专项练习 20 题", "target": "知识点名"}]}],
  "advice": ["整体提升建议"],
  "review_dates": [{"knowledge_point_id": 0, "name": "知识点名", "dates": ["2026-10-15", "2026-10-16"]}]
}"""

    def execute(
        self,
        db: Session,
        user_id: Optional[int] = None,
        student_id: Optional[int] = None,
        days: int = 7,
        daily_minutes: int = 90,
        **kwargs,
    ) -> Dict[str, Any]:
        student_id = student_id or user_id
        if not student_id:
            return {}

        # 1. 采集学情数据
        analysis = self._analyze(db, student_id)

        # 2. 调用 LLM 生成计划
        result = self.call_llm(
            f"学生学情数据：\n{self._format_analysis(analysis)}\n\n"
            f"请为该学生制定未来 {days} 天的学习计划，每日学习时长约 {daily_minutes} 分钟。",
            db=db, user_id=user_id, biz_type="study_plan", json_mode=True,
        )

        if result["success"] and isinstance(result.get("parsed"), dict):
            plan = result["parsed"]
            plan = self._normalize_plan(plan, analysis, days, daily_minutes)
        else:
            plan = self.fallback(db, student_id=student_id, days=days,
                                 daily_minutes=daily_minutes, analysis=analysis)

        # 3. 落库复习计划（艾宾浩斯节点）
        created = self._persist_review_plan(db, student_id, plan)
        return {
            **plan,
            "stats": {
                "total_questions": analysis["total_questions"],
                "accuracy": analysis["accuracy"],
                "wrong_count": analysis["wrong_count"],
                "mastered_count": analysis["mastered_count"],
                "study_minutes_7d": analysis["study_minutes_7d"],
                "review_plan_created": created,
            },
        }

    # ---------------- 学情分析 ----------------
    def _analyze(self, db: Session, student_id: int) -> Dict[str, Any]:
        """采集学生学情数据。"""
        # 正确率：限定该学生的作答
        sub_ids = select(Submission.id).where(Submission.student_id == student_id)
        correct = db.scalar(
            select(func.count()).select_from(Answer).where(
                Answer.submission_id.in_(sub_ids), Answer.is_correct.is_(True)
            )
        ) or 0
        total_q = db.scalar(
            select(func.count()).select_from(Answer).where(Answer.submission_id.in_(sub_ids))
        ) or 0

        wrong_count = db.scalar(
            select(func.count()).select_from(WrongQuestion).where(
                WrongQuestion.student_id == student_id, WrongQuestion.is_mastered.is_(False)
            )
        ) or 0
        mastered = db.scalar(
            select(func.count()).select_from(WrongQuestion).where(
                WrongQuestion.student_id == student_id, WrongQuestion.is_mastered.is_(True)
            )
        ) or 0

        # 知识点掌握度
        masteries = db.scalars(
            select(KnowledgeMastery).where(KnowledgeMastery.student_id == student_id)
        ).all()
        points = []
        for m in masteries:
            kp = db.get(KnowledgePoint, m.knowledge_point_id)
            if kp:
                points.append({
                    "knowledge_point_id": kp.id, "name": kp.name,
                    "mastery": round(m.mastery, 1), "total_count": m.total_count,
                    "correct_count": m.correct_count, "wrong_count": m.wrong_count,
                })
        points.sort(key=lambda x: x["mastery"])

        # 近 7 天学习时长
        since = (now_local() - timedelta(days=7)).strftime("%Y-%m-%d")
        study_minutes = (db.scalar(
            select(func.coalesce(func.sum(StudyRecord.study_seconds), 0)).where(
                StudyRecord.student_id == student_id, StudyRecord.study_date >= since
            )
        ) or 0) // 60

        # 成绩趋势
        scores = [
            {"task_id": s.task_id, "score": s.score, "created_at": s.created_at}
            for s in db.scalars(
                select(Submission).where(
                    Submission.student_id == student_id, Submission.score.isnot(None)
                ).order_by(Submission.id.desc()).limit(10)
            ).all()
        ]

        return {
            "total_questions": total_q,
            "correct_count": correct,
            "accuracy": round(correct / total_q * 100, 2) if total_q else 0.0,
            "wrong_count": wrong_count,
            "mastered_count": mastered,
            "knowledge_points": points,
            "study_minutes_7d": study_minutes,
            "scores": scores,
        }

    @staticmethod
    def _format_analysis(a: Dict[str, Any]) -> str:
        lines = [
            f"累计做题：{a['total_questions']} 道，正确率 {a['accuracy']}%",
            f"未掌握错题：{a['wrong_count']} 道，已掌握：{a['mastered_count']} 道",
            f"近 7 天学习时长：{a['study_minutes_7d']} 分钟",
        ]
        weak = [p for p in a["knowledge_points"] if p["mastery"] < 70][:8]
        if weak:
            lines.append("薄弱知识点（按掌握度升序）：")
            for p in weak:
                lines.append(
                    f"  - {p['name']}（掌握度 {p['mastery']}%，做题 {p['total_count']} 道，对 {p['correct_count']} 道）"
                )
        else:
            lines.append("暂无明显薄弱知识点")
        return "\n".join(lines)

    @staticmethod
    def _normalize_plan(
        plan: Dict[str, Any], analysis: Dict[str, Any], days: int, daily_minutes: int
    ) -> Dict[str, Any]:
        """校验并补全模型输出。"""
        plan.setdefault("summary", "")
        plan.setdefault("weak_points", [])
        plan.setdefault("advice", [])
        plan.setdefault("review_dates", [])
        daily = plan.get("daily_plan") or []
        if len(daily) < days:
            # 用规则补齐
            weak = analysis["knowledge_points"][:days] or [{"name": "综合复习", "knowledge_point_id": 0}]
            for i in range(len(daily), days):
                p = weak[i % len(weak)]
                date = (now_local() + timedelta(days=i + 1)).strftime("%Y-%m-%d")
                daily.append({
                    "date": date, "duration": daily_minutes,
                    "tasks": [{"type": "practice",
                               "content": f"{p['name']} 专项练习 15-20 题",
                               "target": p["name"]}],
                })
        plan["daily_plan"] = daily[:days]
        return plan

    # ---------------- 规则降级 ----------------
    def fallback(
        self, db: Session, *, student_id: int, days: int = 7,
        daily_minutes: int = 90, analysis: Optional[Dict[str, Any]] = None, **kwargs,
    ) -> Dict[str, Any]:
        """无 LLM 时基于规则的艾宾浩斯复习计划。"""
        analysis = analysis or self._analyze(db, student_id)
        weak = [p for p in analysis["knowledge_points"] if p["mastery"] < 80] or \
               analysis["knowledge_points"][:5] or [{"name": "综合复习", "knowledge_point_id": 0, "mastery": 0}]

        daily_plan, review_dates = [], []
        for i in range(days):
            date = (now_local() + timedelta(days=i + 1)).strftime("%Y-%m-%d")
            p = weak[i % len(weak)]
            tasks = [
                {"type": "review", "content": f"复习「{p['name']}」笔记与公式，5-10 分钟", "target": p["name"]},
                {"type": "practice", "content": f"{p['name']} 专项练习 15 题", "target": p["name"]},
                {"type": "wrong", "content": "重做昨日错题 5 道", "target": "错题本"},
            ]
            daily_plan.append({"date": date, "duration": daily_minutes, "tasks": tasks})
            # 艾宾浩斯间隔
            for stage, interval in enumerate(settings.REVIEW_INTERVALS[: days]):
                d = (now_local() + timedelta(days=interval)).strftime("%Y-%m-%d")
                review_dates.append({
                    "knowledge_point_id": p["knowledge_point_id"], "name": p["name"],
                    "dates": [d], "stage": stage + 1,
                })

        return {
            "summary": (
                f"共做题 {analysis['total_questions']} 道，正确率 {analysis['accuracy']}%。"
                f"未掌握错题 {analysis['wrong_count']} 道，建议优先巩固薄弱知识点。"
            ),
            "weak_points": [
                {"knowledge_point_id": p["knowledge_point_id"], "name": p["name"],
                 "mastery": p["mastery"], "reason": f"掌握度仅 {p['mastery']}%",
                 "priority": "high" if p["mastery"] < 60 else "medium"}
                for p in weak[:5]
            ],
            "daily_plan": daily_plan,
            "advice": [
                "坚持每天完成复习清单，遵循艾宾浩斯遗忘曲线记忆规律",
                "错题要及时标注错因，避免重复犯错",
                "做题后务必查看解析，弄懂每一步",
            ],
            "review_dates": review_dates,
        }

    @staticmethod
    def _persist_review_plan(db: Session, student_id: int, plan: Dict[str, Any]) -> int:
        """将复习计划写入数据库。"""
        from app.models import ReviewPlan, WrongQuestion

        # 关键：把复习节点关联到具体错题。
        # 否则 /learning/review/plans/{id}/complete 里「连续完成 2 轮 → 标记错题已掌握」
        # 的逻辑因 wrong_question_id 恒为 None 而永不生效，错题本无法闭环。
        wrong_by_kp: Dict[int, int] = {}
        for w in db.scalars(
            select(WrongQuestion).where(
                WrongQuestion.student_id == student_id,
                WrongQuestion.is_mastered.is_(False),
                WrongQuestion.knowledge_point_id.isnot(None),
            )
        ).all():
            # 同一知识点只挂最早的一道未掌握错题，避免计划条目重复指向同一题
            wrong_by_kp.setdefault(w.knowledge_point_id, w.id)

        count = 0
        relinked = 0
        for item in plan.get("review_dates", []):
            kp_id = item.get("knowledge_point_id") or 0
            if not kp_id:
                continue
            kp = db.get(KnowledgePoint, kp_id)
            if not kp:
                continue
            for date in item.get("dates", [])[:6]:
                exists = db.scalar(
                    select(ReviewPlan).where(
                        ReviewPlan.student_id == student_id,
                        ReviewPlan.knowledge_point_id == kp_id,
                        ReviewPlan.scheduled_date == date,
                    )
                )
                if exists:
                    # 已存在的计划补挂错题，保证历史数据也能闭环
                    if exists.wrong_question_id is None:
                        exists.wrong_question_id = wrong_by_kp.get(kp_id)
                        relinked += 1
                    continue
                db.add(
                    ReviewPlan(
                        student_id=student_id, knowledge_point_id=kp_id,
                        subject_id=kp.subject_id, scheduled_date=date,
                        stage=item.get("stage", 1),
                        wrong_question_id=wrong_by_kp.get(kp_id),
                    )
                )
                count += 1
        # 注意：即使没有新增（count==0），补挂错题的改动也必须提交，
        # 否则「完成 2 轮 → 错题标掌握」的闭环在存量计划上永远不生效。
        if count or relinked:
            db.commit()
        return count
