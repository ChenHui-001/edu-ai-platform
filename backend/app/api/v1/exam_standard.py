"""命题标准管理接口（管理员可视化配置）。

前缀 `/question/standards`。需求要求「题型、分值、难度标准支持管理员后台
可视化配置，无需修改代码」，因此这里提供完整 CRUD + 重置为内置标准。

权限：
- 读取：paper:list（组卷时要选标准，教师必须能读）
- 写入：sys_admin（标准是组织级配置，不开放给普通教师）

与既有试卷接口完全隔离，不改动 question.py 的任何行为。
"""
import json
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import require_perm
from app.core.database import get_db
from app.core.exception import BusinessException, NotFoundException, PermissionException
from app.models import ExamStandard, Grade, Paper, Subject, User
from app.services.exam_standard_seed import (
    DEFAULT_DIFFICULTY, VALID_TYPES, seed_exam_standards,
)
from app.utils.common import PageParams, dictify, ok

router = APIRouter(prefix="/question/standards", tags=["命题标准"])

EXAM_TYPE_LABEL = {
    "final": "期末学业水平考试",
    "hsee": "学业水平考试（中考）",
    "unit": "单元测试",
    "monthly": "月考",
    "custom": "自定义",
}


def _is_sys_admin(user: User) -> bool:
    return "sys_admin" in (user.role_codes or [])


def _require_admin(user: User) -> None:
    if not _is_sys_admin(user):
        raise PermissionException("仅系统管理员可配置命题标准")


def _loads(value: Optional[str], default: Any = None) -> Any:
    if not value:
        return default
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return default


def _validate_sections(sections: Any, total_score: float) -> List[Dict[str, Any]]:
    """校验题型结构：合法题型 + 正数题量分值 + 小计等于总分。

    小计必须等于总分：否则卷面分与「总分 100」自相矛盾，
    发布任务时及格线（总分×60%）会算错，且导出卷面分数加不平。
    """
    if not isinstance(sections, list) or not sections:
        raise BusinessException("题型结构不能为空")
    cleaned: List[Dict[str, Any]] = []
    subtotal = 0.0
    for idx, raw in enumerate(sections, start=1):
        if not isinstance(raw, dict):
            raise BusinessException("题型结构格式错误")
        code = str(raw.get("code") or "").strip().lower()
        if code not in VALID_TYPES:
            raise BusinessException(
                f"第 {idx} 个大题题型不合法：{code!r}，可选值 {'/'.join(sorted(VALID_TYPES))}")
        try:
            count = int(raw.get("count") or 0)
            score_per = float(raw.get("score_per") or 0)
        except (TypeError, ValueError):
            raise BusinessException(f"第 {idx} 个大题的题量/分值必须为数字")
        if count <= 0:
            raise BusinessException(f"第 {idx} 个大题题量必须大于 0")
        if score_per <= 0:
            raise BusinessException(f"第 {idx} 个大题单题分值必须大于 0")
        difficulty = str(raw.get("difficulty") or "medium").strip()
        if difficulty not in ("easy", "medium", "hard"):
            raise BusinessException(f"第 {idx} 个大题难度不合法：{difficulty!r}")
        cleaned.append({
            "code": code,
            "name": str(raw.get("name") or "").strip()[:64] or f"第{idx}大题",
            "count": count,
            "score_per": round(score_per, 2),
            "difficulty": difficulty,
            "sort": idx,
        })
        subtotal += count * score_per
    if abs(round(subtotal, 2) - round(float(total_score), 2)) > 0.01:
        raise BusinessException(
            f"题型分值小计 {round(subtotal, 2)} 与总分 {total_score} 不一致，请调整题量或单题分值")
    return cleaned


def _validate_difficulty(ratio: Any) -> Dict[str, int]:
    """难度分布：三项齐全、非负、合计 100。"""
    if ratio in (None, ""):
        return dict(DEFAULT_DIFFICULTY)
    if not isinstance(ratio, dict):
        raise BusinessException("难度分布格式错误")
    result: Dict[str, int] = {}
    for key in ("easy", "medium", "hard"):
        try:
            value = int(ratio.get(key) or 0)
        except (TypeError, ValueError):
            raise BusinessException(f"难度 {key} 必须为整数")
        if value < 0 or value > 100:
            raise BusinessException(f"难度 {key} 需在 0~100 之间")
        result[key] = value
    total = sum(result.values())
    if total != 100:
        raise BusinessException(f"难度分布合计必须为 100，当前为 {total}")
    return result


