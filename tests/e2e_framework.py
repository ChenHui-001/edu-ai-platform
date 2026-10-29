"""
端到端自动化测试框架 —— 新芽学堂 · 九年义务教育 AI 学习平台

设计要点：
1. 绕过本机代理（127.0.0.1:10064 会劫持 localhost 请求），用 ProxyHandler({}) 禁用
2. 统一断言封装，失败不中断整体流程，最后汇总报告
3. 每个测试用例独立记录（名称/状态/耗时/错误信息）
"""
import json
import os
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from datetime import datetime

BASE_HOST = os.environ.get("E2E_BASE", "http://localhost")


def _detect_base():
    """自动探测实际服务端口：读 .env 的 HOST_PORT，再回退到逐个探测。

    启动脚本在 8080 被占用时会自动顺延并写回 .env，硬编码端口会导致
    整批用例全部连接失败，必须在运行时探测。
    """
    raw = BASE_HOST.strip().rstrip("/")
    if raw.startswith("http://"):
        raw = raw[len("http://"):]
    if raw.startswith("https://"):
        raw = raw[len("https://"):]
    scheme = "https" if BASE_HOST.strip().startswith("https://") else "http"
    host, port = "localhost", None
    if ":" in raw:
        maybe_host, maybe_port = raw.rsplit(":", 1)
        if maybe_port.isdigit():
            host, port = maybe_host, int(maybe_port)
        else:
            host = raw
    # 1) 显式端口直接用
    if port:
        return f"{scheme}://{host}:{port}/api/v1"
    # 2) 读项目 .env 的 HOST_PORT
    env_file = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
    ports = []
    if os.path.exists(env_file):
        for line in open(env_file, encoding="utf-8", errors="ignore"):
            line = line.strip()
            if line.upper().startswith("HOST_PORT="):
                v = line.split("=", 1)[1].strip().strip('"').strip("'")
                if v.isdigit():
                    ports.append(int(v))
    # 3) 默认候选
    ports += [8080, 8081, 8082, 8083, 8000]
    seen = set()
    for p in ports:
        if p in seen:
            continue
        seen.add(p)
        try:
            req = urllib.request.Request(f"http://{host}:{p}/api/v1/health", method="GET")
            opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
            with opener.open(req, timeout=3) as r:
                if json.loads(r.read().decode("utf-8")).get("data", {}).get("status") == "healthy":
                    return f"http://{host}:{p}/api/v1"
        except Exception:
            continue
    return f"http://{host}:8080/api/v1"


BASE = _detect_base()


class ServiceDown(Exception):
    """服务不可达——属于测试环境故障，不能算作功能通过或失败。"""


def _filename(disposition):
    """从 Content-Disposition 解析文件名，解析失败返回空串。"""
    if not disposition:
        return ""
    for part in disposition.split(";"):
        part = part.strip()
        if part.lower().startswith("filename="):
            return part.split("=", 1)[1].strip().strip('"').strip("'")
    return ""


# ================================================================
#  测试结果收集
# ================================================================
class Result:
    def __init__(self):
        self.cases = []          # [(阶段, 名称, 状态, 耗时ms, 详情)]
        self.issues = []         # 发现的问题
        self.phase = "初始化"
        self.context = {}        # 跨用例共享的数据（用户ID、试卷ID 等）

    def add(self, name, ok, detail="", elapsed=0):
        status = "PASS" if ok else "FAIL"
        self.cases.append((self.phase, name, status, elapsed, detail))
        icon = "\033[92m[PASS]\033[0m" if ok else "\033[91m[FAIL]\033[0m"
        print(f"  {icon} {name}" + (f"  -> {detail}" if detail else ""))
        return ok

    def env(self, name, detail=""):
        """环境故障：单列标记，既不算 PASS 也不算业务 FAIL。"""
        self.cases.append((self.phase, name, "ENV", 0, detail))
        print(f"  \033[93m[ENV ] {name}\033[0m  -> {detail}")
        return False

    def issue(self, severity, title, detail, repro=None):
        self.issues.append({
            "severity": severity, "title": title, "detail": detail, "repro": repro
        })
        print(f"  \033[95m[ISSUE:{severity}]\033[0m {title}")

    def set_phase(self, phase):
        self.phase = phase
        print(f"\n\033[96m{'=' * 66}\033[0m")
        print(f"\033[1;96m  {phase}\033[0m")
        print(f"\033[96m{'=' * 66}\033[0m")

    @property
    def passed(self):
        return sum(1 for c in self.cases if c[2] == "PASS")

    @property
    def failed(self):
        return sum(1 for c in self.cases if c[2] == "FAIL")

    @property
    def env_failed(self):
        return sum(1 for c in self.cases if c[2] == "ENV")


