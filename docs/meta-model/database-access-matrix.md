# 数据访问矩阵

- Output Language: zh-CN
- 状态: in-progress

分母来自 63 张物理表；当前记录服务级主访问能力，后续按功能逐表补齐。

| TBL ID | Physical Table | Owner | Main Access Path | Operations | Consumers | Evidence |
|---|---|---|---|---|---|---|
| TBL-sys-user | sys_user | backend | system.py/auth_service.py | R/C/U/D | 用户管理、认证、审批 | SQLAlchemy metadata + service calls |
| TBL-sys-role | sys_role | backend | system.py/init_db.py | R/C/U/D | 角色权限管理 | SQLAlchemy metadata |
| TBL-sys-permission | sys_permission | backend | init_db.py/system.py | R/C/U/D | 权限初始化、角色权限 | SQLAlchemy metadata |
| TBL-sys-user-role | sys_user_role | backend | init_db.py/system.py | R/C/U/D | 用户角色、权限计算 | SQLAlchemy metadata |
| TBL-sys-role-permission | sys_role_permission | backend | init_db.py/system.py | R/C/U/D | 角色权限授权 | SQLAlchemy metadata |
| TBL-sys-registration | sys_registration | backend | auth.py/auth_service.py | R/C/U/D | 注册审批、流程编排 | SQLAlchemy metadata |
| TBL-sys-config | sys_config | backend | ai_config_service.py/system.py | R/U/D | 运行配置、AI 配置 | SQLAlchemy metadata |
| TBL-sys-captcha | sys_captcha | backend | auth.py/security_cache.py | R/C/U/D | 登录验证码 | SQLAlchemy metadata |
| TBL-sys-revoked-token | sys_revoked_token | backend | auth_service.py/security.py | R/C/U/D | JWT 吊销 | SQLAlchemy metadata |
| TBL-sys-user-token-revocation | sys_user_token_revocation | backend | auth_service.py/security.py | R/C/U/D | 用户级吊销 | SQLAlchemy metadata |
| TBL-sys-rate-limit | sys_rate_limit | backend | core/rate_limit.py | R/C/U/D | 登录限流 | SQLAlchemy metadata |
| TBL-sys-reset-code | sys_reset_code | backend | auth.py/security_cache.py | R/C/U/D | 找回密码验证码 | SQLAlchemy metadata |
| TBL-sys-login-log | sys_login_log | backend | logger.py/logs.py | R/C/U/D | 登录审计与查询 | SQLAlchemy metadata |
| TBL-sys-operation-log | sys_operation_log | backend | middleware/audit.py/logs.py | R/C/U/D | 操作审计与查询 | SQLAlchemy metadata |
| TBL-sys-error-log | sys_error_log | backend | logger.py/exception.py/logs.py | R/C/U/D | 错误审计与查询 | SQLAlchemy metadata |
| TBL-sys-scheduled-job | sys_scheduled_job | backend | scheduler.py/logs.py/init_db.py | R/C/U/D | 定时任务管理 | SQLAlchemy metadata |
| TBL-sys-job-execution-log | sys_job_execution_log | backend | scheduler.py/task_jobs.py/logs.py | R/C/U/D | 任务执行记录 | SQLAlchemy metadata |
| TBL-sys-job-lock | sys_job_lock | backend | job_lock.py | R/C/U/D | 任务锁 | SQLAlchemy metadata |
| TBL-sys-llm-breaker | sys_llm_breaker | backend | llm_breaker.py/llm.py | R/C/U/D | LLM 熔断 | SQLAlchemy metadata |
| TBL-sys-attachment | sys_attachment | backend | attachment.py/knowledge.py/lesson.py | R/C/U/D | 附件管理 | SQLAlchemy metadata |
| TBL-sys-agent-call-log | sys_agent_call_log | backend | llm.py/agent.py | R/C/U/D | AI 调用审计 | SQLAlchemy metadata |
| TBL-sys-notification | sys_notification | backend | notification.py/system.py | R/C/U/D | 通知投递 | SQLAlchemy metadata |
| TBL-sys-notify-pref | sys_notify_pref | backend | system.py/notification.py | R/C/U/D | 通知偏好 | SQLAlchemy metadata |
| TBL-sys-agent-rate | sys_agent_rate | backend | rate_limit.py/llm.py | R/C/U/D | Agent 限流 | SQLAlchemy metadata |
| TBL-sys-agent-job | sys_agent_job | backend | agent_job_state.py/agent.py/export_job.py | R/C/U/D | 异步任务 | SQLAlchemy metadata |
| TBL-edu-grade | edu_grade | backend | edu.py/init_db.py | R/C/U/D | 年级管理 | SQLAlchemy metadata |
| TBL-edu-subject | edu_subject | backend | edu.py/init_db.py | R/C/U/D | 学科管理 | SQLAlchemy metadata |
| TBL-edu-class | edu_class | backend | edu.py/init_db.py | R/C/U/D | 班级管理 | SQLAlchemy metadata |
| TBL-edu-knowledge-point | edu_knowledge_point | backend | knowledge.py/taxonomy_sync.py | R/C/U/D | 知识点管理 | SQLAlchemy metadata |
| TBL-edu-teaching-assignment | edu_teaching_assignment | backend | edu.py/system.py | R/C/U/D | 任课关系 | SQLAlchemy metadata |
| TBL-edu-class-request | edu_class_request | backend | edu.py/flow_orchestration.py | R/C/U/D | 建班申请 | SQLAlchemy metadata |
| TBL-edu-question | edu_question | backend | question.py/question_ai.py | R/C/U/D | 题库管理 | SQLAlchemy metadata |
| TBL-edu-question-knowledge | edu_question_knowledge | backend | question.py/knowledge.py | R/C/U/D | 题目知识点关系 | SQLAlchemy metadata |
| TBL-edu-paper | edu_paper | backend | question.py/paper_compose*.py | R/C/U/D | 试卷管理 | SQLAlchemy metadata |
| TBL-edu-paper-item | edu_paper_item | backend | question.py/paper_compose*.py | R/C/U/D | 试卷题目 | SQLAlchemy metadata |
| TBL-edu-paper-share | edu_paper_share | backend | question.py/paper_compose*.py | R/C/U/D | 试卷共享 | SQLAlchemy metadata |
| TBL-edu-exam-standard | edu_exam_standard | backend | exam_standard.py/exam_structures.py | R/C/U/D | 命题标准 | SQLAlchemy metadata |
| TBL-edu-paper-version | edu_paper_version | backend | paper_version_service.py | R/C/U/D | 试卷版本 | SQLAlchemy metadata |
| TBL-edu-paper-favorite | edu_paper_favorite | backend | paper_compose.py | R/C/U/D | 试卷收藏 | SQLAlchemy metadata |
| TBL-edu-task | edu_task | backend | task.py/task_jobs.py | R/C/U/D | 作业考试 | SQLAlchemy metadata |
| TBL-edu-task-assignment | edu_task_assignment | backend | task.py/task_urge.py | R/C/U/D | 任务分配 | SQLAlchemy metadata |
| TBL-edu-submission | edu_submission | backend | task.py/grading.py | R/C/U/D | 作答提交 | SQLAlchemy metadata |
| TBL-edu-answer | edu_answer | backend | task.py/grading.py | R/C/U/D | 学生答案 | SQLAlchemy metadata |
| TBL-edu-wrong-question | edu_wrong_question | backend | grading_service.py/wrongbook.py | R/C/U/D | 错题本 | SQLAlchemy metadata |
| TBL-edu-knowledge-prerequisite | edu_knowledge_prerequisite | backend | knowledge_diagnosis.py/knowledge_graph.py | R/C/U/D | 先修关系 | SQLAlchemy metadata |
| TBL-edu-taxonomy-diagnosis-session | edu_taxonomy_diagnosis_session | backend | knowledge_diagnosis.py | R/C/U/D | 诊断会话 | SQLAlchemy metadata |
| TBL-edu-lesson-plan | edu_lesson_plan | backend | lesson.py/lesson_ai.py | R/C/U/D | 教案 | SQLAlchemy metadata |
| TBL-edu-lesson-stage | edu_lesson_stage | backend | lesson.py/lesson_ai.py | R/C/U/D | 教案环节 | SQLAlchemy metadata |
| TBL-edu-note | edu_note | backend | learning/notes.py | R/C/U/D | 笔记 | SQLAlchemy metadata |
| TBL-edu-knowledge-mastery | edu_knowledge_mastery | backend | grading_service.py/report.py | R/C/U/D | 掌握度 | SQLAlchemy metadata |
| TBL-edu-review-plan | edu_review_plan | backend | learning/review.py/task_jobs.py | R/C/U/D | 复习计划 | SQLAlchemy metadata |
| TBL-edu-study-record | edu_study_record | backend | learning/review.py/task_jobs.py | R/C/U/D | 学习记录 | SQLAlchemy metadata |
| TBL-edu-question-favorite | edu_question_favorite | backend | learning/tools.py | R/C/U/D | 题目收藏 | SQLAlchemy metadata |
| TBL-edu-study-goal | edu_study_goal | backend | learning/tools.py | R/C/U/D | 学习目标 | SQLAlchemy metadata |
| TBL-edu-study-checkin | edu_study_checkin | backend | learning/tools.py | R/C/U/D | 学习打卡 | SQLAlchemy metadata |
| TBL-edu-remediation-plan | edu_remediation_plan | backend | remediation.py | R/C/U/D | 补弱计划 | SQLAlchemy metadata |
| TBL-edu-tutor-feedback | edu_tutor_feedback | backend | grounded_tutor.py | R/C/U/D | 答疑反馈 | SQLAlchemy metadata |
| TBL-edu-taxonomy-sync-run | edu_taxonomy_sync_run | backend | taxonomy_sync.py | R/C/U/D | 同步运行 | SQLAlchemy metadata |
| TBL-edu-flow-definition | edu_flow_definition | backend | flow_engine.py/flow.py | R/C/U/D | 流程定义 | SQLAlchemy metadata |
| TBL-edu-flow-instance | edu_flow_instance | backend | flow_engine.py/flow.py | R/C/U/D | 流程实例 | SQLAlchemy metadata |
| TBL-edu-flow-task | edu_flow_task | backend | flow_engine.py/flow.py | R/C/U/D | 流程任务 | SQLAlchemy metadata |
| TBL-edu-flow-transfer | edu_flow_transfer | backend | flow_engine.py/flow.py | R/C/U/D | 转办记录 | SQLAlchemy metadata |
| TBL-edu-flow-history | edu_flow_history | backend | flow_engine.py/flow.py | R/C/U/D | 流程历史 | SQLAlchemy metadata |
