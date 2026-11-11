"""QA 审计单元套件（对应 audit-reports/qa/TEST_CASES.csv 关键用例）。

覆盖：JSON 解析、难度归一化、题量拆分、长任务超时判据、JWT 吊销 fail-closed、
知识点种子完整性，以及用**内存 SQLite** 直接验证 BUG-001(usage_count 对称递减)
与 BUG-009(并发落库 id 回填) 的修复。

运行：cd backend && python -m pytest qa_audit_suite.py -q
"""
from datetime import datetime, timedelta

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.agents.llm import extract_json
from app.core.security import create_access_token, decode_token
from app.services.agent_job_state import effective_status, is_timed_out
from app.services.init_db import KNOWLEDGE_POINTS
from app.services.paper_compose_service import normalize_difficulty, split_by_difficulty


# ===================== LLM / JSON 解析 =====================
def test_extract_json_truncated_array_returns_none():
    """残缺 JSON 数组必须返回 None，不能被伪装成成功。"""
    content = '[{"type":"single","stem":"题干未闭合"'
    assert extract_json(content) is None


def test_extract_json_trailing_comma():
    assert extract_json('{"a":1,}') == {"a": 1}


def test_extract_json_strip_fence_and_text():
    content = "说明文字\n```json\n[{\"x\":1}]\n```"
    assert extract_json(content) == [{"x": 1}]


def test_extract_json_unbalanced_returns_none():
    # 外层 { 未闭合、内部无任何完整片段 → None
    assert extract_json('前文 {"a":') is None


# ===================== 难度归一化 / 题量拆分 =====================
def test_normalize_default():
    assert normalize_difficulty(None) == {"easy": 70, "medium": 20, "hard": 10}


def test_normalize_scale_to_100():
    r = normalize_difficulty({"easy": 3, "medium": 5, "hard": 2})
    assert sum(r.values()) == 100
    assert r == {"easy": 30, "medium": 50, "hard": 20}


@pytest.mark.parametrize("raw", [
    {"easy": 33.34, "medium": 33.33, "hard": 33.33},
    {"easy": 33.33, "medium": 33.33, "hard": 33.34},
    {"easy": 50.5, "medium": 25.25, "hard": 24.25},
])
def test_normalize_decimal_sum_is_100(raw):
    """BUG-014 修复验证：小数占比四舍五入后三档之和必须精确 100。"""
    result = normalize_difficulty(raw)
    assert sum(result.values()) == 100
    assert all(v >= 0 for v in result.values())


def test_split_by_difficulty_remainer_to_max():
    r = split_by_difficulty(23, {"easy": 70, "medium": 20, "hard": 10})
    assert sum(r.values()) == 23
    assert r["easy"] >= r["medium"] >= r["hard"]


# ===================== 长任务超时判据 =====================
def test_is_timed_out_strict_greater_than():
    base = datetime(2026, 1, 1, 0, 0, 0)
    # 恰好 T 秒：未超时（边界严格 > 非 >=）
    assert is_timed_out("running", base - timedelta(seconds=300), now=base) is False
    # T+1 微秒：超时
    assert is_timed_out("running", base - timedelta(seconds=300, microseconds=1), now=base) is True


def test_is_timed_out_none_created_at():
    assert is_timed_out("running", None) is False


def test_is_timed_out_non_running():
    assert is_timed_out("success", datetime(2026, 1, 1)) is False


def test_effective_status_now_injection():
    """BUG-018 修复验证：effective_status 现在可注入 now，边界确定性可测。"""
    base = datetime(2026, 1, 1, 0, 0, 0)
    assert effective_status("running", base - timedelta(seconds=301), now=base) == "failed"
    assert effective_status("running", base - timedelta(seconds=299), now=base) == "running"


# ===================== 认证 / JWT 吊销 =====================
class _FakeDB:
    """最小假 DB：scalar 返回预设的吊销 jti（None 表示未吊销）。"""

    def __init__(self, revoked_jti=None):
        self._revoked = revoked_jti

    def scalar(self, *args, **kwargs):
        return self._revoked


def test_decode_token_fail_closed_without_db():
    """BUG-006 修复验证：未传 db 时默认 fail-closed（不再静默跳过吊销）。"""
    tok = create_access_token(1, role="student")
    assert decode_token(tok) is None
    # 登出等场景显式关闭吊销校验才允许解析
    assert decode_token(tok, check_revocation=False) is not None


def test_decode_token_revocation_with_db():
    tok = create_access_token(1, role="student")
    assert decode_token(tok, _FakeDB(revoked_jti="some-jti")) is None
    assert decode_token(tok, _FakeDB(revoked_jti=None)) is not None


# ===================== 知识点种子完整性 =====================
def test_grade7_has_no_physics():
    """BUG-015 修复验证：七年级无物理（国家课程），八年级/九年级有。"""
    assert "物理" not in KNOWLEDGE_POINTS[7]
    assert "物理" in KNOWLEDGE_POINTS[8]
    assert "物理" in KNOWLEDGE_POINTS[9]


# ===================== 内存 DB：BUG-001 / BUG-009 =====================
@pytest.fixture()
def db_session():
    import app.models  # noqa: F401 确保所有表注册到 Base.metadata

    from app.core.database import Base

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, expire_on_commit=False)()
    try:
        yield session
    finally:
        session.close()


def _seed_basic(session):
    from app.models import Grade, Subject, User

    grade = Grade(name="审计测试年级", stage="junior", grade_num=7)
    session.add(grade)
    session.flush()
    subject = Subject(name="数学", grade_id=grade.id)
    session.add(subject)
    session.flush()
    user = User(username="audit_t1", password="x", real_name="审计教师")
    session.add(user)
    session.flush()
    return grade, subject, user


def _mk_question(session, grade, subject, user, stem, usage=0):
    from app.models import Question

    q = Question(stem=stem, grade_id=grade.id, subject_id=subject.id,
                 owner_id=user.id, usage_count=usage)
    session.add(q)
    session.flush()
    return q


