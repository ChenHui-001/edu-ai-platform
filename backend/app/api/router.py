"""API 路由汇总。"""
from fastapi import APIRouter

from app.api.v1 import (
    agent, attachment, auth, edu, exam_standard, grading, knowledge, knowledge_ai,
    lesson, lesson_ai, logs, paper_ai, paper_compose, question, question_ai, report,
    system, task,
)

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(system.router)
api_router.include_router(edu.router)
# 知识点 V2 独立成文件（树/批量/导入导出），与 edu 同为 /edu 前缀。
# 旧的 /edu/knowledge* 路由已从 edu.py 移除，这里不会产生重复注册。
api_router.include_router(knowledge.router)
# 知识点 AI（生成/补全）：独立文件，前缀 /edu/knowledge/ai。
# 权限/scope 直接复用 knowledge.py 的 helper，避免两套权限判定漂移。
api_router.include_router(knowledge_ai.router)
api_router.include_router(question.router)
# 题库 AI（变式/补全/质检）：独立文件，前缀 /question/questions/ai。
# 只预览不落库，不修改 question.py 的既有 CRUD/LLM 行为。
api_router.include_router(question_ai.router)
# 试卷 AI（分析/推荐）：独立文件，路径 /question/papers/{paper_id}/ai/*。
# 只读接口，不修改 question.py 的 paper CRUD/导出/LLM 行为。
api_router.include_router(paper_ai.router)
# 标准组卷 V3：命题标准配置 + 双模式组卷 + 预览编辑 + 导出 + 共享。
# 全部新增路径，不改动 question.py 既有 CRUD 的契约与行为。
api_router.include_router(exam_standard.router)
api_router.include_router(paper_compose.router)
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
