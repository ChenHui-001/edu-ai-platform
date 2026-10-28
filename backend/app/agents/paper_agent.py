"""5.2 智能组卷 Agent：自然语言需求 → 平衡抽题生成试卷。"""
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents.base import BaseAgent
from app.core.exception import BusinessException
from app.models import KnowledgePoint, Paper, PaperItem, Question
from app.utils.common import now_local

DIFFICULTY_WEIGHT = {"easy": 0.3, "medium": 0.5, "hard": 0.2}
TYPE_LABEL = {
    "single": "单选题", "multiple": "多选题", "judge": "判断题", "blank": "填空题",
    "short": "简答题", "calc": "计算题", "material": "材料分析题", "composition": "作文题",
}


class PaperComposerAgent(BaseAgent):
    name = "paper_composer"
    display_name = "智能组卷智能体"
    description = "理解组卷需求，自动平衡知识点分布与难度结构，生成符合要求的试卷"

    system_prompt = """你是九年义务教育的智能组卷专家。请把用户的自然语言组卷需求解析为结构化参数。

可选值：
- grade_num: 年级序号，整数 1-9（如"七年级"填 7，"初二"填 8），不确定填 0
- subject_name: 学科中文名，如 "数学" / "语文" / "英语" / "物理" / "化学"，
  不确定填空字符串
- total_score: 总分，默认 100
- duration: 建议时长（分钟），默认 60
- difficulty_ratio: 难度分布，形如 {"easy":3,"medium":5,"hard":2}
- type_ratio: 题型分布，形如 {"single":10,"fill":5,"solve":4}，key 可用 single/multiple/judge/blank/short/calc/material/composition
- knowledge_point_ids: 知识点ID数组，空数组表示不限
- knowledge_keywords: 涉及的知识点关键词数组

**不要输出 grade_id / subject_id**：你不知道系统内部的主键，猜出来的 id 会指向
别的年级/学科，导致组卷直接失败。只输出 grade_num 与 subject_name 即可。

只输出 JSON：{"params": {...}, "clarify": null 或 "需要澄清的问题"}
若需求已经清晰，clarify 为 null。"""

    def execute(
        self,
        db: Session,
        user_id: Optional[int] = None,
        request: str = "",
        grade_id: Optional[int] = None,
        subject_id: Optional[int] = None,
        total_score: float = 100,
        difficulty_ratio: Optional[Dict[str, int]] = None,
        type_ratio: Optional[Dict[str, int]] = None,
        knowledge_point_ids: Optional[List[int]] = None,
        paper_name: Optional[str] = None,
        save: bool = False,
        **kwargs,
    ) -> Dict[str, Any]:
        # 1. 解析自然语言需求（补齐结构化参数）
        parsed_params: Dict[str, Any] = {}
        if request:
            r = self.call_llm(f"组卷需求：{request}", db=db, user_id=user_id,
                              biz_type="paper_parse", json_mode=True)
            if r["success"] and r.get("parsed"):
                p = r["parsed"]
                parsed_params = (p.get("params") if isinstance(p, dict) else {}) or {}

        subject_id = subject_id or parsed_params.get("subject_id") or 0
        grade_id = grade_id or parsed_params.get("grade_id") or 0
        total_score = float(parsed_params.get("total_score") or total_score)
        difficulty_ratio = difficulty_ratio or parsed_params.get("difficulty_ratio") or DIFFICULTY_WEIGHT
        type_ratio = type_ratio or parsed_params.get("type_ratio") or {
            "single": 0.5, "blank": 0.2, "short": 0.3,
        }
        kp_ids = knowledge_point_ids or parsed_params.get("knowledge_point_ids") or []

        if not subject_id:
            raise BusinessException("无法识别学科，请指定学科后再组卷")

        # 2. 规则组卷引擎
        plan = self._compose(
            db, grade_id=grade_id, subject_id=subject_id, total_score=total_score,
            difficulty_ratio=difficulty_ratio, type_ratio=type_ratio, kp_ids=kp_ids,
        )
        if not plan["items"]:
            # 3. 无题可用时调用 AI 生成补足
            return self._ai_fill(
                db, user_id=user_id, request=request, grade_id=grade_id, subject_id=subject_id,
                plan=plan, total_score=total_score, paper_name=paper_name, save=save,
                difficulty_ratio=difficulty_ratio,
            )

        # 4. 生成难度分析与知识点覆盖报告
        report = self._build_report(plan, difficulty_ratio)

        paper: Optional[Paper] = None
        if save:
            paper = Paper(
                name=paper_name or f"{self._grade_name(db, grade_id)}智能组卷-{now_local():%Y%m%d%H%M}",
                grade_id=grade_id, subject_id=subject_id,
                total_score=total_score, duration=int(parsed_params.get("duration") or 60),
                difficulty_ratio=str(difficulty_ratio),
                knowledge_coverage=__import__("json").dumps(report["knowledge_coverage"], ensure_ascii=False),
                difficulty_report=__import__("json").dumps(report["difficulty_report"], ensure_ascii=False),
                creator_id=user_id or 1, source="ai",
            )
            db.add(paper)
            db.flush()
            for i, it in enumerate(plan["items"]):
                db.add(
                    PaperItem(
                        paper_id=paper.id, question_id=it["question_id"],
                        sort_order=i + 1, score=it["score"],
                        section_name=it.get("section_name"),
                    )
                )
                q = db.get(Question, it["question_id"])
                if q:
                    q.usage_count += 1
            db.commit()
            db.refresh(paper)

        return {
            "paper": {
                "id": paper.id if paper else None,
                "name": paper.name if paper else (paper_name or "预览试卷"),
                "total_score": total_score,
                "item_count": len(plan["items"]),
                "items": plan["preview"],
            },
            **report,
            "saved": bool(paper),
            "tip": "" if plan["items"] else "",
        }

    # ---------------- 组卷引擎 ----------------
    def _compose(
        self, db: Session, *, grade_id: int, subject_id: int, total_score: float,
        difficulty_ratio: Dict[str, int], type_ratio: Dict[str, int], kp_ids: List[int],
    ) -> Dict[str, Any]:
        """按难度分布与题型分布从题库抽题，并平衡知识点覆盖。"""
        used: set = set()
        selected: List[Dict[str, Any]] = []
        coverage: Dict[str, int] = {}

        total_items = sum(int(v) for v in type_ratio.values()) or 10
        # 每题平均分
        avg = round(total_score / total_items, 1)

        for qtype, qty in type_ratio.items():
            qty = int(qty)
            if qty <= 0:
                continue
            picked = 0
            # 题型 + 难度双维度抽题
            for diff, _w in difficulty_ratio.items():
                need = max(1, round(qty * int(_w) / max(1, sum(difficulty_ratio.values()))))
                stmt = select(Question).where(
                    Question.subject_id == subject_id,
                    Question.type == qtype,
                    Question.difficulty == diff,
                    Question.status == "published",
                )
                if grade_id:
                    stmt = stmt.where(Question.grade_id == grade_id)
                if kp_ids:
                    stmt = stmt.where(Question.knowledge_point_id.in_(kp_ids))
                for q in db.scalars(stmt.limit(need * 3)).all():
                    if picked >= qty:
                        break
                    if q.id in used:
                        continue
                    used.add(q.id)
                    picked += 1
                    kp = db.get(KnowledgePoint, q.knowledge_point_id) if q.knowledge_point_id else None
                    kp_name = kp.name if kp else "综合"
                    coverage[kp_name] = coverage.get(kp_name, 0) + 1
                    selected.append({
                        "question_id": q.id, "score": avg, "difficulty": q.difficulty,
                        "type": q.type, "stem": q.stem, "knowledge_point": kp_name,
                        "section_name": f"一、{TYPE_LABEL.get(qtype, qtype)}（共 {qty} 题，每题 {avg} 分）",
                    })
            # 难度配额不足时放宽难度
            if picked < qty:
                stmt = select(Question).where(
                    Question.subject_id == subject_id,
                    Question.type == qtype,
                    Question.status == "published",
                )
                if grade_id:
                    stmt = stmt.where(Question.grade_id == grade_id)
                for q in db.scalars(stmt.limit(qty * 3)).all():
                    if picked >= qty:
                        break
                    if q.id in used:
                        continue
                    used.add(q.id)
                    picked += 1
                    kp = db.get(KnowledgePoint, q.knowledge_point_id) if q.knowledge_point_id else None
                    kp_name = kp.name if kp else "综合"
                    coverage[kp_name] = coverage.get(kp_name, 0) + 1
                    selected.append({
                        "question_id": q.id, "score": avg, "difficulty": q.difficulty,
                        "type": q.type, "stem": q.stem, "knowledge_point": kp_name,
                        "section_name": f"一、{TYPE_LABEL.get(qtype, qtype)}（共 {qty} 题，每题 {avg} 分）",
                    })

        # 重新编号排序
        total_score_actual = round(sum(i["score"] for i in selected), 1)
        preview = [
            {**i, "sort_order": idx + 1} for idx, i in enumerate(selected)
        ]
        return {"items": preview, "preview": preview, "actual_score": total_score_actual, "coverage": coverage}

    def _build_report(self, plan: Dict[str, Any], ratio: Dict[str, int]) -> Dict[str, Any]:
        """难度分析 + 知识点覆盖报告。"""
        items = plan["items"]
        diff_count: Dict[str, int] = {}
        type_count: Dict[str, int] = {}
        for i in items:
            diff_count[i["difficulty"]] = diff_count.get(i["difficulty"], 0) + 1
            type_count[i["type"]] = type_count.get(i["type"], 0) + 1
        n = len(items) or 1
        return {
            "difficulty_report": {
                "distribution": {k: v for k, v in diff_count.items()},
                "ratio": {k: round(v / n * 100, 1) for k, v in diff_count.items()},
                "target_ratio": {k: round(int(v) / max(1, sum(ratio.values())) * 100, 1) for k, v in ratio.items()},
                "avg_score": round(plan["actual_score"] / n, 2) if n else 0,
            },
            "knowledge_coverage": {
                "points": [{"name": k, "count": v} for k, v in plan["coverage"].items()],
                "total_points": len(plan["coverage"]),
                "balance": self._balance_text(plan["coverage"]),
            },
            "type_distribution": type_count,
        }

    @staticmethod
    def _balance_text(coverage: Dict[str, int]) -> str:
        if not coverage:
            return "暂无知识点覆盖数据"
        vals = list(coverage.values())
        spread = max(vals) - min(vals)
        if spread <= 1:
            return "知识点分布均衡"
        if spread <= 2:
            return "知识点分布基本均衡"
        return "知识点分布不均，建议人工调整部分题目"

    @staticmethod
    def _grade_name(db: Session, grade_id: int) -> str:
        from app.models import Grade
        g = db.get(Grade, grade_id) if grade_id else None
        return g.name if g else "综合"

    # ---------------- AI 补题 ----------------
    def _ai_fill(
        self, db: Session, *, user_id, request, grade_id, subject_id, plan,
        total_score, paper_name, save, difficulty_ratio,
    ) -> Dict[str, Any]:
        """题库不足时调用题库生成 Agent 补足题目。"""
        from app.agents.question_agent import QuestionGeneratorAgent

        need = max(5, 10 - len(plan["items"]))
        gen = QuestionGeneratorAgent()
        res = gen.run(
            db, user_id=user_id, grade_id=grade_id, subject_id=subject_id,
            count=need, difficulty="medium", save=save,
        )
        gen_data = res.get("data") or {}
        questions = gen_data.get("questions", [])
        if not questions:
            return {
                "paper": {"items": [], "item_count": 0},
                "message": "题库中暂无匹配题目，且 AI 生成未成功。请先录入题目或检查模型配置。",
                "difficulty_report": {}, "knowledge_coverage": {},
            }

        preview = [
            {
                "sort_order": i + 1, "stem": q["stem"], "type": q["type"],
                "difficulty": q["difficulty"],
                "score": q.get("score") or round(total_score / len(questions), 1),
                "knowledge_point": "题库复用", "section_name": None,
                "question_id": q.get("id") or q.get("question_id"),
            }
            for i, q in enumerate(questions)
        ]

        # 关键：AI 补题分支同样必须落库。
        # 原实现无论 save 与否都返回 id=None、question_id=None 的纯预览，
        # 前端点「保存」后拿不到任何可用试卷，智能组卷功能形同虚设。
        coverage = {
            "points": [{"name": "题库复用", "count": len(preview)}],
            "total_points": 1,
            "balance": "题库按学科补足，知识点未精确匹配",
        }
        report = {
            "distribution": {"medium": len(preview)},
            "ratio": {"medium": 100.0}, "target_ratio": difficulty_ratio,
        }
        paper = None
        if save:
            paper = Paper(
                name=paper_name
                or f"{self._grade_name(db, grade_id)}智能组卷-{now_local():%Y%m%d%H%M}",
                grade_id=grade_id, subject_id=subject_id,
                total_score=total_score, duration=60,
                difficulty_ratio=__import__("json").dumps(difficulty_ratio, ensure_ascii=False),
                knowledge_coverage=__import__("json").dumps(coverage, ensure_ascii=False),
                difficulty_report=__import__("json").dumps(report, ensure_ascii=False),
                creator_id=user_id or 1, source="ai",
            )
            db.add(paper)
            db.flush()
        for i, q in enumerate(questions):
            qid = q.get("id") or q.get("question_id")
            preview[i]["section_name"] = (
                f"一、{TYPE_LABEL.get(preview[i]['type'], '综合')}题"
            )
            if not qid:
                continue
            db.add(
                PaperItem(
                    paper_id=paper.id, question_id=qid,
                    sort_order=i + 1, score=preview[i]["score"],
                    section_name=preview[i]["section_name"],
                )
            )
            qq = db.get(Question, qid)
            if qq:
                qq.usage_count += 1
            db.commit()
            db.refresh(paper)

        return {
            "paper": {
                "id": paper.id if paper else None,
                "name": paper.name if paper else (paper_name or "AI 生成试卷（待入库）"),
                "total_score": total_score,
                "item_count": len(preview),
                "items": preview,
            },
            "difficulty_report": report,
            "knowledge_coverage": coverage,
            "saved": bool(paper),
            "tip": "题库题目不足，已按学科补足并生成试卷"
                  if paper else "题库题目不足，已补足预览题目（未保存）",
        }
