#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""定时任务注册守护：内置任务的 func_path 必须命中 JOB_HANDLERS（P1-6）。

`run_job()` 只认 `task_jobs.JOB_HANDLERS` 注册表。往
`init_db.DEFAULT_JOBS` 加一条内置任务却忘了在注册表补一行时：

  * 该任务永远不会执行（修复动作完全没生效）；
  * 每次到点 `run_job` 抛 `ValueError: 未找到任务处理函数`，
    scheduler 的失败分支会给**全体 sys_admin** 推一条系统通知 ——
    每天固定时间骚扰全员；
  * 管理端列表里它与正常任务外观完全一致，看不出跑不了。

原有实现靠人工目视对齐两个注册表（7 对 7 恰好齐过一次），所以这条门禁
就是那 5 行不变量。

检查两件事：
  1) `DEFAULT_JOBS` 里每个 func_path 都在 `JOB_HANDLERS` 里；
  2) `JOB_HANDLERS` 的 key 能解析成 `task_jobs` 模块里的真实可调用对象
     （防「key 拼对了、值写错/复制粘贴成别的函数」）。

用法：python tools/check_job_handlers.py    # 0=通过 1=不一致
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "backend"))

from app.services import task_jobs  # noqa: E402
from app.services.init_db import DEFAULT_JOBS  # noqa: E402
from app.services.task_jobs import JOB_HANDLERS  # noqa: E402

MODULE_PREFIX = "app.services.task_jobs."


def main() -> int:
    errors = []

    for name, func_path, cron, _desc in DEFAULT_JOBS:
        if func_path not in JOB_HANDLERS:
            errors.append(
                f"内置任务「{name}」的 func_path 未注册：{func_path}")
        if not str(cron or "").strip():
            errors.append(f"内置任务「{name}」缺少 cron 表达式")

    for key, handler in JOB_HANDLERS.items():
        if not key.startswith(MODULE_PREFIX):
            errors.append(f"注册表 key 不在 task_jobs 模块内：{key}")
            continue
        attr = key[len(MODULE_PREFIX):]
        actual = getattr(task_jobs, attr, None)
        if actual is None:
            errors.append(f"注册表 key 指向不存在的函数：{key}")
        elif actual is not handler:
            errors.append(
                f"注册表 key 与函数不匹配：{key} → {getattr(handler, '__name__', handler)}")

    if errors:
        print("[FAIL] 定时任务注册不一致：")
        for e in errors:
            print("  -", e)
        print("\n内置任务必须同时出现在：")
        print("  app/services/init_db.py::DEFAULT_JOBS（播种）")
        print("  app/services/task_jobs.py::JOB_HANDLERS（执行）")
        print("漏一处 = 任务永远不执行 + 每天给全体管理员推一条失败通知。")
        return 1

    print(f"[OK] 内置任务 {len(DEFAULT_JOBS)} 个全部命中处理函数，"
          f"注册表 {len(JOB_HANDLERS)} 项均可解析")
    return 0


if __name__ == "__main__":
    sys.exit(main())
