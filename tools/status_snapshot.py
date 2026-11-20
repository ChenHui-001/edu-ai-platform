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
    # ★ 编码必须显式指定，不能靠 text=True 走系统默认编码。
    #   Windows 中文环境的默认编码是 GBK，而子进程输出的 `[config] APP_VERSION=
    #   '' 非版本号...` 是 UTF-8（应用内部统一用 UTF-8）。用 GBK 解码会抛
    #   UnicodeDecodeError: 'gbk' codec can't decode byte 0xac ...，
    #   而 capture_output=True 下这个异常发生在读取线程里，**子进程已经跑完**
    #   （returncode=0）但 stdout 变成 None —— 于是调用方拿到
    #   `AttributeError: 'NoneType' object has no attribute 'strip'`，
    #   报错点离真正的原因隔了三层，极难定位。
    #   errors="replace" 是第二道保险：万一子进程真吐出非法字节，
    #   宁可拿到带替换符的文本，也不要整条命令崩掉。
    return subprocess.run(
        cmd, cwd=cwd, env=env, capture_output=True, text=True,
        encoding="utf-8", errors="replace",
    )


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
    # FastAPI 0.165 起 include_router 改为惰性 `_IncludedRouter` 包装，
    # `len(app.routes)` 只剩默认文档路由 + 包装节点，不再反映真实端点数。
    # 统一改用 openapi() 的操作数（path × method），跨版本口径稳定。
    code = (
        "from app.main import app\n"
        "from app.core.database import Base, engine\n"
        "Base.metadata.create_all(bind=engine)\n"
        "schema = app.openapi()\n"
        "methods = ('get', 'post', 'put', 'delete', 'patch', 'head', 'options')\n"
        "ops = sum(1 for item in schema['paths'].values() for m in item if m in methods)\n"
        "print(ops, len(Base.metadata.tables), sep=',')\n"
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


# 后端用例所在的测试文件。写死单个文件会让新增的测试套件不被计数，
# 现状卡上的「后端用例」当场低估——指标失真比指标缺失更糟。
PYTEST_SUITES = (
    "backend/qa_audit_suite.py",
    "backend/qa_flow_engine_suite.py",
    "backend/qa_flow_urge_suite.py",
)


def count_pytest():
    """用例数（`--collect-only` 不执行，约 1s）。

    多个套件合并计数：口径是「后端 pytest 用例总数」，
    不是「某一个套件的用例数」。
    """
    total = 0
    for suite in PYTEST_SUITES:
        if not os.path.exists(os.path.join(ROOT, suite)):
            continue
        r = _run([PY, "-m", "pytest", suite, "--collect-only", "-q"], cwd=ROOT)
        m = re.search(r"(\d+)\s+tests?\s+collected", r.stdout or "")
        if not m:
            # 老版本 pytest 输出形如 "60 tests collected"；再兜一层「收集到 N 项」
            m = re.search(r"collected\s+(\d+)", r.stdout or "")
        if m:
            total += int(m.group(1))
    return total or None


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


def count_image_size():
    """生产镜像体积（`docker images` 实测 unified 镜像）。

    阶段 0 镜像瘦身后新增这一行：2.01GB → 1.39GB。
    体积是「用户能感知的资源成本」——镜像每 GB 都要下载、存储、解压，
    在服务器上还要占磁盘与内存。做瘦身时这一行必须能被自动核对，
    否则下次谁加回一个依赖，体积回涨了也没人知道。

    读不到 docker（未装 / 无权限 / 镜像未构建）时返回 None，
    渲染成「—」，不因此让整个脚本失败。
    """
    try:
        r = subprocess.run(
            ["docker", "images", "--format", "{{.Repository}}:{{.Tag}}\t{{.Size}}"],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=30,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if r.returncode != 0 or not r.stdout:
        return None
    # 优先取 `:latest`（生产交付物约定的标签）；没有再退回列表里第一个
    # 含 "edu-ai-platform" 的镜像。本机常有多个实验 tag（slim-test / baseline
    # 等），按列表序取第一个会拿到实验镜像，数字会随本机残留漂移。
    best = None
    fallback = None
    for line in r.stdout.splitlines():
        if "\t" not in line:
            continue
        name, _, size = line.partition("\t")
        if "edu-ai-platform" not in name:
            continue
        name = name.strip()
        if name.endswith(":latest"):
            best = size.strip()
            break
        if fallback is None:
            fallback = size.strip()
    return best or fallback


def render():
    version = open(os.path.join(ROOT, "VERSION"), encoding="utf-8").read().strip()
    routes, tables = measure_routes_tables()
    data = [
        ("版本", version, "`VERSION` 文件"),
        ("接口操作数", routes, "`app.openapi()` 的 path×method"),
        ("数据表数", tables, "`Base.metadata.tables`"),
        ("后端用例", count_pytest(), "`pytest backend/qa_*_suite.py --collect-only` 合计"),
        ("前端用例", count_vitest(), "`frontend/src/**/__tests__` 内 `it(` 计数"),
        ("接口断言", count_verify_assertions(), "`tools/verify_p0_fixes.py` 实际通过条数"),
        ("补列迁移", count_migrations(), "`core/db_migrations._COLUMNS`"),
        ("发版门禁", count_gates(), "`tools/auto_ship.sh` 引用的 check_*/scan_vue_* 数"),
        ("镜像体积", count_image_size(), "`docker images` 实测 unified 镜像"),
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
