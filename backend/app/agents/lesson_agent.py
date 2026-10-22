"""AI 教案生成 Agent：教学条件 → 结构完整、可直接使用的教案。

设计要点（与出题/组卷 Agent 的差异）：

1. **两段式生成**。教案正文（目标+重难点+准备 / 过程+练习+作业+板书）如果一次
   生成，长教案必然超出 `LLM_MAX_TOKENS=2048`，表现为 JSON 被截断 —— 前端看到
   的是「生成失败」，实际是模型没说完。拆成两次调用后，每段输出约 800/1500
   token，超限风险显著下降；同时两次调用之间天然是一个进度节点。

2. **结构必完整**（本模块的核心承诺）。模型的输出不可信：可能漏掉「教学准备」、
   把 5 个环节的时长写成合计 60 分钟（课时只有 45）、直接返回空数组。
   因此无论 LLM 是否成功，都过一遍 `_normalize()`：
   缺章节 → 按模板补齐；时长合计不符 → 按原占比缩放到课时长度；
   环节不足 → 补足到模板环节。补齐的字段会记进 `generation.missing`，
   由前端明确提示「这几节是系统补的，请重点核对」，而不是假装生成完整。

3. **无 LLM 可用**。`_rule_plan()` 是一件真正能用的降级产物（按学段/学科/
   知识点套模板并注入具体内容），不是占位空壳。系统在离线部署下依然可交付。
"""
import json
import re
import time
from typing import Any, Callable, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.agents.base import BaseAgent
from app.core.exception import BusinessException
from app.models import Grade, KnowledgePoint, Subject

# 标准教学环节与时长占比：LLM 漏环节 / 无 LLM 时按此补齐。
# 占比之和必须为 1.0（`_normalize` 依赖它分配剩余时长）。
DEFAULT_STAGE_TEMPLATE: List[Tuple[str, float]] = [
    ("导入新课", 0.10),
    ("新课讲授", 0.45),
    ("巩固练习", 0.24),
    ("课堂小结", 0.13),
    ("作业布置", 0.08),
]

# 章节中文名：用于生成「系统补全了哪些章节」的提示，以及补全时写进正文的占位说明。
SECTION_LABELS: Dict[str, str] = {
    "objectives": "教学目标",
    "key_points": "教学重点",
    "difficulties": "教学难点",
    "teaching_preparation": "教学准备",
    "stages": "教学过程",
    "class_exercise": "课堂练习",
    "homework": "作业布置",
    "board_design": "板书设计",
}

# 教案正文的最小可用长度。低于该长度视为「模型给了个空壳」，按缺失处理。
MIN_SECTION_CHARS = 8

# 环节补全顺序：收尾 -> 练习 -> 导入/新授。
# 一节没有小结与作业的课在实际上课中无法收口，优先保这两节。
STAGE_FILL_ORDER: List[str] = ["课堂小结", "作业布置", "巩固练习", "导入新课", "新课讲授"]


