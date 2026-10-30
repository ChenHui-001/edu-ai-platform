"""试卷管理模块完整功能校验（创建 / 编辑 / 删除 / 查询 / 发布 / 校验）。

设计目标：**一个脚本跑完整条业务链**，不依赖外部已在跑的服务——
自动起一个临时库 + 临时端口的 uvicorn，播完种子数据后按顺序跑用例，
结束时关服务删临时目录。这样在本地、CI、以及任何干净机器上结果一致。

覆盖面（每个 check 对应一条可复现的断言）：
  A 创建：正常 / 空名 / 名称边界 128·129 / 空题目 / 重复题 / 不存在的题 /
          跨年级题 / 分值越界 / 全 0 分 / 时长边界 / 年级不存在 / 学科错配 / 越权
  B 编辑：改名 / 换题（含作答保留计数）/ 只改年级触发题目不一致 / 非创建者 / 404 / 空名
  C 查询：列表 / 关键词 / 年级学科筛选 / 分页 / 统计 / 详情 404 / 私有隔离 / 越权读
  D 发布：直设 public 被拒 / grade 共享 / 同年级可读·跨年级不可读 / 共享库不越界 /
          提交审核 / 重复提交 / 教师审核被拒 / 管理员通过 / 公共库可见 /
          驳回需意见 / 收藏与取消 / 已进公共库再提交
  E 复制：复制成功 / 大题结构保留 / 副本状态为草稿且私有 / 404
  F 删除：非创建者被拒 / 被任务引用被拒 / 正常删除 / 批量删除的 skipped
  G 组卷：题库优先抽题 / 不抽他人私有题 / 保存 / 仅 AI 生成能出题 /
          题型与大题一致 / 非法来源 / 跨年级知识点

用法：
    python tools/verify_paper_module.py            # 全部跑
    python tools/verify_paper_module.py --keep      # 失败时保留临时目录与日志
退出码 0 = 全部通过。
"""
import argparse

import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND = os.path.join(ROOT, "backend")
PY = sys.executable

PASSED, FAILED, SKIPPED = [], [], []


def check(name, ok, detail=""):
    tag = "PASS" if ok else "FAIL"
    print(f"  {tag}  {name}" + (f"  -> {detail}" if detail and not ok else ""))
    (PASSED if ok else FAILED).append(name)
    return ok


def skip(name, why=""):
    print(f"  SKIP  {name}" + (f"  -> {why}" if why else ""))
    SKIPPED.append(name)


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def data_of(payload):
    return (payload or {}).get("data") or {}


