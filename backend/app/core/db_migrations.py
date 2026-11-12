"""轻量 SQLite 结构迁移：启动时幂等补列。

背景：项目依赖 `Base.metadata.create_all` 建表，但它**只创建缺失的表，
不会给已存在的表添加新列**。模型加了字段、老库没有该列时，一切涉及
该列的读写都会 500（案例：v1.0.19 给 sys_attachment 加 biz_type，
老库长期未暴露，直到教案附件按 biz_type 查询才炸）。

在引入 Alembic 之前，用这张清单兜底：启动时逐项检查，缺列则
ALTER TABLE ADD COLUMN（SQLite 支持，且重复执行幂等——先 PRAGMA 探测）。
"""
import logging
import time
from typing import List, Optional, Tuple

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings

logger = logging.getLogger(__name__)

# 瞬时错误：重试有意义。SQLite 单写锁在并发启动/备份/大事务时会出现
# `database is locked`，磁盘抖动会出 `disk I/O error`。这些重试几次就过。
# 其它错误（DDL 本身写错、NOT NULL 无默认值）重试一万次也一样，必须快速失败。
_TRANSIENT_MARKERS = (
    "database is locked",
    "database schema is locked",
    "database table is locked",
    "disk i/o error",
    "unable to open database file",
    "attempt to write a readonly database",
)
MIGRATION_ATTEMPTS = 3
MIGRATION_RETRY_DELAY = 0.5


def _is_transient(exc: BaseException) -> bool:
    msg = str(exc).lower()
    return any(marker in msg for marker in _TRANSIENT_MARKERS)

# (表名, 列名, 列类型 DDL)。新加模型字段若老库可能缺列，登记到这里。
MIGRATION_COLUMNS: List[Tuple[str, str, str]] = [
    # v2.2.27: 作文题建议最少字数。老库无此列时 ORM 读写直接 500
    # （create_all 只建缺失的表，不会给已有表补列）。
    ("edu_question", "answer_min_words", "INTEGER"),
    # v1.0.19: Attachment 业务绑定（教案/作业等按 biz_type+biz_id 挂附件）
    ("sys_attachment", "biz_type", "VARCHAR(32)"),
    # v1.0.42: AI 教案 —— 教案主体补齐「教学准备 / 课堂练习」与生成溯源，
    # 教学过程补「师生活动」分列。AI 教案要求这些是独立章节，
    # 老库没有该列时 create_all 不会补，读写即 500。
    ("edu_lesson_plan", "teaching_preparation", "TEXT"),
    ("edu_lesson_plan", "class_exercise", "TEXT"),
    ("edu_lesson_plan", "ai_generated", "INTEGER DEFAULT 0"),
    ("edu_lesson_plan", "ai_job_id", "INTEGER"),
    ("edu_lesson_stage", "teacher_activity", "TEXT"),
    ("edu_lesson_stage", "student_activity", "TEXT"),
    # v1.0.42: AI 任务进度提示（前后端轮询要给出「正在做什么」）
    ("sys_agent_job", "progress", "INTEGER DEFAULT 0"),
    ("sys_agent_job", "stage", "VARCHAR(64)"),
    # v2.5.22: AI 长任务可取消（F-04）。协作式取消标志，worker 在检查点响应。
    # DEFAULT 0 是必须的：老库里已有的 finished 行要读成「未请求取消」。
    ("sys_agent_job", "cancel_requested", "INTEGER DEFAULT 0"),
    # v1.1.0: 知识点 V2（树治理 / 状态 / 来源 / 创建者）
    ("edu_knowledge_point", "textbook_version", "VARCHAR(64)"),
    ("edu_knowledge_point", "status", "VARCHAR(16) DEFAULT 'published'"),
    ("edu_knowledge_point", "source", "VARCHAR(16) DEFAULT 'manual'"),
    ("edu_knowledge_point", "owner_id", "INTEGER"),
    # v1.3.0: 知识点附件学生可见性（默认可见，旧数据升级后不改变行为）
    ("sys_attachment", "visible_to_student", "INTEGER DEFAULT 1"),
    # v2.1.0: 标准组卷 V3 —— 试卷扩展维度（来源标准 / 学段 / 审核态 / 共享范围 / 版本）
    # status 默认 published：存量试卷升级后必须仍然可见可用，不能因为新增审核态而"消失"。
    ("edu_paper", "description", "TEXT"),
    ("edu_paper", "exam_type", "VARCHAR(32)"),
    ("edu_paper", "stage", "VARCHAR(16)"),
    ("edu_paper", "textbook_version", "VARCHAR(64)"),
    ("edu_paper", "status", "VARCHAR(16) DEFAULT 'published'"),
    ("edu_paper", "standard_id", "INTEGER"),
    ("edu_paper", "share_scope", "VARCHAR(16) DEFAULT 'private'"),
    ("edu_paper", "review_comment", "TEXT"),
    ("edu_paper", "review_by", "INTEGER"),
    ("edu_paper", "review_at", "DATETIME"),
    ("edu_paper", "current_version", "INTEGER DEFAULT 1"),
    ("edu_paper", "generation_params", "TEXT"),
    ("edu_paper", "type_report", "TEXT"),
    # v2.1.0: 题项大题分组（按题型 code 分组，改大题名不会打散分组）
    ("edu_paper_item", "section_code", "VARCHAR(32)"),
    ("edu_paper_item", "section_sort", "INTEGER DEFAULT 0"),
    ("edu_paper_item", "score_override", "INTEGER DEFAULT 0"),
    # v2.1.0: 共享权限级别（仅查看 / 可另存 / 可编辑）
    ("edu_paper_share", "permission", "VARCHAR(16) DEFAULT 'view'"),
    ("edu_paper_share", "scope", "VARCHAR(16)"),
]


