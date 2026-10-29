#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
静态检查门禁：ruff --select F,E9

## 为什么只查 F 类

F（Pyflakes）全部是「几乎必然是真缺陷」的规则：

    F401 未使用导入      → 复制粘贴残留、重构后忘记删
    F811 重复定义        → 后者覆盖前者，功能静默失效
    F821 未定义名        → 运行到该行必然 NameError
    F841 未使用变量      → 常见于「算出来了却没进断言」的假绿用例
    F541 空 f-string     → 少写了对齐/占位符
    E9   语法/IO 错误    → 连编译都过不去

刻意**不**纳入 E501（行长）、I001（导入排序）等风格规则：一次接入就产生
几百条纯风格告警，团队会直接关掉，等于白做。

## 为什么单独包一层脚本

1. CI 与本地（auto_ship.sh）用**同一份**命令，避免「本地过 CI 不过」；
2. ruff 未安装时给出**可执行**的安装提示，而不是一句 ModuleNotFoundError；
3. 固定扫描目录，防止有人 `ruff check .` 扫到 node_modules / 临时目录
   而报出与代码无关的告警。

## 用法

    python tools/lint_gate.py            # 检查（CI / 提交前）
    python tools/lint_gate.py --install-hint   # 只打印安装方式

退出码：0 通过 / 1 有告警 / 2 环境缺 ruff
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# 扫描目录。`tests/` 已随测试体系移除，不要再加回来 —— 目录不存在时
# ruff 会报 E902 并返回非零，把整个门禁变成"因环境缺失而红"的噪声。
TARGETS = ["backend/app", "tools"]

INSTALL_HINT = """\
ruff 未安装。任选一种方式：
  pip install ruff                          # 本机已有 Python 环境
  winget install astral-sh.ruff             # Windows
  brew install ruff                         # macOS
  pipx install ruff                         # 隔离安装（推荐）

安装后复跑：python tools/lint_gate.py
"""


def find_ruff():
    """找 ruff 可执行文件。

    顺序：环境变量 RUFF_BIN（CI/自定义安装路径显式指定）→ PATH → 模块方式。
    """
    env_bin = (os.environ.get("RUFF_BIN") or "").strip()
    if env_bin and Path(env_bin).exists():
        return [env_bin]
    exe = shutil.which("ruff")
    if exe:
        return [exe]
    for py in (sys.executable, "python", "python3"):
        try:
            r = subprocess.run([py, "-m", "ruff", "--version"],
                               capture_output=True, text=True, timeout=30)
            if r.returncode == 0:
                return [py, "-m", "ruff"]
        except (OSError, subprocess.SubprocessError):
            continue
    return None


def main():
    if "--install-hint" in sys.argv:
        print(INSTALL_HINT)
        return 0

    cmd = find_ruff()
    if not cmd:
        print("[FAIL] 未找到 ruff —— 静态门禁无法执行", file=sys.stderr)
        print(INSTALL_HINT, file=sys.stderr)
        return 2

    # 目录存在性预检：ruff 对不存在的路径报 E902 并返回非零，症状是
    # 「门禁因目录缺失而红」，与代码质量无关，极易被误判成真的有告警。
    # 这里提前拦下，给出明确原因。
    missing = [t for t in TARGETS if not (ROOT / t).is_dir()]
    if missing:
        print("[FAIL] 扫描目录缺失 —— 门禁无法覆盖全部代码", file=sys.stderr)
        for m in missing:
            print(f"       缺少: {m}", file=sys.stderr)
        print("     若目录确实已移除，请同步更新 tools/lint_gate.py 的 TARGETS。",
              file=sys.stderr)
        return 2

    args = cmd + ["check", "--output-format", "concise"] + TARGETS
    print(f"$ {' '.join(args)}", flush=True)
    r = subprocess.run(args, cwd=str(ROOT))

    if r.returncode == 0:
        print("[PASS] ruff --select F,E9 无告警")
        return 0

    print(
        "\n[FAIL] 存在 F/E9 类告警。\n"
        "  这些规则只覆盖「一定是缺陷」的情况（未定义名、未使用导入、\n"
        "  未使用变量、空 f-string、语法错误），请修复而不是加 noqa 绕过。\n"
        "  确属误报时用**行级** `# noqa: F401` 并写明原因，不要整文件豁免。",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