def test_write_items_symmetric_usage_count(db_session):
    """BUG-001 修复验证：改卷后 usage_count 等于当前真实引用数。

    b8e3093 起改用 `services/question_usage.recount_usage` 幂等重算，
    语义从「按 +1/-1 记账」变成「重算真实引用数」。旧断言仍期望
    5/4/1（在 5/5/0 初值上做加减），实现正确却被判红——正是
    「测试没接 CI → 断言腐烂无人发现」的实证。
    """
    from app.api.v1.paper_compose import _write_items
    from app.models import Paper, PaperItem

    s = db_session
    g, subj, u = _seed_basic(s)
    q1 = _mk_question(s, g, subj, u, "q1", usage=5)
    q2 = _mk_question(s, g, subj, u, "q2", usage=5)
    q3 = _mk_question(s, g, subj, u, "q3", usage=0)

    paper = Paper(name="审计卷", grade_id=g.id, subject_id=subj.id, creator_id=u.id)
    s.add(paper)
    s.flush()
    s.add_all([
        PaperItem(paper_id=paper.id, question_id=q1.id, sort_order=1, score=5),
        PaperItem(paper_id=paper.id, question_id=q2.id, sort_order=2, score=5),
    ])
    s.flush()

    items = [
        {"question_id": q1.id, "score": 5, "section_name": "一、单选题",
         "section_code": "single", "section_sort": 1},
        {"question_id": q3.id, "score": 5, "section_name": "一、单选题",
         "section_code": "single", "section_sort": 1},
    ]
    _write_items(s, paper, items)
    s.flush()

    assert q1.usage_count == 1  # 保留：真实引用 1
    assert q2.usage_count == 0  # 移除：真实引用 0（不是初值 5-1）
    assert q3.usage_count == 1  # 新增：真实引用 1


def test_id_backfill_old_vs_new_under_concurrency(db_session):
    """BUG-009 修复验证：旧「按 id 倒序回填」在并发下错配；改用对象自身 id 才正确。"""
    from app.models import Question

    s = db_session
    g, subj, u = _seed_basic(s)

    # 批次 A 提交
    batch_a = [_mk_question(s, g, subj, u, f"A{i}") for i in range(2)]
    s.commit()
    ids_a = [q.id for q in batch_a]

    # 批次 B 在 A 之后提交（模拟：A 提交后、A 回填前，B 已插入更高的 id）
    batch_b = [_mk_question(s, g, subj, u, f"B{i}") for i in range(2)]
    s.commit()
    ids_b = [q.id for q in batch_b]

    # 旧实现：按 id 倒序取最近 2 条 → 拿到的是 B，若用于回填 A 即错配
    recent = list(s.scalars(
        select(Question.id).order_by(Question.id.desc()).limit(len(ids_a))
    ).all())
    assert set(recent) == set(ids_b)
    assert set(recent).isdisjoint(set(ids_a))

    # 新实现：用本批对象自身 id → 恰好是 A 的题目
    stems = {q.id: q.stem for q in s.scalars(
        select(Question).where(Question.id.in_(ids_a))
    ).all()}
    assert all(stems[i].startswith("A") for i in ids_a)


# ===================== 版本信息（版本号 / 构建号 / 最后更新时间） =====================
def _snapshot(db):
    from app.models import SysConfig

    return db.scalar(select(SysConfig).where(SysConfig.key == "sys_version_snapshot"))


def test_version_first_boot_records_timestamp(db_session):
    """首次启动（快照表为空）必须落一条快照，且带合法的更新时间。"""
    from app.services import version_info as vi

    res = vi.record_version_update(db_session)
    assert res["changed"] is True
    assert len(res["updated_at"]) == 19, res["updated_at"]

    row = _snapshot(db_session)
    assert row is not None
    assert row.value_type == "json"
    # 版本信息不含敏感内容，需允许非管理员读取
    assert row.is_public is True


def test_version_same_version_keeps_timestamp(db_session, monkeypatch):
    """同版本重启不能刷新时间戳（否则页面上「最后更新」= 上次重启时间）。"""
    from app.services import version_info as vi

    fixed = {"version": "2.2.0", "commit": "abc1234", "built_at": "2026-10-28 08:00:00"}
    monkeypatch.setattr(vi, "_identity", lambda: fixed)

    first = vi.record_version_update(db_session)
    second = vi.record_version_update(db_session)
    assert first["changed"] is True
    assert second["changed"] is False
    assert second["updated_at"] == first["updated_at"]


def test_version_bump_records_new_timestamp_and_prior(db_session, monkeypatch):
    """版本号变化 → 写入新时间戳，并记住上一版版本号。"""
    from app.services import version_info as vi

    monkeypatch.setattr(vi, "_identity", lambda: {
        "version": "2.2.0", "commit": "abc1234", "built_at": "2026-10-28 08:00:00"})
    first = vi.record_version_update(db_session)

    monkeypatch.setattr(vi, "_identity", lambda: {
        "version": "2.2.1", "commit": "def5678", "built_at": "2026-10-29 10:00:00"})
    second = vi.record_version_update(db_session)

    assert second["changed"] is True
    assert second["prior_version"] == "2.2.0"
    assert second["updated_at"] >= first["updated_at"]
    assert vi.version_payload(db_session)["prior_version"] == "2.2.0"


def test_version_build_only_change_is_recorded(db_session, monkeypatch):
    """版本号不变、只换镜像（回滚 / hotfix 重建）也算更新。"""
    from app.services import version_info as vi

    monkeypatch.setattr(vi, "_identity", lambda: {
        "version": "2.2.0", "commit": "aaa1111", "built_at": ""})
    vi.record_version_update(db_session)

    monkeypatch.setattr(vi, "_identity", lambda: {
        "version": "2.2.0", "commit": "bbb2222", "built_at": ""})
    assert vi.record_version_update(db_session)["changed"] is True


