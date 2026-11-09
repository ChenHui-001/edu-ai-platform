#!/usr/bin/env python3
"""supervisord 事件监听器：backend / nginx 进入 FATAL 时让**容器**退出。

## 为什么需要它

`supervisord.conf` 里 `startretries=5`。重试耗尽后 supervisord 会把该 program
置为 FATAL **并停止重试**，但 supervisord 自身不退出 —— 于是：

  容器 PID 1 仍是 supervisord → 容器不退出 → `restart: unless-stopped` 不生效
  → nginx 照常运行并反代到 8000 → **全站 502**
  → healthcheck 只把容器标成 unhealthy，Docker 不会因此重启

从运维视角这比「容器直接退出」隐蔽得多：`docker ps` 显示 Up(unhealthy)，
看不出是 FATAL；而真实故障是「一条迁移写错 = 全站不可用」。

本监听器把「program FATAL」翻译成「supervisord 收到 SIGTERM」→ 容器退出 →
Docker 的重启策略真正接管；确定性故障会表现为 `Restarting`，一眼可见。

## 为什么用 SIGTERM 而不是直接 exit

supervisord 对「event listener 异常退出」的处理在不同版本上语义略有差异。
向 PID 1 发 SIGTERM 是 supervisord 明确支持的优雅关闭信号（会先停所有子进程），
行为确定、不依赖版本细节。发送失败才退回 exit 1。

## supervisord 协议

event listener 每收到一个事件，必须在 stdout 回一行 `RESULT 2\\nOK`，
否则 supervisord 会认为监听器阻塞并停止派发后续事件。
"""
import os
import signal
import sys

# 任何一个挂掉都等于「站点不可用」：backend 挂了是 502，nginx 挂了是连不上
GUARDED_PROGRAMS = ("backend", "nginx")


def _ack() -> None:
    sys.stdout.write("RESULT 2\nOK")
    sys.stdout.flush()


def main() -> int:
    for line in sys.stdin:
        header = line.rstrip("\n")
        if not header:
            continue
        if "eventname:PROCESS_STATE_FATAL" not in header:
            _ack()
            continue
        # 事件体在下一行：`processname:backend groupname:edu ...`
        body = sys.stdin.readline().rstrip("\n")
        _ack()
        program = ""
        for token in body.split():
            if token.startswith("processname:"):
                program = token.split(":", 1)[1]
                break
        if program not in GUARDED_PROGRAMS:
            continue
        sys.stderr.write(
            f"[fatal_guard] {program} 已进入 FATAL（startretries 耗尽，supervisord "
            f"不会自动再拉起）。主动让容器退出，交给 Docker 的重启策略接管。\n"
            f"[fatal_guard] 请查看上方 uvicorn/nginx 日志定位根因；"
            f"若是「结构迁移失败」，按日志给出的表名/列名在库中补齐后重启即可。\n")
        sys.stderr.flush()
        try:
            os.kill(1, signal.SIGTERM)   # PID 1 = supervisord
        except Exception as exc:         # noqa: BLE001
            sys.stderr.write(f"[fatal_guard] 发送 SIGTERM 失败（{exc}），直接退出\n")
            return 1
        # 等 supervisord 收尾；正常情况这里不会再返回
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
