# 数据库模型

- Output Language: zh-CN
- Status: in-progress
- Table Count: 63

| TBL ID | Physical Table | Type | Owner | Meaning | Mapping Object | Main Writers | Readers | Evidence |
|---|---|---|---|---|---|---|---|---|
| TBL-edu-answer | edu_answer | table | backend | edu_answer | edu_answer | unknown | unknown | backend/app/models via SQLAlchemy metadata |
| TBL-edu-class | edu_class | table | backend | edu_class | edu_class | unknown | unknown | backend/app/models via SQLAlchemy metadata |
| TBL-edu-class-request | edu_class_request | table | backend | edu_class_request | edu_class_request | unknown | unknown | backend/app/models via SQLAlchemy metadata |
| TBL-edu-exam-standard | edu_exam_standard | table | backend | edu_exam_standard | edu_exam_standard | unknown | unknown | backend/app/models via SQLAlchemy metadata |
| TBL-edu-flow-definition | edu_flow_definition | table | backend | edu_flow_definition | edu_flow_definition | unknown | unknown | backend/app/models via SQLAlchemy metadata |
| TBL-edu-flow-history | edu_flow_history | table | backend | edu_flow_history | edu_flow_history | unknown | unknown | backend/app/models via SQLAlchemy metadata |
| TBL-edu-flow-instance | edu_flow_instance | table | backend | edu_flow_instance | edu_flow_instance | unknown | unknown | backend/app/models via SQLAlchemy metadata |
| TBL-edu-flow-task | edu_flow_task | table | backend | edu_flow_task | edu_flow_task | unknown | unknown | backend/app/models via SQLAlchemy metadata |
| TBL-edu-flow-transfer | edu_flow_transfer | table | backend | edu_flow_transfer | edu_flow_transfer | unknown | unknown | backend/app/models via SQLAlchemy metadata |
| TBL-edu-grade | edu_grade | table | backend | edu_grade | edu_grade | unknown | unknown | backend/app/models via SQLAlchemy metadata |
| TBL-edu-knowledge-mastery | edu_knowledge_mastery | table | backend | edu_knowledge_mastery | edu_knowledge_mastery | unknown | unknown | backend/app/models via SQLAlchemy metadata |
| TBL-edu-knowledge-point | edu_knowledge_point | table | backend | edu_knowledge_point | edu_knowledge_point | unknown | unknown | backend/app/models via SQLAlchemy metadata |
| TBL-edu-knowledge-prerequisite | edu_knowledge_prerequisite | table | backend | edu_knowledge_prerequisite | edu_knowledge_prerequisite | unknown | unknown | backend/app/models via SQLAlchemy metadata |
| TBL-edu-lesson-plan | edu_lesson_plan | table | backend | edu_lesson_plan | edu_lesson_plan | unknown | unknown | backend/app/models via SQLAlchemy metadata |
| TBL-edu-lesson-stage | edu_lesson_stage | table | backend | edu_lesson_stage | edu_lesson_stage | unknown | unknown | backend/app/models via SQLAlchemy metadata |
| TBL-edu-note | edu_note | table | backend | edu_note | edu_note | unknown | unknown | backend/app/models via SQLAlchemy metadata |
| TBL-edu-paper | edu_paper | table | backend | edu_paper | edu_paper | unknown | unknown | backend/app/models via SQLAlchemy metadata |
| TBL-edu-paper-favorite | edu_paper_favorite | table | backend | edu_paper_favorite | edu_paper_favorite | unknown | unknown | backend/app/models via SQLAlchemy metadata |
| TBL-edu-paper-item | edu_paper_item | table | backend | edu_paper_item | edu_paper_item | unknown | unknown | backend/app/models via SQLAlchemy metadata |
| TBL-edu-paper-share | edu_paper_share | table | backend | edu_paper_share | edu_paper_share | unknown | unknown | backend/app/models via SQLAlchemy metadata |
| TBL-edu-paper-version | edu_paper_version | table | backend | edu_paper_version | edu_paper_version | unknown | unknown | backend/app/models via SQLAlchemy metadata |
| TBL-edu-question | edu_question | table | backend | edu_question | edu_question | unknown | unknown | backend/app/models via SQLAlchemy metadata |
| TBL-edu-question-favorite | edu_question_favorite | table | backend | edu_question_favorite | edu_question_favorite | unknown | unknown | backend/app/models via SQLAlchemy metadata |
| TBL-edu-question-knowledge | edu_question_knowledge | table | backend | edu_question_knowledge | edu_question_knowledge | unknown | unknown | backend/app/models via SQLAlchemy metadata |
| TBL-edu-remediation-plan | edu_remediation_plan | table | backend | edu_remediation_plan | edu_remediation_plan | unknown | unknown | backend/app/models via SQLAlchemy metadata |
| TBL-edu-review-plan | edu_review_plan | table | backend | edu_review_plan | edu_review_plan | unknown | unknown | backend/app/models via SQLAlchemy metadata |
| TBL-edu-study-checkin | edu_study_checkin | table | backend | edu_study_checkin | edu_study_checkin | unknown | unknown | backend/app/models via SQLAlchemy metadata |
| TBL-edu-study-goal | edu_study_goal | table | backend | edu_study_goal | edu_study_goal | unknown | unknown | backend/app/models via SQLAlchemy metadata |
| TBL-edu-study-record | edu_study_record | table | backend | edu_study_record | edu_study_record | unknown | unknown | backend/app/models via SQLAlchemy metadata |
| TBL-edu-subject | edu_subject | table | backend | edu_subject | edu_subject | unknown | unknown | backend/app/models via SQLAlchemy metadata |
| TBL-edu-submission | edu_submission | table | backend | edu_submission | edu_submission | unknown | unknown | backend/app/models via SQLAlchemy metadata |
| TBL-edu-task | edu_task | table | backend | edu_task | edu_task | unknown | unknown | backend/app/models via SQLAlchemy metadata |
| TBL-edu-task-assignment | edu_task_assignment | table | backend | edu_task_assignment | edu_task_assignment | unknown | unknown | backend/app/models via SQLAlchemy metadata |
| TBL-edu-taxonomy-diagnosis-session | edu_taxonomy_diagnosis_session | table | backend | edu_taxonomy_diagnosis_session | edu_taxonomy_diagnosis_session | unknown | unknown | backend/app/models via SQLAlchemy metadata |
| TBL-edu-taxonomy-sync-run | edu_taxonomy_sync_run | table | backend | edu_taxonomy_sync_run | edu_taxonomy_sync_run | unknown | unknown | backend/app/models via SQLAlchemy metadata |
| TBL-edu-teaching-assignment | edu_teaching_assignment | table | backend | edu_teaching_assignment | edu_teaching_assignment | unknown | unknown | backend/app/models via SQLAlchemy metadata |
| TBL-edu-tutor-feedback | edu_tutor_feedback | table | backend | edu_tutor_feedback | edu_tutor_feedback | unknown | unknown | backend/app/models via SQLAlchemy metadata |
| TBL-edu-wrong-question | edu_wrong_question | table | backend | edu_wrong_question | edu_wrong_question | unknown | unknown | backend/app/models via SQLAlchemy metadata |
| TBL-sys-agent-call-log | sys_agent_call_log | table | backend | sys_agent_call_log | sys_agent_call_log | unknown | unknown | backend/app/models via SQLAlchemy metadata |
| TBL-sys-agent-job | sys_agent_job | table | backend | sys_agent_job | sys_agent_job | unknown | unknown | backend/app/models via SQLAlchemy metadata |
| TBL-sys-agent-rate | sys_agent_rate | table | backend | sys_agent_rate | sys_agent_rate | unknown | unknown | backend/app/models via SQLAlchemy metadata |
| TBL-sys-attachment | sys_attachment | table | backend | sys_attachment | sys_attachment | unknown | unknown | backend/app/models via SQLAlchemy metadata |
| TBL-sys-captcha | sys_captcha | table | backend | sys_captcha | sys_captcha | unknown | unknown | backend/app/models via SQLAlchemy metadata |
| TBL-sys-config | sys_config | table | backend | sys_config | sys_config | unknown | unknown | backend/app/models via SQLAlchemy metadata |
| TBL-sys-error-log | sys_error_log | table | backend | sys_error_log | sys_error_log | unknown | unknown | backend/app/models via SQLAlchemy metadata |
| TBL-sys-job-execution-log | sys_job_execution_log | table | backend | sys_job_execution_log | sys_job_execution_log | unknown | unknown | backend/app/models via SQLAlchemy metadata |
| TBL-sys-job-lock | sys_job_lock | table | backend | sys_job_lock | sys_job_lock | unknown | unknown | backend/app/models via SQLAlchemy metadata |
| TBL-sys-llm-breaker | sys_llm_breaker | table | backend | sys_llm_breaker | sys_llm_breaker | unknown | unknown | backend/app/models via SQLAlchemy metadata |
| TBL-sys-login-log | sys_login_log | table | backend | sys_login_log | sys_login_log | unknown | unknown | backend/app/models via SQLAlchemy metadata |
| TBL-sys-notification | sys_notification | table | backend | sys_notification | sys_notification | unknown | unknown | backend/app/models via SQLAlchemy metadata |
| TBL-sys-notify-pref | sys_notify_pref | table | backend | sys_notify_pref | sys_notify_pref | unknown | unknown | backend/app/models via SQLAlchemy metadata |
| TBL-sys-operation-log | sys_operation_log | table | backend | sys_operation_log | sys_operation_log | unknown | unknown | backend/app/models via SQLAlchemy metadata |
| TBL-sys-permission | sys_permission | table | backend | sys_permission | sys_permission | unknown | unknown | backend/app/models via SQLAlchemy metadata |
| TBL-sys-rate-limit | sys_rate_limit | table | backend | sys_rate_limit | sys_rate_limit | unknown | unknown | backend/app/models via SQLAlchemy metadata |
| TBL-sys-registration | sys_registration | table | backend | sys_registration | sys_registration | unknown | unknown | backend/app/models via SQLAlchemy metadata |
| TBL-sys-reset-code | sys_reset_code | table | backend | sys_reset_code | sys_reset_code | unknown | unknown | backend/app/models via SQLAlchemy metadata |
| TBL-sys-revoked-token | sys_revoked_token | table | backend | sys_revoked_token | sys_revoked_token | unknown | unknown | backend/app/models via SQLAlchemy metadata |
| TBL-sys-role | sys_role | table | backend | sys_role | sys_role | unknown | unknown | backend/app/models via SQLAlchemy metadata |
| TBL-sys-role-permission | sys_role_permission | table | backend | sys_role_permission | sys_role_permission | unknown | unknown | backend/app/models via SQLAlchemy metadata |
| TBL-sys-scheduled-job | sys_scheduled_job | table | backend | sys_scheduled_job | sys_scheduled_job | unknown | unknown | backend/app/models via SQLAlchemy metadata |
| TBL-sys-user | sys_user | table | backend | sys_user | sys_user | unknown | unknown | backend/app/models via SQLAlchemy metadata |
| TBL-sys-user-role | sys_user_role | table | backend | sys_user_role | sys_user_role | unknown | unknown | backend/app/models via SQLAlchemy metadata |
| TBL-sys-user-token-revocation | sys_user_token_revocation | table | backend | sys_user_token_revocation | sys_user_token_revocation | unknown | unknown | backend/app/models via SQLAlchemy metadata |

