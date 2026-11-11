#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""新增代码覆盖守护：关键模块必须有测试盯着，且测试总量只许涨不许跌。

## 为什么需要这条门禁

第三轮复审的核心指控是「**新写的代码没有被新写的门禁覆盖**」：一轮 4585 行
新代码（`utils/confirm.js`、重写的 `main.js`、`fatal_guard.py`、演示造数、
3 个 Pydantic 模型），自动化测试增量是 **0**。同一句话在第二轮报告里已经写过
一遍，于是第二轮修完又原样发生了一次。

「新代码必须有测试」没法用静态分析精确判定，所以这里用两条可执行的近似：

  1. **登记制**：`REGISTRY` 里每个模块都必须被某个测试文件真正 import。
     只写注释提到不算 —— 必须是 import 语句或动态 import。
  2. **棘轮**：pytest 的 `def test_` 数量与 vitest 的 `it/test(` 数量
     不得低于基线。测试被删掉时 CI 立刻变红，逼着同步下调基线（且要写出理由）。

新增一个「值得测的关键模块」时，把它加进 REGISTRY 并补测试——
直接 `python tools/check_new_code_tests.py --update` 会把当前值写成新基线，
但 REGISTRY 需要人工登记（故意的：登记这个动作本身就是在问"它被测了吗"）。

用法：
  python tools/check_new_code_tests.py             # 0=通过 1=失败
  python tools/check_new_code_tests.py --update    # 把当前实测值写成新基线
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ---------------- 登记表：模块 → 必须 import 它的测试文件 ----------------
# 只登记「逻辑藏在这里、出错症状肉眼难以发现」的模块：
# 错误分拣、取消语义、空产出判定、限流键、容器自杀、选项契约……
# 纯展示组件（页面 .vue）不在此列 —— 它们靠功能回归覆盖。
REGISTRY = {
    # 前端：全局错误分拣（哪些弹红条、哪些是用户取消）
    "frontend/src/utils/errors.js": [
        "frontend/src/utils/__tests__/errors.test.js",
    ],
    # 前端：消息框统一出口（取消返回布尔值，不抛异常）
    "frontend/src/utils/confirm.js": [
        "frontend/src/utils/__tests__/confirm.test.js",
    ],
    # 前端：AI 生成「空产出」判定（0 条不能弹"生成完成"）
    "frontend/src/utils/agentResult.js": [
        "frontend/src/utils/__tests__/agentResult.test.js",
    ],
    # 前端：组卷按钮禁用原因（回归表现为"按钮恒灰"）
    "frontend/src/utils/paperWizard.js": [
        "frontend/src/utils/__tests__/paperWizard.test.js",
    ],
    # 后端：选项形状归一（写入/读取唯一真源，P1-C 的根治层）
    "backend/app/utils/options.py": ["backend/qa_audit_suite.py"],
    # 后端：限流键摘要 + 表有界（P1-B）
    "backend/app/services/rate_limit.py": ["backend/qa_audit_suite.py"],
    # 后端：判分口径（错题重算必须与演示数据自洽）
    "backend/app/utils/answer.py": ["backend/qa_audit_suite.py"],
    # 后端：通知唯一写入出口 + 订阅偏好（"关掉了却照发"肉眼看不出来）
    "backend/app/services/notification.py": ["backend/qa_audit_suite.py"],
    # 后端：导出文件的落盘名/时效/属主校验（404 变 200 就是泄题）
    "backend/app/services/export_job.py": ["backend/qa_audit_suite.py"],
    # 前端：导出任务轮询编排（按非终态结束 = 下载到空文件）
    "frontend/src/utils/exportJob.js": [
        "frontend/src/utils/__tests__/exportJob.test.js",
    ],
    # 部署：supervisord FATAL → 容器退出（否则 Up + 全站 502）
    "deploy/fatal_guard.py": ["backend/qa_audit_suite.py"],
    # 工具：四层一致性合议（服务器落后不能被其它层绿灯掩盖）
    "tools/check_four_layer.py": ["backend/qa_audit_suite.py"],
    # 工具：部署器重建命令（少一个 flag 就是静默降级 / 空库）
    "tools/deploy_release.py": ["backend/qa_audit_suite.py"],
}

