"""分页、CRUD 基类、响应封装等通用工具。"""
import json
from datetime import datetime, timezone
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar

from fastapi import Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings

T = TypeVar("T")


def today_str() -> str:
    """本地时区的当天日期串（YYYY-MM-DD）。

    打卡 / 复习计划 / 学习目标这类「今天」语义必须按用户所在时区算：
    utcnow() 是 UTC，北京时间 0:00-8:00 期间仍是"昨天"，会把打卡
    日历与复习计划整体错位 8 小时。容器与开发机 TZ 均为 Asia/Shanghai，
    datetime.now() 即北京时间。
    """
    return datetime.now().strftime("%Y-%m-%d")


def utcnow() -> datetime:
    """带时区的当前时间（SQLite 不存时区，这里统一 naive UTC）。"""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class ORMBase(BaseModel):
    """Pydantic ORM 序列化基类。"""

    model_config = ConfigDict(from_attributes=True)


class PageParams(BaseModel):
    """分页入参。"""

    page: int = Query(1, ge=1, description="页码，从 1 开始")
    page_size: int = Query(
        settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"
    )

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


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
