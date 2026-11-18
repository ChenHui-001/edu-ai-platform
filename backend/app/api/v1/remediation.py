"""Student-owned diagnosis-to-review learning plans."""
from fastapi import APIRouter, Depends

from app.api.deps import get_current_student_self
from app.core.database import get_db
from app.schemas.learning_ext import PlanCreate, QuizStart, QuizSubmit
from app.services import remediation
from app.utils.common import ok

router = APIRouter(prefix="/learning/remediation", tags=["补弱学习"])


@router.get("")
def plans(db=Depends(get_db), user=Depends(get_current_student_self)):
    return ok({"items": remediation.list_plans(db, user)})


@router.post("")
def create_plan(data: PlanCreate, db=Depends(get_db), user=Depends(get_current_student_self)):
    return ok(remediation.create_plan(db, user, data.diagnosis_id))


@router.get("/{plan_id}")
def plan(plan_id: int, db=Depends(get_db), user=Depends(get_current_student_self)):
    return ok(remediation.plan_out(remediation.get_plan(db, user, plan_id)))


@router.post("/{plan_id}/quizzes")
def start(plan_id: int, data: QuizStart, db=Depends(get_db), user=Depends(get_current_student_self)):
    return ok(remediation.start_quiz(db, user, plan_id, data))


@router.post("/{plan_id}/answers")
def answer(plan_id: int, data: QuizSubmit, db=Depends(get_db), user=Depends(get_current_student_self)):
    return ok(remediation.submit_quiz(db, user, plan_id, data))
