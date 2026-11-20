# 无菜单功能索引

- Output Language: zh-CN
- Status: in-progress

## JOB-clean-expired-exams
- Handler: app.services.task_jobs.clean_expired_exams
- Cron: 0 3 * * *
- Trigger Type: scheduled
- Business Result: 归档已结束的超期考试
- Failure Discovery: sys_job_execution_log + admin notification
- Manual Intervention: /jobs 手动执行或启停

## JOB-generate-daily-report
- Handler: app.services.task_jobs.generate_daily_report
- Cron: 0 7 * * *
- Trigger Type: scheduled
- Business Result: 生成前一日学习与考试数据报表
- Failure Discovery: sys_job_execution_log + admin notification
- Manual Intervention: /jobs 手动执行或启停

## JOB-clean-temp-attachments
- Handler: app.services.task_jobs.clean_temp_attachments
- Cron: 0 4 * * *
- Trigger Type: scheduled
- Business Result: 清理超过 7 天未绑定业务附件
- Failure Discovery: sys_job_execution_log + admin notification
- Manual Intervention: /jobs 手动执行或启停

## JOB-push-review-reminders
- Handler: app.services.task_jobs.push_review_reminders
- Cron: 0 8 * * *
- Trigger Type: scheduled
- Business Result: 按艾宾浩斯计划推送复习提醒
- Failure Discovery: sys_job_execution_log + admin notification
- Manual Intervention: /jobs 手动执行或启停

## JOB-generate-weekly-report
- Handler: app.services.task_jobs.generate_weekly_report
- Cron: 0 8 * * 1
- Trigger Type: scheduled
- Business Result: 生成上周学情周报
- Failure Discovery: sys_job_execution_log + admin notification
- Manual Intervention: /jobs 手动执行或启停

## JOB-publish-scheduled-tasks
- Handler: app.services.task_jobs.publish_scheduled_tasks
- Cron: * * * * *
- Trigger Type: scheduled
- Business Result: 激活 publish_at 到期的草稿任务并补发通知
- Failure Discovery: sys_job_execution_log + admin notification
- Manual Intervention: /jobs 手动执行或启停

## JOB-clean-old-logs
- Handler: app.services.task_jobs.clean_old_logs
- Cron: 30 4 * * *
- Trigger Type: scheduled
- Business Result: 清理过期日志、任务记录和已读通知
- Failure Discovery: sys_job_execution_log + admin notification
- Manual Intervention: /jobs 手动执行或启停

## JOB-clean-ai-draft-questions
- Handler: app.services.task_jobs.clean_ai_draft_questions
- Cron: 0 5 * * *
- Trigger Type: scheduled
- Business Result: 清理 7 天前无人引用的 AI 草稿题
- Failure Discovery: sys_job_execution_log + admin notification
- Manual Intervention: /jobs 手动执行或启停

## FUNC-jobs-clean-expired-exams
- Trigger Entries: JOB-clean-expired-exams
- Trigger Type: scheduled
- Why Menu-Less: 系统内部定时任务，不面向人工页面。
- Real Upstream: APScheduler
- Business Result Consumer: admin, student, teacher
- Failure Discovery: sys_job_execution_log + notification
- Manual Intervention: /jobs 手动执行或启停





## FUNC-flow-flow-definitions-sync
- Trigger Entries: API-op-0022
- Trigger Type: api-only or batch
- Why Menu-Less: API/批处理功能，不依赖前端菜单。
- Real Upstream: HTTP client or scheduler
- Business Result Consumer: relevant role user or admin
- Failure Discovery: API response, job execution log, audit log
- Manual Intervention: admin console, retry API, or job toggle

## FUNC-taxonomy-sync-system-taxonomy-sync
- Trigger Entries: API-op-0042
- Trigger Type: api-only or batch
- Why Menu-Less: API/批处理功能，不依赖前端菜单。
- Real Upstream: HTTP client or scheduler
- Business Result Consumer: relevant role user or admin
- Failure Discovery: API response, job execution log, audit log
- Manual Intervention: admin console, retry API, or job toggle

