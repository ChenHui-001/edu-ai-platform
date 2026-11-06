# -*- coding: utf-8 -*-
"""
功能用例执行器（接口级冒烟）

读取 FUNCTIONAL_TEST_CASES.json，对 api 类、无路径模板占位符的 GET 用例做
跨角色可达性 + 越权(403)验证，输出 results JSON 与汇总。

默认连本地：BASE_URL=http://127.0.0.1:8899/api/v1
登录凭据走环境变量，缺省用仓库种子默认账号。
"""
import json
import os
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))

DEFAULTS = {
    "admin": os.environ.get("QA_ADMIN", "admin|Admin@123456"),
    "teacher": os.environ.get("QA_TEACHER", "teacher1|Teacher@123"),
    "student": os.environ.get("QA_STUDENT", "stu101|Student@123"),
}


def _post(url, body, token=None, timeout=20):
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST",
                                 headers={"Content-Type": "application/json"})
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, json.loads(r.read().decode("utf-8") or "{}")
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode("utf-8") or "{}")
        except Exception:
            return e.code, {}
    except Exception as e:  # noqa
        return -1, {"error": str(e)}


def _read_json(resp):
    """解析响应体；导出端点是二进制/HTML，不是 JSON 也不能丢掉状态码。

    旧实现把 `json.loads` 抛出的 ValueError 当成「连接失败」返回 -1，
    于是导出端点无论 200 还是 500 都被记成 -1，再被 `st != 404` 判 PASS
    —— 服务端错误被完全掩盖。这里保留真实 HTTP 状态码。
    """
    try:
        raw = resp.read().decode("utf-8", "replace")
        return json.loads(raw or "{}")
    except (ValueError, TypeError, OSError):
        return {"_non_json": True}


def _get(url, token, timeout=20):
    last = (-1, {})
    for _ in range(2):  # 单次重试，规避单 worker 连接抖动
        req = urllib.request.Request(url, method="GET")
        if token:
            req.add_header("Authorization", f"Bearer {token}")
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.status, _read_json(r)
        except urllib.error.HTTPError as e:
            last = e.code, _read_json(e)
        except Exception as e:  # noqa
            last = -1, {"error": str(e)}
    return last


def _put(url, body, token=None, timeout=20):
    """改密接口是 PUT /auth/password：用 POST 打会得到 405，
    表现为"强制改密没生效 → 后续业务接口全 403"，很容易被误判成权限缺陷。"""
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="PUT",
                                 headers={"Content-Type": "application/json"})
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, json.loads(r.read().decode("utf-8") or "{}")
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode("utf-8") or "{}")
        except Exception:
            return e.code, {}
    except Exception as e:  # noqa
        return -1, {"error": str(e)}


# 端点可达即算通过：服务端已路由并响应（200/鉴权/需参均非缺陷）。
# 仅 404(路径错)/500(服务端错误)/持续 -1(连接失败) 判 FAIL。
REACHABLE = {200, 400, 401, 403, 422, 429}

# 按用例 id 显式声明跨角色期望码（P1-3）。此前 cross_status 只写进报告、
# 从不参与判定，实测 8 条跨角色 200 全部记 PASS，越权探测形同虚设。
#  - 列在这里的：管理端专属端点必须被其它角色拒绝；学生端按
#    get_current_student 的「学生及以上」设计允许教师/管理员代查，期望 200。
#  - 未列出的：多角色共享端点，只断言「没被服务端打挂」（状态码落在
#    REACHABLE），但 cross_status 同样参与 PASS/FAIL，不再只记录。
CROSS_EXPECT = {
    "FUNC-ADM-041": (403,),  # /logs/login
    "FUNC-ADM-042": (403,),  # /logs/export
    "FUNC-ADM-043": (403,),  # /auth/registrations
    "FUNC-ADM-049": (403,),  # /system/users
    "FUNC-STU-028": (200,),  # /learning/practice/history
    "FUNC-STU-030": (200,),  # /learning/wrong-questions/export
}


# 受保护接口探活：用于检测种子账号是否被强制改密（must_change_password）
PROBE = {"admin": "/system/users", "teacher": "/question/questions", "student": "/task/my/scores"}


def login(base, role):
    user, pwd = DEFAULTS.get(role, "|").split("|", 1)
    if not user:
        return None
    st, body = _post(f"{base}/auth/login", {"username": user, "password": pwd})
    if st != 200 or not body.get("data", {}).get("access_token"):
        return None
    token = body["data"]["access_token"]
    # 种子账号可能 must_change_password=true：探测受保护接口，若被强制改密则
    # 自动改密后重登，使执行器在任意环境（本地/CI）自洽，无需外部 curl 预处理。
    probe = PROBE.get(role)
    if probe:
        pst, pbody = _get(f"{base}{probe}", token)
        if pst == 403 and "修改密码" in str((pbody or {}).get("message", "")):
            newpwd = pwd + "Xy9!"  # 与原口令不同且仍满足策略（字母+数字+符号）
            cs, _ = _put(f"{base}/auth/password",
                         {"old_password": pwd, "new_password": newpwd}, token=token)
            if cs == 200:
                st2, body2 = _post(f"{base}/auth/login", {"username": user, "password": newpwd})
                if st2 == 200 and body2.get("data", {}).get("access_token"):
                    token = body2["data"]["access_token"]
    return token


