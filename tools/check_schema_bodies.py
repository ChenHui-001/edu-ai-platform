#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""契约层守护：裸 `Dict[...] = Body(...)` 不得继续增长（P1-7）。

裸 Dict 让字段拼错静默生效、类型错误到 SQL 层才炸、OpenAPI 请求体显示
成 `{}`。存量几十处一次性替换风险过高，因此采用「锁住上限、逐步下降」
的策略：新增端点必须从 `app.schemas` 取 Pydantic 模型；每迁移一处，
把 BASELINE 同步减 1。这样契约层只会变好，不会再恶化。

P2-8 的修正（旧口径可绕过）：旧正则只认 `Dict[str, Any] = Body(`，
`Dict[str, str] = Body(...)`、`Dict[str, List[int]] = Body(...)` 完全在视野
之外 —— 换个内层类型就绕过去了。现在匹配任意 `Dict[<任意>] = Body(`，
且按**出现次数**计数（同一行两个也分别算）。

用法：python tools/check_schema_bodies.py    # 0=通过 1=新增裸 Dict
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API_DIR = os.path.join(ROOT, "backend", "app", "api", "v1")

# 按新口径（任意 Dict 内层类型 + 出现次数）重测后的基线。
# **棘轮语义**：BASELINE 是"当前允许的最大值"，也是"当前实测值"。
# total < BASELINE 时必须同步下调本常量（否则 CI 红）——这样基线只会单向
# 收紧，不会出现"迁完存量忘了改常量、门禁永远停在旧上限"的假进步
# （第三轮复审 §5.3：三道门禁都只锁不增长、没有任何推动下降的机制）。
BASELINE = 63
# 目的地：迁到这个数就算还清。CI 会在未达标时提示还差多少。
TARGET = 40
PATTERN = re.compile(r"Dict\s*\[[^\[\]]*\]\s*=\s*Body\s*\(")


def main() -> int:
    hits = []
    total = 0
    for root, _dirs, files in os.walk(API_DIR):
        for name in files:
            if not name.endswith(".py"):
                continue
            path = os.path.join(root, name)
            with open(path, encoding="utf-8") as fh:
                for lineno, line in enumerate(fh, 1):
                    found = PATTERN.findall(line)
                    if found:
                        total += len(found)
                        hits.append((os.path.relpath(path, ROOT), lineno, len(found)))
    if total > BASELINE:
        print(f"[FAIL] 裸 Dict Body = {total}，超过基线 {BASELINE}")
        for path, lineno, _n in hits[:8]:
            print(f"  - {path}:{lineno}")
        print("新端点请使用 app.schemas 中的 Pydantic 模型；")
        print("迁移存量后请把本脚本 BASELINE 同步减 1。")
        return 1
    if total < BASELINE:
        print(f"[FAIL] 裸 Dict Body = {total}，低于基线 {BASELINE} —— 请同步收紧基线")
        print(f"       把 BASELINE 从 {BASELINE} 改成 {total} 后重跑。")
        print("       棘轮必须单向：迁完不降基线，等于把额度又还回去。")
        return 1
    if total > TARGET:
        print(f"[OK] 裸 Dict Body = {total}（基线 {BASELINE}，未增长）；"
              f"距目标 {TARGET} 还差 {total - TARGET} 处")
    else:
        print(f"[OK] 裸 Dict Body = {total}，已达到目标 {TARGET}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
