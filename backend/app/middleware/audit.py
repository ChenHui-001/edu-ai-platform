"""审计中间件：自动记录操作日志与错误日志。"""
import json
import time
from typing import Any, Callable, Dict

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.api.deps import get_client_ip
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


# 审计日志落库前的脱敏关键字：按 key 递归匹配，覆盖 llm_api_key、
# smtp_password、Authorization、refresh_token 等（原先只认 password 三个键，
# AI 配置里的 llm_api_key 会以明文写进操作日志，且 grade_admin 可读取/导出）。
_SENSITIVE_KEY_MARKS = (
    "password", "passwd", "secret", "token", "api_key", "apikey",
    "authorization", "credential",
)
# 这些字段虽含 token 字样但只是类型说明，不需要脱敏
_SAFE_KEYS = {"token_type"}
# 大字段不落审计日志，避免日志表膨胀
_IGNORED_BODY_KEYS = {"content", "stem", "analysis"}

# 必须留痕的读接口特征。导出与下载是数据外流风险最高、却最需要事后追溯
# 的动作（谁在什么时候导走了哪个班的学生名单），因此不受「GET 不记日志」
# 的写放大优化豁免。用路径特征而不是端点清单，新增导出接口自动纳入。
_AUDITED_READ_MARKERS = ("/export", "/download")


def _redact(value: Any) -> Any:
    """递归脱敏：命中敏感关键字的键统一替换为 ******。"""
    if isinstance(value, dict):
        out = {}
        for k, v in value.items():
            key = str(k)
            if key.lower() not in _SAFE_KEYS and any(
                    m in key.lower() for m in _SENSITIVE_KEY_MARKS):
                out[k] = "******"
            else:
                out[k] = _redact(v)
        return out
    if isinstance(value, (list, tuple)):
        return [_redact(v) for v in value]
    return value


class AuditMiddleware(BaseHTTPMiddleware):
    """请求级审计：记录操作日志、错误日志、性能耗时。"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        path = request.url.path
        if path in SKIP_PATHS or path.startswith(SKIP_PREFIX):
            return await call_next(request)

        start = time.perf_counter()

        # ⚠️ 请求体必须在 `call_next` **之前**读取。
        # BaseHTTPMiddleware 用 `_CachedRequest` 包装 request：只有在 dispatch 里
        # 调用过 body()/stream() 之后，它才会把读到的内容缓存下来喂给下游 app。
        # 原实现在 call_next 返回**之后**才 `await request.body()`，此时下游端点
        # 已经把流消费完毕（`_wrapped_rcv_consumed=True`），再次读取必定抛
        # `RuntimeError: Stream consumed` —— 而异常被 `_log` 的 except 吞掉，
        # 表现为「所有 POST/PUT/PATCH/DELETE 的操作日志从未写进库」，
        # 只有 GET 的日志能存下来（GET 无 body 不触发该分支）。
        raw_body = b""
        ctype = (request.headers.get("content-type") or "").lower()
        # 只缓存 JSON 体：multipart 文件上传若整段读进内存会直接撑爆
        # 大附件场景，而审计日志本来也不记录二进制内容。
        if request.method in ("POST", "PUT", "PATCH", "DELETE") and (
            "application/json" in ctype or ctype == ""
        ):
            try:
                raw_body = await request.body()
            except Exception as exc:  # noqa: BLE001
                logger.warning(f"读取请求体失败（审计降级）: {exc}")
                raw_body = b""

        try:
            response = await call_next(request)
        except Exception as exc:  # 交给全局异常处理器，这里只记录
            await self._log(
                request, 500, time.perf_counter() - start,
                error=str(exc), raw_body=raw_body,
            )
            raise

        duration_ms = int((time.perf_counter() - start) * 1000)
        # 读接口默认不写操作日志：日志只用于「谁改了什么」的审计追溯，
        # 而 GET（尤其是前端轮询 /agent/status、通知列表）按请求写库会
        # 在 SQLite 单写者下形成写放大；5xx 仍要落错误日志便于排查。
        #
        # 但「导出/下载」必须例外：这两种 GET 恰是**数据外流风险最高**的动作
        # （班级学生 CSV、成绩、操作日志、错题、附件原件…），按原实现它们
        # 是唯一一类完全不记录的操作 —— 事后无法回答「谁在什么时候导走了
        # 哪个班的名单」。导出本身低频，写放大可忽略。
        # 用路径特征匹配而非逐个列端点：新增导出接口会自动纳入。
        if request.method in ("GET", "HEAD", "OPTIONS") and response.status_code < 500:
            response.headers["X-Process-Time"] = str(duration_ms)
            if any(m in request.url.path for m in _AUDITED_READ_MARKERS):
                await self._log(request, response.status_code, duration_ms)
            return response
        if response.status_code >= 500:
            await self._log(
                request, response.status_code, duration_ms,
                error="服务端异常", raw_body=raw_body,
            )
        else:
            await self._log(
                request, response.status_code, duration_ms, raw_body=raw_body,
            )
        response.headers["X-Process-Time"] = str(duration_ms)
        return response

    async def _log(
        self, request: Request, status_code: int, duration_ms: int,
        error: str = "", raw_body: bytes = b"",
    ) -> None:
        if not settings.LOG_TO_DB:
            return

        try:
            user = getattr(request.state, "user", None)
            user_id = getattr(user, "id", None)
            username = getattr(user, "username", None)

            params: Dict[str, Any] = _redact(dict(request.query_params))
            body: Any = None
            if raw_body:
                try:
                    body = _redact(json.loads(raw_body))
                    if isinstance(body, dict):
                        body = {
                            k: v for k, v in body.items()
                            if k not in _IGNORED_BODY_KEYS
                        }
                except (ValueError, UnicodeDecodeError):
                    body = "<binary>"

            # 与 deps.get_client_ip 共用同一份取值逻辑：此处原先又自己写了
            # 一遍 `X-Forwarded-For.split(",")[0]`，取到的正是客户端自填值，
            # 审计里的 IP 因此可被任意伪造（改 deps 而不改这里等于没修）。
            ip = get_client_ip(request)
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
