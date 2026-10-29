"""A1 启动互斥实测探针（仅在 Linux 容器内运行，需要 fcntl）。

验证 `main._startup_lock()` 把「建表 + 两个破坏性 V2 迁移 + init_all」串行化。

判定方式：在**全新库**上并发启动两个进程，然后数**关键日志的出现次数**。
比数表行数更可靠——不依赖任何表名/字段名（种子与迁移的表结构会漂移，
探针不该跟着漂）。每条关键日志代表一次「本不该重复发生的副作用」：

  演示数据初始化完成        → 种子是否被播了两份（班级/教师/学生翻倍）
  知识点 V2 迁移完成        → 破坏性 DELETE 是否执行了两次
  题库 V2 迁移完成          → 同上
  默认管理员已创建          → init_admin 是否被并发重复插入
  知识点树初始化完成        → 知识树是否被播两份
  命题标准播种完成          → 命题标准是否被播两份

再加一道保险：双进程跑完后的表行数必须与单进程基准逐表相等。

用法（容器内）：
    docker run --rm -e A1_BACKEND_DIR=/app \
        -v <app目录>:/app/app:ro -v <本文件>:/tmp/probe.py:ro \
        --entrypoint python <镜像> /tmp/probe.py

退出码 0 = 通过，非 0 = 失败。脚本只建临时库，不触碰项目 data/。
"""
import os
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

BACKEND = Path(os.environ.get("A1_BACKEND_DIR") or
               (Path(__file__).resolve().parent.parent / "backend"))

# 每条日志 = 一次「本不该重复发生」的副作用
ONCE_ONLY = [
    "演示数据初始化完成",
    "知识点 V2 迁移完成",
    "题库 V2 迁移完成",
    "默认管理员已创建",
    "知识点树初始化完成",
    "命题标准播种完成",
]

TABLES = ("edu_class", "edu_knowledge_point", "sys_user", "sys_role",
          "sys_permission", "edu_exam_standard", "sys_scheduled_job",
          "edu_teaching_assignment")


def _counts(db_path: str) -> dict:
    con = sqlite3.connect(db_path)
    try:
        out = {}
        for tbl in TABLES:
            try:
                out[tbl] = con.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]
            except sqlite3.Error as exc:
                out[tbl] = f"ERR:{exc}"
        return out
    finally:
        con.close()


def _spawn(db_path: str, tag: str, gate_dir: str) -> subprocess.Popen:
    """起一个只跑 lifespan 的进程（不经 uvicorn，避免端口/信号干扰）。

    子进程在 import app 之后、进入 lifespan 之前先做一次 rendezvous：
      1. 写 `gate/<tag>.ready`
      2. 自旋等 `gate/go` 出现
    这样两个进程的 `lifespan` 才会真正同时在毫秒级窗口内进入。没有这一步，
    `Popen` 两次返回的时间差（实测几十~上百毫秒）比整个启动钩子还长，
    第二个进程自然看到「第一次的成果已在库里」，于是**并发窗口根本不存在** ——
    反向验证时探针会误报「无锁也没问题」。
    """
    gate = Path(gate_dir)
    code = (
        "import os, time\n"
        "from pathlib import Path\n"
        "from fastapi.testclient import TestClient\n"
        "from app.main import app\n"
        "gate = Path(os.environ['A1_GATE_DIR'])\n"
        "gate.mkdir(parents=True, exist_ok=True)\n"
        "(gate / (os.environ['A1_TAG'] + '.ready')).write_text('1')\n"
        "deadline = time.time() + 120\n"
        "while not (gate / 'go').exists():\n"
        "    if time.time() > deadline:\n"
        "        raise SystemExit('gate timeout')\n"
        "    time.sleep(0.001)\n"
        "with TestClient(app) as c:\n"
        "    r = c.get('/api/v1/health')\n"
        "    print('HEALTH', r.status_code)\n"
        "print('EXIT_OK')\n"
    )
    work = Path(db_path).parent
    env = dict(os.environ)
    env.update({
        "A1_GATE_DIR": str(gate),
        "A1_TAG": tag,
        "DATABASE_URL": f"sqlite:///{db_path}",
        "SECRET_KEY": "a1probe-" + "x" * 40,
        "LLM_ENABLED": "false",
        "SCHEDULER_ENABLED": "false",
        "DEBUG": "false",
        "SEED_DEMO_DATA": "true",
        "LOG_DIR": str(work / f"logs_{tag}"),
        "UPLOAD_DIR": str(work / f"up_{tag}"),
        "EXPORT_DIR": str(work / f"ex_{tag}"),
        "CHROMA_PERSIST_DIR": str(work / f"ch_{tag}"),
    })
    return subprocess.Popen(
        [sys.executable, "-c", code],
        cwd=str(BACKEND), env=env,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
    )


def _launch(db_path: str, n: int):
    """并发启动 n 个进程，等它们全部 ready 后同时放行。"""
    gate = Path(tempfile.mkdtemp(prefix="a1_gate_"))
    procs = [_spawn(db_path, f"p{i}", str(gate)) for i in range(n)]
    # 等全部 ready（最多 120s）
    import time as _t
    deadline = _t.time() + 120
    while _t.time() < deadline:
        if len(list(gate.glob("*.ready"))) >= n:
            break
        if any(p.poll() is not None for p in procs):
            break
        _t.sleep(0.01)
    (gate / "go").write_text("1")
    return [p.communicate(timeout=300)[0] for p in procs]


def main() -> int:
    fails: list = []

    # ---- 基准：单进程全新库 ----
    base_db = os.path.join(tempfile.mkdtemp(prefix="a1_base_"), "x.db")
    base_out = _launch(base_db, 1)[0]
    if "EXIT_OK" not in base_out:
        print(f"FAIL: 基准单进程启动失败\n{base_out[-3000:]}")
        return 1
    base = _counts(base_db)
    print(f"[基准] 单进程行数: {base}")
    for msg in ONCE_ONLY:
        n = base_out.count(msg)
        if n != 1:
            print(f"  [提示] 基准里「{msg}」出现 {n} 次（预期 1）")

    # ---- 并发：双进程全新库 ----
    par_db = os.path.join(tempfile.mkdtemp(prefix="a1_par_"), "x.db")
    outs = _launch(par_db, 2)
    for i, o in enumerate(outs):
        if "EXIT_OK" not in o:
            fails.append(f"进程 {i} 未正常退出:\n{o[-2000:]}")
    if not any("另一个进程正在执行启动钩子" in o for o in outs):
        fails.append("没有出现「另一个进程正在执行启动钩子」日志 —— 两个进程未串行")

    print("\n[并发] 双进程关键日志次数（合计，预期各 1）：")
    for msg in ONCE_ONLY:
        n = sum(o.count(msg) for o in outs)
        flag = "OK " if n == 1 else "!! "
        print(f"  {flag}{msg}: {n}")
        if n != 1:
            fails.append(f"「{msg}」出现 {n} 次（应为 1）—— 启动钩子非单点执行")

    par = _counts(par_db)
    print(f"\n[并发] 双进程行数: {par}")
    for tbl in TABLES:
        if base.get(tbl) != par.get(tbl):
            fails.append(f"{tbl} 行数不一致: 单进程={base.get(tbl)} 双进程={par.get(tbl)}")

    if fails:
        print("\n=== FAIL ===")
        for f in fails:
            print(" -", f)
        return 1
    print("\n=== PASS: 启动钩子单点执行，种子/迁移/建表均未重复 ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
