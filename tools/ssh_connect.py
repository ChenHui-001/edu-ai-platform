#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""SSH 连接助手：优先公钥，回退口令。

生产服务器已关闭密码登录（PasswordAuthentication no），只接受公钥。
历史脚本只读 `DEPLOY_PASS`，在凭据清理后必然连不上；这里统一成：

1. `DEPLOY_KEY` 指定的私钥；
2. `~/.ssh/id_ed25519`；
3. `~/.ssh/id_rsa`；
4. `DEPLOY_PASS` 或仓库外 `deploy_scripts/.deploy_pass`。

只返回连接，不打印任何凭据内容。paramiko 不支持 Windows ssh-agent，
因此必须显式使用私钥文件；口令仅作为旧环境的回退。
"""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PASS_FILE = os.path.join(os.path.dirname(ROOT), "deploy_scripts", ".deploy_pass")


def load_pass() -> str:
    pwd = os.environ.get("DEPLOY_PASS", "").strip()
    if pwd:
        return pwd
    try:
        with open(PASS_FILE, encoding="utf-8") as fh:
            return fh.read().strip()
    except OSError:
        return ""


def _key_candidates():
    explicit = os.environ.get("DEPLOY_KEY", "").strip()
    if explicit:
        yield explicit
    home = os.path.expanduser("~")
    for name in ("id_ed25519", "id_rsa"):
        yield os.path.join(home, ".ssh", name)


def connect(host: str, username: str = "root", timeout: int = 20):
    """返回已连接的 paramiko SSHClient；失败抛最后一个异常。"""
    import logging

    import paramiko

    logging.getLogger("paramiko").setLevel(logging.CRITICAL)
    paramiko.util.log_to_file(os.devnull)

    last_exc = None
    for path in _key_candidates():
        if not os.path.isfile(path):
            continue
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            client.connect(
                host,
                username=username,
                key_filename=path,
                timeout=timeout,
                banner_timeout=timeout,
                auth_timeout=timeout,
                allow_agent=False,
                look_for_keys=False,
            )
            return client
        except Exception as exc:  # noqa: BLE001 下一把钥匙/口令继续尝试
            last_exc = exc
            client.close()

    pwd = load_pass()
    if pwd:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            client.connect(
                host,
                username=username,
                password=pwd,
                timeout=timeout,
                banner_timeout=timeout,
                auth_timeout=timeout,
            )
            return client
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            client.close()

    if last_exc is not None:
        raise last_exc
    raise RuntimeError("找不到可用的 SSH 凭据：设置 DEPLOY_KEY 或提供 ~/.ssh/id_ed25519")
