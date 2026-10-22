#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""扫描 e2e 用例中的「恒真断言」与「弱断言」。

## 为什么需要它

本地回归最贵的浪费不是跑得慢，而是**跑出绿灯但什么都没验证**。

真实案例（一个弱断言污染三轮）：批量移出学生的用例写成

    check("管理员可批量移出学生", len(sids) >= 1, ...)

它只断言「有学生待移出」。于是移出**全部失败也照样 PASS**。
后果链：移出静默失败 → 班级删不掉（"该班级仍有 2 名学生"）→
`[E2E-RS-] 导入测试班` 永久残留 → 下一轮 `test_admin` 的年级/班级
计数断言被顶红 → 看起来是「新 bug」，实际是三轮前埋的雷。

同样危险的是字面 `True`：

    check("前置题目已自建", True, tag)

它连「有没有建成」都不问，纯粹占位。

## 判定规则

1. **BLOCK**：`check(...)` 第二个实参是字面 `True` → 恒真，必须改成真实判据，
   或在行尾加 `# allow-info-only` 标注为「仅记录、不作判据」。
2. **WARN**：第二个实参形如 `len(x) >= 1` / `len(x) > 0` → 只证明「非空」，
   若该对象随后被用于删除/清理，必须回读确认。

## 用法

    python tools/check_weak_assertion.py

退出码：0 = 无 BLOCK，1 = 存在恒真断言。
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCAN_DIR = os.path.join(ROOT, "tests")

ALLOW_MARK = "allow-info-only"

# check(  "name"  ,  True  ,  ...
RE_ALWAYS_TRUE = re.compile(
    r"check\(\s*(?:f?\"[^\"]*\"|f?'[^']*')\s*,\s*True\s*,"
)
# check(  "name"  ,  len(x) >= 1  , ...
RE_LEN_GE = re.compile(
    r"check\(\s*(?:f?\"[^\"]*\"|f?'[^']*')\s*,\s*len\([^)]*\)\s*(?:>=|>)\s*[01]\s*,"
)


def scan():
    blocks, warns = [], []
    for dirpath, dirnames, filenames in os.walk(SCAN_DIR):
        dirnames[:] = [d for d in dirnames if d not in
                       ("__pycache__", "node_modules", ".git", "ui_e2e")]
        for fn in sorted(filenames):
            if not fn.startswith("test_") or not fn.endswith(".py"):
                continue
            path = os.path.join(dirpath, fn)
            try:
                with open(path, encoding="utf-8", errors="ignore") as f:
                    lines = f.readlines()
                for i, line in enumerate(lines):
                    # 允许把标注写在 check( 的**上一行**：多行写法下把注释塞在
                    # 行尾会显得很挤，且容易漏看。向上看一行就够了。
                    prev = lines[i - 1] if i > 0 else ""
                    if ALLOW_MARK in line or ALLOW_MARK in prev:
                        continue
                    lineno = i + 1
                    if RE_ALWAYS_TRUE.search(line):
                        blocks.append((path, lineno, line.strip()))
                    elif RE_LEN_GE.search(line):
                        warns.append((path, lineno, line.strip()))
            except OSError:
                continue
    return blocks, warns


def main():
    blocks, warns = scan()

    if warns:
        print(f"[WARN] 弱断言（仅证明非空，{len(warns)} 处）：\n")
        for path, lineno, line in warns:
            print(f"  {os.path.relpath(path, ROOT)}:{lineno}")
            print(f"    {line[:110]}")
            print("    → 若该对象随后被删除/清理，必须回读确认结果\n")

    if not blocks:
        print("[OK] 未发现恒真断言（check(..., True, ...)）")
        return 0

    print(f"[FAIL] 恒真断言（{len(blocks)} 处）：\n")
    for path, lineno, line in blocks:
        print(f"  {os.path.relpath(path, ROOT)}:{lineno}")
        print(f"    {line[:110]}")
        print()
    print("修复方式（二选一）：")
    print("  1) 改成真实判据，例如 check(name, resp.get('success') is True, detail)")
    print("  2) 确属「仅记录信息、不参与判定」时，在行尾加注释：")
    print("     check(name, True, detail)  # allow-info-only")
    return 1


if __name__ == "__main__":
    sys.exit(main())
