"""Readiness probes used by Docker and release health gates."""
import os
import tempfile

from sqlalchemy import text

from app.core.config import settings
from app.core.database import SessionLocal


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
