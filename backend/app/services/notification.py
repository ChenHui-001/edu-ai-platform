"""站内通知的**唯一写入出口** + 用户订阅偏好（F-07）。

## 为什么要有这个模块

改前 `db.add(Notification(...))` 散在 13 处（api/v1、services），每处自己拼
`type` / `biz_type`，没有任何统一校验。两个后果：

1. **`type` 词表漂移**：`system` 既是「建班申请被拒」也是「定时任务执行失败」，
   前端既没法按语义分类展示，也没法做订阅偏好 —— 想关「作业发布提醒」的人
   只能连「成绩已发布」一起关掉。
2. **想加一个全局规则（比如订阅偏好、去重、限流）就要改 13 个地方**，
   漏一个就会出现"有些通知关不掉"的诡现象。

所以写入收敛到 `notify()` / `notify_many()`，并引入**语义类别**（`category`）
与底层 `type` 解耦：`category` 决定"能不能被关"，`type` 继续用于溯源/前端着色。

## 类别设计

| category | 说明 | 可否关闭 |
|---|---|---|
| `task` | 作业/考试发布 | 可 |
| `grade` | 成绩发布、作业退回 | 可 |
| `review` | 复习提醒 | 可 |
| `audit` | 审批类（注册/建班申请） | 可 |
| `system` | 系统与运维（定时任务失败、共享试卷…） | 可 |
| `security` | 安全提醒（异常登录） | **不可，永远发送** |

`security` 刻意不可关：能被静默关掉的登录告警等于没有告警。真要联系管理员，
应该改密码，而不是关掉通知。

## 缺省值

没配过的类别一律**开启**（opt-out）。所以升级不需要回填数据，
"从未打开过设置页"的用户行为与改动前完全一致。
"""
import json
from typing import Any, Dict, Iterable, List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.logger import get_logger
from app.models import Notification, NotifyPref

logger = get_logger("notification")

# 固定顺序：前端按这个顺序渲染开关
CATEGORY_TASK = "task"
CATEGORY_GRADE = "grade"
CATEGORY_REVIEW = "review"
CATEGORY_AUDIT = "audit"
CATEGORY_SYSTEM = "system"
CATEGORY_SECURITY = "security"

CATEGORIES: List[Dict[str, Any]] = [
    {"key": CATEGORY_TASK, "label": "作业 / 考试发布",
     "description": "老师发布新作业、考试时提醒我", "locked": False},
    {"key": CATEGORY_GRADE, "label": "成绩与批改结果",
     "description": "成绩发布、作业被退回时提醒我", "locked": False},
    {"key": CATEGORY_REVIEW, "label": "复习提醒",
     "description": "每日艾宾浩斯复习计划提醒", "locked": False},
    {"key": CATEGORY_AUDIT, "label": "审批事项",
     "description": "注册申请、建班申请及其审批结果", "locked": False},
    {"key": CATEGORY_SYSTEM, "label": "系统消息",
     "description": "共享试卷、定时任务异常等系统通知", "locked": False},
    {"key": CATEGORY_SECURITY, "label": "安全提醒",
     "description": "异常登录等安全告警（为保障账号安全，不可关闭）", "locked": True},
]

CATEGORY_KEYS = tuple(c["key"] for c in CATEGORIES)
LOCKED_KEYS = frozenset(c["key"] for c in CATEGORIES if c["locked"])

# 历史调用点只有 `type`/`biz_type`，没有 category。这张表是**兜底映射**，
# 新增调用请直接传 `category=`（显式优于推断）。
_TYPE_FALLBACK = {
    "exam": CATEGORY_TASK,
    "review": CATEGORY_REVIEW,
    "audit": CATEGORY_AUDIT,
}


def resolve_category(notif_type: Optional[str], biz_type: Optional[str] = None,
                     explicit: Optional[str] = None) -> str:
    """确定通知的语义类别。显式传入优先，其次按 type/biz_type 兜底。"""
    if explicit:
        if explicit not in CATEGORY_KEYS:
            # 打错字的 category 不应静默变成 system —— 那会让"关不掉"变成
            # "莫名其妙关掉了"。这里记 warning 并当 system 处理。
            logger.warning(f"未知通知类别 {explicit!r}，按 system 处理")
            return CATEGORY_SYSTEM
        return explicit
    if biz_type in (CATEGORY_TASK, CATEGORY_GRADE):
        return biz_type
    if notif_type in _TYPE_FALLBACK:
        mapped = _TYPE_FALLBACK[notif_type]
        # 成绩发布/作业退回历史上都用 type="system"+biz_type="task"，
        # 靠标题区分是不可靠的，因此由调用点显式传 category。
        return mapped
    return CATEGORY_SYSTEM


