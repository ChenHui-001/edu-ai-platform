"""验证「空基线」开关：`SEED_BASE_DATA=false` 时只留账号，且**重启不重建学科**。

## 为什么需要这个脚本

学科、知识点、命题标准在 `init_all` 里都是「表为空就播种」。这意味着运维把表
删空之后，容器一重启就被灌回来 —— 想要一个可复现的"只有账号"的空环境，
光删数据是不够的，必须有启动期开关。本脚本锁住三件事：

1. `SEED_BASE_DATA=false` 时：年级照播（账号依赖它），学科/知识点/标准为空；
2. **连续两次 lifespan**（等价于重启两次）后仍然为空 —— 这是开关存在的意义，
   也是最容易回归的一条：只要有人把某个 `if not settings.SEED_BASE_DATA`
   删掉，这里立刻红；
3. 账号仍可登录、`/edu/subjects` 返回空数组（前端能正常渲染"没有学科"）。

用法：python tools/verify_empty_baseline.py
退出码 0 = 全部通过。
"""
import os
import sys
import tempfile

BACKEND = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend")
sys.path.insert(0, BACKEND)

DB_PATH = os.path.join(tempfile.gettempdir(), "verify_empty_baseline.db")
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)
os.environ.update({
    "DATABASE_URL": "sqlite:///" + DB_PATH.replace("\\", "/"),
    # ★ 被测开关
    "SEED_BASE_DATA": "false",
    "LLM_ENABLED": "false",
    "CAPTCHA_ENFORCED": "false",
    "SCHEDULER_ENABLED": "false",
    "SEED_DEMO_DATA": "false",
    "RAG_WARMUP_ENABLED": "false",
    "APP_VERSION": "test",
    "SECRET_KEY": "empty-baseline-test-key-0123456789abcdef0123",
})

from sqlalchemy import func, select  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.core.database import Base, SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models import (  # noqa: E402
    ExamStandard, Grade, KnowledgePoint, Subject, User,
)

FAILED = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"  -> {detail}" if detail else ""))
    if not ok:
        FAILED.append(name)


def counts():
    db = SessionLocal()
    try:
        return {
            "user": int(db.scalar(select(func.count()).select_from(User)) or 0),
            "grade": int(db.scalar(select(func.count()).select_from(Grade)) or 0),
            "subject": int(db.scalar(select(func.count()).select_from(Subject)) or 0),
            "kp": int(db.scalar(select(func.count()).select_from(KnowledgePoint)) or 0),
            "standard": int(db.scalar(select(func.count()).select_from(ExamStandard)) or 0),
        }
    finally:
        db.close()


def main() -> int:
    Base.metadata.create_all(bind=engine)

    # ---------------- 第一次启动（等价于首次部署的空库）----------------
    with TestClient(app) as c:
        api = "/api/v1"
        snap = counts()
        check("A1 年级照常播种（账号的 grade_id 依赖它）",
              snap["grade"] == 9, str(snap))
        check("A2 学科为空（开关生效）", snap["subject"] == 0, str(snap["subject"]))
        check("A3 知识点为空", snap["kp"] == 0, str(snap["kp"]))
        check("A4 命题标准为空", snap["standard"] == 0, str(snap["standard"]))
        check("A5 只有出厂管理员（SEED_DEMO_DATA=false）",
              snap["user"] == 1, str(snap["user"]))

        r = c.post(f"{api}/auth/login", json={"username": "admin", "password": "Admin@123456"})
        tok = ((r.json() or {}).get("data") or {}).get("access_token")
        check("A6 管理员可登录（空基线不影响认证）", bool(tok), (r.text or "")[:120])
        if tok:
            H = {"Authorization": f"Bearer {tok}"}
            c.put(f"{api}/auth/password", headers=H, json={
                "old_password": "Admin@123456", "new_password": "Emp@Test2026!"})
            r = c.post(f"{api}/auth/login",
                       json={"username": "admin", "password": "Emp@Test2026!"})
            tok = ((r.json() or {}).get("data") or {}).get("access_token")
            H = {"Authorization": f"Bearer {tok}"}

            d = ((c.get(f"{api}/edu/subjects", headers=H).json() or {}).get("data")) or []
            rows = d if isinstance(d, list) else (d.get("items") or [])
            check("A7 /edu/subjects 返回空数组（前端不会 500）",
                  r.status_code == 200 and rows == [], f"{r.status_code} n={len(rows)}")

            d = ((c.get(f"{api}/edu/grades", headers=H).json() or {}).get("data")) or []
            rows = d if isinstance(d, list) else (d.get("items") or [])
            check("A8 /edu/grades 仍有 9 条", len(rows) == 9, str(len(rows)))

    # ---------------- 第二次启动：等价于容器重启 ----------------
    # 这是本脚本的核心：如果开关没接进 init_all，这里学科会被灌回 59 个。
    with TestClient(app) as _c:
        snap2 = counts()
        check("B1 重启后学科仍为 0（开关挡住了「空表就播种」）",
              snap2["subject"] == 0, str(snap2["subject"]))
        check("B2 重启后知识点仍为 0", snap2["kp"] == 0, str(snap2["kp"]))
        check("B3 重启后命题标准仍为 0", snap2["standard"] == 0, str(snap2["standard"]))
        check("B4 重启不会重复建账号", snap2["user"] == 1, str(snap2["user"]))

    print("\n" + "=" * 60)
    if FAILED:
        print(f"失败 {len(FAILED)} 项：")
        for f in FAILED:
            print("  -", f)
        return 1
    print("全部通过")
    return 0


if __name__ == "__main__":
    code = 1
    try:
        code = main()
    except Exception:  # noqa: BLE001
        import traceback

        traceback.print_exc()
        code = 1
    finally:
        try:
            os.remove(DB_PATH)
        except OSError:
            pass
        sys.stdout.flush()
        sys.stderr.flush()
        os._exit(code)   # 与 verify_kp_import 同理：避开 daemon 线程析构期 abort
