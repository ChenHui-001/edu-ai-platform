#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""轻量只读压测：验证单实例 SQLite 部署的真实吞吐与尾延迟。

用途：
  - 压测 health / 列表 / 详情等 GET 接口，不执行写操作；
  - 输出 RPS、p50/p95/p99、状态码分布与错误率；
  - 默认在错误率 >1% 或 p95 >500ms 时返回非零，可直接接 CI/发版前检查。

示例：
  # 只压健康检查（无需登录）
  LOAD_TEST_BASE='<服务地址>/api/v1' python tools/load_test.py --base "$LOAD_TEST_BASE" \
      --path /health --concurrency 20 --duration 10

  # 登录后压班级列表（只读）
  LOAD_TEST_PASSWORD='***' python tools/load_test.py --base "$LOAD_TEST_BASE" \
      --username admin \
      --path '/edu/classes?page_size=20' --concurrency 20 --duration 10

**不要直接压生产库**：SQLite 单写者，压测会把审计日志写放大到整库。
请在临时库/预发环境运行；生产只读压测也必须先确认业务低峰。
"""
import argparse
import json
import os
import statistics
import sys
import threading
import time
import urllib.error
import urllib.request
from collections import Counter


def _opener():
    # 绕过系统代理：压测本机服务时代理会把 127.0.0.1 也劫走
    return urllib.request.build_opener(urllib.request.ProxyHandler({}))


def _request(opener, url, token=None, timeout=10):
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = "Bearer " + token
    req = urllib.request.Request(url, headers=headers, method="GET")
    start = time.perf_counter()
    try:
        with opener.open(req, timeout=timeout) as resp:
            resp.read()
            return resp.status, (time.perf_counter() - start) * 1000, ""
    except urllib.error.HTTPError as exc:
        try:
            exc.read()
        except Exception:
            pass
        return exc.code, (time.perf_counter() - start) * 1000, f"HTTP {exc.code}"
    except Exception as exc:  # noqa: BLE001
        return 0, (time.perf_counter() - start) * 1000, f"{type(exc).__name__}: {exc}"


def login(base, username, password, timeout=10):
    opener = _opener()
    body = json.dumps({"username": username, "password": password}).encode()
    req = urllib.request.Request(
        base.rstrip("/") + "/auth/login",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with opener.open(req, timeout=timeout) as resp:
        payload = json.loads(resp.read().decode())
    token = ((payload.get("data") or {}).get("access_token") or "")
    if not token:
        raise RuntimeError(f"登录失败：{payload.get('message') or payload}")
    return token


def percentile(sorted_values, p):
    if not sorted_values:
        return 0.0
    idx = min(len(sorted_values) - 1, max(0, int(round((p / 100) * (len(sorted_values) - 1)))))
    return sorted_values[idx]


def run(args):
    base = args.base.rstrip("/")
    token = ""
    if args.username:
        password = args.password or os.environ.get("LOAD_TEST_PASSWORD", "")
        if not password:
            raise SystemExit("使用 --username 时必须提供 --password 或 LOAD_TEST_PASSWORD")
        token = login(base, args.username, password, timeout=args.timeout)
        print(f"[load] 登录成功：{args.username}")

    paths = args.path or ["/health"]
    stop = threading.Event()
    lock = threading.Lock()
    latencies = []
    statuses = Counter()
    errors = []
    count = 0

    def worker(index):
        nonlocal count
        opener = _opener()
        local_lat, local_status, local_err = [], Counter(), []
        path = paths[index % len(paths)]
        url = base + path
        while not stop.is_set():
            status, latency, err = _request(opener, url, token=token, timeout=args.timeout)
            local_lat.append(latency)
            local_status[status] += 1
            if err:
                local_err.append(err)
        with lock:
            latencies.extend(local_lat)
            statuses.update(local_status)
            errors.extend(local_err)
            count += len(local_lat)

    threads = [threading.Thread(target=worker, args=(i,), daemon=True)
               for i in range(max(1, args.concurrency))]
    print(f"[load] base={base} paths={paths} concurrency={args.concurrency} "
          f"duration={args.duration}s")
    started = time.perf_counter()
    for t in threads:
        t.start()
    time.sleep(max(0.1, args.duration))
    stop.set()
    for t in threads:
        t.join(timeout=args.timeout + 1)
    elapsed = max(0.001, time.perf_counter() - started)

    latencies.sort()
    total = len(latencies)
    ok = sum(v for k, v in statuses.items() if 200 <= k < 400)
    error_rate = (total - ok) / total if total else 1.0
    p50 = percentile(latencies, 50)
    p95 = percentile(latencies, 95)
    p99 = percentile(latencies, 99)
    avg = statistics.fmean(latencies) if latencies else 0.0
    rps = total / elapsed

    print(f"[load] total={total} ok={ok} rps={rps:.1f} "
          f"avg={avg:.1f}ms p50={p50:.1f}ms p95={p95:.1f}ms p99={p99:.1f}ms")
    print(f"[load] status={dict(sorted(statuses.items()))} error_rate={error_rate:.2%}")
    if errors:
        print(f"[load] errors(sample)={errors[:5]}")

    if args.json:
        print(json.dumps({
            "total": total, "ok": ok, "rps": rps, "avg_ms": avg,
            "p50_ms": p50, "p95_ms": p95, "p99_ms": p99,
            "status": dict(statuses), "error_rate": error_rate,
        }, ensure_ascii=False))

    if total == 0:
        print("[load][FAIL] 没有收到任何响应")
        return 1
    if error_rate > args.max_error_rate:
        print(f"[load][FAIL] 错误率 {error_rate:.2%} > {args.max_error_rate:.2%}")
        return 1
    if p95 > args.max_p95_ms:
        print(f"[load][FAIL] p95 {p95:.1f}ms > {args.max_p95_ms:.0f}ms")
        return 1
    print("[load][OK] 阈值通过")
    return 0


def main():
    parser = argparse.ArgumentParser(description="轻量只读压测")
    parser.add_argument("--base", default=os.environ.get("LOAD_TEST_BASE", ""),
                        help="服务基地址（也可用 LOAD_TEST_BASE；必须显式提供，避免误压生产）")
    parser.add_argument("--path", action="append", help="可重复，GET 相对路径")
    parser.add_argument("--username", default="", help="登录用户名；不传则匿名压测")
    parser.add_argument("--password", default="", help="登录口令；建议用 LOAD_TEST_PASSWORD")
    parser.add_argument("--concurrency", type=int, default=20)
    parser.add_argument("--duration", type=float, default=10.0)
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument("--max-error-rate", type=float, default=0.01)
    parser.add_argument("--max-p95-ms", type=float, default=500.0)
    parser.add_argument("--json", action="store_true", help="额外输出一行 JSON 摘要")
    args = parser.parse_args()
    if not args.base:
        parser.error("缺少 --base 或 LOAD_TEST_BASE；本项目不允许内置默认主机")
    try:
        return run(args)
    except KeyboardInterrupt:
        print("\n[load] 用户中断")
        return 130


if __name__ == "__main__":
    sys.exit(main())