def _serialize(std: ExamStandard, paper_count: int = 0) -> Dict[str, Any]:
    d = dictify(std)
    d["sections"] = _loads(std.sections, [])
    d["difficulty_ratio"] = _loads(std.difficulty_ratio, dict(DEFAULT_DIFFICULTY))
    d["exam_type_label"] = EXAM_TYPE_LABEL.get(std.exam_type, std.exam_type)
    d["item_count"] = sum(int(s.get("count") or 0) for s in d["sections"])
    d["paper_count"] = paper_count
    # 是否被人工改过：seed 源可被「重置为内置」覆盖，manual 源受保护
    d["editable"] = True
    return d


@router.get("", summary="命题标准列表")
def list_standards(
    params: PageParams = Depends(),
    stage: Optional[str] = None,
    subject_name: Optional[str] = None,
    exam_type: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_perm("paper:list")),
):
    stmt = select(ExamStandard)
    if stage:
        stmt = stmt.where(ExamStandard.stage == stage)
    if subject_name:
        stmt = stmt.where(ExamStandard.subject_name == subject_name)
    if exam_type:
        stmt = stmt.where(ExamStandard.exam_type == exam_type)
    if is_active is not None:
        stmt = stmt.where(ExamStandard.is_active.is_(bool(is_active)))

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(
        stmt.order_by(ExamStandard.stage, ExamStandard.sort, ExamStandard.id)
        .offset(params.offset).limit(params.page_size)
    ).all()

    # 引用计数：标准被多少份试卷使用（删除前提示用）
    ids = [s.id for s in rows]
    usage: Dict[int, int] = {}
    if ids:
        usage = dict(db.execute(
            select(Paper.standard_id, func.count())
            .where(Paper.standard_id.in_(ids)).group_by(Paper.standard_id)
        ).all())

    return ok({
        "items": [_serialize(s, usage.get(s.id, 0)) for s in rows],
        "total": total, "page": params.page,
        "exam_type_label": EXAM_TYPE_LABEL,
    })


@router.get("/options", summary="组卷用标准选项（按学段学科分组）")
def standard_options(
    stage: Optional[str] = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_perm("paper:list")),
):
    """组卷向导用：只返回启用中的标准，含展开后的题型结构。"""
    stmt = select(ExamStandard).where(ExamStandard.is_active.is_(True))
    if stage:
        stmt = stmt.where(ExamStandard.stage == stage)
    rows = db.scalars(
        stmt.order_by(ExamStandard.stage, ExamStandard.sort, ExamStandard.id)).all()
    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for s in rows:
        grouped.setdefault(s.stage, []).append(_serialize(s))
    return ok({"by_stage": grouped, "total": len(rows)})


@router.get("/{std_id}", summary="命题标准详情")
def get_standard(
    std_id: int, db: Session = Depends(get_db),
    user: User = Depends(require_perm("paper:list")),
):
    std = db.get(ExamStandard, std_id)
    if not std:
        raise NotFoundException("命题标准不存在")
    return ok(_serialize(std))


