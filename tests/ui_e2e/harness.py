"""UI 端到端验证采集框架。

每条用例记录：模块 / 用例名 / 复现步骤 / 预期 / 实际 / 结论 / 截图 / 控制台与网络异常。
结果落到 tests/ui_e2e/result.json，截图落 tests/ui_e2e/shots/。

设计要点：
- 每个用例独立 try/except，单条崩溃不影响后续；
- 每条用例前后清空 console/network 缓冲，保证证据归属准确；
- 截图失败不阻断（仅告警）。
"""
from __future__ import annotations

import json
import os
import re
import time
import traceback
from datetime import datetime
from typing import Any, Dict, List, Optional

from playwright.sync_api import Page, sync_playwright

BASE = "http://localhost:5173"
API = "http://localhost:8000/api/v1"
ROOT = os.path.dirname(os.path.abspath(__file__))
SHOTS = os.path.join(ROOT, "shots")
RESULT = os.path.join(ROOT, "result.json")
os.makedirs(SHOTS, exist_ok=True)

# 忽略与业务无关的噪音
_NOISE = (
    "el-link] [API] The underline option",
    "[vite]",
    "Download the Vue Devtools",
)


class E2E:
    def __init__(self, tag: str = "run"):
        self.tag = tag
        self.rows: List[Dict[str, Any]] = []
        self.console: List[str] = []
        self.http: List[str] = []
        self.failed: List[str] = []
        self.calls: List[Dict[str, Any]] = []
        self.step_no = 0
        self.current: Optional[Dict[str, Any]] = None
        self._pw = None
        self._browser = None

    # ---------------------------------------------------------------- 生命周期
    def start(self, token: Optional[str] = None, user: Optional[dict] = None):
        self._pw = sync_playwright().start()
        # 本机 Chrome 遵循系统代理，localhost 必须绕过，否则连接被拒
        self._browser = self._pw.chromium.launch(
            headless=True, channel="chrome",
            args=["--no-proxy-server", "--disable-dev-shm-usage"],
        )
        ctx = self._browser.new_context(
            viewport={"width": 1600, "height": 1000},
            ignore_https_errors=True,
        )
        self.page = ctx.new_page()
        self.page.set_default_timeout(15000)
        self.page.on("console", self._on_console)
        self.page.on("pageerror", lambda e: self.console.append(f"[pageerror] {str(e)[:300]}"))
        self.page.on("requestfailed", self._on_reqfail)
        self.page.on("response", self._on_response)
        if token:
            self.page.goto(f"{BASE}/login", timeout=30000)
            self.page.evaluate(
                """([t, u]) => {
                    localStorage.setItem('access_token', t);
                    if (u) localStorage.setItem('user', JSON.stringify(u));
                }""",
                [token, user],
            )
        return self

    def stop(self):
        try:
            if self._browser:
                self._browser.close()
            if self._pw:
                self._pw.stop()
        except Exception:
            pass

    # ---------------------------------------------------------------- 事件采集
    def _on_console(self, msg):
        if msg.type not in ("error", "warning"):
            return
        text = msg.text or ""
        if any(n in text for n in _NOISE):
            return
        self.console.append(f"[console.{msg.type}] {text[:300]}")

    def _on_reqfail(self, req):
        u = req.url
        if "/api/" not in u and "localhost:5173" not in u:
            return
        self.failed.append(f"[netfail] {req.method} {u.split('5173')[-1][:120]} :: {req.failure}")

    def _on_response(self, resp):
        try:
            if "/api/" not in resp.url:
                return
            method = resp.request.method
            path = re.sub(r"^https?://[^/]+", "", resp.url)
            body = ""
            # 只对写操作与错误响应取 body：toast 文案是二次加工过的，
            # 真正确认「后端到底怎么说」必须看原始响应。
            if resp.status >= 400 or method in ("POST", "PUT", "DELETE", "PATCH"):
                try:
                    body = (resp.text() or "")[:400]
                except Exception:
                    body = ""
            self.calls.append({"method": method, "path": path, "status": resp.status, "body": body})
            if resp.status < 400:
                return
            self.http.append(f"[HTTP {resp.status}] {method} {path[:120]}")
        except Exception:
            pass

    def last_call(self, method: str = "", contains: str = "") -> Dict[str, Any]:
        """取最近一条匹配的接口调用记录（断言后端真实返回时用）。"""
        for c in reversed(self.calls):
            if method and c["method"] != method:
                continue
            if contains and contains not in c["path"]:
                continue
            return c
        return {}

    def call_msg(self, method: str = "", contains: str = "") -> str:
        """最近一条匹配调用的 message 字段（FastAPI 统一响应体）。"""
        c = self.last_call(method, contains)
        if not c:
            return ""
        try:
            d = json.loads(c["body"] or "{}")
            return str(d.get("message") or d.get("detail") or "")[:200]
        except Exception:
            return ""

    def reset_evidence(self):
        self.console.clear()
        self.http.clear()
        self.failed.clear()
        self.calls.clear()

    def evidence(self) -> str:
        items = list(dict.fromkeys(self.http + self.failed + self.console))
        return " ; ".join(items)[:1500]

    # ---------------------------------------------------------------- 用例记录
    def case(self, module: str, title: str, steps: List[str], expected: str):
        self.step_no += 1
        self.reset_evidence()
        self.current = {
            "no": self.step_no, "module": module, "title": title,
            "steps": steps, "expected": expected,
            "actual": "", "verdict": "PENDING", "evidence": "",
            "shot": "",
        }
        return self.current

    def shot(self, name: str = "") -> str:
        self.step_no_slug = re.sub(r"[^\w]+", "_", name or (self.current or {}).get("title", "x"))[:40]
        fn = f"{self.step_no:03d}_{self.step_no_slug}.png"
        path = os.path.join(SHOTS, fn)
        try:
            self.page.screenshot(path=path, full_page=True)
            if self.current is not None:
                self.current["shot"] = f"shots/{fn}"
        except Exception as exc:
            print(f"  [warn] 截图失败: {exc}")
        return path

    def ok(self, actual: str, shot: bool = True):
        c = self.current
        c["verdict"] = "PASS"
        c["actual"] = actual
        c["evidence"] = self.evidence()
        if shot:
            self.shot()
        self._commit()
        print(f"  PASS  {c['title']}  -> {actual[:90]}")

    def bug(self, severity: str, actual: str, impact: str = "", shot: bool = True):
        c = self.current
        c["verdict"] = severity
        c["actual"] = actual
        c["impact"] = impact
        c["evidence"] = self.evidence()
        if shot:
            self.shot()
        self._commit()
        print(f"  {severity}  {c['title']}  -> {actual[:110]}")

    def _commit(self):
        self.rows.append(self.current)
        self.current = None
        self.save()

    def save(self):
        with open(RESULT, "w", encoding="utf-8") as f:
            json.dump(self.rows, f, ensure_ascii=False, indent=1)

    # ---------------------------------------------------------------- 常用操作
    def goto(self, path: str, wait: int = 1800):
        self.page.goto(BASE + path, timeout=30000)
        self.page.wait_for_timeout(wait)
        return self.page.url

    def text(self) -> str:
        try:
            return self.page.inner_text("body")
        except Exception:
            return ""

    def toast_text(self) -> str:
        """读取当前可见的 Element Plus 消息/通知。"""
        parts = []
        for sel in (".el-message", ".el-notification", ".el-message-box"):
            for el in self.page.query_selector_all(sel):
                try:
                    if el.is_visible():
                        parts.append((el.inner_text() or "").strip())
                except Exception:
                    pass
        return " | ".join(p for p in parts if p)[:400]

    def click_text(self, text: str, nth: int = 0) -> bool:
        """按可见文本点击（优先按钮/链接/菜单项）。"""
        locs = [
            self.page.get_by_role("button", name=text, exact=False),
            self.page.get_by_text(text, exact=False),
        ]
        for loc in locs:
            try:
                if loc.count() > nth:
                    loc.nth(nth).click(timeout=8000)
                    self.page.wait_for_timeout(700)
                    return True
            except Exception:
                continue
        return False

    def fill_placeholder(self, placeholder: str, value: str) -> bool:
        try:
            el = self.page.get_by_placeholder(placeholder).first
            el.fill(value, timeout=6000)
            return True
        except Exception:
            return False

    def select_first(self, placeholder: str) -> Optional[str]:
        """打开 el-select 并选第一项，返回选中文本。"""
        try:
            box = self.page.locator(".el-select").filter(has_text=placeholder).first
            box.click(timeout=6000)
            self.page.wait_for_timeout(600)
            opts = self.page.locator(".el-select-dropdown__item:visible")
            if opts.count() == 0:
                self.page.keyboard.press("Escape")
                return None
            label = (opts.first.inner_text() or "").strip()
            opts.first.click()
            self.page.wait_for_timeout(500)
            return label
        except Exception:
            return None

    # ------------------------------------------------- label 驱动的表单操作
    # 弹窗/表单里的输入框普遍没有 placeholder，只能靠 el-form-item 的 label 定位。
    def form_item(self, label: str, scope: str = ""):
        return self.page.locator(f"{scope} .el-form-item".strip(), has_text=label).first

    def fill_by_label(self, label: str, value: str, scope: str = "") -> bool:
        try:
            self.form_item(label, scope).locator("input, textarea").first.fill(value, timeout=6000)
            return True
        except Exception:
            return False

    def select_by_label(self, label: str, option_text: Optional[str] = None,
                        scope: str = "") -> Optional[str]:
        """按 label 打开 el-select；option_text 为空则选第一项。返回选中文本。"""
        try:
            self.form_item(label, scope).locator(".el-select").first.click(timeout=6000)
            self.page.wait_for_timeout(600)
            opts = self.page.locator(".el-select-dropdown__item:visible")
            if opts.count() == 0:
                self.page.keyboard.press("Escape")
                return None
            target = opts.filter(has_text=option_text).first if option_text else opts.first
            label_txt = (target.inner_text() or "").strip()
            target.click()
            self.page.wait_for_timeout(450)
            return label_txt
        except Exception:
            return None

    def select_value(self, label: str, scope: str = "") -> str:
        """读取 el-select 当前回显文本（注意：input.value 恒为空，必须看 placeholder 节点）。"""
        try:
            item = self.form_item(label, scope)
            el = item.locator(".el-select__placeholder, .el-select__selected-item").first
            return (el.inner_text() or "").strip()
        except Exception:
            return ""

    def input_value(self, label: str, scope: str = "") -> str:
        try:
            return (self.form_item(label, scope).locator("input").first
                    .input_value(timeout=4000) or "")
        except Exception:
            return ""

    def form_errors(self) -> List[str]:
        return [(x.inner_text() or "").strip()
                for x in self.page.query_selector_all(".el-form-item__error")]

    def dialog_visible(self) -> bool:
        try:
            return self.page.locator(".el-dialog").first.is_visible()
        except Exception:
            return False

    def confirm(self, labels=("确定", "确认", "提交", "保存")) -> bool:
        """点击最上层的确认按钮。"""
        for lab in labels:
            b = self.page.get_by_role("button", name=lab)
            try:
                if b.count() and b.last.is_visible():
                    b.last.click()
                    self.page.wait_for_timeout(1200)
                    return True
            except Exception:
                continue
        return False

    def dump(self) -> Dict[str, Any]:
        """侦察辅助：一次性导出页面可交互元素概览。"""
        js = """() => {
          const txt = e => (e.innerText || '').trim();
          return {
            url: location.pathname,
            buttons: [...document.querySelectorAll('button')].map(txt).filter(Boolean).slice(0, 30),
            placeholders: [...document.querySelectorAll('input,textarea')]
                .map(i => i.getAttribute('placeholder')).filter(Boolean),
            labels: [...document.querySelectorAll('.el-form-item__label')].map(txt).filter(Boolean),
            selects: [...document.querySelectorAll('.el-select')].map(s => txt(s).slice(0,24)),
            tabs: [...document.querySelectorAll('.el-tabs__item')].map(txt).filter(Boolean),
            headers: [...document.querySelectorAll('.el-table__header th')].map(txt).filter(Boolean).slice(0,20),
            rows: document.querySelectorAll('.el-table__body-wrapper tbody tr').length,
            empty: (document.querySelector('.el-table__empty-text')||{}).innerText || '',
            body: (document.body.innerText || '').slice(0, 400),
          };
        }"""
        try:
            return self.page.evaluate(js)
        except Exception as exc:
            return {"error": str(exc)}

    def search(self, placeholder: str, keyword: str):
        """在列表页搜索框输入并回车。"""
        if self.fill_placeholder(placeholder, keyword):
            self.page.keyboard.press("Enter")
            self.page.wait_for_timeout(1500)
            return True
        return False

    def row_count(self) -> int:
        return len(self.page.query_selector_all(".el-table__body-wrapper tbody tr"))

    def empty_hint(self) -> str:
        for el in self.page.query_selector_all(".el-table__empty-text, .el-empty__description"):
            try:
                t = (el.inner_text() or "").strip()
                if t:
                    return t
            except Exception:
                pass
        return ""

    def run(self, module, title, steps, expected, fn, shot=True):
        """执行一条用例：fn() 返回 (verdict, actual, impact)。

        verdict: 'PASS' 或 'P0'/'P1'/'P2'/'P3'
        """
        self.case(module, title, steps, expected)
        try:
            verdict, actual, impact = fn()
        except Exception as exc:
            verdict, actual, impact = "BLOCKED", f"用例执行异常：{type(exc).__name__}: {exc}"[:300], ""
        if verdict == "PASS":
            self.ok(actual, shot)
        else:
            self.bug(verdict, actual, impact, shot)
        return verdict


def api_login(username: str, password: str) -> Optional[str]:
    import urllib.request
    body = json.dumps({"username": username, "password": password}).encode()
    req = urllib.request.Request(f"{API}/auth/login", data=body,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            d = json.loads(r.read().decode())
        return (d.get("data") or {}).get("access_token")
    except Exception as exc:
        print(f"  [api_login 失败] {username}: {exc}")
        return None


def api(method: str, path: str, token: str, body: Any = None) -> Dict[str, Any]:
    import urllib.error
    import urllib.parse
    import urllib.request
    data = json.dumps(body).encode() if body is not None else None
    # 查询串里可能带中文（如 ?keyword=UI年级171305）。urllib 只接受 ASCII 路径，
    # 不编码会抛 UnicodeEncodeError，被下面的 except 吞成 {"code": -1}，
    # 于是「接口回查为空」被误判成业务缺陷（实测因此误报「新增年级未落库」）。
    safe_path = urllib.parse.quote(path, safe="/?&=:#%")
    req = urllib.request.Request(API + safe_path, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    req.add_header("Authorization", "Bearer " + token)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        try:
            return json.loads(e.read().decode() or "{}")
        except Exception:
            return {"code": e.code}
    except Exception as exc:
        return {"code": -1, "message": str(exc)}