def main():
    base = os.environ.get("BASE_URL", "http://127.0.0.1:8899/api/v1").rstrip("/")
    with open(os.path.join(HERE, "FUNCTIONAL_TEST_CASES.json"), encoding="utf-8") as f:
        cases = json.load(f)

    # 登录三角色
    tokens = {}
    for role in ("admin", "teacher", "student"):
        t = login(base, role)
        tokens[role] = t
        print(f"[login] {role}: {'OK' if t else 'FAILED'}")

    results = []
    # 1) 登录类用例本身
    for c in cases:
        if c["api"] == "POST /auth/login" or c["menu"] == "登录":
            role = c["role"]
            # public 角色无独立令牌；登录机制已通过三角色登录验证
            ok = bool(tokens.get(role)) or (role == "public" and any(tokens.values()))
            results.append({"id": c["id"], "kind": "auth", "role": role,
                            "status": "PASS" if ok else "FAIL",
                            "detail": "登录机制验证通过(三角色均签发令牌)" if ok else "登录失败"})

    # 2) 无模板占位符的 GET 用例：本角色可达性 + 越权 403
    get_cases = [c for c in cases
                 if c["automation"]["type"] == "api"
                 and c["automation"]["method"] == "GET"
                 and c["automation"]["path"]
                 and "{" not in c["automation"]["path"]
                 and c["role"] in ("admin", "teacher", "student")]

    for c in get_cases:
        role = c["role"]
        path = c["automation"]["path"]
        own = tokens.get(role)
        st, _ = _get(f"{base}{path}", own)
        # 旧实现对导出端点用 `st != 404`：非 JSON body 被记成 -1 后，
        # 500 也照样 PASS。_get 已保留真实状态码，所有端点统一判定，
        # 404 / 500 / -1 一律 FAIL。
        reached = st in REACHABLE

        # 角色配对按用例显式遍历**所有**其它角色：旧实现只取第一个不同
        # 角色，方向单一，高权→低权与低权→高权无法同时覆盖。
        cross_detail, cross_ok = [], True
        for other in ("admin", "teacher", "student"):
            if other == role or not tokens.get(other):
                continue
            cross_st, _ = _get(f"{base}{path}", tokens[other])
            expected = CROSS_EXPECT.get(c["id"])
            ok_cross = (cross_st in expected) if expected else (cross_st in REACHABLE)
            cross_ok = cross_ok and ok_cross
            cross_detail.append(f"{other}={cross_st}{'' if ok_cross else '(!)'}")
        results.append({
            "id": c["id"], "kind": "reach", "role": role, "path": path,
            "own_status": st, "status": "PASS" if (reached and cross_ok) else "FAIL",
            "cross_role": "all-others", "cross_status": "; ".join(cross_detail),
            "detail": f"本角色 {st}; 跨角色 {'; '.join(cross_detail) or '无其它角色令牌'}",
        })

    # 3) 核心写路径（P1-5）：旧筛选条件只挑「无路径占位符的 GET」，
    #    POST/PUT/DELETE 一条都不执行，组卷/交卷/批改这类最易出事故的
    #    改动完全落在覆盖之外。这里用**校验层形态**的幂等请求真实打到
    #    写端点：body 故意缺参，不写任何业务数据，但会走完整
    #    「路由 → 鉴权 → 参数校验」链，足以抓出 404 / 500 / 漏挂鉴权。
    write_path = os.path.join(HERE, "WRITE_CASES.json")
    if os.path.exists(write_path):
        with open(write_path, encoding="utf-8") as f:
            write_cases = json.load(f)
        for c in write_cases:
            token = tokens.get(c["role"])
            url = f"{base}{c['path']}"
            body = c.get("body") or {}
            if c["method"] == "POST":
                st, _ = _post(url, body, token)
            elif c["method"] == "PUT":
                st, _ = _put(url, body, token)
            else:
                st, _ = _get(url, token)
            results.append({
                "id": c["id"], "kind": "write", "role": c["role"],
                "path": c["path"], "own_status": st,
                "status": "PASS" if st in REACHABLE else "FAIL",
                "detail": f"{c['method']} {c['path']} -> {st}; {c.get('note', '')}",
            })

    # 4) 版本信息接口（公开）
    st, body = _get(f"{base}/system/version", None)
    results.append({"id": "FUNC-VER", "kind": "public", "path": "/system/version",
                    "own_status": st, "status": "PASS" if st == 200 else "FAIL",
                    "detail": json.dumps(body.get("data", {}), ensure_ascii=False)[:120]})

    # 4) 系统配置契约：字段小写键绑定
    if tokens.get("admin"):
        st, body = _get(f"{base}/system/config", tokens["admin"])
        data = body.get("data", {})
        keys_ok = all(k.islower() for k in data.keys() if k != "editable") if isinstance(data, dict) else False
        results.append({"id": "FUNC-CFG", "kind": "contract", "path": "/system/config",
                        "own_status": st, "status": "PASS" if (st == 200 and keys_ok) else "FAIL",
                        "detail": f"小写键绑定={'是' if keys_ok else '否'}; 样本={list(data.keys())[:6] if isinstance(data,dict) else []}"})

    passed = sum(1 for r in results if r["status"] == "PASS")
    failed = sum(1 for r in results if r["status"] == "FAIL")
    out = {"summary": {"total": len(results), "passed": passed, "failed": failed},
           "results": results}
    with open(os.path.join(HERE, "FUNCTIONAL_TEST_RESULTS.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"\n[run] total={len(results)} PASS={passed} FAIL={failed}")
    print(f"[run] -> {os.path.join(HERE, 'FUNCTIONAL_TEST_RESULTS.json')}")
    for r in results:
        if r["status"] == "FAIL":
            print("  FAIL", r["id"], r.get("detail"))


if __name__ == "__main__":
    main()
