#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""CSS 变量守护：禁止自引用、禁止引用未定义的变量。

## 为什么需要这条门禁

2026-11-09 发生过一次**全站级静默回归**，症状是「教学管理等页面的按钮变成
透明 / 白色，看不见」，根因在 `frontend/src/styles/index.css` 的第一行：

    --el-color-primary: var(--el-color-primary);   /* ← 自引用 */

CSS 自定义属性一旦**自引用**就形成循环，按 CSS Variables Level 1 的规定，
该属性的计算值变成 *guaranteed-invalid*（而不是回落到 Element Plus 的默认值）。
后果不是"颜色没生效"，而是**所有引用它的声明整体失效**：

  * `el-button--primary` 的 `--el-button-bg-color: var(--el-color-primary)`
    → `background-color` 无效 → 取初始值 `transparent`；文字是 `--el-color-white`
    （#fff）、边框也是 currentColor（白）→ **白字透明底白框的"空按钮"**，
    在白卡片上完全不可见；
  * `linear-gradient(135deg, var(--el-color-primary) 0%, …)` → **整条
    background 声明失效** → 登录页品牌区的蓝紫渐变整块消失；
  * `color: var(--el-color-primary)` → 无效 → 对可继承属性回落到 inherit，
    链接与统计数字退回黑色，失去主色语义。

而 `light-3/5/7/9` 与 `dark-2` 仍是 `#2f6fd0` 家族，于是同一套按钮里
**混进了两个色相**（实心填充是 Element 默认青蓝 #409eff，hover/边框却是品牌蓝）。

引入原因是一次性的"硬编码色令牌化"批量替换：脚本把 `#2f6fd0` 全仓换成
`var(--el-color-primary)`，**连定义行本身也一起换了**。仓库里没有这个脚本，
所以只能靠门禁兜住。

本门禁查两件事：
  ① 自引用：`--x: var(--x)`（同一条声明内）—— CSS 循环，必失效；
  ② 引用未定义：`var(--x)` 的 `--x` 在项目源码与 Element Plus 样式里都找不到
     —— 计算值同样是 guaranteed-invalid。

用法：python tools/check_css_tokens.py    # 0=通过 1=存在失效变量
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "frontend", "src")
EP_CSS = os.path.join(ROOT, "frontend", "node_modules", "element-plus", "dist", "index.css")

DEF_RE = re.compile(r"(--[A-Za-z0-9_-]+)\s*:")
USE_RE = re.compile(r"var\(\s*(--[A-Za-z0-9_-]+)")
SCAN_EXT = (".vue", ".css", ".scss")


def iter_files():
    for base, dirs, files in os.walk(SRC):
        dirs[:] = [d for d in dirs if d not in ("node_modules", "__tests__", "dist")]
        for name in files:
            if name.endswith(SCAN_EXT):
                yield os.path.join(base, name)


def main() -> int:
    if not os.path.isdir(SRC):
        print(f"[FAIL] 目录不存在：{SRC}")
        return 1

    defined = set()
    self_refs = []
    uses = {}

    for path in iter_files():
        rel = os.path.relpath(path, ROOT)
        with open(path, encoding="utf-8", errors="replace") as f:
            for lineno, line in enumerate(f, 1):
                for m in DEF_RE.finditer(line):
                    var = m.group(1)
                    defined.add(var)
                    # 同一行声明里引用自己 → CSS 循环
                    if re.search(r"var\(\s*" + re.escape(var) + r"\s*\)", line[m.end():]):
                        self_refs.append((rel, lineno, line.strip()))
                for m in USE_RE.finditer(line):
                    uses.setdefault(m.group(1), []).append((rel, lineno, line.strip()[:100]))

    # Element Plus 自带的设计变量（--el-color-primary / --el-fill-color-* 等）
    ep_defined = set()
    ep_css_ok = os.path.exists(EP_CSS)
    if ep_css_ok:
        with open(EP_CSS, encoding="utf-8", errors="replace") as f:
            ep_defined = set(DEF_RE.findall(f.read()))

    failed = False

    if self_refs:
        failed = True
        print(f"[FAIL] 发现 {len(self_refs)} 处 CSS 变量自引用（循环 → guaranteed-invalid）：")
        for rel, lineno, text in self_refs:
            print(f"  - {rel}:{lineno}  {text[:100]}")
        print()
        print("自引用的变量计算值为 guaranteed-invalid，引用它的**整条声明**失效：")
        print("  · el-button--primary → 背景 transparent + 白字白框 = 看不见的按钮")
        print("  · linear-gradient(...var(--x)...) → 整条 background 失效 → 渐变消失")
        print("修法：定义处必须写字面值，例如 --el-color-primary: #2f6fd0;")
        print()

    # Element Plus 的样式没装出来时无法判断"是否未定义"（--el-* 几乎全是它提供的），
    # 此时只报自引用，不把「找不到 element-plus」误报成几百个未定义变量。
    if not ep_css_ok:
        print(f"[??] 找不到 {EP_CSS}（element-plus 未安装），跳过「未定义引用」检查。")
        print("     自引用检查已执行，结果见上。")
    else:
        undefined = {
            var: refs for var, refs in uses.items()
            if var not in defined and var not in ep_defined
        }
        if undefined:
            failed = True
            print(f"[FAIL] 发现 {len(undefined)} 个未定义的 CSS 变量引用：")
            for var, refs in sorted(undefined.items()):
                print(f"  - {var}（{len(refs)} 处）")
                for rel, lineno, text in refs[:3]:
                    print(f"      {rel}:{lineno}  {text}")
            print()
            print("未定义变量的引用同样落到 guaranteed-invalid，请先定义或改用已存在的变量。")
            print()

    if failed:
        return 1

    if not ep_css_ok:
        print(f"[OK] {len(defined)} 个项目内定义变量，无自引用（未定义引用检查已跳过）")
        return 0

    print(
        f"[OK] {len(defined)} 个项目内定义变量 / {len(ep_defined)} 个 Element Plus 变量，"
        f"{len(uses)} 种引用全部有效，无自引用"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
