"""5.1 题库生成 Agent：按知识点/题型/难度自动生成原创题目。"""
import hashlib
import random
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents.base import BaseAgent
from app.agents.rag import build_context, search
from app.core.exception import BusinessException
from app.models import KnowledgePoint, Question, Subject, User
from app.utils.common import utcnow


class QuestionGeneratorAgent(BaseAgent):
    name = "question_generator"
    display_name = "题库生成智能体"
    description = "根据知识点、题型、难度要求自动生成原创题目，覆盖中小学全学科"

    system_prompt = """你是中国九年义务教育的资深命题专家，精通小学 1-6 年级和初中 7-9 年级的语文、数学、英语、物理、化学、生物、政治、历史、地理等学科。

要求：
1. 题目必须严格符合该年级该学科的教学大纲和认知水平，不超纲。
2. 题干清晰准确，选项互斥且有区分度，干扰项合理。
3. 解析要讲清解题思路和易错点。
4. 只输出 JSON 数组，不要任何额外文字。

输出格式：
[
  {
    "type": "single",
    "stem": "题干",
    "options": [{"key":"A","text":"选项"},{"key":"B","text":"选项"},{"key":"C","text":"选项"},{"key":"D","text":"选项"}],
    "answer": "A",
    "analysis": "解析",
    "difficulty": "medium",
    "score": 5,
    "knowledge_point_id": 0,
    "knowledge_point_name": "知识点名称"
  }
]

type 取值：single(单选) multiple(多选) judge(判断) blank(填空) short(简答) calc(计算) material(材料分析) composition(作文)
difficulty 取值：easy / medium / hard"""

    def execute(
        self,
        db: Session,
        user_id: Optional[int] = None,
        grade_id: Optional[int] = None,
        subject_id: Optional[int] = None,
        knowledge_point_id: Optional[int] = None,
        question_type: str = "single",
        count: int = 5,
        difficulty: str = "medium",
        save: bool = False,
        **kwargs,
    ) -> Dict[str, Any]:
        if not subject_id:
            raise BusinessException("请指定学科")
        count = max(1, min(int(count), 20))

        subject = db.get(Subject, subject_id)
        if not subject:
            raise BusinessException("学科不存在")

        # 组装上下文：相关知识点 + 同类题参考
        context: List[str] = []
        if knowledge_point_id:
            kp = db.get(KnowledgePoint, knowledge_point_id)
            if kp:
                context.append(f"目标知识点：{kp.name}（{kp.description or '无描述'}）")
        else:
            kps = db.scalars(
                select(KnowledgePoint).where(
                    KnowledgePoint.subject_id == subject_id,
                    KnowledgePoint.level == 3,
                    KnowledgePoint.is_active.is_(True),
                ).limit(10)
            ).all()
            if kps:
                context.append("可选知识点：" + "、".join(k.name for k in kps[:10]))
            refs = search(
                "常见考题", db, subject_id=subject_id, top_k=3, types=["question"]
            )
            context.extend(build_context(refs, 3))

        prompt = (
            f"请生成 {count} 道{self._type_name(question_type)}，"
            f"难度要求：{self._difficulty_name(difficulty)}，"
            f"学科：{subject.name}（教材 {subject.textbook_version or '默认'}）。"
        )
        if knowledge_point_id and context:
            prompt += f"\n必须紧扣知识点：{context[0].split('：')[1].split('（')[0]}。"

        result = self.call_llm(prompt, db=db, user_id=user_id, context=context,
                               biz_type="question_generate", json_mode=True)

        if not result["success"] or not result.get("parsed"):
            return self.fallback(db, grade_id=grade_id, subject_id=subject_id,
                                 question_type=question_type, count=count,
                                 difficulty=difficulty, save=save, user_id=user_id)

        items = result["parsed"]
        if isinstance(items, dict):
            items = items.get("questions", [items])
        if not isinstance(items, list):
            items = []

        owner_id = user_id or (db.query(User).filter(User.username == "admin").scalar() or User.id).first().id
        questions: List[Dict[str, Any]] = []
        saved = 0
        for it in items[:count]:
            if not isinstance(it, dict) or not it.get("stem"):
                continue
            q = Question(
                type=it.get("type", question_type),
                stem=it["stem"],
                options=self._dump(it.get("options")),
                answer=self._dump(it.get("answer")),
                analysis=it.get("analysis"),
                score=float(it.get("score", 5)),
                difficulty=it.get("difficulty", difficulty),
                grade_id=grade_id or 0,
                subject_id=subject_id,
                knowledge_point_id=it.get("knowledge_point_id") or knowledge_point_id,
                bank_type="private",
                owner_id=owner_id,
                status="draft",  # AI 生成题目先进待审核库
                fingerprint=self._fingerprint(it["stem"]),
                source="ai",
            )
            questions.append({"stem": q.stem, "type": q.type, "difficulty": q.difficulty,
                              "score": q.score, "answer": it.get("answer"), "analysis": q.analysis,
                              "options": it.get("options")})
            if save:
                db.add(q)
                saved += 1

        if save:
            db.commit()
            for q in db.scalars(select(Question).order_by(Question.id.desc()).limit(saved)).all():
                from app.agents.rag import index_question
                index_question(q)

        return {
            "questions": questions,
            "total": len(questions),
            "saved": saved,
            "subject": subject.name,
            "tip": "AI 生成题目已进入待审核库，审核通过后方可上架使用" if save else "",
        }

    def fallback(self, db: Session, **kwargs) -> Dict[str, Any]:
        """规则引擎：基于题库检索复用（无 LLM 时）。"""
        subject_id = kwargs.get("subject_id")
        count = kwargs.get("count", 5)
        kp_id = kwargs.get("knowledge_point_id")

        stmt = select(Question).where(
            Question.subject_id == subject_id,
            Question.status == "published",
        )
        if kp_id:
            stmt = stmt.where(Question.knowledge_point_id == kp_id)
        rows = db.scalars(stmt.limit(count)).all()

        items = [
            {"stem": q.stem, "type": q.type, "difficulty": q.difficulty,
             "score": q.score, "answer": q.answer, "analysis": q.analysis, "options": q.options}
            for q in rows
        ]
        return {
            "questions": items,
            "total": len(items),
            "saved": 0,
            "tip": "模型不可用，已从公共题库匹配相似题目。请配置 LLM_API_KEY 启用 AI 生成。",
        }

    # ---------------- 工具 ----------------
    @staticmethod
    def _type_name(t: str) -> str:
        return {
            "single": "单选题", "multiple": "多选题", "judge": "判断题", "blank": "填空题",
            "short": "简答题", "calc": "计算题", "material": "材料分析题", "composition": "作文题",
        }.get(t, "单选题")

    @staticmethod
    def _difficulty_name(d: str) -> str:
        return {"easy": "简单", "medium": "中等", "hard": "困难"}.get(d, "中等")

    @staticmethod
    def _dump(v: Any) -> Optional[str]:
        import json
        if v is None:
            return None
        return v if isinstance(v, str) else json.dumps(v, ensure_ascii=False)

    @staticmethod
    def _fingerprint(stem: str) -> str:
        """题干归一化哈希，用于查重。"""
        import re
        norm = re.sub(r"\s+", "", re.sub(r"[（(].*?[)）]", "", stem))
        return hashlib.md5(norm.encode()).hexdigest()