def test_version_payload_source_fallbacks(db_session, monkeypatch):
    """快照缺失时的回落顺序：构建时间 → 进程启动时间，且取值必须稳定。"""
    from app.services import version_info as vi

    # 有构建时间 → build
    monkeypatch.setattr(vi, "_identity", lambda: {
        "version": "1.0.0", "commit": "abcdef1234567", "built_at": "2026-10-27 09:30:00"})
    payload = vi.version_payload(db_session)
    assert payload["updated_source"] == "build"
    assert payload["updated_at"] == "2026-10-27 09:30:00"
    assert payload["build_number"] == "abcdef1"

    # 无构建时间 → startup，且两次调用必须一致（不能用 now_local()）
    monkeypatch.setattr(vi, "_identity", lambda: {
        "version": "dev", "commit": "", "built_at": ""})
    a = vi.version_payload(db_session)
    b = vi.version_payload(db_session)
    assert a["updated_source"] == "startup"
    assert a["updated_at"] == b["updated_at"]


def test_version_build_time_normalized():
    """CI 传入的构建时间必须归一化后再展示。

    **CI 实测传的是纪元秒**（`github.event.repository.pushed_at` 渲染成
    `1793266152`）：2.2.1 上线后页面上「构建时间」直接显示了这串数字，
    因为旧实现只认 ISO 串、原样透传。三种形态都要覆盖。
    """
    from app.services.version_info import _fmt_time

    assert _fmt_time("2026-10-29T09:12:34Z") == "2026-10-29 09:12:34"
    assert _fmt_time("2026-10-29T09:12:34.123456+00:00") == "2026-10-29 09:12:34"
    assert _fmt_time("2026-10-29 09:12:34 -05:00") == "2026-10-29 09:12:34"
    # 纪元秒 / 毫秒（毫秒 = 同秒的 1000 倍，两者结果必须一致）
    epoch = _fmt_time("1793266152")
    assert len(epoch) == 19 and epoch[4] == "-", epoch
    assert _fmt_time("1793266152000") == epoch
    # 非法/未知值一律空串，由调用方显示占位
    assert _fmt_time("unknown") == ""
    assert _fmt_time(None) == ""


def test_version_endpoint_body(db_session):
    """直接调用路由本体：不依赖鉴权链也能返回完整字段（公开接口）。"""
    from app.api.v1.system import get_version_info

    resp = get_version_info(db=db_session)
    data = resp["data"]
    for key in ("app_name", "version", "build_number", "commit", "built_at",
                "updated_at", "updated_source", "prior_version", "from_image"):
        assert key in data, f"缺少字段 {key}"
    assert isinstance(data["from_image"], bool)


# ===================== 系统配置页契约（前后端字段名对齐） =====================
def test_system_config_matches_frontend_bindings(db_session, monkeypatch):
    """页面读的每个 `config.*` 键都必须在 `/system/config` 的返回里存在。

    这条用例的由来：`SystemSetting.vue` 曾按大写键（APP_NAME/APP_VERSION…）
    渲染，而接口返回小写键，两边都没报错，只是整页字段**静默显示为空**。
    静态代码看不出问题，只有把模板里的绑定名与实际响应逐一对齐才能发现。
    """
    import os
    import re

    from app.agents import llm as llm_mod

    # 隔离真实库：_get_db_value 会另开 SessionLocal 读 sys_config
    monkeypatch.setattr(llm_mod, "_get_db_value", lambda key, vtype, default=None: default)
    monkeypatch.setattr(llm_mod, "is_available", lambda: False)

    from app.api.v1.system import get_config

    data = get_config(db=db_session, _=None)["data"]

    vue_path = os.path.join(
        os.path.dirname(__file__), "..", "frontend", "src", "views", "admin", "SystemSetting.vue"
    )
    if not os.path.exists(vue_path):
        pytest.skip("前端源码不在当前检出中")
    with open(vue_path, encoding="utf-8") as fp:
        source = fp.read()

    # 只扫模板段：script 里的 `config.value` 是 ref 取值，不是接口字段。
    # 必须用 rsplit 取**最后**一个 </template>：模板里还有 <template #header>
    # 这类插槽，按第一个闭合标签切会把主体整段截掉（实测误报"没解析到绑定"）。
    #
    # 正则**必须含大写**：本用例要抓的正是「模板写 config.APP_NAME、接口回
    # app_name」这种大小写漂移，只匹配 `[a-z_]+` 会把要抓的 bug 自己过滤掉，
    # 变成永远绿的假探针（已用旧版反向验证过）。
    template = source.split("<template>", 1)[-1].rsplit("</template>", 1)[0]
    bound = set(re.findall(r"config\.([A-Za-z_][A-Za-z0-9_]*)", template)) - {"value"}
    assert bound, "未从模板中解析到任何 config.* 绑定，正则或模板可能已变"
    missing = bound - set(data)
    assert not missing, f"前端绑定了接口未返回的字段：{sorted(missing)}"


def test_mask_dsn_hides_password_keeps_target():
    """连接串脱敏：抹掉密码，保留协议/账号/主机/库名（否则看不出连的哪个库）。"""
    from app.api.v1.system import _mask_dsn

    masked = _mask_dsn("postgresql+psycopg://edu:Secret123@10.0.0.5:5432/edu_db")
    assert "Secret123" not in masked
    assert masked == "postgresql+psycopg://edu:****@10.0.0.5:5432/edu_db"
    # 无密码的 sqlite 原样返回
    assert _mask_dsn("sqlite:///./data/app.db") == "sqlite:///./data/app.db"


