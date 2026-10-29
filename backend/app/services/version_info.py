"""版本信息：版本号 / 构建号 / 最后更新时间。

## 三个字段各自的真源

- **版本号**：镜像内 `VERSION` 文件（CI 由 `VERSION` 注入 `APP_VERSION`），
  `settings.APP_VERSION` 是第一顺位；`BUILD_INFO` 里也有同一份值。
- **构建号**：`BUILD_INFO` 的 `commit=`（CI 注入 `GITHUB_SHA` 短/全串）。
  只有版本号是**不够**的 —— `2.2.0` 可以构建十次、内容各不相同，必须能回答
  「这份部署到底出自哪个 commit」。
- **最后更新时间**：见下方「为什么要单独记时间戳」。

## 为什么要单独记「更新时间」而不是直接用构建时间/启动时间

`built_at` 是 CI 构建那一刻，`进程启动` 是容器被拉起的时刻，两者都不等于
「这个版本是什么时候上线的」：同一镜像反复重启会刷新启动时间，让人误以为
「又更新了」；而构建完成到真正部署之间可能隔几天。

因此维护一份**快照**（`sys_config.key = sys_version_snapshot`）：启动时比对
「本次运行的 版本号 + 构建号」与快照，**只有二者之一变化**才写入新的
`updated_at`。同版本重启不刷新 —— 用户看到的「最后更新时间」始终等于
「上一次真正换版本的时刻」。

## BUILD_INFO 从哪来

`Dockerfile` 两个阶段都会 `printf` 出 `/app/BUILD_INFO`（见构建溯源注释），
同时写 `org.opencontainers.image.revision` LABEL。本地开发（不走 Docker）
没有这个文件，按候选路径逐个探测，全都没有则退回 `unknown`，前端显示占位，
不报错。
"""
from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional

from loguru import logger
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.system import SysConfig
from app.utils.common import now_local

# 快照键：与业务配置（llm_* 等）区分开，category=system 且 is_public=True
# （版本信息不含敏感内容，教师/学生端也可能要在页脚读它）。
SNAPSHOT_KEY = "sys_version_snapshot"

_TIME_FMT = "%Y-%m-%d %H:%M:%S"

# 进程启动时刻：快照表为空（全新库、首次部署）且没有 build 时间时的兜底值。
# 不能用 now_local()：每次请求都算一次「现在」会让「最后更新时间」一直变。
_PROCESS_STARTED_AT = now_local()

# 解析结果进程内缓存：BUILD_INFO 在容器生命周期内不会变，每请求读磁盘没必要。
# 解析失败（文件不存在）**不缓存**，方便本地开发中途补上文件后立即生效。
_build_info_cache: Optional[Dict[str, str]] = None


def _candidate_paths() -> list[str]:
    """BUILD_INFO 候选路径：环境变量 > 容器内固定路径 > 仓库根 > 工作目录。"""
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    candidates = [
        os.environ.get("BUILD_INFO_FILE", "").strip(),
        "/app/BUILD_INFO",
        os.path.join(root, "BUILD_INFO"),
        os.path.abspath("BUILD_INFO"),
    ]
    seen: set[str] = set()
    ordered: list[str] = []
    for p in candidates:
        if p and p not in seen:
            seen.add(p)
            ordered.append(p)
    return ordered


def _clean(value: Any) -> str:
    """`unknown` / 空串 / None 统一视为「未知」。"""
    text = str(value or "").strip()
    if not text or text.lower() in ("unknown", "none", "null"):
        return ""
    return text


def _fmt_time(value: Any) -> str:
    """统一成 `YYYY-MM-DD HH:MM:SS`（服务端本地时区字符串，前端不做时区换算）。

    CI 传进来的 `BUILD_TIME` 是 `github.event.repository.pushed_at`，形如
    `2026-10-29T09:12:34Z`；直接回显会把 T/Z 带给用户，故在这里规整。
    """
    text = _clean(value)
    if not text:
        return ""
    text = text.replace("T", " ").replace("Z", "").strip()
    # 去掉毫秒与时区尾巴："2026-10-29 09:12:34.123456+00:00" → "2026-10-29 09:12:34"
    if "." in text:
        text = text.split(".", 1)[0]
    if "+" in text:
        text = text.split("+", 1)[0]
    # 形如 "2026-10-29 09:12:34 -05:00"：用空格分隔的时区后缀一并丢掉
    parts = text.split()
    if len(parts) >= 3:
        text = " ".join(parts[:2])
    return text[:19]


def read_build_info(*, force: bool = False) -> Dict[str, str]:
    """读取并解析 BUILD_INFO（`key=value` 逐行），失败返回空字段而不抛异常。"""
    global _build_info_cache
    if _build_info_cache is not None and not force:
        return _build_info_cache

    info: Dict[str, str] = {"version": "", "commit": "", "built_at": "", "_path": ""}
    for path in _candidate_paths():
        try:
            with open(path, encoding="utf-8") as fp:
                raw = fp.read()
        except OSError:
            continue
        for line in raw.splitlines():
            if "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            if key in ("version", "commit", "built_at"):
                info[key] = _clean(value)
        info["_path"] = path
        break

    if info["_path"]:
        _build_info_cache = info
    return info