def msg_of(resp):
    try:
        return str((resp.json() or {}).get("message") or "")[:200]
    except Exception:  # noqa: BLE001
        return (resp.text or "")[:200]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--keep", action="store_true", help="失败时保留临时目录（含服务日志）")
    args = ap.parse_args()

    import httpx

    port = free_port()
    base = f"http://127.0.0.1:{port}"
    api = f"{base}/api/v1"
    tmpdir = tempfile.mkdtemp(prefix="papermodule_")
    db_path = os.path.join(tmpdir, "test.db")
    log_path = os.path.join(tmpdir, "server.log")

    env = dict(os.environ)
    env.update({
        # 测试必须关掉真实大模型：AI 分支要验证的是"无 LLM 时也能出题"的降级路径
        "LLM_ENABLED": "false",
        "CAPTCHA_ENFORCED": "false",
        "SEED_DEMO_DATA": "false",
        "SCHEDULER_ENABLED": "false",
        "APP_VERSION": "test",
        "DATABASE_URL": f"sqlite:///{db_path}",
        "SECRET_KEY": "paper-module-test-key-0123456789",
        "TZ": "Asia/Shanghai",
    })
    logf = open(log_path, "w", encoding="utf-8")
    proc = subprocess.Popen(
        [PY, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", str(port)],
        cwd=BACKEND, env=env, stdout=logf, stderr=subprocess.STDOUT,
    )


    try:
        deadline = time.time() + 180
        ready = False
        while time.time() < deadline:
            try:
                r = httpx.get(f"{api}/health", timeout=3)
                if r.status_code == 200:
                    ready = True
                    break
            except Exception:  # noqa: BLE001
                pass
            time.sleep(1.5)
        if not ready:
            print("服务未就绪，日志尾部：")
            print(open(log_path, encoding="utf-8", errors="replace").read()[-3000:])
            return 1

        run_cases(httpx, api)
        print("\n" + "=" * 60)
        if FAILED:
            print(f"失败 {len(FAILED)} 项（通过 {len(PASSED)} 项）：")
            for f in FAILED:
                print("  -", f)
            print(f"\n服务日志：{log_path}")
            return 1
        print(f"全部通过：{len(PASSED)} 项" + (f"，跳过 {len(SKIPPED)} 项" if SKIPPED else ""))
        return 0
    finally:
        try:
            proc.terminate()
            proc.wait(timeout=15)
        except Exception:  # noqa: BLE001
            try:
                proc.kill()
            except Exception:  # noqa: BLE001
                pass
        logf.close()
        if not (args.keep and FAILED):
            shutil.rmtree(tmpdir, ignore_errors=True)


def run_cases(httpx, api):
    # ------------------------------------------------------------ 0. 准备
    print("\n=== 0. 准备（管理员 / 三教师 / 学生 / 题库）===")

    def post(path, body, hdr=None, expect=None, timeout=60):
        r = httpx.post(f"{api}{path}", json=body, headers=hdr or {}, timeout=timeout)
        return r

    def get(path, hdr=None, params=None, timeout=60):
        return httpx.get(f"{api}{path}", headers=hdr or {}, params=params or {}, timeout=timeout)

    # 出厂管理员带 must_change_password=True：先改密再重登，否则所有业务接口都 403
    r = post("/auth/login", {"username": "admin", "password": "Admin@123456"})
    adm_tok = data_of(r.json()).get("access_token")
    if not adm_tok:
        check("管理员登录", False, msg_of(r))
        return False
    HA = {"Authorization": f"Bearer {adm_tok}"}
    rpw = httpx.put(f"{api}/auth/password", headers=HA, timeout=60, json={
        "old_password": "Admin@123456", "new_password": "Adm@Test2026!"})
    if rpw.status_code != 200:
        print(f"  [debug] 改密返回 {rpw.status_code} {msg_of(rpw)}")
    r = post("/auth/login", {"username": "admin", "password": "Adm@Test2026!"})
    adm_tok = data_of(r.json()).get("access_token")
    HA = {"Authorization": f"Bearer {adm_tok}"}
    check("管理员登录（含首次强制改密）", bool(adm_tok), msg_of(r))
    if not adm_tok:
        return False

    def login(u, p):
        rr = post("/auth/login", {"username": u, "password": p})
        return data_of(rr.json()).get("access_token")

    g_data = data_of(get("/edu/grades", HA).json())
    g_items = g_data if isinstance(g_data, list) else (g_data.get("items") or [])
    g7 = next((g for g in g_items if g.get("grade_num") == 7), None)
    g9 = next((g for g in g_items if g.get("grade_num") == 9), None)

    def subjects_of(gid):
        d = data_of(get("/edu/subjects", HA, {"grade_id": gid}).json())
        return d if isinstance(d, list) else (d.get("items") or [])

    s7 = next((s for s in subjects_of(g7["id"]) if s["name"] == "数学"), None)
    s9 = next((s for s in subjects_of(g9["id"]) if s["name"] == "数学"), None)
    check("取到七/九年级数学", bool(s7 and s9),
          f"g7={g7 and g7.get('id')} g9={g9 and g9.get('id')} s7={s7 and s7.get('id')}")

    uniq = str(int(time.time()))[-6:]

    def make_user(prefix, real, identity, grade_id, class_id=None):
        body = {
            "username": f"{prefix}{uniq}", "real_name": real, "password": "Pass@123456",
            "identity": identity, "grade_id": grade_id, "status": "active",
            "roles": [identity], "must_change_password": False,
        }
        if class_id:
            body["class_id"] = class_id
        rr = post("/system/users", body, HA)
        return data_of(rr.json())

    cls = data_of(post("/edu/classes", {
        "name": f"试卷模块班{uniq}", "grade_id": g7["id"], "head_teacher_id": None}, HA).json())
    cls_id = cls.get("id")

    ua = make_user("ka", f"甲教师{uniq}", "teacher", g7["id"])
    ub = make_user("kb", f"乙教师{uniq}", "teacher", g7["id"])
    uc = make_user("kc", f"丙教师{uniq}", "teacher", g9["id"])
    stu = make_user("ks", f"试卷学生{uniq}", "student", g7["id"], cls_id)
    check("准备账号（3 教师 + 1 学生）",
          all(x.get("id") for x in (ua, ub, uc, stu)),
          str([x.get("id") for x in (ua, ub, uc, stu)]))

    HAa = {"Authorization": f"Bearer {login(f'ka{uniq}', 'Pass@123456')}"}
    HAb = {"Authorization": f"Bearer {login(f'kb{uniq}', 'Pass@123456')}"}
    HAc = {"Authorization": f"Bearer {login(f'kc{uniq}', 'Pass@123456')}"}
    HS = {"Authorization": f"Bearer {login(f'ks{uniq}', 'Pass@123456')}"}
    check("三教师 + 学生均可登录",
          all(len(h["Authorization"]) > 20 for h in (HAa, HAb, HAc, HS)))

    def new_q(stem, hdr, *, qtype="single", score=10, bank_type="public",
              grade_id=None, subj_id=None, answer="B"):
        body = {
            "type": qtype, "difficulty": "medium", "score": score, "stem": stem,
            "options": [{"key": "A", "text": "甲"}, {"key": "B", "text": "乙"}],
            "answer": answer, "analysis": "验证用解析。",
            "grade_id": grade_id or g7["id"], "subject_id": subj_id or s7["id"],
            "status": "published", "bank_type": bank_type,
        }
        rr = post("/question/questions", body, hdr)
        return data_of(rr.json()).get("id")

    # 乙教师的私有题**先建**：id 最小，旧版抽题（按 usage_count desc→id asc）
    # 会优先抽到它 —— 这是"组卷抽到他人私有题"缺陷的复现前提。
    q_priv_b = new_q(f"【私有·乙】{uniq} 私有题", HAb, bank_type="private")
    # 填空题**故意建在单选题之前**：它的 id 更小。若缺口丢失大题顺序（sort=0），
    # `_renumber` 只能按题号排，"填空题"会跑到"单选题"前面 —— 这条数据布局
    # 让顺序缺陷必然暴露，而不是靠运气。
    q_blank = new_q(f"【公共·{uniq}】填空题", HA, qtype="blank", answer="2")
    pub = [new_q(f"【公共·{uniq}】单选 {i}", HA) for i in range(1, 7)]
    check("题库准备（1 私有 + 1 填空 + 6 单选）",
          bool(q_priv_b) and bool(q_blank) and all(pub),
          f"priv={q_priv_b} blank={q_blank} pub={pub}")
    # 教师建公共题会被强制降级为 draft（防自行上架），这里顺带确认该守卫仍在
    new_q(f"【教师建·{uniq}】公共题", HAa, bank_type="public")
    rr = get("/question/questions", HAa, {"keyword": f"【教师建·{uniq}】"})
    rows = data_of(rr.json()).get("items") or []
    check("教师建公共题被降级为 draft（不能自行上架）",
          bool(rows) and rows[0].get("status") == "draft",
          str(rows[0].get("status") if rows else None))

    def new_paper(name, hdr, **kw):
        body = {"name": name, "grade_id": g7["id"], "subject_id": s7["id"],
                "duration": 60, "items": [{"question_id": q, "score": 10} for q in pub[:3]]}
        body.update(kw)
        return post("/question/papers", body, hdr)

    # ------------------------------------------------------------ A. 创建
    print("\n=== A. 创建试卷 ===")
    name_a = f"试卷模块验证卷{uniq}"
    r = new_paper(name_a, HAa, total_score=999)
    d = data_of(r.json())
    pid = d.get("id")
    check("创建成功（伪造 total_score 被忽略）",
          r.status_code == 200 and d.get("total_score") == 30,
          f"{r.status_code} {d}")

    r = get(f"/question/papers/{pid}", HAa)
    d = data_of(r.json())
    check("详情返回 3 道题且汇总字段齐全",
          len(d.get("items") or []) == 3 and d.get("creator_name")
          and d.get("subject_name") and d.get("grade_name"),
          str({k: d.get(k) for k in ("item_count", "creator_name", "subject_name")}))
    check("手工建卷 source 固定 manual", d.get("source") == "manual", str(d.get("source")))

    r = new_paper("", HAa)
    check("空名称被拒", r.status_code == 400, f"{r.status_code} {msg_of(r)}")

    r = new_paper("N" * 128, HAa)
    check("名称 128 字符（边界）通过", r.status_code == 200, f"{r.status_code} {msg_of(r)}")

    r = new_paper("N" * 129, HAa)
    check("名称 129 字符被拒", r.status_code == 400, f"{r.status_code} {msg_of(r)}")

    r = post("/question/papers", {"name": f"空卷{uniq}", "grade_id": g7["id"],
                                  "subject_id": s7["id"], "items": []}, HAa)
    check("空题目列表被拒", r.status_code == 400, f"{r.status_code} {msg_of(r)}")

    r = new_paper(f"重复题{uniq}", HAa,
                  items=[{"question_id": pub[0], "score": 10},
                         {"question_id": pub[0], "score": 10}])
    check("同一题重复出现被拒", r.status_code == 400, f"{r.status_code} {msg_of(r)}")

    r = new_paper(f"不存在题{uniq}", HAa, items=[{"question_id": 99_999_999, "score": 10}])
    check("不存在的题目被拒", r.status_code == 400, f"{r.status_code} {msg_of(r)}")

    r = new_paper(f"跨年级题{uniq}", HAa,
                  items=[{"question_id": new_q(f"【九年级】{uniq}", HA, grade_id=g9["id"],
                                               subj_id=s9["id"]), "score": 10}])
    check("跨年级题目被拒", r.status_code == 400, f"{r.status_code} {msg_of(r)}")

    r = new_paper(f"分越界{uniq}", HAa, items=[{"question_id": pub[0], "score": 1001}])
    check("单题分值 >1000 被拒", r.status_code == 400, f"{r.status_code} {msg_of(r)}")

    r = new_paper(f"零分卷{uniq}", HAa, items=[{"question_id": pub[0], "score": 0}])
    check("全 0 分试卷被拒（否则永远发不出去）", r.status_code == 400,
          f"{r.status_code} {msg_of(r)}")

    for dur, want, label in ((0, 400, "时长 0 被拒"), (301, 400, "时长 301 被拒"),
                             (1, 200, "时长 1（边界）通过")):
        r = new_paper(f"时长{dur}{uniq}", HAa, duration=dur)
        check(label, r.status_code == want, f"{r.status_code} {msg_of(r)}")

    r = new_paper(f"坏年级{uniq}", HAa, grade_id=99_999_999)
    check("不存在的年级被拒", r.status_code == 400, f"{r.status_code} {msg_of(r)}")

    r = new_paper(f"学科错配{uniq}", HAa, subject_id=s9["id"])
    check("年级与学科错配被拒", r.status_code == 400, f"{r.status_code} {msg_of(r)}")

    r = new_paper(f"越权建卷{uniq}", HS)
    check("学生无 paper:write 权限（403）", r.status_code == 403, f"{r.status_code}")

    # ------------------------------------------------------------ B. 编辑
    print("\n=== B. 编辑试卷 ===")
    new_name = f"{name_a}-改名"
    r = httpx.put(f"{api}/question/papers/{pid}",
                  json={"name": new_name}, headers=HAa, timeout=60)
    d = data_of(r.json())
    d2 = data_of(get(f"/question/papers/{pid}", HAa).json())
    check("改名成功且详情已更新",
          r.status_code == 200 and d2.get("name") == new_name,
          f"{r.status_code} {d2.get('name')}")

    r = httpx.put(f"{api}/question/papers/{pid}", json={
        "items": [{"question_id": pub[0], "score": 12},
                  {"question_id": pub[1], "score": 8}]}, headers=HAa, timeout=60)
    d = data_of(r.json())
    d2 = data_of(get(f"/question/papers/{pid}", HAa).json())
    check("换题后题量与总分同步更新",
          r.status_code == 200 and len(d2.get("items") or []) == 2
          and d2.get("total_score") == 20,
          f"{r.status_code} items={len(d2.get('items') or [])} total={d2.get('total_score')}")
    check("换题返回作答保留/作废计数（dropped_answers）",
          "dropped_answers" in d and d.get("dropped_answers") == 0, str(d))

    r = httpx.put(f"{api}/question/papers/{pid}",
                  json={"grade_id": g9["id"], "subject_id": s9["id"]},
                  headers=HAa, timeout=60)
    check("只改年级学科但题目不一致被拒", r.status_code == 400,
          f"{r.status_code} {msg_of(r)}")

    r = httpx.put(f"{api}/question/papers/{pid}", json={"name": ""}, headers=HAa, timeout=60)
    check("改名为空被拒", r.status_code == 400, f"{r.status_code} {msg_of(r)}")

    r = httpx.put(f"{api}/question/papers/{pid}", json={"name": f"越权{uniq}"},
                  headers=HAb, timeout=60)
    check("非创建者编辑被拒（403）", r.status_code == 403, f"{r.status_code}")

    r = httpx.put(f"{api}/question/papers/99999999", json={"name": "x"},
                  headers=HAa, timeout=60)
    check("编辑不存在的试卷（404）", r.status_code == 404, f"{r.status_code}")

    # ------------------------------------------------------------ C. 查询
    print("\n=== C. 查询试卷 ===")
    d = data_of(get("/question/papers", HAa, {"keyword": uniq}).json())
    names = [p.get("name") for p in (d.get("items") or [])]
    check("列表按关键词命中", any(new_name == n for n in names), str(names)[:200])

    d = data_of(get("/question/papers", HAa,
                    {"subject_id": s7["id"], "grade_id": g7["id"]}).json())
    check("按年级+学科筛选可用",
          d.get("total", 0) >= 1
          and all(p.get("subject_id") == s7["id"] for p in (d.get("items") or [])),
          str(d.get("total")))

    d = data_of(get("/question/papers", HAa,
                    {"page": 1, "page_size": 2, "keyword": uniq}).json())
    check("分页 page_size 生效",
          len(d.get("items") or []) <= 2 and d.get("total", 0) >= 1,
          f"items={len(d.get('items') or [])} total={d.get('total')}")

    d = data_of(get("/question/papers/stats", HAa, {"keyword": uniq}).json())
    check("统计接口自洽（total_items ≥ total）",
          d.get("total_items", 0) >= d.get("total", 0)
          and isinstance(d.get("by_subject"), dict),
          str({k: d.get(k) for k in ("total", "total_items", "avg_score")}))

    r = get("/question/papers/99999999", HAa)
    check("详情不存在（404）", r.status_code == 404, f"{r.status_code}")

    d = data_of(get("/question/papers", HAb, {"keyword": uniq}).json())
    check("他人私有卷不出现在乙的列表",
          all(p.get("id") != pid for p in (d.get("items") or [])),
          str([p.get("id") for p in (d.get("items") or [])]))

    check("乙直接读甲私有卷被拒（403）",
          get(f"/question/papers/{pid}", HAb).status_code == 403)

    # ------------------------------------------------------------ D. 发布/共享/审核
    print("\n=== D. 共享范围 / 审核发布 ===")
    r = post(f"/question/papers/{pid}/share-scope", {"scope": "public"}, HAa)
    check("不能直接设为 public（必须走审核）", r.status_code == 400,
          f"{r.status_code} {msg_of(r)}")

    r = post(f"/question/papers/{pid}/share-scope", {"scope": "bogus"}, HAa)
    check("非法 scope 被拒", r.status_code == 400, f"{r.status_code} {msg_of(r)}")

    r = post(f"/question/papers/{pid}/share-scope", {"scope": "grade"}, HAa)
    check("设为同年级共享成功", r.status_code == 200, f"{r.status_code} {msg_of(r)}")
    check("同年级教师乙可读", get(f"/question/papers/{pid}", HAb).status_code == 200)
    check("跨年级教师丙不可读（403）",
          get(f"/question/papers/{pid}", HAc).status_code == 403)

    d = data_of(get("/question/papers/library/list", HAc, {"scope": "shared"}).json())
    check("丙的「共享给我」不含跨年级卷（列表/详情一致）",
          all(p.get("id") != pid for p in (d.get("items") or [])),
          str([p.get("id") for p in (d.get("items") or [])])[:160])

    r = post(f"/question/papers/{pid}/review", {"action": "submit"}, HAa)
    check("提交审核成功", r.status_code == 200
          and data_of(r.json()).get("status") == "pending",
          f"{r.status_code} {r.text[:120]}")

    r = post(f"/question/papers/{pid}/review", {"action": "submit"}, HAa)
    check("重复提交审核被拒", r.status_code == 400, f"{r.status_code} {msg_of(r)}")

    r = post(f"/question/papers/{pid}/review", {"action": "approve"}, HAa)
    check("教师无权审核（403）", r.status_code == 403, f"{r.status_code}")

    r = post(f"/question/papers/{pid}/review", {"action": "approve"}, HA)
    d = data_of(r.json())
    check("管理员审核通过 → published + public",
          r.status_code == 200 and d.get("status") == "published"
          and d.get("share_scope") == "public", f"{r.status_code} {d}")

    check("跨年级教师丙此时可读（公共库）",
          get(f"/question/papers/{pid}", HAc).status_code == 200)

    d = data_of(get("/question/papers/library/list", HAc, {"scope": "public"}).json())
    check("公共库列表包含该卷",
          any(p.get("id") == pid for p in (d.get("items") or [])),
          str(d.get("total")))

    r = post(f"/question/papers/{pid}/review", {"action": "submit"}, HAa)
    check("已进公共库的卷不能再提交审核", r.status_code == 400,
          f"{r.status_code} {msg_of(r)}")

    # 驳回流程：另建一份卷走 submit → reject
    pid_rej = data_of(new_paper(f"待驳回卷{uniq}", HAa).json()).get("id")
    post(f"/question/papers/{pid_rej}/review", {"action": "submit"}, HAa)
    r = post(f"/question/papers/{pid_rej}/review", {"action": "reject"}, HA)
    check("驳回未填意见被拒", r.status_code == 400, f"{r.status_code} {msg_of(r)}")
    r = post(f"/question/papers/{pid_rej}/review",
             {"action": "reject", "comment": "难度结构待调整"}, HA)
    check("驳回成功并记录意见",
          r.status_code == 200
          and data_of(r.json()).get("review_comment") == "难度结构待调整",
          f"{r.status_code} {r.text[:120]}")

    r = post(f"/question/papers/{pid}/favorite", {}, HAb)
    check("收藏成功", r.status_code == 200 and data_of(r.json()).get("favorite") is True,
          f"{r.status_code} {r.text[:100]}")
    d = data_of(get("/question/papers/library/list", HAb, {"scope": "favorite"}).json())
    check("收藏夹包含该卷",
          any(p.get("id") == pid for p in (d.get("items") or [])), str(d.get("total")))
    r = post(f"/question/papers/{pid}/favorite", {"favorite": False}, HAb)
    check("取消收藏", r.status_code == 200 and data_of(r.json()).get("favorite") is False,
          f"{r.status_code} {r.text[:100]}")

    # ------------------------------------------------------------ E. 复制
    print("\n=== E. 复制试卷 ===")
    r = post(f"/question/papers/{pid}/copy", {}, HAb)
    d = data_of(r.json())
    copy_id = d.get("id")
    check("公共卷可被他人复制", r.status_code == 200 and bool(copy_id),
          f"{r.status_code} {d}")
    src = data_of(get(f"/question/papers/{pid}", HAa).json())
    cpy = data_of(get(f"/question/papers/{copy_id}", HAb).json())
    check("副本题量与源卷一致",
          len(cpy.get("items") or []) == len(src.get("items") or []),
          f"{len(cpy.get('items') or [])} vs {len(src.get('items') or [])}")
    check("副本状态为草稿且私有（不继承发布态）",
          cpy.get("status") == "draft" and cpy.get("share_scope") == "private",
          f"status={cpy.get('status')} scope={cpy.get('share_scope')}")
    prev = data_of(get(f"/question/papers/{copy_id}/preview", HAb).json())
    sec_codes = [s.get("section_code") for s in (prev.get("sections") or [])]
    # 创建时未传 section_code → 落库为 None，预览按题型归组；这里验的是归组未丢题
    check("副本预览可正常按大题归组（不丢题）",
          sum(s.get("item_count", 0) for s in (prev.get("sections") or []))
          == len(cpy.get("items") or []),
          str(sec_codes))

    r = post("/question/papers/99999999/copy", {}, HAa)
    check("复制不存在的试卷（404）", r.status_code == 404, f"{r.status_code}")

    # ------------------------------------------------------------ F. 删除
    print("\n=== F. 删除试卷 ===")
    r = httpx.delete(f"{api}/question/papers/{copy_id}", headers=HAc, timeout=60)
    check("非创建者删除被拒（403）", r.status_code == 403, f"{r.status_code}")

    # 被任务引用的卷：删卷会级联带走学生作答与成绩，必须阻断
    data_of(post("/task/tasks", {
        "title": f"引用卷任务{uniq}", "type": "exam", "paper_id": pid,
        "duration": 60, "allow_retake": 1, "show_answer": True,
        "student_ids": [stu.get("id")], "class_ids": [],
    }, HAa, timeout=90).json())
    r = httpx.delete(f"{api}/question/papers/{pid}", headers=HAa, timeout=60)
    check("被任务引用的试卷删除被拒",
          r.status_code == 400 and "引用" in msg_of(r),
          f"{r.status_code} {msg_of(r)}")

    r = httpx.delete(f"{api}/question/papers/{copy_id}", headers=HAb, timeout=60)
    check("删除无引用的副本成功", r.status_code == 200, f"{r.status_code} {msg_of(r)}")
    check("删除后详情 404", get(f"/question/papers/{copy_id}", HAb).status_code == 404)

    r = post("/question/papers/batch", {"action": "delete", "ids": [pid, 99_999_999]}, HAb)
    d = data_of(r.json())
    skipped = d.get("skipped") or []
    check("批量删除非本人卷被整体拒绝（403）", r.status_code == 403, f"{r.status_code}")

    r = post("/question/papers/batch", {"action": "delete", "ids": [pid, 99_999_999]}, HAa)
    d = data_of(r.json())
    skipped = d.get("skipped") or []
    check("批量删除：被引用卷进 skipped 而不是静默删除",
          r.status_code == 200
          and any(s.get("id") == pid for s in skipped)
          and any(s.get("id") == 99_999_999 for s in skipped),
          f"{r.status_code} {d}")

    r = post("/question/papers/batch", {"action": "bogus", "ids": [pid]}, HAa)
    check("批量操作非法 action 被拒", r.status_code == 400, f"{r.status_code}")

    # ------------------------------------------------------------ G. 组卷
    print("\n=== G. 标准组卷（含 AI 补题）===")
    sec = [{"code": "single", "name": "单选题", "count": 3, "score_per": 10,
            "difficulty": "medium"}]
    body = {"grade_id": g7["id"], "subject_id": s7["id"], "sections": sec,
            "source": "bank_only", "avoid_recent": False}

    r = post("/question/papers/compose/preview", body, HAa, timeout=120)
    d = data_of(r.json())
    items = d.get("items") or []
    ids = [i.get("question_id") for i in items]
    check("题库优先预览抽到题", r.status_code == 200 and len(items) == 3,
          f"{r.status_code} n={len(items)} {msg_of(r)}")
    check("抽题不含他人私有题（越权抽题已修）",
          q_priv_b not in ids, f"priv={q_priv_b} ids={ids}")

    r = post("/question/papers/compose/save", {**body, "name": f"组卷保存{uniq}"},
             HAa, timeout=120)
    d = data_of(r.json())
    saved_id = d.get("id")
    check("组卷保存落库成功",
          r.status_code == 200 and d.get("item_count") == 3 and bool(saved_id),
          f"{r.status_code} {d}")

    ai_body = {"grade_id": g7["id"], "subject_id": s7["id"], "sections": sec,
               "source": "ai_only", "avoid_recent": False}
    r = post("/question/papers/compose/preview", ai_body, HAa, timeout=180)
    d = data_of(r.json())
    ai_items = d.get("items") or []
    check("「仅使用 AI 生成」能出题（修复前为 0 题空卷）",
          r.status_code == 200 and len(ai_items) == 3,
          f"{r.status_code} n={len(ai_items)} msg={msg_of(r)}")
    check("AI 补题后题型与大题一致",
          all(i.get("type") == "single" and i.get("section_code") == "single"
              for i in ai_items),
          str([(i.get("type"), i.get("section_code")) for i in ai_items]))
    check("预览返回补题说明",
          "AI" in str(d.get("message") or ""), str(d.get("message"))[:160])

    r = post("/question/papers/compose/save", {**ai_body, "name": f"AI卷{uniq}"},
             HAa, timeout=180)
    d = data_of(r.json())
    check("仅 AI 生成的试卷可保存（不传 items，服务端重跑）",
          r.status_code == 200 and d.get("item_count", 0) > 0,
          f"{r.status_code} {d}")

    r = post("/question/papers/compose/preview", {**body, "source": "bogus"}, HAa)
    check("非法出题来源被拒", r.status_code == 400, f"{r.status_code} {msg_of(r)}")

    # 多题型全 AI：大题顺序必须与请求的结构一致，不能被题号顺序带偏
    sec2 = [
        {"code": "single", "name": "单选题", "count": 2, "score_per": 10,
         "difficulty": "medium", "sort": 1},
        {"code": "blank", "name": "填空题", "count": 1, "score_per": 10,
         "difficulty": "medium", "sort": 2},
    ]
    r = post("/question/papers/compose/preview",
             {"grade_id": g7["id"], "subject_id": s7["id"], "sections": sec2,
              "source": "ai_only", "avoid_recent": False}, HAa, timeout=180)
    d = data_of(r.json())
    codes = [i.get("section_code") for i in (d.get("items") or [])]
    check("多题型 AI 补题后大题顺序与请求一致（不被题号带偏）",
          r.status_code == 200 and codes == ["single", "single", "blank"],
          f"{r.status_code} codes={codes}")
    names = [i.get("section_name") for i in (d.get("items") or [])]
    check("大题序号按结构生成（一、二、而非全是一、）",
          names[:1] == ["一、单选题"] and names[-1:] == ["二、填空题"], str(names))

    kp = data_of(get("/edu/knowledge", HA,
                     {"grade_id": g9["id"], "subject_id": s9["id"]}).json())
    kp_rows = kp if isinstance(kp, list) else (kp.get("items") or [])
    if kp_rows:
        r = post("/question/papers/compose/preview",
                 {**body, "knowledge_point_ids": [kp_rows[0]["id"]]}, HAa)
        check("跨年级知识点被拒",
              r.status_code == 400 and "知识点" in msg_of(r),
              f"{r.status_code} {msg_of(r)}")
    else:
        skip("跨年级知识点被拒", "九年级数学无知识点数据")

    d = data_of(get(f"/question/papers/{saved_id}/preview", HAa).json())
    check("保存后的卷可按大题预览",
          d.get("item_count", 0) == 3 and len(d.get("sections") or []) == 1,
          f"item_count={d.get('item_count')} sections={len(d.get('sections') or [])}")

    return not FAILED


if __name__ == "__main__":
    sys.exit(main())