## FUNC-taxonomy-sync-system-taxonomy-sync-preview
- Trigger Entries: API-op-0043
- Trigger Type: api-only or batch
- Why Menu-Less: API/批处理功能，不依赖前端菜单。
- Real Upstream: HTTP client or scheduler
- Business Result Consumer: relevant role user or admin
- Failure Discovery: API response, job execution log, audit log
- Manual Intervention: admin console, retry API, or job toggle

## FUNC-taxonomy-sync-system-taxonomy-sync-apply
- Trigger Entries: API-op-0044
- Trigger Type: api-only or batch
- Why Menu-Less: API/批处理功能，不依赖前端菜单。
- Real Upstream: HTTP client or scheduler
- Business Result Consumer: relevant role user or admin
- Failure Discovery: API response, job execution log, audit log
- Manual Intervention: admin console, retry API, or job toggle

## FUNC-taxonomy-sync-system-taxonomy-sync-run-id-restore
- Trigger Entries: API-op-0045
- Trigger Type: api-only or batch
- Why Menu-Less: API/批处理功能，不依赖前端菜单。
- Real Upstream: HTTP client or scheduler
- Business Result Consumer: relevant role user or admin
- Failure Discovery: API response, job execution log, audit log
- Manual Intervention: admin console, retry API, or job toggle

## FUNC-teacher-class-edu-classes-class-id-students-export
- Trigger Entries: API-op-0089
- Trigger Type: api-only or batch
- Why Menu-Less: API/批处理功能，不依赖前端菜单。
- Real Upstream: HTTP client or scheduler
- Business Result Consumer: relevant role user or admin
- Failure Discovery: API response, job execution log, audit log
- Manual Intervention: admin console, retry API, or job toggle

## FUNC-knowledge-edu-knowledge-export
- Trigger Entries: API-op-0109
- Trigger Type: api-only or batch
- Why Menu-Less: API/批处理功能，不依赖前端菜单。
- Real Upstream: HTTP client or scheduler
- Business Result Consumer: relevant role user or admin
- Failure Discovery: API response, job execution log, audit log
- Manual Intervention: admin console, retry API, or job toggle

## FUNC-question-question-questions-export
- Trigger Entries: API-op-0148
- Trigger Type: api-only or batch
- Why Menu-Less: API/批处理功能，不依赖前端菜单。
- Real Upstream: HTTP client or scheduler
- Business Result Consumer: relevant role user or admin
- Failure Discovery: API response, job execution log, audit log
- Manual Intervention: admin console, retry API, or job toggle

## FUNC-question-question-papers-paper-id-export
- Trigger Entries: API-op-0159
- Trigger Type: api-only or batch
- Why Menu-Less: API/批处理功能，不依赖前端菜单。
- Real Upstream: HTTP client or scheduler
- Business Result Consumer: relevant role user or admin
- Failure Discovery: API response, job execution log, audit log
- Manual Intervention: admin console, retry API, or job toggle

## FUNC-question-question-papers-paper-id-export-docx
- Trigger Entries: API-op-0194
- Trigger Type: api-only or batch
- Why Menu-Less: API/批处理功能，不依赖前端菜单。
- Real Upstream: HTTP client or scheduler
- Business Result Consumer: relevant role user or admin
- Failure Discovery: API response, job execution log, audit log
- Manual Intervention: admin console, retry API, or job toggle

## FUNC-question-question-papers-paper-id-export-pdf
- Trigger Entries: API-op-0195
- Trigger Type: api-only or batch
- Why Menu-Less: API/批处理功能，不依赖前端菜单。
- Real Upstream: HTTP client or scheduler
- Business Result Consumer: relevant role user or admin
- Failure Discovery: API response, job execution log, audit log
- Manual Intervention: admin console, retry API, or job toggle

## FUNC-question-question-papers-paper-id-export-answer-sheet
- Trigger Entries: API-op-0196
- Trigger Type: api-only or batch
- Why Menu-Less: API/批处理功能，不依赖前端菜单。
- Real Upstream: HTTP client or scheduler
- Business Result Consumer: relevant role user or admin
- Failure Discovery: API response, job execution log, audit log
- Manual Intervention: admin console, retry API, or job toggle

