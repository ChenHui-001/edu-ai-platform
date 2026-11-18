"""Authorized teacher class graph and targeted assignments."""
from fastapi import APIRouter, Depends, Query

from app.api.deps import get_current_teacher, get_data_scope
from app.core.database import get_db
from app.schemas.learning_ext import ClassAssignment
from app.services.teaching_graph import assign_homework, class_graph
from app.utils.common import ok

router = APIRouter(prefix="/teaching/graph", tags=["班级知识图谱"])


@router.get("")
def graph(class_id: int = Query(gt=0), subject_id: int = Query(gt=0),
          db=Depends(get_db), user=Depends(get_current_teacher), scope=Depends(get_data_scope)):
    return ok(class_graph(db, user, scope, class_id, subject_id))


@router.post("/assign")
def assign(data: ClassAssignment, db=Depends(get_db),
           user=Depends(get_current_teacher), scope=Depends(get_data_scope)):
    return ok(assign_homework(db, user, scope, data))
