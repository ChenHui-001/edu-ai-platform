"""Teacher-visible quality workbench, with audit-protected publishing."""
from fastapi import APIRouter, Depends, Query

from app.api.deps import get_current_teacher
from app.core.database import get_db
from app.schemas.learning_ext import QualityPublish
from app.schemas.question_visual import VisualUpdate
from app.services import question_quality
from app.utils.common import ok

router = APIRouter(prefix="/question/quality", tags=["题库质量"])


@router.get("")
def inventory(subject_id: int = None, page: int = Query(1, ge=1),
              page_size: int = Query(50, ge=1, le=100), keyword: str | None = None,
              only_issues: bool = False, db=Depends(get_db),
              user=Depends(get_current_teacher)):
    return ok(question_quality.inventory(
        db, user, subject_id, page, page_size, keyword, only_issues))


@router.post("/publish")
def publish(data: QualityPublish, db=Depends(get_db), user=Depends(get_current_teacher)):
    return ok(question_quality.publish(db, user, data.ids))


@router.put("/{question_id}/visual")
def visual(question_id: int, data: VisualUpdate, db=Depends(get_db), user=Depends(get_current_teacher)):
    return ok(question_quality.save_visual(db, user, question_id, data.visual))
