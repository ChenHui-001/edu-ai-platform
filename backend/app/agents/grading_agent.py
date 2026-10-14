"""5.3 智能批改 Agent：客观题精准判分，主观题语义理解评分。"""
import difflib
import re
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.agents.base import BaseAgent
from app.core.config import settings
from app.models import Question

OBJECTIVE_TYPES = {"single", "multiple", "judge", "blank"}


class GradingAgent(BaseAgent):
    name = "grading_assistant"
    display_name = "智能批改智能体"
    description = "客观题精准判分，主观题语义理解评分，生成个性化批改评语"

    system_prompt = """你是九年义务教育教师，负责批改学生的主观题（简答题、计算题、材料分析题、作文题）。

评分原则：
1. 按采分点给分，只给实际写对的部分得分，不因表述不同扣分。
2. 严格依据题目满分评分，不得超出满分。
3. 评语要具体、有针对性，像老师那样指出优点和不足，不空泛。
4. 错误点要精确定位。

只输出 JSON：
{
  "score": 得分数字,
  "error_points": ["错误点1", "错误点2"],
  "comment": "批改评语",
  "correct_points": ["答对的采分点"],
  "suggestions": ["改进建议"]
}"""

    def execute(
        self,
        db: Session,
        user_id: Optional[int] = None,
        items: Optional[List[Dict[str, Any]]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """批量批改。items: [{question_id, student_answer, full_score}]"""
        items = items or []
        results: List[Dict[str, Any]] = []
        subjective_queue: List[Tuple[Dict[str, Any], Question]] = []

        # 1. 客观题本地精确判分
        for it in items:
            q = db.get(Question, it.get("question_id")) if it.get("question_id") else None
            if q is None:
                results.append({**it, "grader_type": "auto", "is_correct": False,
                                "score": 0.0, "comment": "题目不存在"})
                continue
            if q.type in OBJECTIVE_TYPES:
                res = self._grade_objective(q, it.get("student_answer") or "")
                results.append({
                    "question_id": q.id, "grader_type": "auto",
                    "full_score": it.get("full_score", q.score),
                    "question_type": q.type, **res,
                })
            else:
                subjective_queue.append((it, q))

        # 2. 主观题 AI 批改
        ai_used = False
        for it, q in subjective_queue:
            if not (it.get("student_answer") or "").strip():
                results.append({
                    "question_id": q.id, "grader_type": "auto", "is_correct": False,
                    "score": 0.0, "full_score": it.get("full_score", q.score),
                    "question_type": q.type, "comment": "未作答",
                })
                continue
            ai_res = self._grade_subjective(
                db, q, it["student_answer"], it.get("full_score", q.score), user_id
            )
            if ai_res:
                ai_used = True
                results.append({
                    "question_id": q.id, "grader_type": "ai",
                    "full_score": it.get("full_score", q.score),
                    "question_type": q.type, **ai_res,
                })
            else:
                results.append({
                    "question_id": q.id, "grader_type": "auto", "is_correct": False,
                    "score": 0.0, "full_score": it.get("full_score", q.score),
                    "question_type": q.type,
                    "comment": "待教师手动批改",
                })

        total_full = sum(float(r.get("full_score") or 0) for r in results)
        total_score = sum(float(r.get("score") or 0) for r in results)
        correct = sum(1 for r in results if r.get("is_correct"))

        return {
            "results": results,
            "summary": {
                "total": len(results),
                "objective_count": len(results) - len(subjective_queue),
                "subjective_count": len(subjective_queue),
                "ai_graded": sum(1 for r in results if r.get("grader_type") == "ai"),
                "pending_manual": sum(1 for r in results if r.get("grader_type") == "auto"
                                      and r.get("question_type") not in OBJECTIVE_TYPES),
                "correct_count": correct,
                "accuracy": round(correct / len(results) * 100, 2) if results else 0.0,
                "total_score": round(total_score, 2),
                "full_score": round(total_full, 2),
                "score_rate": round(total_score / total_full * 100, 2) if total_full else 0.0,
            },
            "ai_used": ai_used,
        }

    # ---------------- 客观题 ----------------
    @staticmethod
    def _grade_objective(q: Question, student_answer: str) -> Dict[str, Any]:
        """客观题本地判分（不依赖 LLM，保证性能与准确）。"""
        import json

        sa = (student_answer or "").strip()
        try:
            std = json.loads(q.answer) if q.answer else None
        except json.JSONDecodeError:
            std = q.answer

        def norm(v: Any) -> str:
            s = str(v if v is not None else "").strip().upper()
            # 去掉标点与多余空白
            s = re.sub(r"[、,，\s]", "", s)
            return s

        if isinstance(std, list):
            std_set = {norm(x) for x in std}
            stu_set = {norm(x) for x in re.split(r"[、,，\s]+", sa) if x.strip()}
            is_correct = std_set == stu_set and bool(stu_set)
            score = float(q.score) if is_correct else 0.0
            return {
                "is_correct": is_correct, "score": score,
                "comment": "回答正确" if is_correct else f"正确答案：{'/'.join(sorted(std_set))}",
            }

        if norm(sa) == norm(std) and sa:
            return {"is_correct": True, "score": float(q.score), "comment": "回答正确"}
        return {
            "is_correct": False, "score": 0.0,
            "comment": f"答案错误，正确答案：{std}" if std else "答案错误",
        }

    # ---------------- 主观题 ----------------
    def _grade_subjective(
        self, db: Session, q: Question, student_answer: str, full_score: float, user_id: Optional[int]
    ) -> Optional[Dict[str, Any]]:
        """主观题 AI 批改。"""
        result = self.call_llm(
            f"【题目】{q.stem}\n"
            f"【标准答案】{q.analysis or '无'}\n"
            f"【满分】{full_score}分\n"
            f"【学生答案】{student_answer}\n\n"
            f"请批改这道题，按采分点给分。",
            db=db, user_id=user_id, biz_type="grading",
            biz_id=q.id, json_mode=True,
        )
        if not result["success"]:
            return None
        parsed = result.get("parsed")
        if not isinstance(parsed, dict):
            # JSON 解析失败时用语义相似度兜底
            sim = self._similarity(student_answer, q.analysis or q.stem)
            score = round(full_score * sim, 1)
            return {
                "is_correct": sim >= 0.6,
                "score": score,
                "comment": f"参考得分（语义相似度 {round(sim * 100)}%），请教师复核",
                "error_points": [],
                "grader_type": "ai",
            }

        try:
            score = max(0.0, min(float(parsed.get("score", 0)), float(full_score)))
        except (TypeError, ValueError):
            score = 0.0

        comment = parsed.get("comment") or ""
        errors = parsed.get("error_points") or []
        suggestions = parsed.get("suggestions") or []
        if suggestions:
            comment += "\n改进建议：" + "；".join(str(s) for s in suggestions[:3])

        return {
            "is_correct": score >= float(full_score) * settings.PASS_SCORE / 100,
            "score": score,
            "comment": comment,
            "error_points": errors,
            "grader_type": "ai",
        }

    @staticmethod
    def _similarity(a: str, b: str) -> float:
        """字符级相似度（difflib），作为语义评分的降级方案。"""
        if not a or not b:
            return 0.0
        return difflib.SequenceMatcher(None, a[:500], b[:500]).ratio()
