"""5.1 题库生成 Agent：按知识点/题型/难度自动生成原创题目。"""
import hashlib
from typing import Any, Dict, List, Optional

from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.agents.base import BaseAgent
from app.agents.rag import build_context, search
from app.core.exception import BusinessException
from app.models import KnowledgePoint, Question, Subject, User


class QuestionGeneratorAgent(BaseAgent):
    name = "question_generator"
    display_name = "题库生成智能体"
    description = "根据知识点、题型、难度要求自动生成原创题目，覆盖中小学全学科"

    system_prompt = """你是中国九年义务教育的资深命题专家，精通小学 1-6 年级和初中 7-9 年级的语文、数学、英语、物理、化学、生物、政治、历史、地理等学科。

要求：
1. 题目必须严格符合该年级该学科的教学大纲和认知水平，不超纲。
2. 题干清晰准确，选项互斥且有区分度，干扰项合理。
3. 解析要讲清解题思路和易错点。
4. 只输出 JSON 数组，不要任何额外文字；**不要换行和缩进**，请输出紧凑 JSON。
   （缩进与换行会显著占用 max_tokens 预算，推理型模型的 thinking token 还要
   再分走一部分，预算不足时正文会被截断成非法 JSON。）
5. knowledge_point_id 只能填【参考资料】里【可选知识点】列出的 id；没有对应的
   知识点就填 0。**绝对不要编造 id**，填错的 id 无法落库。

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
            if not kp:
                # 原来这里只是 if kp: 静默跳过，知识点 id 错的会被忽略并继续出题，
                # 之后题目落到一个不属于本学科的 knowledge_point_id 上，
                # 掌握图谱/复习计划按知识点统计时全部错位。必须显式拦截。
                raise BusinessException("知识点不存在，请重新选择")
            if kp.subject_id and kp.subject_id != subject_id:
                # 知识点必须属于所选学科。前端若传了跨年级的学科 id
                # （Subject 唯一键是 (grade_id, name)，代表 id 永远指向最低年级），
                # 就会走到这里 —— 实测产生过「七年级一元一次方程的题
                # 挂在一年级『20以内加减法』知识点上」的脏数据。
                other = db.get(Subject, kp.subject_id)
                raise BusinessException(
                    f"知识点「{kp.name}」属于"
                    f"{other.name if other else '其他学科'}，与所选学科「{subject.name}」不匹配，"
                    f"请重新选择年级与学科"
                )
            context.append(f"目标知识点：{kp.name}（{kp.description or '无描述'}）")
        else:
            # 候选知识点：**不能按 level==3 过滤** —— 实测种子数据只到 level 1/2，
            # level=3 恒为 0 条，过滤后候选永远为空，模型拿不到任何真实 id
            # 只能凭空编造（实测编出不存在的 101），落库直接触发外键约束失败。
            # 必须把 id 一起给模型：只给名称时模型无从选择 knowledge_point_id。
            kps = db.scalars(
                select(KnowledgePoint).where(
                    KnowledgePoint.subject_id == subject_id,
                    KnowledgePoint.is_active.is_(True),
                ).order_by(KnowledgePoint.level.desc(), KnowledgePoint.id)
                .limit(12)
            ).all()
            if kps:
                context.append(
                    "可选知识点（knowledge_point_id 只能取下列 id 之一，"
                    "找不到对应知识点就填 0，不要编造 id）："
                    + "、".join(f"{k.name}(id={k.id})" for k in kps)
                )
            else:
                context.append("该学科暂无知识点，knowledge_point_id 必须填 0。")
            refs = search(
                "常见考题", db, subject_id=subject_id, top_k=3,
                types=["question"], student_id=user_id,
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
            # 把真实原因带下去：「未配置 Key」「鉴权失败」「输出被截断」是三类
            # 完全不同的问题，笼统报「请配置 LLM_API_KEY」会把运维引向错误方向
            # （实测：Key 正常，只是 max_tokens 被推理 token 吃光导致正文为空）。
            return self.fallback(db, grade_id=grade_id, subject_id=subject_id,
                                 question_type=question_type, count=count,
                                 difficulty=difficulty, save=save, user_id=user_id,
                                 reason=result.get("reason") or "")

        items = result["parsed"]
        if isinstance(items, dict):
            items = items.get("questions", [items])
        if not isinstance(items, list):
            items = []

        owner_id = user_id or self._default_owner_id(db)
        # grade_id 是**非空外键**：调用方没传时必须回落到学科所属年级，
        # 写 0 会直接触发外键约束失败。
        grade_id = grade_id or (subject.grade_id if subject else None)
        if not grade_id:
            raise BusinessException("该学科未绑定年级，无法生成题目")
        questions: List[Dict[str, Any]] = []
        saved_objs: List[Question] = []
        saved = 0
        for it in items[:count]:
            if not isinstance(it, dict) or not it.get("stem"):
                continue
            # 模型给的知识点 id **不可信**：必须校验后再落库。
            # 未校验时模型编造的 id 会让整批题目因外键约束失败而全军覆没。
            kp_id = self._resolve_kp_id(
                db, it.get("knowledge_point_id"), subject_id,
                kp_name=it.get("knowledge_point_name"),
                fallback_id=knowledge_point_id,
            )
            q = Question(
                type=it.get("type", question_type),
                stem=it["stem"],
                options=self._dump(it.get("options")),
                answer=self._dump(it.get("answer")),
                analysis=it.get("analysis"),
                score=float(it.get("score", 5)),
                difficulty=it.get("difficulty", difficulty),
                grade_id=grade_id,
                subject_id=subject_id,
                knowledge_point_id=kp_id,
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
                saved_objs.append(q)
                saved += 1

        if not questions:
            # 解析出了结构却没有一道可用题目（缺 stem 等必要字段），
            # 同样按失败处理并说明原因 —— 否则前端会看到「生成成功但 0 道题」
            # 的空结果，比降级提示更难排查。
            return self.fallback(db, grade_id=grade_id, subject_id=subject_id,
                                 question_type=question_type, count=count,
                                 difficulty=difficulty, save=save, user_id=user_id,
                                 reason="模型返回的题目缺少题干等必要字段")

        if save:
            try:
                db.commit()
            except IntegrityError as exc:
                # 兜底：即便前置校验漏了某个外键，也不能让整批题目因
                # 约束失败而 500 + 一句堆栈。回滚并给出可读的失败原因。
                db.rollback()
                raise BusinessException(
                    "题目落库失败：关联数据（知识点/学科/属主）不存在或已删除，"
                    "本次生成未保存，请重新选择知识点后重试"
                ) from exc
            # 关键：把落库后的主键回填到返回值。
            # 下游（智能组卷）依赖 question_id 建立 PaperItem，
            # 不回填的话生成的题目无法被任何试卷引用。
            #
            # 必须用**本批落库对象自身的主键**回填，不能再用
            # `select(Question.id).order_by(desc).limit(saved)` 反查：
            # 并发出题时另一个请求可能已插入更高的 id，反查会把别人的题目
            # 误当成本批结果（BUG-009）。SessionLocal 已设 expire_on_commit=False，
            # 提交后 obj.id 可直接读取，无需再回查。
            for q, obj in zip(questions, saved_objs):
                q["id"] = obj.id
            from app.agents.rag import index_question
            for obj in saved_objs:
                if obj.id:
                    index_question(obj)

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
        owner_id = kwargs.get("user_id")
        want_type = kwargs.get("question_type")

        stmt = select(Question).where(
            Question.subject_id == subject_id,
            Question.status == "published",
        )
        # 复用的题必须**当前用户可用**（公共库或本人私有）：
        # 旧实现只按学科 + published 取，会把别的教师的私有题（含答案与解析）
        # 直接返回给调用方。AI 组卷/补题走这条降级路径时，这些题会进入预览——
        # 预览能看到、保存时却被 `_normalize_items` 以"无权使用题目"拒绝，
        # 表现为"明明抽到 3 题，保存报错"。在源头收窄，下游无需再猜。
        if not kwargs.get("allow_all_banks"):
            if owner_id:
                stmt = stmt.where(or_(
                    Question.bank_type == "public",
                    Question.owner_id == owner_id,
                ))
            else:
                stmt = stmt.where(Question.bank_type == "public")
        # 题型必须匹配：调用方要 3 道单选题时，旧实现会把题库里排在前面的
        # 填空题一起 `limit(3)` 出来，白占配额——上层过滤后只剩 1~2 道，
        # 表现为"要 3 题只给 2 题"，且混进别的大题还会把卷面结构搞乱。
        if want_type:
            stmt = stmt.where(Question.type == str(want_type))
        if kp_id:
            stmt = stmt.where(Question.knowledge_point_id == kp_id)
        rows = db.scalars(stmt.limit(count)).all()

        items = [
            # 必须带上 id：下游智能组卷依赖 question_id 建立 PaperItem，
            # 缺失时 AI 组卷会生成 0 道题的空卷。
            {"id": q.id, "question_id": q.id, "stem": q.stem, "type": q.type,
             "difficulty": q.difficulty, "score": q.score, "answer": q.answer,
             "analysis": q.analysis, "options": q.options}
            for q in rows
        ]
        reason = str(kwargs.get("reason") or "")
        if not reason or "未配置" in reason or "API_KEY" in reason:
            tip = "模型不可用，已从公共题库匹配相似题目。请配置 LLM_API_KEY 启用 AI 生成。"
        else:
            tip = f"AI 生成未成功（{reason}），已从公共题库匹配相似题目。"
        return {
            "questions": items,
            "total": len(items),
            "saved": 0,
            "reused": len(items),
            "tip": tip,
        }

    # ---------------- 工具 ----------------
    @staticmethod
    def _resolve_kp_id(
        db: Session,
        raw_id: Any,
        subject_id: Optional[int],
        kp_name: Optional[str] = None,
        fallback_id: Optional[int] = None,
    ) -> Optional[int]:
        """校验模型给出的知识点 id，返回**可安全落库**的值（无效则回退或置空）。

        模型会**编造**不存在的知识点 id（实测在候选为空时编出 101，而库里
        只有 id ≤ 97）。直接写库会触发 `FOREIGN KEY constraint failed`，
        **整批题目全部落库失败**，用户只看到一句 500 堆栈。

        三重判据：
          1. id 必须真实存在；
          2. 必须属于当前学科（跨学科挂靠会让掌握度/复习计划按知识点统计错位）；
          3. 都不过则回退：请求指定的知识点 → 按名称在同学科内匹配 → 留空。
             留空是可接受的：题目照样入库，只是未挂知识点，用户可在审核台补挂。
        """
        def _valid(kp_id: Optional[int]) -> Optional[int]:
            if not kp_id:
                return None
            kp = db.get(KnowledgePoint, int(kp_id))
            if kp is None:
                return None
            if subject_id and kp.subject_id != subject_id:
                return None
            return kp.id

        value = 0
        try:
            value = int(str(raw_id).strip()) if raw_id is not None and str(raw_id).strip() else 0
        except (TypeError, ValueError):
            value = 0
        resolved = _valid(value) if value > 0 else None
        if resolved:
            return resolved
        resolved = _valid(fallback_id)
        if resolved:
            return resolved
        # 模型给了名称但 id 无效 → 在同学科内按名称匹配（与 question_ai 的
        # _suggest_kp 同一思路，保证两条 AI 出题路径的挂靠口径一致）
        name = str(kp_name or "").strip()
        if name and subject_id:
            rows = db.scalars(
                select(KnowledgePoint).where(
                    KnowledgePoint.subject_id == subject_id,
                    KnowledgePoint.is_active.is_(True),
                )
            ).all()
            matched = [k for k in rows if k.name and (k.name in name or name in k.name)]
            if matched:
                return max(matched, key=lambda k: len(k.name or "")).id
        return None

    @staticmethod
    def _default_owner_id(db: Session) -> int:
        """兜底属主：优先 admin 账号，其次第一个用户（保证 owner_id 外键有效）。

        原实现 `(... or User.id).first().id` 在 user_id 为空时会对整数调
        `.first()`（AttributeError），是一条走不通的分支。
        """
        row = db.scalar(select(User.id).where(User.username == "admin"))
        if row:
            return int(row)
        row = db.scalar(select(User.id).order_by(User.id).limit(1))
        if not row:
            raise BusinessException("系统内没有任何用户，无法确定题目属主")
        return int(row)

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