## FUNC-question-question-papers-paper-id-export-html
- Trigger Entries: API-op-0197
- Trigger Type: api-only or batch
- Why Menu-Less: API/批处理功能，不依赖前端菜单。
- Real Upstream: HTTP client or scheduler
- Business Result Consumer: relevant role user or admin
- Failure Discovery: API response, job execution log, audit log
- Manual Intervention: admin console, retry API, or job toggle

## FUNC-question-question-papers-paper-id-export-jobs
- Trigger Entries: API-op-0198
- Trigger Type: api-only or batch
- Why Menu-Less: API/批处理功能，不依赖前端菜单。
- Real Upstream: HTTP client or scheduler
- Business Result Consumer: relevant role user or admin
- Failure Discovery: API response, job execution log, audit log
- Manual Intervention: admin console, retry API, or job toggle

## FUNC-question-question-papers-export-jobs-job-id
- Trigger Entries: API-op-0199
- Trigger Type: api-only or batch
- Why Menu-Less: API/批处理功能，不依赖前端菜单。
- Real Upstream: HTTP client or scheduler
- Business Result Consumer: relevant role user or admin
- Failure Discovery: API response, job execution log, audit log
- Manual Intervention: admin console, retry API, or job toggle

## FUNC-question-question-papers-export-jobs-job-id-file
- Trigger Entries: API-op-0200
- Trigger Type: api-only or batch
- Why Menu-Less: API/批处理功能，不依赖前端菜单。
- Real Upstream: HTTP client or scheduler
- Business Result Consumer: relevant role user or admin
- Failure Discovery: API response, job execution log, audit log
- Manual Intervention: admin console, retry API, or job toggle

## FUNC-question-question-papers-compose-ai-async
- Trigger Entries: API-op-0201
- Trigger Type: api-only or batch
- Why Menu-Less: API/批处理功能，不依赖前端菜单。
- Real Upstream: HTTP client or scheduler
- Business Result Consumer: relevant role user or admin
- Failure Discovery: API response, job execution log, audit log
- Manual Intervention: admin console, retry API, or job toggle

## FUNC-question-question-papers-compose-jobs-job-id
- Trigger Entries: API-op-0202
- Trigger Type: api-only or batch
- Why Menu-Less: API/批处理功能，不依赖前端菜单。
- Real Upstream: HTTP client or scheduler
- Business Result Consumer: relevant role user or admin
- Failure Discovery: API response, job execution log, audit log
- Manual Intervention: admin console, retry API, or job toggle

## FUNC-question-question-papers-compose-jobs-job-id-cancel
- Trigger Entries: API-op-0203
- Trigger Type: api-only or batch
- Why Menu-Less: API/批处理功能，不依赖前端菜单。
- Real Upstream: HTTP client or scheduler
- Business Result Consumer: relevant role user or admin
- Failure Discovery: API response, job execution log, audit log
- Manual Intervention: admin console, retry API, or job toggle

## FUNC-learning-learning-notes-note-id-export
- Trigger Entries: API-op-0240
- Trigger Type: api-only or batch
- Why Menu-Less: API/批处理功能，不依赖前端菜单。
- Real Upstream: HTTP client or scheduler
- Business Result Consumer: relevant role user or admin
- Failure Discovery: API response, job execution log, audit log
- Manual Intervention: admin console, retry API, or job toggle

## FUNC-learning-learning-wrong-questions-export
- Trigger Entries: API-op-0245
- Trigger Type: api-only or batch
- Why Menu-Less: API/批处理功能，不依赖前端菜单。
- Real Upstream: HTTP client or scheduler
- Business Result Consumer: relevant role user or admin
- Failure Discovery: API response, job execution log, audit log
- Manual Intervention: admin console, retry API, or job toggle

