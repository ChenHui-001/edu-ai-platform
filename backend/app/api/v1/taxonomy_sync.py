"""Administrator upstream preview, synchronization and recovery."""
from fastapi import APIRouter, Depends

from app.api.deps import get_current_admin
from app.core.database import get_db
from app.schemas.learning_ext import SyncApply, SyncPreview
from app.services import taxonomy_sync
from app.utils.common import ok

router = APIRouter(prefix="/system/taxonomy-sync", tags=["上游同步"])


@router.get("")
def history(db=Depends(get_db), user=Depends(get_current_admin)):
    return ok({"items": taxonomy_sync.history(db)})


@router.post("/preview")
def preview(data: SyncPreview, db=Depends(get_db), user=Depends(get_current_admin)):
    return ok(taxonomy_sync.preview(db, user, data.ref))


@router.post("/apply")
def apply(data: SyncApply, db=Depends(get_db), user=Depends(get_current_admin)):
    return ok(taxonomy_sync.apply(db, user, data.preview_id))


@router.post("/{run_id}/restore")
def restore(run_id: int, db=Depends(get_db), user=Depends(get_current_admin)):
    return ok(taxonomy_sync.restore(db, user, run_id))
