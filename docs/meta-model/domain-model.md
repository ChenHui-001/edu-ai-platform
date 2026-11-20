# 领域对象索引

- Output Language: zh-CN
- Status: in-progress
- Object Count: 63

## OBJ-agentcalllog - AgentCallLog
- ID: OBJ-agentcalllog
- 类别: entity
- 所有者: backend
- 业务或契约含义: AgentCallLog
- 字段摘要或字段表: id, agent_name, user_id, input_text, output_text, input_tokens, output_tokens, duration_ms, status, error_msg, is_fallback, biz_type, biz_id, created_at
- 生命周期/状态: CRUD/status
- 映射物理表/接口: TBL-sys-agent-call-log
- 核心功能: unknown
- 外部消费者: service layer
- 代码落点: backend/app/models/ops.py

## OBJ-agentjob - AgentJob
- ID: OBJ-agentjob
- 类别: entity
- 所有者: backend
- 业务或契约含义: AgentJob
- 字段摘要或字段表: id, user_id, agent, status, progress, stage, params, result, error, cancel_requested, created_at, started_at, finished_at
- 生命周期/状态: CRUD/status
- 映射物理表/接口: TBL-sys-agent-job
- 核心功能: unknown
- 外部消费者: service layer
- 代码落点: backend/app/models/ops.py

## OBJ-agentrate - AgentRate
- ID: OBJ-agentrate
- 类别: entity
- 所有者: backend
- 业务或契约含义: AgentRate
- 字段摘要或字段表: user_id, window_minute, count, updated_at
- 生命周期/状态: CRUD/status
- 映射物理表/接口: TBL-sys-agent-rate
- 核心功能: unknown
- 外部消费者: service layer
- 代码落点: backend/app/models/ops.py

## OBJ-answer - Answer
- ID: OBJ-answer
- 类别: entity
- 所有者: backend
- 业务或契约含义: Answer
- 字段摘要或字段表: id, submission_id, paper_item_id, question_id, content, is_correct, score, full_score, grader_type, ai_comment, ai_error_points, teacher_comment
- 生命周期/状态: CRUD/status
- 映射物理表/接口: TBL-edu-answer
- 核心功能: unknown
- 外部消费者: service layer
- 代码落点: backend/app/models/task.py

## OBJ-attachment - Attachment
- ID: OBJ-attachment
- 类别: entity
- 所有者: backend
- 业务或契约含义: Attachment
- 字段摘要或字段表: id, filename, stored_name, file_path, file_size, file_type, category, biz_type, biz_id, uploader_id, download_count, is_temp, visible_to_student, created_at
- 生命周期/状态: CRUD/status
- 映射物理表/接口: TBL-sys-attachment
- 核心功能: unknown
- 外部消费者: service layer
- 代码落点: backend/app/models/ops.py

## OBJ-captcha - Captcha
- ID: OBJ-captcha
- 类别: entity
- 所有者: backend
- 业务或契约含义: Captcha
- 字段摘要或字段表: key, text, expire_at, created_at
- 生命周期/状态: CRUD/status
- 映射物理表/接口: TBL-sys-captcha
- 核心功能: unknown
- 外部消费者: service layer
- 代码落点: backend/app/models/security_cache.py

## OBJ-class - Class
- ID: OBJ-class
- 类别: entity
- 所有者: backend
- 业务或契约含义: Class
- 字段摘要或字段表: id, name, grade_id, head_teacher_id, is_active, remark, created_at
- 生命周期/状态: CRUD/status
- 映射物理表/接口: TBL-edu-class
- 核心功能: unknown
- 外部消费者: service layer
- 代码落点: backend/app/models/edu.py

## OBJ-classrequest - ClassRequest
- ID: OBJ-classrequest
- 类别: entity
- 所有者: backend
- 业务或契约含义: ClassRequest
- 字段摘要或字段表: id, teacher_id, name, grade_id, description, status, review_by, review_at, review_note, class_id, created_at
- 生命周期/状态: CRUD/status
- 映射物理表/接口: TBL-edu-class-request
- 核心功能: unknown
- 外部消费者: service layer
- 代码落点: backend/app/models/edu.py