@router.post("", summary="新建命题标准")
def create_standard(
    data: Dict[str, Any] = Body(...), db: Session = Depends(get_db),
    user: User = Depends(require_perm("paper:write")),
):
    _require_admin(user)
    name = str(data.get("name") or "").strip()
    if not name:
        raise BusinessException("标准名称不能为空")
    stage = str(data.get("stage") or "").strip()
    if stage not in ("primary", "junior"):
        raise BusinessException("学段仅支持 primary / junior")
    subject_name = str(data.get("subject_name") or "").strip()
    if not subject_name:
        raise BusinessException("请选择学科")
    exam_type = str(data.get("exam_type") or "final").strip()
    if exam_type not in EXAM_TYPE_LABEL:
        raise BusinessException(f"考试类型仅支持 {'/'.join(EXAM_TYPE_LABEL)}")

    try:
        total_score = float(data.get("total_score") or 100)
    except (TypeError, ValueError):
        raise BusinessException("总分必须为数字")
    if total_score <= 0:
        raise BusinessException("总分必须大于 0")
    try:
        duration = int(data.get("duration") or 90)
    except (TypeError, ValueError):
        raise BusinessException("考试时长必须为整数")
    if duration < 1 or duration > 300:
        raise BusinessException("考试时长需在 1~300 分钟之间")

    sections = _validate_sections(data.get("sections"), total_score)
    difficulty = _validate_difficulty(data.get("difficulty_ratio"))

    exists = db.scalar(select(ExamStandard.id).where(
        ExamStandard.region == "hubei", ExamStandard.stage == stage,
        ExamStandard.subject_name == subject_name,
        ExamStandard.exam_type == exam_type,
    ))
    if exists:
        raise BusinessException(
            f"已存在「{stage}/{subject_name}/{exam_type}」的标准，请直接编辑该标准")

    std = ExamStandard(
        name=name[:128], region="hubei", stage=stage,
        subject_name=subject_name, exam_type=exam_type,
        total_score=total_score, duration=duration,
        sections=json.dumps(sections, ensure_ascii=False),
        difficulty_ratio=json.dumps(difficulty, ensure_ascii=False),
        description=str(data.get("description") or "")[:2000] or None,
        is_active=bool(data.get("is_active", True)),
        is_default=bool(data.get("is_default", False)),
        source="manual", owner_id=user.id, sort=int(data.get("sort") or 99),
    )
    db.add(std)
    if std.is_default:
        _clear_other_defaults(db, std)
    db.commit()
    db.refresh(std)
    return ok({"id": std.id}, message="命题标准已创建")


def _clear_other_defaults(db: Session, std: ExamStandard) -> None:
    """同一 学段+学科 只能有一个默认标准。"""
    db.execute(
        ExamStandard.__table__.update()
        .where(
            ExamStandard.stage == std.stage,
            ExamStandard.subject_name == std.subject_name,
            ExamStandard.id != std.id,
        )
        .values(is_default=False)
    )


@router.put("/{std_id}", summary="编辑命题标准")
def update_standard(
    std_id: int, data: Dict[str, Any] = Body(...), db: Session = Depends(get_db),
    user: User = Depends(require_perm("paper:write")),
):
    _require_admin(user)
    std = db.get(ExamStandard, std_id)
    if not std:
        raise NotFoundException("命题标准不存在")

    if "name" in data:
        name = str(data.get("name") or "").strip()
        if not name:
            raise BusinessException("标准名称不能为空")
        std.name = name[:128]

    # 总分与题型结构必须一起校验：单改总分会让小计对不上
    new_total = std.total_score
    if "total_score" in data:
        try:
            new_total = float(data.get("total_score"))
        except (TypeError, ValueError):
            raise BusinessException("总分必须为数字")
        if new_total <= 0:
            raise BusinessException("总分必须大于 0")
    if "sections" in data:
        sections = _validate_sections(data.get("sections"), new_total)
        std.sections = json.dumps(sections, ensure_ascii=False)
    elif "total_score" in data:
        # 只改总分：现有结构必须仍能加平，否则拒绝
        _validate_sections(_loads(std.sections, []), new_total)
    std.total_score = new_total

    if "duration" in data:
        try:
            duration = int(data.get("duration"))
        except (TypeError, ValueError):
            raise BusinessException("考试时长必须为整数")
        if duration < 1 or duration > 300:
            raise BusinessException("考试时长需在 1~300 分钟之间")
        std.duration = duration
    if "difficulty_ratio" in data:
        std.difficulty_ratio = json.dumps(
            _validate_difficulty(data.get("difficulty_ratio")), ensure_ascii=False)
    if "description" in data:
        std.description = str(data.get("description") or "")[:2000] or None
    if "is_active" in data:
        std.is_active = bool(data.get("is_active"))
    if "is_default" in data:
        std.is_default = bool(data.get("is_default"))
        if std.is_default:
            _clear_other_defaults(db, std)
    if "sort" in data:
        std.sort = int(data.get("sort") or 0)

    # 管理员改过就标记为 manual：后续「重置内置」不会覆盖手工配置
    std.source = "manual"
    std.owner_id = user.id
    db.commit()
    return ok({"id": std.id}, message="命题标准已更新")