## Physical Definitions

## TBL-edu-answer - edu_answer
- ID: TBL-edu-answer
- 对象类型: table
- 所有者: backend
- 业务含义: edu_answer
- 映射对象: SQLAlchemy model for edu_answer
- 主写功能: unknown
- 读取功能: unknown
- DAO/Mapper/Entity: SQLAlchemy model + service layer
- DDL/SQL证据: Base.metadata and migrations/versions
- 结论级别: 事实（表与字段）；访问归属待补

## TBL-edu-class - edu_class
- ID: TBL-edu-class
- 对象类型: table
- 所有者: backend
- 业务含义: edu_class
- 映射对象: SQLAlchemy model for edu_class
- 主写功能: unknown
- 读取功能: unknown
- DAO/Mapper/Entity: SQLAlchemy model + service layer
- DDL/SQL证据: Base.metadata and migrations/versions
- 结论级别: 事实（表与字段）；访问归属待补

## TBL-edu-class-request - edu_class_request
- ID: TBL-edu-class-request
- 对象类型: table
- 所有者: backend
- 业务含义: edu_class_request
- 映射对象: SQLAlchemy model for edu_class_request
- 主写功能: unknown
- 读取功能: unknown
- DAO/Mapper/Entity: SQLAlchemy model + service layer
- DDL/SQL证据: Base.metadata and migrations/versions
- 结论级别: 事实（表与字段）；访问归属待补

