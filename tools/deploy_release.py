#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
生产部署器 —— 把「本地/仓库/镜像」的版本落到服务器，并保证失败可回滚。

## 为什么不在服务器上手工 `docker rm -f && docker run`

历史上每次手工部署都会漏一步，且漏了都不报错：

| 漏掉的步骤 | 后果 |
|---|---|
| 没备份就重建 | 新版本启动迁移失败 → 数据卷被写坏 → 只能回滚到备份，而备份不存在 |
| 重建时重生成 SECRET_KEY | 全员 JWT 失效，编辑到一半的老师被踢回登录页 |
| 重建时少传一个 `-e` | AI 静默降级 / 定时任务不跑 / 验证码关闭（安全回退） |
| 启动后没验健康 | 容器 `Up` 但 502，第二天才被发现 |
| 失败后没有回滚路径 | 只能现场手写 `docker run`，凭记忆拼参数 |

这个脚本把上述每一步都固化成顺序步骤，任何一步失败立即停止并按原样回滚。

## 与旧脚本的关系

仓库外 `deploy_scripts/deploy_run.py` 是历史版本（能跑，但没有备份/回滚/健康门禁）。
**本脚本是唯一规范入口**：它在仓库内，改动会走 review 与 CI 门禁。

## 用法

    python tools/deploy_release.py --dry-run     # 只打印将执行的命令（不连服务器）
    python tools/deploy_release.py --preflight  # 只做本地预检（干净/已推送/镜像存在）
    python tools/deploy_release.py --yes        # 真正部署 VERSION 指向的版本

退出码：0 成功 / 1 预检失败 / 2 部署失败（已回滚）/ 3 环境不可达（SSH/凭据）

## 环境变量（全部可选）

    PROD_HOST / PROD_PORT     默认 186.241.77.194 / 8081
    DEPLOY_PASS               无则读仓库外 deploy_scripts/.deploy_pass
    KEEP_BACKUPS              默认 10，保留最近多少个预部署备份
