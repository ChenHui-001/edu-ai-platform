"""Staged learning assistance and teacher correction workflow."""
from fastapi import APIRouter, Depends

from app.api.deps import get_current_teacher, get_current_user, get_data_scope
from app.core.database import get_db
from app.schemas.learning_ext import FeedbackCreate, FeedbackReview, TutorAsk
from app.services import grounded_tutor
from app.utils.common import ok

router = APIRouter(prefix="/learning/tutor", tags=["有依据的答疑"])


@router.post("")
def ask(data: TutorAsk, db=Depends(get_db), user=Depends(get_current_user)):
    return ok(grounded_tutor.tutor_response(db, user, data.question_id, data.stage))


@router.post("/feedback")
def feedback(data: FeedbackCreate, db=Depends(get_db), user=Depends(get_current_user)):
    return ok(grounded_tutor.create_feedback(db, user, data))


@router.get("/feedback")
def feedback_list(db=Depends(get_db), user=Depends(get_current_teacher), scope=Depends(get_data_scope)):
    return ok({"items": grounded_tutor.feedback_list(db, user, scope)})


@router.put("/feedback/{feedback_id}")
def review(feedback_id: int, data: FeedbackReview, db=Depends(get_db),
           user=Depends(get_current_teacher), scope=Depends(get_data_scope)):
    return ok(grounded_tutor.review_feedback(db, user, scope, feedback_id, data.correction))