## OBJ-errorlog - ErrorLog
- ID: OBJ-errorlog
- 类别: entity
- 所有者: backend
- 业务或契约含义: ErrorLog
- 字段摘要或字段表: id, level, module, path, message, traceback, user_id, created_at
- 生命周期/状态: CRUD/status
- 映射物理表/接口: TBL-sys-error-log
- 核心功能: unknown
- 外部消费者: service layer
- 代码落点: backend/app/models/ops.py

## OBJ-examstandard - ExamStandard
- ID: OBJ-examstandard
- 类别: entity
- 所有者: backend
- 业务或契约含义: ExamStandard
- 字段摘要或字段表: id, name, region, stage, subject_name, exam_type, total_score, duration, sections, difficulty_ratio, description, is_active, is_default, source, sort, owner_id, created_at, updated_at
- 生命周期/状态: CRUD/status
- 映射物理表/接口: TBL-edu-exam-standard
- 核心功能: unknown
- 外部消费者: service layer
- 代码落点: backend/app/models/paper_ext.py

## OBJ-flowdefinition - FlowDefinition
- ID: OBJ-flowdefinition
- 类别: entity
- 所有者: backend
- 业务或契约含义: FlowDefinition
- 字段摘要或字段表: id, code, name, flow_type, trigger_type, trigger_behavior, definition, version, status, created_at, updated_at
- 生命周期/状态: CRUD/status
- 映射物理表/接口: TBL-edu-flow-definition
- 核心功能: unknown
- 外部消费者: service layer
- 代码落点: backend/app/models/flow.py

## OBJ-flowhistory - FlowHistory
- ID: OBJ-flowhistory
- 类别: entity
- 所有者: backend
- 业务或契约含义: FlowHistory
- 字段摘要或字段表: id, instance_id, activity_id, activity_name, operator_id, operator_name, action, comment, from_activity, to_activity, created_at
- 生命周期/状态: CRUD/status
- 映射物理表/接口: TBL-edu-flow-history
- 核心功能: unknown
- 外部消费者: service layer
- 代码落点: backend/app/models/flow.py

## OBJ-flowinstance - FlowInstance
- ID: OBJ-flowinstance
- 类别: entity
- 所有者: backend
- 业务或契约含义: FlowInstance
- 字段摘要或字段表: id, def_id, biz_type, biz_id, biz_key, current_activity_ids, variables, status, creator_id, started_at, ended_at, updated_at
- 生命周期/状态: CRUD/status
- 映射物理表/接口: TBL-edu-flow-instance
- 核心功能: unknown
- 外部消费者: service layer
- 代码落点: backend/app/models/flow.py

## OBJ-flowtask - FlowTask
- ID: OBJ-flowtask
- 类别: entity
- 所有者: backend
- 业务或契约含义: FlowTask
- 字段摘要或字段表: id, instance_id, activity_id, activity_type, activity_name, role_code, assignee_id, status, action, comment, created_at, claimed_at, done_at, deadline, urge_count, last_urged_at, transfer_count, last_transferred_at
- 生命周期/状态: CRUD/status
- 映射物理表/接口: TBL-edu-flow-task
- 核心功能: unknown
- 外部消费者: service layer
- 代码落点: backend/app/models/flow.py

## OBJ-flowtransfer - FlowTransfer
- ID: OBJ-flowtransfer
- 类别: entity
- 所有者: backend
- 业务或契约含义: FlowTransfer
- 字段摘要或字段表: id, task_id, from_user_id, to_user_id, operator_id, reason, created_at
- 生命周期/状态: CRUD/status
- 映射物理表/接口: TBL-edu-flow-transfer
- 核心功能: unknown
- 外部消费者: service layer
- 代码落点: backend/app/models/flow.py

## OBJ-grade - Grade
- ID: OBJ-grade
- 类别: entity
- 所有者: backend
- 业务或契约含义: Grade
- 字段摘要或字段表: id, name, stage, grade_num, is_active, sort
- 生命周期/状态: CRUD/status
- 映射物理表/接口: TBL-edu-grade
- 核心功能: unknown
- 外部消费者: service layer
- 代码落点: backend/app/models/edu.py