## TBL-edu-exam-standard - edu_exam_standard
- ID: TBL-edu-exam-standard
- 对象类型: table
- 所有者: backend
- 业务含义: edu_exam_standard
- 映射对象: SQLAlchemy model for edu_exam_standard
- 主写功能: unknown
- 读取功能: unknown
- DAO/Mapper/Entity: SQLAlchemy model + service layer
- DDL/SQL证据: Base.metadata and migrations/versions
- 结论级别: 事实（表与字段）；访问归属待补

## TBL-edu-flow-definition - edu_flow_definition
- ID: TBL-edu-flow-definition
- 对象类型: table
- 所有者: backend
- 业务含义: edu_flow_definition
- 映射对象: SQLAlchemy model for edu_flow_definition
- 主写功能: unknown
- 读取功能: unknown
- DAO/Mapper/Entity: SQLAlchemy model + service layer
- DDL/SQL证据: Base.metadata and migrations/versions
- 结论级别: 事实（表与字段）；访问归属待补

## TBL-edu-flow-history - edu_flow_history
- ID: TBL-edu-flow-history
- 对象类型: table
- 所有者: backend
- 业务含义: edu_flow_history
- 映射对象: SQLAlchemy model for edu_flow_history
- 主写功能: unknown
- 读取功能: unknown
- DAO/Mapper/Entity: SQLAlchemy model + service layer
- DDL/SQL证据: Base.metadata and migrations/versions
- 结论级别: 事实（表与字段）；访问归属待补

## TBL-edu-flow-instance - edu_flow_instance
- ID: TBL-edu-flow-instance
- 对象类型: table
- 所有者: backend
- 业务含义: edu_flow_instance
- 映射对象: SQLAlchemy model for edu_flow_instance
- 主写功能: unknown
- 读取功能: unknown
- DAO/Mapper/Entity: SQLAlchemy model + service layer
- DDL/SQL证据: Base.metadata and migrations/versions
- 结论级别: 事实（表与字段）；访问归属待补

## TBL-edu-flow-task - edu_flow_task
- ID: TBL-edu-flow-task
- 对象类型: table
- 所有者: backend
- 业务含义: edu_flow_task
- 映射对象: SQLAlchemy model for edu_flow_task
- 主写功能: unknown
- 读取功能: unknown
- DAO/Mapper/Entity: SQLAlchemy model + service layer
- DDL/SQL证据: Base.metadata and migrations/versions
- 结论级别: 事实（表与字段）；访问归属待补

## TBL-edu-flow-transfer - edu_flow_transfer
- ID: TBL-edu-flow-transfer
- 对象类型: table
- 所有者: backend
- 业务含义: edu_flow_transfer
- 映射对象: SQLAlchemy model for edu_flow_transfer
- 主写功能: unknown
- 读取功能: unknown
- DAO/Mapper/Entity: SQLAlchemy model + service layer
- DDL/SQL证据: Base.metadata and migrations/versions
- 结论级别: 事实（表与字段）；访问归属待补

