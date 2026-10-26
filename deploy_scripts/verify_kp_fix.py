"""验证 knowledge_point_id 外键修复（在容器内跑，用真实 DB）。

覆盖：
 1. 复现原缺陷：未经校验直接写模型给的 id → 外键约束失败
 2. _resolve_kp_id 三重判据：不存在的 id / 跨学科 id / 有效 id
 3. 名称回退：id 无效但名称有效 → 按名匹配
 4. 上下文候选知识点不再被 level==3 过滤成空
"""
import sys

sys.path.insert(0, "/app")

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.agents.question_agent import QuestionGeneratorAgent
from app.core.database import SessionLocal
from app.models import KnowledgePoint, Question, Subject

ok = True


def chk(label, cond, extra=""):
    global ok
    ok = ok and bool(cond)
    print(f"  {'✓' if cond else '✗'} {label} {extra}")


with SessionLocal() as db:
    print("=== 0) 数据现状 ===")
    levels = db.execute(
        select(KnowledgePoint.level).distinct()
    ).scalars().all()
    n3 = db.scalar(
        select(__import__("sqlalchemy").func.count())
        .select_from(KnowledgePoint)
        .where(KnowledgePoint.level == 3)
    )
    print(f"  知识点 level 取值={levels}  level=3 条数={n3}")
    subject = db.scalar(select(Subject).where(Subject.name == "数学").limit(1))
    sid = subject.id
    kps = db.scalars(
        select(KnowledgePoint).where(
            KnowledgePoint.subject_id == sid,
            KnowledgePoint.is_active.is_(True),
        ).order_by(KnowledgePoint.level.desc(), KnowledgePoint.id).limit(12)
    ).all()
    print(f"  学科「数学」id={sid} grade_id={subject.grade_id} 候选知识点={len(kps)} 个")
    chk("修复后候选知识点非空（旧逻辑 level==3 会是 0 个）", len(kps) > 0)

    valid_kp = kps[0] if kps else None
    other_subject = db.scalar(
        select(Subject).where(Subject.id != sid).limit(1)
    )
    other_kp = None
    if other_subject:
        other_kp = db.scalar(
            select(KnowledgePoint).where(
                KnowledgePoint.subject_id == other_subject.id
            ).limit(1)
        )

    print("\n=== 1) 复现原缺陷（未校验直接写库）===")
    bogus_id = 999999
    q = Question(
        type="single", stem="【复现用】外键约束失败复现题", options=None,
        answer="A", analysis=None, score=5.0, difficulty="medium",
        grade_id=subject.grade_id, subject_id=sid,
        knowledge_point_id=bogus_id,  # 模型编造的 id
        bank_type="private", owner_id=1, status="draft",
        fingerprint="e2e-fk-repro", source="ai",
    )
    db.add(q)
    try:
        db.commit()
        print("  ! 竟然插入成功（本用例前提不成立）")
        db.rollback()
    except IntegrityError as e:
        db.rollback()
        print(f"  ✓ 如期复现 IntegrityError: {str(e).splitlines()[0][:70]}")
        chk("原缺陷可复现（未校验模型 id → 外键失败）", True)

    print("\n=== 2) _resolve_kp_id 三重判据 ===")
    agent = QuestionGeneratorAgent()
    r = agent._resolve_kp_id(db, bogus_id, sid)
    chk("不存在的 id → 置空（不再写库报错）", r is None, f"-> {r}")

    if valid_kp:
        r = agent._resolve_kp_id(db, valid_kp.id, sid)
        chk("有效且同学科的 id → 原样采用", r == valid_kp.id, f"-> {r}")

    if other_kp:
        r = agent._resolve_kp_id(db, other_kp.id, sid)
        chk("跨学科 id → 置空", r is None, f"-> {r} (该 id 属 subject {other_kp.subject_id})")

    r = agent._resolve_kp_id(db, "abc", sid)
    chk("非数字 id → 置空", r is None, f"-> {r}")

    r = agent._resolve_kp_id(db, None, sid, fallback_id=valid_kp.id if valid_kp else None)
    chk("模型未给 id → 回退到请求指定的知识点", r == (valid_kp.id if valid_kp else None), f"-> {r}")

    print("\n=== 3) 名称回退（id 无效但名称有效）===")
    if valid_kp:
        r = agent._resolve_kp_id(db, bogus_id, sid, kp_name=valid_kp.name)
        chk("按名称在同学科内匹配回知识点", r == valid_kp.id, f"-> {r} (name={valid_kp.name})")
    r = agent._resolve_kp_id(db, bogus_id, sid, kp_name="不存在的知识点名称XYZ")
    chk("名称也匹配不上 → 置空（题目照常入库，仅不挂知识点）", r is None, f"-> {r}")

    print("\n=== 4) 端到端：校验后的 id 可安全落库 ===")
    kp_id = agent._resolve_kp_id(db, bogus_id, sid, kp_name=valid_kp.name if valid_kp else None)
    q2 = Question(
        type="single", stem="【验证用】修复后带知识点落库", options=None,
        answer="A", analysis=None, score=5.0, difficulty="medium",
        grade_id=subject.grade_id, subject_id=sid,
        knowledge_point_id=kp_id, bank_type="private", owner_id=1,
        status="draft", fingerprint="e2e-fk-fixed", source="ai",
    )
    db.add(q2)
    try:
        db.commit()
        print(f"  ✓ 修复后落库成功（knowledge_point_id={kp_id}）")
        db.delete(q2)
        db.commit()
    except IntegrityError as e:
        db.rollback()
        print(f"  ✗ 仍然失败: {str(e).splitlines()[0][:80]}")
        ok = False

print("\n" + ("全部通过 ✅" if ok else "存在失败 ❌"))
sys.exit(0 if ok else 1)