## FUNC-ai-agent-agent-chat-stream
- Trigger Entries: API-op-0272
- Trigger Type: api-only or batch
- Why Menu-Less: API/批处理功能，不依赖前端菜单。
- Real Upstream: HTTP client or scheduler
- Business Result Consumer: relevant role user or admin
- Failure Discovery: API response, job execution log, audit log
- Manual Intervention: admin console, retry API, or job toggle

## FUNC-ai-agent-agent-jobs
- Trigger Entries: API-op-0279, API-op-0280
- Trigger Type: api-only or batch
- Why Menu-Less: API/批处理功能，不依赖前端菜单。
- Real Upstream: HTTP client or scheduler
- Business Result Consumer: relevant role user or admin
- Failure Discovery: API response, job execution log, audit log
- Manual Intervention: admin console, retry API, or job toggle

## FUNC-ai-agent-agent-jobs-job-id
- Trigger Entries: API-op-0281
- Trigger Type: api-only or batch
- Why Menu-Less: API/批处理功能，不依赖前端菜单。
- Real Upstream: HTTP client or scheduler
- Business Result Consumer: relevant role user or admin
- Failure Discovery: API response, job execution log, audit log
- Manual Intervention: admin console, retry API, or job toggle

## FUNC-report-report-export-excel
- Trigger Entries: API-op-0297
- Trigger Type: api-only or batch
- Why Menu-Less: API/批处理功能，不依赖前端菜单。
- Real Upstream: HTTP client or scheduler
- Business Result Consumer: relevant role user or admin
- Failure Discovery: API response, job execution log, audit log
- Manual Intervention: admin console, retry API, or job toggle

## FUNC-log-logs-export
- Trigger Entries: API-op-0301
- Trigger Type: api-only or batch
- Why Menu-Less: API/批处理功能，不依赖前端菜单。
- Real Upstream: HTTP client or scheduler
- Business Result Consumer: relevant role user or admin
- Failure Discovery: API response, job execution log, audit log
- Manual Intervention: admin console, retry API, or job toggle

## FUNC-job-jobs-handlers
- Trigger Entries: API-op-0302
- Trigger Type: api-only or batch
- Why Menu-Less: API/批处理功能，不依赖前端菜单。
- Real Upstream: HTTP client or scheduler
- Business Result Consumer: relevant role user or admin
- Failure Discovery: API response, job execution log, audit log
- Manual Intervention: admin console, retry API, or job toggle

## FUNC-job-jobs
- Trigger Entries: API-op-0303, API-op-0304
- Trigger Type: api-only or batch
- Why Menu-Less: API/批处理功能，不依赖前端菜单。
- Real Upstream: HTTP client or scheduler
- Business Result Consumer: relevant role user or admin
- Failure Discovery: API response, job execution log, audit log
- Manual Intervention: admin console, retry API, or job toggle

## FUNC-job-jobs-job-id
- Trigger Entries: API-op-0305, API-op-0306
- Trigger Type: api-only or batch
- Why Menu-Less: API/批处理功能，不依赖前端菜单。
- Real Upstream: HTTP client or scheduler
- Business Result Consumer: relevant role user or admin
- Failure Discovery: API response, job execution log, audit log
- Manual Intervention: admin console, retry API, or job toggle

## FUNC-job-jobs-job-id-toggle
- Trigger Entries: API-op-0307
- Trigger Type: api-only or batch
- Why Menu-Less: API/批处理功能，不依赖前端菜单。
- Real Upstream: HTTP client or scheduler
- Business Result Consumer: relevant role user or admin
- Failure Discovery: API response, job execution log, audit log
- Manual Intervention: admin console, retry API, or job toggle

## FUNC-job-jobs-job-id-run
- Trigger Entries: API-op-0308
- Trigger Type: api-only or batch
- Why Menu-Less: API/批处理功能，不依赖前端菜单。
- Real Upstream: HTTP client or scheduler
- Business Result Consumer: relevant role user or admin
- Failure Discovery: API response, job execution log, audit log
- Manual Intervention: admin console, retry API, or job toggle