R = Result()


# ================================================================
#  HTTP 客户端
# ================================================================
class Client:
    """单用户会话客户端，自动携带 Bearer Token。"""

    def __init__(self, label):
        self.label = label
        self.token = None
        self.refresh_token = None
        self.user = None
        self.permission = None
        self.unreachable = False
        # 关键：清空代理，否则 localhost 请求会被 127.0.0.1:10064 劫持
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        self.opener = urllib.request.build_opener(
            urllib.request.ProxyHandler({}),
            urllib.request.HTTPSHandler(context=ctx),
        )

    def request(self, method, path, body=None, params=None, raw_body=None,
                headers=None, timeout=30):
        url = BASE + path
        if params:
            url += "?" + urllib.parse.urlencode(
                {k: v for k, v in params.items() if v is not None and v != ""}
            )
        data = None
        hdrs = {"Accept": "application/json"}
        if raw_body is not None:
            data = raw_body
        elif body is not None:
            data = json.dumps(body, ensure_ascii=False).encode("utf-8")
            hdrs["Content-Type"] = "application/json; charset=utf-8"
        if self.token:
            hdrs["Authorization"] = f"Bearer {self.token}"
        if headers:
            hdrs.update(headers)

        req = urllib.request.Request(url, data=data, headers=hdrs, method=method)
        t0 = time.time()
        try:
            resp = self.opener.open(req, timeout=timeout)
            elapsed = int((time.time() - t0) * 1000)
            raw = resp.read()
            ctype = resp.headers.get("Content-Type", "")
            # 文件下载类接口（Excel 导出、附件）返回二进制，不能按 JSON 解析
            if "application/json" not in ctype:
                return ({"code": resp.status, "success": True,
                         "data": {"bytes": len(raw), "content_type": ctype,
                                  "filename": _filename(resp.headers.get("Content-Disposition"))}},
                        elapsed, resp.status)
            payload = json.loads(raw.decode("utf-8"))
            return payload, elapsed, resp.status
        except urllib.error.HTTPError as e:
            elapsed = int((time.time() - t0) * 1000)
            try:
                payload = json.loads(e.read().decode("utf-8"))
            except Exception:
                payload = {"code": e.code, "message": str(e), "success": False}
            return payload, elapsed, e.code
        except (urllib.error.URLError, ConnectionError, OSError) as e:
            elapsed = int((time.time() - t0) * 1000)
            # 服务不可达属于环境故障，必须显式标记，不能混入业务判定
            return {"code": -1, "message": f"[不可达] {e}", "success": False,
                    "_unreachable": True}, elapsed, -1

    def reachable(self):
        """探活，避免把环境故障当成业务通过。"""
        p, _, _ = self.request("GET", "/health")
        return p.get("data", {}).get("status") == "healthy"

    def get(self, path, **kw):
        return self.request("GET", path, **kw)

    def post(self, path, body=None, **kw):
        return self.request("POST", path, body=body, **kw)

    def put(self, path, body=None, **kw):
        return self.request("PUT", path, body=body, **kw)

    def delete(self, path, **kw):
        return self.request("DELETE", path, **kw)

    def upload(self, path, filename, content, fields=None, timeout=60):
        """multipart/form-data 上传。

        手写 multipart 边界而不引入 requests：本项目测试只依赖标准库，
        且 self.request 已支持 raw_body + 自定义 headers，够用。
        用于覆盖「导入接口的大小上限/格式白名单」这类只能靠真实上传
        才能验证的行为（此前导入只有模板下载用例，从未真正上传过文件）。
        """
        boundary = "----e2eBoundary" + uuid.uuid4().hex
        chunks = []
        for k, v in (fields or {}).items():
            if v is None:
                continue
            chunks.append(
                f"--{boundary}\r\nContent-Disposition: form-data; "
                f"name=\"{k}\"\r\n\r\n{v}\r\n".encode("utf-8")
            )
        chunks.append(
            f"--{boundary}\r\nContent-Disposition: form-data; "
            f"name=\"file\"; filename=\"{filename}\"\r\n"
            f"Content-Type: application/octet-stream\r\n\r\n".encode("utf-8")
        )
        chunks.append(content if isinstance(content, bytes) else content.encode())
        chunks.append(f"\r\n--{boundary}--\r\n".encode("utf-8"))
        return self.request(
            "POST", path, raw_body=b"".join(chunks), timeout=timeout,
            headers={"Content-Type":
                     f"multipart/form-data; boundary={boundary}"},
        )

    def login(self, username, password):
        payload, ms, _ = self.post("/auth/login",
                                   {"username": username, "password": password})
        if payload.get("_unreachable"):
            self.unreachable = True
            return False, f"[服务不可达] {payload.get('message')}"
        if payload.get("success") and "access_token" in payload.get("data", {}):
            d = payload["data"]
            self.token = d["access_token"]
            self.refresh_token = d.get("refresh_token")
            self.user = d.get("user")
            self.permission = d.get("permission")
            # 出厂/被重置的账号带 must_change_password=True，deps.get_current_user
            # 会拦下除白名单外的一切请求（生产安全默认，见 services/init_db.py）。
            # 这里真实走一遍「强制改密」闭环再继续，而不是在种子阶段绕过它。
            #
            # 2026-10 变更：`change_password` 现在**拒绝 new == old**（这是修 S5
            # 可绕过漏洞的核心，见 auth_service.change_password 的 docstring），
            # 所以不能再拿同一个口令"改"一次。但也不能改成真新密码：
            # 各阶段有 99 处 `.login()` 共用硬编码常量，其中 42 处是裸登录
            # （直接 post /auth/login 读响应体，用不上这里的自愈），真改密码会让
            # "当前密码"在 100+ 个 Client 实例之间漂移。
            # 故 e2e 服务端以 MUST_CHANGE_PASSWORD_ENFORCED=false 启动，拦截本身
            # 不生效，这里**不需要**再跑自愈。
            #
            # 强制改密行为的真实断言在 tests/test_unit_must_change_pwd.py：
            # 那一层用 monkeypatch 把开关设回 true，逐条验证 403/400/200 三个分支。
            # 专门验证拦截行为的 e2e 用例请直接用 client.post("/auth/login")
            # （test_requirements.py 的三处即如此），不走本方法。
            return True, f"{self.user.get('real_name')}（{','.join(self.permission.get('roles', []))}）"
        return False, payload.get("message", "登录失败")


