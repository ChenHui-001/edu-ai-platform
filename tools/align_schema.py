#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""把实际库结构对齐到 ORM 元数据（SQLite，幂等）。

## 为什么需要

`Base.metadata.create_all` 只建**缺失的表**。模型加列/加索引/收紧可空性，
对已经存在的库毫无作用；项目长期靠 `db_migrations.MIGRATION_COLUMNS` 用
`ALTER TABLE ADD COLUMN` 兜底 —— 而 SQLite 的 ADD COLUMN 只能补「可空或
带默认值」的列，**加不了 NOT NULL、加不了 FOREIGN KEY、加不了索引、也改不了
类型**。于是存量库会慢慢长成一副「能跑但结构不对劲」的样子。

实测 2.5.36 的生产库与模型有 4 张表不一致：

| 表 | 漂移 |
| --- | --- |
| `edu_paper` | 缺 exam_type/stage/status/standard_id/share_scope 五个索引；缺 `review_by → sys_user.id` 外键；status/share_scope/current_version 可空；difficulty_ratio 仍是 VARCHAR(64)（模型已改 Text） |
| `edu_paper_item` | 缺 section_code 索引；section_sort 可空 |
| `edu_paper_share` | 缺 `uq_paper_share_target` 唯一约束；permission 可空 |
| `sys_agent_job` | cancel_requested 可空 |

这不是「看着别扭」：可空性与 NOT NULL 不一致意味着 `paper.status is None`、
按 `current_version` 排序都可能踩空；缺索引意味着试卷列表按 status/exam_type
过滤全表扫描；缺外键意味着删用户后 review_by 指向不存在的 id。

## 做法

判定用 Alembic 自己的 `compare_metadata()` —— 只有和 `alembic check` 同源的
比对，才能保证「本工具说齐了」与「守卫说齐了」是同一件事。

修复用 SQLite 唯一可行的方式，**按元数据重建表**：
建 `_<表>__align` → 拷数据 → 删旧表 → 改名 → 按元数据建索引。
外键检查在重建期间关闭（DROP TABLE 会被子表外键挡住），重建后
`PRAGMA foreign_key_check` 必须为空，且每张表行数必须前后一致，否则整体回滚。

**拒绝删数据**：库里多出来的列/表/约束一律不自动删（那是数据丢失），只报告。
索引是纯派生物，`--drop-extra-indexes` 才允许删。

## 用法

    python tools/align_schema.py                        # 只看差异（默认 dry-run，0 差异返回 0）
    python tools/align_schema.py --apply --yes           # 真改（自动先备份到同目录）
    python tools/align_schema.py --apply --yes --drop-extra-indexes

改完打基线版本，再用守卫确认：

    alembic stamp <head>      # 首次接入时；已有版本号则跳过
    alembic check             # 必须输出 "No new upgrade operations detected"
