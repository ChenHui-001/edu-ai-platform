# 数据所有权

- Output Language: zh-CN
- 状态: in-progress

| TBL ID | Physical Table | Primary Owner | Shared Writers | Conflict Handling | Evidence |
|---|---|---|---|---|---|
| TBL-sys-user | sys_user | MOD-backend-fastapi / auth & system service | registration audit, flow orchestration, user management | service-level validation + transaction | service code |
| TBL-sys-role | sys_role | MOD-backend-fastapi / system service | init_db seeds, role management | upsert + UI validation | service code |
| TBL-sys-permission | sys_permission | MOD-backend-fastapi / init_db & system service | role assignment | idempotent init | service code |
| TBL-sys-registration | sys_registration | MOD-backend-fastapi / auth service | registration API, admin audit, flow callback | flow orchestration + audit | service code |
| TBL-sys-config | sys_config | MOD-backend-fastapi / ai_config_service | system config API | env override + DB precedence | ai_config_service.py |
| TBL-edu-knowledge-point | edu_knowledge_point | MOD-backend-fastapi / knowledge service | taxonomy sync, AI enrichment, manual CRUD | optimistic/check-only sync | knowledge.py, taxonomy_sync.py |
| TBL-edu-question | edu_question | MOD-backend-fastapi / question service | manual CRUD, AI drafts, import/export | quality status and draft cleanup | question.py |
| TBL-edu-paper | edu_paper | MOD-backend-fastapi / paper service | compose, edit, export, favorite | versioned updates | paper_compose*.py |
| TBL-edu-task | edu_task | MOD-backend-fastapi / task service | task publish/edit/delete, scheduled publish | idempotent create + scheduler lock | task.py, task_jobs.py |
| TBL-edu-submission | edu_submission | MOD-backend-fastapi / grading service | student submit, grading, publishing | transactional state transitions | grading.py |
| TBL-edu-flow-instance | edu_flow_instance | MOD-backend-fastapi / flow engine | flow orchestration, approval, transfer | engine-managed transitions | flow_engine.py |
| 其余 51 张表 | 见 database-model.md | MOD-backend-fastapi | 按服务域读写 | service transaction | model metadata + service calls |