def is_down(payload):
    return bool(payload.get("_unreachable"))


def data_of(payload):
    """兼容 data 可能是 dict / list 的情况。"""
    return payload.get("data")


def rows_of(payload):
    """统一取出列表型数据：兼容 {items:[...]} / {...} / [ ... ] 三种返回形态。"""
    d = data_of(payload)
    if isinstance(d, list):
        return d
    if isinstance(d, dict):
        for k in ("items", "list", "rows", "records", "data"):
            if isinstance(d.get(k), list):
                return d[k]
    return []


def total_of(payload):
    """取 total，缺失时退化为列表长度。"""
    d = data_of(payload)
    if isinstance(d, dict):
        for k in ("total", "count", "total_count"):
            if k in d:
                return d[k]
        for k in ("items", "list", "rows", "records"):
            if isinstance(d.get(k), list):
                return len(d[k])
    if isinstance(d, list):
        return len(d)
    return 0


# ================================================================
#  断言辅助
# ================================================================
def check(name, condition, detail=""):
    return R.add(name, bool(condition), detail)


# ---------------------------------------------------------------- 服务器时间
def server_now():
    """取**服务端**当前时间（naive datetime），用于构造/校验时间窗参数。

    ⚠️ 绝对不要用 `datetime.now()`（测试进程本地时区）去拼 `start_at` /
    `publish_at` / `deadline`：

    - 本地跑：测试进程和容器都在 Asia/Shanghai，碰巧一致，看不出问题；
    - CI 跑：GitHub runner 是 **UTC**，而镜像里 `TZ=Asia/Shanghai`，
      两边差 8 小时。于是 `now + 1h`（UTC）= 北京时间「7 小时前」，
      服务端判定已经到点 → 定时发布任务被**立即发布**（用例期望「存为草稿」）；
      「未开考」用例同理翻成「已开始」。

    这类失败的特征是「本机全绿、CI 必红」，且只有时间相关用例成片倒下。
    统一从服务端 `/health` 的 `server_time` 取时间，彻底消除时区依赖。
    """
    payload = {}
    try:
        # ⚠️ `BASE` / `_detect_base()` 返回的**已包含** `/api/v1` 前缀
        # （见本文件第 42/66 行），这里只能拼 `/health`。
        # 曾经写成 `_detect_base() + "/api/v1/health"` → 实际请求
        # `/api/v1/api/v1/health` 必然 404 → 静默落到下面的 `datetime.now()`
        # 兜底。本地因测试进程与容器同时区，兜底值恰好正确，问题被完全掩盖；
        # 一旦到了 CI（runner UTC / 容器 Asia/Shanghai）就退回旧的坏行为。
        # 这类「兜底掩盖主逻辑失效」的写法必须靠**断言走的是主路径**来防。
        req = urllib.request.Request(BASE + "/health", method="GET")
        # 绕开系统代理：本机有 https_proxy 时 urllib 会把 localhost 也代理走
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(req, timeout=5) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except Exception:
        payload = {}
    raw = (payload.get("data") or {}).get("server_time")
    if raw:
        try:
            return datetime.strptime(str(raw)[:19], "%Y-%m-%d %H:%M:%S")
        except ValueError:
            pass
    # 兜底：接口未回时间时退回本地时间（至少与旧行为一致，不会更差）
    #
    # ⚠️ 兜底必须**吵**：静默降级正是上一次时区 bug 在本地全绿的原因。
    # 一旦走了这条路，说明 CI 上时间相关问题会重新出现，日志必须一眼可见。
    print(f"[WARN] 未能从服务端取到 server_time（{BASE}/health），"
          f"回退到本地时间 {datetime.now():%Y-%m-%d %H:%M:%S}；"
          f"CI 与容器时区不一致时，时间窗用例会假失败。")
    return datetime.now()


