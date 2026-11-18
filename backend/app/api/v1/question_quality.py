"""Teacher-visible quality workbench, with audit-protected publishing."""
from fastapi import APIRouter, Depends

from app.api.deps import get_current_teacher
from app.core.database import get_db
from app.schemas.learning_ext import QualityPublish
from app.schemas.question_visual import VisualUpdate
from app.services import question_quality
from app.utils.common import ok

router = APIRouter(prefix="/question/quality", tags=["题库质量"])


@router.get("")
def inventory(subject_id: int = None, db=Depends(get_db), user=Depends(get_current_teacher)):
    return ok(question_quality.inventory(db, user, subject_id))


@router.post("/publish")
def publish(data: QualityPublish, db=Depends(get_db), user=Depends(get_current_teacher)):
    return ok(question_quality.publish(db, user, data.ids))


@router.put("/{question_id}/visual")
def visual(question_id: int, data: VisualUpdate, db=Depends(get_db), user=Depends(get_current_teacher)):
    return ok(question_quality.save_visual(db, user, question_id, data.visual))