def test_system_config_hides_internal_markers(db_session):
    """category=system 的内部标记不许出现在「可编辑配置项」里。

    `question_bank_v2_migrated` 这类标志位被改回 0，下次启动就会当成「首次迁移」
    清空题库；把它展示成一个可编辑项，等于把数据丢失按钮摆到管理员面前。
    """
    from app.models import SysConfig
    from app.api.v1.system import get_config

    db_session.add_all([
        SysConfig(key="question_bank_v2_migrated", value="1", category="system", is_public=False),
        SysConfig(key="llm_model", value="deepseek-chat", category="ai", is_public=True),
    ])
    db_session.commit()

    keys = [x["key"] for x in get_config(db=db_session, _=None)["data"]["editable"]]
    assert "question_bank_v2_migrated" not in keys
    assert "llm_model" in keys


def test_update_config_rejects_system_marker(db_session):
    """PUT /system/config 不能改系统内部标记（否则可把题库迁移标志位改回 0）。"""
    from app.api.v1.system import ConfigUpdateIn, update_config
    from app.core.exception import BusinessException
    from app.models import SysConfig

    db_session.add(SysConfig(key="question_bank_v2_migrated", value="1",
                             category="system", is_public=False))
    db_session.commit()

    class _Admin:
        id = 1

    with pytest.raises(BusinessException):
        update_config(
            payload=ConfigUpdateIn(key="question_bank_v2_migrated", value="0", category="system"),
            db=db_session, admin=_Admin(),
        )
    # 值必须保持原样
    from sqlalchemy import select as _select

    row = db_session.scalar(_select(SysConfig).where(SysConfig.key == "question_bank_v2_migrated"))
    assert row.value == "1"


# ===================== 题库 V2：批量新增（B9 批量保存） =====================
def _call_batch_create(session, user, items):
    """直接调路由函数绕过 Depends，并屏蔽 chroma 向量化副作用。"""
    from app.api.v1 import question as qmod
    from app.schemas.question import QuestionBatchCreateIn

    indexed = []
    original = qmod.index_question
    qmod.index_question = lambda q: indexed.append(q.id)
    try:
        res = qmod.batch_create_questions(
            data=QuestionBatchCreateIn(items=items), db=session, user=user)
    finally:
        qmod.index_question = original
    return res, indexed


def test_batch_create_partial_success_and_in_batch_dedup(db_session):
    """B9：批量新增逐条校验，非法项进 skipped（带 1 起 index），合法项一次提交。

    同一批里题干只差空白的重复题必须去重 —— AI 出题一轮常给出近似重复题，
    重复入库会污染「少用优先」排序。
    """
    from app.models import Question

    s = db_session
    g, subj, u = _seed_basic(s)
    res, indexed = _call_batch_create(s, u, [
        {"stem": "1+1=?", "grade_id": g.id, "subject_id": subj.id, "type": "single"},
        {"stem": "   ", "grade_id": g.id, "subject_id": subj.id},
        {"stem": "1 + 1 = ?", "grade_id": g.id, "subject_id": subj.id},
        {"stem": "2+2=?", "grade_id": g.id, "subject_id": subj.id},
    ])

    body = res["data"]
    assert len(body["done"]) == 2
    reasons = {item["index"]: item["reason"] for item in body["skipped"]}
    assert reasons[2] == "题干不能为空"
    assert "重复" in reasons[3]

    rows = s.scalars(select(Question).where(Question.owner_id == u.id)).all()
    assert len(rows) == 2
    # 向量化只对真正落库的题执行，且用对象自身 id（不回查、不串号）
    assert sorted(indexed) == sorted(r.id for r in rows)


def test_batch_create_public_question_waits_for_audit(db_session):
    """批量入口必须复用单题审核口径：非审核角色建公共题一律落 draft。"""
    from app.models import Question

    s = db_session
    g, subj, u = _seed_basic(s)
    res, _ = _call_batch_create(s, u, [
        {"stem": "公共题上架尝试", "grade_id": g.id, "subject_id": subj.id,
         "bank_type": "public", "status": "published"},
    ])
    assert len(res["data"]["done"]) == 1
    q = s.get(Question, res["data"]["done"][0])
    assert q.bank_type == "public"
    assert q.status == "draft"


def test_batch_create_grade_subject_mismatch_is_skipped(db_session):
    """学科与年级不匹配是「该条不合法」，不能整批 500/400。"""
    from app.models import Grade, Subject

    s = db_session
    g, subj, u = _seed_basic(s)
    other = Grade(name="审计测试年级2", stage="junior", grade_num=8)
    s.add(other)
    s.flush()
    other_subj = Subject(name="物理", grade_id=other.id)
    s.add(other_subj)
    s.flush()

    res, _ = _call_batch_create(s, u, [
        {"stem": "合法题", "grade_id": g.id, "subject_id": subj.id},
        {"stem": "跨年级题", "grade_id": g.id, "subject_id": other_subj.id},
    ])
    body = res["data"]
    assert len(body["done"]) == 1
    assert body["skipped"][0]["index"] == 2
    assert "不匹配" in body["skipped"][0]["reason"]


def test_batch_create_rejects_empty_and_oversized(db_session):
    from pydantic import ValidationError

    from app.api.v1 import question as qmod
    from app.core.exception import BusinessException
    from app.schemas.question import QuestionBatchCreateIn

    s = db_session
    g, subj, u = _seed_basic(s)
    with pytest.raises(BusinessException):
        qmod.batch_create_questions(data=QuestionBatchCreateIn(items=[]), db=s, user=u)
    # 非数组由 Pydantic 在 422 阶段挡住，路由层无需重复判断
    with pytest.raises(ValidationError):
        QuestionBatchCreateIn(items="not-a-list")
    with pytest.raises(BusinessException):
        qmod.batch_create_questions(
            data=QuestionBatchCreateIn(items=[
                {"stem": "x", "grade_id": g.id, "subject_id": subj.id}
            ] * (qmod.BATCH_CREATE_LIMIT + 1)),
            db=s, user=u,
        )


