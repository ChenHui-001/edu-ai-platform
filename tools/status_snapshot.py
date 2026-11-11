"""重算 `docs/STATUS.md` 的实测数字（Q-02）。

## 为什么要有这个脚本

「现状卡」的宿命是过期：手写一次 288 个端点，下次加 3 个端点就没人改，
三个月后又变成第二个 `ARCHITECTURE_ASSESSMENT`。所以卡里的数字必须能一条命令
重算，而不是靠人记得。

用法：
    python tools/status_snapshot.py            # 只打印
    python tools/status_snapshot.py --write    # 回写 docs/STATUS.md 的 auto 区块
    python tools/status_snapshot.py --check    # 只比对，卡上的数字与实测不一致就 FAIL

`--write` 只改 `<!-- status:auto:begin -->` 与 `<!-- status:auto:end -->` 之间，
不会动卡里的说明文字。`--check` 给 CI 用：CI 不该改工作区，只该判红。
"""
import os
import re
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND = os.path.join(ROOT, "backend")
STATUS = os.path.join(ROOT, "docs", "STATUS.md")

BEGIN = "<!-- status:auto:begin -->"
END = "<!-- status:auto:end -->"

PY = sys.executable


def _run(cmd, cwd, env=None):
    return subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True)


def measure_routes_tables():
    """导入 app 统计路由与表数（一次性临时库，绝不碰 ./data）。"""
    tmp = tempfile.mkdtemp(prefix="status_snapshot_")
    env = dict(os.environ)
    env.update({
        "DATABASE_URL": "sqlite:///" + os.path.join(tmp, "snap.db").replace("\\", "/"),
        "LLM_ENABLED": "false", "SCHEDULER_ENABLED": "false",
        "SEED_DEMO_DATA": "false", "DEBUG": "false", "APP_ENV": "test",
        "SECRET_KEY": "status_snapshot_secret_key_0123456789",
    })
    code = (
        "from app.main import app\n"
        "from app.core.database import Base, engine\n"
        "Base.metadata.create_all(bind=engine)\n"
        "print(len(app.routes), len(Base.metadata.tables), sep=',')\n"
    )
    r = _run([PY, "-c", code], cwd=BACKEND, env=env)
    if r.returncode != 0:
        return None, None
    line = (r.stdout or "").strip().splitlines()[-1] if r.stdout.strip() else ""
    try:
        routes, tables = line.split(",")
        return int(routes), int(tables)
    except ValueError:
        return None, None


def count_pytest():
    """用例数（`--collect-only` 不执行，约 1s）。"""
    r = _run([PY, "-m", "pytest", "backend/qa_audit_suite.py",
              "--collect-only", "-q"], cwd=ROOT)
    m = re.search(r"(\d+)\s+tests?\s+collected", r.stdout or "")
    if m:
        return int(m.group(1))
    # 老版本 pytest 输出形如 "60 tests collected"；再兜一层「收集到 N 项」
    m = re.search(r"collected\s+(\d+)", r.stdout or "")
    return int(m.group(1)) if m else None


def count_vitest():
    """前端用例数：读 __tests__ 里的 `it(`/`test(` 计数（不启动 vitest）。"""
    base = os.path.join(ROOT, "frontend", "src")
    n = 0
    for root, _dirs, files in os.walk(base):
        for name in files:
            if not name.endswith((".test.js", ".spec.js")):
                continue
            with open(os.path.join(root, name), encoding="utf-8") as fh:
                n += len(re.findall(r"^\s*(?:it|test)\s*\(", fh.read(), re.M))
    return n


def count_verify_assertions():
    """接口级断言条数 = **实际执行**的断言数（数 PASS 行），不是源码里的 check( 个数。

    两者不等：`for path, name in (...)` 里那次 `check(...)` 会跑 4 遍
    （BUG-026 的四条端点各一次）。数源码会少算 5 条，正好把"加了断言"这件事
    统计没了 —— 卡上的数字必须和 `auto_ship` 打印的条数对得上。
    """
    path = os.path.join(ROOT, "tools", "verify_p0_fixes.py")
    if not os.path.exists(path):
        return None
    r = _run([PY, path], cwd=ROOT)
    if r.returncode != 0:
        return None
    return len(re.findall(r"^\s*PASS\s", r.stdout or "", re.M))