def _identity() -> Dict[str, str]:
    """当前运行的版本标识（版本号 + 构建号 + 构建时间）。"""
    info = read_build_info()
    return {
        "version": info.get("version") or _clean(settings.APP_VERSION) or "dev",
        # commit 缺失时留空串，由调用方决定展示成 unknown / 本地开发
        "commit": info.get("commit") or "",
        "built_at": _fmt_time(info.get("built_at")),
    }


def short_build(commit: str, length: int = 7) -> str:
    """构建号展示形式：git short sha。"""
    text = _clean(commit)
    return text[:length] if text else ""


def read_snapshot(db: Optional[Session]) -> Optional[Dict[str, Any]]:
    """读取版本快照；不存在/损坏一律返回 None（不影响页面展示）。"""
    if db is None:
        return None
    try:
        row = db.scalar(select(SysConfig).where(SysConfig.key == SNAPSHOT_KEY))
    except Exception as exc:  # noqa: BLE001 表未建好/DB 抖动时不能拖垮 /system/version
        logger.warning(f"读取版本快照失败: {exc}")
        return None
    if row is None or not row.value:
        return None
    try:
        data = json.loads(row.value)
    except (TypeError, ValueError):
        logger.warning("版本快照内容不是合法 JSON，按未记录处理")
        return None
    return data if isinstance(data, dict) else None


def record_version_update(db: Session) -> Dict[str, Any]:
    """启动时调用：版本号或构建号变化才写入新的更新时间戳。

    返回 `{"changed": bool, "version": str, "updated_at": str, "prior_version": str}`。

    ## 为什么比较的是「版本号 + 构建号」而不是只比版本号

    补丁版本号不变、只换镜像（回滚、hotfix 重建）是常态；只比版本号会把这类
    更新当成「没变」，页面上仍显示几天前的旧时间，实际已经是新代码。

    ## 为什么 commit 为空时不参与比较

    本地开发/未注入 GIT_COMMIT 时 commit 恒为空串，参与比较也不会误判；
    但若从「有 commit 的镜像」退回「无 commit 的本地运行」，会误记一次更新。
    这属于可接受的噪声（单机开发环境），比「漏记真实更新」轻。
    """
    ident = _identity()
    prev = read_snapshot(db) or {}

    same_version = _clean(prev.get("version")) == ident["version"]
    same_build = _clean(prev.get("commit")) == _clean(ident["commit"])
    if prev and same_version and same_build:
        return {
            "changed": False,
            "version": ident["version"],
            "updated_at": _clean(prev.get("updated_at")),
            "prior_version": _clean(prev.get("prior_version")),
        }

    snapshot = {
        "version": ident["version"],
        "commit": ident["commit"],
        "built_at": ident["built_at"],
        "updated_at": now_local().strftime(_TIME_FMT),
        # 保留「上一版是什么」，便于在界面上提示「从 x.y.z 升级而来」
        "prior_version": _clean(prev.get("version")) if prev else "",
    }

    payload = json.dumps(snapshot, ensure_ascii=False)
    try:
        row = db.scalar(select(SysConfig).where(SysConfig.key == SNAPSHOT_KEY))
        if row is None:
            db.add(SysConfig(
                key=SNAPSHOT_KEY, value=payload, value_type="json",
                category="system", label="版本更新时间快照",
                description="系统自动维护：版本号或构建号变化时写入更新时间，勿手工编辑",
                is_public=True,
            ))
        else:
            row.value = payload
            row.value_type = "json"
            row.is_public = True
        db.commit()
    except Exception as exc:  # noqa: BLE001 记录失败只告警，绝不阻断启动
        db.rollback()
        logger.warning(f"写入版本更新时间失败: {exc}")
        return {
            "changed": False, "version": ident["version"],
            "updated_at": "", "prior_version": "",
        }

    return {
        "changed": True,
        "version": ident["version"],
        "updated_at": snapshot["updated_at"],
        "prior_version": snapshot["prior_version"],
    }


def version_payload(db: Optional[Session] = None) -> Dict[str, Any]:
    """对外展示用版本信息。

    `updated_source` 让前端能如实区分「系统记录的真实版本更新时间」与
    「回落值」，避免把构建时间当上线时间展示给用户：
    - `recorded`：快照命中的真实版本更新时间
    - `build`：快照缺失（首次部署尚未落库）时回落到镜像构建时间
    - `startup`：连构建时间都没有（本地开发）时回落到进程启动时间
    """
    ident = _identity()
    snapshot = read_snapshot(db) or {}

    updated_at = _clean(snapshot.get("updated_at"))
    if updated_at:
        source = "recorded"
    elif ident["built_at"]:
        updated_at, source = ident["built_at"], "build"
    else:
        updated_at = _PROCESS_STARTED_AT.strftime(_TIME_FMT)
        source = "startup"

    commit = ident["commit"]
    return {
        "app_name": settings.APP_NAME,
        "version": ident["version"],
        "build_number": short_build(commit),
        "commit": commit,
        "built_at": ident["built_at"],
        "updated_at": updated_at,
        "updated_source": source,
        "prior_version": _clean(snapshot.get("prior_version")),
        # 是否真的是容器镜像（有 BUILD_INFO）。本地开发时前端可据此弱化「构建号」
        "from_image": bool(read_build_info().get("_path")),
    }