# ===================== 选项契约（reaudit3 P1-C） =====================
# 第三轮复审的核心事故：演示数据把 options 写成 `["A. 7", "B. 8"]`，
# 而全站契约是 `[{"key","text"}]` —— 试卷 Excel 导出与错题导出直接 500，
# 学生答题页渲染成 `undefined. undefined`。现在写入/读取共用一个归一化函数，
# 这组用例就是那个函数的行为基线。
def test_normalize_options_standard_shape_passthrough():
    from app.utils.options import normalize_options

    raw = [{"key": "A", "text": "7"}, {"key": "B", "text": "8"}]
    assert normalize_options(raw) == raw


def test_normalize_options_legacy_string_list():
    """旧导入模板 / 演示数据的 `["A. 7", "B. 8"]` 必须被救回来。"""
    from app.utils.options import normalize_options

    assert normalize_options(["A. 7", "B. 8"]) == [
        {"key": "A", "text": "7"}, {"key": "B", "text": "8"}]


def test_normalize_options_chinese_separators():
    from app.utils.options import normalize_options

    assert normalize_options(["A．甲", "B、乙", "C）丙"]) == [
        {"key": "A", "text": "甲"}, {"key": "B", "text": "乙"},
        {"key": "C", "text": "丙"}]


def test_normalize_options_unprefixed_gets_sequential_key():
    from app.utils.options import normalize_options

    assert normalize_options(["甲", "乙"]) == [
        {"key": "A", "text": "甲"}, {"key": "B", "text": "乙"}]


def test_normalize_options_json_text():
    """库里存的是 JSON 文本，读取侧必须先 unjson 再归一化。"""
    import json as _json

    from app.utils.options import normalize_options

    assert normalize_options(_json.dumps(["A. 1"])) == [{"key": "A", "text": "1"}]


def test_normalize_options_mapping_shape():
    from app.utils.options import normalize_options

    assert normalize_options({"A": "7", "B": "8"}) == [
        {"key": "A", "text": "7"}, {"key": "B", "text": "8"}]


def test_normalize_options_never_raises_on_garbage():
    """展示链路不能因为一条脏数据整页崩：任何输入都返回列表。"""
    from app.utils.options import normalize_options

    for bad in (None, "", "{不是 JSON", 42, object(), [None, 3], {"k": None}):
        assert isinstance(normalize_options(bad), list)


def test_options_match_key_accepts_both_shapes():
    """判分前用它兜脏数据：标准形状与旧字符串数组都要认出同一个 key。"""
    from app.utils.options import options_match_key

    assert options_match_key([{"key": "A", "text": "7"}], "a") is True
    assert options_match_key(["A. 7", "B. 8"], "B") is True
    assert options_match_key(["A. 7"], "C") is False
    assert options_match_key(None, "A") is False


# ===================== 限流：键摘要 + 表有界（reaudit3 P1-B） =====================
def test_key_digest_hides_raw_key():
    """限流键落库前必须哈希：裸邮箱等于在库里存一份任意人可写的 PII。"""
    from app.services.rate_limit import key_digest

    d = key_digest("reset", "Someone@Example.com")
    assert "someone" not in d.lower()
    assert "@" not in d
    # 归一化：大小写与首尾空格不影响同一个名额
    assert d == key_digest("reset", "  someone@example.com  ")


def test_key_digest_prefix_isolated():
    from app.services.rate_limit import key_digest

    assert key_digest("reset", "x").split(":")[0] == "reset"
    assert key_digest("reset", "x") != key_digest("pubupload", "x")


def test_purge_expired_removes_only_expired(db_session):
    from datetime import timedelta

    from app.models.security_cache import RateLimit
    from app.services.rate_limit import purge_expired_and_cap
    from app.utils.common import now_local

    now = now_local()
    db_session.add_all([
        RateLimit(key="k:old", hits=1,
                  window_start=(now - timedelta(hours=2)).timestamp(),
                  expire_at=now - timedelta(hours=1)),
        RateLimit(key="k:live", hits=1, window_start=now.timestamp(),
                  expire_at=now + timedelta(hours=1)),
    ])
    db_session.commit()
    removed = purge_expired_and_cap(db_session)
    assert removed == 1
    assert db_session.scalar(select(RateLimit).where(RateLimit.key == "k:live")) is not None


def test_purge_caps_keyspace(db_session, monkeypatch):
    """键由攻击者控制 → 表必须自己有上界，否则 25 个 target 就是 25 行。"""
    from datetime import timedelta

    from app.models.security_cache import RateLimit
    from app.services import rate_limit as rl
    from app.utils.common import now_local

    monkeypatch.setattr(rl, "KEY_SOFT_CAP", 10)
    now = now_local()
    db_session.add_all([
        RateLimit(key=f"k:{i}", hits=1, window_start=now.timestamp(),
                  expire_at=now + timedelta(minutes=i + 1))
        for i in range(30)
    ])
    db_session.commit()
    removed = rl.purge_expired_and_cap(db_session)
    left = db_session.scalar(select(func.count()).select_from(RateLimit))
    assert removed == 22          # 30 → 保留 80% = 8
    assert left == 8
    # 淘汰的是最早过期的那些，最"新"的必须还在
    assert db_session.scalar(select(RateLimit).where(RateLimit.key == "k:29")) is not None


