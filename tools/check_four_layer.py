#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
四层一致性巡检 —— 本地 / 仓库 / 镜像 / 服务器

## 为什么要单独有这一层

`check_release_consistency.py` 管的是**发布链路**（VERSION → commit → 镜像 →
health），它保证「发出去的东西是对的」，但**不知道服务器上跑的是哪一版**。
真实事故是：镜像发得好好的，服务器还停在三天前的版本 —— 前三次复审里的
安全修复（账号枚举、限流、找回密码节流）全部没上线，而所有 CI 都是绿的。

这一层把「运行时第四层」也变成断言：

    本地 worktree  ==  origin/master  ==  镜像 BUILD_INFO  ==  服务器容器 BUILD_INFO

## 用法

    python tools/check_four_layer.py              # 全量（含 git fetch）
    python tools/check_four_layer.py --no-fetch   # 不联网拉仓库（离线/发版后立刻用）
    python tools/check_four_layer.py --skip-server  # 只查前三层（无生产环境时）
    python tools/check_four_layer.py --json       # 机读

退出码：0 四层一致 / 1 存在漂移 / 2 无法判定（如服务器不可达，且没有其他漂移）

## 服务器层怎么取

1. 首选 SSH（读 `/app/BUILD_INFO` 拿 version+commit，最硬的证据）；
   凭据来自 `DEPLOY_PASS` 或仓库外 `deploy_scripts/.deploy_pass`，不落命令行、不打印。
2. SSH 不可达时降级为 HTTP `/api/v1/health`：只能拿到 version，commit 标未知，
   该层判定降级为 DEGRADED（不当作漂移，但也不当作通过）。
   典型场景：本机到服务器的 /32 直连路由失效（mihomo TUN 按端口丢包，8081 仍通）。
