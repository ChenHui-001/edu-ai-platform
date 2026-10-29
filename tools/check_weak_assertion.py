#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""扫描「恒真断言」与「弱断言」。

## 为什么需要它

最贵的浪费不是跑得慢，而是**跑出绿灯但什么都没验证**。

真实案例（一个弱断言污染三轮）：批量移出学生的用例写成

    check("管理员可批量移出学生", len(sids) >= 1, ...)

它只断言「有学生待移出」。于是移出**全部失败也照样 PASS**。
后果链：移出静默失败 → 班级删不掉（"该班级仍有 2 名学生"）→
导入测试班永久残留 → 下一轮年级/班级计数断言被顶红 →
看起来是「新 bug」，实际是三轮前埋的雷。

同样危险的是字面 `True`：

    check("前置题目已自建", True, tag)

它连「有没有建成」都不问，纯粹占位。

## 扫描范围

`tools/` 下的诊断/验证脚本（它们同样用 `check(name, cond, detail)`
宏自建断言体系，且是运维排障时唯一的判据来源）。

⚠️ 维护提示：扫描目录**必须校验存在性**。`os.walk` 对不存在的目录返回空，
会让本门禁打印 `[OK]` 却什么也没检查 —— 这种「假绿」比红灯危险得多。
本次即踩到：`tests/` 移除后本脚本曾照常打印
`[OK] 未发现恒真断言`，实际一个文件都没扫。现在目录缺失即退出码 2。

## 判定规则

1. **BLOCK**：`check(...)` 第二个实参是字面 `True` → 恒真，必须改成真实判据，
   或在行尾/上一行加 `# allow-info-only` 标注为「仅记录、不作判据」。
2. **WARN**：第二个实参形如 `len(x) >= 1` / `len(x) > 0` → 只证明「非空」，
   若该对象随后被用于删除/清理，必须回读确认。

## 用法

    python tools/check_weak_assertion.py

退出码：0 = 无 BLOCK，1 = 存在恒真断言，2 = 扫描目录缺失
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SCAN_DIRS = ["tools"]
SKIP_DIRS = {"__pycache__", "node_modules", ".git"}

ALLOW_MARK = "allow-info-only"

# check(  "name"  ,  True  ,  ...
RE_ALWAYS_TRUE = re.compile(
    r"check\(\s*(?:f?\"[^\"]*\"|f?'[^']*')\s*,\s*True\s*,"
)
# check(  "name"  ,  len(x) >= 1  , ...
RE_LEN_GE = re.compile(
    r"check\(\s*(?:f?\"[^\"]*\"|f?'[^']*')\s*,\s*len\([^)]*\)\s*(?:>=|>)\s*[01]\s*,"
)


def _scan_dirs():
    dirs, missing = [], []
    for rel in SCAN_DIRS:
        p = os.path.join(ROOT, rel)
        if os.path.isdir(p):
            dirs.append(p)
        else:
            missing.append(rel)
    return dirs, missing


def scan():
    blocks, warns = [], []
    dirs, missing = _scan_dirs()
    for base in dirs:
        for dirpath, dirnames, filenames in os.walk(base):
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
            for fn in sorted(filenames):
                if not fn.endswith(".py"):
                    continue
                if fn == "check_weak_assertion.py":   # 本文件（含示例文本）
                    continue
                path = os.path.join(dirpath, fn)
                try:
                    with open(path, encoding="utf-8", errors="ignore") as f:
                        lines = f.readlines()
                    for i, line in enumerate(lines):
                        # 允许把标注写在 check( 的**上一行**：多行写法下把注释
                        # 塞在行尾会显得很挤，且容易漏看。向上看一行就够了。
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
    return blocks, warns, missing


def main():
    blocks, warns, missing = scan()

    if missing:
        print("[FAIL] 扫描目录缺失 —— 门禁无法覆盖全部代码，拒绝静默通过")
        for m in missing:
            print(f"       缺少: {m}")
        print("     若目录确实已移除，请同步更新本脚本的 SCAN_DIRS。")
        return 2

    if warns:
        print(f"[WARN] 弱断言（仅证明非空，{len(warns)} 处）：\n")
        for path, lineno, line in warns:
            print(f"  {os.path.relpath(path, ROOT)}:{lineno}")
            print(f"    {line[:110]}")
            print("    → 若该对象随后被删除/清理，必须回读确认结果\n")

    if not blocks:
        print(f"[OK] 未发现恒真断言（已扫描 {', '.join(SCAN_DIRS)}）")
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
