#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Alembic 守卫：迁移链能建库、且与模型**结构一致**（Q-06）。

## 为什么需要

引入 Alembic 最容易变成"摆设"：文件建了、依赖装了，但从来没在空库上跑过，
也没人比对过迁移结果和 `Base.metadata`。等到某天真的要改列，才发现基线漏了
一张表、或者某次 autogenerate 漏了一种列类型 —— 那时已经在改生产了。

这个脚本把三件事变成一次可重复的本地检查（约 3s，不需要 Docker）：

1. **迁移链自洽**：`head` 唯一（多 head = 分支冲突，`upgrade head` 会直接报错），
   且 `alembic upgrade head` 能在**空库**上跑完。
2. **与模型一致**：`compare_metadata()` 必须返回空列表 —— 也就是"迁移建出来的
   结构"与"模型定义的结构"没有差异。这是本脚本的核心断言：模型加了列却忘了
   生成迁移，这里立刻红。
3. **与 create_all 等价**：表集合、每张表的列（名称+类型+可空）必须完全一致。
   `create_all` 是新库/测试库的建库方式，两者不等价意味着"测试库能跑、迁移库
   跑不了"这类只在生产暴露的偏差。

临时库放系统 temp 目录，跑完即删，**不碰任何真实库**。

用法：
    python tools/check_alembic_sync.py        # 0=通过 1=不一致 2=环境缺 alembic
"""
import os
import sys
import tempfile

TOOLS = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.join(os.path.dirname(TOOLS), "backend")
sys.path.insert(0, BACKEND)

DB_PATH = os.path.join(tempfile.gettempdir(), "check_alembic_sync.db")
DB_URL = "sqlite:///" + DB_PATH.replace("\\", "/")

# env.py 优先读它；这里必须在 import app.* 之前设好，否则会连到开发库
os.environ["ALEMBIC_DB_URL"] = DB_URL
for _stale in (DB_PATH, DB_PATH + "-wal", DB_PATH + "-shm"):
    if os.path.exists(_stale):
        os.remove(_stale)

try:
    from alembic import command
    from alembic.autogenerate import compare_metadata
    from alembic.config import Config
    from alembic.migration import MigrationContext
    from alembic.script import ScriptDirectory
except ImportError:
    print("[SKIP] 未安装 alembic（pip install alembic==1.14.0）")
    sys.exit(2)

from sqlalchemy import create_engine, inspect  # noqa: E402

from app.core.database import Base  # noqa: E402

FAILED = []


def fail(msg):
    FAILED.append(msg)
    print("  [FAIL] " + msg)


def column_signature(inspector, table):
    """列指纹：名称 + 类型字符串 + 可空性。

    不比 default/server_default：SQLite 的 DDL 文本在 create_all 与迁移之间
    会有字面差异（如 `'0'` vs `0`），比了只会产生噪音，而这两者不影响读写。
    """
    out = []
    for col in inspector.get_columns(table):
        out.append((col["name"], str(col["type"]), bool(col["nullable"])))
    return sorted(out)


def main() -> int:
    cfg = Config(os.path.join(BACKEND, "alembic.ini"))
    # 不依赖当前工作目录：显式指到 backend/migrations
    cfg.set_main_option("script_location", os.path.join(BACKEND, "migrations"))

    print("\n=== 1. 迁移链 head 唯一 ===")
    # 用 ScriptDirectory 而不是 command.heads()：后者只往 stdout 打印，
    # 拿不到返回值（1.14 里返回 None），无法参与断言。
    heads = ScriptDirectory.from_config(cfg).get_heads()
    if len(heads) != 1:
        fail(f"head 不唯一（{len(heads)} 个：{heads}）—— 存在分支迁移")
        return 1
    print(f"  [OK] head = {heads[0]}")

    print("\n=== 2. 空库执行 alembic upgrade head ===")
    try:
        command.upgrade(cfg, "head")
    except Exception as exc:  # noqa: BLE001
        fail(f"upgrade head 失败：{type(exc).__name__}: {exc}")
        return 1
    alembic_engine = create_engine(DB_URL)
    tables_migrated = set(inspect(alembic_engine).get_table_names()) - {"alembic_version"}
    print(f"  [OK] 迁移建出 {len(tables_migrated)} 张表")

    print("\n=== 3. 迁移结果 vs 模型（compare_metadata 必须为空）===")
    with alembic_engine.connect() as conn:
        ctx = MigrationContext.configure(conn, opts={"compare_type": True})
        diff = compare_metadata(ctx, Base.metadata)
    # 只关心"结构层面的偏差"，索引/约束差异也照报，避免漏掉真实问题
    if diff:
        fail(f"迁移与模型结构不一致，共 {len(diff)} 处差异：")
        for item in diff[:15]:
            print(f"         {item}")
        if len(diff) > 15:
            print(f"         ...（其余 {len(diff) - 15} 处省略）")
    else:
        print("  [OK] 迁移结果与模型结构完全一致")

    print("\n=== 4. 迁移结果 vs create_all（表与列逐项比对）===")
    ref_path = DB_PATH.replace(".db", "_ref.db")
    for _stale in (ref_path, ref_path + "-wal", ref_path + "-shm"):
        if os.path.exists(_stale):
            os.remove(_stale)
    ref_engine = create_engine("sqlite:///" + ref_path.replace("\\", "/"))
    Base.metadata.create_all(ref_engine)
    ref_insp, mig_insp = inspect(ref_engine), inspect(alembic_engine)
    tables_ref = set(ref_insp.get_table_names())

    missing = tables_ref - tables_migrated
    extra = tables_migrated - tables_ref
    if missing:
        fail(f"迁移缺表 {len(missing)} 张：{sorted(missing)}")
    if extra:
        fail(f"迁移多出 {len(extra)} 张：{sorted(extra)}")
    if not missing and not extra:
        print(f"  [OK] 表集合一致（{len(tables_ref)} 张）")

    col_diff = 0
    for table in sorted(tables_ref & tables_migrated):
        a, b = column_signature(ref_insp, table), column_signature(mig_insp, table)
        if a != b:
            col_diff += 1
            only_ref = [c for c in a if c not in b]
            only_mig = [c for c in b if c not in a]
            print(f"  [FAIL] {table} 列不一致")
            if only_ref:
                print(f"         create_all 有、迁移没有：{only_ref}")
            if only_mig:
                print(f"         迁移有、create_all 没有：{only_mig}")
    if col_diff:
        FAILED.append(f"{col_diff} 张表列定义不一致")
    else:
        print("  [OK] 全部表列定义一致（名称/类型/可空）")

    alembic_engine.dispose()
    ref_engine.dispose()
    for path in (DB_PATH, ref_path):
        for suffix in ("", "-wal", "-shm"):
            if os.path.exists(path + suffix):
                os.remove(path + suffix)

    print("\n" + "=" * 60)
    if FAILED:
        print(f"[FAIL] Alembic 守卫未通过（{len(FAILED)} 项）")
        print("       改完模型别忘了：cd backend && alembic revision --autogenerate -m \"...\"")
        return 1
    print("[OK] Alembic 迁移链与模型、create_all 三者一致")
    return 0


if __name__ == "__main__":
    sys.exit(main())
