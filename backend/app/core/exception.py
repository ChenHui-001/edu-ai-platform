"""统一异常处理。"""
import re
from typing import Any, Dict

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.logger import get_logger

logger = get_logger("exception")


class AppException(Exception):
    """业务异常基类。"""

    def __init__(self, message: str, code: int = 400, detail: Any = None):
        self.message = message
        self.code = code
        self.detail = detail
        super().__init__(message)


class NotFoundException(AppException):
    def __init__(self, message: str = "资源不存在"):
        super().__init__(message, 404)


class PermissionException(AppException):
    def __init__(self, message: str = "无权限访问该资源"):
        super().__init__(message, 403)


class AuthException(AppException):
    def __init__(self, message: str = "认证失败或登录已过期"):
        super().__init__(message, 401)


class BusinessException(AppException):
    def __init__(self, message: str, detail: Any = None):
        super().__init__(message, 400, detail)


def _body(code: int, message: str, detail: Any = None) -> Dict[str, Any]:
    payload: Dict[str, Any] = {"code": code, "message": message, "success": code == 200}
    if detail is not None:
        payload["detail"] = detail
    return payload


# 表名 → 业务名称。冲突提示要说人话：把
# "UNIQUE constraint failed: edu_subject.grade_id, edu_subject.name"
# 翻译成「学科已存在相同的 grade_id、name」，用户才知道改哪个字段。
# 未登记的表回退显示原始表名，不会因为漏登记而丢失信息。
_TABLE_LABELS = {
    "edu_subject": "学科", "edu_grade": "年级", "edu_class": "班级",
    "edu_knowledge_point": "知识点", "edu_paper": "试卷", "edu_question": "题目",
    "edu_paper_share": "试卷分享", "edu_exam_standard": "命题标准",
    "edu_task": "作业/考试", "edu_task_assignment": "任务下发",
    "edu_teaching_assignment": "任课关系", "edu_question_knowledge": "题目知识点",
    "sys_user": "账号", "sys_role": "角色", "sys_user_role": "用户角色",
    "sys_role_permission": "角色权限", "sys_config": "系统配置",
}

# 列名 → 业务名称（只登记用户看得懂的那些，其余保留原列名）
_COL_LABELS = {
    "username": "登录账号", "name": "名称", "code": "编码",
    "grade_id": "年级", "subject_id": "学科", "class_id": "班级",
}


def _describe_integrity(exc: IntegrityError) -> str:
    """把数据库完整性错误翻译成用户能据此行动的中文提示。

    原来统一返回「数据冲突，请检查唯一性字段或关联数据」—— 比 500 好，
    但管理员看到后仍不知道该改哪个字段（是学科重名？还是账号重复？），
    只能反复试。这里按错误类型分流，尽量把表名/字段名带出来。

    同时兼容 SQLite（本项目）与 PostgreSQL（可切换）两种报错文案。
    """
    raw = str(getattr(exc, "orig", exc) or exc)

    # SQLite: UNIQUE constraint failed: t.a, t.b
    m = re.search(r"UNIQUE constraint failed:\s*([\w\.,\s]+)", raw)
    if m:
        cols = [c.strip() for c in m.group(1).split(",") if c.strip()]
        tables: list = []
        for c in cols:
            t = c.split(".")[0]
            if t not in tables:
                tables.append(t)
        label = "、".join(_TABLE_LABELS.get(t, t) for t in tables)
        fields = "、".join(_COL_LABELS.get(c.split(".")[-1], c.split(".")[-1]) for c in cols)
        return f"{label}已存在相同的{fields}，请修改后重试"

    # PostgreSQL: duplicate key value violates unique constraint "xxx"
    if "duplicate key value" in raw:
        return "已存在相同的记录（唯一字段冲突），请修改后重试"

    if "FOREIGN KEY" in raw:
        return "关联数据不存在或已被删除（外键约束失败），请刷新页面后重试"

    if "NOT NULL" in raw:
        m2 = re.search(r"NOT NULL constraint failed:\s*([\w\.]+)", raw)
        col = _COL_LABELS.get(m2.group(1).split(".")[-1], m2.group(1)) if m2 else "必填字段"
        return f"{col}不能为空"

    return "数据冲突，请检查唯一性字段或关联数据"


def register_exception_handlers(app: FastAPI) -> None:
    """注册全局异常处理器。"""

    @app.exception_handler(AppException)
    async def handle_app_exception(request: Request, exc: AppException):
        logger.warning(f"业务异常 {request.method} {request.url.path}: {exc.message}")
        return JSONResponse(
            status_code=exc.code, content=_body(exc.code, exc.message, exc.detail)
        )

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_exception(request: Request, exc: StarletteHTTPException):
        message = exc.detail if isinstance(exc.detail, str) else "请求失败"
        if exc.status_code == status.HTTP_401_UNAUTHORIZED:
            message = message or "认证失败或登录已过期"
        return JSONResponse(
            status_code=exc.status_code, content=_body(exc.status_code, message)
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation(request: Request, exc: RequestValidationError):
        errors = [
            {"field": ".".join(str(x) for x in e["loc"][1:]), "msg": e["msg"]}
            for e in exc.errors()
        ]
        logger.warning(f"参数校验失败 {request.url.path}: {errors}")
        return JSONResponse(
            status_code=422, content=_body(422, "请求参数校验失败", errors)
        )

    @app.exception_handler(IntegrityError)
    async def handle_integrity(request: Request, exc: IntegrityError):
        logger.error(f"数据完整性错误 {request.url.path}: {exc}")
        return JSONResponse(
            status_code=400, content=_body(400, _describe_integrity(exc))
        )

    @app.exception_handler(SQLAlchemyError)
    async def handle_db(request: Request, exc: SQLAlchemyError):
        logger.error(f"数据库错误 {request.url.path}: {exc}")
        return JSONResponse(status_code=500, content=_body(500, "数据库操作失败"))

    @app.exception_handler(Exception)
    async def handle_unknown(request: Request, exc: Exception):
        logger.opt(exception=True).error(f"未捕获异常 {request.method} {request.url.path}: {exc}")
        return JSONResponse(
            status_code=500,
            content=_body(500, "服务器内部错误，请联系管理员"),
        )
