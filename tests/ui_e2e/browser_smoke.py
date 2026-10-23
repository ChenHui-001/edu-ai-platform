# -*- coding: utf-8 -*-
"""真实浏览器逐页冒烟（Playwright + 本机 Chrome/Edge，无需额外下载浏览器）。

做法：
  1. 通过后端 /auth/login API 拿到 token 与权限快照（UI 登录有图形验证码，
     这里不测验证码本身），注入 localStorage 后直接访问受保护路由；
  2. 三种角色分别遍历其菜单/路由页，检查：
       - 未被路由守卫踢回 /login 或 /403；
       - #app 渲染出的文本长度合理（防止白屏）；
       - 无 pageerror、无 console error（忽略 favicon/ResizeObserver 噪声）。
  3. 失败时输出 URL/错误并截图到 tests/ui_e2e/shots/（已 gitignore）。

用法：
  python tests/ui_e2e/browser_smoke.py --base http://127.0.0.1:18081
  python tests/ui_e2e/browser_smoke.py --base http://127.0.0.1:18081 --channel msedge
"""
import argparse
import json
import os
import sys
import time

import httpx
from playwright.sync_api import sync_playwright

ROUTES = {
    "admin": [
        "/dashboard", "/admin/users", "/admin/roles", "/admin/registrations",
        "/admin/grades", "/admin/subjects", "/admin/knowledge", "/admin/classes",
        "/admin/logs", "/admin/jobs", "/admin/attachments", "/admin/reports",
        "/admin/settings", "/admin/ai-config", "/admin/agent-logs",
        "/agent/chat", "/agent/generate", "/profile",
    ],
    "teacher": [
        "/dashboard", "/teacher/questions", "/teacher/papers", "/teacher/tasks",
        "/teacher/grading", "/teacher/lessons", "/teacher/analysis",
        "/teacher/students", "/teacher/reports", "/agent/chat",
        "/agent/generate", "/profile",
    ],
    "student": [
        "/dashboard", "/student/practice", "/student/exams", "/student/wrong",
        "/student/notes", "/student/review", "/student/report", "/student/scores",
        "/student/favorites", "/student/mastery", "/student/custom",
        "/student/goals", "/student/path", "/student/flashcard",
        "/agent/chat", "/profile",
    ],
}
ACCOUNTS = {
    "admin": ("admin", "Admin@123456"),
    "teacher": ("teacher1", "Teacher@123"),
    "student": ("stu731", "Student@123"),
}
IGNORE_CONSOLE = ("favicon", "ResizeObserver loop", "Failed to load resource")


def login_api(base: str, username: str, password: str) -> dict:
    resp = httpx.post(f"{base}/api/v1/auth/login",
                      json={"username": username, "password": password}, timeout=20)
    resp.raise_for_status()
    payload = resp.json()
    if payload.get("code") != 200:
        raise RuntimeError(f"登录失败: {payload}")
    return payload["data"]


def run_role(page, base: str, role: str, route_list, shots_dir: str) -> list:
    username, password = ACCOUNTS[role]
    data = login_api(base, username, password)
    user = dict(data["user"])
    user["permissions"] = data["permission"]
    page.goto(base + "/login", wait_until="domcontentloaded", timeout=30000)
    page.evaluate(
        """([access, refresh, user]) => {
            localStorage.setItem('access_token', access);
            localStorage.setItem('refresh_token', refresh);
            localStorage.setItem('user', JSON.stringify(user));
        }""",
        [data["access_token"], data["refresh_token"], user],
    )

    failures = []
    for path in route_list:
        page_errors = []
        console_errors = []

        def on_pageerror(exc, errors=page_errors):
            errors.append(str(exc))

        def on_console(msg, errors=console_errors):
            if msg.type != "error":
                return
            text = msg.text or ""
            if any(k in text for k in IGNORE_CONSOLE):
                return
            errors.append(text)

        page.on("pageerror", on_pageerror)
        page.on("console", on_console)
        try:
            page.goto(base + path, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(1200)
            current = page.url.replace(base, "")
            body_text = page.locator("#app").inner_text(timeout=5000).strip()
            if current.startswith("/login") or current.startswith("/403"):
                failures.append((path, f"被重定向到 {current}"))
            elif len(body_text) < 40:
                failures.append((path, f"页面文本过短({len(body_text)})，疑似白屏"))
            elif page_errors:
                failures.append((path, "pageerror: " + " | ".join(page_errors[:2])))
            elif console_errors:
                failures.append((path, "console error: " + " | ".join(console_errors[:2])))
        except Exception as exc:  # noqa: BLE001
            failures.append((path, f"异常: {exc}"))
            try:
                os.makedirs(shots_dir, exist_ok=True)
                page.screenshot(path=os.path.join(
                    shots_dir, f"smoke_{role}_{path.strip('/').replace('/', '_') or 'root'}.png"),
                    full_page=False)
            except Exception:  # noqa: BLE001
                pass
        finally:
            page.remove_listener("pageerror", on_pageerror)
            page.remove_listener("console", on_console)
    return failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default=os.environ.get("SMOKE_BASE", "http://127.0.0.1:18081"))
    parser.add_argument("--channel", default="chrome",
                        help="Playwright channel：chrome / msedge（本机浏览器）")
    parser.add_argument("--roles", default="admin,teacher,student")
    parser.add_argument("--shots", default=os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "shots"))
    args = parser.parse_args()
    base = args.base.rstrip("/")
    roles = [r.strip() for r in args.roles.split(",") if r.strip()]

    print(f"[smoke] base={base} channel={args.channel} roles={roles}")
    all_failures = {}
    started = time.time()
    with sync_playwright() as pw:
        try:
            browser = pw.chromium.launch(channel=args.channel, headless=True)
        except Exception as exc:  # noqa: BLE001
            print(f"[smoke] {args.channel} 启动失败，尝试 msedge: {exc}")
            browser = pw.chromium.launch(channel="msedge", headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()
        for role in roles:
            routes = ROUTES[role]
            print(f"[smoke] {role}: {len(routes)} 页 ...")
            failures = run_role(page, base, role, routes, args.shots)
            all_failures[role] = failures
            print(f"[smoke] {role}: {'PASS' if not failures else str(len(failures)) + ' FAIL'}")
            for path, reason in failures:
                print(f"    - {path}: {reason}")
        browser.close()

    total = sum(len(v) for v in all_failures.values())
    elapsed = time.time() - started
    print(f"[smoke] done in {elapsed:.1f}s, failures={total}")
    if total:
        return 1
    print("[smoke] ALL PAGES PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