# ---------------- 棘轮基线（只许涨） ----------------
# 计数口径是**测试函数个数**，不是 pytest 报的 "N passed"：
# 带 `@pytest.mark.parametrize` 的函数会在运行时展开成多条，
# 拿运行数做基线会让同一次改动在两个口径间来回对不上。
BASELINE = {
    "pytest_cases": 71,   # def test_* 个数（运行 73 passed，含 2 条参数化展开）
    "vitest_cases": 87,
}

PYTEST_FILE = "backend/qa_audit_suite.py"
VITEST_DIR = "frontend/src/utils/__tests__"
PYTEST_RE = re.compile(r"^def test_\w+\(", re.M)
VITEST_RE = re.compile(r"^\s*(?:it|test)\s*\(", re.M)


def read(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
        return f.read()


def imported_by(test_rel, module_rel):
    """测试文件是否**真的** import 了这个模块（注释里提到不算）。"""
    if not os.path.exists(os.path.join(ROOT, test_rel)):
        return False
    text = read(test_rel)
    stem = os.path.splitext(os.path.basename(module_rel))[0]
    # JS: from '../confirm' / from '@/utils/confirm' / import('../confirm')
    # PY: from app.utils.options import ... / importlib 按路径加载
    patterns = [
        rf"from\s+['\"][^'\"]*{re.escape(stem)}['\"]",
        rf"import\s*\(\s*['\"][^'\"]*{re.escape(stem)}['\"]",
        rf"from\s+[\w.]*{re.escape(stem)}+\s+import",
        rf"import\s+[\w.]*{re.escape(stem)}\b",
        re.escape(os.path.basename(module_rel)),
    ]
    code = "\n".join(line.split("//", 1)[0].split("#", 1)[0]
                     for line in text.splitlines())
    return any(re.search(p, code) for p in patterns)


def count_pytest():
    if not os.path.exists(os.path.join(ROOT, PYTEST_FILE)):
        return 0
    return len(PYTEST_RE.findall(read(PYTEST_FILE)))


def count_vitest():
    base = os.path.join(ROOT, VITEST_DIR)
    if not os.path.isdir(base):
        return 0
    total = 0
    for name in sorted(os.listdir(base)):
        if name.endswith((".test.js", ".spec.js")):
            total += len(VITEST_RE.findall(read(os.path.join(VITEST_DIR, name))))
    return total


def main() -> int:
    update = "--update" in sys.argv

    errors = []
    for module_rel, tests in REGISTRY.items():
        if not os.path.exists(os.path.join(ROOT, module_rel)):
            errors.append(f"登记的模块不存在（改名了？）：{module_rel}")
            continue
        if not any(imported_by(t, module_rel) for t in tests):
            errors.append(
                f"模块没有测试盯：{module_rel}\n"
                f"      期望以下测试之一 import 它：{', '.join(tests)}")

    actual = {"pytest_cases": count_pytest(), "vitest_cases": count_vitest()}

    if update:
        print("# 把下面这段同步进 BASELINE（确认减少是有意的再改）")
        for k in ("pytest_cases", "vitest_cases"):
            print(f'    "{k}": {actual[k]},')
        return 0 if not errors else 1

    for key, floor in BASELINE.items():
        if actual[key] < floor:
            errors.append(
                f"{key} 从 {floor} 降到 {actual[key]}：测试被删了。\n"
                f"      如果是有意删除，请同步下调 BASELINE 并写清原因。")

    if errors:
        print(f"[FAIL] 新增代码覆盖守护：{len(errors)} 项不满足")
        for e in errors:
            print("  -", e)
        print()
        print("背景：第二轮、第三轮复审各出现过一次「新代码零覆盖」。")
        print("新增关键模块时：登记进 REGISTRY + 补测试 + 更新基线。")
        return 1

    print(f"[OK] {len(REGISTRY)} 个关键模块均有测试 import；"
          f"pytest={actual['pytest_cases']} vitest={actual['vitest_cases']}"
          f"（基线 {BASELINE['pytest_cases']}/{BASELINE['vitest_cases']}）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