## OBJ-jobexecutionlog - JobExecutionLog
- ID: OBJ-jobexecutionlog
- 类别: entity
- 所有者: backend
- 业务或契约含义: JobExecutionLog
- 字段摘要或字段表: id, job_id, job_name, status, started_at, finished_at, duration_ms, message, trigger_type
- 生命周期/状态: CRUD/status
- 映射物理表/接口: TBL-sys-job-execution-log
- 核心功能: unknown
- 外部消费者: service layer
- 代码落点: backend/app/models/ops.py

## OBJ-joblock - JobLock
- ID: OBJ-joblock
- 类别: entity
- 所有者: backend
- 业务或契约含义: JobLock
- 字段摘要或字段表: job_id, owner, acquired_at, expire_at
- 生命周期/状态: CRUD/status
- 映射物理表/接口: TBL-sys-job-lock
- 核心功能: unknown
- 外部消费者: service layer
- 代码落点: backend/app/models/ops.py

## OBJ-knowledgemastery - KnowledgeMastery
- ID: OBJ-knowledgemastery
- 类别: entity
- 所有者: backend
- 业务或契约含义: KnowledgeMastery
- 字段摘要或字段表: id, student_id, knowledge_point_id, subject_id, total_count, correct_count, mastery, wrong_count, study_seconds, last_practice_at, updated_at
- 生命周期/状态: CRUD/status
- 映射物理表/接口: TBL-edu-knowledge-mastery
- 核心功能: unknown
- 外部消费者: service layer
- 代码落点: backend/app/models/learning.py

## OBJ-knowledgepoint - KnowledgePoint
- ID: OBJ-knowledgepoint
- 类别: entity
- 所有者: backend
- 业务或契约含义: KnowledgePoint
- 字段摘要或字段表: id, name, level, parent_id, path, grade_id, subject_id, term, code, description, difficulty, keywords, sort, is_active, textbook_version, status, source, owner_id, external_source, external_id
- 生命周期/状态: CRUD/status
- 映射物理表/接口: TBL-edu-knowledge-point
- 核心功能: unknown
- 外部消费者: service layer
- 代码落点: backend/app/models/edu.py

## OBJ-knowledgeprerequisite - KnowledgePrerequisite
- ID: OBJ-knowledgeprerequisite
- 类别: entity
- 所有者: backend
- 业务或契约含义: KnowledgePrerequisite
- 字段摘要或字段表: id, topic_kp_id, prerequisite_kp_id, strength, reason, source, created_at
- 生命周期/状态: CRUD/status
- 映射物理表/接口: TBL-edu-knowledge-prerequisite
- 核心功能: unknown
- 外部消费者: service layer
- 代码落点: backend/app/models/taxonomy.py

## OBJ-lessonplan - LessonPlan
- ID: OBJ-lessonplan
- 类别: entity
- 所有者: backend
- 业务或契约含义: LessonPlan
- 字段摘要或字段表: id, title, topic, subject_id, grade_id, textbook_version, knowledge_point_id, duration_minutes, period, objectives, key_points, difficulties, teaching_preparation, class_exercise, board_design, homework, reflection, creator_id, use_count, is_shared, ai_generated, ai_job_id, created_at, updated_at
- 生命周期/状态: CRUD/status
- 映射物理表/接口: TBL-edu-lesson-plan
- 核心功能: unknown
- 外部消费者: service layer
- 代码落点: backend/app/models/lesson.py

## OBJ-lessonstage - LessonStage
- ID: OBJ-lessonstage
- 类别: entity
- 所有者: backend
- 业务或契约含义: LessonStage
- 字段摘要或字段表: id, lesson_id, name, duration_minutes, content, teacher_activity, student_activity, sort_order
- 生命周期/状态: CRUD/status
- 映射物理表/接口: TBL-edu-lesson-stage
- 核心功能: unknown
- 外部消费者: service layer
- 代码落点: backend/app/models/lesson.py

