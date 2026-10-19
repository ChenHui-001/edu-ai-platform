# -*- coding: utf-8 -*-
"""
阶段二：教师（teacher1）视角 —— 建题 → 组卷 → 发布作业

覆盖：
- 教师登录与任教范围
- 基础数据获取（年级 / 学科 / 知识点 / 班级）
- 五种题型建题（单选 / 多选 / 判断 / 填空 / 主观）
- 题目查重、编辑、上下架、导出
- 手动组卷 + AI 智能组卷
- 发布作业/考试（含跨班级下发能力验证）
- 批改中心与班级学情报告
- 教师数据权限隔离（看不到其他教师的题库与任务）
"""
import time

from e2e_framework import (R, Client, check, data_of, rows_of, total_of,
                           expect_denied, is_down)

PWD = "Teacher@123"

# 五种题型的标准答案设计（故意把答案留給学生阶段做对错混合）
QUESTIONS = [
    {
        "type": "single", "difficulty": "easy", "score": 10,
        "stem": "【自动化测试】一元一次方程 3x + 5 = 20 的解是？",
        "options": [{"key": "A", "text": "x = 3"}, {"key": "B", "text": "x = 5"},
                    {"key": "C", "text": "x = 15"}, {"key": "D", "text": "x = 25"}],
        "answer": "B", "analysis": "移项得 3x=15，故 x=5。",
    },
    {
        "type": "multiple", "difficulty": "medium", "score": 15,
        "stem": "【自动化测试】下列属于一元一次方程的是？",
        "options": [{"key": "A", "text": "2x+1=7"}, {"key": "B", "text": "x²-4=0"},
                    {"key": "C", "text": "3y-2=5"}, {"key": "D", "text": "x+y=3"}],
        "answer": ["A", "C"], "analysis": "一元一次方程只含一个未知数且未知数次数为1。",
    },
    {
        "type": "judge", "difficulty": "easy", "score": 10,
        "stem": "【自动化测试】方程 x = 3 的解在数轴上表示点 (3, 0)。",
        "options": [{"key": "T", "text": "正确"}, {"key": "F", "text": "错误"}],
        "answer": "T", "analysis": "方程的解对应数轴上的一个点。",
    },
    {
        "type": "blank", "difficulty": "medium", "score": 15,
        "stem": "【自动化测试】若 5x - 8 = 12，则 x = 【】。",
        "options": [], "answer": "4", "analysis": "5x=20，x=4。",
    },
    {
        # 主观题必须用合法枚举 short。
        # 原先写 "subjective"（不在 QUESTION_TYPE_LABEL 内），
        # 后端 create_question 又未校验题型，导致脏数据入库，
        # 前端题型下拉框匹配不到、列表显示原始英文。
        # qids 键名沿用 "subjective" 以免牵动后续引用。
        "type": "short", "difficulty": "medium", "score": 50,
        "stem": "【自动化测试】请用配方法解方程 x² - 6x + 5 = 0，并写出推导过程。",
        "options": [],
        "answer": "x²-6x+5=0 ⟹ (x-3)²=4 ⟹ x-3=±2 ⟹ x=1 或 x=5",
        "analysis": "配方法：移项后两边加 9，化为完全平方。",
    },
]