# 知识点 V2 一次性迁移标记：旧数据是平铺结构且用户已确认不需要保留，
# 首次升级时清空并按新层级重新播种；只执行一次，之后不再触碰业务数据。
# 值即版本号：以后结构再升级时递增，旧值会自动触发对应迁移。
_KNOWLEDGE_V2_MARKER = "knowledge_v2_migrated"
_KNOWLEDGE_V2_MARKER_VALUE = "2"


# 题库 V2 一次性迁移标记：历史题库数据用户已确认可全部删除，首次升级清空
# edu_question（级联 question_knowledge / paper_item），**不重新播种**；
# E2E 在空库基础上自建题目。只执行一次，之后不再触碰业务数据。
_QUESTION_V2_MARKER = "question_bank_v2_migrated"
_QUESTION_V2_MARKER_VALUE = "1"


# 索引迁移清单：(索引名, 表名, 列名)。
#
# 为什么需要独立清单：`Base.metadata.create_all` **只建缺失的表**，不会给
# 已存在的表补索引 —— 模型上写 `index=True` 只对全新库生效，老库永远不会
# 有这个索引。这与「补列」是同一类问题，因此放在同一个启动步骤里做。
#
# 只登记「确实会被 where/join 用到、且表会持续增长」的列。表只有几十行时
# 加索引收益接近 0，登记进来只会让每次启动多做一次无意义的 DDL。
MIGRATION_INDEXES: List[Tuple[str, str, str]] = [
    # 分享列表按分享人过滤（PaperShare.from_user_id 原先无索引）。
    # 索引名必须与 SQLAlchemy 的默认命名（ix_<表>_<列>）**完全一致**：
    # 新建库时 create_all 会按模型上的 index=True 自动建同名索引，这里若用
    # 别的名字（如 ix_..._from_user），新库就会同时存在两个等价索引 ——
    # 浪费空间且拖慢写入。同名才能让「已有则跳过」的判断真正生效。
    ("ix_edu_paper_share_from_user_id", "edu_paper_share", "from_user_id"),
]


def run_index_migrations(db: Session) -> List[str]:
    """幂等补建缺失索引。返回本次实际创建的索引名。

    SQLite 的 `CREATE INDEX IF NOT EXISTS` 本身幂等，但仍先查 sqlite_master：
    ① 便于只对真正缺失的项执行 DDL（避免每次启动都写一次 schema）；
    ② 表尚未创建时（极端情况下的半初始化库）能跳过而不是抛错。
    """
    applied: List[str] = []
    for name, table, column in MIGRATION_INDEXES:
        try:
            table_exists = db.execute(
                text("SELECT 1 FROM sqlite_master WHERE type='table' AND name=:t"),
                {"t": table},
            ).first()
            if not table_exists:
                continue
            index_exists = db.execute(
                text("SELECT 1 FROM sqlite_master WHERE type='index' AND name=:n"),
                {"n": name},
            ).first()
            if index_exists:
                continue
            db.execute(text(f"CREATE INDEX IF NOT EXISTS {name} ON {table} ({column})"))
            applied.append(f"{table}.{column}")
        except Exception as exc:  # noqa: BLE001 索引失败绝不能阻断启动
            logger.warning(f"索引迁移跳过 {table}.{column}: {exc}")
    if applied:
        db.commit()
    return applied