@router.delete("/{std_id}", summary="删除命题标准")
def delete_standard(
    std_id: int, db: Session = Depends(get_db),
    user: User = Depends(require_perm("paper:write")),
):
    _require_admin(user)
    std = db.get(ExamStandard, std_id)
    if not std:
        raise NotFoundException("命题标准不存在")
    # 已被试卷引用则拒绝：删了标准，那些试卷就失去命题依据，
    # 「重新按标准校验」与细目表导出都会失效。
    used = db.scalar(
        select(func.count()).select_from(Paper).where(Paper.standard_id == std_id)
    ) or 0
    if used:
        raise BusinessException(
            f"该标准已被 {used} 份试卷引用，删除会使其失去命题依据；"
            "请改用「停用」（is_active=false）")
    db.delete(std)
    db.commit()
    return ok(message="命题标准已删除")


@router.post("/{std_id}/duplicate", summary="复制命题标准")
def duplicate_standard(
    std_id: int, data: Dict[str, Any] = Body(default={}),
    db: Session = Depends(get_db),
    user: User = Depends(require_perm("paper:write")),
):
    """基于现有标准改一份新的（改考试类型或学科）。"""
    _require_admin(user)
    src = db.get(ExamStandard, std_id)
    if not src:
        raise NotFoundException("命题标准不存在")
    exam_type = str(data.get("exam_type") or "custom").strip()
    if exam_type not in EXAM_TYPE_LABEL:
        raise BusinessException("考试类型不合法")
    subject_name = str(data.get("subject_name") or src.subject_name).strip()

    exists = db.scalar(select(ExamStandard.id).where(
        ExamStandard.region == src.region, ExamStandard.stage == src.stage,
        ExamStandard.subject_name == subject_name,
        ExamStandard.exam_type == exam_type,
    ))
    if exists:
        raise BusinessException("目标维度上已存在标准，请直接编辑")

    new = ExamStandard(
        name=(str(data.get("name") or f"{src.name}（副本）"))[:128],
        region=src.region, stage=src.stage, subject_name=subject_name,
        exam_type=exam_type, total_score=src.total_score, duration=src.duration,
        sections=src.sections, difficulty_ratio=src.difficulty_ratio,
        description=src.description, is_active=True, is_default=False,
        source="manual", owner_id=user.id, sort=src.sort,
    )
    db.add(new)
    db.commit()
    db.refresh(new)
    return ok({"id": new.id}, message="已复制命题标准")


