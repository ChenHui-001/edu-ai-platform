"""5.3 智能批改 Agent：客观题精准判分，主观题语义理解评分。"""
import difflib
import re
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents.base import BaseAgent
from app.core.config import settings
from app.models import Question
from app.utils.answer import answers_match, normalize_answer

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

        # 一次性把本题涉及的题目全部取出。
        # 原来在循环里 db.get(Question, ...)，22 道题的练习就是 22 次查询；
        # 交卷是学生端最热的路径，串行 N+1 会直接放大大卷面的响应时间
        # （实测 22 题交卷 24s，其中主观题 LLM 往返占大头，查询也贡献了一部分）。
        qids = [it.get("question_id") for it in items if it.get("question_id")]
        qmap: Dict[int, Question] = {}
        if qids:
            qmap = {q.id: q for q in db.scalars(
                select(Question).where(Question.id.in_(set(qids)))).all()}

        # 1. 客观题本地精确判分
        for it in items:
            q = qmap.get(it.get("question_id")) if it.get("question_id") else None
            if q is None:
                results.append({**it, "grader_type": "auto", "is_correct": False,
                                "score": 0.0, "comment": "题目不存在"})
                continue
            if q.type in OBJECTIVE_TYPES:
                fs = it.get("full_score", q.score)
                res = self._grade_objective(q, it.get("student_answer"), full_score=fs)
                results.append({
                    "question_id": q.id, "grader_type": "auto",
                    "full_score": fs,
                    "question_type": q.type,
                    "student_answer": it.get("student_answer"),
                    **res,
                })
            else:
                subjective_queue.append((it, q))

        # 2. 主观题 AI 批改
        # 串行调用的代价：评分一次 LLM 往返 1.5~7s，6 道简答题就是 9~42s，
        # 交卷接口直接被拖到前端 30s 超时（实测 32 题卷子 116s）。
        # 改为**并发**：主观题之间互不依赖，用线程池同时发出。
        # 注意不能共用一个 Session（SQLAlchemy Session 非线程安全），
        # 所以并发只做「纯 LLM 计算」，结果回到主线程再写库。
        ai_used = False
        graded: Dict[int, Optional[Dict[str, Any]]] = {}   # q.id -> ai_res
        blanks: Dict[int, str] = {}                        # q.id -> 未作答

        pending: List[Tuple[Dict[str, Any], Question, str]] = []
        for it, q in subjective_queue:
            raw_answer = it.get("student_answer")
            # 主观题作答可能是 list（异常提交），统一转字符串再判空
            if isinstance(raw_answer, (list, tuple, set)):
                raw_answer = " ".join(str(x) for x in raw_answer)
            raw_answer = (raw_answer or "").strip()
            if not raw_answer:
                blanks[q.id] = "未作答"
                continue
            pending.append((it, q, raw_answer))

        if pending:
            graded = self._grade_subjective_batch(db, pending, user_id)
            ai_used = any(v for v in graded.values())

        for it, q in subjective_queue:
            fs = it.get("full_score", q.score)
            if q.id in blanks:
                results.append({
                    "question_id": q.id, "grader_type": "auto", "is_correct": False,
                    "score": 0.0, "full_score": fs,
                    "question_type": q.type, "comment": blanks[q.id],
                    "student_answer": it.get("student_answer"),
                })
                continue
            ai_res = graded.get(q.id)
            if ai_res:
                results.append({
                    "question_id": q.id, "grader_type": "ai",
                    "full_score": fs,
                    "question_type": q.type,
                    "student_answer": it.get("student_answer"),
                    **ai_res,
                })
            else:
                results.append({
                    "question_id": q.id, "grader_type": "auto", "is_correct": False,
                    "score": 0.0, "full_score": fs,
                    "question_type": q.type,
                    "comment": "待教师手动批改",
                    "student_answer": it.get("student_answer"),
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
    def _norm_answer_set(value: Any) -> set:
        """把学生/标准答案统一成无标点的选项集合。

        多选题的作答在前端是数组（["A","C"]），但历史数据、导入题库或
        手动调用时也可能是 "A,C" 这类字符串，必须双向归一化后再比较，
        否则 list 没有 .strip() 会直接抛 AttributeError 导致整场交卷判分为空。
        """
        def norm(v: Any) -> str:
            s = str(v if v is not None else "").strip().upper()
            return re.sub(r"[、,，\s]", "", s)

        if value is None:
            return set()
        if isinstance(value, (list, tuple, set)):
            raw = list(value)
        else:
            raw = re.split(r"[、,，\s]+", str(value))
        return {norm(x) for x in raw if norm(x)}

    @classmethod
    def _grade_objective(
        cls, q: Question, student_answer: Any, full_score: Optional[float] = None
    ) -> Dict[str, Any]:
        """客观题本地判分（不依赖 LLM，保证性能与准确）。

        答案比较统一走 `app.utils.answer`：判断题的「正确/错误/对/错/T/F」
        与选项 key A/B 等价；多选题兼容 JSON 数组与 "A,C" 字符串。

        full_score：试卷项分值。得分口径应是**试卷项 full_score**，而不是
        题库里 Question.score（两者可能不同，如组卷时统一给了更高的分值）。
        不传时保持旧行为，取 q.score（tests/verify_answer_normalization.py
        仍以两参调用）。
        """
        import json

        try:
            std = json.loads(q.answer) if q.answer else None
        except json.JSONDecodeError:
            std = q.answer

        is_correct = answers_match(q.type, std, student_answer)
        if is_correct:
            score = full_score if full_score is not None else q.score
            return {"is_correct": True, "score": float(score or 0.0), "comment": "回答正确"}

        std_set = normalize_answer(q.type, std)
        shown = "/".join(sorted(std_set)) if std_set else str(std or "")
        return {
            "is_correct": False, "score": 0.0,
            "comment": f"答案错误，正确答案：{shown}" if shown else "答案错误",
        }

    # ---------------- 主观题 ----------------
    def _grade_subjective_batch(
        self, db: Session, pending: List[Tuple[Dict[str, Any], Question, str]],
        user_id: Optional[int],
    ) -> Dict[int, Optional[Dict[str, Any]]]:
        """并发批改一批主观题，返回 {question_id: 判分结果 or None}。

        只做纯计算（LLM 往返 + 解析），**不在子线程里碰 Session**。
        并发度受题目数与 8 上限约束：再高对本机 SQLite 写日志没好处。
        首题若命中熔断（密钥无效/配额耗尽），其余题立即放弃 —— 此时再发
        请求只会把交卷时间继续拉长，而结果注定相同。
        """
        if not pending:
            return {}

        out: Dict[int, Optional[Dict[str, Any]]] = {}

        def one(q: Question, ans: str, fs: float) -> Optional[Dict[str, Any]]:
            return self._grade_subjective(db, q, ans, fs, user_id)

        # 先跑第一题：用于探测配置是否可用（熔断后 get_client 立即返回 None，
        # 后续调用毫秒级失败，不会产生网络等待）。
        first_it, first_q, first_ans = pending[0]
        out[first_q.id] = one(first_q, first_ans, first_it.get("full_score", first_q.score))

        rest = pending[1:]
        if not rest:
            return out

        # 首题就失败（且不是「答得不对」而是调用失败）→ 直接返回，
        # 让其余题走「待教师手动批改」，避免无谓的多轮重试。
        from app.agents.llm import is_available as _llm_ok
        if out[first_q.id] is None and not _llm_ok():
            for it, q, _a in rest:
                out[q.id] = None
            return out

        try:
            from concurrent.futures import ThreadPoolExecutor
            import time

            # 整批共享一个截止时间：逐题 fut.result(timeout=60) 会让总耗时
            # 变成 60×N（第一题就超时后面仍继续等），交卷接口必然被打爆。
            deadline = time.monotonic() + max(30.0, float(settings.LLM_TIMEOUT) * 2)
            pool = ThreadPoolExecutor(max_workers=min(8, len(rest)))
            try:
                futs = {
                    pool.submit(one, q, a, it.get("full_score", q.score)): q.id
                    for it, q, a in rest
                }
                for fut, qid in futs.items():
                    try:
                        remaining = max(0.001, deadline - time.monotonic())
                        out[qid] = fut.result(timeout=remaining)
                    except Exception:  # noqa: BLE001  单题失败/超时不影响整卷
                        out[qid] = None
                        fut.cancel()
            finally:
                # 不等待未完成任务：到点即返回，避免持线程/持请求到 3 分钟
                pool.shutdown(wait=False, cancel_futures=True)
        except Exception:  # noqa: BLE001  线程池不可用时退化为串行
            for it, q, a in rest:
                if q.id not in out:
                    out[q.id] = one(q, a, it.get("full_score", q.score))
        return out

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