## OBJ-llmbreakerstate - LlmBreakerState
- ID: OBJ-llmbreakerstate
- 类别: entity
- 所有者: backend
- 业务或契约含义: LlmBreakerState
- 字段摘要或字段表: id, kind, reason, streak, expire_at, updated_at
- 生命周期/状态: CRUD/status
- 映射物理表/接口: TBL-sys-llm-breaker
- 核心功能: unknown
- 外部消费者: service layer
- 代码落点: backend/app/models/ops.py

## OBJ-loginlog - LoginLog
- ID: OBJ-loginlog
- 类别: entity
- 所有者: backend
- 业务或契约含义: LoginLog
- 字段摘要或字段表: id, user_id, username, login_type, status, message, ip, location, device, os, is_abnormal, login_at
- 生命周期/状态: CRUD/status
- 映射物理表/接口: TBL-sys-login-log
- 核心功能: unknown
- 外部消费者: service layer
- 代码落点: backend/app/models/ops.py

## OBJ-note - Note
- ID: OBJ-note
- 类别: entity
- 所有者: backend
- 业务或契约含义: Note
- 字段摘要或字段表: id, title, content, format, student_id, subject_id, knowledge_point_id, tags, ai_summary, ai_outline, ai_mindmap, is_favorite, view_count, is_shared, created_at, updated_at
- 生命周期/状态: CRUD/status
- 映射物理表/接口: TBL-edu-note
- 核心功能: unknown
- 外部消费者: service layer
- 代码落点: backend/app/models/learning.py

## OBJ-notification - Notification
- ID: OBJ-notification
- 类别: entity
- 所有者: backend
- 业务或契约含义: Notification
- 字段摘要或字段表: id, user_id, title, content, type, biz_type, biz_id, is_read, created_at
- 生命周期/状态: CRUD/status
- 映射物理表/接口: TBL-sys-notification
- 核心功能: unknown
- 外部消费者: service layer
- 代码落点: backend/app/models/ops.py

## OBJ-notifypref - NotifyPref
- ID: OBJ-notifypref
- 类别: entity
- 所有者: backend
- 业务或契约含义: NotifyPref
- 字段摘要或字段表: user_id, prefs, updated_at
- 生命周期/状态: CRUD/status
- 映射物理表/接口: TBL-sys-notify-pref
- 核心功能: unknown
- 外部消费者: service layer
- 代码落点: backend/app/models/ops.py

## OBJ-operationlog - OperationLog
- ID: OBJ-operationlog
- 类别: entity
- 所有者: backend
- 业务或契约含义: OperationLog
- 字段摘要或字段表: id, user_id, username, module, action, method, path, ip, params, result, status, error_msg, duration_ms, created_at
- 生命周期/状态: CRUD/status
- 映射物理表/接口: TBL-sys-operation-log
- 核心功能: unknown
- 外部消费者: service layer
- 代码落点: backend/app/models/ops.py

## OBJ-paper - Paper
- ID: OBJ-paper
- 类别: entity
- 所有者: backend
- 业务或契约含义: Paper
- 字段摘要或字段表: id, name, grade_id, subject_id, total_score, duration, difficulty_ratio, knowledge_coverage, difficulty_report, creator_id, source, is_shared, use_count, description, exam_type, stage, textbook_version, status, standard_id, share_scope, review_comment, review_by, review_at, current_version, generation_params, type_report, created_at, updated_at
- 生命周期/状态: CRUD/status
- 映射物理表/接口: TBL-edu-paper
- 核心功能: unknown
- 外部消费者: service layer
- 代码落点: backend/app/models/question.py

## OBJ-paperfavorite - PaperFavorite
- ID: OBJ-paperfavorite
- 类别: entity
- 所有者: backend
- 业务或契约含义: PaperFavorite
- 字段摘要或字段表: id, paper_id, user_id, created_at
- 生命周期/状态: CRUD/status
- 映射物理表/接口: TBL-edu-paper-favorite
- 核心功能: unknown
- 外部消费者: service layer
- 代码落点: backend/app/models/paper_ext.py

