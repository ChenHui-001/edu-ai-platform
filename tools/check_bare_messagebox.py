#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""消息框守护：全站禁止裸用 ElMessageBox，必须走 utils/confirm.js。

## 为什么需要这条门禁

Element Plus 的 `ElMessageBox.confirm/prompt` 被用户「取消 / 关闭」时，
reject 的是**裸字符串** `'cancel'` / `'close'`，不是 Error。调用点只要少写一个
`catch`，rejection 就冒泡到 `app.config.errorHandler`，于是用户只是点了「取消」，
页面却弹「页面运行时错误：cancel」并挂一条盖住页头的红条（P1-9）。

第一轮修法是在 main.js 里加一条「一切非对象都算业务错误」的宽规则，症状确实
消失了 —— 但代价是真故障被一起吞掉（P2-B）。第三轮复审实测：全站 44 处
`await ElMessageBox.*` 有 21 处不在 try 块里，而新写的 `utils/confirm.js`
**只被用了 1 处**，实质是死代码（P2-C）。

正确的分工是：**调用点自己吃掉取消语义**（`confirmAction` 返回布尔值），
全局兜底只处理真正的异常。这条门禁就守这个分工：`frontend/src` 里出现
`ElMessageBox.confirm/prompt/alert` 即失败，唯一豁免是 `utils/confirm.js`
（它就是那个统一出口）。

用法：python tools/check_bare_messagebox.py    # 0=通过 1=存在裸用
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "frontend", "src")

# 唯一允许直接触碰 ElMessageBox 的模块
ALLOWED = {os.path.join("frontend", "src", "utils", "confirm.js")}

# 只盯「会 reject」的三个方法：ElMessageBox.close() 之类不产生 rejection
BARE = re.compile(r"ElMessageBox\s*\.\s*(confirm|prompt|alert)\s*\(")

SCAN_EXT = (".vue", ".js")


def iter_files():
    for base, dirs, files in os.walk(SRC):
        dirs[:] = [d for d in dirs if d not in ("node_modules", "__tests__")]
        for name in files:
            if name.endswith(SCAN_EXT):
                yield os.path.join(base, name)


def main() -> int:
    if not os.path.isdir(SRC):
        print(f"[FAIL] 目录不存在：{SRC}")
        return 1

    hits = []
    scanned = 0
    for path in iter_files():
        rel = os.path.relpath(path, ROOT)
        if rel.replace("/", os.sep) in ALLOWED or rel in ALLOWED:
            continue
        scanned += 1
        with open(path, encoding="utf-8") as f:
            for lineno, line in enumerate(f, 1):
                # 行内注释里的示例不算（如 `// 不再调用 ElMessageBox.confirm`）
                code = line.split("//", 1)[0]
                if BARE.search(code):
                    hits.append((rel, lineno, line.strip()))

    if hits:
        print(f"[FAIL] 发现 {len(hits)} 处裸用 ElMessageBox：")
        for rel, lineno, text in hits:
            print(f"  - {rel}:{lineno}  {text[:100]}")
        print()
        print("改为：")
        print("  import { confirmAction, promptAction, alertAction } from '@/utils/confirm'")
        print("  if (!await confirmAction('确认删除？')) return      // 取消=false，不抛异常")
        print("  const v = await promptAction('请输入名称')          // 取消=null")
        print("  alertAction('提示内容')                            // 内部已吞掉 close")
        print()
        print("裸用 ElMessageBox 的后果：用户点「取消」→ 全局兜底弹")
        print("「页面运行时错误：cancel」+ 红条（P1-9 / P2-C）。")
        return 1

    print(f"[OK] {scanned} 个文件未见裸用 ElMessageBox（统一出口 utils/confirm.js）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
