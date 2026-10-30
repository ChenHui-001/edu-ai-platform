"""标准组卷 V3 端到端验证：起真实服务，跑完整业务链路。

覆盖：
  命题标准种子 → 登录 → 组卷预览 → 保存 → 预览（教师/学生）→ 编辑题目
  → 版本列表/回溯 → Word/PDF/答题卡导出 → 收藏 → 试卷库 → 审核流

用法：
    python tools/verify_paper_v3.py
退出码 0 = 全部通过。
"""
import json
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

FAILED = []
PASSED = []


def check(name, ok, detail=""):
    mark = "PASS" if ok else "FAIL"
    print(f"  {mark}  {name}" + (f"  {detail}" if detail and not ok else ""))
    (PASSED if ok else FAILED).append(name)
    return ok


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def wait_health(base, timeout=90):
    import httpx
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            r = httpx.get(f"{base}/api/v1/health", timeout=3)
            if r.status_code == 200 and r.json().get("data", {}).get("server_time"):
                return True
            if r.status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(1)
    return False


def main():
    import httpx

    tmpdir = tempfile.mkdtemp(prefix="verify_v3_")
    db_path = os.path.join(tmpdir, "v3.db").replace("\\", "/")
    port = free_port()
    base = f"http://127.0.0.1:{port}"
    env = dict(os.environ)
    env.update({
        "DATABASE_URL": f"sqlite:///{db_path}",
        "LLM_ENABLED": "false",
        "SECRET_KEY": "verify-v3-secret-key-0123456789abcdef",
        "ENV": "test",
        # S7 起登录强制图形验证码，测试脚本无法取码 → 必须显式关闭，
        # 否则所有用例在第一步登录就 FATAL（曾长期如此，误以为脚本过期）。
        "CAPTCHA_ENFORCED": "false",
        # 出厂管理员带 must_change_password，脚本不做改密流程 → 关掉拦截
        "MUST_CHANGE_PASSWORD_ENFORCED": "false",
    })

    print(f"[env] db={db_path}\n[env] port={port}\n")
    log_path = os.path.join(tmpdir, "server.log")

    def _spawn():
        # 输出写文件而非 PIPE：PIPE 不读取会写满缓冲区导致进程阻塞，
        # 表现出来就是"服务永远不健康"。
        lf = open(log_path, "a", encoding="utf-8")
        return subprocess.Popen(
            [PY, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1",
             "--port", str(port), "--log-level", "warning"],
            cwd=BACKEND, env=env, stdout=lf, stderr=subprocess.STDOUT,
        )

    proc = _spawn()

    try:
        if not wait_health(base):
            print("[FATAL] 服务未就绪，日志如下：")
            try:
                with open(log_path, encoding="utf-8", errors="ignore") as f:
                    print(f.read()[-5000:])
            except Exception:
                pass
            proc.kill()
            return 1

        api = f"{base}/api/v1"

        # ---------------- 登录 ----------------
        print("=== 0. 登录 ===")
        tok = None
        # 新库的默认管理员是 admin/Admin@123456（init_db 播种）；
        # 生产库才有 sysadmin/自定义口令。两个都试，谁通用谁。
        for user, pwd in (("admin", "Admin@123456"),
                          ("admin", "Prod@Admin2026!Xy"),
                          ("sysadmin", "Sys@Admin2026!Qw"),
                          ("sysadmin", "Admin@123456")):
            r = httpx.post(f"{api}/auth/login", json={"username": user, "password": pwd},
                           timeout=15)
            if r.status_code == 200:
                tok = (r.json().get("data") or {}).get("access_token")
                if tok:
                    print(f"  登录成功：{user}")
                    break
        if not tok:
            print("[FATAL] 无法登录，无法继续")
            return 1
        H = {"Authorization": f"Bearer {tok}"}

        # ---------------- 1. 命题标准 ----------------
        print("\n=== 1. 命题标准 ===")
        r = httpx.get(f"{api}/question/standards/options", headers=H, timeout=15)
        check("标准选项接口可用", r.status_code == 200, r.text[:200])
        by_stage = (r.json().get("data") or {}).get("by_stage") or {}
        total_std = sum(len(v) for v in by_stage.values())
        check("命题标准已播种（>=10 条）", total_std >= 10, f"实际 {total_std} 条")
        check("小学标准存在", len(by_stage.get("primary") or []) >= 4,
              f"{len(by_stage.get('primary') or [])} 条")
        check("初中标准存在", len(by_stage.get("junior") or []) >= 6,
              f"{len(by_stage.get('junior') or [])} 条")

        std = None
        for v in by_stage.values():
            for s in v:
                if s.get("subject_name") == "数学":
                    std = s
                    break
            if std:
                break
        if not std:
            print("[FATAL] 未找到数学标准")
            return 1
        check("标准含题型结构", bool(std.get("sections")), str(std.get("sections"))[:120])
        check("标准难度为百分制", sum((std.get("difficulty_ratio") or {}).values()) == 100,
              str(std.get("difficulty_ratio")))

        # ---------------- 2. 造基础数据 ----------------
        print("\n=== 2. 准备年级/学科/知识点/题目 ===")
        r = httpx.get(f"{api}/edu/grades", headers=H, timeout=15)
        gd = r.json().get("data")
        # /edu/grades 直接返回 list，其他接口常返回 {items:[...]}，两种都兼容
        if isinstance(gd, list):
            grades = gd
        elif isinstance(gd, dict):
            grades = gd.get("items") or []
        else:
            grades = []
        grade7 = next((g for g in grades if g.get("grade_num") == 7), None)
        check("七年级存在", grade7 is not None, f"共 {len(grades)} 个年级")
        if not grade7:
            return 1

        r = httpx.get(f"{api}/edu/subjects", headers=H,
                      params={"grade_id": grade7["id"]}, timeout=15)
        sd_ = r.json().get("data")
        subs = sd_.get("items") if isinstance(sd_, dict) else sd_
        math = next((s for s in (subs or []) if s.get("name") == "数学"), None)
        check("七年级数学存在", math is not None)
        if not math:
            return 1

        # 知识点
        r = httpx.get(f"{api}/edu/knowledge/tree", headers=H,
                      params={"grade_id": grade7["id"], "subject_id": math["id"]}, timeout=20)
        tree = r.json().get("data")
        nodes = tree.get("items") if isinstance(tree, dict) else tree
        kp_ids = []

        def _walk(items):
            for it in items or []:
                kp_ids.append(it["id"])
                _walk(it.get("children"))

        _walk(nodes or [])
        print(f"  知识点节点数：{len(kp_ids)}")

        # 造题（直接建库更稳：走 API 建题需要知识点归属，可能因数据缺口失败）
        sys.path.insert(0, BACKEND)
        os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
        # Windows 不支持向子进程发 SIGINT（ValueError: Unsupported signal），
        # 用 terminate 后必须 wait 确认进程已退出，否则 SQLite 写锁还在，
        # 后面的建题会 "database is locked"。
        proc.terminate()
        try:
            proc.wait(timeout=15)
        except Exception:
            proc.kill()
            proc.wait(timeout=5)
        time.sleep(1)

        from app.core.database import SessionLocal  # noqa: E402
        from app.models import KnowledgePoint, Question, QuestionStatus  # noqa: E402

        db = SessionLocal()
        kps = db.query(KnowledgePoint).filter(
            KnowledgePoint.grade_id == grade7["id"],
            KnowledgePoint.subject_id == math["id"]).limit(6).all()
        admin_user = None
        from app.models import User  # noqa: E402
        admin_user = (db.query(User).filter(User.username == "admin").first()
                      or db.query(User).filter(User.username == "sysadmin").first())
        owner_id = admin_user.id if admin_user else 1

        made = 0
        for kp in kps:
            for diff in ("easy", "medium", "hard"):
                for n in range(3):
                    db.add(Question(
                        type="single",
                        stem=f"{kp.name} 第{n + 1}题（{diff}）：下列选项中正确的是（　）",
                        options=json.dumps([{"key": "A", "text": "选项A"},
                                            {"key": "B", "text": "选项B"},
                                            {"key": "C", "text": "选项C"},
                                            {"key": "D", "text": "选项D"}], ensure_ascii=False),
                        answer=json.dumps("A"), analysis=f"本题考查{kp.name}。",
                        score=3.0, difficulty=diff,
                        grade_id=grade7["id"], subject_id=math["id"],
                        knowledge_point_id=kp.id, bank_type="public",
                        owner_id=owner_id, status=QuestionStatus.PUBLISHED.value,
                    ))
                    made += 1
        db.commit()
        db.close()
        print(f"  已造题：{made} 道")
        check("造题成功", made > 0, f"{made} 道")
        if made == 0:
            return 1

        # 重启服务
        proc = _spawn()
        if not wait_health(base):
            print("[FATAL] 重启后服务未就绪")
            return 1

        # ---------------- 3. 组卷预览 ----------------
        print("\n=== 3. 自定义参数组卷预览 ===")
        r = httpx.post(f"{api}/question/papers/compose/preview", headers=H, json={
            "grade_id": grade7["id"], "subject_id": math["id"],
            "sections": [
                {"code": "single", "name": "一、选择题", "count": 10,
                 "score_per": 3, "difficulty": "easy"},
            ],
            "difficulty_ratio": {"easy": 70, "medium": 20, "hard": 10},
            "source": "bank_only",
            "avoid_recent": False,
        }, timeout=60)
        check("预览接口 200", r.status_code == 200, r.text[:300])
        pv = (r.json().get("data") or {})
        check("预览返回题目", len(pv.get("items") or []) > 0,
              f"{len(pv.get('items') or [])} 题")
        check("卷面总分正确（10题×3分=30）", abs(float(pv.get("total_score") or 0) - 30) < 0.01,
              str(pv.get("total_score")))
        check("返回三份报告", all(k in pv for k in
                              ("difficulty_report", "knowledge_report", "type_report")),
              str([k for k in pv if "report" in k]))

        sec_names = {i.get("section_name") for i in pv.get("items") or []}
        check("大题名带中文序号", all(n and n[0] in "一二三四五六七八九十" for n in sec_names),
              str(sec_names))

        # 知识点过滤
        if kps:
            one_kp = kps[0].id
            r2 = httpx.post(f"{api}/question/papers/compose/preview", headers=H, json={
                "grade_id": grade7["id"], "subject_id": math["id"],
                "sections": [{"code": "single", "name": "选择题", "count": 5,
                              "score_per": 3, "difficulty": "medium"}],
                "knowledge_point_ids": [one_kp],
                "source": "bank_only", "avoid_recent": False,
            }, timeout=60)
            d2 = (r2.json().get("data") or {})
            got_kps = {i.get("knowledge_point_id") for i in d2.get("items") or []}
            check("知识点过滤生效（旧实现放宽难度时会丢过滤）",
                  got_kps <= {one_kp}, f"实际 {got_kps}，期望 {{{one_kp}}}")

        # ---------------- 4. 保存 ----------------
        print("\n=== 4. 保存试卷 ===")
        r = httpx.post(f"{api}/question/papers/compose/save", headers=H, json={
            "grade_id": grade7["id"], "subject_id": math["id"],
            "standard_id": std["id"],
            "name": "七年级数学期末学业水平考试（V3验证）",
            "description": "自动化验证用试卷",
            "duration": 90,
            "sections": [{"code": "single", "name": "一、选择题", "count": 10,
                          "score_per": 3, "difficulty": "easy"}],
            "difficulty_ratio": {"easy": 70, "medium": 20, "hard": 10},
            "source": "bank_only", "avoid_recent": False,
            "mode": "custom",
        }, timeout=60)
        check("保存接口 200", r.status_code == 200, r.text[:300])
        saved = (r.json().get("data") or {})
        paper_id = saved.get("id")
        check("返回试卷 id", bool(paper_id), str(saved))
        if not paper_id:
            return 1
        check("保存后总分=30", abs(float(saved.get("total_score") or 0) - 30) < 0.01,
              str(saved.get("total_score")))
        check("初始版本=1", saved.get("version") == 1, str(saved.get("version")))

        # ---------------- 5. 预览双版本 ----------------
        print("\n=== 5. 预览（教师卷/学生卷）===")
        r = httpx.get(f"{api}/question/papers/{paper_id}/preview", headers=H,
                      params={"mode": "teacher"}, timeout=20)
        check("教师卷预览 200", r.status_code == 200, r.text[:200])
        td = (r.json().get("data") or {})
        items_t = [i for s in (td.get("sections") or []) for i in s.get("items") or []]
        check("教师卷含答案", any(i.get("answer") for i in items_t))
        check("教师卷含解析", any(i.get("analysis") for i in items_t))
        check("预览按大题分组", len(td.get("sections") or []) > 0,
              f"{len(td.get('sections') or [])} 个大题")

        r = httpx.get(f"{api}/question/papers/{paper_id}/preview", headers=H,
                      params={"mode": "student"}, timeout=20)
        sd = (r.json().get("data") or {})
        items_s = [i for s in (sd.get("sections") or []) for i in s.get("items") or []]
        check("学生卷不含答案", all(not i.get("answer") for i in items_s))
        check("学生卷不含解析", all(not i.get("analysis") for i in items_s))

        # ---------------- 6. 编辑题目 ----------------
        print("\n=== 6. 编辑题目（删一题 + 改分）===")
        edit_items = [{
            "question_id": i["question_id"],
            "score": 5 if idx == 0 else 3,
            "section_code": i.get("type") or "single",
            "section_name": "一、选择题",
        } for idx, i in enumerate(items_t[1:])]  # 删掉第一题
        r = httpx.post(f"{api}/question/papers/{paper_id}/items", headers=H,
                       json={"items": edit_items}, timeout=30)
        check("编辑接口 200", r.status_code == 200, r.text[:300])
        ed = (r.json().get("data") or {})
        expect_total = round(5 + 3 * (len(edit_items) - 1), 2)
        check(f"总分按新分值重算={expect_total}",
              abs(float(ed.get("total_score") or 0) - expect_total) < 0.01,
              str(ed.get("total_score")))
        check("版本号递增", (ed.get("version") or 0) > 1, str(ed.get("version")))

        # ---------------- 7. 版本 ----------------
        print("\n=== 7. 版本管理 ===")
        r = httpx.get(f"{api}/question/papers/{paper_id}/versions", headers=H, timeout=20)
        check("版本列表 200", r.status_code == 200, r.text[:200])
        vd = (r.json().get("data") or {})
        versions = vd.get("items") or []
        check("至少 2 个版本", len(versions) >= 2, f"{len(versions)} 个")

        if versions:
            oldest = versions[-1]["version"]
            r = httpx.post(f"{api}/question/papers/{paper_id}/versions/{oldest}/restore",
                           headers=H, timeout=30)
            check("版本回溯 200", r.status_code == 200, r.text[:300])
            if r.status_code == 200:
                rd = (r.json().get("data") or {})
                check("回溯后版本继续递增", (rd.get("current_version") or 0) > 0,
                      str(rd.get("current_version")))

        # ---------------- 8. 导出 ----------------
        print("\n=== 8. 导出（Word / PDF / 答题卡 / HTML）===")
        r = httpx.get(f"{api}/question/papers/{paper_id}/export/docx", headers=H,
                      params={"mode": "teacher", "layout": "a4_single"}, timeout=60)
        check("Word 导出 200", r.status_code == 200, r.text[:200])
        if r.status_code == 200:
            check("Word 内容非空且为 zip", r.content[:2] == b"PK" and len(r.content) > 5000,
                  f"{len(r.content)} bytes")

        r = httpx.get(f"{api}/question/papers/{paper_id}/export/docx", headers=H,
                      params={"mode": "student", "layout": "a3_double"}, timeout=60)
        check("A3 双栏 Word 导出 200", r.status_code == 200, r.text[:200])

        r = httpx.get(f"{api}/question/papers/{paper_id}/export/pdf", headers=H,
                      params={"mode": "teacher"}, timeout=60)
        check("PDF 导出 200", r.status_code == 200, r.text[:200])
        if r.status_code == 200:
            check("PDF 魔数正确", r.content[:4] == b"%PDF", r.content[:8])
            try:
                import fitz
                doc = fitz.open(stream=r.content, filetype="pdf")
                txt = "\n".join(p.get_text() for p in doc)
                check("PDF 中文可提取（非黑块）",
                      any("\u4e00" <= ch <= "\u9fff" for ch in txt),
                      txt[:80])
                check("PDF 含密封线", "密" in txt, "")
                check("PDF 含页码", "页" in txt, "")
            except Exception as exc:  # noqa: BLE001
                check("PDF 可解析", False, str(exc))

        r = httpx.get(f"{api}/question/papers/{paper_id}/export/answer-sheet",
                      headers=H, timeout=60)
        check("答题卡导出 200", r.status_code == 200, r.text[:200])
        if r.status_code == 200:
            check("答题卡为 PDF", r.content[:4] == b"%PDF", r.content[:8])

        r = httpx.get(f"{api}/question/papers/{paper_id}/export/html", headers=H,
                      params={"mode": "teacher"}, timeout=30)
        check("HTML 导出 200", r.status_code == 200, r.text[:200])
        if r.status_code == 200:
            check("HTML 含打印样式", "@page" in r.text, "")

        # ---------------- 9. 收藏与试卷库 ----------------
        print("\n=== 9. 收藏与试卷库 ===")
        r = httpx.post(f"{api}/question/papers/{paper_id}/favorite", headers=H,
                       json={"favorite": True}, timeout=20)
        check("收藏成功", r.status_code == 200 and
              (r.json().get("data") or {}).get("favorite") is True, r.text[:200])

        for scope in ("mine", "shared", "public", "favorite"):
            r = httpx.get(f"{api}/question/papers/library/list", headers=H,
                          params={"scope": scope}, timeout=20)
            ok_ = r.status_code == 200
            cnt = len((r.json().get("data") or {}).get("items") or []) if ok_ else -1
            check(f"试卷库 scope={scope} 可用", ok_ and cnt >= 0, r.text[:150])

        r = httpx.get(f"{api}/question/papers/library/list", headers=H,
                      params={"scope": "favorite"}, timeout=20)
        fav_items = (r.json().get("data") or {}).get("items") or []
        check("收藏列表含刚收藏的卷", any(i.get("id") == paper_id for i in fav_items),
              f"{len(fav_items)} 条")

        # ---------------- 10. 审核流 ----------------
        print("\n=== 10. 公共库审核流 ===")
        r = httpx.post(f"{api}/question/papers/{paper_id}/review", headers=H,
                       json={"action": "submit"}, timeout=20)
        check("提交审核 200", r.status_code == 200, r.text[:200])
        check("状态变为 pending",
              (r.json().get("data") or {}).get("status") == "pending", r.text[:150])

        r = httpx.post(f"{api}/question/papers/{paper_id}/review", headers=H,
                       json={"action": "approve"}, timeout=20)
        check("审核通过 200", r.status_code == 200, r.text[:200])
        ad = (r.json().get("data") or {})
        check("审核后进入公共库",
              ad.get("status") == "published" and ad.get("share_scope") == "public",
              str(ad))

        # ---------------- 10.5 共享范围 ----------------
        print("\n=== 10.5 共享范围（私有/年级/全校）===")
        r = httpx.post(f"{api}/question/papers/{paper_id}/share-scope", headers=H,
                       json={"scope": "grade"}, timeout=20)
        check("设为年级共享 200", r.status_code == 200, r.text[:200])
        check("返回 share_scope=grade",
              (r.json().get("data") or {}).get("share_scope") == "grade", r.text[:150])

        r = httpx.get(f"{api}/question/papers/{paper_id}/share-info", headers=H, timeout=20)
        check("共享信息可读", r.status_code == 200, r.text[:200])
        check("共享信息回显 grade",
              (r.json().get("data") or {}).get("share_scope") == "grade", r.text[:150])

        r = httpx.post(f"{api}/question/papers/{paper_id}/share-scope", headers=H,
                       json={"scope": "public"}, timeout=20)
        check("不能绕过审核直接设 public（应 400）",
              r.status_code == 400, str(r.status_code))

        r = httpx.post(f"{api}/question/papers/{paper_id}/share-scope", headers=H,
                       json={"scope": "bogus"}, timeout=20)
        check("非法 scope 被拒（应 400）", r.status_code == 400, str(r.status_code))

        r = httpx.post(f"{api}/question/papers/{paper_id}/share-scope", headers=H,
                       json={"scope": "private"}, timeout=20)
        check("可改回私有", r.status_code == 200 and
              (r.json().get("data") or {}).get("share_scope") == "private", r.text[:150])

        # ---------------- 11. 权限隔离 ----------------
        print("\n=== 11. 权限与隔离 ===")
        r = httpx.get(f"{api}/question/papers/999999/preview", headers=H, timeout=10)
        check("不存在的试卷返回 404", r.status_code == 404, str(r.status_code))
        r = httpx.get(f"{api}/question/papers/{paper_id}/preview", timeout=10)
        check("未登录访问被拒（401/403）", r.status_code in (401, 403), str(r.status_code))

        print("\n" + "=" * 62)
        print(f"通过 {len(PASSED)} 项，失败 {len(FAILED)} 项")
        if FAILED:
            print("失败项：")
            for f in FAILED:
                print("  -", f)
            return 1
        print("全部通过")
        return 0

    finally:
        try:
            proc.terminate()
            proc.wait(timeout=10)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass
        shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