def dt_str(dt):
    """格式化成后端 `_parse_dt` 唯一接受的格式（**不支持 ISO 的 T 分隔**）。"""
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def expect_denied(name, client, method, path, body=None, params=None,
                  allow_statuses=()):
    """断言「应当被拒绝」，且**必须是被拒绝**，不能是接口出错。

    判定标准（两条同时满足）：
      1. HTTP 状态码属于拒绝类 —— 默认 {401, 403}（未认证 / 权限不足）；
         数据隔离场景后端可能故意返回 404（不暴露资源是否存在），
         个别历史实现用 400 表达「无权」，由调用方用 allow_statuses 显式声明。
      2. 响应 success 不为 True。

    为什么不能只判 success：原实现只要 `success is not True` 就算通过，
    于是 500（服务端异常）、422（参数校验失败）、405（HTTP 方法用错）、
    404（路径写错）都会被当成「越权已拦截」而 PASS —— 接口崩了、请求发错了
    反而全绿，门禁形同虚设。收紧后，这些情况一律 FAIL 并打印实际状态码与响应。
    """
    fn = {"GET": client.get, "POST": client.post,
          "PUT": client.put, "DELETE": client.delete}[method]
    payload, ms, status = fn(path, body=body, params=params)
    if is_down(payload):
        return R.env(name, payload.get("message", "服务不可达"))

    allowed = (401, 403) + tuple(allow_statuses)
    if payload.get("success") is not True and status in allowed:
        return R.add(name, True, payload.get("message", "") or f"{ms}ms")

    # 失败时把「实际状态码 + 响应体」打出来，方便区分两种成因：
    # 真越权（2xx / success=True）还是请求本身有问题（405/422/404/500）。
    detail = (f"{method} {path} -> HTTP {status}（期望拒绝码 {sorted(allowed)}）；"
              f"message={str(payload.get('message', ''))[:80]!r}；"
              f"响应={str(payload)[:200]}")
    if payload.get("success") is True:
        R.issue("高", f"越权未拦截：{name}", detail, f"{method} {path}")
    else:
        R.issue("高", f"越权断言拒绝码异常：{name}", detail, f"{method} {path}")
    return R.add(name, False, detail)


def api_ok(name, client, method, path, body=None, params=None, expect_keys=None):
    """调用接口并断言 success=True。"""
    fn = {"GET": client.get, "POST": client.post,
          "PUT": client.put, "DELETE": client.delete}[method]
    payload, ms, status = fn(path, body=body, params=params)
    if is_down(payload):
        return R.env(name, payload.get("message", "服务不可达")), payload
    ok = payload.get("success") is True
    detail = payload.get("message") if not ok else f"{ms}ms"
    if ok and expect_keys:
        d = data_of(payload)
        missing = [k for k in expect_keys
                   if not (isinstance(d, dict) and k in d)]
        if missing:
            ok = False
            detail = f"响应缺少字段 {missing}"
    if ok and not detail:
        detail = f"{ms}ms"
    return R.add(name, ok, detail), payload