@router.post("/generate-missing", summary="为缺失学科批量生成标准草案")
def generate_missing_standards(
    db: Session = Depends(get_db),
    user: User = Depends(require_perm("paper:write")),
):
    """给「有学科但没有命题标准」的组合各生成一条草案（幂等）。

    为什么需要它：内置种子只覆盖小学 4 科 / 初中 6 科，而中小学实际开设
    十几门学科。缺标准的学科在组卷时会落到通用结构兜底（结构不权威），
    教师也没有可编辑的基准。这里按学段学科一次性铺出草案，管理员再按
    教研要求改分值/题量即可，避免逐个手填。

    草案口径（全部可编辑，**不是权威结构**）：
    - 学段：由 edu_grade.stage 推导（primary/junior）
    - 考试类型：小学 final（期末）、初中 hsee（学业水平考试），与内置种子一致
    - 总分：初中语数英 120，物理 70、化学 50、道法/历史 60、地理/生物 50，
      其余 100；小学统一 100
    - 时长：小学 90 分钟；初中 120 分卷 120 分钟、其余 60 分钟
    - 题型结构：与组卷兜底**同一实现**（paper_compose_service.generic_sections）
    """
    from app.services.paper_compose_service import generic_sections

    _require_admin(user)

    # 1) 枚举真实存在的 (stage, subject_name) —— 以学科表为准，不凭空造学科
    pairs = db.execute(
        select(Grade.stage, Subject.name)
        .join(Subject, Subject.grade_id == Grade.id)
        .where(Subject.is_active.is_(True))
        .distinct()
    ).all()

    existing = {
        (s, n, t) for s, n, t in db.execute(
            select(ExamStandard.stage, ExamStandard.subject_name, ExamStandard.exam_type)
        ).all()
    }

    junior_score = {"物理": 70, "化学": 50, "道德与法治": 60,
                    "历史": 60, "地理": 50, "生物": 50}
    stage_label = {"primary": "小学", "junior": "初中"}

    created: List[Dict[str, Any]] = []
    skipped = 0
    for stage, subject_name in sorted(set((str(s or ""), str(n or "")) for s, n in pairs)):
        if not stage or not subject_name:
            continue
        exam_type = "final" if stage == "primary" else "hsee"
        if (stage, subject_name, exam_type) in existing:
            skipped += 1
            continue
        if stage == "primary":
            total = 100.0
            duration = 90
        else:
            total = float(120 if subject_name in ("语文", "数学", "英语")
                          else junior_score.get(subject_name, 100))
            duration = 120 if total >= 120 else 60
        sections = generic_sections(total)
        std = ExamStandard(
            name=f"湖北省{stage_label.get(stage, '')}{subject_name}"
                 f"{EXAM_TYPE_LABEL.get(exam_type, '')}（草案）"[:128],
            region="hubei", stage=stage, subject_name=subject_name,
            exam_type=exam_type, total_score=total, duration=duration,
            sections=json.dumps(sections, ensure_ascii=False),
            difficulty_ratio=json.dumps(DEFAULT_DIFFICULTY, ensure_ascii=False),
            description="系统按通用结构自动生成的草案：题量/分值请按教研要求修订。",
            is_active=True, is_default=True,
            # 用 manual 而不是新造 source 值：reset 只认 seed，
            # 草案本就不该有"恢复内置值"的语义（它没有内置值）。
            source="manual", owner_id=user.id, sort=99,
        )
        db.add(std)
        db.flush()
        _clear_other_defaults(db, std)
        existing.add((stage, subject_name, exam_type))
        created.append({
            "id": std.id, "stage": stage, "subject_name": subject_name,
            "exam_type": exam_type, "total_score": total, "duration": duration,
        })

    db.commit()
    if not created:
        return ok({"created": [], "created_count": 0, "skipped": skipped},
                  message=f"没有缺失的标准（已覆盖 {skipped} 个学段学科组合）")
    return ok({"created": created, "created_count": len(created), "skipped": skipped},
              message=f"已生成 {len(created)} 条标准草案，请按教研要求核对分值")


@router.post("/seed", summary="播种/补齐内置湖北标准")
def reseed_standards(
    force: bool = False, db: Session = Depends(get_db),
    user: User = Depends(require_perm("paper:write")),
):
    """补齐缺失的内置标准。

    force=False（默认）：只补不覆盖——已被管理员改过的标准不动。
    force=True：忽略标记位重新播种，但仍跳过已存在的维度，
                因此**不会**覆盖管理员的任何修改，只是补缺。
                要恢复某条标准的内置值，走 /{id}/reset。
    """
    _require_admin(user)
    result = seed_exam_standards(db, force=force)
    return ok(result, message=(
        f"已补齐 {result['created']} 条标准，跳过 {result['skipped']} 条已存在"
    ))


@router.post("/{std_id}/reset", summary="重置为内置标准")
def reset_standard(
    std_id: int, db: Session = Depends(get_db),
    user: User = Depends(require_perm("paper:write")),
):
    """把某条标准恢复为代码内置值（管理员改坏了时的兜底）。"""
    _require_admin(user)
    std = db.get(ExamStandard, std_id)
    if not std:
        raise NotFoundException("命题标准不存在")

    from app.services.exam_standard_seed import _JUNIOR, _PRIMARY

    pool = _PRIMARY if std.stage == "primary" else _JUNIOR
    builtin = next((r for r in pool if r["subject_name"] == std.subject_name
                    and r["exam_type"] == std.exam_type), None)
    if not builtin:
        raise BusinessException("该标准没有对应的内置版本，无法重置")

    std.name = builtin["name"]
    std.total_score = float(builtin["total_score"])
    std.duration = int(builtin["duration"])
    std.sections = json.dumps(builtin["sections"], ensure_ascii=False)
    std.difficulty_ratio = json.dumps(DEFAULT_DIFFICULTY, ensure_ascii=False)
    std.description = builtin.get("description")
    std.source = "seed"
    db.commit()
    return ok({"id": std.id}, message="已恢复为内置标准")
