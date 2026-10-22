"""API 路由汇总。"""
from fastapi import APIRouter

from app.api.v1 import (
    agent, attachment, auth, edu, grading, lesson, lesson_ai, logs, question, report,
    system, task,
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
# /lesson/ai/* 必须挂在这里：与教案 CRUD 同前缀，前端一处调用即可；
# 但独立成文件是因为它依赖 Agent + 异步任务，塞进 lesson.py 会让
# 那个纯 CRUD 文件混入 threading 与 LLM 依赖。
api_router.include_router(lesson_ai.router)
