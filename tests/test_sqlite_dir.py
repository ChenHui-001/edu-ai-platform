"""SQLite 数据目录自动创建（D 组）。

## 这个缺陷的形状

SQLite **不会自动创建父目录**，只会在目录不存在时抛
`sqlite3.OperationalError: unable to open database file`。而建库时机是分散的：
`create_all`、任意一条查询、乃至 `SessionLocal()` 的第一次 flush 都会触发。

它曾经真实存在，而且**被一个无关的副作用掩盖了很久**：
`core/logger.py` 原来默认启用 loguru FileSink（路径 `./data/logs/...`），
loguru 会 `makedirs` 整个路径 → `./data/` 被顺手建出来 → `create_all` 成功。
把 FileSink 改成默认关闭之后（那次修复本身是对的），`./data` 没人建了，
CI 的「应用导入与建表检查」立刻红，报的却是「数据库打不开」——
看起来像数据库故障，实际是目录问题。

**这类"被别人的副作用养着"的代码，在副作用被移除前永远测不出来。**

## 为什么这组测试必须用子进程

`_build_engine()` 在**模块导入时**执行（`engine = _build_engine()`），
且 `settings` 是导入期读环境变量生成的单例。同一进程里既无法改
`DATABASE_URL` 再重建引擎，也无法撤销已建好的目录副作用。
所以每个场景都起一个干净的子进程，各自给不同的 `DATABASE_URL`。

## 反向验证

把 `_build_engine()` 里的 `_ensure_sqlite_parent_dir(url)` 换成 `pass`：
D1① / D2① 变红（`OperationalError: unable to open database file`），
失败原因与预期一致。恢复后全绿。
"""
import os
import subprocess
import sys
import tempfile

_BACKEND = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))

_PASSED = 0
_FAILED = []


def ok(name, cond, detail=""):
    global _PASSED
    if cond:
        _PASSED += 1
        print(f"  [PASS] {name}" + (f"  -> {detail}" if detail else ""))
    else:
        _FAILED.append(name)
        print(f"  [FAIL] {name}" + (f"  -> {detail}" if detail else ""))


def _run(url, workdir, snippet):
    """在指定 cwd/env 下起子进程跑 snippet，返回 (rc, stdout, stderr)。"""
    env = dict(os.environ)
    env.update({
        "DATABASE_URL": url,
        "LLM_ENABLED": "false",
        "SCHEDULER_ENABLED": "false",
        "LOG_TO_DB": "false",
        "LOG_FILE_SINK": "false",
        "SECRET_KEY": "d_group_secret_key_0123456789abcdefgh",
        "LOG_DIR": os.path.join(workdir, "logs"),
        "UPLOAD_DIR": os.path.join(workdir, "uploads"),
        "EXPORT_DIR": os.path.join(workdir, "exports"),
        "CHROMA_PERSIST_DIR": os.path.join(workdir, "chroma"),
    })
    p = subprocess.run(
        [sys.executable, "-c", snippet], cwd=_BACKEND, env=env,
        capture_output=True, text=True, timeout=300,
    )
    return p.returncode, p.stdout, p.stderr


_CREATE_ALL = """
from app.main import app
from app.core.database import Base, engine
Base.metadata.create_all(bind=engine)
print("ROUTES", len(app.routes))
print("TABLES_OK")
"""

_BARE_ENGINE = """
# 不导入 app.main（它的 lifespan 里有 ensure_dirs）—— 只测引擎自己
from app.core.database import Base, engine
Base.metadata.create_all(bind=engine)
print("TABLES_OK")
"""


