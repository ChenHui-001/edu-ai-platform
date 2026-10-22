#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
契约门禁：时间函数命名与语义一致性

## 守的是什么

`utcnow()` 曾长期返回**本地时间**（`datetime.now()`），名字与行为相反。
这类「命名撒谎」的破坏力远超普通 bug：

- 看到 `utcnow()` 会自然假设它是 UTC，于是手工再偏移 8 小时 → 时间窗全错；
- 排查时区问题时方向被带偏，把「CI runner 是 UTC」的问题归因到业务逻辑；
- 它不会报错、不会抛异常，只在跨时区环境才暴露 —— 属于最难发现的缺陷类型。

改名只是第一步，**更难的是防止它回来**。本脚本守三条契约：

### 契约 1：仓库内不得再调用旧名
`utcnow` 在 `utils/common.py` 中保留为兼容别名（供外部代码 ImportError 兜底），
但**本仓库内零调用点**。有人写 `utcnow()` 一律拦截 —— 新代码必须用
`now_local()`，语义写在名字里。

### 契约 2：时间函数不得声称自己是 UTC
扫函数 docstring / 函数名中含 `utc` 的，若实现是 `datetime.now()`（本地），
直接报错。反过来也拦：名字叫 `*_local` 却用 `datetime.now(timezone.utc)`。
这条防的是「改了名字但没改实现，或者实现被改回去了」。

### 契约 3：`/health` 必须暴露 `server_time`
这是 e2e 时间窗用例的**唯一合法时间基准**。缺失会让测试进程退回本地
`datetime.now()`，在 CI（runner UTC / 容器 +8h）上成片假失败。
本契约曾因写成 `_detect_base() + "/api/v1/health"`（BASE 已含 `/api/v1`，
实际请求 `/api/v1/api/v1/health` 必然 404）而静默失效整整一轮。

## 用法
    python tools/check_time_contract.py
退出码：0 通过 / 1 违反契约
"""
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 兼容别名所在文件：这里出现 utcnow 是**允许**的（定义本身）
LEGACY_DEF_FILE = os.path.join("backend", "app", "utils", "common.py")

# 检查器自身的说明文字里必然要提到旧名，跳过
SELF_FILE = os.path.join("tools", "check_time_contract.py")

SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "dist", "data",
             "__pycache__", ".pytest_cache"}

# 契约 2 的扫描目标：时间工具与核心模块
TIME_FUNC_FILES = [LEGACY_DEF_FILE, os.path.join("backend", "app", "core", "security.py")]


def iter_py_files():
    for root, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for fn in files:
            if fn.endswith(".py"):
                yield os.path.join(root, fn)


def rel(path):
    return os.path.relpath(path, ROOT)


# ---------------------------------------------------------------- 契约 1
def check_no_legacy_calls():
    """仓库内不得再出现 `utcnow` 调用（定义文件里的别名除外）。"""
    violations = []
    pat = re.compile(r"\butcnow\b")
    for path in iter_py_files():
        r = rel(path)
        if r in (LEGACY_DEF_FILE, SELF_FILE):
            continue
        try:
            src = io.open(path, encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        if not pat.search(src):
            continue
        for i, line in enumerate(src.splitlines(), 1):
            # 允许注释里提到旧名（说明历史原因），不允许真的调用
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            if not pat.search(line):
                continue
            # `utcnow = now_local` 这类赋值在非定义文件里也不该出现
            violations.append(f"{r}:{i}: {stripped[:100]}")
    return violations


# ---------------------------------------------------------------- 契约 2
def check_name_matches_impl():
    """名字里带 utc 的必须用 UTC 实现；名字带 local 的不得用 UTC 实现。"""
    violations = []

    utc_impl = re.compile(r"datetime\.now\(\s*(?:timezone\.utc|tz\s*=\s*timezone\.utc|UTC)\s*\)")
    local_impl = re.compile(r"datetime\.now\(\s*\)")

    for relf in TIME_FUNC_FILES:
        path = os.path.join(ROOT, relf)
        if not os.path.exists(path):
            continue
        src = io.open(path, encoding="utf-8", errors="replace").read()
        # 简易函数体切分：def <name>(...): 到下一个顶层 def
        for m in re.finditer(r"\ndef\s+(\w+)\s*\([^)]*\)[^\n]*:\n(.*?)(?=\ndef\s|\Z)",
                             src, re.S):
            name, body = m.group(1), m.group(2)
            low = name.lower()
            has_utc = bool(utc_impl.search(body))
            has_local = bool(local_impl.search(body))
            if "utc" in low and has_local and not has_utc:
                violations.append(
                    f"{relf}: 函数 `{name}()` 名字含 utc，实现却是 datetime.now()（本地时间）"
                    f" —— 名字与行为相反")
            if "local" in low and has_utc and not has_local:
                violations.append(
                    f"{relf}: 函数 `{name}()` 名字含 local，实现却是 UTC —— 名字与行为相反")
    return violations


# ---------------------------------------------------------------- 契约 3
def check_health_server_time():
    """`/health` 必须返回 server_time（e2e 时间基准的唯一来源）。"""
    path = os.path.join(ROOT, "backend", "app", "main.py")
    if not os.path.exists(path):
        return ["backend/app/main.py: 文件不存在，无法校验 server_time 契约"]
    src = io.open(path, encoding="utf-8", errors="replace").read()
    if "server_time" not in src:
        return ["backend/app/main.py: /health 未暴露 server_time —— "
                "e2e 时间窗用例将失去服务端基准，CI 上会成片假失败"]

    # 同时校验 e2e_framework 走的是主路径而不是 404 兜底
    fw = os.path.join(ROOT, "tests", "e2e_framework.py")
    if os.path.exists(fw):
        fsrc = io.open(fw, encoding="utf-8", errors="replace").read()
        # BASE 已含 /api/v1，再拼 /api/v1/health 会变成 /api/v1/api/v1/health
        bad = re.search(r"BASE\s*\+\s*[\"']/api/v1/health[\"']", fsrc)
        if bad:
            return ["tests/e2e_framework.py: 拼出了 `BASE + \"/api/v1/health\"`，"
                    "但 BASE 已包含 /api/v1 → 实际请求 /api/v1/api/v1/health 必然 404，"
                    "server_now() 会静默退回本地时间"]
    return []


def main():
    checks = [
        ("契约1 仓库内无 utcnow() 调用（别名仅保留在定义处）", check_no_legacy_calls),
        ("契约2 时间函数名与实现语义一致", check_name_matches_impl),
        ("契约3 /health 暴露 server_time 且 e2e 走主路径", check_health_server_time),
    ]
    failed = 0
    for title, fn in checks:
        try:
            bad = fn()
        except Exception as exc:  # noqa: BLE001
            print(f"[FAIL] {title} —— 检查器异常: {exc}")
            failed += 1
            continue
        if bad:
            failed += 1
            print(f"[FAIL] {title}")
            for b in bad:
                print(f"       {b}")
        else:
            print(f"[PASS] {title}")

    if failed:
        print(f"\n共 {failed} 项时间契约被违反。")
        print("  时间函数的名字必须与其真实语义一致：本仓库统一使用**上海本地时间**")
        print("  （naive，容器 TZ=Asia/Shanghai），函数名为 now_local()。")
        return 1
    print("\n[PASS] 时间契约全部通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
