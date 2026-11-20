#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""本体模型一致性门禁。

校验三件事，任一失败即阻断交付：

1. **跨模型引用完整**：M1/M2/M3/M5/M6/M7/MU 之间的引用型字段不得有断链
   （委托 audit-reports/ontology-inventory/check_references.py）。
2. **M6 流程定义合规**：框架 §6.5 的七条流程约束逐条机器核对
   （委托 audit-reports/ontology-inventory/verify_m6.py）。
3. **本体副本与源文件一致**：backend/app/ontology/ 下随代码分发的副本必须与
   audit-reports/ontology-inventory/ 下的源文件逐字节相同。

第 3 条是前两条在生产环境成立的前提：容器镜像只 COPY backend/app，
没有 audit-reports/。副本一旦漏改，本地全绿而线上流程引擎找不到任何定义——
这类「本地过、线上炸」的差异最难在事后查出来。

用法：
    python tools/check_ontology_consistency.py
退出码：0 通过 / 1 有问题
"""
import filecmp
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INVENTORY = os.path.join(ROOT, "audit-reports", "ontology-inventory")
SHIPPED = os.path.join(ROOT, "backend", "app", "ontology")
ASSETS = ("m6-flow-model.yaml", "m3-rule-model.yaml")

PYTHON = sys.executable or "python3"


def _run(name, args):
    """跑一个校验器，返回 (是否通过, 输出)。"""
    path = os.path.join(INVENTORY, name)
    if not os.path.exists(path):
        return True, f"{name}: 不存在，跳过（本体目录未纳入本仓库时允许）"
    try:
        # encoding 必须显式指定：Windows 中文环境的默认编码是 GBK，
        # 而校验器输出 UTF-8 中文，不指定会在解码子进程输出时抛
        # UnicodeDecodeError——真正的失败信息反而被吞掉。
        proc = subprocess.run(
            [PYTHON, path] + args,
            capture_output=True, text=True, encoding="utf-8",
            errors="replace", cwd=INVENTORY, timeout=120,
            # 子进程必须显式按 UTF-8 输出：Windows 中文控制台默认 GBK，
            # 不设这个环境变量时子进程写的是 GBK 字节，父进程按 UTF-8 解码
            # 会得到 U+FFFD，再打印时直接 UnicodeEncodeError 崩掉——
            # 真正的校验结论反而看不到。父进程 errors="replace" 只是兜底。
            env={**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"},
        )
    except Exception as exc:  # 校验器自身崩了也算不通过
        return False, f"{name}: 执行失败 {exc}"
    output = (proc.stdout or "") + (proc.stderr or "")
    return proc.returncode == 0, output.strip()


def check_references():
    ok, out = _run("check_references.py", [])
    return ok, out


def check_m6():
    ok, out = _run("verify_m6.py", [])
    return ok, out


def check_shipped_assets():
    """随代码分发的本体副本必须与源文件一致。"""
    problems = []
    for name in ASSETS:
        source = os.path.join(INVENTORY, name)
        shipped = os.path.join(SHIPPED, name)
        if not os.path.exists(source):
            continue  # 本体目录未纳入仓库时不阻断
        if not os.path.exists(shipped):
            problems.append(
                f"{name}: 缺少随代码分发的副本 backend/app/ontology/{name}"
                "（容器镜像里没有 audit-reports/，流程引擎将找不到定义）")
            continue
        if not filecmp.cmp(source, shipped, shallow=False):
            problems.append(
                f"{name}: 副本与源文件不一致——改本体后必须同步 "
                "backend/app/ontology/ 下的副本")
    return (not problems), ("\n".join(problems) if problems else "全部一致")


def main():
    # 自身 stdout 也可能是 GBK：门禁输出含中文与本体标识符，
    # 直接 print 会 UnicodeEncodeError，让「通过/失败」本身都读不到。
    for _stream in (sys.stdout, sys.stderr):
        _reconfigure = getattr(_stream, "reconfigure", None)
        if _reconfigure is not None:
            try:
                _reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass

    failures = []

    for label, fn in (
        ("跨模型引用完整性", check_references),
        ("M6 流程定义合规", check_m6),
        ("本体副本一致性", check_shipped_assets),
    ):
        ok, detail = fn()
        if ok:
            print(f"[OK] {label}")
            if detail:
                for line in detail.splitlines()[-3:]:
                    print(f"     {line}")
        else:
            print(f"[FAIL] {label}")
            for line in detail.splitlines()[-25:]:
                print(f"     {line}")
            failures.append(label)

    print()
    if failures:
        print(f"本体一致性门禁未通过：{'、'.join(failures)}")
        return 1
    print("本体一致性门禁通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