def upgrade_draft_standards_to_spec(db: Session) -> List[str]:
    """把「系统自动生成的命题标准草案」刷新为最新的分学科规范结构。

    与 `upgrade_generic_standards` 的分工：
    - 上一个函数认的是**更老的一版**（单选/填空/解答 10/5/5），精确匹配题型序列；
    - 本函数认的是「一键生成草案」产出的记录，以
      **description 里的固定文案**为标识（`系统按通用结构自动生成的草案`），
      并在结构真的变化时才更新。

    为什么需要它：模板从「按题库题型配额凑结构」改成「逐科对齐
    《初中毕业学业水平考试试卷结构规范》」后，生产库里已有的草案仍是旧结构，
    组卷继续按旧结构出卷 —— 代码改了但线上完全看不到效果。

    为什么按 description 而非 source：`source='manual'` 既包含系统草案也包含
    管理员手建的标准；只有草案带这句固定文案（见 `exam_standard.create_generic_standards`）。
    管理员手工新建/编辑过的标准不会被误改。

    幂等：结构一致即跳过（第二次启动不再命中）。
    """
    import json

    from app.services.exam_structures import (
        difficulty_gradient, exam_meta, sections_for,
    )

    marker = "系统按通用结构自动生成的草案"
    try:
        rows = db.execute(text(
            "SELECT id, stage, subject_name, total_score, duration, sections,"
            " difficulty_ratio, description FROM edu_exam_standard"
        )).fetchall()
    except Exception as exc:  # noqa: BLE001 表不存在（全新库）时跳过
        logger.debug(f"草案结构刷新跳过：{exc}")
        return []

    refreshed: List[str] = []
    for row in rows:
        if marker not in str(row.description or ""):
            continue
        meta = exam_meta(row.stage, row.subject_name)
        # 目标总分：有规范元信息时用「笔试卷面分」（英语 90，其余同卷面分），
        # 否则沿用原值 —— 学科不在规范内（如体育）不该被改成 100/90。
        target_score = float(meta["written_score"]) if meta else float(row.total_score or 100)
        new_sections = sections_for(row.stage, row.subject_name, target_score)
        new_json = json.dumps(new_sections, ensure_ascii=False)
        if new_json == json.dumps(json.loads(row.sections or "[]"), ensure_ascii=False):
            continue

        new_diff = json.dumps(
            difficulty_gradient(new_sections, row.subject_name, stage=row.stage),
            ensure_ascii=False)
        new_duration = int(meta["duration"]) if meta else int(row.duration or 90)
        db.execute(
            text("UPDATE edu_exam_standard SET sections=:s, difficulty_ratio=:d,"
                 " total_score=:t, duration=:u WHERE id=:i"),
            {"s": new_json, "d": new_diff, "t": target_score,
             "u": new_duration, "i": row.id},
        )
        refreshed.append(
            f"{row.stage}/{row.subject_name}({row.total_score}→{target_score:g}分)")

    if refreshed:
        db.commit()
        logger.warning(f"命题标准草案已刷新为规范结构（{len(refreshed)} 条）：{refreshed}")
    return refreshed


def upgrade_generic_standards(db: Session) -> List[str]:
    """把「旧通用结构」生成的命题标准草案，升级为分学段学科的真实考试结构。

    背景：旧版 `generic_sections()` 只输出「单选 10 / 填空 5 / 解答 5」三种题型，
    而生产环境 `SEED_BASE_DATA=false`（规范种子标准不播种），命题标准是用
    「一键生成草案」批量造的 —— 于是所有学科的标准都是这三种题型，AI 一键
    组卷跟着只剩三种题型（用户反馈的「题型单一」）。

    **识别条件必须精确**，否则会覆盖管理员手工配过的结构：
    题型序列恰为 ["single","blank","short"] **且**题量为 [10,5,5]。
    只要有一项不同就跳过 —— 宁可漏升级，也不能改坏别人的配置。

    幂等：升级后序列变成 4~6 个题型，下次启动不再命中。
    """
    import json

    from app.services.exam_structures import (
        difficulty_gradient, legacy_draft_codes, sections_for,
    )

    old_codes = legacy_draft_codes()
    try:
        rows = db.execute(text(
            "SELECT id, stage, subject_name, total_score, sections FROM edu_exam_standard"
        )).fetchall()
    except Exception as exc:  # noqa: BLE001 表不存在（全新库）时跳过
        logger.debug(f"命题标准升级跳过：{exc}")
        return []

    upgraded: List[str] = []
    for row in rows:
        try:
            sections = json.loads(row.sections or "[]")
        except (TypeError, ValueError):
            continue
        if not isinstance(sections, list) or len(sections) != len(old_codes):
            continue
        if [str(s.get("code")) for s in sections] != old_codes:
            continue
        if [int(s.get("count") or 0) for s in sections] != [10, 5, 5]:
            continue

        new_sections = sections_for(
            row.stage, row.subject_name, float(row.total_score or 100))
        db.execute(
            text("UPDATE edu_exam_standard SET sections=:s, difficulty_ratio=:d WHERE id=:i"),
            {
                "s": json.dumps(new_sections, ensure_ascii=False),
                "d": json.dumps(
                    difficulty_gradient(new_sections, row.subject_name, stage=row.stage),
                    ensure_ascii=False),
                "i": row.id,
            },
        )
        upgraded.append(f"{row.stage}/{row.subject_name}({row.total_score}分)")

    if upgraded:
        db.commit()
        logger.warning(f"命题标准结构升级完成（{len(upgraded)} 条）：{upgraded}")
    return upgraded


