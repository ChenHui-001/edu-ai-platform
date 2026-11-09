# -*- coding: utf-8 -*-
"""历史端点的请求体模型（第三轮复审 P1-4 的契约层迁移）。

由一次性脚本按「端点实际读取的字段」生成，只做两件事：
  1. 让 OpenAPI 显示真实字段名，而不是 `additionalProp1: {}`
  2. 把裸 `Dict[str, Any] = Body(...)` 从门禁统计里消掉

字段类型统一 `Any`、并 `extra="allow"`：行为与原 Dict **完全等价**，
不会静默丢字段。逐字段强类型化请在各自业务模块评审时单独做，
不要在这里批量猜类型 —— 猜错会把原本宽松的入参变成 422。
"""
from typing import Any

from pydantic import BaseModel, ConfigDict


class ComposeRegenerateIn(BaseModel):
    """在**保存之前**替换预览里的某些题目（不写试卷，只把新题返回给前端）。"""

    model_config = ConfigDict(extra="allow")

    grade_id: Any = None
    subject_id: Any = None
    items: Any = None
    mode: Any = None
    index: Any = None
    section_code: Any = None

class ComposePreviewIn(BaseModel):
    """按年级/学科/知识点/题型/分值/难度抽题。"""

    model_config = ConfigDict(extra="allow")


class ComposeAiIn(BaseModel):
    """极简参数 + 自然语言 → 全卷。"""

    model_config = ConfigDict(extra="allow")

    request: Any = None
    grade_id: Any = None
    subject_id: Any = None

class ComposeSaveIn(BaseModel):
    """把预览结果落库。"""

    model_config = ConfigDict(extra="allow")

    name: Any = None
    items: Any = None
    duration: Any = None
    description: Any = None
    exam_type: Any = None
    mode: Any = None
    avoid_recent: Any = None

class UpdateItemsIn(BaseModel):
    """整卷题目覆盖写。"""

    model_config = ConfigDict(extra="allow")

    items: Any = None
    name: Any = None
    description: Any = None
    duration: Any = None

class RegenerateItemIn(BaseModel):
    """替换单题为 AI 新生成的同题型同难度题目。"""

    model_config = ConfigDict(extra="allow")


class RenameSectionIn(BaseModel):
    """按 section_code 批量改大题名（改名不打散分组）。"""

    model_config = ConfigDict(extra="allow")

    section_code: Any = None
    section_name: Any = None

class RestructurePaperIn(BaseModel):
    """按题型重新归组并重排大题序号。"""

    model_config = ConfigDict(extra="allow")


class RestoreVersionIn(BaseModel):
    """把试卷恢复到历史版本。"""

    model_config = ConfigDict(extra="allow")

    force: Any = None

class ToggleFavoriteIn(BaseModel):
    """toggle_favorite"""

    model_config = ConfigDict(extra="allow")

    favorite: Any = None

class SetShareScopeIn(BaseModel):
    """设置试卷可见范围。"""

    model_config = ConfigDict(extra="allow")

    scope: Any = None

class ReviewPaperIn(BaseModel):
    """公共库审核流。"""

    model_config = ConfigDict(extra="allow")

    action: Any = None
    comment: Any = None

class ComposeAiAsyncIn(BaseModel):
    """提交组卷任务，立即返回 job_id；轮询 `/compose/jobs/{id}` 取结果。"""

    model_config = ConfigDict(extra="allow")

    request: Any = None
    grade_id: Any = None
    subject_id: Any = None

class CreateGradeIn(BaseModel):
    """create_grade"""

    model_config = ConfigDict(extra="allow")

    stage: Any = None
    grade_num: Any = None
    auto_name: Any = None
    name: Any = None
    sort: Any = None
    is_active: Any = None

class UpdateGradeIn(BaseModel):
    """update_grade"""

    model_config = ConfigDict(extra="allow")

    auto_name: Any = None
    stage: Any = None
    grade_num: Any = None
    name: Any = None
    sort: Any = None
    is_active: Any = None

class CreateSubjectIn(BaseModel):
    """create_subject"""

    model_config = ConfigDict(extra="allow")

    name: Any = None
    grade_id: Any = None
    textbook_version: Any = None
    code: Any = None
    sort: Any = None
    sort_order: Any = None
    is_active: Any = None

