"""Readiness probes used by Docker and release health gates."""
import os
import tempfile

from sqlalchemy import text

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.db_migrations import MIGRATION_COLUMNS


def readiness_status():
    checks = {}
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
            db.execute(text("SELECT id FROM sys_user LIMIT 1"))
            db.execute(text("SELECT id FROM edu_remediation_plan LIMIT 1"))
            db.execute(text("SELECT id FROM edu_tutor_feedback LIMIT 1"))
            db.execute(text("SELECT id FROM edu_taxonomy_sync_run LIMIT 1"))
        checks["database"] = True
    except Exception:
        checks["database"] = False
    checks["schema"] = _schema_ok()
    for key, path in (("uploads", settings.UPLOAD_DIR),
                      ("exports", settings.EXPORT_DIR), ("logs", settings.LOG_DIR)):
        try:
            if not os.path.isdir(path):
                raise OSError("missing directory")
            with tempfile.TemporaryFile(dir=path) as probe:
                probe.write(b"ready")
                probe.flush()
            checks[key] = os.access(path, os.R_OK)
        except OSError:
            checks[key] = False
    return {"ready": all(checks.values()), "checks": checks}


def _schema_ok() -> bool:
    """补列清单里的每一项都必须真的存在——否则查询即 500，宁可 readiness 先红。"""
    if not settings.DATABASE_URL.startswith("sqlite"):
        return True
    try:
        with SessionLocal() as db:
            columns = {}
            for table, column, _ddl in MIGRATION_COLUMNS:
                if table not in columns:
                    rows = db.execute(text(f"PRAGMA table_info({table})")).fetchall()
                    columns[table] = {row[1] for row in rows}
                present = columns[table]
                if present and column not in present:
                    return False
        return True
    except Exception:
        return False