## TBL-edu-grade - edu_grade
- ID: TBL-edu-grade
- 对象类型: table
- 所有者: backend
- 业务含义: edu_grade
- 映射对象: SQLAlchemy model for edu_grade
- 主写功能: unknown
- 读取功能: unknown
- DAO/Mapper/Entity: SQLAlchemy model + service layer
- DDL/SQL证据: Base.metadata and migrations/versions
- 结论级别: 事实（表与字段）；访问归属待补

## TBL-edu-knowledge-mastery - edu_knowledge_mastery
- ID: TBL-edu-knowledge-mastery
- 对象类型: table
- 所有者: backend
- 业务含义: edu_knowledge_mastery
- 映射对象: SQLAlchemy model for edu_knowledge_mastery
- 主写功能: unknown
- 读取功能: unknown
- DAO/Mapper/Entity: SQLAlchemy model + service layer
- DDL/SQL证据: Base.metadata and migrations/versions
- 结论级别: 事实（表与字段）；访问归属待补

## TBL-edu-knowledge-point - edu_knowledge_point
- ID: TBL-edu-knowledge-point
- 对象类型: table
- 所有者: backend
- 业务含义: edu_knowledge_point
- 映射对象: SQLAlchemy model for edu_knowledge_point
- 主写功能: unknown
- 读取功能: unknown
- DAO/Mapper/Entity: SQLAlchemy model + service layer
- DDL/SQL证据: Base.metadata and migrations/versions
- 结论级别: 事实（表与字段）；访问归属待补

## TBL-edu-knowledge-prerequisite - edu_knowledge_prerequisite
- ID: TBL-edu-knowledge-prerequisite
- 对象类型: table
- 所有者: backend
- 业务含义: edu_knowledge_prerequisite
- 映射对象: SQLAlchemy model for edu_knowledge_prerequisite
- 主写功能: unknown
- 读取功能: unknown
- DAO/Mapper/Entity: SQLAlchemy model + service layer
- DDL/SQL证据: Base.metadata and migrations/versions
- 结论级别: 事实（表与字段）；访问归属待补

## TBL-edu-lesson-plan - edu_lesson_plan
- ID: TBL-edu-lesson-plan
- 对象类型: table
- 所有者: backend
- 业务含义: edu_lesson_plan
- 映射对象: SQLAlchemy model for edu_lesson_plan
- 主写功能: unknown
- 读取功能: unknown
- DAO/Mapper/Entity: SQLAlchemy model + service layer
- DDL/SQL证据: Base.metadata and migrations/versions
- 结论级别: 事实（表与字段）；访问归属待补

## TBL-edu-lesson-stage - edu_lesson_stage
- ID: TBL-edu-lesson-stage
- 对象类型: table
- 所有者: backend
- 业务含义: edu_lesson_stage
- 映射对象: SQLAlchemy model for edu_lesson_stage
- 主写功能: unknown
- 读取功能: unknown
- DAO/Mapper/Entity: SQLAlchemy model + service layer
- DDL/SQL证据: Base.metadata and migrations/versions
- 结论级别: 事实（表与字段）；访问归属待补

## TBL-edu-note - edu_note
- ID: TBL-edu-note
- 对象类型: table
- 所有者: backend
- 业务含义: edu_note
- 映射对象: SQLAlchemy model for edu_note
- 主写功能: unknown
- 读取功能: unknown
- DAO/Mapper/Entity: SQLAlchemy model + service layer
- DDL/SQL证据: Base.metadata and migrations/versions
- 结论级别: 事实（表与字段）；访问归属待补

## TBL-edu-paper - edu_paper
- ID: TBL-edu-paper
- 对象类型: table
- 所有者: backend
- 业务含义: edu_paper
- 映射对象: SQLAlchemy model for edu_paper
- 主写功能: unknown
- 读取功能: unknown
- DAO/Mapper/Entity: SQLAlchemy model + service layer
- DDL/SQL证据: Base.metadata and migrations/versions
- 结论级别: 事实（表与字段）；访问归属待补

## TBL-edu-paper-favorite - edu_paper_favorite
- ID: TBL-edu-paper-favorite
- 对象类型: table
- 所有者: backend
- 业务含义: edu_paper_favorite
- 映射对象: SQLAlchemy model for edu_paper_favorite
- 主写功能: unknown
- 读取功能: unknown
- DAO/Mapper/Entity: SQLAlchemy model + service layer
- DDL/SQL证据: Base.metadata and migrations/versions
- 结论级别: 事实（表与字段）；访问归属待补

## TBL-edu-paper-item - edu_paper_item
- ID: TBL-edu-paper-item
- 对象类型: table
- 所有者: backend
- 业务含义: edu_paper_item
- 映射对象: SQLAlchemy model for edu_paper_item
- 主写功能: unknown
- 读取功能: unknown
- DAO/Mapper/Entity: SQLAlchemy model + service layer
- DDL/SQL证据: Base.metadata and migrations/versions
- 结论级别: 事实（表与字段）；访问归属待补

## TBL-edu-paper-share - edu_paper_share
- ID: TBL-edu-paper-share
- 对象类型: table
- 所有者: backend
- 业务含义: edu_paper_share
- 映射对象: SQLAlchemy model for edu_paper_share
- 主写功能: unknown
- 读取功能: unknown
- DAO/Mapper/Entity: SQLAlchemy model + service layer
- DDL/SQL证据: Base.metadata and migrations/versions
- 结论级别: 事实（表与字段）；访问归属待补