## FUNC-job-jobs-status
- Trigger Entries: API-op-0309
- Trigger Type: api-only or batch
- Why Menu-Less: API/批处理功能，不依赖前端菜单。
- Real Upstream: HTTP client or scheduler
- Business Result Consumer: relevant role user or admin
- Failure Discovery: API response, job execution log, audit log
- Manual Intervention: admin console, retry API, or job toggle

## FUNC-job-jobs-job-id-executions
- Trigger Entries: API-op-0310
- Trigger Type: api-only or batch
- Why Menu-Less: API/批处理功能，不依赖前端菜单。
- Real Upstream: HTTP client or scheduler
- Business Result Consumer: relevant role user or admin
- Failure Discovery: API response, job execution log, audit log
- Manual Intervention: admin console, retry API, or job toggle

## FUNC-lesson-lesson-ai-jobs-job-id
- Trigger Entries: API-op-0332
- Trigger Type: api-only or batch
- Why Menu-Less: API/批处理功能，不依赖前端菜单。
- Real Upstream: HTTP client or scheduler
- Business Result Consumer: relevant role user or admin
- Failure Discovery: API response, job execution log, audit log
- Manual Intervention: admin console, retry API, or job toggle

## FUNC-lesson-lesson-ai-jobs-job-id-cancel
- Trigger Entries: API-op-0333
- Trigger Type: api-only or batch
- Why Menu-Less: API/批处理功能，不依赖前端菜单。
- Real Upstream: HTTP client or scheduler
- Business Result Consumer: relevant role user or admin
- Failure Discovery: API response, job execution log, audit log
- Manual Intervention: admin console, retry API, or job toggle

## FUNC-lesson-lesson-ai-jobs
- Trigger Entries: API-op-0334
- Trigger Type: api-only or batch
- Why Menu-Less: API/批处理功能，不依赖前端菜单。
- Real Upstream: HTTP client or scheduler
- Business Result Consumer: relevant role user or admin
- Failure Discovery: API response, job execution log, audit log
- Manual Intervention: admin console, retry API, or job toggle

## FUNC-lesson-lesson-ai-jobs-job-id-save
- Trigger Entries: API-op-0335
- Trigger Type: api-only or batch
- Why Menu-Less: API/批处理功能，不依赖前端菜单。
- Real Upstream: HTTP client or scheduler
- Business Result Consumer: relevant role user or admin
- Failure Discovery: API response, job execution log, audit log
- Manual Intervention: admin console, retry API, or job toggle

## FUNC-lesson-lesson-ai-jobs-job-id-export
- Trigger Entries: API-op-0336
- Trigger Type: api-only or batch
- Why Menu-Less: API/批处理功能，不依赖前端菜单。
- Real Upstream: HTTP client or scheduler
- Business Result Consumer: relevant role user or admin
- Failure Discovery: API response, job execution log, audit log
- Manual Intervention: admin console, retry API, or job toggle

## FUNC-health-health
- Trigger Entries: API-op-0338
- Trigger Type: api-only or batch
- Why Menu-Less: API/批处理功能，不依赖前端菜单。
- Real Upstream: HTTP client or scheduler
- Business Result Consumer: relevant role user or admin
- Failure Discovery: API response, job execution log, audit log
- Manual Intervention: admin console, retry API, or job toggle

## FUNC-ready-ready
- Trigger Entries: API-op-0339
- Trigger Type: api-only or batch
- Why Menu-Less: API/批处理功能，不依赖前端菜单。
- Real Upstream: HTTP client or scheduler
- Business Result Consumer: relevant role user or admin
- Failure Discovery: API response, job execution log, audit log
- Manual Intervention: admin console, retry API, or job toggle

## FUNC-jobs-clean-expired-exams
- Trigger Entries: JOB-clean-expired-exams
- Trigger Type: api-only or batch
- Why Menu-Less: API/批处理功能，不依赖前端菜单。
- Real Upstream: HTTP client or scheduler
- Business Result Consumer: relevant role user or admin
- Failure Discovery: API response, job execution log, audit log
- Manual Intervention: admin console, retry API, or job toggle
