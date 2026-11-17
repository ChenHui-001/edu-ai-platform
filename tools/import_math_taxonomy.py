#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""导入 cn-math-taxonomy 数学 1-9 年级子集。

用法（仓库根目录）：
    python tools/import_math_taxonomy.py --source-dir C:/path/to/cn-math-taxonomy --dry-run
    python tools/import_math_taxonomy.py --source-dir C:/path/to/cn-math-taxonomy

只读取数据目录，不做网络请求；题目默认作为私有已发布题导入，避免未经
教师审核直接进入公共题库。上游为 CC BY-NC 4.0，使用前请确认授权边界。
"""
import argparse
import json
import os
import sys

BACKEND = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend")
sys.path.insert(0, BACKEND)

from app.core.database import Base, SessionLocal, engine  # noqa: E402
from app.services.math_taxonomy_import import import_math_taxonomy  # noqa: E402


def parse_grades(raw: str):
    values = set()
    for part in str(raw or "").split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            start, end = part.split("-", 1)
            values.update(range(int(start), int(end) + 1))
        else:
            values.add(int(part))
    return sorted(v for v in values if 1 <= v <= 9)


def main() -> int:
    parser = argparse.ArgumentParser(description="导入 cn-math-taxonomy 到本地知识图谱")
    parser.add_argument("--source-dir", required=True, help="上游仓库根目录")
    parser.add_argument("--grades", default="1-9", help="年级范围，如 1-9 / 7,8,9")
    parser.add_argument("--subject", default="math", help="外部学科编码，默认 math")
    parser.add_argument("--limit", type=int, default=None, help="仅导入前 N 个知识点（联调用）")
    parser.add_argument("--owner-id", type=int, default=None, help="题目 owner 用户 ID")
    parser.add_argument("--bank-type", default="private", choices=["private", "public"])
    parser.add_argument("--status", default="published",
                        choices=["draft", "published", "offline"])
    parser.add_argument("--dry-run", action="store_true", help="完整执行后回滚")
    args = parser.parse_args()

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        result = import_math_taxonomy(
            db,
            args.source_dir,
            grades=parse_grades(args.grades),
            subject=args.subject,
            dry_run=args.dry_run,
            limit=args.limit,
            owner_id=args.owner_id,
            bank_type=args.bank_type,
            status=args.status,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if not result.get("errors") else 1
    except Exception as exc:  # noqa: BLE001 CLI 需要给出可执行错误
        print(f"[FAIL] {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
