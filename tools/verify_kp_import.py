"""知识点批量导入的层级校验验证（TestClient，进程内自起 lifespan）。

## 修的是什么

`_import_row_hierarchy` 原来是 `[x for x in (单元, 章节, 知识点) if x]`：
**空列自动折叠**意味着「只填知识点、单元章节留空」会被折成 `["知识点"]`，
深度 1 —— 这个"知识点"被当成**单元**写进库里。教师以为建了考点，实际得到一棵
只有单元、没有考点的树；`created` 还正常 +1，全程静默。

现在：单元必填、同名跨层拒绝、跳级给 warning。本脚本逐一验证这些行为，
并确认 dry_run 不落库、真实导入幂等。

用法：python tools/verify_kp_import.py
退出码 0 = 全部通过。
"""
import io
import os
import sys
import tempfile

BACKEND = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend")
sys.path.insert(0, BACKEND)

DB_PATH = os.path.join(tempfile.gettempdir(), "verify_kp_import.db")
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)
os.environ.update({
    "DATABASE_URL": "sqlite:///" + DB_PATH.replace("\\", "/"),
    "LLM_ENABLED": "false",
    "CAPTCHA_ENFORCED": "false",
    "SCHEDULER_ENABLED": "false",
    "SEED_DEMO_DATA": "false",
    "APP_VERSION": "test",
    "SECRET_KEY": "kp-import-test-key-0123456789abcdef0123456789",
})

from openpyxl import Workbook  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

FAILED = []
HEADERS = ["年级", "学科", "教材版本", "学期", "单元", "章节", "知识点",
           "难度", "关键词", "说明", "编码"]
XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"  -> {detail}" if detail else ""))
    if not ok:
        FAILED.append(name)


def build_xlsx(rows):
    wb = Workbook()
    ws = wb.active
    ws.append(HEADERS)
    for row in rows:
        ws.append(row)
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf


