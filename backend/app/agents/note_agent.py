"""5.6 笔记整理 Agent：提炼核心、结构化梳理、生成思维导图与复习大纲。"""
import json
import re
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.agents.base import BaseAgent
from app.models import KnowledgePoint, Note


class NoteOrganizerAgent(BaseAgent):
    name = "note_organizer"
    display_name = "笔记整理智能体"
    description = "提炼笔记核心内容，结构化梳理知识点，生成思维导图和复习大纲"

    system_prompt = """你是九年义务教育的笔记整理专家，擅长把零散的学习记录整理成结构化的高质量笔记。

要求：
1. 提炼核心知识点，删除冗余重复内容。
2. 知识点用层级结构组织（总-分-细）。
3. 补充必要的公式、定义、定理。
4. 复习大纲要能直接作为复习清单使用。
5. 思维导图用缩进文本表示层级。

只输出 JSON：
{
  "summary": "核心知识点总结（150字以内）",
  "outline": ["一级标题", "二级要点", ...],
  "mindmap": {"name": "中心主题", "children": [{"name": "分支", "children": [{"name": "叶子"}]}]},
  "knowledge_points": [{"name": "知识点名", "description": "简要说明", "importance": "high/medium/low"}],
  "review_tasks": ["复习任务1", "复习任务2"],
  "polished_content": "整理优化后的笔记正文（Markdown）"
}"""

    def execute(
        self,
        db: Session,
        user_id: Optional[int] = None,
        note_id: Optional[int] = None,
        content: Optional[str] = None,
        title: Optional[str] = None,
        save: bool = False,
        **kwargs,
    ) -> Dict[str, Any]:
        raw = content or ""
        note: Optional[Note] = None
        if note_id:
            note = db.get(Note, note_id)
            if not note:
                return {"message": "笔记不存在"}
            raw = note.content
            title = title or note.title
        if not raw.strip():
            return {"message": "笔记内容为空"}

        result = self.call_llm(
            f"笔记标题：{title or '未命名'}\n\n笔记原文：\n{raw[:8000]}",
            db=db, user_id=user_id, biz_type="note", biz_id=note_id, json_mode=True,
        )

        if not result["success"]:
            data = self.fallback(content=raw, title=title)
        else:
            parsed = result.get("parsed")
            if isinstance(parsed, dict):
                data = parsed
            else:
                data = self.fallback(content=raw, title=title)

        # 尝试关联已有知识点
        data["matched_knowledge"] = self._match_knowledge(db, data.get("knowledge_points", []))

        if save and note:
            note.ai_summary = data.get("summary")
            note.ai_outline = json.dumps(data.get("outline", []), ensure_ascii=False)
            note.ai_mindmap = json.dumps(data.get("mindmap", {}), ensure_ascii=False)
            if data.get("polished_content"):
                note.content = data["polished_content"]
            db.commit()

        return data

    def fallback(self, content: str = "", title: str = "", **kwargs) -> Dict[str, Any]:
        """规则降级：基于文本结构分析提炼大纲。"""
        lines = [ln.strip() for ln in content.splitlines() if ln.strip()]

        # 提取标题级行（# 标题、加粗、编号列表）
        outline: List[str] = []
        points: List[Dict[str, Any]] = []
        for ln in lines[:80]:
            if re.match(r"^#{1,6}\s", ln) or re.match(r"^\d+[\.、]", ln) or re.match(r"^[-*]\s", ln):
                clean = re.sub(r"^[#\d\.\-*\s]+", "", ln).strip()
                if clean and clean not in outline:
                    outline.append(clean)
                    points.append({
                        "name": clean[:40],
                        "description": clean[:120],
                        "importance": "high" if len(clean) < 15 else "medium",
                    })
        if not outline:
            # 按句子切分
            sentences = [s.strip() for s in re.split(r"[。！？\n]", content) if len(s.strip()) > 8]
            for s in sentences[:20]:
                outline.append(s[:60])
                points.append({"name": s[:30], "description": s[:120], "importance": "medium"})

        mindmap = self._build_mindmap(title or "笔记主题", points[:8])
        return {
            "summary": f"本笔记共 {len(content)} 字，提取 {len(points)} 个要点。配置大模型后可获得更深入的智能整理。",
            "outline": outline[:30],
            "mindmap": mindmap,
            "knowledge_points": points[:15],
            "review_tasks": [f"复习「{p['name']}」并做 3 道练习题" for p in points[:5]],
            "polished_content": "",
        }

    @staticmethod
    def _build_mindmap(center: str, points: List[Dict[str, Any]]) -> Dict[str, Any]:
        """构建简易思维导图结构。"""
        return {
            "name": center,
            "children": [
                {"name": p["name"], "children": [{"name": p["description"][:40]}]}
                for p in points[:8]
            ],
        }

    @staticmethod
    def _match_knowledge(db: Session, kps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """匹配已有知识点。"""
        from sqlalchemy import select

        matched = []
        for kp in kps[:10]:
            name = kp.get("name", "")
            if not name:
                continue
            row = db.scalar(
                select(KnowledgePoint).where(KnowledgePoint.name.like(f"%{name}%")).limit(1)
            )
            if row:
                matched.append({"id": row.id, "name": row.name, "subject_id": row.subject_id})
        return matched
