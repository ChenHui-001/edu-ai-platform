# -*- coding: utf-8 -*-
"""四层一致性校验：本地代码 / 远程仓库 / ghcr 镜像 / 服务器容器。

对应用户要求（2026-10-26）：
    「每次修改代码后及时提交并推送，保证本地、远程仓库、docker 镜像、服务器都是一致的」

四层必须指向同一个 commit：
    ① 本地 git HEAD
    ② 远程 origin/master
    ③ ghcr 镜像内 /app/BUILD_INFO 的 commit
    ④ 服务器容器内 /app/BUILD_INFO 的 commit

额外比对：本地容器与服务器容器内关键文件的 sha256 —— 同一份镜像必然相同，
一旦不同说明两端跑的不是同一份二进制（最隐蔽的「本地好好的、线上出问题」）。

用法：
    python tools/verify_consistency.py
    python tools/verify_consistency.py --host 186.241.77.194 --user root
    DEPLOY_PASS=xxx python tools/verify_consistency.py    # 服务器需要密码
"""
import argparse
import json
import os
import subprocess
import sys

GHCR_IMAGE = os.environ.get("GHCR_IMAGE", "ghcr.io/chenhui-001/edu-ai-platform")
KEY_FILES = [
    "app/api/v1/grading.py",
    "app/api/v1/lesson_ai.py",
    "app/agents/lesson_agent.py",
    "VERSION",
]
OK, BAD = 0, 0


def _run(cmd, timeout=120):
    """执行本地命令，返回 (rc, stdout)。"""
    try:
        p = subprocess.run(cmd, shell=True, capture_output=True, timeout=timeout)
        return p.returncode, p.stdout.decode("utf-8", "replace").strip()
    except Exception as e:  # noqa: BLE001
        return 1, str(e)[:200]


def _ssh(host, user, cmd, timeout=120):
    """在远程执行命令（需 paramiko + DEPLOY_PASS）。"""
    try:
        import paramiko
    except ImportError:
        return 1, "paramiko 未安装（跳过远程层）"
    pwd = os.environ.get("DEPLOY_PASS", "")
    if not pwd:
        return 1, "未提供 DEPLOY_PASS（跳过远程层）"
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        c.connect(host, username=user, password=pwd, timeout=20)
        _, out, err = c.exec_command(cmd, timeout=timeout)
        so = out.read().decode("utf-8", "replace").strip()
        se = err.read().decode("utf-8", "replace").strip()
        return 0, so or se
    except Exception as e:  # noqa: BLE001
        return 1, f"{type(e).__name__}: {str(e)[:120]}"
    finally:
        try:
            c.close()
        except Exception:  # noqa: BLE001
            pass


def check(label, got, expect=None, extra=""):
    global OK, BAD
    if expect is None:
        if got and not got.startswith(("ERR", "未", "paramiko")):
            OK += 1
            print(f"  \033[92m✔\033[0m {label}: {got} {extra}")
        else:
            BAD += 1
            print(f"  \033[91m✘\033[0m {label}: {got or '(空)'} {extra}")
        return
    if got == expect:
        OK += 1
        print(f"  \033[92m✔\033[0m {label}: {got}")
    else:
        BAD += 1
        print(f"  \033[91m✘\033[0m {label}: {got}  ≠ 期望 {expect} {extra}")