# ===================== fatal_guard：FATAL → 容器退出 =====================
# 这段逻辑在容器里跑，出错的后果是「全站 502 但 docker ps 显示 Up」，
# 靠人工根本发现不了，所以必须用单测钉住事件解析与放行名单。
def _run_guard(monkeypatch, stdin_text):
    import importlib.util
    from pathlib import Path

    root = Path(__file__).resolve().parent.parent
    spec = importlib.util.spec_from_file_location(
        "fatal_guard", root / "deploy" / "fatal_guard.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    killed = []
    monkeypatch.setattr(mod.signal, "raise_signal", lambda sig: killed.append(sig))
    monkeypatch.setattr(mod.os, "getppid", lambda: 4242)
    monkeypatch.setattr(mod.os, "kill", lambda pid, sig: killed.append((pid, sig)))
    monkeypatch.setattr(mod.sys, "stdin", __import__("io").StringIO(stdin_text))
    out = __import__("io").StringIO()
    monkeypatch.setattr(mod.sys, "stdout", out)
    rc = mod.main()
    return rc, killed, out.getvalue()


def test_fatal_guard_kills_container_on_backend_fatal(monkeypatch):
    ev = ("eventname:PROCESS_STATE_FATAL\n"
          "processname:backend groupname:edu from_state:RUNNING\n")
    rc, killed, out = _run_guard(monkeypatch, ev)
    assert killed, "backend FATAL 必须触发退出信号，否则容器 Up 而全站 502"
    assert rc == 0
    assert "RESULT 2" in out, "event listener 必须回 ack，否则 supervisord 停止派发事件"


def test_fatal_guard_kills_on_nginx_fatal(monkeypatch):
    ev = ("eventname:PROCESS_STATE_FATAL\n"
          "processname:nginx groupname:edu from_state:RUNNING\n")
    _, killed, _ = _run_guard(monkeypatch, ev)
    assert killed


def test_fatal_guard_ignores_non_guarded_program(monkeypatch):
    """偶发失败的辅助进程不该把整个站点拉下线。"""
    ev = ("eventname:PROCESS_STATE_FATAL\n"
          "processname:fatal_guard groupname:edu from_state:RUNNING\n")
    _, killed, out = _run_guard(monkeypatch, ev)
    assert not killed
    assert "RESULT 2" in out


def test_fatal_guard_ignores_non_fatal_events(monkeypatch):
    ev = ("eventname:PROCESS_STATE_RUNNING\n"
          "processname:backend groupname:edu from_state:STARTING\n")
    _, killed, out = _run_guard(monkeypatch, ev)
    assert not killed
    assert "RESULT 2" in out


# ===================== 演示造数契约（reaudit3 P2-H / P2-K） =====================
# 造出来的数据必须能被产品自己的判分函数接受，否则演示闭环自相矛盾：
# 错题写着 is_correct=False，用 answers_match 重算却是满分。
def test_demo_options_all_contract_compliant():
    from app.services.init_db import _demo_banks, _demo_options
    from app.utils.options import normalize_options

    for bank in _demo_banks().values():
        for row in bank:
            qtype, stem, options = row[0], row[1], row[2]
            if qtype not in ("single", "multiple"):
                continue
            opts = _demo_options(options)
            assert opts, f"选择题必须造出选项：{stem}"
            assert normalize_options(opts) == opts, f"选项形状违约：{opts}"


def test_demo_wrong_answer_is_not_the_right_answer():
    """错题本的 wrong_answer 必须与标准答案不同，否则「错的那个」=「对的」。"""
    from app.services.init_db import _demo_banks, _demo_options, _wrong_answer_for
    from app.utils.options import normalize_options

    for bank in _demo_banks().values():
        for row in bank:
            qtype, stem, options, answer = row[0], row[1], row[2], row[3]
            opts = normalize_options(_demo_options(options))
            wrong = _wrong_answer_for(qtype, answer, opts)
            assert wrong != "", f"应能造出错答：{stem}"
            assert str(wrong).upper() != str(answer).strip().upper(), \
                f"错答与正确答案相同：{stem} answer={answer}"


def test_demo_answers_match_grading_function():
    """用平台自己的判分函数验证：错答判 0 分、对答判满分。"""
    from app.services.init_db import _demo_banks, _demo_options, _wrong_answer_for
    from app.utils.answer import answers_match

    checked = 0
    for bank in _demo_banks().values():
        for row in bank:
            qtype, _stem, options, answer = row[0], row[1], row[2], row[3]
            if qtype not in ("single", "multiple", "judge"):
                continue
            opts = _demo_options(options)
            wrong = _wrong_answer_for(qtype, answer, opts)
            assert answers_match(qtype, answer, answer) is True, "标准答案必须判对"
            assert answers_match(qtype, answer, wrong) is False, \
                f"错答被判对：wrong={wrong} answer={answer}"
            checked += 1
    assert checked >= 8, f"可校验的演示题太少（{checked}）"


def test_demo_seed_guard_is_off_by_default():
    """生产形态默认不造演示数据：两个开关的**类默认值**都必须是 False。

    这里查的是 Settings 的字段默认值，不是实例值 —— 实例会被仓库里的
    `.env` 覆盖（开发机通常开着 SEED_DEMO_DATA），拿实例断言等于在测环境。
    """
    from app.core.config import Settings

    fields = Settings.model_fields
    assert fields["SEED_DEMO_DATA"].default is False
    assert fields["DEMO_LEARNING_FLOW"].default is False


def _load_tool(filename):
    """按文件路径加载 tools/ 下的脚本（tools 不是包，不能直接 import）。

    传**带 .py 的文件名**而不是模块名：覆盖门禁靠「测试里出现该文件名」
    来证明这个模块真的被测过，去掉扩展名会让登记制失效。
    """
    import importlib.util
    from pathlib import Path

    root = Path(__file__).resolve().parent.parent
    spec = importlib.util.spec_from_file_location(
        f"_tool_{filename[:-3]}", root / "tools" / filename)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_four_layer_verdict_matrix():
    """四层合议：任何一种漂移都不能被"其它层绿"稀释成通过。"""
    m = _load_tool("check_four_layer.py")
    row = lambda st: {"layer": "x", "status": st, "version": "1", "commit": None, "note": ""}

    assert m.verdict([row(m.OK), row(m.OK)]) == 0
    assert m.verdict([row(m.OK), row(m.BAD)]) == 1
    # 服务器不可达 / 镜像未拉取 = 无法判定，既不算通过也不算漂移
    assert m.verdict([row(m.OK), row(m.WARN)]) == 2
    assert m.verdict([row(m.WARN), row(m.NA)]) == 2


def test_four_layer_behind_count_uses_git():
    """服务器落后几个提交必须真去数，不能按版本号字符串猜。"""
    m = _load_tool("check_four_layer.py")
    head = m.git("rev-parse", "HEAD")[0]
    prev = m.git("rev-parse", "HEAD~1")[0]
    if not head or not prev:
        pytest.skip("浅克隆或无父提交，跳过")
    assert m.behind_count(prev, head) == 1
    assert m.behind_count(head, head) == 0


def test_four_layer_local_flags_dirty_worktree(monkeypatch):
    """本地有未提交改动 = 已经不是任何已发布版本，必须报漂移。"""
    m = _load_tool("check_four_layer.py")

    monkeypatch.setattr(m, "git", lambda *a, **k: (
        ("M backend/x.py", "") if a[:2] == ("status", "--porcelain") else ("f" * 40, "")))
    assert m.layer_local("2.5.13")["status"] == m.BAD

    monkeypatch.setattr(m, "git", lambda *a, **k: (
        ("", "") if a[:2] == ("status", "--porcelain") else ("f" * 40, "")))
    assert m.layer_local("2.5.13")["status"] == m.OK


def test_deploy_run_cmd_keeps_every_required_flag():
    """重建容器的命令行少任何一个 flag 都是**静默降级**：

    - 少 `--env-file` → AI/调度/上传上限全回默认
    - 少 `-e SECRET_KEY` → 每次重启 JWT 随机换密钥，全员掉线
    - 少 `-v data` → 新容器起来是空库（最惨的一种）
    """
    d = _load_tool("deploy_release.py")
    cmd = d.run_cmd("9.9.9", "/opt/edu-ai-platform/.env.runtime", "SK123",
                    "ghcr.io/chenhui-001/edu-ai-platform:9.9.9")
    for frag in (
        "--env-file /opt/edu-ai-platform/.env.runtime",
        "APP_VERSION=9.9.9",
        "-p 8081:80",
        "-v /opt/edu-ai-platform/data:/app/data",
        "-v /opt/edu-ai-platform/logs:/app/data/logs",
        "SECRET_KEY=SK123",
        "DATABASE_URL=sqlite:////app/data/edu_platform.db",
        "--restart unless-stopped",
    ):
        assert frag in cmd, f"重建命令缺少 {frag}"


def test_deploy_strips_docker_injected_env():
    """从旧容器抄环境时，PATH/HOSTNAME 这类必须剔除，否则新容器会继承旧容器身份。"""
    d = _load_tool("deploy_release.py")
    assert {"PATH", "HOSTNAME", "HOME", "PWD", "LANG"} <= d.INJECTED


def test_deploy_dotenv_parsing(tmp_path):
    """首装回落读 .env：注释/空行跳过，值里的 `=` 不能被截断。"""
    d = _load_tool("deploy_release.py")
    p = tmp_path / ".env"
    p.write_text("# 注释\n\nLLM_MODEL=m1\nLLM_BASE_URL=https://x/y?a=1\nEMPTY=\n",
                 encoding="utf-8")
    env = d.read_dotenv(str(p))
    assert env["LLM_MODEL"] == "m1"
    assert env["LLM_BASE_URL"] == "https://x/y?a=1"
    assert env["EMPTY"] == ""
    assert "注释" not in "".join(env)


# ===================== 通知订阅偏好（F-07） =====================
def test_notification_category_fallback_maps_known_types():
    """历史调用点只给 type，没有 category —— 兜底映射错了就会"关不掉/乱关"。"""
    from app.services import notification as n

    assert n.resolve_category("exam") == n.CATEGORY_TASK
    assert n.resolve_category("review") == n.CATEGORY_REVIEW
    assert n.resolve_category("audit") == n.CATEGORY_AUDIT
    # 无法判断的一律 system：宁可关不掉一条系统通知，也不能误判成安全提醒
    assert n.resolve_category("whatever") == n.CATEGORY_SYSTEM


def test_notification_unknown_explicit_category_degrades_to_system(caplog):
    """显式传错类别不能静默变成「关不掉的安全提醒」，记 warning 后按 system。"""
    from app.services import notification as n

    assert n.resolve_category("system", explicit="securty") == n.CATEGORY_SYSTEM


def test_notification_effective_fills_default_and_forces_locked():
    from app.services import notification as n

    eff = n.effective({"grade": False, "security": False})
    assert eff["grade"] is False
    # 没配过的类别默认开启（opt-out，升级无需回填）
    assert eff["task"] is True and eff["review"] is True
    # 安全提醒即使被写成 False 也强制开启
    assert eff["security"] is True


def test_notification_parse_ignores_garbage():
    """prefs 列是自由文本：坏 JSON / 非 dict / 未知键 / 非 bool 值都不能炸。"""
    from app.services import notification as n

    assert n._parse("{不是 JSON") == {}
    assert n._parse("[1,2]") == {}
    assert n._parse('{"unknown": false, "grade": "no"}') == {}
    assert n._parse('{"grade": false}') == {"grade": False}
    assert n._parse(None) == {}


def test_notification_save_ignores_locked_and_merges(db_session):
    """锁定类别提交 false 应被忽略且**不落库**；其余类别只改传进来的那些。"""
    from app.models import User
    from app.services import notification as n

    u = User(username="np_user", password="x", real_name="偏好", status="active",
             identity="teacher")
    db_session.add(u)
    db_session.commit()

    n.save_prefs(db_session, u.id, {"grade": False, "security": False})
    prefs = n.load_prefs(db_session, u.id)
    assert prefs["grade"] is False
    assert prefs["security"] is True

    # 第二次只传 review：不能把 grade=False 冲掉
    n.save_prefs(db_session, u.id, {"review": False})
    prefs = n.load_prefs(db_session, u.id)
    assert prefs["grade"] is False and prefs["review"] is False


def test_notify_respects_prefs_and_keeps_transaction_open(db_session):
    """关闭的类别不落库；`notify` 不自己 commit（否则业务回滚会留孤儿通知）。"""
    from app.models import Notification, User
    from app.services import notification as n

    u = User(username="np_user2", password="x", real_name="偏好2", status="active",
             identity="teacher")
    db_session.add(u)
    db_session.commit()
    n.save_prefs(db_session, u.id, {"grade": False})

    assert n.notify(db_session, u.id, title="成绩已发布",
                    category=n.CATEGORY_GRADE) is None
    row = n.notify(db_session, u.id, title="新作业", type="exam",
                   category=n.CATEGORY_TASK)
    assert row is not None
    # 此刻它只是 session 里的 pending 对象 —— 证明 `notify` 没有自己 commit
    # （注意别用 query().count() 判断：会触发 autoflush，把 pending 刷进事务）
    assert row in db_session.new
    db_session.commit()
    assert db_session.query(Notification).count() == 1


def test_notify_many_counts_only_sent(db_session):
    """返回值是**实际发出**条数：`已通知 N 名学生` 直接用它，不能拿人数顶替。"""
    from app.models import User
    from app.services import notification as n

    users = [User(username=f"np_m{i}", password="x", real_name=f"批量{i}",
                  status="active", identity="teacher") for i in range(3)]
    db_session.add_all(users)
    db_session.commit()
    for u in users[:1]:
        n.save_prefs(db_session, u.id, {"task": False})

    sent = n.notify_many(db_session, [u.id for u in users], title="新作业",
                         type="exam", category=n.CATEGORY_TASK)
    assert sent == 2
    db_session.commit()


# ===================== 导出异步化的文件与时效（F-05） =====================
def test_export_job_options_rejects_unknown_kind():
    """类型写错必须在提交时就拒，不能渲染出一个空文件还标成功。"""
    from app.services import export_job as ej

    with pytest.raises(ValueError):
        ej.options_for("xlsx")


def test_export_job_answer_sheet_forces_student_mode():
    """答题卡没有"教师卷"，学生卷模式是唯一正确语义。"""
    from app.services import export_job as ej

    assert ej.options_for(ej.KIND_ANSWER_SHEET, mode="teacher")["mode"] == "student"
    assert ej.options_for(ej.KIND_PDF, mode="teacher")["mode"] == "teacher"


def test_export_job_target_path_inside_dir_and_unique(tmp_path, monkeypatch):
    """落盘名带 job_id + 随机后缀：既防枚举，也防同一任务重跑互相覆盖。"""
    import os

    from app.core.config import settings
    from app.services import export_job as ej

    monkeypatch.setattr(settings, "EXPORT_DIR", str(tmp_path))
    p1, name = ej.target_path(7, ej.KIND_DOCX)
    p2, _ = ej.target_path(7, ej.KIND_DOCX)
    assert os.path.dirname(os.path.abspath(p1)) == str(tmp_path)
    assert os.path.basename(p1).startswith("job7_")
    assert p1 != p2
    assert name.endswith(".docx")


def _seed_export_job(db_session, tmp_path, monkeypatch, *, age_minutes=0):
    """造一条已完成的导出任务 + 一个真实存在的文件，返回 (job, user, path)。"""
    import json as _json
    import os
    from datetime import timedelta

    from app.core.config import settings
    from app.models import AgentJob, User
    from app.services import agent_job_state, export_job as ej
    from app.utils.common import now_local

    monkeypatch.setattr(settings, "EXPORT_DIR", str(tmp_path))
    user = User(username=f"exp_u{age_minutes}", password="x", real_name="导出",
                status="active", identity="teacher")
    db_session.add(user)
    db_session.commit()

    job = AgentJob(user_id=user.id, agent=ej.EXPORT_JOB_AGENT,
                   status=agent_job_state.STATUS_SUCCEEDED, progress=100,
                   stage="完成", params="{}")
    db_session.add(job)
    db_session.commit()

    res = ej.write_file(job.id, ej.KIND_DOCX, b"PK\x03\x04fake", filename="p.docx")
    job.result = _json.dumps(res, ensure_ascii=False)
    job.finished_at = now_local() - timedelta(minutes=age_minutes)
    db_session.commit()
    return job, user, os.path.join(str(tmp_path), res["file"])


def test_export_job_download_ok(db_session, tmp_path, monkeypatch):
    from app.services import export_job as ej

    job, user, path = _seed_export_job(db_session, tmp_path, monkeypatch)
    got_path, filename, media = ej.resolve_download(job.id, user, db_session)
    assert got_path == path and filename == "p.docx"
    assert media.startswith("application/vnd.openxmlformats")


def test_export_job_download_expired_returns_410(db_session, tmp_path, monkeypatch):
    """过期必须明确 410，让前端提示"请重新导出"；不能给个空文件。"""
    import os

    from fastapi import HTTPException

    from app.services import export_job as ej

    job, user, path = _seed_export_job(db_session, tmp_path, monkeypatch,
                                       age_minutes=ej.TTL_MINUTES + 1)
    with pytest.raises(HTTPException) as exc:
        ej.resolve_download(job.id, user, db_session)
    assert exc.value.status_code == 410
    # 只删文件、不删 job 行：任务记录是"导出过什么"的溯源
    assert ej.cleanup_expired(db_session) == 1
    assert not os.path.exists(path)


def test_export_job_download_rejects_other_user(db_session, tmp_path, monkeypatch):
    """试卷里含答案 —— 知道 job_id 就能下载别人导出好的文件是实打实的泄露。"""
    from fastapi import HTTPException

    from app.models import User
    from app.services import export_job as ej

    job, _owner, _path = _seed_export_job(db_session, tmp_path, monkeypatch)
    other = User(username="exp_other", password="x", real_name="别人",
                 status="active", identity="teacher")
    db_session.add(other)
    db_session.commit()
    with pytest.raises(HTTPException) as exc:
        ej.resolve_download(job.id, other, db_session)
    assert exc.value.status_code == 403


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))