"""
import argparse
import os
import sqlite3
import sys
import time
from typing import Dict, List, Optional, Tuple

TOOLS = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.join(os.path.dirname(TOOLS), "backend")
sys.path.insert(0, BACKEND)

from app.core.config import settings  # noqa: E402
from app.core.database import Base  # noqa: E402

# ⚠️ 必须有这一行：`Base.metadata` 只有在模型模块被 import 之后才装满表。
# 漏掉时 metadata 是空的，compare_metadata 会返回「零差异」——工具"通过"了，
# 但什么都没比。和 migrations/env.py 里那一行同理。
import app.models  # noqa: E402,F401

# 这些差异意味着「库里有的东西模型里没有」= 自动修复会丢数据，默认拒绝
BLOCKING = {"remove_table", "remove_column", "remove_constraint", "remove_fk"}
# 索引是纯派生物（可随时重建），只有显式开关才删
INDEX_ONLY = {"remove_index"}


# ---------------------------------------------------------------- 库定位
def resolve_db(explicit: str = "") -> Tuple[str, str]:
    """返回 (文件路径, SQLAlchemy URL)。只处理 SQLite 文件库。"""
    url = explicit or os.environ.get("ALIGN_DB_URL") or settings.DATABASE_URL
    if not url.startswith("sqlite"):
        raise SystemExit(f"本工具只处理 SQLite（当前 DATABASE_URL 是 {url.split(':')[0]}）")
    path = url.split("sqlite:///")[-1]
    if not path or path == ":memory:":
        raise SystemExit(f"无法从 {url} 推出库文件路径")
    if not os.path.exists(path):
        raise SystemExit(f"库文件不存在：{path}")
    return path, url


# ---------------------------------------------------------------- 差异采集
def _flatten(diff) -> List[tuple]:
    """compare_metadata 会把「同一列的多个变更」打包成 list（如类型+可空性一起变）。

    不摊平的话，遍历时会拿到 `[('modify_nullable', ...), ('modify_type', ...)]`
    这种嵌套项，按 tuple 解包直接 IndexError。
    """
    out: List[tuple] = []
    for item in diff:
        if isinstance(item, list):
            out.extend(_flatten(item))
        else:
            out.append(item)
    return out


def collect_diff(url: str) -> List[tuple]:
    from alembic.autogenerate import compare_metadata
    from alembic.migration import MigrationContext
    from sqlalchemy import create_engine

    engine = create_engine(url)
    try:
        with engine.connect() as conn:
            ctx = MigrationContext.configure(conn, opts={"compare_type": True})
            return _flatten(compare_metadata(ctx, Base.metadata))
    finally:
        engine.dispose()


def table_of(item: tuple) -> Optional[str]:
    kind = item[0]
    if kind in ("add_table", "remove_table"):
        return item[1].name
    if kind in ("add_column", "remove_column", "modify_nullable", "modify_type"):
        return item[2]
    obj = item[1]
    return getattr(getattr(obj, "table", None), "name", None)


def describe(item: tuple) -> str:
    kind = item[0]
    if kind in ("add_column", "remove_column"):
        col = item[3]
        return f"{kind} {col.name} {col.type}"
    # modify_* 是 7 元组：(kind, schema, 表, 列, 库侧附加信息, 库侧当前值, 模型目标值)。
    # 只认 item[5]/item[6]；老版本 alembic 把值塞进 item[4] 的 dict，故留兜底。
    if kind in ("modify_nullable", "modify_type"):
        old, new = (item[5], item[6]) if len(item) >= 7 else (item[4], item[5])
        if kind == "modify_nullable":
            o, n = _pick(old, new, "nullable")
            return f"可空性 {item[3]}: {o} -> {n}（True=可空）"
        o, n = _pick(old, new, "type")
        return f"类型 {item[3]}: {o} -> {n}"
    if kind in ("add_index", "remove_index"):
        ix = item[1]
        cols = ", ".join(getattr(c, "name", str(c)) for c in ix.columns)
        return f"{kind} {ix.name}({cols})"
    if kind in ("add_fk", "remove_fk"):
        fk = item[1]
        cols = ", ".join(c.name for c in fk.columns)
        target = getattr(fk.elements[0].column.table, "name", "?") if fk.elements else "?"
        return f"{kind} {fk.name or ''}({cols}) -> {target}".replace(" ()", "()")
    if kind in ("add_constraint", "remove_constraint"):
        obj = item[1]
        cols = ", ".join(getattr(c, "name", str(c)) for c in getattr(obj, "columns", []))
        return f"{kind} {getattr(obj, 'name', '') or ''}({cols})".replace(" ()", "()")
    return " ".join(str(x) for x in item)[:160]


def _pick(old, new, key: str) -> Tuple:
    """从 (库里当前值, 模型目标值) 里取展示用值，兼容 dict 形式。"""
    def one(v):
        return v.get(key) if isinstance(v, dict) else v
    return one(old), one(new)


# ---------------------------------------------------------------- 重建
def _create_ddl(table, tmp: str, dialect) -> str:
    """按元数据编译建表语句，改成临时表名。"""
    from sqlalchemy.schema import CreateTable

    ddl = str(CreateTable(table).compile(dialect=dialect)).strip()
    if not ddl.upper().startswith("CREATE TABLE"):
        raise SystemExit(f"意外的建表语句：{ddl[:80]}")
    _, body = ddl.split("(", 1)
    return f'CREATE TABLE "{tmp}" (\n{body}'


def _create_indexes(con: sqlite3.Connection, table, dialect) -> int:
    from sqlalchemy.schema import CreateIndex

    n = 0
    for ix in table.indexes:
        con.execute(str(CreateIndex(ix).compile(dialect=dialect)))
        n += 1
    return n


def rebuild_table(con: sqlite3.Connection, table, dialect) -> str:
    """把一张表重建为元数据结构，返回人类可读的摘要。必须在事务内调用。"""
    name = table.name
    tmp = f"_{name}__align"
    con.execute(f'DROP TABLE IF EXISTS "{tmp}"')
    con.execute(_create_ddl(table, tmp, dialect))

    exists = con.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)).fetchone()
    if not exists:
        con.execute(f'ALTER TABLE "{tmp}" RENAME TO "{name}"')
        return f"新建表 + {_create_indexes(con, table, dialect)} 个索引"

    before = con.execute(f'SELECT COUNT(*) FROM "{name}"').fetchone()[0]
    old_cols = {r[1] for r in con.execute(f'PRAGMA table_info("{name}")')}
    cols = [c.name for c in table.columns if c.name in old_cols]
    # 元数据要求 NOT NULL 且无默认值、库里却没有的列 → 拷数据必炸，提前说清楚
    fatal = [c.name for c in table.columns
             if c.name not in old_cols and not c.nullable
             and c.default is None and c.server_default is None]
    if fatal:
        raise SystemExit(
            f"{name}: 以下列在模型里 NOT NULL 且无默认值，但库里不存在，无法补数据：{fatal}")
    if cols:
        names = ", ".join(f'"{c}"' for c in cols)
        con.execute(f'INSERT INTO "{tmp}" ({names}) SELECT {names} FROM "{name}"')
    con.execute(f'DROP TABLE "{name}"')
    con.execute(f'ALTER TABLE "{tmp}" RENAME TO "{name}"')
    n_ix = _create_indexes(con, table, dialect)

    after = con.execute(f'SELECT COUNT(*) FROM "{name}"').fetchone()[0]
    if before != after:
        raise SystemExit(f"{name}: 拷贝行数不一致（{before} -> {after}），已回滚")
    dropped = sorted(old_cols - {c.name for c in table.columns})
    note = f"，丢弃库里多余的列 {dropped}" if dropped else ""
    return (f"{before} 行 / {len(cols)} 列 → 重建完成，{n_ix} 个索引{note}")


def backup(path: str) -> str:
    """sqlite backup API 备份（不能直接 cp：WAL 里可能还有未落盘的页）。"""
    dst = os.path.join(
        os.path.dirname(path),
        f"align_backup_{time.strftime('%Y%m%d-%H%M%S')}.db")
    src_con = sqlite3.connect(path)
    dst_con = sqlite3.connect(dst)
    try:
        src_con.backup(dst_con)
    finally:
        dst_con.close()
        src_con.close()
    return dst if os.path.getsize(dst) > 0 else ""


# ---------------------------------------------------------------- 主流程
def main() -> int:
    ap = argparse.ArgumentParser(description="把 SQLite 库结构对齐到 ORM 元数据")
    ap.add_argument("--apply", action="store_true", help="真的执行（默认只看差异）")
    ap.add_argument("--yes", action="store_true", help="确认执行（与 --apply 配对）")
    ap.add_argument("--drop-extra-indexes", action="store_true",
                    help="删除元数据里没有的索引（仅索引，不涉及数据）")
    ap.add_argument("--db-url", default="", help="覆盖 DATABASE_URL")
    args = ap.parse_args()

    path, url = resolve_db(args.db_url)
    print(f"库文件：{path}")

    diff = collect_diff(url)
    if not diff:
        print("\n[OK] 结构已与模型完全一致，无需对齐")
        return 0

    groups: Dict[str, List[tuple]] = {}
    for item in diff:
        groups.setdefault(table_of(item) or "(未知)", []).append(item)

    print(f"\n== 差异：{len(diff)} 处 / {len(groups)} 张表 ==")
    blocked, extra_indexes, to_rebuild = [], [], []
    for name in sorted(groups):
        items = groups[name]
        print(f"\n  {name}")
        for item in items:
            print(f"    - {describe(item)}")
            if item[0] in BLOCKING:
                blocked.append((name, describe(item)))
        if any(i[0] in INDEX_ONLY for i in items):
            extra_indexes.extend(i[1].name for i in items if i[0] in INDEX_ONLY)
        if any(i[0] not in INDEX_ONLY and i[0] not in BLOCKING for i in items):
            to_rebuild.append(name)

    if blocked:
        print("\n[STOP] 以下差异意味着库里存在模型没有的列/表/约束，自动修复会丢数据：")
        for name, text in blocked:
            print(f"   {name}: {text}")
        print("   请人工确认后再处理（要么补回模型，要么手写迁移 DROP）。")
        return 1

    if extra_indexes and not args.drop_extra_indexes:
        # 必须整体中止，不能"先重建完再报错"：那会把库留在「改了一半、退出码非零」
        # 的状态，而运维看到失败只会以为什么都没动，转头就去查别的原因。
        print(f"\n[STOP] 元数据里没有这些索引：{extra_indexes}")
        print("       两条路选一条，本次**不做任何修改**：")
        print("       1) 补进模型（推荐）——索引也是结构，应该只有模型一个真源；")
        print("       2) 确认是手工 DDL 残留 → 加 --drop-extra-indexes 显式删掉。")
        return 1

    if not args.apply:
        print("\n[dry-run] 未做任何修改。要执行加 --apply --yes")
        return 0
    if not args.yes:
        print("\n[STOP] --apply 必须与 --yes 配对（避免误触）")
        return 1

    bak = backup(path)
    if not bak:
        print("\n[STOP] 备份失败，拒绝继续")
        return 1
    print(f"\n已备份：{bak}")

    from sqlalchemy.dialects import sqlite as sqlite_dialect
    dialect = sqlite_dialect.dialect()
    targets = [t for t in Base.metadata.sorted_tables if t.name in to_rebuild]

    con = sqlite3.connect(path, isolation_level=None, timeout=30)
    con.execute("PRAGMA busy_timeout=30000")
    con.execute("PRAGMA foreign_keys=OFF")
    if con.execute("PRAGMA foreign_keys").fetchone()[0] != 0:
        con.close()
        raise SystemExit("[STOP] 无法关闭外键检查（重建表会被子表挡住）")

    print("\n== 执行 ==")
    total_orphans = 0
    con.execute("BEGIN IMMEDIATE")
    try:
        for table in targets:
            print(f"  {table.name}: {rebuild_table(con, table, dialect)}")
        for ix in extra_indexes:
            con.execute(f'DROP INDEX IF EXISTS "{ix}"')
            print(f"  已删除多余索引 {ix}")
        # ⚠️ 孤儿检查必须在 COMMIT 之前：新增外键（如 edu_paper.review_by）可能
        # 撞上历史脏值，COMMIT 之后再发现就只能靠备份手工回滚了。
        # 只断言「本次重建过的表」—— 别的表的历史孤儿不是本工具的职责，
        # 拿全库结果当门槛会让一次无关的脏数据挡住整个对齐。
        # PRAGMA foreign_key_check 每行是 (表, rowid, 父表, fk序号) —— 表名已在第一列，
        # 不要再加前缀，否则打印成「表 edu_paper rowid=edu_paper -> 7」。
        bad: List[tuple] = []
        for table in targets:
            bad.extend(con.execute(f"PRAGMA foreign_key_check({table.name})").fetchall())
        if bad:
            con.execute("ROLLBACK")
            con.close()
            print(f"\n[FAIL] 已回滚：重建表里有 {len(bad)} 条孤儿引用")
            for row in bad[:8]:
                print(f"       {row[0]} rowid={row[1]} → 父表 {row[2]} 无对应行")
            print("       多为新增外键撞上历史脏值（如 review_by 指向已删用户）。"
                  "把脏值置空后重跑即可。")
            print(f"       备份在 {bak}")
            return 1
        total_orphans = len(con.execute("PRAGMA foreign_key_check").fetchall())
        con.execute("COMMIT")
    except Exception as exc:  # noqa: BLE001
        con.execute("ROLLBACK")
        con.close()
        print(f"\n[FAIL] 已回滚：{type(exc).__name__}: {exc}")
        print(f"       备份仍在 {bak}")
        return 1

    print("  [OK] 重建表无孤儿引用")
    if total_orphans:
        print(f"  [注意] 全库另有 {total_orphans} 条历史孤儿引用（本次未触碰的表，"
              f"未处理）")
    con.close()

    left = collect_diff(url)
    if left:
        print(f"\n[FAIL] 仍有 {len(left)} 处差异（未覆盖的差异类型）：")
        for item in left[:10]:
            print(f"   - {table_of(item)}: {describe(item)}")
        return 1
    print("\n[OK] 结构已与模型完全一致")
    print("     下一步：cd backend && alembic stamp <head>（首次接入时），"
          "然后 alembic check 确认干净")
    return 0


if __name__ == "__main__":
    sys.exit(main())