class LessonPlanAgent(BaseAgent):
    """把教学条件扩展成完整教案。"""

    name = "lesson_planner"
    display_name = "AI 教案生成智能体"
    description = "根据主题/知识点/年级/学科/课时自动生成结构完整的教案，含师生活动与练习作业"

    system_prompt = """你是九年义务教育的资深教研员，擅长按最新课程标准编写可直接上课的教案。

写作要求：
1. 教学目标必须落到可观测的行为动词（如"能说出""会运用""能区分"），分「知识与技能 / 过程与方法 / 情感态度与价值观」三段。
2. 重点与难点要区分开：重点是最核心的知识技能，难点是学生实际容易卡住的地方。
3. 教师活动要写清具体动作与关键提问原话，学生活动要写清具体任务与预期表现，不要写"教师讲解、学生听讲"这类空话。
4. 内容必须贴合指定年级学生的认知水平，不超纲、不使用该年级未学的知识。
5. 只输出 JSON，不要任何解释性文字、不要 markdown 代码块标记。"""

    # ------------------------------------------------------------ 主流程
    def execute(
        self,
        db: Session,
        user_id: Optional[int] = None,
        *,
        topic: str = "",
        grade_id: Optional[int] = None,
        subject_id: Optional[int] = None,
        knowledge_point_id: Optional[int] = None,
        duration_minutes: Any = 45,
        period: Optional[str] = None,
        objectives: str = "",
        textbook_version: Optional[str] = None,
        difficulty: str = "",
        extra_requirements: str = "",
        progress_cb: Optional[Callable[[int, str], None]] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        t0 = time.perf_counter()
        ctx = self._resolve_context(
            db, topic=topic, grade_id=grade_id, subject_id=subject_id,
            knowledge_point_id=knowledge_point_id, duration_minutes=duration_minutes,
            period=period, objectives=objectives, textbook_version=textbook_version,
            difficulty=difficulty, extra_requirements=extra_requirements,
        )
        self._progress(progress_cb, 15, "解析教学条件")

        # 第一段：目标 / 重难点 / 教学准备
        head = self._llm_head(db, user_id, ctx)
        self._progress(progress_cb, 45, "拟定教学目标与重难点")

        # 第二段：教学过程 / 练习 / 作业 / 板书
        body = self._llm_body(db, user_id, ctx, head or {})
        self._progress(progress_cb, 80, "展开教学过程与师生活动")

        mode = "llm" if (head or body) else "rule"
        if head is None and body is None:
            head, body = self._rule_head(ctx), self._rule_body(ctx)

        data = self._assemble(ctx, head or {}, body or {}, mode=mode)
        self._progress(progress_cb, 95, "校验并补全教案结构")

        data["generation"]["duration_ms"] = int((time.perf_counter() - t0) * 1000)
        return data

    def fallback(self, db: Optional[Session] = None, **kwargs: Any) -> Dict[str, Any]:
        """规则引擎降级入口（BaseAgent 契约）。

        execute() 内部已自行降级，这里是为「execute 抛异常时 base.run 兜底」
        准备的最小可用产物：条件不全就返回带 warnings 的骨架，而不是空 dict。
        """
        try:
            ctx = self._resolve_context(
                db, topic=kwargs.get("topic", "") or "未命名课题",
                grade_id=kwargs.get("grade_id"), subject_id=kwargs.get("subject_id"),
                knowledge_point_id=kwargs.get("knowledge_point_id"),
                duration_minutes=kwargs.get("duration_minutes", 45),
                period=kwargs.get("period"), objectives=kwargs.get("objectives", "") or "",
                textbook_version=kwargs.get("textbook_version"),
                difficulty=kwargs.get("difficulty", "") or "",
                extra_requirements=kwargs.get("extra_requirements", "") or "",
            )
        except Exception:  # noqa: BLE001  条件本身不合法时只能给出最简骨架
            ctx = {
                "topic": kwargs.get("topic", "") or "未命名课题",
                "grade_id": None, "grade_name": "", "subject_id": None, "subject_name": "",
                "knowledge_point_id": None, "knowledge_point_name": None,
                "knowledge_point_desc": "", "duration_minutes": 45, "period": None,
                "textbook_version": None, "objectives": "", "difficulty": "",
                "extra_requirements": "",
            }
        return self._assemble(ctx, self._rule_head(ctx), self._rule_body(ctx), mode="rule")

    # ------------------------------------------------------------ 条件解析
    def _resolve_context(
        self, db: Optional[Session], *, topic: str, grade_id: Optional[int],
        subject_id: Optional[int], knowledge_point_id: Optional[int],
        duration_minutes: Any, period: Optional[str], objectives: str,
        textbook_version: Optional[str], difficulty: str, extra_requirements: str,
    ) -> Dict[str, Any]:
        """校验并解析教学条件。开头就把非法条件拦住，避免生成出错误年级的教案。"""
        topic = (topic or "").strip()
        if not topic:
            raise BusinessException("教学主题（topic）不能为空")

        grade: Optional[Grade] = None
        if grade_id:
            grade = db.get(Grade, int(grade_id)) if db else None
            if db and not grade:
                raise BusinessException("年级不存在")

        subject: Optional[Subject] = None
        if subject_id:
            subject = db.get(Subject, int(subject_id)) if db else None
            if db and not subject:
                raise BusinessException("学科不存在")

        # 学科按年级配置（unique(grade_id, name)），跨年级取 id 是历史高频错误：
        # 「数学 + 七年级」会静默命中一年级的数学学科记录，生成整份错年级的教案。
        # 教案的价值全在「贴合这个年级」，因此这里硬失败而不是告警放行。
        if subject and grade and subject.grade_id and int(subject.grade_id) != int(grade.id):
            raise BusinessException(
                f"学科「{subject.name}」不属于{grade.name}，请传该年级下的学科 id"
                f"（用 /edu/subjects?grade_id={grade.id} 查询）")

        kp: Optional[KnowledgePoint] = None
        if knowledge_point_id:
            kp = db.get(KnowledgePoint, int(knowledge_point_id)) if db else None
            if db and not kp:
                raise BusinessException("知识点不存在")

        try:
            minutes = int(duration_minutes or 45)
        except (TypeError, ValueError):
            raise BusinessException("课时长度必须是分钟数") from None
        minutes = max(15, min(180, minutes))

        return {
            "topic": topic,
            "grade_id": int(grade.id) if grade else (int(grade_id) if grade_id else None),
            "grade_name": grade.name if grade else (f"{grade_id} 年级" if grade_id else "未指定年级"),
            "grade_num": grade.grade_num if grade else None,
            "subject_id": int(subject.id) if subject else (int(subject_id) if subject_id else None),
            "subject_name": subject.name if subject else (f"学科{subject_id}" if subject_id else "未指定学科"),
            "knowledge_point_id": int(kp.id) if kp else None,
            "knowledge_point_name": kp.name if kp else None,
            "knowledge_point_desc": (kp.description or "") if kp else "",
            "duration_minutes": minutes,
            "period": (period or "").strip() or None,
            "textbook_version": (textbook_version or "").strip() or None,
            "objectives": (objectives or "").strip(),
            "difficulty": (difficulty or "").strip(),
            "extra_requirements": (extra_requirements or "").strip(),
        }

    # ------------------------------------------------------------ 提示词
    def _context_block(self, ctx: Dict[str, Any]) -> str:
        lines = [
            f"- 年级：{ctx['grade_name']}",
            f"- 学科：{ctx['subject_name']}",
            f"- 教学主题：{ctx['topic']}",
            f"- 课时长度：{ctx['duration_minutes']} 分钟",
        ]
        if ctx.get("textbook_version"):
            lines.append(f"- 教材版本：{ctx['textbook_version']}")
        if ctx.get("period"):
            lines.append(f"- 课次：{ctx['period']}")
        if ctx.get("knowledge_point_name"):
            kp_line = f"- 知识点：{ctx['knowledge_point_name']}"
            if ctx.get("knowledge_point_desc"):
                kp_line += f"（{ctx['knowledge_point_desc'][:200]}）"
            lines.append(kp_line)
        if ctx.get("objectives"):
            lines.append(f"- 教师给定的教学目标（可优化表述，但不得遗漏其要求）：{ctx['objectives'][:500]}")
        if ctx.get("difficulty"):
            lines.append(f"- 期望难度：{ctx['difficulty']}")
        if ctx.get("extra_requirements"):
            lines.append(f"- 其他要求：{ctx['extra_requirements'][:300]}")
        return "\n".join(lines)

    def _llm_head(self, db: Session, user_id: Optional[int], ctx: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        prompt = (
            f"{self._context_block(ctx)}\n\n"
            "请写出这份教案的前半部分。\n"
            """只输出 JSON：{"objectives": "教学目标，按 1./2./3. 分条，覆盖知识与技能、过程与方法、情感态度与价值观三个维度", "key_points": "教学重点，分条", "difficulties": "教学难点，分条并说明学生为什么会卡住", "teaching_preparation": "教学准备，分「教师准备」「学生准备」两段"}\n"""
            "每段都要有实质内容，至少 2 条，不要写空话。"
        )
        try:
            res = self.call_llm(prompt, db=db, user_id=user_id,
                                biz_type="lesson_head", json_mode=True)
        except Exception:  # noqa: BLE001  单段失败不该毁掉整份教案
            return None
        if not res.get("success"):
            return None
        parsed = res.get("parsed")
        return parsed if isinstance(parsed, dict) else None

    def _llm_body(
        self, db: Session, user_id: Optional[int], ctx: Dict[str, Any],
        head: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        minutes = ctx["duration_minutes"]
        head_lines = []
        if head.get("objectives"):
            head_lines.append(f"教学目标：{str(head['objectives'])[:600]}")
        if head.get("key_points"):
            head_lines.append(f"教学重点：{str(head['key_points'])[:300]}")
        if head.get("difficulties"):
            head_lines.append(f"教学难点：{str(head['difficulties'])[:300]}")

        prompt = (
            f"{self._context_block(ctx)}\n\n"
            + ("【已确定的前半部分】\n" + "\n".join(head_lines) + "\n\n" if head_lines else "")
            + "请写出这份教案的后半部分（教学过程、练习、作业、板书）。\n"
            "只输出 JSON：\n"
            '{"stages": [{"name": "环节名", "duration_minutes": 8, '
            '"content": "本环节的设计意图与要点", '
            '"teacher_activity": "教师的具体动作与关键提问原话", '
            '"student_activity": "学生的具体任务与预期表现"}],'
            ' "class_exercise": "课堂练习 2-3 题，含参考答案",'
            ' "homework": "作业，分「必做」「选做」两层",'
            ' "board_design": "板书设计，用缩进文本表示结构与位置"}\n'
            f"硬性要求：stages 至少 4 个环节（含导入、新授、练习、小结），"
            f"各环节 duration_minutes 之和必须等于 {minutes}。"
        )
        try:
            res = self.call_llm(prompt, db=db, user_id=user_id,
                                biz_type="lesson_body", json_mode=True)
        except Exception:  # noqa: BLE001
            return None
        if not res.get("success"):
            return None
        parsed = res.get("parsed")
        return parsed if isinstance(parsed, dict) else None

    # ------------------------------------------------------------ 规则引擎
    def _rule_head(self, ctx: Dict[str, Any]) -> Dict[str, Any]:
        topic = ctx["topic"]
        kp = ctx.get("knowledge_point_name") or topic
        grade = ctx.get("grade_name") or "本年级"
        subject = ctx.get("subject_name") or "本学科"
        base_obj = (ctx.get("objectives") or "").strip()

        objectives = base_obj or "\n".join([
            f"1. 知识与技能：能说出「{kp}」的含义与关键特征，能在{grade}{subject}问题中正确运用。",
            f"2. 过程与方法：经历「观察—猜想—验证—归纳」的探究过程，"
            f"学会用已有知识迁移解决与「{topic}」相关的新问题。",
            f"3. 情感态度与价值观：在探究「{topic}」的过程中体会{subject}的严谨性，"
            f"愿意主动表达自己的思考并倾听同伴意见。",
        ])
        return {
            "objectives": objectives,
            "key_points": (f"1. 「{kp}」的核心内容与适用条件。\n"
                           f"2. 在具体问题中识别并正确运用「{kp}」的步骤。"),
            "difficulties": (f"1. 学生容易把「{kp}」与相近概念混淆，"
                             f"需要在对比辨析中明确边界。\n"
                             f"2. 从理解到运用之间存在落差，需通过变式练习逐步搭桥。"),
            "teaching_preparation": (
                "教师准备：多媒体课件、板书用卡片/磁性贴、分层练习纸、课堂检测题。\n"
                "学生准备：教材、笔记本、草稿纸，课前完成与"
                f"「{kp}」相关的预习任务。"),
        }

    def _rule_body(self, ctx: Dict[str, Any]) -> Dict[str, Any]:
        topic = ctx["topic"]
        kp = ctx.get("knowledge_point_name") or topic
        minutes = ctx["duration_minutes"]
        durations = self._split_duration(minutes, [p for _, p in DEFAULT_STAGE_TEMPLATE])

        contents = {
            "导入新课": (f"用生活情境或旧知复习引出「{topic}」，让学生产生认知冲突，"
                         f"明确本节课要解决的问题。",
                         f"出示情境问题，请 1-2 名学生口答；追问「凭已有知识能不能解决」，"
                         f"在学生卡住处点明本课任务：学习「{kp}」。",
                         "观察情境，尝试用已学知识作答；在无法解决时产生疑问，进入学习状态。"),
            "新课讲授": (f"围绕「{kp}」展开：先建立概念/规则，再通过例题示范运用，"
                         f"最后归纳出可操作的步骤。",
                         f"① 结合实例讲解「{kp}」的含义，板书关键词；"
                         f"② 示范一道典型例题，边做边讲每一步的依据；"
                         f"③ 追问「为什么这一步不能省」，引导学生说出理由；"
                         f"④ 与学生共同归纳解题步骤并板书。",
                         "① 观察实例，用自己的话说出关键特征；② 跟着例题推理，记录步骤；"
                         "③ 回答追问，修正自己的表述；④ 同桌互述归纳出的步骤。"),
            "巩固练习": (f"用基础题—变式题的梯度练习检验「{kp}」的掌握情况，"
                         f"暴露并纠正典型错误。",
                         "先让学生独立完成基础题，巡视收集典型错误；"
                         "再出示变式题，请不同程度的学生板演；针对错误当堂点评，"
                         "强调易错点。",
                         "独立完成基础题；板演变式题；对照点评修改自己的解答，"
                         "在错题旁标注错因。"),
            "课堂小结": (f"回扣教学目标，梳理「{kp}」的知识结构与学习方法。",
                         "提问「这节课你学会了什么」「还有哪里不清楚」，"
                         "根据学生回答补全板书结构图，点明下节课的衔接点。",
                         "口头复述本课要点；提出仍然存在的疑问；补全笔记中的结构图。"),
            "作业布置": ("分层布置作业，兼顾保底与提升。",
                         "说明必做与选做的区别与要求，提示完成时间与检查方式。",
                         "记录作业要求，按自身情况选择选做题。"),
        }

        stages = []
        for (name, _ratio), dur in zip(DEFAULT_STAGE_TEMPLATE, durations):
            content, teacher, student = contents.get(name, ("", "", ""))
            stages.append({
                "name": name, "duration_minutes": dur, "content": content,
                "teacher_activity": teacher, "student_activity": student,
            })

        return {
            "stages": stages,
            "class_exercise": (
                f"1. 基础题：直接运用「{kp}」完成一道标准题。（请补充具体题干）\n"
                f"2. 变式题：改变条件后仍用「{kp}」求解，检验理解深度。（请补充具体题干）\n"
                f"3. 辨析题：给出一个常见错误解法，请指出错在哪一步并改正。\n"
                f"（当前为规则引擎生成，题目需教师补充具体数值与情境。）"),
            "homework": (
                f"必做：教材中与「{topic}」对应的课后练习，巩固「{kp}」的基本运用。\n"
                f"选做：自编一道能用「{kp}」解决的实际问题，并写出完整解答过程。\n"
                f"（当前为规则引擎生成，请按班级实际进度调整题量。）"),
            "board_design": (
                f"{topic}\n"
                f"├─ 核心：{kp}\n"
                f"│   ├─ 含义/规则：\n"
                f"│   └─ 适用条件：\n"
                f"├─ 例题示范（步骤与依据）\n"
                f"│   ├─ 步骤 1：\n"
                f"│   ├─ 步骤 2：\n"
                f"│   └─ 易错提醒：\n"
                f"└─ 方法归纳：\n"
                f"（请教师在课堂上随讲随填）"),
        }

    @staticmethod
    def _split_duration(total: int, ratios: List[float]) -> List[int]:
        """按占比切分时长，保证合计**精确等于** total 且每环 ≥1 分钟。

        不用 int() 截断：45×0.10=4.5 被截成 4，导入环节会系统性地
        比设计占比短（少的时间全部堆到占比最大的环节），
        一节课的节奏就从源头偏了。改为四舍五入后再用差额补偿。
        """
        if not ratios:
            return []
        n = len(ratios)
        if total < n:
            # 课时短于环节数：物理上无法每环 1 分钟，只能均分并接受合计偏差。
            # 正常流程不会到这里（_resolve_context 把课时下限锁在 15 分钟）。
            return [1] * total + [0] * (n - total)

        raw = [total * r for r in ratios]
        out = [max(1, int(x + 0.5)) for x in raw]

        # 差额补偿：优先补/扣占比最大的环节（它对总时长的敏感度最低，
        # 多 1 分钟的观感影响最小），且扣减时不允许低于 1 分钟。
        guard = 0
        while sum(out) != total and guard < 500:
            guard += 1
            diff = total - sum(out)
            if diff > 0:
                out[out.index(max(out))] += 1
            else:
                order = sorted(range(n), key=lambda i: -out[i])
                for i in order:
                    if out[i] > 1:
                        out[i] -= 1
                        break
                else:
                    break  # 全部已到 1 分钟下限，无法再扣
        return out

    # ------------------------------------------------------------ 结构校验
    def _assemble(
        self, ctx: Dict[str, Any], head: Dict[str, Any], body: Dict[str, Any],
        *, mode: str,
    ) -> Dict[str, Any]:
        """合并两段结果并做结构校验补全，返回前端可直接渲染的教案。"""
        data: Dict[str, Any] = {
            "title": self._make_title(ctx),
            "topic": ctx["topic"],
            "grade_id": ctx.get("grade_id"),
            "grade_name": ctx.get("grade_name"),
            "subject_id": ctx.get("subject_id"),
            "subject_name": ctx.get("subject_name"),
            "textbook_version": ctx.get("textbook_version"),
            "knowledge_point_id": ctx.get("knowledge_point_id"),
            "knowledge_point_name": ctx.get("knowledge_point_name"),
            "duration_minutes": ctx["duration_minutes"],
            "period": ctx.get("period"),
            "objectives": self._as_text(head.get("objectives")),
            "key_points": self._as_text(head.get("key_points")),
            "difficulties": self._as_text(head.get("difficulties")),
            "teaching_preparation": self._as_text(head.get("teaching_preparation")),
            "stages": self._normalize_stages(body.get("stages"), ctx),
            "class_exercise": self._as_text(body.get("class_exercise")),
            "homework": self._as_text(body.get("homework")),
            "board_design": self._as_text(body.get("board_design")),
        }

        missing: List[str] = []
        warnings: List[str] = []

        # 章节级缺漏补全：模型漏了哪节就补哪节，并如实记账。
        rule_head = self._rule_head(ctx) if mode == "llm" else {}
        rule_body = self._rule_body(ctx) if mode == "llm" else {}
        for field in ("objectives", "key_points", "difficulties", "teaching_preparation"):
            if len(data[field]) < MIN_SECTION_CHARS:
                if mode == "llm" and rule_head.get(field):
                    data[field] = rule_head[field]
                if not data[field]:
                    data[field] = SECTION_LABELS[field] + "（生成内容缺失，请补充）"
                missing.append(SECTION_LABELS[field])

        for field in ("class_exercise", "homework", "board_design"):
            if len(data[field]) < MIN_SECTION_CHARS:
                if mode == "llm" and rule_body.get(field):
                    data[field] = rule_body[field]
                if not data[field]:
                    data[field] = SECTION_LABELS[field] + "（生成内容缺失，请补充）"
                missing.append(SECTION_LABELS[field])

        if not data["stages"]:
            fallback_stages = (self._rule_body(ctx) if mode == "rule" else self._rule_body(ctx))["stages"]
            data["stages"] = [
                {"name": s["name"], "duration_minutes": s["duration_minutes"],
                 "content": s["content"], "teacher_activity": s["teacher_activity"],
                 "student_activity": s["student_activity"], "sort_order": i}
                for i, s in enumerate(fallback_stages)
            ]
            missing.append(SECTION_LABELS["stages"])

        # 时长校验：LLM 常把环节时长写成合计 60（课时 45）。不修正会让教案
        # 在真实课堂上直接超时，属于「看着完整、上课用不了」的隐性缺陷。
        total = sum(s["duration_minutes"] for s in data["stages"])
        if total != ctx["duration_minutes"]:
            warnings.append(
                f"各环节时长合计 {total} 分钟，与课时 {ctx['duration_minutes']} 分钟不一致，"
                f"已按原占比缩放")
            data["stages"] = self._rescale_stages(data["stages"], ctx["duration_minutes"])

        # 师生活动缺失：这篇教案就退化成「教学流程提纲」，明确提示。
        empty_activity = [s["name"] for s in data["stages"]
                          if not s.get("teacher_activity") or not s.get("student_activity")]
        if empty_activity:
            warnings.append("以下环节缺少师生活动描述：" + "、".join(empty_activity[:6]))

        generation = {
            "mode": mode,
            "is_fallback": mode == "rule",
            "missing": missing,
            "warnings": warnings,
            "stage_total_minutes": sum(s["duration_minutes"] for s in data["stages"]),
            "llm_enabled_hint": mode == "llm",
        }
        data["generation"] = generation

        # 质量评级：给前端一个「要不要重点复核」的信号，避免用户盲信 AI 产物。
        if mode == "rule" or len(missing) >= 3:
            data["generation"]["quality"] = "low"
        elif missing or warnings:
            data["generation"]["quality"] = "medium"
        else:
            data["generation"]["quality"] = "high"

        return data

    @staticmethod
    def _make_title(ctx: Dict[str, Any]) -> str:
        """标题：学科 + 课题（与教务惯用的「学科-课题」命名对齐）。"""
        parts = [p for p in (ctx.get("subject_name"), ctx["topic"]) if p]
        title = "－".join(parts) if parts else ctx["topic"]
        if ctx.get("period"):
            title = f"{title}（{ctx['period']}）"
        return title[:128]

    @staticmethod
    def _as_text(value: Any) -> str:
        """把模型可能给出的 str / list / dict 统一成可显示的文本。

        模型不稳定时会把 objectives 输出成数组、把 stages 输出成对象，
        直接 str() 会得到 "{'a': 1}" 这种半 Python 半 JSON 的脏文本。
        """
        if value is None:
            return ""
        if isinstance(value, str):
            return value.strip()
        if isinstance(value, (list, tuple)):
            items = []
            for i, v in enumerate(value, 1):
                if isinstance(v, str):
                    items.append(f"{i}. {v.strip()}")
                elif isinstance(v, dict):
                    name = v.get("name") or v.get("title") or ""
                    desc = v.get("description") or v.get("content") or ""
                    items.append(f"{i}. {name}：{desc}".strip("："))
                elif v is not None:
                    items.append(f"{i}. {v}")
            return "\n".join(x for x in items if x.strip())
        if isinstance(value, dict):
            return json.dumps(value, ensure_ascii=False, indent=2)
        return str(value).strip()

    def _normalize_stages(self, raw: Any, ctx: Dict[str, Any]) -> List[Dict[str, Any]]:
        """把模型输出的 stages 规范成统一结构，过滤空环节。"""
        if isinstance(raw, dict):  # 有些模型会返回 {"导入": {...}}
            raw = [{"name": k, **v} if isinstance(v, dict) else {"name": k, "content": str(v)}
                   for k, v in raw.items()]
        if not isinstance(raw, list):
            return []

        out: List[Dict[str, Any]] = []
        for i, item in enumerate(raw):
            if isinstance(item, str):
                item = {"name": item}
            if not isinstance(item, dict):
                continue
            name = self._as_text(item.get("name") or item.get("stage") or "").strip()
            if not name:
                continue
            try:
                dur = int(float(item.get("duration_minutes") or item.get("duration") or 0))
            except (TypeError, ValueError):
                dur = 0
            out.append({
                "name": name[:32],
                "duration_minutes": max(1, dur),
                "content": self._as_text(item.get("content") or item.get("description")),
                "teacher_activity": self._as_text(
                    item.get("teacher_activity") or item.get("teacher")),
                "student_activity": self._as_text(
                    item.get("student_activity") or item.get("student")),
                "sort_order": i,
            })

        # 环节不足 3 个时补足模板环节 —— 少于 3 个环节的「教学过程」
        # 在实际上课中没有可操作性。
        # ⚠️ 补足必须用**真实 ctx**：早期实现传的是空 topic/空知识点，
        # 补出来的环节正文成了「围绕「」展开」，看着有 5 个环节却全是残句。
        # 补足优先级：先补**收尾**（小结/作业），再补导入与练习。
        # 只按模板顺序取前几个会把「热身→探究」补成「导入→新授→练习」，
        # 一节课没有小结也没有作业，直接不能用。
        if out and len(out) < 3:
            rule_by_name = {s["name"]: s for s in self._rule_body(ctx)["stages"]}
            for name in STAGE_FILL_ORDER:
                if len(out) >= 5:
                    break
                s = rule_by_name.get(name)
                if not s or self._stage_name_taken(name, out):
                    continue
                out.append(dict(s, sort_order=len(out)))
        return out

    @staticmethod
    def _stage_name_taken(name: str, existing: List[Dict[str, Any]]) -> bool:
        """判断环节名是否已被占用（含「导入」与「导入新课」这类包含关系）。

        只做精确比对时，模型给出「导入」、模板补「导入新课」，
        一节课会同时出现两个导入环节 —— 时长和内容都重复。
        """
        n = name.strip()
        for s in existing:
            e = (s.get("name") or "").strip()
            if not e:
                continue
            if e == n or e in n or n in e:
                return True
        return False

    def _rescale_stages(self, stages: List[Dict[str, Any]], minutes: int) -> List[Dict[str, Any]]:
        """按原占比把环节时长缩放到课时长度，保证合计精确相等且每环 ≥1 分钟。"""
        total = sum(s["duration_minutes"] for s in stages) or 1
        ratios = [s["duration_minutes"] / total for s in stages]
        new_durations = self._split_duration(minutes, ratios)
        for s, d in zip(stages, new_durations):
            s["duration_minutes"] = d
        return stages

    @staticmethod
    def _progress(cb: Optional[Callable[[int, str], None]], pct: int, stage: str) -> None:
        """上报进度。回调失败绝不能影响生成本身。"""
        if cb is None:
            return
        try:
            cb(pct, stage)
        except Exception:  # noqa: BLE001
            pass


# ---------------------------------------------------------------- 文本导出
def render_markdown(plan: Dict[str, Any]) -> str:
    """把教案渲染成 Markdown（导出用）。前端与后端共用同一套章节顺序。"""
    meta = "｜".join(str(x) for x in (
        plan.get("grade_name"), plan.get("subject_name"),
        plan.get("textbook_version"), plan.get("period"),
    ) if x)

    lines: List[str] = [f"# {plan.get('title') or plan.get('topic') or '教案'}", ""]
    if meta:
        lines += [f"> {meta}　课时：{plan.get('duration_minutes', 45)} 分钟", ""]

    sections = (
        ("一、教学目标", "objectives"),
        ("二、教学重点", "key_points"),
        ("三、教学难点", "difficulties"),
        ("四、教学准备", "teaching_preparation"),
    )
    for heading, key in sections:
        lines += [f"## {heading}", "", str(plan.get(key) or "（未填写）"), ""]

    lines += ["## 五、教学过程", ""]
    stages = plan.get("stages") or []
    if stages:
        lines += ["| 环节 | 时长 | 教师活动 | 学生活动 |", "| --- | --- | --- | --- |"]
        for s in stages:
            lines.append(
                f"| {s.get('name', '')} | {s.get('duration_minutes', 0)} 分钟 | "
                f"{_one_line(s.get('teacher_activity'))} | {_one_line(s.get('student_activity'))} |")
        lines.append("")
        for i, s in enumerate(stages, 1):
            lines += [f"### 5.{i} {s.get('name', '')}（{s.get('duration_minutes', 0)} 分钟）", ""]
            if s.get("content"):
                lines += [f"**设计意图**：{s['content']}", ""]
            if s.get("teacher_activity"):
                lines += ["**教师活动**：", s["teacher_activity"], ""]
            if s.get("student_activity"):
                lines += ["**学生活动**：", s["student_activity"], ""]
    else:
        lines += ["（未填写）", ""]

    for heading, key in (("六、课堂练习", "class_exercise"), ("七、作业布置", "homework"),
                         ("八、板书设计", "board_design")):
        lines += [f"## {heading}", "", str(plan.get(key) or "（未填写）"), ""]

    gen = plan.get("generation") or {}
    if gen.get("mode") == "rule":
        lines += ["---", "",
                  "> 本教案由规则引擎生成（未配置大模型）。题目与情境需要教师补充具体内容。", ""]
    return "\n".join(lines).rstrip() + "\n"


def _one_line(text: Any, limit: int = 60) -> str:
    """表格单元格里不能有换行与竖线。"""
    s = re.sub(r"\s+", " ", str(text or "")).replace("|", "/").strip()
    return (s[:limit] + "…") if len(s) > limit else s
