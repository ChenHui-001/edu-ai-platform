"""P0-3 反向验证：异步组卷路径必须与同步路径共用参数解析。

旧实现的判定方式：`_run_compose_job` 里没有 `_ai_resolve_params` 调用，
直接把 `job.params` 丢给 `_compose_from_payload`。所以这里做两件事：

1. 结构断言：`_run_compose_job` 源码里必须出现 `_ai_resolve_params`（锚点）。
2. 行为断言：`_ai_resolve_params` 对「只有 request、没有 grade/subject」的入参，
   必须能推出 grade_id / subject_id（走 request 文本正则，不依赖 LLM）。
"""
import os
import sys
import tempfile

BACKEND = os.path.join(os.path.dirname(__file__), "..", "backend")
sys.path.insert(0, BACKEND)

os.environ.setdefault("LLM_ENABLED", "false")
os.environ.setdefault("CAPTCHA_ENFORCED", "false")
os.environ["SEED_BASE_DATA"] = "true"

# 一次性库，避免污染项目 data/
_tmp = tempfile.mkdtemp(prefix="p0_3_")
os.environ["DATABASE_URL"] = f"sqlite:///{os.path.join(_tmp, 'verify.db').replace(os.sep, '/')}"

from app.core.database import Base, SessionLocal, engine  # noqa: E402
import app.models  # noqa: F401,E402  确保全部模型注册到 metadata
from app.models import User  # noqa: E402
from app.services.init_db import init_grades_subjects  # noqa: E402


def _make_user(db):
    u = User(username="verify_p03", password="x", real_name="验证用",
             status="active")
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


def main():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    init_grades_subjects(db)
    db.commit()
    user = _make_user(db)

    failures = []

    # ---- 1) 结构断言（锚点必须落在真正被改的那一行）
    import inspect
    from app.api.v1 import paper_compose as pc

    src = inspect.getsource(pc._run_compose_job)
    if "_ai_resolve_params" not in src:
        failures.append("_run_compose_job 未调用 _ai_resolve_params（P0-3 回归）")
    else:
        print("[PASS] _run_compose_job 复用 _ai_resolve_params")

    # 旧实现的位置：直接 _compose_from_payload(db, user, params)
    if "on_progress=on_progress)" in src and "merged, parse_error, request = _ai_resolve_params" not in src:
        failures.append("_run_compose_job 仍直接把原始 params 交给引擎")

    # ---- 2) 行为断言：只给 request
    merged, parse_error, request = pc._ai_resolve_params(
        db, user, {"request": "出一份一年级数学期中卷"})
    print(f"       merged.grade_id={merged.get('grade_id')} "
          f"subject_id={merged.get('subject_id')} parse_error={parse_error!r}")
    if not merged.get("grade_id"):
        failures.append("只写描述时未能解析出年级（异步路径仍会失败）")
    if not merged.get("subject_id"):
        failures.append("只写描述时未能解析出学科（异步路径仍会失败）")

    # ---- 3) 显式选择优先：给了 grade_id/subject_id 就不该被改写
    from app.models import Grade, Subject
    g = db.query(Grade).filter(Grade.grade_num == 3).first()
    s = db.query(Subject).filter(Subject.grade_id == g.id).first() if g else None
    if g and s:
        merged2, _, _ = pc._ai_resolve_params(
            db, user, {"request": "一年级数学", "grade_id": g.id, "subject_id": s.id})
        if merged2.get("grade_id") != g.id or merged2.get("subject_id") != s.id:
            failures.append("显式年级/学科被 AI 推断覆盖（应客户端优先）")
        else:
            print(f"[PASS] 显式选择优先：grade={g.id} subject={s.id}")

    db.close()
    if failures:
        print("\n=== 失败 ===")
        for f in failures:
            print(" -", f)
        sys.exit(1)
    print("\n=== P0-3 全部通过 ===")


if __name__ == "__main__":
    main()
