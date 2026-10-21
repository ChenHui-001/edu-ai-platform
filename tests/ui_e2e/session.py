"""会话获取与注入。

UI 登录受图形验证码制约（一次性 + 180s），不可能每个模块都做一次真实验证码登录。
策略：
  - 登录模块本身用**真实验证码**走完整 UI 登录（阶段二已验证）；
  - 其余模块通过 API 取真实登录响应，把 access_token / refresh_token / user
    （含 permissions:roles/perms/menus）写入 localStorage 再 goto，
    等价于「用户已登录」状态，页面渲染与权限判断完全走真实链路。
"""
from __future__ import annotations

import json
import os
import urllib.request

from harness import API

HERE = os.path.dirname(os.path.abspath(__file__))

ACCOUNTS = {
    "admin": ("admin", "Admin@123456"),
    "teacher": ("teacher1", "Teacher@123"),
    "student": ("stu731", "Student@123"),
    # teacher1 任教一年级(1)班，stu101 属于该班 —— 教师下发/学生作答闭环用这个账号
    "student1": ("stu101", "Student@123"),
}


def login_payload(username: str, password: str) -> dict:
    """调登录接口，返回 {token, refresh, user}；user 内嵌 permissions。"""
    body = json.dumps({"username": username, "password": password}).encode()
    req = urllib.request.Request(API + "/auth/login", data=body,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=20) as r:
        d = json.loads(r.read().decode())
    if d.get("code") != 200:
        raise RuntimeError(f"登录失败 {username}: {d.get('message')}")
    data = d["data"]
    user = {**data["user"], "permissions": data.get("permission") or {}}
    return {"token": data["access_token"], "refresh": data.get("refresh_token"), "user": user}


def session(role: str) -> dict:
    """取会话（带本地缓存，1 小时内复用）。"""
    cache = os.path.join(HERE, f"session_{role}.json")
    if os.path.exists(cache):
        try:
            d = json.load(open(cache, encoding="utf-8"))
            if d.get("token"):
                return d
        except Exception:
            pass
    username, password = ACCOUNTS[role]
    d = login_payload(username, password)
    with open(cache, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False)
    return d


def inject(e, role: str, path: str = "/dashboard", wait: int = 2200):
    """把会话写入 localStorage 后打开目标页。"""
    s = session(role)
    e.page.goto("http://localhost:5173/login", timeout=30000)
    e.page.evaluate(
        """([t, r, u]) => {
            localStorage.setItem('access_token', t);
            if (r) localStorage.setItem('refresh_token', r);
            localStorage.setItem('user', JSON.stringify(u));
        }""",
        [s["token"], s.get("refresh"), s["user"]],
    )
    return e.goto(path, wait)