## TBL-edu-paper-version - edu_paper_version
- ID: TBL-edu-paper-version
- 对象类型: table
- 所有者: backend
- 业务含义: edu_paper_version
- 映射对象: SQLAlchemy model for edu_paper_version
- 主写功能: unknown
- 读取功能: unknown
- DAO/Mapper/Entity: SQLAlchemy model + service layer
- DDL/SQL证据: Base.metadata and migrations/versions
- 结论级别: 事实（表与字段）；访问归属待补

## TBL-edu-question - edu_question
- ID: TBL-edu-question
- 对象类型: table
- 所有者: backend
- 业务含义: edu_question
- 映射对象: SQLAlchemy model for edu_question
- 主写功能: unknown
- 读取功能: unknown
- DAO/Mapper/Entity: SQLAlchemy model + service layer
- DDL/SQL证据: Base.metadata and migrations/versions
- 结论级别: 事实（表与字段）；访问归属待补

## TBL-edu-question-favorite - edu_question_favorite
- ID: TBL-edu-question-favorite
- 对象类型: table
- 所有者: backend
- 业务含义: edu_question_favorite
- 映射对象: SQLAlchemy model for edu_question_favorite
- 主写功能: unknown
- 读取功能: unknown
- DAO/Mapper/Entity: SQLAlchemy model + service layer
- DDL/SQL证据: Base.metadata and migrations/versions
- 结论级别: 事实（表与字段）；访问归属待补

## TBL-edu-question-knowledge - edu_question_knowledge
- ID: TBL-edu-question-knowledge
- 对象类型: table
- 所有者: backend
- 业务含义: edu_question_knowledge
- 映射对象: SQLAlchemy model for edu_question_knowledge
- 主写功能: unknown
- 读取功能: unknown
- DAO/Mapper/Entity: SQLAlchemy model + service layer
- DDL/SQL证据: Base.metadata and migrations/versions
- 结论级别: 事实（表与字段）；访问归属待补

## TBL-edu-remediation-plan - edu_remediation_plan
- ID: TBL-edu-remediation-plan
- 对象类型: table
- 所有者: backend
- 业务含义: edu_remediation_plan
- 映射对象: SQLAlchemy model for edu_remediation_plan
- 主写功能: unknown
- 读取功能: unknown
- DAO/Mapper/Entity: SQLAlchemy model + service layer
- DDL/SQL证据: Base.metadata and migrations/versions
- 结论级别: 事实（表与字段）；访问归属待补

## TBL-edu-review-plan - edu_review_plan
- ID: TBL-edu-review-plan
- 对象类型: table
- 所有者: backend
- 业务含义: edu_review_plan
- 映射对象: SQLAlchemy model for edu_review_plan
- 主写功能: unknown
- 读取功能: unknown
- DAO/Mapper/Entity: SQLAlchemy model + service layer
- DDL/SQL证据: Base.metadata and migrations/versions
- 结论级别: 事实（表与字段）；访问归属待补

## TBL-edu-study-checkin - edu_study_checkin
- ID: TBL-edu-study-checkin
- 对象类型: table
- 所有者: backend
- 业务含义: edu_study_checkin
- 映射对象: SQLAlchemy model for edu_study_checkin
- 主写功能: unknown
- 读取功能: unknown
- DAO/Mapper/Entity: SQLAlchemy model + service layer
- DDL/SQL证据: Base.metadata and migrations/versions
- 结论级别: 事实（表与字段）；访问归属待补

## TBL-edu-study-goal - edu_study_goal
- ID: TBL-edu-study-goal
- 对象类型: table
- 所有者: backend
- 业务含义: edu_study_goal
- 映射对象: SQLAlchemy model for edu_study_goal
- 主写功能: unknown
- 读取功能: unknown
- DAO/Mapper/Entity: SQLAlchemy model + service layer
- DDL/SQL证据: Base.metadata and migrations/versions
- 结论级别: 事实（表与字段）；访问归属待补

## TBL-edu-study-record - edu_study_record
- ID: TBL-edu-study-record
- 对象类型: table
- 所有者: backend
- 业务含义: edu_study_record
- 映射对象: SQLAlchemy model for edu_study_record
- 主写功能: unknown
- 读取功能: unknown
- DAO/Mapper/Entity: SQLAlchemy model + service layer
- DDL/SQL证据: Base.metadata and migrations/versions
- 结论级别: 事实（表与字段）；访问归属待补

## TBL-edu-subject - edu_subject
- ID: TBL-edu-subject
- 对象类型: table
- 所有者: backend
- 业务含义: edu_subject
- 映射对象: SQLAlchemy model for edu_subject
- 主写功能: unknown
- 读取功能: unknown
- DAO/Mapper/Entity: SQLAlchemy model + service layer
- DDL/SQL证据: Base.metadata and migrations/versions
- 结论级别: 事实（表与字段）；访问归属待补

## TBL-edu-submission - edu_submission
- ID: TBL-edu-submission
- 对象类型: table
- 所有者: backend
- 业务含义: edu_submission
- 映射对象: SQLAlchemy model for edu_submission
- 主写功能: unknown
- 读取功能: unknown
- DAO/Mapper/Entity: SQLAlchemy model + service layer
- DDL/SQL证据: Base.metadata and migrations/versions
- 结论级别: 事实（表与字段）；访问归属待补