## OBJ-paperitem - PaperItem
- ID: OBJ-paperitem
- 类别: entity
- 所有者: backend
- 业务或契约含义: PaperItem
- 字段摘要或字段表: id, paper_id, question_id, sort_order, score, section_name, section_code, section_sort, score_override
- 生命周期/状态: CRUD/status
- 映射物理表/接口: TBL-edu-paper-item
- 核心功能: unknown
- 外部消费者: service layer
- 代码落点: backend/app/models/question.py

## OBJ-papershare - PaperShare
- ID: OBJ-papershare
- 类别: entity
- 所有者: backend
- 业务或契约含义: PaperShare
- 字段摘要或字段表: id, paper_id, from_user_id, to_user_id, permission, scope, created_at
- 生命周期/状态: CRUD/status
- 映射物理表/接口: TBL-edu-paper-share
- 核心功能: unknown
- 外部消费者: service layer
- 代码落点: backend/app/models/question.py

## OBJ-paperversion - PaperVersion
- ID: OBJ-paperversion
- 类别: entity
- 所有者: backend
- 业务或契约含义: PaperVersion
- 字段摘要或字段表: id, paper_id, version, snapshot, change_note, item_count, total_score, created_by, created_at
- 生命周期/状态: CRUD/status
- 映射物理表/接口: TBL-edu-paper-version
- 核心功能: unknown
- 外部消费者: service layer
- 代码落点: backend/app/models/paper_ext.py

## OBJ-permission - Permission
- ID: OBJ-permission
- 类别: entity
- 所有者: backend
- 业务或契约含义: Permission
- 字段摘要或字段表: id, code, name, type, parent_id, path, icon, sort, is_hidden
- 生命周期/状态: CRUD/status
- 映射物理表/接口: TBL-sys-permission
- 核心功能: unknown
- 外部消费者: service layer
- 代码落点: backend/app/models/system.py

## OBJ-question - Question
- ID: OBJ-question
- 类别: entity
- 所有者: backend
- 业务或契约含义: Question
- 字段摘要或字段表: id, type, stem, options, answer, analysis, score, answer_min_words, difficulty, grade_id, subject_id, knowledge_point_id, bank_type, owner_id, status, fingerprint, source, usage_count, external_source, external_id, extra_json, created_at, updated_at
- 生命周期/状态: CRUD/status
- 映射物理表/接口: TBL-edu-question
- 核心功能: unknown
- 外部消费者: service layer
- 代码落点: backend/app/models/question.py

## OBJ-questionfavorite - QuestionFavorite
- ID: OBJ-questionfavorite
- 类别: entity
- 所有者: backend
- 业务或契约含义: QuestionFavorite
- 字段摘要或字段表: id, user_id, question_id, tag, note, created_at
- 生命周期/状态: CRUD/status
- 映射物理表/接口: TBL-edu-question-favorite
- 核心功能: unknown
- 外部消费者: service layer
- 代码落点: backend/app/models/learning.py

## OBJ-questionknowledge - QuestionKnowledge
- ID: OBJ-questionknowledge
- 类别: entity
- 所有者: backend
- 业务或契约含义: QuestionKnowledge
- 字段摘要或字段表: id, question_id, knowledge_point_id
- 生命周期/状态: CRUD/status
- 映射物理表/接口: TBL-edu-question-knowledge
- 核心功能: unknown
- 外部消费者: service layer
- 代码落点: backend/app/models/question.py

## OBJ-ratelimit - RateLimit
- ID: OBJ-ratelimit
- 类别: entity
- 所有者: backend
- 业务或契约含义: RateLimit
- 字段摘要或字段表: key, window_start, hits, expire_at, created_at
- 生命周期/状态: CRUD/status
- 映射物理表/接口: TBL-sys-rate-limit
- 核心功能: unknown
- 外部消费者: service layer
- 代码落点: backend/app/models/security_cache.py

