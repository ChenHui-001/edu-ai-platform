#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""扫描测试代码中硬编码的服务地址。

## 为什么需要它

回归用例必须通过 `e2e_framework.BASE`（由 `E2E_BASE` / `HOST_PORT` 探测而来）
访问服务。一旦某个用例自己写死 `http://localhost:8000/api/v1`：

- 本地默认端口跑，**恰好命中**，看不出问题；
- 换端口时（隔离库 8001/8002、CI 的 8080、自定义），就连到**另一个实例**；
- 症状通常是「401 鉴权失败」「404 接口不存在」「数据对不上」，
  看起来像业务 bug，实际是连错了服务。

真实案例：`test_agent_struct.py` 的 SSE 用例写死探测 `8099/8080/8000`，
回归跑在 8002 时连到 8000 的库，本次登录的 Token 在那边无效 → 报
`★ SSE 接口可访问 -> HTTP 401`，而接口本身完全正常。

## 用法

    python tools/check_hardcoded_host.py            # 扫描 tests/
    python tools/check_hardcoded_host.py --fix-list # 仅列出，便于人工确认

退出码：0 = 干净，1 = 发现硬编码。
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCAN_DIR = os.path.join(ROOT, "tests")

# 允许出现字面地址的文件：框架自身就是负责「探测端口」的地方。
WHITELIST_FILES = {
    "e2e_framework.py",
}

# 「已知遗留」文件：不在 run_all.py 的 15 个阶段内，不被回归执行，
# 因此不会污染回归结论。它们属于历史排查脚本，暂不强制整改，
# 仅提示（WARN），不阻断门禁。
# ⚠️ 若将来把这些脚本纳入回归，必须先删除本名单中的对应项。
LEGACY_FILES = {
    "verify_sse_live.py",
    "verify_sys_secrets.py",
    "verify_system_admin.py",
    "verify_system_admin_v2.py",
    "verify_agent_access.py",
    "verify_analysis_stats.py",
    "verify_learning_access.py",
    "verify_teaching_defects.py",
}

# 匹配 http://localhost:8000 / http://127.0.0.1:8080 这类带端口的本机地址
PATTERN = re.compile(
    r"https?://(?:localhost|127\.0\.0\.1|0\.0\.0\.0):\d{2,5}",
    re.IGNORECASE,
)


def scan():
    """返回 (blocking, legacy) 两组命中。"""
    blocking, legacy = [], []
    for dirpath, dirnames, filenames in os.walk(SCAN_DIR):
        dirnames[:] = [d for d in dirnames if d not in
                       ("__pycache__", "node_modules", ".git", "ui_e2e")]
        for fn in filenames:
            if not fn.endswith(".py"):
                continue
            if fn in WHITELIST_FILES:
                continue
            bucket = legacy if fn in LEGACY_FILES else blocking
            path = os.path.join(dirpath, fn)
            try:
                with open(path, encoding="utf-8", errors="ignore") as f:
                    for lineno, line in enumerate(f, 1):
                        for m in PATTERN.finditer(line):
                            bucket.append((path, lineno, m.group(0), line.strip()))
            except OSError:
                continue
    return blocking, legacy


def _print_group(title, hits):
    print(f"{title}（{len(hits)} 处）：\n")
    for path, lineno, url, line in hits:
        rel = os.path.relpath(path, ROOT)
        print(f"  {rel}:{lineno}")
        print(f"    地址: {url}")
        print(f"    代码: {line[:110]}")
        print()


def main():
    blocking, legacy = scan()

    if legacy:
        _print_group("[WARN] 历史脚本中的硬编码地址（不在回归体系内，不阻断）", legacy)

    if not blocking:
        print("[OK] 回归用例未发现硬编码服务地址（统一走 BASE）")
        return 0

    _print_group("[FAIL] 回归用例中的硬编码服务地址", blocking)
    print("修复方式：改用框架导出的 BASE，不要再自己拼端口")
    print("    from e2e_framework import BASE")
    print("    urllib.request.urlopen(BASE + '/health', timeout=5)")
    print()
    print("说明：BASE 已包含 '/api/v1' 前缀，只能追加具体路径（如 '/health'）。")
    return 1


if __name__ == "__main__":
    sys.exit(main())