## TBL-edu-task - edu_task
- ID: TBL-edu-task
- 对象类型: table
- 所有者: backend
- 业务含义: edu_task
- 映射对象: SQLAlchemy model for edu_task
- 主写功能: unknown
- 读取功能: unknown
- DAO/Mapper/Entity: SQLAlchemy model + service layer
- DDL/SQL证据: Base.metadata and migrations/versions
- 结论级别: 事实（表与字段）；访问归属待补

## TBL-edu-task-assignment - edu_task_assignment
- ID: TBL-edu-task-assignment
- 对象类型: table
- 所有者: backend
- 业务含义: edu_task_assignment
- 映射对象: SQLAlchemy model for edu_task_assignment
- 主写功能: unknown
- 读取功能: unknown
- DAO/Mapper/Entity: SQLAlchemy model + service layer
- DDL/SQL证据: Base.metadata and migrations/versions
- 结论级别: 事实（表与字段）；访问归属待补

## TBL-edu-taxonomy-diagnosis-session - edu_taxonomy_diagnosis_session
- ID: TBL-edu-taxonomy-diagnosis-session
- 对象类型: table
- 所有者: backend
- 业务含义: edu_taxonomy_diagnosis_session
- 映射对象: SQLAlchemy model for edu_taxonomy_diagnosis_session
- 主写功能: unknown
- 读取功能: unknown
- DAO/Mapper/Entity: SQLAlchemy model + service layer
- DDL/SQL证据: Base.metadata and migrations/versions
- 结论级别: 事实（表与字段）；访问归属待补

## TBL-edu-taxonomy-sync-run - edu_taxonomy_sync_run
- ID: TBL-edu-taxonomy-sync-run
- 对象类型: table
- 所有者: backend
- 业务含义: edu_taxonomy_sync_run
- 映射对象: SQLAlchemy model for edu_taxonomy_sync_run
- 主写功能: unknown
- 读取功能: unknown
- DAO/Mapper/Entity: SQLAlchemy model + service layer
- DDL/SQL证据: Base.metadata and migrations/versions
- 结论级别: 事实（表与字段）；访问归属待补

## TBL-edu-teaching-assignment - edu_teaching_assignment
- ID: TBL-edu-teaching-assignment
- 对象类型: table
- 所有者: backend
- 业务含义: edu_teaching_assignment
- 映射对象: SQLAlchemy model for edu_teaching_assignment
- 主写功能: unknown
- 读取功能: unknown
- DAO/Mapper/Entity: SQLAlchemy model + service layer
- DDL/SQL证据: Base.metadata and migrations/versions
- 结论级别: 事实（表与字段）；访问归属待补

## TBL-edu-tutor-feedback - edu_tutor_feedback
- ID: TBL-edu-tutor-feedback
- 对象类型: table
- 所有者: backend
- 业务含义: edu_tutor_feedback
- 映射对象: SQLAlchemy model for edu_tutor_feedback
- 主写功能: unknown
- 读取功能: unknown
- DAO/Mapper/Entity: SQLAlchemy model + service layer
- DDL/SQL证据: Base.metadata and migrations/versions
- 结论级别: 事实（表与字段）；访问归属待补

## TBL-edu-wrong-question - edu_wrong_question
- ID: TBL-edu-wrong-question
- 对象类型: table
- 所有者: backend
- 业务含义: edu_wrong_question
- 映射对象: SQLAlchemy model for edu_wrong_question
- 主写功能: unknown
- 读取功能: unknown
- DAO/Mapper/Entity: SQLAlchemy model + service layer
- DDL/SQL证据: Base.metadata and migrations/versions
- 结论级别: 事实（表与字段）；访问归属待补

## TBL-sys-agent-call-log - sys_agent_call_log
- ID: TBL-sys-agent-call-log
- 对象类型: table
- 所有者: backend
- 业务含义: sys_agent_call_log
- 映射对象: SQLAlchemy model for sys_agent_call_log
- 主写功能: unknown
- 读取功能: unknown
- DAO/Mapper/Entity: SQLAlchemy model + service layer
- DDL/SQL证据: Base.metadata and migrations/versions
- 结论级别: 事实（表与字段）；访问归属待补

## TBL-sys-agent-job - sys_agent_job
- ID: TBL-sys-agent-job
- 对象类型: table
- 所有者: backend
- 业务含义: sys_agent_job
- 映射对象: SQLAlchemy model for sys_agent_job
- 主写功能: unknown
- 读取功能: unknown
- DAO/Mapper/Entity: SQLAlchemy model + service layer
- DDL/SQL证据: Base.metadata and migrations/versions
- 结论级别: 事实（表与字段）；访问归属待补

## TBL-sys-agent-rate - sys_agent_rate
- ID: TBL-sys-agent-rate
- 对象类型: table
- 所有者: backend
- 业务含义: sys_agent_rate
- 映射对象: SQLAlchemy model for sys_agent_rate
- 主写功能: unknown
- 读取功能: unknown
- DAO/Mapper/Entity: SQLAlchemy model + service layer
- DDL/SQL证据: Base.metadata and migrations/versions
- 结论级别: 事实（表与字段）；访问归属待补

