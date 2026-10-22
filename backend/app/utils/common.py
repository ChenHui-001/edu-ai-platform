"""分页、CRUD 基类、响应封装等通用工具。"""
import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Type, TypeVar

from fastapi import Query
from pydantic import BaseModel, field_validator, ConfigDict
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings

T = TypeVar("T")


def today_str() -> str:
    """本地时区的当天日期串（YYYY-MM-DD）。

    打卡 / 复习计划 / 学习目标这类「今天」语义必须按用户所在时区算：
    用 UTC 计算，北京时间 0:00-8:00 期间仍是"昨天"，会把打卡日历与
    复习计划整体错位 8 小时。容器与开发机 TZ 均为 Asia/Shanghai，
    datetime.now() 即北京时间。
    """
    return datetime.now().strftime("%Y-%m-%d")


def now_local() -> datetime:
    """当前时间（naive，跟随进程时区；容器 TZ=Asia/Shanghai 即北京时间）。

    ## 为什么叫 now_local 而不是 utcnow

    这个函数**一直返回本地时间**，不是 UTC：

        >>> now_local().utcoffset() is None   # naive，不带时区信息
        True

    历史名字 `utcnow()` 与实际行为相反，代价是真实的：

    - 构造时间窗时误以为拿到的是 UTC，再手动 +8 小时 → 服务端判定「已过期」；
    - 排查时区问题时按「UTC」的直觉推演，结论方向错误；
    - CI（runner UTC）与本机（Asia/Shanghai）行为不一致，却归因到业务代码。

    改名后名字即语义，配合 `/health` 暴露的 `server_time` 形成「时间基准
    必须来自服务端」的明确约定。

    ## 为什么不改成真 UTC

    改用 `datetime.now(timezone.utc)` 会**改变现有数据语义**：库里存的
    历史时间戳是本地时间，混入 UTC 会让「8 小时前/后」的判定整体错位。
    前端也直接拼本地时间字符串（如 "2026-10-22 09:00:00"）提交——那是
    后端 `_parse_dt` 唯一接受的格式，不含时区，按 UTC 解析就是错的。
    因此保留本地时间语义，只把名字改对。
    """
    return datetime.now()


# ---------------------------------------------------------------- 兼容别名
# 旧名保留为别名，避免尚未更新到的外部脚本 / 二次开发代码 ImportError。
# **本仓库内已无任何调用点**（`tools/check_legacy_utcnow.py` 守住这一契约）。
# 新代码一律用 now_local()：别名只为兼容，不参与业务逻辑。
utcnow = now_local


class ORMBase(BaseModel):
    """Pydantic ORM 序列化基类。"""

    model_config = ConfigDict(from_attributes=True)


class PageParams(BaseModel):
    """分页入参。

    容错策略：page/page_size 传入 0、负数或超大值时**自动收敛**到合法区间，
    而不是返回 422。前端分页组件在「清空筛选」「首次渲染」等场景会传 0，
    此前直接 422 导致列表白屏（实测 page=0 / page_size=0 均 422）。
    """

    page: int = Query(1, description="页码，从 1 开始（<1 时按 1 处理）")
    page_size: int = Query(
        settings.DEFAULT_PAGE_SIZE, description="每页数量（越界自动收敛）"
    )

    @field_validator("page", mode="before")
    @classmethod
    def _clamp_page(cls, v):
        try:
            return max(1, int(v))
        except (TypeError, ValueError):
            return 1

    @field_validator("page_size", mode="before")
    @classmethod
    def _clamp_page_size(cls, v):
        try:
            n = int(v)
        except (TypeError, ValueError):
            return settings.DEFAULT_PAGE_SIZE
        return min(max(1, n), settings.MAX_PAGE_SIZE)

    @property
    def offset(self) -> int:
        return (max(1, self.page) - 1) * self.page_size


class PageResult(BaseModel):
    """分页出参。"""

    items: List[Any] = []
    total: int = 0
    page: int = 1
    page_size: int = 20
    pages: int = 0

    @classmethod
    def build(cls, items: List[Any], total: int, page: int, page_size: int):
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            pages=(total + page_size - 1) // page_size if page_size else 0,
        )


def paginate(db: Session, model: Type[T], params: PageParams, order_by=None) -> PageResult:
    """通用分页查询。"""
    stmt = select(model)
    if order_by is not None:
        stmt = stmt.order_by(order_by)
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    stmt = stmt.offset(params.offset).limit(params.page_size)
    return PageResult.build(list(db.scalars(stmt).all()), total, params.page, params.page_size)


def ok(data: Any = None, message: str = "操作成功", **extra) -> Dict[str, Any]:
    """统一成功响应。"""
    payload: Dict[str, Any] = {"code": 200, "message": message, "success": True}
    if data is not None:
        payload["data"] = data
    payload.update(extra)
    return payload


def fail(message: str = "操作失败", code: int = 500,
         **extra) -> Dict[str, Any]:
    """统一失败响应。success=False，前端应据此走错误分支而不是盲取 data。
    用于路由层包装 Agent 失败、业务校验失败等场景。
    """
    payload: Dict[str, Any] = {"code": code, "message": message, "success": False}
    payload.update(extra)
    return payload


def load_json(v: Optional[str]) -> Any:
    """把 SQLite Text 列中的 JSON 字符串还原为对象；非法 JSON 原样返回。

    SQLAlchemy 的 Text 列不能直接绑定 Python list，必须先JSON 序列化再
    存储，读取时统一走本函数还原。原先各路由模块各自定义 `_load`，
    现收敛到 utils 层共用。
    """
    if not v:
        return None
    try:
        return json.loads(v)
    except json.JSONDecodeError:
        return v


def dictify(obj: Any) -> Any:
    """将 SQLAlchemy 模型或列表转为普通 dict。"""
    from datetime import date, datetime as dt

    def conv(v):
        if isinstance(v, dt):
            return v.strftime("%Y-%m-%d %H:%M:%S")
        if isinstance(v, date):
            return v.strftime("%Y-%m-%d")
        return v

    if obj is None:
        return None
    if isinstance(obj, list):
        return [dictify(o) for o in obj]
    if hasattr(obj, "__table__"):
        return {c.name: conv(getattr(obj, c.name)) for c in obj.__table__.columns}
    return obj