## OBJ-registration - Registration
- ID: OBJ-registration
- 类别: entity
- 所有者: backend
- 业务或契约含义: Registration
- 字段摘要或字段表: id, user_id, identity, attachments, reason, status, audit_user_id, audit_at, audit_reason, created_at
- 生命周期/状态: CRUD/status
- 映射物理表/接口: TBL-sys-registration
- 核心功能: unknown
- 外部消费者: service layer
- 代码落点: backend/app/models/system.py

## OBJ-remediationplan - RemediationPlan
- ID: OBJ-remediationplan
- 类别: entity
- 所有者: backend
- 业务或契约含义: RemediationPlan
- 字段摘要或字段表: id, student_id, diagnosis_id, title, payload, version, created_at, updated_at
- 生命周期/状态: CRUD/status
- 映射物理表/接口: TBL-edu-remediation-plan
- 核心功能: unknown
- 外部消费者: service layer
- 代码落点: backend/app/models/learning_ext.py

## OBJ-resetcode - ResetCode
- ID: OBJ-resetcode
- 类别: entity
- 所有者: backend
- 业务或契约含义: ResetCode
- 字段摘要或字段表: target, code, expire_at, created_at
- 生命周期/状态: CRUD/status
- 映射物理表/接口: TBL-sys-reset-code
- 核心功能: unknown
- 外部消费者: service layer
- 代码落点: backend/app/models/security_cache.py

## OBJ-reviewplan - ReviewPlan
- ID: OBJ-reviewplan
- 类别: entity
- 所有者: backend
- 业务或契约含义: ReviewPlan
- 字段摘要或字段表: id, student_id, wrong_question_id, knowledge_point_id, subject_id, stage, scheduled_date, is_completed, completed_at, correct_rate, created_at
- 生命周期/状态: CRUD/status
- 映射物理表/接口: TBL-edu-review-plan
- 核心功能: unknown
- 外部消费者: service layer
- 代码落点: backend/app/models/learning.py

## OBJ-revokedtoken - RevokedToken
- ID: OBJ-revokedtoken
- 类别: entity
- 所有者: backend
- 业务或契约含义: RevokedToken
- 字段摘要或字段表: jti, expire_at, created_at
- 生命周期/状态: CRUD/status
- 映射物理表/接口: TBL-sys-revoked-token
- 核心功能: unknown
- 外部消费者: service layer
- 代码落点: backend/app/models/security_cache.py

## OBJ-role - Role
- ID: OBJ-role
- 类别: entity
- 所有者: backend
- 业务或契约含义: Role
- 字段摘要或字段表: id, code, name, description, data_scope, is_builtin, is_active, sort, created_at
- 生命周期/状态: CRUD/status
- 映射物理表/接口: TBL-sys-role
- 核心功能: unknown
- 外部消费者: service layer
- 代码落点: backend/app/models/system.py

## OBJ-rolepermission - RolePermission
- ID: OBJ-rolepermission
- 类别: entity
- 所有者: backend
- 业务或契约含义: RolePermission
- 字段摘要或字段表: id, role_id, permission_id
- 生命周期/状态: CRUD/status
- 映射物理表/接口: TBL-sys-role-permission
- 核心功能: unknown
- 外部消费者: service layer
- 代码落点: backend/app/models/system.py

## OBJ-scheduledjob - ScheduledJob
- ID: OBJ-scheduledjob
- 类别: entity
- 所有者: backend
- 业务或契约含义: ScheduledJob
- 字段摘要或字段表: id, name, description, func_path, cron_expression, is_builtin, is_active, retry_times, last_run_at, last_status, last_error, run_count, created_at
- 生命周期/状态: CRUD/status
- 映射物理表/接口: TBL-sys-scheduled-job
- 核心功能: unknown
- 外部消费者: service layer
- 代码落点: backend/app/models/ops.py

## OBJ-studycheckin - StudyCheckin
- ID: OBJ-studycheckin
- 类别: entity
- 所有者: backend
- 业务或契约含义: StudyCheckin
- 字段摘要或字段表: id, user_id, goal_id, checkin_date, actual_value, streak, note, created_at
- 生命周期/状态: CRUD/status
- 映射物理表/接口: TBL-edu-study-checkin
- 核心功能: unknown
- 外部消费者: service layer
- 代码落点: backend/app/models/learning.py

