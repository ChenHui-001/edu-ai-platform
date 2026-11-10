"""5.2 智能组卷 Agent：自然语言需求 → 平衡抽题生成试卷。"""
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents.base import BaseAgent
from app.core.exception import BusinessException
from app.models import (
    KnowledgePoint, Paper, PaperItem, Question, QuestionBankType,
)
from app.services.question_usage import recount_usage as _recount_usage
from app.utils.common import now_local

DIFFICULTY_WEIGHT = {"easy": 0.3, "medium": 0.5, "hard": 0.2}
TYPE_LABEL = {
    "single": "单选题", "multiple": "多选题", "judge": "判断题", "blank": "填空题",
    "short": "简答题", "calc": "计算题", "material": "材料分析题", "composition": "作文题",
}

# 传入的题型/难度分布可能是「比例」也可能是「题量」，两者语义完全不同。
# 旧实现一律 `int(v)` 当题量：默认值 `{"single":0.5,"blank":0.2,"short":0.3}`
# 被截断成 0 → 每个题型都 `continue` → 恒 0 题（P0-4）。
_RATIO_SUM_TOL = 1.0001


def _split_counts(ratio: Dict[str, Any], default_total: int = 10) -> Dict[str, int]:
    """把「比例」或「题量」统一换算成整数题量，且合计等于 `default_total`。

    判定规则：**数值全在 (0,1] 且合计 ≤ 1** 视为比例，按 `default_total` 换算；
    否则视为题量，直接取整求和。

    余数补给占比最大的那一档（与 `paper_compose._difficulty_to_ratio` 同一口径），
    保证 `sum(结果) == 合计`，不会因为四舍五入少出一道题。
    """
    nums: Dict[str, float] = {}
    for k, v in (ratio or {}).items():
        try:
            f = float(v)
        except (TypeError, ValueError):
            continue
        if f > 0:
            nums[str(k)] = f
    if not nums:
        return {}

    total_vals = sum(nums.values())
    is_ratio = total_vals <= _RATIO_SUM_TOL and max(nums.values()) <= 1.0

    if is_ratio:
        total_items = max(1, int(default_total))
        raw = {k: v * total_items / total_vals for k, v in nums.items()}
    else:
        total_items = max(1, int(round(total_vals)))
        raw = dict(nums)

    counts = {k: max(0, int(v)) for k, v in raw.items()}
    diff = total_items - sum(counts.values())
    if diff:
        # 余数补/扣到占比最大的一档
        top = max(raw, key=lambda k: raw[k])
        counts[top] = max(0, counts[top] + diff)
    return {k: v for k, v in counts.items() if v > 0}


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
- type_ratio: 题型分布**（可选）**，形如 {"single":10,"multiple":5,"judge":5,"blank":5,"short":5}。
  key 只能取 single / multiple / judge / blank / short / calc / material / composition
  之一，**不要编造 fill、solve、essay 等别名**（会被系统丢弃）。
  要求：
  ① 至少给出 2 种题型，单一题型的卷子不符合考试规范；
  ② 用户没有明确指定题型分布时**留空**（null 或不填），系统会按该学科
     命题标准的完整结构出卷，比自行编造更准确。
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

        # ★ 提示词明确规定「不要输出 grade_id / subject_id，只输出 grade_num / subject_name」
        #   （模型猜的 id 会指向别的年级/学科）。所以这里必须**按名称反查 id**，
        #   旧实现只读 id → 只传 request 时必然抛「无法识别学科」（P1-7）。
        grade_id, subject_id = self._resolve_grade_subject(
            db, grade_id, subject_id, parsed_params)

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
            db, user_id=user_id,
            grade_id=grade_id, subject_id=subject_id, total_score=total_score,
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
            db.flush()
            # 引用计数统一重算，不再逐题 +1（重算幂等，避免与其它入口的记账漂移）
            _recount_usage(db, [it["question_id"] for it in plan["items"]])
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
            # 约束被放宽过就说清楚，别让教师以为勾的知识点/难度都生效了（P1-11）
            "relaxations": plan.get("relaxations") or [],
            "tip": "；".join(plan.get("relaxations") or []),
        }

    # ---------------- 组卷引擎 ----------------
    def _compose(
        self, db: Session, *, grade_id: int, subject_id: int, total_score: float,
        difficulty_ratio: Dict[str, int], type_ratio: Dict[str, int], kp_ids: List[int],
        user_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """按难度分布与题型分布从题库抽题，并平衡知识点覆盖。

        **必须带题库可见性过滤**：`Question.bank_type` 默认 `private`、
        `status` 默认 `published`，只按 subject/type/difficulty 查会抽到
        **别人已发布但私有**的题——预览里能看到他人题干，保存时又被
        `_normalize_items` 以「无权使用题目」拒绝，表现为「抽到 N 题却保存失败」。
        同项目 `question_agent.py` 与 `paper_compose.py` 都收窄了，只有这里漏（P1-6）。
        """
        used: set = set()
        selected: List[Dict[str, Any]] = []
        coverage: Dict[str, int] = {}
        # 放宽记录：知识点/难度被放宽过就如实上报，不能让教师以为约束生效了
        relaxations: List[str] = []

        def _visible(stmt):
            """题库可见范围：公共库 ∪ 本人题目。

            私有题只有作者能用；`bank_type` 为空的历史数据按私有处理（宁严不宽）。
            """
            from sqlalchemy import or_

            cond = Question.bank_type == QuestionBankType.PUBLIC.value
            if user_id:
                cond = or_(cond, Question.owner_id == user_id)
            return stmt.where(cond)

        # 题型分布可能是比例也可能是题量，先统一成整数题量（P0-4）
        type_counts = _split_counts(type_ratio, default_total=10)
        total_items = sum(type_counts.values()) or 10
        # 每题平均分
        avg = round(total_score / total_items, 1)

        # 难度权重同样可能是比例（0.3/0.5/0.2）也可能是百分制（30/50/20），
        # 一律按 float 归一化。旧实现 `int(_w)` 把 0.3 截成 0，
        # 于是每档 `need` 恒为 1，难度分布形同虚设。
        diff_weights = {}
        for k, v in (difficulty_ratio or {}).items():
            try:
                f = float(v)
            except (TypeError, ValueError):
                continue
            if f > 0:
                diff_weights[str(k)] = f
        diff_total = sum(diff_weights.values()) or 1.0

        for qtype, qty in type_counts.items():
            if qty <= 0:
                continue
            picked = 0
            # 题型 + 难度双维度抽题
            for diff, _w in diff_weights.items():
                need = max(1, round(qty * _w / diff_total))
                stmt = _visible(select(Question).where(
                    Question.subject_id == subject_id,
                    Question.type == qtype,
                    Question.difficulty == diff,
                    Question.status == "published",
                ))
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
            # 难度配额不足时**先放宽难度、保留知识点约束**。
            # 旧实现这段兜底把 `knowledge_point_id.in_(kp_ids)` 丢了，
            # 用户勾的知识点被静默忽略，卷子里混进无关题，而知识点覆盖报告
            # 按"实际抽到的"统计 → 教师看不出约束没生效（P1-11）。
            if picked < qty:
                picked = self._fallback_fill(
                    db, qtype=qtype, qty=qty, picked=picked, avg=avg, used=used,
                    selected=selected, coverage=coverage,
                    subject_id=subject_id, grade_id=grade_id,
                    kp_ids=kp_ids, visible=_visible,
                )
            # 仍然不足：才放宽知识点约束，并**显式记账**，不假装约束生效
            if picked < qty and kp_ids:
                before = picked
                picked = self._fallback_fill(
                    db, qtype=qtype, qty=qty, picked=picked, avg=avg, used=used,
                    selected=selected, coverage=coverage,
                    subject_id=subject_id, grade_id=grade_id,
                    kp_ids=[], visible=_visible,
                )
                if picked > before:
                    relaxations.append(
                        f"{TYPE_LABEL.get(qtype, qtype)}：{picked - before} 题"
                        f"不在所选知识点范围内（题库匹配不足，已放宽）")

        # 重新编号排序
        total_score_actual = round(sum(i["score"] for i in selected), 1)
        preview = [
            {**i, "sort_order": idx + 1} for idx, i in enumerate(selected)
        ]
        return {
            "items": preview, "preview": preview,
            "actual_score": total_score_actual, "coverage": coverage,
            "relaxations": relaxations,
        }

    def _fallback_fill(
        self, db: Session, *, qtype: str, qty: int, picked: int, avg: float,
        used: set, selected: List[Dict[str, Any]], coverage: Dict[str, int],
        subject_id: int, grade_id: int, kp_ids: List[int], visible,
    ) -> int:
        """在指定约束下把某题型的缺口补齐，返回补后的已选数量。

        单独成函数是为了让「先放宽难度、再放宽知识点」两轮共用同一段逻辑：
        两轮只差 `kp_ids` 传不传，复制一份必然漂移（旧实现就是兜底那轮
        把知识点条件整个丢了）。
        """
        stmt = visible(select(Question).where(
            Question.subject_id == subject_id,
            Question.type == qtype,
            Question.status == "published",
        ))
        if grade_id:
            stmt = stmt.where(Question.grade_id == grade_id)
        if kp_ids:
            stmt = stmt.where(Question.knowledge_point_id.in_(kp_ids))
        for q in db.scalars(stmt.limit(max(qty, 1) * 3)).all():
            if picked >= qty:
                break
            if q.id in used:
                continue
            used.add(q.id)
            picked += 1
            kp = (db.get(KnowledgePoint, q.knowledge_point_id)
                  if q.knowledge_point_id else None)
            kp_name = kp.name if kp else "综合"
            coverage[kp_name] = coverage.get(kp_name, 0) + 1
            selected.append({
                "question_id": q.id, "score": avg, "difficulty": q.difficulty,
                "type": q.type, "stem": q.stem, "knowledge_point": kp_name,
                "section_name":
                    f"一、{TYPE_LABEL.get(qtype, qtype)}（共 {qty} 题，每题 {avg} 分）",
            })
        return picked

    def _build_report(self, plan: Dict[str, Any], ratio: Dict[str, int]) -> Dict[str, Any]:
        """难度分析 + 知识点覆盖报告。"""
        items = plan["items"]
        diff_count: Dict[str, int] = {}
        type_count: Dict[str, int] = {}
        for i in items:
            diff_count[i["difficulty"]] = diff_count.get(i["difficulty"], 0) + 1
            type_count[i["type"]] = type_count.get(i["type"], 0) + 1
        n = len(items) or 1
        # 目标占比按 float 归一（比例 0.3 / 百分制 30 两种写法都要能算）
        w = {}
        for k, v in (ratio or {}).items():
            try:
                f = float(v)
            except (TypeError, ValueError):
                continue
            if f > 0:
                w[str(k)] = f
        w_total = sum(w.values()) or 1.0
        return {
            "difficulty_report": {
                "distribution": {k: v for k, v in diff_count.items()},
                "ratio": {k: round(v / n * 100, 1) for k, v in diff_count.items()},
                "target_ratio": {k: round(v / w_total * 100, 1) for k, v in w.items()},
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

    @staticmethod
    def _resolve_grade_subject(
        db: Session, grade_id: Optional[int], subject_id: Optional[int],
        parsed: Dict[str, Any],
    ) -> tuple:
        """把「显式 id」或「模型给的名称/序号」解析成真实的 `(grade_id, subject_id)`。

        为什么必须做：本 Agent 的提示词写得很明确——「**不要输出 grade_id /
        subject_id**，你不知道系统内部主键，猜出来的 id 会指向别的年级/学科，
        只输出 grade_num 与 subject_name」。而旧代码只读 id，全仓也没有任何
        一处做名称→id 映射，于是「只传 request」这条主路径稳定报
        「无法识别学科」（P1-7）。

        `Subject` 的唯一键是 `(grade_id, name)`，所以**不能只按 name 查**：
        「数学」在 1~9 年级各有一条记录，按名称裸查会随机命中某个年级的数学，
        进而触发「题目年级/学科与试卷不一致」。先定位年级，再按 (grade_id, name) 过滤。
        """
        from app.models import Grade, Subject

        try:
            gid = int(grade_id or 0)
        except (TypeError, ValueError):
            gid = 0
        try:
            sid = int(subject_id or 0)
        except (TypeError, ValueError):
            sid = 0

        grade = db.get(Grade, gid) if gid else None
        if grade is None:
            # 提示词要求的是年级序号（1-9），不是主键
            raw = parsed.get("grade_num") or parsed.get("grade")
            try:
                num = int(raw)
            except (TypeError, ValueError):
                num = 0
            if 1 <= num <= 9:
                grade = db.scalar(select(Grade).where(Grade.grade_num == num))

        subject = db.get(Subject, sid) if sid else None
        if subject is None:
            name = str(parsed.get("subject_name") or "").strip()
            if name:
                stmt = select(Subject).where(Subject.name == name)
                if grade is not None:
                    stmt = stmt.where(Subject.grade_id == grade.id)
                subject = db.scalar(stmt.order_by(Subject.id).limit(1))

        # 只给了学科、没给年级：按学科的归属年级补齐，避免下游拿 grade_id=0 去抽题
        if grade is None and subject is not None:
            grade = db.get(Grade, subject.grade_id)

        return (grade.id if grade else 0, subject.id if subject else 0)

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
            # ★ 必须判 `paper` 再落库：旧实现这段在 `if save:` 之外，
            #   save=False（纯预览）时 paper 是 None → `paper.id` 直接 AttributeError，
            #   整条智能组卷链路崩掉（P0-4）。纯预览本来就不该写 PaperItem。
            if paper is None:
                continue
            db.add(
                PaperItem(
                    paper_id=paper.id, question_id=qid,
                    sort_order=i + 1, score=preview[i]["score"],
                    section_name=preview[i]["section_name"],
                )
            )
        if paper is not None:
            db.flush()
            # 引用计数统一重算一次即可：旧实现逐题 flush+commit+recount+refresh，
            # N 道题就 N 次全量重算，白烧 I/O 还可能把中间态写进库。
            _recount_usage(db, {
                int(q.get("id") or q.get("question_id")) for q in questions
                if (q.get("id") or q.get("question_id"))
            })
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