"""
import argparse
import base64
import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from check_release_consistency import sh  # noqa: E402

HOST = os.environ.get("PROD_HOST", "186.241.77.194")
PORT = os.environ.get("PROD_PORT", "8081")
IMAGE_REPO = os.environ.get("GHCR_IMAGE", "ghcr.io/chenhui-001/edu-ai-platform")
BASE_DIR = "/opt/edu-ai-platform"
CONTAINER = "edu-platform"
PASS_FILE = os.path.join(os.path.dirname(ROOT), "deploy_scripts", ".deploy_pass")
KEEP_BACKUPS = int(os.environ.get("KEEP_BACKUPS", "10"))

# 容器创建时由 Docker 自己注入、或镜像内已固化的变量：
# 从旧容器抄环境时**必须剔除**，否则会把旧容器的 HOSTNAME/PATH 带进新容器。
INJECTED = {"PATH", "HOSTNAME", "HOME", "PWD", "TERM", "LANG", "GPG_KEY",
            "PYTHON_VERSION", "PYTHON_SHA256", "PYTHON_GET_PIP_URL",
            "PYTHON_GET_PIP_SHA256", "PYTHON_SETUPTOOLS_VERSION",
            "PYTHON_PIP_VERSION", "LD_PRELOAD", "SSL_CERT_FILE"}


# ---------------------------------------------------------------- 基础
def _fail(code, msg):
    """按约定退出码失败。

    坑：`sys.exit("字符串")` 在 Python 里**恒退 1**，并把字符串打到 stderr ——
    写了 [3] 也拿不到 3。约定退出码必须用整数，所以走这个包装。
    """
    print(msg, file=sys.stderr)
    return code


def read_version():
    with open(os.path.join(ROOT, "VERSION"), encoding="utf-8") as fh:
        return fh.read().strip()


def read_dotenv(path=None):
    out = {}
    path = path or os.path.join(ROOT, ".env")
    try:
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                out[k.strip()] = v.strip()
    except OSError:
        pass
    return out


def load_pass():
    pwd = os.environ.get("DEPLOY_PASS", "").strip()
    if pwd:
        return pwd
    try:
        with open(PASS_FILE, encoding="utf-8") as fh:
            return fh.read().strip()
    except OSError:
        return ""


class Remote:
    """一次连接跑完全部命令：SSH 握手成本高，且本机链路容易抖。"""

    def __init__(self, dry_run=False):
        self.dry = dry_run
        self.c = None

    def __enter__(self):
        if self.dry:
            return self
        pwd = load_pass()
        if not pwd:
            raise SystemExit(_fail(3, "找不到部署凭据：设 DEPLOY_PASS 或放 deploy_scripts/.deploy_pass"))
        try:
            import paramiko
        except ImportError:
            raise SystemExit(_fail(3, "缺 paramiko：pip install paramiko"))
        import logging
        logging.getLogger("paramiko").setLevel(logging.CRITICAL)
        paramiko.util.log_to_file(os.devnull)
        self.c = paramiko.SSHClient()
        self.c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            self.c.connect(HOST, username="root", password=pwd, timeout=20,
                           banner_timeout=20, auth_timeout=20)
        except Exception as exc:  # noqa: BLE001
            raise SystemExit(_fail(3,
                f"SSH 不可达（{type(exc).__name__}）。\n"
                f"    先验证选路：PowerShell `Find-NetRoute -RemoteIPAddress {HOST}`\n"
                f"    若指向 Meta/mihomo TUN 而非 WLAN，说明本机 /32 直连路由失效（见 GOTCHAS）。"))
        return self

    def __exit__(self, *exc):
        if self.c:
            self.c.close()
        return False

    def run(self, cmd, timeout=600, quiet=False):
        if self.dry:
            print(f"    $ {cmd}")
            return ""
        _, out, _ = self.c.exec_command(cmd, timeout=timeout)
        so = out.read().decode("utf-8", "replace")
        out.channel.recv_exit_status()
        if not quiet and so.strip():
            print("    " + so.strip()[:400].replace("\n", "\n    "))
        return so


# ---------------------------------------------------------------- 步骤
def preflight(version, strict=True):
    """本地侧断言：干净、已推送、镜像真的存在。

    strict=False（--dry-run）时只把问题打出来、不当场中止 —— 干跑的目的
    是看命令长什么样，不该被"改动还没提交"挡住。
    """
    print("== 1/6 预检 ==")
    problems = []
    code, head, _ = sh(["git", "rev-parse", "HEAD"])
    head = head.strip()
    code, origin, _ = sh(["git", "rev-parse", "origin/master"])
    origin = origin.strip()
    code, dirty, _ = sh(["git", "status", "--porcelain"])
    dirty = [ln for ln in dirty.splitlines() if ln.strip()]
    image = f"{IMAGE_REPO}:{version}"

    if dirty:
        problems.append(f"工作区有 {len(dirty)} 个未提交文件（部署会把未入库的改动留在本地，先提交）")
    if head != origin:
        problems.append(f"本地 HEAD {head[:7]} != origin/master {origin[:7]}（先 push，否则镜像与服务器对不上）")
    code, _, err = sh(["docker", "image", "inspect", image])
    if code != 0:
        problems.append(f"本地没有镜像 {image}（先 docker pull 或等 CI 构建完成）")

    print(f"  版本 {version} / HEAD {head[:7]} / 镜像 {image}")
    for p in problems:
        print(f"  [!!] {p}")
    if problems and strict:
        print("  预检未通过，已中止（未连接服务器）")
        return 1, head
    if problems:
        print("  （dry-run 忽略以上问题，仅演示命令）")
        return 0, head
    print("  预检通过")
    return 0, head


def backup(remote, old_version, stamp):
    """WAL 热备：复制正在使用的库不能 `cp`（会拿到撕裂的 -wal），必须用 sqlite backup API。"""
    print("  方式：容器内 sqlite3 backup API（不能 cp，会读到撕裂的 -wal）")
    name = f"pre-{stamp}-{old_version}.db"
    remote.run(f"docker exec {CONTAINER} mkdir -p /app/data/backups", quiet=True)
    py = ('import sqlite3;'
          's=sqlite3.connect("/app/data/edu_platform.db");'
          f'd=sqlite3.connect("/app/data/backups/{name}");'
          's.backup(d);d.close();s.close();'
          'print("backup ok")')
    remote.run(f"docker exec {CONTAINER} python -c '{py}'")
    remote.run(f"docker exec {CONTAINER} sh -c 'ls -l /app/data/backups/{name}'", quiet=True)
    # 备份是唯一的安全网，必须先确认它真的落盘再继续。
    # （容器不存在=首装，此时没有数据可备，跳过校验。）
    has_container = bool(remote.run(
        f"docker ps -a --filter name=^/{CONTAINER}$ --format '{{{{.Names}}}}'", quiet=True).strip())
    if has_container and not remote.dry:
        size = remote.run(
            f"docker exec {CONTAINER} sh -c 'wc -c < /app/data/backups/{name}'",
            quiet=True).strip()
        if not size.isdigit() or int(size) < 4096:
            raise SystemExit(_fail(1, f"[!!] 备份文件异常（{size or '空'} 字节），已中止："
                                      f"没有备份就不重建容器"))
        print(f"  备份完成：{name}（{int(size) // 1024} KB）")
    # 只留最近 N 份：备份挤满磁盘会连带把容器写挂
    remote.run("docker exec {c} sh -c 'ls -1t /app/data/backups/pre-*.db 2>/dev/null | "
               "tail -n +{n} | xargs -r rm -f'".format(c=CONTAINER, n=KEEP_BACKUPS + 1),
               quiet=True)
    return name


def collect_env(remote):
    """以**运行中容器的环境**为基线：它已验证可用，重建时不应引入任何变化。

    只有容器不存在（首装）才回落到仓库 .env —— 两条路都收敛到同一份
    KEY=VALUE，避免「手工加过的变量在重建时消失」这类静默降级。
    """
    if remote.dry:
        return {}, "dry-run 未读取"
    raw = remote.run(f"docker inspect {CONTAINER} --format "
                     f"'{{{{range .Config.Env}}}}{{{{println .}}}}{{{{end}}}}'", quiet=True)
    env = {}
    for line in raw.splitlines():
        line = line.strip()
        if not line or "=" not in line:
            continue
        k, v = line.split("=", 1)
        if k in INJECTED:
            continue
        env[k] = v
    if env:
        env.pop("APP_VERSION", None)
        return env, "运行中容器"

    dot = read_dotenv()
    for k in ("LLM_ENABLED", "LLM_PROVIDER", "LLM_BASE_URL", "LLM_MODEL",
              "LLM_API_KEY", "LLM_MAX_TOKENS", "LLM_TEMPERATURE", "LLM_TIMEOUT",
              "LOG_LEVEL", "SCHEDULER_ENABLED", "MAX_UPLOAD_SIZE", "DEBUG",
              "SEED_DEMO_DATA", "SEED_BASE_DATA"):
        if dot.get(k):
            env[k] = dot[k]
    return env, "仓库 .env（首装回落）"


def write_env_file(remote, env):
    """把环境写进服务器上的 0600 文件，再用 --env-file 传给容器。

    为什么不用一长串 `-e K=V`：值里有空格/引号时会被 sh 拆开，
    而且 `docker inspect` 的输出会把这些值原样暴露在进程列表里。
    """
    body = "\n".join(f"{k}={v}" for k, v in sorted(env.items())) + "\n"
    b64 = base64.b64encode(body.encode("utf-8")).decode("ascii")
    remote.run(f"echo {b64} | base64 -d > {BASE_DIR}/.env.runtime && "
               f"chmod 600 {BASE_DIR}/.env.runtime", quiet=True)
    return f"{BASE_DIR}/.env.runtime"


def run_cmd(version, env_file, secret_key, image):
    return (
        f"docker run -d --name {CONTAINER} --restart unless-stopped "
        f"-p {PORT}:80 "
        f"-v {BASE_DIR}/data:/app/data "
        f"-v {BASE_DIR}/logs:/app/data/logs "
        f"--env-file {env_file} "
        f"-e APP_VERSION={version} "
        f"-e SECRET_KEY={secret_key} "
        f"-e DATABASE_URL=sqlite:////app/data/edu_platform.db "
        f"-e TZ=Asia/Shanghai "
        f"{image}"
    )


def wait_healthy(remote, expect_version, tries=30):
    """健康门禁：不只看 healthy，还要看版本号 —— 容器成功起来但跑的是旧镜像的情形真实存在。"""
    if remote.dry:
        print(f"    （dry-run 跳过健康门禁，期望 version={expect_version}）")
        return True
    for i in range(tries):
        raw = remote.run(f"curl -s -m 5 http://127.0.0.1:{PORT}/api/v1/health", quiet=True)
        try:
            data = (json.loads(raw).get("data") or {})
        except Exception:  # noqa: BLE001
            data = {}
        if data.get("status") == "healthy":
            if data.get("version") == expect_version:
                print(f"  健康（第 {i + 1} 次探测）version={data.get('version')}")
                return True
            print(f"  容器健康但版本是 {data.get('version')}，期望 {expect_version}，继续等待…")
        time.sleep(3)
    return False


def main():
    ap = argparse.ArgumentParser(description="把 VERSION 指向的版本安全部署到生产")
    ap.add_argument("--yes", action="store_true", help="确认执行（不加只做预检）")
    ap.add_argument("--dry-run", action="store_true", help="只打印命令，不连服务器")
    ap.add_argument("--preflight", action="store_true", help="只做本地预检")
    args = ap.parse_args()

    version = read_version()
    image = f"{IMAGE_REPO}:{version}"
    rc, head = preflight(version, strict=not args.dry_run)
    if rc != 0 or args.preflight or not args.yes and not args.dry_run:
        if rc == 0:
            print("\n加 --yes 才会真正部署（--dry-run 可先看命令）")
        return rc

    stamp = time.strftime("%Y%m%d-%H%M%S")
    with Remote(dry_run=args.dry_run) as remote:
        print("== 2/6 读取现状 ==")
        old_tag = remote.run(f"docker inspect {CONTAINER} --format '{{{{.Config.Image}}}}'",
                             quiet=True).strip()
        old_version = old_tag.rsplit(":", 1)[-1] if old_tag else "none"
        print(f"  当前运行：{old_tag or '(无容器)'}")

        print("== 3/6 备份数据库 ==")
        name = backup(remote, old_version, stamp)

        print("== 4/6 拉取镜像 ==")
        remote.run(f"docker pull {image}", timeout=1800)
        secret = remote.run(f"cat {BASE_DIR}/.secret_key", quiet=True).strip()
        if not secret and not args.dry_run:
            print("  [!!] 服务器缺 .secret_key，中止（重建会让 JWT 全失效）")
            return 1
        if args.dry_run:
            secret = "$(cat {}/.secret_key)".format(BASE_DIR)

        env, src = collect_env(remote)
        print(f"  环境基线：{src}（{len(env)} 项）")
        env_file = write_env_file(remote, env)

        print("== 5/6 重建容器 ==")
        remote.run(f"docker rm -f {CONTAINER} 2>&1 || true", quiet=True)
        remote.run(run_cmd(version, env_file, secret, image), timeout=300)

        if args.dry_run:
            print("\n[dry-run] 未实际执行")
            return 0

        print("== 6/6 健康门禁 ==")
        if wait_healthy(remote, version):
            raw = remote.run(f"docker exec {CONTAINER} sh -c 'cat /app/BUILD_INFO'", quiet=True)
            commit = ""
            for line in raw.splitlines():
                if line.startswith("commit="):
                    commit = line.split("=", 1)[1].strip()
            ok = commit.startswith(head[:7]) if commit else False
            print(f"  BUILD_INFO commit={commit[:7] or '?'} / 本地 HEAD={head[:7]} -> "
                  f"{'一致' if ok else '不一致'}")
            if not ok:
                print("  [!!] 版本号对但 commit 不一致：镜像不是由这个提交构建的")
                return 2
            print(f"\n部署完成：{old_version} -> {version}（备份 {name}）")
            return 0

        print("  [!!] 健康门禁超时，开始回滚")
        remote.run(f"docker logs --tail 40 {CONTAINER} 2>&1", quiet=True)
        if old_tag:
            remote.run(f"docker rm -f {CONTAINER} 2>&1 || true", quiet=True)
            remote.run(run_cmd(old_version, env_file, secret, old_tag), timeout=300)
            if wait_healthy(remote, old_version):
                print(f"  已回滚到 {old_version}（数据库备份：{name}）")
            else:
                print("  [!!] 回滚也失败：需要人工介入，备份在 /app/data/backups/" + name)
        return 2


if __name__ == "__main__":
    sys.exit(main())