## OBJ-studygoal - StudyGoal
- ID: OBJ-studygoal
- 类别: entity
- 所有者: backend
- 业务或契约含义: StudyGoal
- 字段摘要或字段表: id, user_id, title, target_type, target_value, unit, subject_id, start_date, end_date, is_active, created_at, updated_at
- 生命周期/状态: CRUD/status
- 映射物理表/接口: TBL-edu-study-goal
- 核心功能: unknown
- 外部消费者: service layer
- 代码落点: backend/app/models/learning.py

## OBJ-studyrecord - StudyRecord
- ID: OBJ-studyrecord
- 类别: entity
- 所有者: backend
- 业务或契约含义: StudyRecord
- 字段摘要或字段表: id, student_id, subject_id, study_date, study_seconds, question_count, correct_count, note_count, created_at
- 生命周期/状态: CRUD/status
- 映射物理表/接口: TBL-edu-study-record
- 核心功能: unknown
- 外部消费者: service layer
- 代码落点: backend/app/models/learning.py

## OBJ-subject - Subject
- ID: OBJ-subject
- 类别: entity
- 所有者: backend
- 业务或契约含义: Subject
- 字段摘要或字段表: id, name, code, textbook_version, grade_id, is_active, sort
- 生命周期/状态: CRUD/status
- 映射物理表/接口: TBL-edu-subject
- 核心功能: unknown
- 外部消费者: service layer
- 代码落点: backend/app/models/edu.py

## OBJ-submission - Submission
- ID: OBJ-submission
- 类别: entity
- 所有者: backend
- 业务或契约含义: Submission
- 字段摘要或字段表: id, task_id, student_id, attempt, status, score, objective_score, subjective_score, duration_seconds, is_passed, class_rank, comment, switch_count, submit_count, submit_time, grade_time, created_at
- 生命周期/状态: CRUD/status
- 映射物理表/接口: TBL-edu-submission
- 核心功能: unknown
- 外部消费者: service layer
- 代码落点: backend/app/models/task.py

## OBJ-sysconfig - SysConfig
- ID: OBJ-sysconfig
- 类别: entity
- 所有者: backend
- 业务或契约含义: SysConfig
- 字段摘要或字段表: id, key, value, value_type, category, label, description, is_public, updated_by, updated_at, created_at
- 生命周期/状态: CRUD/status
- 映射物理表/接口: TBL-sys-config
- 核心功能: unknown
- 外部消费者: service layer
- 代码落点: backend/app/models/system.py

## OBJ-task - Task
- ID: OBJ-task
- 类别: entity
- 所有者: backend
- 业务或契约含义: Task
- 字段摘要或字段表: id, title, type, paper_id, subject_id, grade_id, creator_id, status, start_at, end_at, duration, publish_at, allow_retake, show_answer, anti_cheat, total_score, pass_score, description, created_at, updated_at
- 生命周期/状态: CRUD/status
- 映射物理表/接口: TBL-edu-task
- 核心功能: unknown
- 外部消费者: service layer
- 代码落点: backend/app/models/task.py

## OBJ-taskassignment - TaskAssignment
- ID: OBJ-taskassignment
- 类别: entity
- 所有者: backend
- 业务或契约含义: TaskAssignment
- 字段摘要或字段表: id, task_id, class_id, student_id, group_name, notified
- 生命周期/状态: CRUD/status
- 映射物理表/接口: TBL-edu-task-assignment
- 核心功能: unknown
- 外部消费者: service layer
- 代码落点: backend/app/models/task.py

