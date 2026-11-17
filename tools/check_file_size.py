#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""上帝文件预算门禁：存量只许降，新增不许再长。

为什么需要：大文件不是靠一次“重构周”解决的，而是靠每次提交都不让它继续长。
本脚本给当前超长文件登记一个**只降不升**的行数预算；新增文件超过全局阈值
也会失败。预算不是目标，拆分后请同步下调预算。
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 2026-11-17 基线。拆分后同步下调；不要为“通过”而上调。
BUDGETS = {
    "frontend/src/views/admin/KnowledgeManage.vue": 2138,
    "backend/app/api/v1/question.py": 2049,
    "tools/gen_knowledge_points.py": 2049,
    "backend/app/api/v1/knowledge.py": 1820,
    "frontend/src/views/teacher/QuestionBank.vue": 1716,
    "frontend/src/views/teacher/PaperWizard.vue": 1656,
    "backend/app/api/v1/paper_compose.py": 1626,
    "backend/app/api/v1/edu.py": 1409,
    "backend/app/services/init_db.py": 1381,
    "frontend/src/views/teacher/PaperManage.vue": 1263,
    "backend/app/api/v1/task.py": 1260,
    "backend/app/services/paper_compose_engine.py": 1193,
    "frontend/src/views/teacher/PaperEdit.vue": 1137,
}

# 未登记文件超过该阈值即失败：防止新上帝文件出现。
GLOBAL_LIMIT = 1200
SCAN_DIRS = ("backend/app", "frontend/src", "tools")
EXTS = (".py", ".js", ".vue")
SKIP_DIRS = {"node_modules", "dist", "__pycache__", ".git", "data"}


def count_lines(path):
    with open(path, "rb") as fh:
        return sum(1 for _ in fh)


def iter_files():
    for rel_dir in SCAN_DIRS:
        base = os.path.join(ROOT, rel_dir)
        for root, dirs, files in os.walk(base):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            for name in files:
                if name.endswith(EXTS):
                    full = os.path.join(root, name)
                    rel = os.path.relpath(full, ROOT).replace("\\", "/")
                    yield rel, full


def main():
    failures = []
    rows = []
    for rel, full in iter_files():
        lines = count_lines(full)
        budget = BUDGETS.get(rel)
        if budget is None and lines > GLOBAL_LIMIT:
            failures.append(f"{rel}: {lines} 行，超过未登记文件阈值 {GLOBAL_LIMIT}")
        elif budget is not None and lines > budget:
            failures.append(f"{rel}: {lines} 行，超过预算 {budget}（只许降不许升）")
        if budget is not None or lines >= 900:
            rows.append((lines, budget, rel))

    rows.sort(key=lambda r: r[0], reverse=True)
    print("=== 上帝文件预算（行数 / 预算）===")
    for lines, budget, rel in rows:
        flag = "OVER" if budget is not None and lines > budget else ""
        print(f"  {lines:>5} / {str(budget or '-'):>5}  {rel}  {flag}")

    if failures:
        print("\n[FAIL] 文件体积门禁未通过：")
        for item in failures:
            print("  - " + item)
        print("\n拆分建议：先抽纯函数/服务到 services 或 composables，再拆路由/模板。")
        return 1
    print(f"\n[OK] {len(BUDGETS)} 个存量文件未超预算；新增文件均 <= {GLOBAL_LIMIT} 行")
    return 0


if __name__ == "__main__":
    sys.exit(main())