def main() -> int:
    with TestClient(app) as c:
        api = "/api/v1"
        r = c.post(f"{api}/auth/login", json={"username": "admin", "password": "Admin@123456"})
        tok = ((r.json() or {}).get("data") or {}).get("access_token")
        if not tok:
            print("  管理员登录失败：", (r.text or "")[:200])
            return 1
        H = {"Authorization": f"Bearer {tok}"}
        # 出厂口令会被标记强制改密，改掉再重登（否则业务接口 403）
        c.put(f"{api}/auth/password", headers=H, json={
            "old_password": "Admin@123456", "new_password": "Kp@Test2026!"})
        r = c.post(f"{api}/auth/login", json={"username": "admin", "password": "Kp@Test2026!"})
        tok = ((r.json() or {}).get("data") or {}).get("access_token")
        H = {"Authorization": f"Bearer {tok}"}
        check("管理员登录（含强制改密）", bool(tok), (r.text or "")[:120])
        if not tok:
            return 1

        d = ((c.get(f"{api}/edu/grades", headers=H).json() or {}).get("data")) or []
        g = next((x for x in (d if isinstance(d, list) else d.get("items") or [])
                  if x.get("grade_num") == 7), None)
        subs = ((c.get(f"{api}/edu/subjects", headers=H,
                       params={"grade_id": g["id"]}).json() or {}).get("data")) or []
        subs = subs if isinstance(subs, list) else (subs.get("items") or [])
        s = next((x for x in subs if x["name"] == "数学"), None)
        check("取到七年级数学", bool(g and s), f"g={g and g.get('id')} s={s and s.get('id')}")
        if not g or not s:
            return 1

        def upload(rows, dry=True):
            buf = build_xlsx(rows)
            files = {"file": ("kp.xlsx", buf, XLSX_MIME)}
            data = {"dry_run": "true" if dry else "false"}
            resp = c.post(f"{api}/edu/knowledge/import", headers=H, files=files, data=data)
            try:
                body = resp.json() or {}
            except Exception:  # noqa: BLE001
                body = {}
            return resp.status_code, (body.get("data") or {})

        def kp_names(tag="校验"):
            """该学科下名字含 tag 的节点（用例名统一带「校验」前缀，便于隔离种子数据）。"""
            resp = c.get(f"{api}/edu/knowledge", headers=H,
                         params={"grade_id": g["id"], "subject_id": s["id"]})
            data = (resp.json() or {}).get("data") or {}
            rows = data if isinstance(data, list) else (data.get("items") or [])
            return [x.get("name") for x in rows if tag in str(x.get("name") or "")]

        base = [g["name"], "数学", "人教版", 1]
        tag = "校验"

        # ---------------- A. 正常三级 ----------------
        st, d = upload([base + [f"{tag}单元A", f"{tag}章节1", f"{tag}考点A", "easy", "", "", ""]])
        check("A1 三级结构预检通过",
              st == 200 and not d.get("errors") and d.get("created", 0) >= 3,
              f"{st} created={d.get('created')} errors={d.get('errors')}")
        check("A2 三级结构没有层级 warning",
              not (d.get("warnings") or []), str(d.get("warnings"))[:120])

        # ---------------- B. 缺单元（只填章节）----------------
        st, d = upload([base + ["", "孤立章节", "", "medium", "", "", ""]])
        msgs = " ".join(e.get("message", "") for e in (d.get("errors") or []))
        check("B1 只填章节（无单元）被拒", st == 200 and "缺少「单元」" in msgs, msgs[:120])

        # ---------------- C. 缺单元（只填知识点）—— 旧版会静默变成「单元」 ----------------
        st, d = upload([base + ["", "", f"{tag}孤立考点", "medium", "", "", ""]])
        msgs = " ".join(e.get("message", "") for e in (d.get("errors") or []))
        check("C1 只填知识点被拒（旧版会把它写成单元）",
              st == 200 and "缺少「单元」" in msgs, msgs[:120])

        # ---------------- D. 同名跨层 ----------------
        st, d = upload([
            base + [f"{tag}单元B", f"{tag}同名", "", "medium", "", "", ""],
            base + [f"{tag}单元B", f"{tag}同名", f"{tag}同名", "medium", "", "", ""],
        ])
        msgs = " ".join(e.get("message", "") for e in (d.get("errors") or []))
        check("D1 同名跨层被拒（避免树里出现两个同名节点）",
              st == 200 and "层级冲突" in msgs, msgs[:160])

        # ---------------- E. 跳章节 ----------------
        st, d = upload([base + [f"{tag}单元C", "", f"{tag}二级考点", "medium", "", "", ""]])
        warns = " ".join(w.get("message", "") for w in (d.get("warnings") or []))
        check("E1 跳过节给 warning（该知识点会落在二级）",
              st == 200 and "跳过了「章节」" in warns, warns[:140])

        # ---------------- F. 只到章节 ----------------
        st, d = upload([base + [f"{tag}单元D", f"{tag}章节D", "", "medium", "", "", ""]])
        warns = " ".join(w.get("message", "") for w in (d.get("warnings") or []))
        check("F1 只到章节给 warning（没有三级考点）",
              st == 200 and "只填写到「章节」" in warns, warns[:140])

        # ---------------- G. dry_run 不落库 ----------------
        names = kp_names()
        check("G1 dry_run 未写库", not names, str(names[:5]))

        # ---------------- H. 真实导入 ----------------
        st, d = upload([base + [f"{tag}单元A", f"{tag}章节1", f"{tag}考点A", "easy", "", "", ""]], dry=False)
        names = kp_names()
        check("H1 真实导入后落库",
              st == 200 and f"{tag}单元A" in names and f"{tag}考点A" in names,
              f"{st} names={names[:6]}")
        check("H2 三级节点数正确", len(names) == 3, str(len(names)))

        # ---------------- I. 幂等 ----------------
        st, d = upload([base + [f"{tag}单元A", f"{tag}章节1", f"{tag}考点A", "easy", "", "", ""]], dry=False)
        names2 = kp_names()
        check("I1 重复导入不重复建节点",
              st == 200 and len(names2) == 3 and d.get("created", 0) == 0,
              f"created={d.get('created')} updated={d.get('updated')} n={len(names2)}")

    print("\n" + "=" * 60)
    if FAILED:
        print(f"失败 {len(FAILED)} 项：")
        for f in FAILED:
            print("  -", f)
        return 1
    print("全部通过")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    finally:
        try:
            os.remove(DB_PATH)
        except OSError:
            pass
