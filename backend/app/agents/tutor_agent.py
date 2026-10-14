"""5.5 答疑助教 Agent：RAG 知识库检索 + 题目解析 + 知识点讲解。"""
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents.base import BaseAgent
from app.agents.rag import build_context, search
from app.models import KnowledgePoint, Note, Question


class TutorAgent(BaseAgent):
    name = "tutor"
    display_name = "答疑助教智能体"
    description = "解答学生学科问题，讲解知识点，解析题目，提供学习方法指导"

    system_prompt = """你是九年义务教育阶段的资深助教，擅长用小学生/初中生能听懂的语言讲清知识点。

讲解要求：
1. 先给结论，再讲原理，层次分明。
2. 用类比、举例帮助理解，语言亲切不啰嗦。
3. 有参考资料时必须以参考资料为准，不要偏离教学大纲。
4. 讲完给一道同类练习题巩固，并给出答案。
5. 注意：涉及道德与法治、政治、历史等内容要符合教材表述。

只输出 JSON：
{
  "answer": "讲解正文（Markdown 格式，可用列表和代码块）",
  "knowledge_points": [{"id": 0, "name": "关联知识点名称"}],
  "related_questions": [{"stem": "同类练习题", "answer": "答案", "analysis": "简要解析"}],
  "study_tips": ["学习方法建议"]
}"""

    def execute(
        self,
        db: Session,
        user_id: Optional[int] = None,
        request: str = "",
        grade_id: Optional[int] = None,
        subject_id: Optional[int] = None,
        student_id: Optional[int] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        if not request:
            return {"answer": "请描述你的问题", "related_questions": []}

        # 1. RAG 检索
        results = search(
            request, db, grade_id=grade_id, subject_id=subject_id, top_k=5,
        )
        context = build_context(results, 5)

        # 2. 学生自己的笔记也纳入上下文
        if student_id:
            notes = db.scalars(
                select(Note).where(
                    Note.student_id == student_id,
                    Note.title.like(f"%{request[:20]}%"),
                ).limit(2)
            ).all()
            for n in notes:
                context.append(f"[我的笔记] {n.title}：{n.content[:300]}")

        # 3. 生成讲解
        result = self.call_llm(
            f"学生问题：{request}", db=db, user_id=user_id, context=context,
            biz_type="tutor", json_mode=True,
        )

        if not result["success"]:
            return self.fallback(db, request=request)

        parsed = result.get("parsed")
        if not isinstance(parsed, dict):
            # JSON 解析失败则直接用原文作为答案
            return {
                "answer": result.get("raw", "抱歉，我暂时无法回答该问题。"),
                "knowledge_points": [],
                "related_questions": [],
                "study_tips": [],
                "references": self._ref_meta(results),
            }

        return {
            "answer": parsed.get("answer", ""),
            "knowledge_points": parsed.get("knowledge_points", []),
            "related_questions": parsed.get("related_questions", []),
            "study_tips": parsed.get("study_tips", []),
            "references": self._ref_meta(results),
        }

    def fallback(self, db: Session, request: str = "", **kwargs) -> Dict[str, Any]:
        """无 LLM 时的关键词检索式答疑。"""
        results = search(request, db, top_k=5)
        if not results:
            return {
                "answer": (
                    f"未在题库和知识库中检索到与「{request[:30]}」相关的内容。\n\n"
                    "建议：\n1. 换个更具体的关键词，比如加上学科名和知识点名\n"
                    "2. 配置大模型 API Key（环境变量 LLM_API_KEY）后可获得完整的 AI 讲解"
                ),
                "knowledge_points": [],
                "related_questions": [],
                "study_tips": ["遇到不懂的知识点，先看教材定义，再看例题，最后做题巩固"],
            }

        lines = ["根据知识库检索，为你找到以下相关内容：\n"]
        for r in results:
            meta = r.get("metadata", {})
            kind = {"question": "相关题目", "knowledge": "知识点", "note": "笔记"}.get(
                meta.get("type"), "资料"
            )
            lines.append(f"**[{kind}]** {r.get('content', '')[:400]}\n")

        # 若命中题目，给出标准答案与解析
        for r in results:
            meta = r.get("metadata", {})
            if meta.get("type") == "question":
                q = db.get(Question, meta.get("id"))
                if q and q.answer:
                    lines.append(f"\n**参考答案**：{q.answer}\n")
                    if q.analysis:
                        lines.append(f"**解析**：{q.analysis}\n")

        return {
            "answer": "\n".join(lines),
            "knowledge_points": [],
            "related_questions": [],
            "study_tips": ["建议结合教材复习相关章节，再做 2-3 道同类题巩固"],
            "references": self._ref_meta(results),
        }

    @staticmethod
    def _ref_meta(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """整理引用来源。"""
        refs = []
        for r in results:
            meta = r.get("metadata", {})
            if meta.get("type") == "question":
                refs.append({"type": "题目", "id": meta.get("id"), "name": r.get("content", "")[:60]})
            elif meta.get("type") == "knowledge":
                refs.append({"type": "知识点", "id": meta.get("id"), "name": meta.get("name", "")})
            elif meta.get("type") == "note":
                refs.append({"type": "笔记", "id": meta.get("id"), "name": meta.get("title", "")})
        return refs