def count_gates():
    """接入 auto_ship 的门禁道数（按脚本里的调用计，不按文件数）。"""
    path = os.path.join(ROOT, "tools", "auto_ship.sh")
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    # 段落 0.x 里的显式调用
    calls = set(re.findall(r"tools/(check_\w+|scan_vue_\w+)\.py", text))
    # 前端普查是 `for _g in scan_vue_refs scan_vue_dup ...` 的循环，没有
    # 字面量 `tools/xxx.py`，必须单独把这串名字数出来，否则少算 5 道。
    for m in re.finditer(r"for\s+_g\s+in\s+([\w\s]+);\s*do", text):
        calls.update(n for n in m.group(1).split() if n)
    return len(calls)


def count_migrations():
    """补列迁移条数（`db_migrations._COLUMNS` 的项数）。"""
    path = os.path.join(BACKEND, "app", "core", "db_migrations.py")
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    block = re.search(r"_COLUMNS[^=]*=\s*\[(.*?)\n\]", text, re.S)
    return len(re.findall(r"\(\s*\"", block.group(1))) if block else None


def render():
    version = open(os.path.join(ROOT, "VERSION"), encoding="utf-8").read().strip()
    routes, tables = measure_routes_tables()
    data = [
        ("版本", version, "`VERSION` 文件"),
        ("路由数", routes, "`app.routes`"),
        ("数据表数", tables, "`Base.metadata.tables`"),
        ("后端用例", count_pytest(), "`pytest backend/qa_audit_suite.py --collect-only`"),
        ("前端用例", count_vitest(), "`frontend/src/**/__tests__` 内 `it(` 计数"),
        ("接口断言", count_verify_assertions(), "`tools/verify_p0_fixes.py` 实际通过条数"),
        ("补列迁移", count_migrations(), "`core/db_migrations._COLUMNS`"),
        ("发版门禁", count_gates(), "`tools/auto_ship.sh` 引用的 check_*/scan_vue_* 数"),
    ]
    lines = [BEGIN, "| 项 | 实测值 | 口径 |", "|---|---:|---|"]
    for label, value, how in data:
        shown = "—" if value is None else value
        lines.append(f"| {label} | {shown} | {how} |")
    lines.append("\n> 由 `python tools/status_snapshot.py --write` 生成。"
                 "版本号另由 `tools/check_doc_versions.py` 门禁强制与 `VERSION` 一致。")
    lines.append(END)
    return "\n".join(lines)


def main() -> int:
    block = render()

    if "--check" in sys.argv:
        with open(STATUS, encoding="utf-8") as fh:
            text = fh.read()
        if BEGIN not in text or END not in text:
            print(f"[FAIL] {STATUS} 里找不到 {BEGIN} / {END} 标记")
            return 1
        current = BEGIN + text.split(BEGIN, 1)[1].split(END, 1)[0] + END
        if current.strip() == block.strip():
            print("[OK] 现状卡数字与实测一致")
            return 0
        print("[FAIL] docs/STATUS.md 的实测数字已过期，跑 `python tools/status_snapshot.py --write`：")
        old_lines = current.splitlines()
        for i, line in enumerate(block.splitlines()):
            got = old_lines[i] if i < len(old_lines) else "<缺行>"
            if got.strip() != line.strip():
                print(f"  - {got.strip()}")
                print(f"  + {line.strip()}")
        return 1

    if "--write" not in sys.argv:
        print(block)
        return 0

    with open(STATUS, encoding="utf-8") as fh:
        text = fh.read()
    if BEGIN not in text or END not in text:
        print(f"[FAIL] {STATUS} 里找不到 {BEGIN} / {END} 标记")
        return 1
    head, rest = text.split(BEGIN, 1)
    _old, tail = rest.split(END, 1)
    with open(STATUS, "w", encoding="utf-8", newline="") as fh:
        fh.write(head + block + tail)
    print(f"[OK] 已回写 {os.path.relpath(STATUS, ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
