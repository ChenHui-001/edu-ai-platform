"""学习中心路由包（/api/v1/learning/*）。

原 1333 行的 api/v1/grading.py 同时承载批改中心与学习中心，现拆分为：
  - api/v1/grading.py批改中心（/grading/*）
  - api/v1/learning/notes.py         学习笔记
  - api/v1/learning/wrongbook.py     错题本
  - api/v1/learning/review.py        智能复习 + 随机练习
  - api/v1/learning/tools.py         收藏 / 组卷 / 目标 / 路径 / 闪卡

**include顺序敏感**：静态路由必须早于同前缀参数路由注册，例如
`/practice/history` 需在 `/practice/{task_id}` 之前，否则返回 422。
下方顺序与拆分前完全一致，切勿随意调换。
"""
from fastapi import APIRouter

from . import notes, review, tools, wrongbook

learning_router = APIRouter(prefix="/learning", tags=["学习中心"])

# 顺序与拆分前保持一致，切勿调换
learning_router.include_router(notes.router)
learning_router.include_router(wrongbook.router)
learning_router.include_router(review.router)
learning_router.include_router(tools.router)

__all__ = ["learning_router"]
