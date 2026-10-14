"""统一异常处理。"""
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
            status_code=400, content=_body(400, "数据冲突，请检查唯一性字段或关联数据")
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