## TBL-sys-attachment - sys_attachment
- ID: TBL-sys-attachment
- 对象类型: table
- 所有者: backend
- 业务含义: sys_attachment
- 映射对象: SQLAlchemy model for sys_attachment
- 主写功能: unknown
- 读取功能: unknown
- DAO/Mapper/Entity: SQLAlchemy model + service layer
- DDL/SQL证据: Base.metadata and migrations/versions
- 结论级别: 事实（表与字段）；访问归属待补

## TBL-sys-captcha - sys_captcha
- ID: TBL-sys-captcha
- 对象类型: table
- 所有者: backend
- 业务含义: sys_captcha
- 映射对象: SQLAlchemy model for sys_captcha
- 主写功能: unknown
- 读取功能: unknown
- DAO/Mapper/Entity: SQLAlchemy model + service layer
- DDL/SQL证据: Base.metadata and migrations/versions
- 结论级别: 事实（表与字段）；访问归属待补

## TBL-sys-config - sys_config
- ID: TBL-sys-config
- 对象类型: table
- 所有者: backend
- 业务含义: sys_config
- 映射对象: SQLAlchemy model for sys_config
- 主写功能: unknown
- 读取功能: unknown
- DAO/Mapper/Entity: SQLAlchemy model + service layer
- DDL/SQL证据: Base.metadata and migrations/versions
- 结论级别: 事实（表与字段）；访问归属待补

## TBL-sys-error-log - sys_error_log
- ID: TBL-sys-error-log
- 对象类型: table
- 所有者: backend
- 业务含义: sys_error_log
- 映射对象: SQLAlchemy model for sys_error_log
- 主写功能: unknown
- 读取功能: unknown
- DAO/Mapper/Entity: SQLAlchemy model + service layer
- DDL/SQL证据: Base.metadata and migrations/versions
- 结论级别: 事实（表与字段）；访问归属待补

## TBL-sys-job-execution-log - sys_job_execution_log
- ID: TBL-sys-job-execution-log
- 对象类型: table
- 所有者: backend
- 业务含义: sys_job_execution_log
- 映射对象: SQLAlchemy model for sys_job_execution_log
- 主写功能: unknown
- 读取功能: unknown
- DAO/Mapper/Entity: SQLAlchemy model + service layer
- DDL/SQL证据: Base.metadata and migrations/versions
- 结论级别: 事实（表与字段）；访问归属待补

## TBL-sys-job-lock - sys_job_lock
- ID: TBL-sys-job-lock
- 对象类型: table
- 所有者: backend
- 业务含义: sys_job_lock
- 映射对象: SQLAlchemy model for sys_job_lock
- 主写功能: unknown
- 读取功能: unknown
- DAO/Mapper/Entity: SQLAlchemy model + service layer
- DDL/SQL证据: Base.metadata and migrations/versions
- 结论级别: 事实（表与字段）；访问归属待补

## TBL-sys-llm-breaker - sys_llm_breaker
- ID: TBL-sys-llm-breaker
- 对象类型: table
- 所有者: backend
- 业务含义: sys_llm_breaker
- 映射对象: SQLAlchemy model for sys_llm_breaker
- 主写功能: unknown
- 读取功能: unknown
- DAO/Mapper/Entity: SQLAlchemy model + service layer
- DDL/SQL证据: Base.metadata and migrations/versions
- 结论级别: 事实（表与字段）；访问归属待补

## TBL-sys-login-log - sys_login_log
- ID: TBL-sys-login-log
- 对象类型: table
- 所有者: backend
- 业务含义: sys_login_log
- 映射对象: SQLAlchemy model for sys_login_log
- 主写功能: unknown
- 读取功能: unknown
- DAO/Mapper/Entity: SQLAlchemy model + service layer
- DDL/SQL证据: Base.metadata and migrations/versions
- 结论级别: 事实（表与字段）；访问归属待补

## TBL-sys-notification - sys_notification
- ID: TBL-sys-notification
- 对象类型: table
- 所有者: backend
- 业务含义: sys_notification
- 映射对象: SQLAlchemy model for sys_notification
- 主写功能: unknown
- 读取功能: unknown
- DAO/Mapper/Entity: SQLAlchemy model + service layer
- DDL/SQL证据: Base.metadata and migrations/versions
- 结论级别: 事实（表与字段）；访问归属待补

## TBL-sys-notify-pref - sys_notify_pref
- ID: TBL-sys-notify-pref
- 对象类型: table
- 所有者: backend
- 业务含义: sys_notify_pref
- 映射对象: SQLAlchemy model for sys_notify_pref
- 主写功能: unknown
- 读取功能: unknown
- DAO/Mapper/Entity: SQLAlchemy model + service layer
- DDL/SQL证据: Base.metadata and migrations/versions
- 结论级别: 事实（表与字段）；访问归属待补

## TBL-sys-operation-log - sys_operation_log
- ID: TBL-sys-operation-log
- 对象类型: table
- 所有者: backend
- 业务含义: sys_operation_log
- 映射对象: SQLAlchemy model for sys_operation_log
- 主写功能: unknown
- 读取功能: unknown
- DAO/Mapper/Entity: SQLAlchemy model + service layer
- DDL/SQL证据: Base.metadata and migrations/versions
- 结论级别: 事实（表与字段）；访问归属待补