def run_question_v2_migration(db: Session) -> bool:
    """题库 V2 数据迁移：首次启动清空历史题库（只执行一次）。

    与知识点迁移一样仅走 SQLite 轻量路径；全新库表为空，DELETE 无副作用。
    返回本次是否执行了清空。
    """
    if not settings.DATABASE_URL.startswith("sqlite"):
        return False
    try:
        # 表不存在说明 create_all 尚未建表（正常启动流程不会发生），直接跳过
        info = db.execute(text("PRAGMA table_info(edu_question)")).fetchall()
        if not info:
            return False
        applied = db.execute(text(
            "SELECT value FROM sys_config WHERE key = :k"), {"k": _QUESTION_V2_MARKER}
        ).first()
        if applied and str(applied[0]) == _QUESTION_V2_MARKER_VALUE:
            return False

        old_count = db.execute(text("SELECT COUNT(*) FROM edu_question")).scalar() or 0
        # 显式清空子表：不依赖数据库外键级联开关（SQLite PRAGMA 非全局生效，
        # PostgreSQL 迁移路径未来接入时也能保证不残留孤儿关联）。
        db.execute(text("DELETE FROM edu_question_knowledge"))
        db.execute(text("DELETE FROM edu_paper_item"))
        db.execute(text("DELETE FROM edu_question"))
        db.execute(text(
            "INSERT INTO sys_config "
            "(key, value, value_type, category, is_public, created_at, updated_at) "
            "VALUES (:k, :v, 'string', 'system', 0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP) "
            "ON CONFLICT(key) DO UPDATE SET value = :v, updated_at = CURRENT_TIMESTAMP"),
            {"k": _QUESTION_V2_MARKER, "v": _QUESTION_V2_MARKER_VALUE})
        db.commit()
        logger.warning(
            "题库 V2 迁移完成：已清空 %s 道历史题目（用户已确认可删除），"
            "不重新播种；E2E 将在空库上自建题", old_count)
        return True
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        logger.error("题库 V2 迁移失败: %s", exc)
        return False


def run_knowledge_v2_migration(db: Session) -> bool:
    """知识点结构升级：清空旧平铺数据 + 建索引 + 写迁移标记。

    仅 SQLite 轻量迁移路径；全新库表为空，不会误删。返回是否执行了清空。
    """
    if not settings.DATABASE_URL.startswith("sqlite"):
        return False
    try:
        info = db.execute(text("PRAGMA table_info(edu_knowledge_point)")).fetchall()
        if not info:
            return False
        applied = db.execute(text(
            "SELECT value FROM sys_config WHERE key = :k"), {"k": _KNOWLEDGE_V2_MARKER}
        ).first()
        if applied and str(applied[0]) == _KNOWLEDGE_V2_MARKER_VALUE:
            return False

        # 旧结构（无 status 列）说明是从 V1 升级：按用户确认清空旧知识点。
        # 新库 create_all 已带 status，表为空，DELETE 无副作用。
        old_count = db.execute(text("SELECT COUNT(*) FROM edu_knowledge_point")).scalar() or 0
        db.execute(text("DELETE FROM edu_knowledge_point"))

        # 树查询/编码查重依赖的索引（create_all 只对新库生效，老库需显式补）
        db.execute(text(
            "CREATE INDEX IF NOT EXISTS ix_kp_grade_subject_parent "
            "ON edu_knowledge_point (grade_id, subject_id, parent_id)"))
        # 这里原本还建过一个 `ux_kp_subject_code` 部分唯一索引
        # （ON (grade_id, subject_id, code) WHERE code IS NOT NULL）。它和模型里的
        # `uq_kp_subject_code` UNIQUE 约束**完全重复**：SQLite 的唯一约束/唯一索引
        # 本来就把多个 NULL 视为互不相同，那个 WHERE 不改变任何语义。留着只会让
        # `alembic check` 永久报一个 remove_index（元数据里没有它），
        # 所以已删除；唯一性由模型的 UNIQUE 约束保证。
        db.execute(text(
            "INSERT INTO sys_config "
            "(key, value, value_type, category, is_public, created_at, updated_at) "
            "VALUES (:k, :v, 'string', 'system', 0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP) "
            "ON CONFLICT(key) DO UPDATE SET value = :v, updated_at = CURRENT_TIMESTAMP"),
            {"k": _KNOWLEDGE_V2_MARKER, "v": _KNOWLEDGE_V2_MARKER_VALUE})
        db.commit()
        logger.warning(
            "知识点 V2 迁移完成：已清空 %s 条旧平铺数据并重建索引（按用户确认）", old_count)
        return True
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        logger.error("知识点 V2 迁移失败: %s", exc)
        return False


