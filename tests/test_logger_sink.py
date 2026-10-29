"""日志文件 sink 的开关与多进程行为（L 组）。

## 为什么这组测试值得存在

`core/logger.py` 原来的写法是 `if settings.LOG_DIR:` 无条件加 FileSink，
而 `LOG_DIR` 默认 `./data/logs` —— 即**默认就开**。两个后果：

① 全仓没有任何代码读那个文件。真实通道是 stdout（`docker logs`）和
   `sys_error_log` 表（`/logs/error` 页面查的是表）。写文件是纯冗余。

② 多 worker 下直接报错且**不会退出**。loguru 的 FileSink 以独占方式打开
   文件，`--workers 2` 时第二个进程拿到
   `PermissionError: [Errno 13] Permission denied: '.../app_2026-xx-xx.log'`；
   loguru 把这个异常吞掉打到 stderr，于是 N-1 个 worker 全程没有文件日志，
   而进程还活着、`/health` 也绿。这种「少了几个进程的日志」极难发现。

所以现在的契约是：
  - 默认只加控制台 sink（L1/L2）
  - 显式 `LOG_FILE_SINK=true` 才写文件，且文件名带 pid（L3/L4/L6）
  - 多进程各自一份，不互相抢、不报权限错（L7/L8/L9）
  - 目录不存在自动建；建不出来也只降级不崩（L10/L11）

## 为什么用子进程而不是直接调 setup_logging

`logger.add()` 是**进程级**副作用，一旦在测试进程里加了 sink 就摘不干净，
会污染同进程里的其它断言（尤其 L1「不产生文件」必须先跑且必须干净）。
子进程还能顺便测「多进程抢同一个路径」这个真实场景 —— 同进程内根本复现
不出来。
"""
import glob
import os
import re
import subprocess
import sys
import tempfile

_BACKEND = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))

# 子进程脚本：只做「读环境变量 → setup_logging → 写 5 条日志 → 退出」。
# 走 app.core.logger 的真实实现，不是复刻一份配置。
_CHILD = r'''
import os, sys, time
sys.path.insert(0, os.environ["BE"])
from app.core.logger import setup_logging, get_logger
setup_logging()
log = get_logger("sinkprobe")
for i in range(5):
    log.info(f"probe pid={os.getpid()} i={i}")
    time.sleep(0.02)
print("CHILD_OK", os.getpid())
'''

_PASSED = 0
_FAILED = []


def ok(name, cond, detail=""):
    global _PASSED
    if cond:
        _PASSED += 1
        print(f"  [PASS] {name}" + (f"  -> {detail}" if detail else ""))
    else:
        _FAILED.append(name)
        print(f"  [FAIL] {name}" + (f"  -> {detail}" if detail else ""))