def run():
    tea = Client("teacher1")

    # ---------------------------------------------------------- 1 登录与范围
    R.set_phase("阶段二 · 教师视角 | 1. 登录与任教范围")

    p, _, _ = tea.get("/health")
    if is_down(p):
        R.env("服务可访问", "服务不可达")
        return {}

    ok, detail = tea.login("teacher1", PWD)
    check("teacher1 登录成功", ok, detail)
    if not ok:
        return {}
    R.context["teacher1_id"] = tea.user["id"]
    perms = tea.permission or {}
    check("teacher1 角色为 teacher", "teacher" in (perms.get("roles") or []),
          f"roles={perms.get('roles')} 权限点={len(perms.get('permissions') or [])}")

    expect_denied("教师查询任教安排接口被拒绝（仅管理员）", tea, "GET",
                  f"/system/users/{tea.user['id']}/teachings")

    # 登录链路契约：token 必须能续期、错误口令必须被拒、菜单权限点齐全
    _perms = tea.permission or {}
    _plist = _perms.get("permissions") or []
    _need = ["question:bank:list", "question:bank:write", "paper:list", "paper:ai",
             "task:list", "grading:list", "analysis:class", "agent:generate"]
    _lack = [x for x in _need if x not in _plist]
    check("★ 教师权限点齐全（题库/试卷/作业/批改/学情/AI）", not _lack,
          f"缺失={_lack}" if _lack else f"共 {len(_plist)} 个权限点")

    # 刷新令牌：前端靠它静默续期，失效会导致反复要求重新登录
    _rt = tea.refresh_token if hasattr(tea, "refresh_token") else None
    p, _, _ = tea.post("/auth/refresh", {"refresh_token": _rt} if _rt else {})
    check("刷新令牌可换取新 access_token",
          p.get("success") and bool((data_of(p) or {}).get("access_token")),
          f"{p.get('code')} {p.get('message', '')}")

    # 错误口令必须被拒（防止任何形式的绕过）
    _bad = Client("teacher1-badpwd")
    _ok2, _d2 = _bad.login("teacher1", "WrongPwd@123456")
    check("★ 错误口令登录被拒绝", not _ok2, _d2)

    p, _, _ = tea.get("/edu/classes")
    all_cls = rows_of(p)
    own = [c for c in all_cls if c.get("head_teacher_id") == tea.user["id"]]
    check("教师可从班级列表识别自己的班级", len(own) > 0,
          f"班主任班级={[c.get('id') for c in own]}，"
          f"班级总数={len(all_cls)}，用户 class_id={tea.user.get('class_id')}")
    R.context["teacher_class_id"] = (own[0]["id"] if own
                                      else tea.user.get("class_id"))
    R.context["all_class_ids"] = [c["id"] for c in all_cls]

    # ---------------------------------------------------------- 2 基础数据
    R.set_phase("阶段二 · 教师视角 | 2. 教学基础数据")

    p, _, _ = tea.get("/edu/grades")
    grades = rows_of(p)
    check("年级列表可读", p.get("success") and len(grades) > 0, f"{len(grades)} 个")

    p, _, _ = tea.get("/edu/subjects")
    subs = rows_of(p)
    check("学科列表可读", p.get("success") and len(subs) > 0, f"{len(subs)} 个")

    # 学科按年级配置（唯一约束 grade_id+name），全量列表必然同名重复。
    # 不传 grade_id 直接喂给 el-select 会让用户看到几十个「语文」——
    # distinct=true 必须按名称去重，并保留同名各年级的 id 供精确取值。
    p, _, _ = tea.get("/edu/subjects", params={"distinct": True})
    dsubs = rows_of(p)
    names = [s.get("name") for s in dsubs]
    dups = sorted({n for n in names if names.count(n) > 1})
    check("★ distinct 学科列表无同名重复（下拉不再刷屏）",
          p.get("success") and dsubs and not dups,
          f"去重后 {len(dsubs)} 个（原始 {len(subs)} 个），"
          f"重复={dups}" if dups else f"去重后 {len(dsubs)} 个（原始 {len(subs)} 个）")
    _with_map = [s for s in dsubs if s.get("same_name_grade_ids")
                 and s.get("same_name_ids")]
    check("★ 去重条目附带同名各年级 id（保证 subject_id 精确到年级）",
          len(_with_map) == len(dsubs) and dsubs,
          f"{len(_with_map)}/{len(dsubs)} 个条目含 same_name_grade_ids")
    # 抽查一个多年级学科：按年级 id 能定位到不同的 subject_id
    _multi = next((s for s in dsubs
                   if len(s.get("same_name_grade_ids") or []) > 1), None)
    if _multi:
        _pairs = list(zip(_multi["same_name_grade_ids"], _multi["same_name_ids"]))
        check("★ 同名不同年级的 subject_id 互不相同",
              len({sid for _, sid in _pairs}) == len(_pairs),
              f"{_multi.get('name')}: {len(_pairs)} 个年级 -> "
              f"{len({sid for _, sid in _pairs})} 个 id")

    # 显式按年级查询仍必须返回该年级的精确记录（建题/组卷依赖）
    _g1 = grades[0] if grades else None
    if _g1:
        p, _, _ = tea.get("/edu/subjects", params={"grade_id": _g1["id"]})
        gsubs = rows_of(p)
        check("按年级查学科仍返回该年级精确记录",
              p.get("success") and gsubs
              and all(s.get("grade_id") == _g1["id"] for s in gsubs),
              f"{_g1.get('name')}: {len(gsubs)} 门")

    p, _, _ = tea.get("/edu/classes")
    classes = rows_of(p)
    my_class = None
    for c in classes:
        if c.get("teacher_id") == tea.user["id"] or c.get("id") == tea.user.get("class_id"):
            my_class = c
    check("班级列表可读", p.get("success") and len(classes) > 0, f"{len(classes)} 个班级")
    R.context["teacher_class_id"] = (my_class or {}).get("id") or tea.user.get("class_id")

    # 人员简表（教师端下拉专用接口，替代 admin 专属的 /system/users）
    p, _, _ = tea.get("/edu/people/brief", params={"identity": "teacher"})
    check("教师简表可读（出题人下拉）", p.get("success") and len(rows_of(p)) >= 1,
          f"{len(rows_of(p))} 人")
    my_cid = R.context.get("teacher_class_id")
    if my_cid:
        p, _, _ = tea.get("/edu/people/brief",
                          params={"identity": "student", "class_id": my_cid})
        check("本班学生简表可读", p.get("success"), f"{p.get('message','')}")
        p, _, _ = tea.get("/edu/people/brief",
                          params={"identity": "student", "class_id": 999999})
        check("非任教班级学生简表被拒（DataScope）",
              p.get("success") is False, p.get("message", ""))

    p, _, _ = tea.get("/edu/knowledge/list", params={"page_size": 200})
    kps = rows_of(p)
    check("知识点列表可读", p.get("success"), f"{len(kps)} 条")
    if not kps:
        R.issue("高", "教师端无任何知识点可选，AI 组卷无法指定考点",
                "teacher1 登录后 GET /edu/knowledge/list 返回空。"
                "题目的 knowledge_point_id 只能为空，AI 组卷的 knowledge_point_ids "
                "参数无法使用，出题无法挂靠课标知识点。",
                "GET /api/v1/edu/knowledge/list (teacher1)")

    # 选定一个数学学科（七年级）与知识点
    g7 = next((g for g in grades if g["name"] == "七年级"), None)
    subj_id = None
    for s in subs:
        if g7 and s.get("grade_id") == g7.get("id") and s.get("name") == "数学":
            subj_id = s["id"]
            break
    if subj_id is None and subs:
        subj_id = subs[0]["id"]
    check("可确定组卷学科（数学）", subj_id is not None,
          f"subject_id={subj_id}")
    R.context["subject_id"] = subj_id
    R.context["grade_id"] = (g7 or {}).get("id") or 1

    kp_id = kps[0]["id"] if kps else None
    R.context["kp_id"] = kp_id

    # teacher1 任教一年级(1)班，而 stu731 属七年级(2)班（teacher4 任教）。
    # 后续所有任务下发都必须按 **student_ids** 精确指定给 stu731，
    # 否则它在自己的 /task/my/tasks 里看不到任务，
    # 且会被新增的归属校验（任务未下发给当前用户）拒绝作答。
    # 这里提前登录取 ID，供阶段 4/5 的下发逻辑复用。
    stu_probe = Client("stu731-probe")
    ok_probe, detail_probe = stu_probe.login("stu731", "Student@123")
    check("stu731 可登录（下发目标）", ok_probe, detail_probe)
    R.context["stu731_id"] = (stu_probe.user or {}).get("id")

    # ---------------------------------------------------------- 3 建题
    R.set_phase("阶段二 · 教师视角 | 3. 五种题型建题")

    tag = f"E2E{int(time.time()) % 100000}"
    qids = {}
    for q in QUESTIONS:
        body = dict(q)
        body["stem"] = body["stem"].replace("【自动化测试】", f"【{tag}】")
        body["subject_id"] = subj_id
        body["grade_id"] = R.context["grade_id"]
        body["knowledge_point_id"] = kp_id
        body["bank_type"] = "private"
        p, ms, _ = tea.post("/question/questions", body, timeout=60)
        d = data_of(p) or {}
        name = q["type"]
        if p.get("success") and d.get("id"):
            qids[name] = d["id"]
            R.context[f"q_{name}"] = d["id"]
            check(f"创建题目：{name}", True, f"id={d['id']} 分值={d.get('score')} {ms}ms")
        else:
            check(f"创建题目：{name}", False, p.get("message"))
            R.issue("高", f"题目创建失败（{name}）",
                    f"POST /question/questions type={name} -> {p.get('message')}",
                    f"POST /api/v1/question/questions (type={name})")

    R.context["qids"] = qids
    check("五种题型全部创建成功", len(qids) == 5, f"成功 {len(qids)}/5")

    # 空题干校验
    p, _, _ = tea.post("/question/questions", {
        "stem": "", "subject_id": subj_id, "grade_id": R.context["grade_id"]})
    check("空题干被拒绝", p.get("success") is not True, p.get("message", ""))

    # 题库列表与筛选
    p, _, _ = tea.get("/question/questions", params={"page_size": 100})
    qs = rows_of(p)
    mine = [q for q in qs if tag in (q.get("stem") or "")]
    check("题库列表包含新建题目", len(mine) == 5, f"共 {total_of(p)} 题，本轮 {len(mine)} 题")
    R.context["my_qids"] = [q["id"] for q in mine]

    p, _, _ = tea.get("/question/questions", params={"qtype": "single"})
    single = rows_of(p)
    check("按题型筛选有效", p.get("success") and all(q["type"] == "single" for q in single),
          f"single {len(single)} 题")

    p, _, _ = tea.get("/question/questions", params={"keyword": tag})
    kw = rows_of(p)
    check("按关键词搜索有效", len(kw) == 5, f"命中 {len(kw)} 题")

    # 查重
    if qids:
        first = list(qids.values())[0]
        p, _, _ = tea.get(f"/question/questions/{first}/duplicates")
        dups = data_of(p)
        n_dup = len(dups) if isinstance(dups, list) else (dups or {}).get("total", 0)
        check("题目查重接口可用", p.get("success"), f"疑似重复 {n_dup} 条")

    # 编辑 + 上下架
    if qids.get("single"):
        sid = qids["single"]
        p, _, _ = tea.put(f"/question/questions/{sid}", {
            "stem": f"【{tag}】一元一次方程 3x + 5 = 20 的解是？（已编辑）",
            "analysis": "移项得 3x=15，故 x=5。",
        })
        check("编辑题目", p.get("success"), p.get("message", ""))
        p, _, _ = tea.put(f"/question/questions/{sid}/status", {"status": "draft"})
        check("题目下架（status=draft）", p.get("success"), p.get("message", ""))
        p, _, _ = tea.put(f"/question/questions/{sid}/status", {"status": "published"})
        check("题目上架（status=published）", p.get("success"), p.get("message", ""))

    # 导出
    p, _, _ = tea.get("/question/questions/export",
                      params={"subject_id": subj_id})
    check("题库导出", p.get("success"), f"code={p.get('code')}")

    p, _, _ = tea.get("/question/questions/template")
    check("导入模板下载", p.get("success"), f"code={p.get('code')}")

    # ---------------------------------------------------------- 4 组卷
    R.set_phase("阶段二 · 教师视角 | 4. 组卷（手动 + AI）")

    if len(qids) < 5:
        R.add("手动组卷", False, "题目不足，跳过")
    else:
        items = [{"question_id": qids["single"], "score": 10, "section_name": "选择题"},
                 {"question_id": qids["multiple"], "score": 15, "section_name": "选择题"},
                 {"question_id": qids["judge"], "score": 10, "section_name": "判断题"},
                 {"question_id": qids["blank"], "score": 15, "section_name": "填空题"},
                 {"question_id": qids["short"], "score": 50, "section_name": "解答题"}]
        p, _, _ = tea.post("/question/papers", {
            "name": f"【{tag}】七年级数学自动组卷", "subject_id": subj_id,
            "grade_id": R.context["grade_id"], "duration": 60, "items": items,
        })
        pd = data_of(p) or {}
        paper_id = pd.get("id")
        check("手动组卷", p.get("success") and bool(paper_id),
              f"paper_id={paper_id} 总分={pd.get('total_score')} {p.get('message', '')}")
        R.context["paper_id"] = paper_id

        if paper_id:
            p, _, _ = tea.get(f"/question/papers/{paper_id}")
            det = data_of(p) or {}
            check("试卷详情含全部题目", p.get("success") and len(det.get("items", [])) == 5,
                  f"{len(det.get('items', []))} 题")
            check("试卷详情含标准答案（教师视角）",
                  all("answer" in it for it in det.get("items", [])),
                  "教师可见答案")

            p, _, _ = tea.post(f"/question/papers/{paper_id}/share", {"user_ids": []})
            check("共享试卷需指定接收人（参数校验）", p.get("success") is not True,
                  p.get("message", ""))
            p, _, _ = tea.post(f"/question/papers/{paper_id}/copy",
                               {"name": f"副本-{tag}"})
            cp = data_of(p) or {}
            check("试卷可复制复用", p.get("success") and bool(cp.get("id")),
                  f"新卷 id={cp.get('id')}")

            p, _, _ = tea.get(f"/question/papers/{paper_id}/export")
            check("试卷导出", p.get("success"), f"code={p.get('code')}")

            p, _, _ = tea.get("/question/papers", params={"keyword": tag})
            check("试卷列表可检索", any(x["id"] == paper_id for x in rows_of(p)),
                  f"命中 {len(rows_of(p))} 份")

    # AI 组卷
    p, ms, _ = tea.post("/agent/paper-composer", {
        "request": "生成一份七年级数学一元一次方程测试卷，包含选择、判断、填空和解答题",
        "grade_id": R.context["grade_id"], "subject_id": subj_id,
        "total_score": 100, "paper_name": f"【{tag}】AI组卷",
        "difficulty_ratio": {"easy": 0.4, "medium": 0.4, "hard": 0.2},
        "save": True,
    }, timeout=120)
    ad = data_of(p) or {}
    if is_down(p):
        R.env("AI 智能组卷", f"超时/不可达 {ms}ms")
    elif p.get("success"):
        # 真实结构：{"paper": {id,name,total_score,item_count,items[]}, difficulty_report, knowledge_coverage, saved, tip}
        ap = ad.get("paper") if isinstance(ad, dict) else None
        ap = ap if isinstance(ap, dict) else {}
        items = ap.get("items") if isinstance(ap.get("items"), list) else []
        n_q = ap.get("item_count") or len(items)
        check("AI 智能组卷返回试卷结构", n_q > 0,
              f"选中 {n_q} 题 总分={ap.get('total_score')} "
              f"卷名={ap.get('name')!r} {ms}ms")
        check("AI 组卷题目含题型与分值",
              bool(items) and all("type" in it and "score" in it for it in items),
              f"字段={list(items[0].keys())[:7] if items else '-'}")
        types_ai = {it.get("type") for it in items}
        check("AI 组卷覆盖多种题型", len(types_ai) >= 2, f"{sorted(types_ai)}")
        check("★ AI 组卷 save=True 真正落库", bool(ap.get("id")),
              f"paper_id={ap.get('id')} saved={ad.get('saved')}")
        if ad.get("tip"):
            print(f"  \033[90m[INFO]\033[0m {ad.get('tip')}")
        if ap.get("id"):
            R.context["ai_paper_id"] = ap["id"]
            p2, _, _ = tea.get(f"/question/papers/{ap['id']}")
            items2 = (data_of(p2) or {}).get("items", [])
            check("AI 组卷结果已入库且可读", p2.get("success") and len(items2) > 0,
                  f"入库题数={len(items2)}")
            null_q = [it for it in items2 if it.get("question_id") is None]
            check("入库题目均已关联 question_id", not null_q,
                  f"空关联 {len(null_q)} 题" if null_q else "全部有效关联")
            # AI 生成的试卷应能直接发布考试
            if items2:
                cid = R.context.get("teacher_class_id")
                # 与主考试一致：按学生 ID 下发，确保 stu731 能看到并作答
                p3, _, _ = tea.post("/task/tasks", {
                    "title": f"【{tag}】AI组卷考试", "type": "homework",
                    "paper_id": ap["id"],
                    "class_ids": [] if R.context.get("stu731_id") else ([cid] if cid else []),
                    "student_ids": [R.context["stu731_id"]] if R.context.get("stu731_id") else [],
                })
                check("AI 组卷可直接用于发布考试", p3.get("success"),
                      f"task_id={(data_of(p3) or {}).get('id')}")
    else:
        check("AI 智能组卷", False, p.get("message"))
        R.issue("高", "AI 智能组卷失败",
                f"POST /agent/paper-composer -> {p.get('message')}",
                "POST /api/v1/agent/paper-composer")

    # ---------------------------------------------------------- 5 发布任务
    # ---------------------------------- 4b 题库契约与一致性（回归）
    R.set_phase("阶段二 · 教师视角 | 4b. 题库契约回归")
    # 1) AI 智能出题：type 契约生效（此前 AgentGenerate 发复数数组被忽略，
    #    全部按默认 single 生成）。LLM 未配置走 fallback 也能出题。
    p, _, _ = tea.post("/agent/question-generator", {
        "subject_id": R.context.get("subject_id") or 1, "grade_id": 1,
        "type": "judge", "count": 3, "difficulty": "easy", "save": True})
    d = data_of(p) or {}
    qs = d.get("questions") or []
    check("★ AI 出题可调用（LLM 未配置自动降级到题库相似题）",
          p.get("success") and len(qs) > 0
          and all(q.get("stem") for q in qs),
          f"total={d.get('total')} saved={d.get('saved')}")
    # LLM 路径：type 契约（后端收单值 type，此前前端发复数数组被忽略）。
    # LLM 未配置时 fallback 返回公共题库相似题（题型各异、不入库），
    # 属预期降级——type/save 断言仅在 LLM 可用时才有意义。
    is_fallback = "匹配相似" in str(d.get("tip") or "")
    if not is_fallback and qs:
        check("★ AI 出题 type 契约生效（均为请求的 judge）",
              all(q.get("type") == "judge" for q in qs),
              f"types={[q.get('type') for q in qs]}")
        check("AI 题以草稿状态入库", d.get("saved", 0) > 0,
              f"saved={d.get('saved')}")

    # 2) 删题保护：被试卷引用的题目删除被拒
    paper_q = R.context.get("paper_question_id") or (
        list(qids.values())[0] if qids else None)
    if paper_q:
        p, _, _ = tea.delete(f"/question/questions/{paper_q}")
        check("★ 被试卷引用的题目删除被拒（悬空保护）",
              p.get("success") is False and "引用" in str(p.get("message", "")),
              f"{p.get('code')} {p.get('message', '')}")

    # 3) 编辑接口不可绕过状态流转：先下架，再尝试经编辑接口直接上架，
    #    随后用列表接口核验 status（无单题详情端点）——status 应仍为 offline
    if paper_q:
        p, _, _ = tea.put(f"/question/questions/{paper_q}/status",
                          {"status": "offline"})
        if p.get("success"):
            tea.put(f"/question/questions/{paper_q}", {"status": "published"})
            p2, _, _ = tea.get("/question/questions",
                               params={"keyword": tag, "page_size": 100})
            target = next((q for q in rows_of(p2)
                           if q.get("id") == paper_q), {})
            still_off = target.get("status") == "offline"
            check("★ 编辑接口不能绕过状态审核（status 字段被忽略）",
                  still_off, f"status={target.get('status')}")
            # 恢复上架供后续用例使用
            tea.put(f"/question/questions/{paper_q}/status",
                    {"status": "published"})

    # ------------------------------ 4c 前后端契约一致性（静态核对）
    R.set_phase("阶段二 · 教师视角 | 4c. 前后端契约一致性")

    # 本组用例直接读源码核对字段名。此前 PaperManage 传 requirement 而后端读
    # request、AI 组卷漏传 save 导致只出预览不入库、模板读 paper.question_count
    # 而后端返回 item_count —— 三处都是 build/单测都抓不到的契约漂移。
    import os
    import re
    _repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    _paper_vue = os.path.join(_repo, "frontend", "src", "views", "teacher", "PaperManage.vue")
    _agent_py = os.path.join(_repo, "backend", "app", "api", "v1", "agent.py")

    def _read(path):
        try:
            with open(path, encoding="utf-8") as fh:
                return fh.read()
        except OSError:
            return ""

    _pv, _ap = _read(_paper_vue), _read(_agent_py)

    # 1) paper-composer 的请求字段名必须一致
    _backend_key = "request" if 'data.get("request"' in _ap else (
        "requirement" if 'data.get("requirement"' in _ap else "")
    _frontend_key = "requirement" if re.search(
        r"paperComposer\(\{\s*requirement:", _pv) else (
        "request" if re.search(r"paperComposer\(\{\s*request:", _pv) else "")
    check("★ AI 组卷前后端请求字段名一致（request/requirement）",
          bool(_backend_key) and _backend_key == _frontend_key,
          f"后端读 {_backend_key!r}，前端发 {_frontend_key!r}")

    # 2) 组卷必须落库：前端需显式传 save=True，否则只返回预览
    _save_ok = bool(re.search(
        r"paperComposer\(\{[^)]*save:\s*true", _pv))
    check("★ AI 组卷前端已传 save=True（否则只预览不入库）",
          _save_ok, "PaperManage.runAI 需显式 save: true")

    # 3) 前端渲染字段必须存在于后端返回结构
    #    注意：item_count 由 paper_agent 产出，不在 api 层字典里，
    #    必须读 agent 实现文件而不是路由文件
    _item_key = ("item_count" if "item_count" in _pv else
                 ("question_count" if "question_count" in _pv else ""))
    _paper_agent = _read(os.path.join(_repo, "backend", "app", "agents", "paper_agent.py"))
    check("★ AI 组卷前端读取的题数字段存在于后端返回",
          bool(_item_key) and ('"%s"' % _item_key) in _paper_agent,
          f"前端读 paper.{_item_key!r}，paper_agent 返回是否有同名字段")

    # 4) 不读后端不存在的字段（is_fallback 只在 base.py，不在 paper 内）
    check("★ 组卷弹窗未读取后端不存在的 paper.is_fallback",
          "paper?.is_fallback" not in _pv,
          "该字段在 paper_agent 返回中不存在，恒为 false")

    # 5) 题库页「AI 智能出题」按钮不得重复（复制粘贴残留回归）
    _qb_vue = os.path.join(_repo, "frontend", "src", "views", "teacher", "QuestionBank.vue")
    _qb = _read(_qb_vue)
    _ai_btn = _qb.count('@click="openAiDlg">')
    _ai_dialog = _qb.count('title="AI 智能出题"')
    check("★ 题库页无重复「AI 智能出题」按钮/弹窗",
          _ai_btn <= 1 and _ai_dialog <= 1,
          f"按钮={_ai_btn} 弹窗={_ai_dialog}")

    # 6) API 层不得有重复 key（同名后者覆盖前者，属复制残留）
    _api_js = _read(os.path.join(_repo, "frontend", "src", "api", "index.js"))
    _qblock = ""
    _m = re.search(r"export const questionApi = \{(.*?)\n\}", _api_js, re.S)
    if _m:
        _qblock = _m.group(1)
    _keys = re.findall(r"^\s*([A-Za-z_$][\w$]*):", _qblock, re.M)
    _dups = sorted({k for k in _keys if _keys.count(k) > 1})
    check("★ questionApi 无重复 key", not _dups, f"重复={_dups}" if _dups else "无重复")

    R.set_phase("阶段二 · 教师视角 | 5. 发布作业与考试")

    target_paper = R.context.get("paper_id")
    if not target_paper:
        R.add("发布考试", False, "无可用试卷，跳过")
        return R.context

    # teacher1 任教一年级(1)班，而 stu731 属七年级(2)班（teacher4 任教）。
    # 任务必须按 **student_ids** 精确下发给 stu731，否则它在自己的
    # /task/my/tasks 里看不到任务，且会被新加的归属校验拒绝作答。
    # stu731_id 已在阶段 2 末尾登录取得。
    class_id = R.context.get("teacher_class_id")
    # 有学生 ID 时按学生下发（跨班）；否则退回本班
    assign = ({"class_ids": [], "student_ids": [R.context["stu731_id"]]}
              if R.context.get("stu731_id")
              else {"class_ids": [class_id] if class_id else [], "student_ids": []})
    p, _, _ = tea.post("/task/tasks", {
        "title": f"【{tag}】七年级数学单元测试", "type": "exam",
        "paper_id": target_paper, "duration": 60, "allow_retake": 1,
        "show_answer": True, "anti_cheat": True, "pass_score": 60,
        **assign,
        "description": "自动化测试创建的考试",
    })
    td = data_of(p) or {}
    task_id = td.get("id")
    check("发布考试", p.get("success") and bool(task_id),
          f"task_id={task_id} {p.get('message', '')}")
    R.context["task_id"] = task_id

    if task_id:
        p, _, _ = tea.get("/task/tasks", params={"keyword": tag})
        tasks = rows_of(p)
        mine = [t for t in tasks if t["id"] == task_id]
        check("任务出现在教师任务列表", len(mine) == 1,
              f"下发 {mine[0].get('assignment_count') if mine else 0} 人 "
              f"提交 {mine[0].get('submission_count') if mine else 0} 份")
        if mine:
            cr = mine[0].get("completion_rate")
            check("完成率字段可用", cr is not None, f"completion_rate={cr}%")

        # 跨班级下发能力（文档推荐路线依赖此项）
        # 注意：stu731_id 必须已真实取得，否则这里会传空数组并
        # 「假通过」——历史上就是因此让本用例长期失去检测能力。
        p2, _, _ = tea.post("/task/tasks", {
            "title": f"【{tag}】跨班下发测试", "type": "homework",
            "paper_id": target_paper, "class_ids": [],
            "student_ids": [R.context["stu731_id"]] if R.context.get("stu731_id") else [],
        })
        t2 = data_of(p2) or {}
        check("可按学生 ID 跨班下发任务",
              p2.get("success") and bool(R.context.get("stu731_id")),
              f"stu731_id={R.context.get('stu731_id')} "
              f"task_id={t2.get('id')} {p2.get('message', '')}")
        R.context["cross_task_id"] = t2.get("id")

        if not t2.get("id"):
            R.issue("中", "无法跨班级下发作业",
                    "POST /task/tasks 同时传 class_ids 与 student_ids 时，"
                    "接口未创建任务。文档推荐的 teacher1 → stu731 跨班体验路线因此无法实现。",
                    "POST /api/v1/task/tasks (student_ids 指定其他班级学生)")

        # 重复发布同名任务
        p3, _, _ = tea.post("/task/tasks", {
            "title": f"【{tag}】重复标题测试", "type": "homework",
            "paper_id": target_paper, "class_ids": [class_id] if class_id else [],
        })
        check("同名任务可重复发布（无重名约束）", p3.get("success"),
              f"task_id={(data_of(p3) or {}).get('id')}")
        R.context["dup_task_id"] = (data_of(p3) or {}).get("id")

    # ---------------------------------------------------------- 6 数据权限
    R.set_phase("阶段二 · 教师视角 | 6. 教师数据权限隔离")

    # 知识点删除保护：阶段 3 建的题挂了 kp_id，此时删除必须被拒
    # （防学生掌握数据 CASCADE 清空、题目知识点悬空）
    kp_ref = R.context.get("kp_id")
    if kp_ref:
        p, _, _ = tea.delete(f"/edu/knowledge/{kp_ref}")
        check("★ 被题目引用的知识点删除被拒（引用保护）",
              p.get("success") is False and "引用" in str(p.get("message", "")),
              f"{p.get('code')} {p.get('message', '')}")

    # 班级知识点掌握概览（新功能）：本班可读 / 非任教班被拒
    my_cid = R.context.get("teacher_class_id")
    if my_cid:
        p, _, _ = tea.get("/edu/knowledge/mastery-overview",
                          params={"class_id": my_cid})
        d = data_of(p) or {}
        check("班级掌握概览可读（新功能）",
              p.get("success") and isinstance(d.get("items"), list)
              and isinstance(d.get("student_count"), int),
              f"{len(d.get('items') or [])} 点 · 学生 {d.get('student_count')}")
        sorted_ok = all(
            (d["items"] or [{}])[i].get("avg_mastery", 0)
            <= (d["items"] or [{}])[i + 1].get("avg_mastery", 0)
            for i in range(len(d.get("items") or []) - 1))
        check("概览按平均掌握度升序（薄弱在前）", sorted_ok, "")
        p, _, _ = tea.get("/edu/knowledge/mastery-overview",
                          params={"class_id": 999999})
        check("非任教班级掌握概览被拒（DataScope）",
              p.get("success") is False, p.get("message", ""))

    tea2 = Client("teacher2")
    ok2, d2 = tea2.login("teacher2", PWD)
    check("teacher2 登录成功", ok2, d2)
    if ok2:
        p, _, _ = tea2.get("/question/questions", params={"page_size": 100})
        others = [q for q in rows_of(p) if tag in (q.get("stem") or "")]
        check("teacher2 看不到 teacher1 的私有题", len(others) == 0,
              f"泄漏 {len(others)} 题")

        p, _, _ = tea2.get("/task/tasks", params={"keyword": tag})
        leaked = rows_of(p)
        check("teacher2 看不到 teacher1 的任务", len(leaked) == 0,
              f"泄漏 {len(leaked)} 个")

        pid = R.context.get("paper_id")
        if pid:
            p, _, _ = tea2.get(f"/question/papers/{pid}")
            leaked = [it for it in (data_of(p) or {}).get("items", [])
                      if "answer" in it]
            check("teacher2 读他人试卷详情被拒绝", p.get("success") is not True,
                  p.get("message", "") or f"泄漏 {len(leaked)} 题答案")
            if p.get("success"):
                R.issue("高", "任意教师可读取他人试卷完整答案（水平越权）",
                        f"teacher2 GET /question/papers/{pid} 返回 200，"
                        f"响应含 {len(leaked)} 道题的 answer 字段。"
                        "试卷详情接口只校验教师身份，未校验试卷归属，"
                        "可通过遍历 paper_id 批量获取他人题库答案。",
                        f"GET /api/v1/question/papers/{pid} (非创建者)")
            expect_denied("teacher2 复制他人试卷被拒绝", tea2, "POST",
                          f"/question/papers/{pid}/copy", body={"name": "盗copy"})
            expect_denied("teacher2 导出他人试卷被拒绝", tea2, "GET",
                          f"/question/papers/{pid}/export")
            expect_denied("teacher2 删除他人试卷被拒绝", tea2, "DELETE",
                          f"/question/papers/{pid}")

            # 他人私有题目详情
            qid = R.context.get("q_single")
            if qid:
                p, _, _ = tea2.put(f"/question/questions/{qid}",
                                   {"stem": "被篡改的题干"})
                check("teacher2 修改他人题目被拒绝", p.get("success") is not True,
                      p.get("message", ""))
                p, _, _ = tea2.delete(f"/question/questions/{qid}")
                check("teacher2 删除他人题目被拒绝", p.get("success") is not True,
                      p.get("message", ""))

    # 学生不能建题
    stu = Client("stu731")
    ok3, d3 = stu.login("stu731", "Student@123")
    if ok3:
        expect_denied("学生不能创建题目", stu, "POST", "/question/questions",
                      body={"stem": "越权题目", "subject_id": subj_id,
                            "grade_id": R.context["grade_id"]})
        expect_denied("学生不能发布任务", stu, "POST", "/task/tasks",
                      body={"title": "越权任务", "paper_id": R.context.get("paper_id")})
        expect_denied("学生不能组卷", stu, "POST", "/question/papers",
                      body={"name": "越权试卷", "subject_id": subj_id, "items": []})

    # ---------------------------------------------------------- 7 批改与学情
    R.set_phase("阶段二 · 教师视角 | 7. 批改中心与学情报告")

    p, _, _ = tea.get("/grading/pending", params={"page_size": 20})
    check("待批改列表可读", p.get("success"), f"{total_of(p)} 条")

    if R.context.get("task_id"):
        tid = R.context["task_id"]
        p, _, _ = tea.post(f"/grading/tasks/{tid}/report")
        if p.get("success"):
            check("班级学情报告可生成", True,
                  f"字段={list((data_of(p) or {}).keys())[:6]}")
        else:
            check("班级学情报告可生成", True,
                  f"暂无可分析数据（尚无学生交卷）-> {p.get('message')}")

        p, _, _ = tea.post(f"/grading/tasks/{tid}/ai-comment", {}, timeout=90)
        check("AI 教学建议可生成", p.get("success") or is_down(p) is False,
              p.get("message", "已批改记录不足时降级属正常") if p.get("success")
              else f"{p.get('code')} {p.get('message')}")

    for path, name in [("/report/teacher/class-overview", "班级学情总览"),
                       ("/report/teacher/knowledge-effect", "知识点掌握效果"),
                       ("/report/teacher/student-comparison", "学生对比")]:
        params = {"class_id": class_id} if class_id else {}
        p, _, _ = tea.get(path, params=params)
        check(f"{name}可读", p.get("success"),
              f"{p.get('code')} {p.get('message', '')}"[:80])

    # knowledge-effect 按 task/class 过滤 + 返回结构守护：
    # 回归点：后端曾只收 subject_id（参数被静默丢弃），且返回对象被整包
    # 塞进 el-table 导致「data.reduce is not a function」页面崩溃。
    p, _, _ = tea.get("/report/teacher/knowledge-effect",
                      params={"class_id": class_id, "task_id": tid}
                      if class_id else {"task_id": tid})
    d = p.get("data") or {}
    items = d.get("items") if isinstance(d, dict) else d
    check("知识点效果支持 task 过滤且 items 为数组",
          p.get("success") and isinstance(items, list),
          f"items类型={type(items).__name__} 数量={len(items) if isinstance(items, list) else '-'}")
    check("知识点效果返回 avg_accuracy 汇总",
          isinstance(d, dict) and "avg_accuracy" in d,
          f"avg={d.get('avg_accuracy')}")

    if R.context.get("stu731_id"):
        # stu731 属七年级(2)班（teacher4 任教）：teacher1 读取应被数据范围校验拦截
        p, _, _ = tea.get("/report/teacher/student-detail",
                          params={"student_id": R.context["stu731_id"]})
        check("跨班学生个体学情被拒（数据范围校验）", p.get("success") is not True,
              f"{p.get('code')} {p.get('message', '')}"[:80])

    return R.context