## OBJ-taxonomydiagnosissession - TaxonomyDiagnosisSession
- ID: OBJ-taxonomydiagnosissession
- 类别: entity
- 所有者: backend
- 业务或契约含义: TaxonomyDiagnosisSession
- 字段摘要或字段表: id, user_id, subject_id, grade_id, targets_json, mode, question_limit, confirm_count, answers_json, status_json, seed, created_at, updated_at, finished_at
- 生命周期/状态: CRUD/status
- 映射物理表/接口: TBL-edu-taxonomy-diagnosis-session
- 核心功能: unknown
- 外部消费者: service layer
- 代码落点: backend/app/models/taxonomy.py

## OBJ-taxonomysyncrun - TaxonomySyncRun
- ID: OBJ-taxonomysyncrun
- 类别: entity
- 所有者: backend
- 业务或契约含义: TaxonomySyncRun
- 字段摘要或字段表: id, user_id, action, source_commit, status, report, bundle_path, backup_path, created_at
- 生命周期/状态: CRUD/status
- 映射物理表/接口: TBL-edu-taxonomy-sync-run
- 核心功能: unknown
- 外部消费者: service layer
- 代码落点: backend/app/models/learning_ext.py

## OBJ-teachingassignment - TeachingAssignment
- ID: OBJ-teachingassignment
- 类别: entity
- 所有者: backend
- 业务或契约含义: TeachingAssignment
- 字段摘要或字段表: id, teacher_id, class_id, subject_id, grade_id, school_year, is_active, created_at
- 生命周期/状态: CRUD/status
- 映射物理表/接口: TBL-edu-teaching-assignment
- 核心功能: unknown
- 外部消费者: service layer
- 代码落点: backend/app/models/edu.py

## OBJ-tutorfeedback - TutorFeedback
- ID: OBJ-tutorfeedback
- 类别: entity
- 所有者: backend
- 业务或契约含义: TutorFeedback
- 字段摘要或字段表: id, user_id, class_id, question_id, stage, content, correction, reviewer_id, status, created_at
- 生命周期/状态: CRUD/status
- 映射物理表/接口: TBL-edu-tutor-feedback
- 核心功能: unknown
- 外部消费者: service layer
- 代码落点: backend/app/models/learning_ext.py

## OBJ-user - User
- ID: OBJ-user
- 类别: entity
- 所有者: backend
- 业务或契约含义: User
- 字段摘要或字段表: id, username, password, real_name, email, phone, avatar, gender, identity, status, school_name, grade_id, class_id, grade_admin_grade_id, must_change_password, last_login_at, last_login_ip, login_fail_count, locked_until, created_at, updated_at
- 生命周期/状态: CRUD/status
- 映射物理表/接口: TBL-sys-user
- 核心功能: unknown
- 外部消费者: service layer
- 代码落点: backend/app/models/system.py

## OBJ-userrole - UserRole
- ID: OBJ-userrole
- 类别: entity
- 所有者: backend
- 业务或契约含义: UserRole
- 字段摘要或字段表: id, user_id, role_id
- 生命周期/状态: CRUD/status
- 映射物理表/接口: TBL-sys-user-role
- 核心功能: unknown
- 外部消费者: service layer
- 代码落点: backend/app/models/system.py

## OBJ-usertokenrevocation - UserTokenRevocation
- ID: OBJ-usertokenrevocation
- 类别: entity
- 所有者: backend
- 业务或契约含义: UserTokenRevocation
- 字段摘要或字段表: user_id, invalid_before_ts, expire_at, created_at
- 生命周期/状态: CRUD/status
- 映射物理表/接口: TBL-sys-user-token-revocation
- 核心功能: unknown
- 外部消费者: service layer
- 代码落点: backend/app/models/security_cache.py

## OBJ-wrongquestion - WrongQuestion
- ID: OBJ-wrongquestion
- 类别: entity
- 所有者: backend
- 业务或契约含义: WrongQuestion
- 字段摘要或字段表: id, student_id, question_id, subject_id, knowledge_point_id, wrong_answer, error_count, error_reason, ai_reason, source_type, source_id, source_name, is_mastered, mastered_at, last_wrong_at, created_at
- 生命周期/状态: CRUD/status
- 映射物理表/接口: TBL-edu-wrong-question
- 核心功能: unknown
- 外部消费者: service layer
- 代码落点: backend/app/models/task.py
