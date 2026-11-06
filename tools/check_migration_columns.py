#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""结构迁移守护：补列清单必须与模型真实结构一致（P1-6）。

`Base.metadata.create_all` 只建缺失的表，不给已存在的表加列。项目靠
`db_migrations.MIGRATION_COLUMNS` 在启动时幂等补列。这张手写清单没有任何
守护，会出现两类静默事故：

  * 清单里的表名/列名拼错，或模型重构后列被删 —— 补列执行时 ALTER
    一个不存在的目标，旧代码「记日志继续」→ 启动照常完成，运行时随机 500；
  * 清单重复登记同一列 —— 多次 ALTER，日志里全是失败噪音。

本门禁只做**静态一致性**校验，不连数据库、不需要迁移环境，成本极低：
表/列必须在 `Base.metadata` 里真实存在，且 (表, 列) 不重复。

用法：python tools/check_migration_columns.py    # 0=通过 1=不一致
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "backend"))

# 导入全部模型，否则 Base.metadata 里只有被 import 过的表
import app.models  # noqa: F401
from app.core.database import Base  # noqa: E402
from app.core.db_migrations import MIGRATION_COLUMNS  # noqa: E402


def main() -> int:
    errors = []
    seen = set()
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

    if errors:
        print("[FAIL] 补列清单与模型不一致：")
        for e in errors:
            print("  -", e)
        print("\n模型改字段后必须同步 db_migrations.MIGRATION_COLUMNS，")
        print("否则老库缺列会在运行时随机 500。")
        return 1
    print(f"[OK] 补列清单 {len(MIGRATION_COLUMNS)} 项与模型列一致，无重复项")
    return 0


if __name__ == "__main__":
    sys.exit(main())
