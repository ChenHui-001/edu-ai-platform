"""门禁：`sys_agent_job.status` 只能用 `services/agent_job_state` 里的常量。

## 为什么需要（Q-07）

这张表的状态词被两处写成了不同拼写：教案/通用 Agent 写 `success`，
组卷写 `succeeded`。于是**每一处**"是不是已经结束"的判断都要同时列两种，
漏一个就会出现两种后果之一：

- 已完成的任务被判成"还能取消"：接口把 `cancel_requested` 置位，但 worker
  早已退出，没人消费这个标志，前端一直等一个永远不会到来的"已取消"；
- 结果被读成空：`if job.status != "success"` 遇到 `succeeded` 的行直接判失败，
  前端明明有结果却提示"生成失败"。

拼写本身没有对错，靠人记住"这里该写哪个"才是问题。所以写入侧收敛到常量，
读取侧用 `STATUS_TERMINAL`（它包含历史别名，存量行不会因为升级而改写）。

## 检查范围与**刻意不查**的部分

只查 `AgentJob` / `job` 变量：`sys_task_log`、`edu_class_request`、`sys_user`
这些表同样有 `status` 列，但词表不同（`pending` 表示"待审核"而非"待执行"），
把它们一起管起来只会逼人写一堆无意义的豁免。
"""
import os
import re
import sys

BACKEND = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend")
APP = os.path.join(BACKEND, "app")

# 定义常量的文件本身允许出现这些字面量
ALLOW_FILES = {"services/agent_job_state.py"}

JOB_STATUS_WORDS = r"(?:success|succeeded|failed|cancelled|running|pending)"

# 1) `job.status = "..."` / `== "..."` / `!= "..."`（变量名必须正好是 job）
# 2) `AgentJob.status == "..."` / `!=`
# 3) `_touch_job(..., status="...")` —— 这是写状态的唯一间接入口，绕过它等于绕过门禁
PATTERNS = [
    re.compile(r"(?<![_\w])job\.status\s*(?:=|==|!=)\s*[\"']" + JOB_STATUS_WORDS + r"[\"']"),
    re.compile(r"\bAgentJob\.status\s*(?:==|!=)\s*[\"']" + JOB_STATUS_WORDS + r"[\"']"),
    re.compile(r"\b_touch_job\s*\([^)]*status\s*=\s*[\"']" + JOB_STATUS_WORDS + r"[\"']"),
]


def iter_sources():
    for root, _dirs, files in os.walk(APP):
        for name in files:
            if not name.endswith(".py"):
                continue
            path = os.path.join(root, name)
            rel = os.path.relpath(path, BACKEND).replace("\\", "/")
            yield rel, path


def main() -> int:
    hits = []
    for rel, path in iter_sources():
        if rel in ALLOW_FILES or rel.replace("app/", "") in ALLOW_FILES:
            continue
        with open(path, encoding="utf-8") as fh:
            for lineno, line in enumerate(fh, start=1):
                stripped = line.strip()
                # 注释与文档串里的示例不算（`# status = "failed"` 这类说明）
                if stripped.startswith("#"):
                    continue
                for pat in PATTERNS:
                    if pat.search(line):
                        hits.append((rel, lineno, stripped[:110]))
                        break

    if hits:
        print("[FAIL] sys_agent_job.status 出现字面量，请改用 agent_job_state 常量：")
        for rel, lineno, text in hits:
            print(f"  {rel}:{lineno}  {text}")
        print("\n  可用常量：STATUS_PENDING / STATUS_RUNNING[1] / STATUS_SUCCEEDED /")
        print("            STATUS_FAILED / STATUS_CANCELLED")
        return 1
    print("[OK] sys_agent_job.status 全部走 agent_job_state 常量，无字面量写死")
    return 0


if __name__ == "__main__":
    sys.exit(main())