## TBL-sys-permission - sys_permission
- ID: TBL-sys-permission
- 对象类型: table
- 所有者: backend
- 业务含义: sys_permission
- 映射对象: SQLAlchemy model for sys_permission
- 主写功能: unknown
- 读取功能: unknown
- DAO/Mapper/Entity: SQLAlchemy model + service layer
- DDL/SQL证据: Base.metadata and migrations/versions
- 结论级别: 事实（表与字段）；访问归属待补

## TBL-sys-rate-limit - sys_rate_limit
- ID: TBL-sys-rate-limit
- 对象类型: table
- 所有者: backend
- 业务含义: sys_rate_limit
- 映射对象: SQLAlchemy model for sys_rate_limit
- 主写功能: unknown
- 读取功能: unknown
- DAO/Mapper/Entity: SQLAlchemy model + service layer
- DDL/SQL证据: Base.metadata and migrations/versions
- 结论级别: 事实（表与字段）；访问归属待补

## TBL-sys-registration - sys_registration
- ID: TBL-sys-registration
- 对象类型: table
- 所有者: backend
- 业务含义: sys_registration
- 映射对象: SQLAlchemy model for sys_registration
- 主写功能: unknown
- 读取功能: unknown
- DAO/Mapper/Entity: SQLAlchemy model + service layer
- DDL/SQL证据: Base.metadata and migrations/versions
- 结论级别: 事实（表与字段）；访问归属待补

## TBL-sys-reset-code - sys_reset_code
- ID: TBL-sys-reset-code
- 对象类型: table
- 所有者: backend
- 业务含义: sys_reset_code
- 映射对象: SQLAlchemy model for sys_reset_code
- 主写功能: unknown
- 读取功能: unknown
- DAO/Mapper/Entity: SQLAlchemy model + service layer
- DDL/SQL证据: Base.metadata and migrations/versions
- 结论级别: 事实（表与字段）；访问归属待补

## TBL-sys-revoked-token - sys_revoked_token
- ID: TBL-sys-revoked-token
- 对象类型: table
- 所有者: backend
- 业务含义: sys_revoked_token
- 映射对象: SQLAlchemy model for sys_revoked_token
- 主写功能: unknown
- 读取功能: unknown
- DAO/Mapper/Entity: SQLAlchemy model + service layer
- DDL/SQL证据: Base.metadata and migrations/versions
- 结论级别: 事实（表与字段）；访问归属待补

## TBL-sys-role - sys_role
- ID: TBL-sys-role
- 对象类型: table
- 所有者: backend
- 业务含义: sys_role
- 映射对象: SQLAlchemy model for sys_role
- 主写功能: unknown
- 读取功能: unknown
- DAO/Mapper/Entity: SQLAlchemy model + service layer
- DDL/SQL证据: Base.metadata and migrations/versions
- 结论级别: 事实（表与字段）；访问归属待补

## TBL-sys-role-permission - sys_role_permission
- ID: TBL-sys-role-permission
- 对象类型: table
- 所有者: backend
- 业务含义: sys_role_permission
- 映射对象: SQLAlchemy model for sys_role_permission
- 主写功能: unknown
- 读取功能: unknown
- DAO/Mapper/Entity: SQLAlchemy model + service layer
- DDL/SQL证据: Base.metadata and migrations/versions
- 结论级别: 事实（表与字段）；访问归属待补

## TBL-sys-scheduled-job - sys_scheduled_job
- ID: TBL-sys-scheduled-job
- 对象类型: table
- 所有者: backend
- 业务含义: sys_scheduled_job
- 映射对象: SQLAlchemy model for sys_scheduled_job
- 主写功能: unknown
- 读取功能: unknown
- DAO/Mapper/Entity: SQLAlchemy model + service layer
- DDL/SQL证据: Base.metadata and migrations/versions
- 结论级别: 事实（表与字段）；访问归属待补

## TBL-sys-user - sys_user
- ID: TBL-sys-user
- 对象类型: table
- 所有者: backend
- 业务含义: sys_user
- 映射对象: SQLAlchemy model for sys_user
- 主写功能: unknown
- 读取功能: unknown
- DAO/Mapper/Entity: SQLAlchemy model + service layer
- DDL/SQL证据: Base.metadata and migrations/versions
- 结论级别: 事实（表与字段）；访问归属待补

## TBL-sys-user-role - sys_user_role
- ID: TBL-sys-user-role
- 对象类型: table
- 所有者: backend
- 业务含义: sys_user_role
- 映射对象: SQLAlchemy model for sys_user_role
- 主写功能: unknown
- 读取功能: unknown
- DAO/Mapper/Entity: SQLAlchemy model + service layer
- DDL/SQL证据: Base.metadata and migrations/versions
- 结论级别: 事实（表与字段）；访问归属待补

## TBL-sys-user-token-revocation - sys_user_token_revocation
- ID: TBL-sys-user-token-revocation
- 对象类型: table
- 所有者: backend
- 业务含义: sys_user_token_revocation
- 映射对象: SQLAlchemy model for sys_user_token_revocation
- 主写功能: unknown
- 读取功能: unknown
- DAO/Mapper/Entity: SQLAlchemy model + service layer
- DDL/SQL证据: Base.metadata and migrations/versions
- 结论级别: 事实（表与字段）；访问归属待补
