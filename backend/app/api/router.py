"""API 路由汇总。"""
from fastapi import APIRouter

from app.api.v1 import (
    agent, attachment, auth, edu, grading, lesson, logs, question, report, system, task,
)

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(system.router)
api_router.include_router(edu.router)
api_router.include_router(question.router)
api_router.include_router(task.router)
api_router.include_router(grading.grading_router)
api_router.include_router(grading.learning_router)
api_router.include_router(agent.router)
api_router.include_router(report.router)
api_router.include_router(logs.router)
api_router.include_router(logs.jobs_router)
api_router.include_router(attachment.router)
api_router.include_router(lesson.router)
