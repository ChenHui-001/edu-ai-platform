#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""扫描代码中的硬编码服务地址。

## 为什么需要它

服务地址必须统一从配置/探测而来（`settings`、`E2E_BASE`、`HOST_PORT`）。
一旦某处自己写死 `http://localhost:8000/api/v1`：

- 本地默认端口跑，**恰好命中**，看不出问题；
- 换端口时（8001/8002、CI 的 8080、生产反代），就连到**另一个实例**；
- 症状通常是「401 鉴权失败」「404 接口不存在」「数据对不上」，
  看起来像业务 bug，实际是连错了服务。

真实案例：回归框架的 SSE 用例曾写死探测 `8099/8080/8000`，
回归跑在 8002 时连到 8000 的库，本次登录的 Token 在那边无效 → 报
`★ SSE 接口可访问 -> HTTP 401`，而接口本身完全正常。

## 扫描范围

**全仓库**（`backend/app`、`tools`、`frontend/src`）。
原先只扫 `tests/`，那是回归用例专属检查；测试体系移除后，风险主体回到
服务端与运维脚本本身（尤其是那些「连自己的服务」的诊断脚本）。

⚠️ 维护提示：扫描目录**必须校验存在性**。`os.walk` 对不存在的目录返回空，
会让本门禁打印 `[OK]` 却什么也没检查 —— 这种「假绿」比红灯危险得多。
`_scan_dirs()` 在目录缺失时直接报错退出（退出码 2），不再静默通过。
这一条是踩过的坑：删掉 `tests/` 后本脚本曾照常打印
`[OK] 回归用例未发现硬编码服务地址`，实际一个文件都没扫。

## 用法

    python tools/check_hardcoded_host.py            # 扫描
    python tools/check_hardcoded_host.py --fix-list # 仅列出，便于人工确认

退出码：0 = 干净，1 = 发现硬编码，2 = 扫描目录缺失（环境/结构异常）
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 参与扫描的目录（相对仓库根）。任一目录缺失即视为结构异常。
SCAN_DIRS = ["backend/app", "tools", "frontend/src"]

# 跳过：缓存、依赖、构建产物
SKIP_DIRS = {"__pycache__", "node_modules", ".git", "dist", "venv", ".venv"}

# 允许出现字面地址的文件：本文件的正则模式本身就是示例。
WHITELIST_FILES = {
    "check_hardcoded_host.py",
}

# 「已知遗留」文件：历史排查脚本，暂不强制整改，仅提示（WARN）不阻断。
LEGACY_FILES = set()

# 匹配 http://localhost:8000 / http://127.0.0.1:8080 这类带端口的本机地址
PATTERN = re.compile(
    r"https?://(?:localhost|127\.0\.0\.1|0\.0\.0\.0):\d{2,5}",
    re.IGNORECASE,
)

# 覆盖后端、运维脚本与前端
SCAN_EXTS = (".py", ".js", ".vue", ".sh")

# 行级豁免标记：写在命中行的行尾（或上一行）。
# 有些字面地址是**合法默认值**而非「连错服务」的隐患，例如 ollama 的官方
# 端点就是 http://localhost:11434，CLI 诊断工具的 argv 兜底也必须有个默认值。
# 这类不能靠文件名白名单一刀切（同一文件里可能既有合法默认又有真隐患），
# 所以用**行级标注 + 必写理由**：既放行，又留下可审计的记录。
#
#     "base_url": "http://localhost:11434/v1",  # allow-hardcoded-host: ollama 官方默认端点
ALLOW_MARK = "allow-hardcoded-host"


def _scan_dirs():
    """返回 (存在的目录, 缺失的目录) 两组。"""
    dirs, missing = [], []
    for rel in SCAN_DIRS:
        p = os.path.join(ROOT, rel)
        if os.path.isdir(p):
            dirs.append(p)
        else:
            missing.append(rel)
    return dirs, missing


def scan():
    """返回 (blocking, legacy, missing) 三组结果。"""
    blocking, legacy = [], []
    dirs, missing = _scan_dirs()
    for base in dirs:
        for dirpath, dirnames, filenames in os.walk(base):
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
            for fn in filenames:
                if not fn.endswith(SCAN_EXTS):
                    continue
                if fn in WHITELIST_FILES:
                    continue
                bucket = legacy if fn in LEGACY_FILES else blocking
                path = os.path.join(dirpath, fn)
                try:
                    with open(path, encoding="utf-8", errors="ignore") as f:
                        lines = f.readlines()
                    for idx, line in enumerate(lines, 1):
                        # 标注可写在命中行行尾或上一行（多行写法下行尾会挤）
                        prev = lines[idx - 2] if idx >= 2 else ""
                        if ALLOW_MARK in line or ALLOW_MARK in prev:
                            continue
                        for m in PATTERN.finditer(line):
                            bucket.append((path, idx, m.group(0), line.strip()))
                except OSError:
                    continue
    return blocking, legacy, missing


def _print_group(title, hits):
    print(f"{title}（{len(hits)} 处）：\n")
    for path, lineno, url, line in hits:
        rel = os.path.relpath(path, ROOT)
        print(f"  {rel}:{lineno}")
        print(f"    地址: {url}")
        print(f"    代码: {line[:110]}")
        print()


def main():
    blocking, legacy, missing = scan()

    if missing:
        print("[FAIL] 扫描目录缺失 —— 门禁无法覆盖全部代码，拒绝静默通过")
        for m in missing:
            print(f"       缺少: {m}")
        print("     若目录确实已移除，请同步更新本脚本的 SCAN_DIRS。")
        return 2

    if legacy:
        _print_group("[WARN] 历史脚本中的硬编码地址（不阻断）", legacy)

    if not blocking:
        print(f"[OK] 未发现硬编码服务地址（已扫描 {', '.join(SCAN_DIRS)}）")
        return 0

    _print_group("[FAIL] 硬编码服务地址", blocking)
    print("修复方式：改用配置项或框架导出的 BASE，不要再自己拼端口")
    print("    后端：settings.HOST_PORT / 相对路径（同源部署）")
    print("    前端：request.js 的 baseURL（默认 /api/v1）")
    print()
    print("说明：BASE 已包含 '/api/v1' 前缀，只能追加具体路径（如 '/health'）。")
    return 1


if __name__ == "__main__":
    sys.exit(main())