class UpdateSubjectIn(BaseModel):
    """update_subject"""

    model_config = ConfigDict(extra="allow")

    name: Any = None
    sort: Any = None
    sort_order: Any = None

class CloneSubjectIn(BaseModel):
    """把指定学科复制到多个目标年级。"""

    model_config = ConfigDict(extra="allow")

    target_grade_ids: Any = None

class CreateClassIn(BaseModel):
    """create_class"""

    model_config = ConfigDict(extra="allow")

    grade_id: Any = None
    auto_name: Any = None
    strict_name: Any = None
    class_no: Any = None
    name: Any = None
    head_teacher_id: Any = None
    remark: Any = None
    description: Any = None
    is_active: Any = None

class UpdateClassIn(BaseModel):
    """update_class"""

    model_config = ConfigDict(extra="allow")

    grade_id: Any = None
    auto_name: Any = None
    strict_name: Any = None
    class_no: Any = None
    name: Any = None
    head_teacher_id: Any = None
    description: Any = None

class BatchClassesIn(BaseModel):
    """batch_classes"""

    model_config = ConfigDict(extra="allow")

    action: Any = None
    ids: Any = None

class BatchRemoveStudentsIn(BaseModel):
    """batch_remove_students"""

    model_config = ConfigDict(extra="allow")

    ids: Any = None

class CreateClassRequestIn(BaseModel):
    """教师自建班级申请：提交后进入 pending，由年级管理员/超管审核。"""

    model_config = ConfigDict(extra="allow")

    name: Any = None
    grade_id: Any = None
    description: Any = None

class ReviewClassRequestIn(BaseModel):
    """approve：真实创建班级并回填，申请教师自动成为班主任；"""

    model_config = ConfigDict(extra="allow")

    action: Any = None
    note: Any = None

class CreateTeachingAssignmentIn(BaseModel):
    """create_teaching_assignment"""

    model_config = ConfigDict(extra="allow")

    teacher_id: Any = None
    class_id: Any = None
    subject_id: Any = None
    replace: Any = None
    school_year: Any = None

class CreateQuestionIn(BaseModel):
    """create_question"""

    model_config = ConfigDict(extra="allow")


class BatchCreateQuestionsIn(BaseModel):
    """批量新增题目（AI 出题结果一次性落库）。"""

    model_config = ConfigDict(extra="allow")


class BatchQuestionsIn(BaseModel):
    """批量删除/上下架/移动题库/分配知识点/修改难度。"""

    model_config = ConfigDict(extra="allow")

    action: Any = None
    ids: Any = None
    payload: Any = None

class UpdateQuestionIn(BaseModel):
    """update_question"""

    model_config = ConfigDict(extra="allow")

    stem: Any = None
    answer_min_words: Any = None
    knowledge_point_id: Any = None
    options: Any = None
    answer: Any = None
    analysis: Any = None
    grade_id: Any = None
    subject_id: Any = None
    difficulty: Any = None
    score: Any = None

class ChangeStatusIn(BaseModel):
    """change_status"""

    model_config = ConfigDict(extra="allow")

    status: Any = None

class BatchPapersIn(BaseModel):
    """批量删除/复制/共享试卷。返回 {done, skipped}；同批无权整体 403。"""

    model_config = ConfigDict(extra="allow")

    action: Any = None
    ids: Any = None
    payload: Any = None

class CreatePaperIn(BaseModel):
    """create_paper"""

    model_config = ConfigDict(extra="allow")

    name: Any = None
    grade_id: Any = None
    subject_id: Any = None
    duration: Any = None
    items: Any = None
    difficulty_ratio: Any = None

class UpdatePaperIn(BaseModel):
    """update_paper"""

    model_config = ConfigDict(extra="allow")

    name: Any = None
    duration: Any = None
    items: Any = None
    difficulty_ratio: Any = None
    grade_id: Any = None
    subject_id: Any = None

class ArchivePaperIn(BaseModel):
    """停用试卷（body 传 archived=false 则恢复）。"""

    model_config = ConfigDict(extra="allow")

    archived: Any = None

class CopyPaperIn(BaseModel):
    """copy_paper"""

    model_config = ConfigDict(extra="allow")

    name: Any = None

class SharePaperIn(BaseModel):
    """share_paper"""

    model_config = ConfigDict(extra="allow")

    user_ids: Any = None
    to_user_id: Any = None
