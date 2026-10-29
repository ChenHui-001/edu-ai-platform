"""QA 审计单元套件（对应 audit-reports/qa/TEST_CASES.csv 关键用例）。

覆盖：JSON 解析、难度归一化、题量拆分、长任务超时判据、JWT 吊销 fail-closed、
知识点种子完整性，以及用**内存 SQLite** 直接验证 BUG-001(usage_count 对称递减)
与 BUG-009(并发落库 id 回填) 的修复。

运行：cd backend && python -m pytest qa_audit_suite.py -q
"""
from datetime import datetime, timedelta

import pytest
from sqlalchemy import create_engine, select
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
    """BUG-001 修复验证：改卷时保留题计数不变、移除题 -1、新增题 +1。"""
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

    assert q1.usage_count == 5  # 保留：新 +1 与旧 -1 抵消
    assert q2.usage_count == 4  # 移除：净 -1
    assert q3.usage_count == 1  # 新增：+1


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
    """CI 传入的 ISO 时间（带 T/Z、毫秒、时区）必须归一化后再展示。"""
    from app.services.version_info import _fmt_time

    assert _fmt_time("2026-10-29T09:12:34Z") == "2026-10-29 09:12:34"
    assert _fmt_time("2026-10-29T09:12:34.123456+00:00") == "2026-10-29 09:12:34"
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


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))