# ---------------------------------------------------------------- 偏好读写
def _parse(raw: Optional[str]) -> Dict[str, bool]:
    if not raw:
        return {}
    try:
        data = json.loads(raw)
    except (TypeError, ValueError):
        logger.warning("sys_notify_pref.prefs 不是合法 JSON，按全部开启处理")
        return {}
    if not isinstance(data, dict):
        return {}
    out: Dict[str, bool] = {}
    for key, val in data.items():
        if key in CATEGORY_KEYS and isinstance(val, bool):
            out[key] = val
    return out


def effective(prefs: Dict[str, bool]) -> Dict[str, bool]:
    """补全缺省值 + 锁定项强制开启，返回完整开关表。"""
    return {key: (True if key in LOCKED_KEYS else prefs.get(key, True))
            for key in CATEGORY_KEYS}


def load_prefs(db: Session, user_id: int) -> Dict[str, bool]:
    row = db.get(NotifyPref, int(user_id))
    return effective(_parse(row.prefs if row else None))


def load_prefs_many(db: Session, user_ids: Iterable[int]) -> Dict[int, Dict[str, bool]]:
    """一次查出多个用户的偏好（避免通知批量发送时的 N+1）。"""
    ids = [int(u) for u in user_ids]
    if not ids:
        return {}
    rows = db.scalars(
        select(NotifyPref).where(NotifyPref.user_id.in_(ids))
    ).all()
    stored = {int(r.user_id): _parse(r.prefs) for r in rows}
    return {uid: effective(stored.get(uid, {})) for uid in ids}


def save_prefs(db: Session, user_id: int, updates: Dict[str, Any]) -> Dict[str, bool]:
    """合并保存；`locked` 类别提交任何值都被忽略（永远开启）。"""
    row = db.get(NotifyPref, int(user_id))
    current = _parse(row.prefs if row else None)
    for key, val in (updates or {}).items():
        if key not in CATEGORY_KEYS:
            continue
        if key in LOCKED_KEYS:
            current.pop(key, None)
            continue
        if isinstance(val, bool):
            current[key] = val
    if row is None:
        row = NotifyPref(user_id=int(user_id), prefs=json.dumps(current, ensure_ascii=False))
        db.add(row)
    else:
        row.prefs = json.dumps(current, ensure_ascii=False)
    db.commit()
    return effective(current)


# ---------------------------------------------------------------- 写入出口
def notify(
    db: Session,
    user_id: int,
    *,
    title: str,
    content: Optional[str] = None,
    type: str = "system",
    biz_type: Optional[str] = None,
    biz_id: Optional[int] = None,
    category: Optional[str] = None,
) -> Optional[Notification]:
    """给单个用户发通知；该用户关掉了这个类别则**不发**（返回 None）。

    不 commit：与调用方（发布作业、批改、审批）共用同一个事务，
    避免「通知已落库、业务却回滚」留下一条指向不存在作业的提醒。
    """
    cat = resolve_category(type, biz_type, category)
    if not load_prefs(db, user_id).get(cat, True):
        return None
    row = Notification(
        user_id=int(user_id), title=title, content=content,
        type=type, biz_type=biz_type, biz_id=biz_id,
    )
    db.add(row)
    return row


def notify_many(
    db: Session,
    user_ids: Iterable[int],
    *,
    title: str,
    content: Optional[str] = None,
    type: str = "system",
    biz_type: Optional[str] = None,
    biz_id: Optional[int] = None,
    category: Optional[str] = None,
) -> int:
    """批量发通知，返回**实际发出**的条数（已扣掉关掉该类别的用户）。

    偏好用一次 `IN` 查询取回：逐个调 `load_prefs` 在"发布给整个年级"时
    会变成几百次单行查询，正是 `check_n_plus_one` 盯的那类形态。
    """
    cat = resolve_category(type, biz_type, category)
    ids = [int(u) for u in user_ids]
    if not ids:
        return 0
    prefs = load_prefs_many(db, ids)
    sent = 0
    for uid in ids:
        if not prefs.get(uid, {}).get(cat, True):
            continue
        db.add(Notification(
            user_id=uid, title=title, content=content,
            type=type, biz_type=biz_type, biz_id=biz_id,
        ))
        sent += 1
    return sent


def describe_categories() -> List[Dict[str, Any]]:
    """给前端的类别清单（含是否锁定）。"""
    return [dict(c) for c in CATEGORIES]