def _run(log_dir, enable, n=1):
    """起 n 个真子进程，返回 [(rc, stdout, stderr)] 与产生的日志文件列表。"""
    env = dict(os.environ)
    env.update({
        "BE": _BACKEND,
        "LOG_DIR": log_dir,
        "LOG_FILE_SINK": "true" if enable else "false",
        "LOG_TO_DB": "false",
        "SCHEDULER_ENABLED": "false",
        "SECRET_KEY": "x" * 48,
        "DATABASE_URL": "sqlite:///" + os.path.join(log_dir, "t.db").replace("\\", "/"),
    })
    procs = [
        subprocess.Popen(
            [sys.executable, "-c", _CHILD], env=env, cwd=_BACKEND,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        for _ in range(n)
    ]
    outs = []
    for p in procs:
        o, e = p.communicate(timeout=180)
        outs.append((p.returncode,
                     o.decode("utf-8", "replace"),
                     e.decode("utf-8", "replace")))
    files = sorted(glob.glob(os.path.join(log_dir, "app_*.log")))
    return outs, files


def _child_pid(stdout):
    for line in stdout.splitlines():
        if line.startswith("CHILD_OK"):
            return line.split()[1]
    return None


def main():
    print("\n" + "=" * 66)
    print("日志文件 sink：默认关闭 / 开关生效 / 多进程不抢文件")
    print("=" * 66)

    # ---------- L0：默认值守卫 ----------
    #
    # ★ 这一条必须单独写，且必须**在完全不给 LOG_FILE_SINK 环境变量**的子进程里读。
    # 原因是我第一版把「默认关闭」交给 L1 一① 去守，结果反向验证（把
    # config.py 的默认值改成 True）时 **15/15 全绿** —— 因为 `_run()` 每次都显式
    # 注入了 `LOG_FILE_SINK=false`，把默认值覆盖掉了。L1 守的其实是「开关生效」，
    # 不是「默认值保守」。缺了这条，「默认值哪天被改回 True」这个回归无人拦。
    print("\nL0、默认值守卫 —— 不给环境变量时必须是关闭的")
    _env = dict(os.environ)
    _env.pop("LOG_FILE_SINK", None)   # 关键：不能有任何外部注入干扰
    _env["BE"] = _BACKEND
    _probe = subprocess.run(
        [sys.executable, "-c",
         "import os,sys; sys.path.insert(0, os.environ['BE']);"
         "from app.core.config import Settings;"
         "print('DEFAULT=', Settings().LOG_FILE_SINK)"],
        env=_env, cwd=_BACKEND, capture_output=True, text=True, timeout=180,
    )
    _line = next((ln for ln in _probe.stdout.splitlines() if ln.startswith("DEFAULT=")), "")
    _default = _line.split("=", 1)[1].strip() if _line else "<读不到>"
    ok("L0 ① ★ 不给 LOG_FILE_SINK 时默认值是 False（不是 True）",
       _default == "False", f"Settings().LOG_FILE_SINK={_default}")
    ok("L0 ② 读取默认值本身不报错", _probe.returncode == 0,
       f"rc={_probe.returncode}, stderr={_probe.stderr[:120]}")

    with tempfile.TemporaryDirectory() as tmp:
        # ---------- L1/L2：显式关闭 ----------
        print("\nL1、显式 false —— 不产生任何日志文件")
        d_off = os.path.join(tmp, "off")
        os.makedirs(d_off)
        outs, files = _run(d_off, enable=False)
        ok("L1 ① ★ 默认（LOG_FILE_SINK=false）不产生任何日志文件",
           len(files) == 0, f"files={[os.path.basename(f) for f in files]}")
        ok("L1 ② 关闭时子进程正常退出",
           all(rc == 0 for rc, _, _ in outs), f"rc={[r for r, _, _ in outs]}")
        ok("L1 ③ 关闭时日志仍然打到 stderr（控制台 sink 不受影响）",
           "probe pid=" in outs[0][2], f"stderr长度={len(outs[0][2])}")

        # ---------- L2：开关生效 ----------
        print("\nL2、LOG_FILE_SINK=true 才写文件")
        d_on = os.path.join(tmp, "on")
        os.makedirs(d_on)
        outs, files = _run(d_on, enable=True)
        ok("L2 ① ★ 打开后产生日志文件", len(files) == 1,
           f"files={[os.path.basename(f) for f in files]}")
        ok("L2 ② 子进程仍正常退出", all(rc == 0 for rc, _, _ in outs),
           f"rc={[r for r, _, _ in outs]}")
        if files:
            content = open(files[0], encoding="utf-8").read()
            # 文件 sink 没配 format，用 loguru 默认格式（不含模块名），
            # 所以不能断言 "sinkprobe" —— 只断言行数与内容。
            ok("L2 ③ 文件里确实有那 5 条日志",
               content.count("probe pid=") == 5 and "i=4" in content,
               f"len={len(content)}, 条数={content.count('probe pid=')}")

            # ---------- L3：文件名带 pid ----------
            print("\nL3、文件名必须带 pid —— 否则多 worker 会抢同一个路径")
            m = re.search(r"app_(\d+)_\d{4}-\d{2}-\d{2}\.log$",
                          os.path.basename(files[0]))
            pid_in_name = m.group(1) if m else None
            ok("L3 ① ★ 文件名形如 app_<pid>_<date>.log", pid_in_name is not None,
               f"name={os.path.basename(files[0])}")
            ok("L3 ② ★ 名字里的 pid 就是实际写日志的进程 pid",
               pid_in_name == _child_pid(outs[0][1]),
               f"name={pid_in_name} vs child={_child_pid(outs[0][1])}")

        # ---------- L4：多进程不抢文件 ----------
        print("\nL4、两进程同开 —— 不得出现 PermissionError")
        d_multi = os.path.join(tmp, "multi")
        os.makedirs(d_multi)
        outs, files = _run(d_multi, enable=True, n=2)
        errs = " ".join(e for _, _, e in outs)
        ok("L4 ① ★ 无 PermissionError / Permission denied",
           "PermissionError" not in errs and "Permission denied" not in errs,
           f"stderr片段={errs[:160].replace(chr(10), ' ') or '(空)'}")
        ok("L4 ② ★ 两进程各写一份（文件名里的 pid 不同）", len(files) == 2,
           f"files={[os.path.basename(f) for f in files]}")
        ok("L4 ③ 两进程都正常退出",
           all(rc == 0 for rc, _, _ in outs), f"rc={[r for r, _, _ in outs]}")
        if len(files) == 2:
            for f in files:
                c = open(f, encoding="utf-8").read()
                ok(f"L4 ④ 每份文件各有 5 条（{os.path.basename(f)}）",
                   c.count("probe pid=") == 5, f"条数={c.count('probe pid=')}")

        # ---------- L5：目录不存在 ----------
        print("\nL5、目录不存在时自动创建")
        d_nested = os.path.join(tmp, "ro", "sub", "deep")
        outs, files = _run(d_nested, enable=True)
        ok("L5 ① ★ 多级目录不存在也能起来（setup_logging 自己 makedirs）",
           all(rc == 0 for rc, _, _ in outs) and len(files) == 1,
           f"rc={[r for r, _, _ in outs]}, files={len(files)}")
        ok("L5 ② 创建出来的目录里确实有日志内容",
           bool(files) and "probe pid=" in open(files[0], encoding="utf-8").read(),
           f"files={[os.path.basename(f) for f in files]}")

    total = _PASSED + len(_FAILED)
    print(f"\n  日志 sink 回归完成：共 {total} 项 | 通过 {_PASSED} | 失败 {len(_FAILED)}")
    if _FAILED:
        print("\n失败用例：")
        for n in _FAILED:
            print(f"  - {n}")
    print(f"{'=' * 66}\n")
    return 1 if _FAILED else 0


if __name__ == "__main__":
    sys.exit(main())