def run_column_migrations(db: Session) -> List[str]:
    """幂等补列，返回本次实际新增的列（用于日志）。"""
    applied: List[str] = []
    # 本迁移基于 SQLite 的 PRAGMA table_info；切 PostgreSQL 时 PRAGMA 不存在，
    # 逐个失败并静默跳过会让「模型加列、老库缺列」问题在切库后重新出现。
    # 明确跳过并提示使用 Alembic，避免给出"已迁移"的假象。
    if not settings.DATABASE_URL.startswith("sqlite"):
        logger.warning(
            "当前数据库非 SQLite，已跳过轻量补列迁移；"
            "请先执行等价 DDL 或引入版本化迁移工具补齐结构再启动，"
            "否则模型列缺失会在运行时随机 500"
        )
        return applied
    for table, column, ddl in MIGRATION_COLUMNS:
        rows = db.execute(text(f"PRAGMA table_info({table})")).fetchall()
        if not rows:
            continue  # 表尚不存在：create_all 会建出全列结构
        existing = {r[1] for r in rows}
        if column in existing:
            continue
        last_exc: Optional[Exception] = None
        for attempt in range(1, MIGRATION_ATTEMPTS + 1):
            try:
                db.execute(text(
                    f"ALTER TABLE {table} ADD COLUMN {column} {ddl}"))
                db.commit()
                last_exc = None
                applied.append(f"{table}.{column}")
                logger.warning("结构迁移：已为 %s 补充列 %s", table, column)
                break
            except Exception as exc:  # noqa: BLE001
                db.rollback()
                last_exc = exc
                if not _is_transient(exc) or attempt >= MIGRATION_ATTEMPTS:
                    break
                # 瞬时错误才重试，且退避递增；确定性错误立刻跳出
                logger.warning(
                    "结构迁移 %s.%s 第 %d/%d 次失败（瞬时错误，稍后重试）：%s",
                    table, column, attempt, MIGRATION_ATTEMPTS, exc)
                time.sleep(MIGRATION_RETRY_DELAY * attempt)
        if last_exc is None:
            continue
        # 旧实现「记日志继续下一条」：启动照常完成，进程带着缺失列
        # 对外服务，之后任何涉及该列的读写随机 500，且日志里只有一行
        # error 很容易被忽略。结构迁移失败必须阻断启动——带病上线
        # 比启动失败危险得多。静态一致性由 tools/check_migration_columns.py
        # 在 CI 里提前拦住拼错的清单项。
        #
        # 阻断时的报错必须能直接指导人工修复：只说「迁移失败」会让人去翻
        # 代码，而真正要做的是在库里补这一列。容器层面由
        # deploy/fatal_guard.py 把 backend FATAL 翻译成「容器退出」，
        # 使 docker 的 restart 策略接管，避免出现「容器 Up 但全站 502」。
        logger.error("结构迁移失败 %s.%s: %s", table, column, last_exc)
        raise RuntimeError(
            f"结构迁移失败：{table}.{column}：{last_exc}\n"
            f"人工处理（任选其一，补齐后重启容器会自动跳过）：\n"
            f"  1) 在数据库中执行：ALTER TABLE {table} ADD COLUMN {column} {ddl};\n"
            f"  2) 若该列本应可空，给 MIGRATION_COLUMNS 里的 DDL 补 DEFAULT 值后重新发版。\n"
            f"  说明：SQLite 无法给已有数据的表补「NOT NULL 且无默认值」的列。"
        ) from last_exc
    return applied