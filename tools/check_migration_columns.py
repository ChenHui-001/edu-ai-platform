#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""结构迁移守护：补列清单 ↔ 模型结构必须**双向**一致（P1-6 / P1-3）。

`Base.metadata.create_all` 只建缺失的表，不给已存在的表加列。项目靠
`db_migrations.MIGRATION_COLUMNS` 在启动时幂等补列。这张手写清单没有任何
守护，会出现三类静默事故：

  * 清单里的表名/列名拼错，或模型重构后列被删 —— 补列执行时 ALTER
    一个不存在的目标，运行时随机 500；
  * 清单重复登记同一列 —— 多次 ALTER，日志里全是失败噪音；
  * **模型加了列但没登记清单** —— 老库永远缺这一列，任何涉及该列的读写
    都会 500。这是最危险的一类，而且原先的门禁完全抓不到：它只遍历清单，
    从来不看「模型比清单多了什么」，于是给出「补列清单与模型列一致」的
    假绿信号。

## 反向比对怎么落地

反向比对需要知道「哪些列是老库天生就有、不需要迁移的」—— 这部分无法从
当前模型推导（模型只有最终状态）。因此维护一份**基线快照**
`tools/migration_baseline.json`：记录引入本门禁那一刻，每张存量表的全部列。

不变量：**基线表里的每一列，要么在基线快照里，要么登记在 MIGRATION_COLUMNS 里。**

- 基线里没有的表 = 门禁上线之后新建的表 → `create_all` 会连列一起建出来，
  老库也能建全，不需要迁移，跳过；
- 基线里有的表 → 新增列必须登记，否则红。

基线只在「确认某批列确实不需要迁移」时用 `--init` 重生成；平时不要动，
否则等于把门禁调松。

用法：
    python tools/check_migration_columns.py           # 0=通过 1=不一致
    python tools/check_migration_columns.py --init    # 重新生成基线快照
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "backend"))

# 导入全部模型，否则 Base.metadata 里只有被 import 过的表
import app.models  # noqa: F401
from app.core.database import Base  # noqa: E402
from app.core.db_migrations import MIGRATION_COLUMNS  # noqa: E402

BASELINE_PATH = os.path.join(ROOT, "tools", "migration_baseline.json")


def _load_baseline():
    try:
        with open(BASELINE_PATH, encoding="utf-8") as fh:
            return json.load(fh)
    except OSError:
        return None


def _write_baseline() -> int:
    """按「当前模型 − 已登记清单」生成基线快照。"""
    registered = {(t, c) for t, c, _ in MIGRATION_COLUMNS}
    snapshot = {}
    for table_name, table in sorted(Base.metadata.tables.items()):
        cols = [c.name for c in table.columns if (table_name, c.name) not in registered]
        snapshot[table_name] = sorted(cols)
    with open(BASELINE_PATH, "w", encoding="utf-8") as fh:
        json.dump(snapshot, fh, ensure_ascii=False, indent=2, sort_keys=True)
        fh.write("\n")
    total = sum(len(v) for v in snapshot.values())
    print(f"[OK] 已生成基线快照：{len(snapshot)} 张表 / {total} 列 → {BASELINE_PATH}")
    return 0


def main() -> int:
    if "--init" in sys.argv:
        return _write_baseline()

    errors = []
    seen = set()

    # ① 正向：清单里的每一项都必须在模型里真实存在，且不重复
    for table, column, ddl in MIGRATION_COLUMNS:
        key = (table, column)
        if key in seen:
            errors.append(f"重复登记：{table}.{column}")
        seen.add(key)
        if not str(ddl or "").strip():
            errors.append(f"DDL 为空：{table}.{column}")
        meta = Base.metadata.tables.get(table)
        if meta is None:
            errors.append(f"表不存在于模型：{table}（清单项 {table}.{column}）")
        elif column not in meta.c:
            errors.append(f"列不存在于模型：{table}.{column}")

    # ② 反向：存量表新增的列必须登记进清单
    baseline = _load_baseline()
    if baseline is None:
        print("[FAIL] 缺少基线快照 tools/migration_baseline.json")
        print("       首次启用反向比对时执行一次：python tools/check_migration_columns.py --init")
        return 1
    missing = []
    for table, cols in baseline.items():
        meta = Base.metadata.tables.get(table)
        if meta is None:
            errors.append(f"基线表已从模型移除：{table}（确认清单里是否还有它的列）")
            continue
        known = set(cols) | {c for t, c in seen if t == table}
        for column in meta.c.keys():
            if column not in known:
                missing.append(f"{table}.{column}")

    if missing:
        print(f"[FAIL] 模型新增列未登记补列清单（{len(missing)} 项）：")
        for item in sorted(missing):
            print("  -", item)
        print("\n老库不会自动获得这些列，运行时涉及列的读写会 500。")
        print("请把它们加进 backend/app/core/db_migrations.py 的 MIGRATION_COLUMNS；")
        print("若确认该列不需要迁移（新表自带 / 无需回填），执行一次")
        print("  python tools/check_migration_columns.py --init")
        print("更新基线快照。")

    if errors or missing:
        if errors:
            print("[FAIL] 补列清单与模型不一致：")
            for e in errors:
                print("  -", e)
        return 1

    total_cols = sum(len(v) for v in baseline.values())
    print(f"[OK] 补列清单 {len(MIGRATION_COLUMNS)} 项与模型列一致，无重复项；"
          f"反向比对 {len(baseline)} 张表 / {total_cols} 基线列无漏登记")
    return 0


if __name__ == "__main__":
    sys.exit(main())