"""
import argparse
import json
import os
import sys
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

# 复用发布链路校验器里已经打磨过的「读镜像指纹」逻辑：
# 它有 ① BUILD_INFO ② OCI label 三级回退，重复实现只会多一份漂移源。
from check_release_consistency import (  # noqa: E402
    image_embedded_commit,
    image_embedded_version,
    sh,
)

IMAGE_REPO = os.environ.get("GHCR_IMAGE", "ghcr.io/chenhui-001/edu-ai-platform")
PROD_HOST = os.environ.get("PROD_HOST", "186.241.77.194")
PROD_PORT = os.environ.get("PROD_PORT", "8081")
PASS_FILE = os.path.join(os.path.dirname(ROOT), "deploy_scripts", ".deploy_pass")

OK, BAD, WARN, NA = "OK", "DRIFT", "DEGRADED", "UNKNOWN"


# ---------------------------------------------------------------- 工具
def git(*args, timeout=60):
    code, out, err = sh(["git", *args], timeout=timeout)
    return (out.strip() if code == 0 else None), err.strip()


def read_version():
    try:
        with open(os.path.join(ROOT, "VERSION"), encoding="utf-8") as fh:
            return fh.read().strip()
    except OSError:
        return "?"


def short(sha):
    return (sha or "?")[:7]


def load_pass():
    pwd = os.environ.get("DEPLOY_PASS", "").strip()
    if pwd:
        return pwd
    try:
        with open(PASS_FILE, encoding="utf-8") as fh:
            return fh.read().strip()
    except OSError:
        return ""


# ---------------------------------------------------------------- 四层
def layer_local(version):
    head, _ = git("rev-parse", "HEAD")
    dirty, _ = git("status", "--porcelain")
    dirty_n = len([ln for ln in (dirty or "").splitlines() if ln.strip()])
    r = {"layer": "本地 worktree", "version": version, "commit": head,
         "status": OK, "note": ""}
    if not head:
        r.update(status=NA, note="不是 git 仓库")
    elif dirty_n:
        # 有未提交改动 = 本地已经不是任何已发布版本，必须显式报出来
        r.update(status=BAD, note=f"{dirty_n} 个文件未提交")
    else:
        r["note"] = "工作区干净"
    return r


def layer_remote(fetch=True):
    r = {"layer": "远端 origin/master", "version": "?", "commit": None,
         "status": NA, "note": ""}
    if fetch:
        code, out, err = sh(["git", "fetch", "origin", "--quiet"], timeout=120)
        if code != 0:
            r["note"] = f"fetch 失败（按上次已知远端状态判定）：{err[:80]}"
    head, _ = git("rev-parse", "origin/master")
    if not head:
        r["note"] = r["note"] or "无 origin/master（还没推送过）"
        return r
    r["commit"] = head
    ver, _ = git("show", f"{head}:VERSION")
    r["version"] = (ver or "?").strip()
    if r["note"]:
        r["status"] = WARN
    else:
        r["status"] = OK
        r["note"] = "已推送"
    return r


def layer_image(version):
    image = f"{IMAGE_REPO}:{version}"
    r = {"layer": f"镜像 :{version}", "version": "?", "commit": None,
         "status": NA, "note": "", "image": image}

    # ① 本地已有该镜像 → 直接读 BUILD_INFO（快、不需网络，发版后必然是这条路径）
    code, _, _ = sh(["docker", "image", "inspect", image], timeout=60)
    if code == 0:
        ver, src = image_embedded_version(image)
        commit, _ = image_embedded_commit(image)
        r["version"] = ver or "?"
        r["commit"] = commit
        if not ver:
            r["note"] = f"本地镜像读不到版本（{src}）"
            return r
        if ver != version:
            r.update(status=BAD, note=f"镜像内版本 {ver} != VERSION {version}")
            return r
        if not commit:
            r.update(status=WARN, note="镜像未烧入 commit（旧构建）")
            return r
        r.update(status=OK, note="BUILD_INFO 自洽（本地镜像）")
        return r

    # ② 本地没有 → 问 registry 这个标签在不在。
    #    这里只判「存在性」，判不了 commit。网络类失败与「标签不存在」必须区分：
    #    前者是 [??] 无法判定，后者才是真漂移（发版没成功）。
    code, out, err = sh(["docker", "manifest", "inspect", image], timeout=90)
    if code == 0:
        r.update(status=WARN, note="registry 有该标签，但本地未拉取（无法核对 commit）")
        return r
    msg = (err or out or "").strip()
    last = msg.splitlines()[-1][:90] if msg else "未知错误"
    networkish = any(k in msg for k in ("Get \"https://", "timeout", "no such host",
                                        "TLS handshake", "connection reset",
                                        "proxyconnect", "i/o timeout"))
    if networkish:
        r["note"] = f"registry 查询被网络打断（本地也无该镜像）：{last}"
        return r
    r["note"] = f"registry 查不到 :{version}（{last}）"
    return r




def _ssh_build_info():
    """SSH 读服务器容器指纹。返回 dict 或 None（不可达/无凭据/缺 paramiko）。"""
    pwd = load_pass()
    if not pwd:
        return None
    try:
        import paramiko  # 延迟导入：只查前三层时完全不需要它
    except ImportError:
        return None
    # paramiko 默认把「banner 读不到」的异常直接打到 stderr，一行报错配一坨
    # traceback，看起来像脚本崩了。这里静音：连不上是**预期内的常态**
    # （本机 → 服务器的 /32 直连路由丢失时，22 端口会被 mihomo TUN 丢弃）。
    try:
        import logging
        logging.getLogger("paramiko").setLevel(logging.CRITICAL)
        paramiko.util.log_to_file(os.devnull)
    except Exception:  # noqa: BLE001
        pass
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        c.connect(PROD_HOST, username="root", password=pwd, timeout=15,
                  banner_timeout=15, auth_timeout=15)
        _, out, _ = c.exec_command(
            "docker exec edu-platform sh -c 'cat /app/BUILD_INFO' 2>/dev/null; "
            "docker inspect edu-platform --format 'IMAGE_TAG={{.Config.Image}}'; "
            "docker inspect edu-platform --format 'STARTED={{.State.StartedAt}}'",
            timeout=40)
        raw = out.read().decode("utf-8", "replace")
        return raw
    except Exception:  # noqa: BLE001 任何异常都视为"这一层拿不到"
        return None
    finally:
        try:
            c.close()
        except Exception:  # noqa: BLE001
            pass


def _http_health():
    url = f"http://{PROD_HOST}:{PROD_PORT}/api/v1/health"
    try:
        with urllib.request.urlopen(url, timeout=8) as resp:
            body = json.loads(resp.read().decode("utf-8", "replace"))
        return (body.get("data") or {})
    except Exception:  # noqa: BLE001
        return None


def layer_server(version):
    r = {"layer": f"服务器 :{PROD_PORT}", "version": "?", "commit": None,
         "status": NA, "note": "", "source": ""}
    raw = _ssh_build_info()
    if raw:
        info, image_tag, started = {}, "", ""
        for line in raw.splitlines():
            line = line.strip()
            if line.startswith("IMAGE_TAG="):
                image_tag = line.split("=", 1)[1]
            elif line.startswith("STARTED="):
                started = line.split("=", 1)[1]
            elif "=" in line:
                k, v = line.split("=", 1)
                info[k.strip()] = v.strip()
        if info.get("version"):
            r.update(version=info["version"], commit=info.get("commit") or None,
                     source="SSH")
            r["image"] = image_tag
            r["started"] = started
            if info["version"] != version:
                r.update(status=BAD,
                         note=f"服务器 {info['version']} ≠ 期望 {version}")
            elif info.get("commit") and info["commit"] != git("rev-parse", "HEAD")[0]:
                r.update(status=BAD, note="版本号相同但 commit 不同（未走发版流程）")
            else:
                r.update(status=OK, note="容器 BUILD_INFO 与本地一致")
            return r

    # 降级：只有 HTTP health 能证明"活着 + 版本号"
    data = _http_health()
    if not data:
        r["note"] = "SSH 与 HTTP 均不可达（检查 /32 路由或防火墙）"
        return r
    r["source"] = "HTTP(降级)"
    r["version"] = data.get("version", "?")
    if r["version"] != version:
        r.update(status=BAD,
                 note=f"服务器 {r['version']} ≠ 期望 {version}（仅 HTTP，无法核对 commit）")
    else:
        r.update(status=WARN, note="版本一致，但无法核对 commit（SSH 不可用）")
    return r


# ---------------------------------------------------------------- 结论
def behind_count(server_commit, local_head):
    """服务器 commit 落后本地多少个提交（commit 不在本地库时返回 None）。"""
    if not server_commit or not local_head:
        return None
    code, out, _ = sh(["git", "rev-list", "--count", f"{server_commit}..{local_head}"],
                      timeout=60)
    if code != 0:
        return None
    try:
        return int(out.strip())
    except ValueError:
        return None


def verdict(rows):
    """四层合议：任一 DRIFT → 1；全 OK → 0；有 DEGRADED/UNKNOWN 而无 DRIFT → 2。"""
    statuses = [r["status"] for r in rows]
    if BAD in statuses:
        return 1
    if all(s == OK for s in statuses):
        return 0
    return 2


def render(rows):
    head = ("层", "版本", "指纹", "判定", "说明")
    table = [head]
    for r in rows:
        mark = {OK: "[OK]", BAD: "[!!]", WARN: "[??]", NA: "[--]"}[r["status"]]
        table.append((r["layer"], r["version"], short(r["commit"]), mark, r["note"]))

    # 终端里 CJK 占两格：宽度与填充必须用同一套度量，否则列会歪
    def w(text):
        return sum(2 if ord(ch) > 0x2E80 else 1 for ch in str(text))

    widths = [max(w(row[i]) for row in table) for i in range(4)]
    for i, row in enumerate(table):
        cells = []
        for j in range(4):
            pad = " " * max(0, widths[j] + 2 - w(row[j]))
            cells.append(f"{row[j]}{pad}")
        print("".join(cells) + str(row[4]))
        if i == 0:
            print("-" * (sum(widths) + 8 + 24))


def main():
    ap = argparse.ArgumentParser(description="本地/仓库/镜像/服务器 四层一致性巡检")
    ap.add_argument("--no-fetch", action="store_true", help="不执行 git fetch")
    ap.add_argument("--skip-server", action="store_true", help="跳过服务器层")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    args = ap.parse_args()

    version = read_version()
    rows = [layer_local(version), layer_remote(fetch=not args.no_fetch),
            layer_image(version)]
    if not args.skip_server:
        rows.append(layer_server(version))

    code = verdict(rows)

    if args.json:
        print(json.dumps({"version": version, "code": code, "rows": rows},
                         ensure_ascii=False, indent=2))
    else:
        render(rows)
        srv = next((r for r in rows if r["layer"].startswith("服务器")), None)
        if srv and srv["status"] == BAD and srv.get("commit"):
            n = behind_count(srv["commit"], rows[0]["commit"])
            if n:
                print(f"\n服务器落后 {n} 个提交；对齐命令：")
                print("  python tools/deploy_release.py --yes        # 备份+拉取+重建+健康门禁")
        print()
        print({0: "四层一致", 1: "存在漂移（见上表 [!!] 行）",
               2: "无法完全判定（[??] 行需人工确认）"}[code])

    return code


if __name__ == "__main__":
    sys.exit(main())
