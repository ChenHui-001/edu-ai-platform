"""审计中间件：自动记录操作日志与错误日志。"""
import json
import time
from typing import Any, Callable, Dict

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.logger import get_logger
from app.models import ErrorLog, OperationLog

logger = get_logger("audit")

SKIP_PATHS = {"/api/v1/health", "/docs", "/openapi.json", "/favicon.ico", "/"}
SKIP_PREFIX = ("/static", "/assets", "/health")


def _module_from_path(path: str) -> str:
    """从请求路径推断业务模块。"""
    parts = [p for p in path.split("/") if p and p.isdigit() is False]
    parts = [p for p in parts if p != "api" and p != "v1"]
    return parts[0] if parts else "system"


def _jsonable(obj: Any) -> str:
    try:
        return json.dumps(obj, ensure_ascii=False, default=str)[:2000]
    except (TypeError, ValueError):
        return str(obj)[:2000]


class AuditMiddleware(BaseHTTPMiddleware):
    """请求级审计：记录操作日志、错误日志、性能耗时。"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        path = request.url.path
        if path in SKIP_PATHS or path.startswith(SKIP_PREFIX):
            return await call_next(request)

        start = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception as exc:  # 交给全局异常处理器，这里只记录
            await self._log(request, 500, time.perf_counter() - start, error=str(exc))
            raise

        duration_ms = int((time.perf_counter() - start) * 1000)
        if response.status_code >= 500:
            await self._log(request, response.status_code, duration_ms, error="服务端异常")
        else:
            await self._log(request, response.status_code, duration_ms)
        response.headers["X-Process-Time"] = str(duration_ms)
        return response

    async def _log(
        self, request: Request, status_code: int, duration_ms: int, error: str = ""
    ) -> None:
        if not settings.LOG_TO_DB:
            return

        try:
            user = getattr(request.state, "user", None)
            user_id = getattr(user, "id", None)
            username = getattr(user, "username", None)

            params: Dict[str, Any] = dict(request.query_params)
            body: Any = None
            if request.method in ("POST", "PUT", "PATCH", "DELETE"):
                raw = await request.body()
                if raw:
                    try:
                        body = json.loads(raw)
                        if isinstance(body, dict):
                            for k in ("password", "new_password", "old_password"):
                                if k in body:
                                    body[k] = "******"
                            body = {
                                k: v for k, v in body.items()
                                if k not in ("content", "stem", "analysis")
                            }
                    except (ValueError, UnicodeDecodeError):
                        body = "<binary>"

            ip = request.headers.get("X-Forwarded-For", "").split(",")[0].strip() or (
                request.client.host if request.client else ""
            )
            success = status_code < 400
            action = f"{request.method} {request.url.path}"

            with SessionLocal() as db:
                db.add(
                    OperationLog(
                        user_id=user_id, username=username,
                        module=_module_from_path(request.url.path),
                        action=action, method=request.method,
                        path=request.url.path, ip=ip,
                        params=_jsonable({**params, **({"body": body} if body else {})}),
                        result=str(status_code), status="success" if success else "failed",
                        error_msg=error or None, duration_ms=duration_ms,
                    )
                )
                if status_code >= 500:
                    db.add(
                        ErrorLog(
                            level="ERROR", module=_module_from_path(request.url.path),
                            path=request.url.path, message=error or "服务器内部错误",
                            user_id=user_id,
                        )
                    )
                db.commit()
        except Exception as exc:  # 审计失败不影响主流程
            logger.warning(f"审计日志写入失败: {exc}")