def main():
    print("\n" + "=" * 66)
    print("SQLite 数据目录：目录不存在时必须自己建，不能靠别人的副作用")
    print("=" * 66)

    with tempfile.TemporaryDirectory() as tmp:
        # ---------- D1：跑完整的 CI 那三行 ----------
        print("\nD1、CI 同款序列（导入 app.main + create_all）")
        d1 = os.path.join(tmp, "d1")
        os.makedirs(d1)
        db1 = os.path.join(d1, "nested", "data", "ci_test.db")
        url1 = "sqlite:///" + db1.replace("\\", "/")
        rc, out, err = _run(url1, d1, _CREATE_ALL)
        ok("D1 ① ★ 多级目录都不存在时建表成功", rc == 0 and "TABLES_OK" in out,
           f"rc={rc}, stderr尾部={err.strip().splitlines()[-1][:100] if err.strip() else '(空)'}")
        ok("D1 ② 数据库文件确实被创建", os.path.exists(db1),
           f"exists={os.path.exists(db1)}")
        ok("D1 ③ 路由表正常加载（说明不是「跳过初始化」换来的通过）",
           "ROUTES" in out, next((ln for ln in out.splitlines() if ln.startswith("ROUTES")), "(无)"))

        # ---------- D2：不导入 app.main，纯引擎 ----------
        # 这一条是关键：D1 可能被 lifespan/ensure_dirs 掩盖（虽然导入阶段不会跑
        # lifespan），D2 直接只碰引擎，证明是 database.py 自己兜住的。
        print("\nD2、只碰引擎（不导入 app.main）—— 证明兜底在 database.py 而不是别处")
        d2 = os.path.join(tmp, "d2")
        os.makedirs(d2)
        db2 = os.path.join(d2, "a", "b", "c", "x.db")
        url2 = "sqlite:///" + db2.replace("\\", "/")
        rc, out, err = _run(url2, d2, _BARE_ENGINE)
        ok("D2 ① ★ 不导入 app.main 也能建库（兜底在引擎构建处）",
           rc == 0 and "TABLES_OK" in out,
           f"rc={rc}, stderr尾部={err.strip().splitlines()[-1][:100] if err.strip() else '(空)'}")
        ok("D2 ② 四级目录被逐层创建", os.path.exists(db2), f"exists={os.path.exists(db2)}")

        # ---------- D3：内存库与异常形态不能被打坏 ----------
        print("\nD3、非文件库不应该被这套逻辑影响")
        rc, out, err = _run("sqlite:///:memory:", d2, _BARE_ENGINE)
        ok("D3 ① `:memory:` 库仍能正常建表（不因 makedirs 逻辑崩）",
           rc == 0 and "TABLES_OK" in out,
           f"rc={rc}, stderr尾部={err.strip().splitlines()[-1][:100] if err.strip() else '(空)'}")

        # ---------- D4：只读父目录只降级、不在建引擎处抛 ----------
        # 建目录失败时不能让「导入 app 模块」直接炸掉 —— 那会把一个可诊断的
        # 目录问题变成 import-time 崩溃，连日志都来不及打。
        print("\nD4、父目录建不出来时只降级告警")
        if os.name == "nt":
            # Windows 上没法简单可靠地造只读目录（ACL 行为不一致），
            # 用「父路径是个文件」来模拟 makedirs 必失败。
            d4 = os.path.join(tmp, "d4")
            os.makedirs(d4)
            blocker = os.path.join(d4, "blocker")
            with open(blocker, "w") as f:
                f.write("x")
            url4 = "sqlite:///" + os.path.join(blocker, "sub", "x.db").replace("\\", "/")
            rc, out, err = _run(url4, d4, "from app.core.database import engine; print('IMPORT_OK')")
            ok("D4 ① ★ 父路径不可用时导入仍不崩（只 warning）",
               "IMPORT_OK" in out or ("FileExistsError" not in err and "NotADirectoryError" not in err),
               f"rc={rc}, out={out.strip()[:80]}")
        else:
            print("  [SKIP] D4 仅在 Windows 上模拟（POSIX 的只读行为不同）")

    total = _PASSED + len(_FAILED)
    print(f"\n  数据目录回归完成：共 {total} 项 | 通过 {_PASSED} | 失败 {len(_FAILED)}")
    if _FAILED:
        print("\n失败用例：")
        for n in _FAILED:
            print(f"  - {n}")
    print(f"{'=' * 66}\n")
    return 1 if _FAILED else 0


if __name__ == "__main__":
    sys.exit(main())