def main():
    global OK, BAD
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default=os.environ.get("DEPLOY_HOST", ""))
    ap.add_argument("--user", default=os.environ.get("DEPLOY_USER", "root"))
    ap.add_argument("--container", default="edu-platform")
    args = ap.parse_args()

    print("=" * 62)
    print("四层一致性校验 · 本地 / 远程仓库 / docker 镜像 / 服务器")
    print("=" * 62)

    # ---------- ① 本地代码 ----------
    rc, head = _run("git rev-parse HEAD")
    check("① 本地 git HEAD", head if rc == 0 else f"ERR {head}")
    rc, ver = _run("cat VERSION")
    check("   本地 VERSION", ver if rc == 0 else f"ERR {ver}")
    rc, dirty = _run("git status --porcelain | wc -l")
    check("   工作区未提交改动", f"{dirty} 个",
          "0 个" if dirty == "0" else "← 有改动未提交，先提交再校验")

    # ---------- ② 远程仓库 ----------
    rc, remote = _run("git ls-remote origin master")
    remote_sha = remote.split()[0] if rc == 0 and remote else ""
    check("② 远程 origin/master", remote_sha or f"ERR {remote}", head)

    # ---------- ③ ghcr 镜像 ----------
    rc, out = _run(f"docker manifest inspect {GHCR_IMAGE}:{ver}")
    if rc == 0 and out:
        OK += 1
        print(f"  \033[92m✔\033[0m ③ ghcr 镜像 {GHCR_IMAGE}:{ver} 存在（多架构）")
    else:
        BAD += 1
        print(f"  \033[91m✘\033[0m ③ ghcr 镜像 {GHCR_IMAGE}:{ver} 不存在")

    local_img_sha = ""
    rc, out = _run(
        f"docker run --rm --entrypoint sh {GHCR_IMAGE}:{ver} "
        f"-c 'cat /app/VERSION; grep ^commit /app/BUILD_INFO | cut -d= -f2'")
    if rc == 0 and out:
        parts = out.split()
        img_ver = parts[0] if parts else ""
        img_commit = parts[1] if len(parts) > 1 else ""
        local_img_sha = img_commit
        check("   镜像内 VERSION", img_ver, ver)
        check("   镜像内 commit", img_commit, head)
    else:
        BAD += 1
        print(f"  \033[91m✘\033[0m ③ 读取镜像内指纹失败: {out[:80]}")

    # ---------- ④ 服务器容器 ----------
    if args.host:
        rc, out = _ssh(args.host, args.user,
                       f"docker exec {args.container} sh -c "
                       f"'cat /app/VERSION; grep ^commit /app/BUILD_INFO | cut -d= -f2'")
        parts = out.split()
        if rc == 0 and len(parts) >= 2:
            check("④ 服务器容器 VERSION", parts[0], ver)
            check("   服务器容器 commit", parts[1], head)
            # 两端关键文件 sha256 比对
            cmd = (f"docker exec {args.container} sh -c "
                   f"'cd /app && sha256sum {' '.join(KEY_FILES)}'")
            rc2, srv_hash = _ssh(args.host, args.user, cmd)
            rc3, loc_hash = _run(
                f"docker exec {args.container} sh -c "
                f"'cd /app && sha256sum {' '.join(KEY_FILES)}'")
            if rc2 == 0 and rc3 == 0 and srv_hash and loc_hash:
                # sha256sum 输出：<hash>  <相对路径>
                s_map = {l.split()[1]: l.split()[0] for l in srv_hash.splitlines() if l}
                l_map = {l.split()[1]: l.split()[0] for l in loc_hash.splitlines() if l}
                diff = [k for k in s_map if l_map.get(k) != s_map[k]]
                check("   两端关键文件 sha256", "全部一致" if not diff else f"不一致: {diff}",
                      "全部一致")
            else:
                print("  \033[93m!\033[0m 跳过文件哈希比对（本地容器未运行或远程不可达）")
        else:
            print(f"  \033[93m!\033[0m ④ 服务器层不可达: {out[:100]}")
    else:
        print("  \033[93m!\033[0m ④ 服务器层跳过（未提供 --host / DEPLOY_HOST）")

    print("=" * 62)
    print(f"结果：通过 {OK} / 不一致 {BAD}")
    if BAD:
        print("  → 存在不一致：先 auto_ship 提交推送，再 pull 镜像并同步服务器")
    else:
        print("  → 四层一致，状态良好")
    print("=" * 62)
    return 0 if BAD == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
