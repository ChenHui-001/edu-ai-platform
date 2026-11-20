# 接口索引

- Output Language: zh-CN
- Status: in-progress
- OpenAPI Operations: 339

| API ID | Method | Path | Type | Direction | Provider | Consumer Function | Controller | Request Object | Response Object | Auth And Permission | Idempotency | Downstream | Physical Table Operations | Compatibility Risk | Evidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| API-op-0001 | GET | /api/v1/auth/captcha | REST | inbound | backend | FUNC-auth-auth-captcha | get_captcha_api_v1_auth_captcha_get | none | 200 | 获取图形验证码 | FUNC-auth-auth-captcha | unknown | FUNC-auth-auth-captcha | unknown | openapi.json + source code |
| API-op-0002 | POST | /api/v1/auth/register | REST | inbound | backend | FUNC-auth-auth-register | register_api_v1_auth_register_post | application/json | 200,422 | 用户注册（待审批） | FUNC-auth-auth-register | unknown | FUNC-auth-auth-register | unknown | openapi.json + source code |
| API-op-0003 | GET | /api/v1/auth/registrations | REST | inbound | backend | FUNC-auth-auth-registrations | list_registrations_api_v1_auth_registrations_get | none | 200,422 | 注册申请列表（管理员） | FUNC-auth-auth-registrations | unknown | FUNC-auth-auth-registrations | unknown | openapi.json + source code |
| API-op-0004 | POST | /api/v1/auth/registrations/audit | REST | inbound | backend | FUNC-auth-auth-registrations-audit | audit_registration_api_v1_auth_registrations_audit_post | application/json | 200,422 | 审批注册申请（管理员） | FUNC-auth-auth-registrations-audit | unknown | FUNC-auth-auth-registrations-audit | unknown | openapi.json + source code |
| API-op-0005 | POST | /api/v1/auth/login | REST | inbound | backend | FUNC-auth-auth-login | login_api_v1_auth_login_post | application/json | 200,422 | 账号密码登录 | FUNC-auth-auth-login | unknown | FUNC-auth-auth-login | unknown | openapi.json + source code |
| API-op-0006 | POST | /api/v1/auth/refresh | REST | inbound | backend | FUNC-auth-auth-refresh | refresh_token_api_v1_auth_refresh_post | application/json | 200,422 | 刷新访问令牌 | FUNC-auth-auth-refresh | unknown | FUNC-auth-auth-refresh | unknown | openapi.json + source code |
| API-op-0007 | GET | /api/v1/auth/profile | REST | inbound | backend | FUNC-auth-auth-profile | profile_api_v1_auth_profile_get | none | 200 | 获取当前用户信息 | FUNC-auth-auth-profile | unknown | FUNC-auth-auth-profile | unknown | openapi.json + source code |
| API-op-0008 | PUT | /api/v1/auth/profile | REST | inbound | backend | FUNC-auth-auth-profile | update_profile_api_v1_auth_profile_put | application/json | 200,422 | 更新个人资料 | FUNC-auth-auth-profile | unknown | FUNC-auth-auth-profile | unknown | openapi.json + source code |
| API-op-0009 | PUT | /api/v1/auth/password | REST | inbound | backend | FUNC-auth-auth-password | change_password_api_v1_auth_password_put | application/json | 200,422 | 修改密码 | FUNC-auth-auth-password | unknown | FUNC-auth-auth-password | unknown | openapi.json + source code |
| API-op-0010 | POST | /api/v1/auth/logout | REST | inbound | backend | FUNC-auth-auth-logout | logout_api_v1_auth_logout_post | application/json | 200,422 | 退出登录 | FUNC-auth-auth-logout | unknown | FUNC-auth-auth-logout | unknown | openapi.json + source code |
| API-op-0011 | POST | /api/v1/auth/forgot-password | REST | inbound | backend | FUNC-auth-auth-forgot-password | forgot_password_api_v1_auth_forgot_password_post | application/json | 200,422 | 找回密码（发送验证码） | FUNC-auth-auth-forgot-password | unknown | FUNC-auth-auth-forgot-password | unknown | openapi.json + source code |
| API-op-0012 | POST | /api/v1/auth/reset-password | REST | inbound | backend | FUNC-auth-auth-reset-password | reset_password_api_v1_auth_reset_password_post | application/json | 200,422 | 重置密码（验证码） | FUNC-auth-auth-reset-password | unknown | FUNC-auth-auth-reset-password | unknown | openapi.json + source code |
| API-op-0013 | GET | /api/v1/flow/todo | REST | inbound | backend | FUNC-flow-flow-todo | todo_list_api_v1_flow_todo_get | none | 200,422 | 我的待办 | FUNC-flow-flow-todo | unknown | FUNC-flow-flow-todo | unknown | openapi.json + source code |
| API-op-0014 | GET | /api/v1/flow/done | REST | inbound | backend | FUNC-flow-flow-done | done_list_api_v1_flow_done_get | none | 200,422 | 我的已办 | FUNC-flow-flow-done | unknown | FUNC-flow-flow-done | unknown | openapi.json + source code |
| API-op-0015 | GET | /api/v1/flow/instances | REST | inbound | backend | FUNC-flow-flow-instances | my_instances_api_v1_flow_instances_get | none | 200,422 | 我发起的流程 | FUNC-flow-flow-instances | unknown | FUNC-flow-flow-instances | unknown | openapi.json + source code |
| API-op-0016 | GET | /api/v1/flow/instances/{instance_id} | REST | inbound | backend | FUNC-flow-flow-instances-instance-id | instance_detail_api_v1_flow_instances__instance_id__get | none | 200,422 | 流程实例详情 | FUNC-flow-flow-instances-instance-id | unknown | FUNC-flow-flow-instances-instance-id | unknown | openapi.json + source code |
| API-op-0017 | POST | /api/v1/flow/tasks/{task_id}/claim | REST | inbound | backend | FUNC-flow-flow-tasks-task-id-claim | claim_task_api_v1_flow_tasks__task_id__claim_post | none | 200,422 | 认领待办 | FUNC-flow-flow-tasks-task-id-claim | unknown | FUNC-flow-flow-tasks-task-id-claim | unknown | openapi.json + source code |
| API-op-0018 | POST | /api/v1/flow/tasks/{task_id}/approve | REST | inbound | backend | FUNC-flow-flow-tasks-task-id-approve | approve_task_api_v1_flow_tasks__task_id__approve_post | application/json | 200,422 | 审批通过 | FUNC-flow-flow-tasks-task-id-approve | unknown | FUNC-flow-flow-tasks-task-id-approve | unknown | openapi.json + source code |
| API-op-0019 | POST | /api/v1/flow/tasks/{task_id}/reject | REST | inbound | backend | FUNC-flow-flow-tasks-task-id-reject | reject_task_api_v1_flow_tasks__task_id__reject_post | application/json | 200,422 | 审批驳回 | FUNC-flow-flow-tasks-task-id-reject | unknown | FUNC-flow-flow-tasks-task-id-reject | unknown | openapi.json + source code |
| API-op-0020 | POST | /api/v1/flow/tasks/{task_id}/return | REST | inbound | backend | FUNC-flow-flow-tasks-task-id-return | return_task_api_v1_flow_tasks__task_id__return_post | application/json | 200,422 | 退回重填 | FUNC-flow-flow-tasks-task-id-return | unknown | FUNC-flow-flow-tasks-task-id-return | unknown | openapi.json + source code |
| API-op-0021 | POST | /api/v1/flow/tasks/{task_id}/cancel | REST | inbound | backend | FUNC-flow-flow-tasks-task-id-cancel | cancel_task_api_v1_flow_tasks__task_id__cancel_post | application/json | 200,422 | 取消流程 | FUNC-flow-flow-tasks-task-id-cancel | unknown | FUNC-flow-flow-tasks-task-id-cancel | unknown | openapi.json + source code |
| API-op-0022 | POST | /api/v1/flow/definitions/sync | REST | inbound | backend | FUNC-flow-flow-definitions-sync | sync_definitions_api_v1_flow_definitions_sync_post | none | 200 | 同步流程定义 | FUNC-flow-flow-definitions-sync | unknown | FUNC-flow-flow-definitions-sync | unknown | openapi.json + source code |
| API-op-0023 | GET | /api/v1/flow/overdue | REST | inbound | backend | FUNC-flow-flow-overdue | overdue_list_api_v1_flow_overdue_get | none | 200,422 | 逾期待办 | FUNC-flow-flow-overdue | unknown | FUNC-flow-flow-overdue | unknown | openapi.json + source code |
| API-op-0024 | GET | /api/v1/flow/tasks/{task_id}/transfer-candidates | REST | inbound | backend | FUNC-flow-flow-tasks-task-id-transfer-candidates | transfer_candidates_api_v1_flow_tasks__task_id__transfer_candidates_get | none | 200,422 | 可转办人员 | FUNC-flow-flow-tasks-task-id-transfer-candidates | unknown | FUNC-flow-flow-tasks-task-id-transfer-candidates | unknown | openapi.json + source code |
| API-op-0025 | POST | /api/v1/flow/tasks/{task_id}/transfer | REST | inbound | backend | FUNC-flow-flow-tasks-task-id-transfer | transfer_task_api_v1_flow_tasks__task_id__transfer_post | application/json | 200,422 | 转办待办 | FUNC-flow-flow-tasks-task-id-transfer | unknown | FUNC-flow-flow-tasks-task-id-transfer | unknown | openapi.json + source code |
| API-op-0026 | POST | /api/v1/flow/tasks/{task_id}/urge | REST | inbound | backend | FUNC-flow-flow-tasks-task-id-urge | urge_task_api_v1_flow_tasks__task_id__urge_post | application/json | 200,422 | 催办 | FUNC-flow-flow-tasks-task-id-urge | unknown | FUNC-flow-flow-tasks-task-id-urge | unknown | openapi.json + source code |
| API-op-0027 | PUT | /api/v1/flow/tasks/{task_id}/deadline | REST | inbound | backend | FUNC-flow-flow-tasks-task-id-deadline | set_deadline_task_api_v1_flow_tasks__task_id__deadline_put | application/json | 200,422 | 设置待办截止时间 | FUNC-flow-flow-tasks-task-id-deadline | unknown | FUNC-flow-flow-tasks-task-id-deadline | unknown | openapi.json + source code |
| API-op-0028 | GET | /api/v1/learning/remediation | REST | inbound | backend | FUNC-learning-learning-remediation | plans_api_v1_learning_remediation_get | none | 200 | Plans | FUNC-learning-learning-remediation | unknown | FUNC-learning-learning-remediation | unknown | openapi.json + source code |
| API-op-0029 | POST | /api/v1/learning/remediation | REST | inbound | backend | FUNC-learning-learning-remediation | create_plan_api_v1_learning_remediation_post | application/json | 200,422 | Create Plan | FUNC-learning-learning-remediation | unknown | FUNC-learning-learning-remediation | unknown | openapi.json + source code |
| API-op-0030 | GET | /api/v1/learning/remediation/{plan_id} | REST | inbound | backend | FUNC-learning-learning-remediation-plan-id | plan_api_v1_learning_remediation__plan_id__get | none | 200,422 | Plan | FUNC-learning-learning-remediation-plan-id | unknown | FUNC-learning-learning-remediation-plan-id | unknown | openapi.json + source code |
| API-op-0031 | POST | /api/v1/learning/remediation/{plan_id}/quizzes | REST | inbound | backend | FUNC-learning-learning-remediation-plan-id-quizzes | start_api_v1_learning_remediation__plan_id__quizzes_post | application/json | 200,422 | Start | FUNC-learning-learning-remediation-plan-id-quizzes | unknown | FUNC-learning-learning-remediation-plan-id-quizzes | unknown | openapi.json + source code |
| API-op-0032 | POST | /api/v1/learning/remediation/{plan_id}/answers | REST | inbound | backend | FUNC-learning-learning-remediation-plan-id-answers | answer_api_v1_learning_remediation__plan_id__answers_post | application/json | 200,422 | Answer | FUNC-learning-learning-remediation-plan-id-answers | unknown | FUNC-learning-learning-remediation-plan-id-answers | unknown | openapi.json + source code |
| API-op-0033 | GET | /api/v1/teaching/graph | REST | inbound | backend | FUNC-teaching-graph-teaching-graph | graph_api_v1_teaching_graph_get | none | 200,422 | Graph | FUNC-teaching-graph-teaching-graph | unknown | FUNC-teaching-graph-teaching-graph | unknown | openapi.json + source code |
| API-op-0034 | POST | /api/v1/teaching/graph/assign | REST | inbound | backend | FUNC-teaching-graph-teaching-graph-assign | assign_api_v1_teaching_graph_assign_post | application/json | 200,422 | Assign | FUNC-teaching-graph-teaching-graph-assign | unknown | FUNC-teaching-graph-teaching-graph-assign | unknown | openapi.json + source code |
| API-op-0035 | GET | /api/v1/question/quality | REST | inbound | backend | FUNC-question-question-quality | inventory_api_v1_question_quality_get | none | 200,422 | Inventory | FUNC-question-question-quality | unknown | FUNC-question-question-quality | unknown | openapi.json + source code |
| API-op-0036 | POST | /api/v1/question/quality/publish | REST | inbound | backend | FUNC-question-question-quality-publish | publish_api_v1_question_quality_publish_post | application/json | 200,422 | Publish | FUNC-question-question-quality-publish | unknown | FUNC-question-question-quality-publish | unknown | openapi.json + source code |
| API-op-0037 | PUT | /api/v1/question/quality/{question_id}/visual | REST | inbound | backend | FUNC-question-question-quality-question-id-visual | visual_api_v1_question_quality__question_id__visual_put | application/json | 200,422 | Visual | FUNC-question-question-quality-question-id-visual | unknown | FUNC-question-question-quality-question-id-visual | unknown | openapi.json + source code |
| API-op-0038 | POST | /api/v1/learning/tutor | REST | inbound | backend | FUNC-learning-learning-tutor | ask_api_v1_learning_tutor_post | application/json | 200,422 | Ask | FUNC-learning-learning-tutor | unknown | FUNC-learning-learning-tutor | unknown | openapi.json + source code |
| API-op-0039 | POST | /api/v1/learning/tutor/feedback | REST | inbound | backend | FUNC-learning-learning-tutor-feedback | feedback_api_v1_learning_tutor_feedback_post | application/json | 200,422 | Feedback | FUNC-learning-learning-tutor-feedback | unknown | FUNC-learning-learning-tutor-feedback | unknown | openapi.json + source code |
| API-op-0040 | GET | /api/v1/learning/tutor/feedback | REST | inbound | backend | FUNC-learning-learning-tutor-feedback | feedback_list_api_v1_learning_tutor_feedback_get | none | 200,422 | Feedback List | FUNC-learning-learning-tutor-feedback | unknown | FUNC-learning-learning-tutor-feedback | unknown | openapi.json + source code |
| API-op-0041 | PUT | /api/v1/learning/tutor/feedback/{feedback_id} | REST | inbound | backend | FUNC-learning-learning-tutor-feedback-feedback-id | review_api_v1_learning_tutor_feedback__feedback_id__put | application/json | 200,422 | Review | FUNC-learning-learning-tutor-feedback-feedback-id | unknown | FUNC-learning-learning-tutor-feedback-feedback-id | unknown | openapi.json + source code |
| API-op-0042 | GET | /api/v1/system/taxonomy-sync | REST | inbound | backend | FUNC-taxonomy-sync-system-taxonomy-sync | history_api_v1_system_taxonomy_sync_get | none | 200 | History | FUNC-taxonomy-sync-system-taxonomy-sync | unknown | FUNC-taxonomy-sync-system-taxonomy-sync | unknown | openapi.json + source code |
| API-op-0043 | POST | /api/v1/system/taxonomy-sync/preview | REST | inbound | backend | FUNC-taxonomy-sync-system-taxonomy-sync-preview | preview_api_v1_system_taxonomy_sync_preview_post | application/json | 200,422 | Preview | FUNC-taxonomy-sync-system-taxonomy-sync-preview | unknown | FUNC-taxonomy-sync-system-taxonomy-sync-preview | unknown | openapi.json + source code |
| API-op-0044 | POST | /api/v1/system/taxonomy-sync/apply | REST | inbound | backend | FUNC-taxonomy-sync-system-taxonomy-sync-apply | apply_api_v1_system_taxonomy_sync_apply_post | application/json | 200,422 | Apply | FUNC-taxonomy-sync-system-taxonomy-sync-apply | unknown | FUNC-taxonomy-sync-system-taxonomy-sync-apply | unknown | openapi.json + source code |
| API-op-0045 | POST | /api/v1/system/taxonomy-sync/{run_id}/restore | REST | inbound | backend | FUNC-taxonomy-sync-system-taxonomy-sync-run-id-restore | restore_api_v1_system_taxonomy_sync__run_id__restore_post | none | 200,422 | Restore | FUNC-taxonomy-sync-system-taxonomy-sync-run-id-restore | unknown | FUNC-taxonomy-sync-system-taxonomy-sync-run-id-restore | unknown | openapi.json + source code |
| API-op-0046 | GET | /api/v1/system/users | REST | inbound | backend | FUNC-admin-user-system-users | list_users_api_v1_system_users_get | none | 200,422 | 用户列表 | FUNC-admin-user-system-users | unknown | FUNC-admin-user-system-users | unknown | openapi.json + source code |
| API-op-0047 | POST | /api/v1/system/users | REST | inbound | backend | FUNC-admin-user-system-users | create_user_api_v1_system_users_post | application/json | 200,422 | 新增用户 | FUNC-admin-user-system-users | unknown | FUNC-admin-user-system-users | unknown | openapi.json + source code |
| API-op-0048 | PUT | /api/v1/system/users/{user_id} | REST | inbound | backend | FUNC-admin-user-system-users-user-id | update_user_api_v1_system_users__user_id__put | application/json | 200,422 | 编辑用户 | FUNC-admin-user-system-users-user-id | unknown | FUNC-admin-user-system-users-user-id | unknown | openapi.json + source code |
| API-op-0049 | DELETE | /api/v1/system/users/{user_id} | REST | inbound | backend | FUNC-admin-user-system-users-user-id | delete_user_api_v1_system_users__user_id__delete | none | 200,422 | 删除用户 | FUNC-admin-user-system-users-user-id | unknown | FUNC-admin-user-system-users-user-id | unknown | openapi.json + source code |
| API-op-0050 | GET | /api/v1/system/users/{user_id}/teachings | REST | inbound | backend | FUNC-admin-user-system-users-user-id-teachings | user_teachings_api_v1_system_users__user_id__teachings_get | none | 200,422 | 教师授课关系 | FUNC-admin-user-system-users-user-id-teachings | unknown | FUNC-admin-user-system-users-user-id-teachings | unknown | openapi.json + source code |
| API-op-0051 | PUT | /api/v1/system/password/reset | REST | inbound | backend | FUNC-other-system-password-reset | reset_password_api_v1_system_password_reset_put | application/json | 200,422 | 重置用户密码（管理员） | FUNC-other-system-password-reset | unknown | FUNC-other-system-password-reset | unknown | openapi.json + source code |
| API-op-0052 | POST | /api/v1/system/users/{user_id}/unlock | REST | inbound | backend | FUNC-admin-user-system-users-user-id-unlock | unlock_user_api_v1_system_users__user_id__unlock_post | none | 200,422 | 解除账号锁定 | FUNC-admin-user-system-users-user-id-unlock | unknown | FUNC-admin-user-system-users-user-id-unlock | unknown | openapi.json + source code |
| API-op-0053 | GET | /api/v1/system/roles | REST | inbound | backend | FUNC-admin-role-system-roles | list_roles_api_v1_system_roles_get | none | 200 | 角色列表 | FUNC-admin-role-system-roles | unknown | FUNC-admin-role-system-roles | unknown | openapi.json + source code |
| API-op-0054 | POST | /api/v1/system/roles | REST | inbound | backend | FUNC-admin-role-system-roles | create_role_api_v1_system_roles_post | application/json | 200,422 | 新增角色 | FUNC-admin-role-system-roles | unknown | FUNC-admin-role-system-roles | unknown | openapi.json + source code |
| API-op-0055 | PUT | /api/v1/system/roles/{role_id} | REST | inbound | backend | FUNC-admin-role-system-roles-role-id | update_role_api_v1_system_roles__role_id__put | application/json | 200,422 | 编辑角色 | FUNC-admin-role-system-roles-role-id | unknown | FUNC-admin-role-system-roles-role-id | unknown | openapi.json + source code |
| API-op-0056 | DELETE | /api/v1/system/roles/{role_id} | REST | inbound | backend | FUNC-admin-role-system-roles-role-id | delete_role_api_v1_system_roles__role_id__delete | none | 200,422 | 删除角色 | FUNC-admin-role-system-roles-role-id | unknown | FUNC-admin-role-system-roles-role-id | unknown | openapi.json + source code |
| API-op-0057 | POST | /api/v1/system/roles/{role_id}/copy | REST | inbound | backend | FUNC-admin-role-system-roles-role-id-copy | copy_role_api_v1_system_roles__role_id__copy_post | application/json | 200,422 | 复制角色 | FUNC-admin-role-system-roles-role-id-copy | unknown | FUNC-admin-role-system-roles-role-id-copy | unknown | openapi.json + source code |
| API-op-0058 | GET | /api/v1/system/permissions | REST | inbound | backend | FUNC-admin-permission-system-permissions | list_permissions_api_v1_system_permissions_get | none | 200,422 | 权限点列表 / 树 | FUNC-admin-permission-system-permissions | unknown | FUNC-admin-permission-system-permissions | unknown | openapi.json + source code |
| API-op-0059 | GET | /api/v1/system/notifications | REST | inbound | backend | FUNC-notification-system-notifications | my_notifications_api_v1_system_notifications_get | none | 200,422 | 我的通知 | FUNC-notification-system-notifications | unknown | FUNC-notification-system-notifications | unknown | openapi.json + source code |
| API-op-0060 | PUT | /api/v1/system/notifications/{notif_id}/read | REST | inbound | backend | FUNC-notification-system-notifications-notif-id-read | read_notification_api_v1_system_notifications__notif_id__read_put | none | 200,422 | 标记通知已读 | FUNC-notification-system-notifications-notif-id-read | unknown | FUNC-notification-system-notifications-notif-id-read | unknown | openapi.json + source code |
| API-op-0061 | PUT | /api/v1/system/notifications/read-all | REST | inbound | backend | FUNC-notification-system-notifications-read-all | read_all_api_v1_system_notifications_read_all_put | none | 200 | 全部标记已读 | FUNC-notification-system-notifications-read-all | unknown | FUNC-notification-system-notifications-read-all | unknown | openapi.json + source code |
| API-op-0062 | GET | /api/v1/system/notification-prefs | REST | inbound | backend | FUNC-other-system-notification-prefs | get_notification_prefs_api_v1_system_notification_prefs_get | none | 200 | 我的通知订阅偏好 | FUNC-other-system-notification-prefs | unknown | FUNC-other-system-notification-prefs | unknown | openapi.json + source code |
| API-op-0063 | PUT | /api/v1/system/notification-prefs | REST | inbound | backend | FUNC-other-system-notification-prefs | save_notification_prefs_api_v1_system_notification_prefs_put | application/json | 200,422 | 保存通知订阅偏好 | FUNC-other-system-notification-prefs | unknown | FUNC-other-system-notification-prefs | unknown | openapi.json + source code |
| API-op-0064 | GET | /api/v1/system/config | REST | inbound | backend | FUNC-system-config-system-config | get_config_api_v1_system_config_get | none | 200 | 系统配置（可编辑项 + 运行态只读项） | FUNC-system-config-system-config | unknown | FUNC-system-config-system-config | unknown | openapi.json + source code |
| API-op-0065 | PUT | /api/v1/system/config | REST | inbound | backend | FUNC-system-config-system-config | update_config_api_v1_system_config_put | application/json | 200,422 | 更新系统配置（管理员） | FUNC-system-config-system-config | unknown | FUNC-system-config-system-config | unknown | openapi.json + source code |
| API-op-0066 | GET | /api/v1/system/version | REST | inbound | backend | FUNC-system-version-system-version | get_version_info_api_v1_system_version_get | none | 200 | 版本信息（版本号 / 构建号 / 最后更新时间） | FUNC-system-version-system-version | unknown | FUNC-system-version-system-version | unknown | openapi.json + source code |
| API-op-0067 | DELETE | /api/v1/system/config/{key} | REST | inbound | backend | FUNC-system-config-system-config-key | delete_config_api_v1_system_config__key__delete | none | 200,422 | 删除系统配置 | FUNC-system-config-system-config-key | unknown | FUNC-system-config-system-config-key | unknown | openapi.json + source code |
| API-op-0068 | GET | /api/v1/system/ai-config | REST | inbound | backend | FUNC-ai-config-system-ai-config | get_ai_config_route_api_v1_system_ai_config_get | none | 200 | AI 大模型配置 | FUNC-ai-config-system-ai-config | unknown | FUNC-ai-config-system-ai-config | unknown | openapi.json + source code |
| API-op-0069 | PUT | /api/v1/system/ai-config | REST | inbound | backend | FUNC-ai-config-system-ai-config | save_ai_config_route_api_v1_system_ai_config_put | application/json | 200,422 | 保存 AI 大模型配置 | FUNC-ai-config-system-ai-config | unknown | FUNC-ai-config-system-ai-config | unknown | openapi.json + source code |
| API-op-0070 | POST | /api/v1/system/ai-config/test | REST | inbound | backend | FUNC-ai-config-system-ai-config-test | test_ai_config_route_api_v1_system_ai_config_test_post | application/json | 200,422 | 测试 AI 大模型连接 | FUNC-ai-config-system-ai-config-test | unknown | FUNC-ai-config-system-ai-config-test | unknown | openapi.json + source code |
| API-op-0071 | GET | /api/v1/edu/grades | REST | inbound | backend | FUNC-teacher-grade-edu-grades | list_grades_api_v1_edu_grades_get | none | 200,422 | 年级列表 | FUNC-teacher-grade-edu-grades | unknown | FUNC-teacher-grade-edu-grades | unknown | openapi.json + source code |
| API-op-0072 | POST | /api/v1/edu/grades | REST | inbound | backend | FUNC-teacher-grade-edu-grades | create_grade_api_v1_edu_grades_post | application/json | 200,422 | 新增年级 | FUNC-teacher-grade-edu-grades | unknown | FUNC-teacher-grade-edu-grades | unknown | openapi.json + source code |
| API-op-0073 | PUT | /api/v1/edu/grades/{grade_id} | REST | inbound | backend | FUNC-teacher-grade-edu-grades-grade-id | update_grade_api_v1_edu_grades__grade_id__put | application/json | 200,422 | 编辑年级 | FUNC-teacher-grade-edu-grades-grade-id | unknown | FUNC-teacher-grade-edu-grades-grade-id | unknown | openapi.json + source code |
| API-op-0074 | DELETE | /api/v1/edu/grades/{grade_id} | REST | inbound | backend | FUNC-teacher-grade-edu-grades-grade-id | delete_grade_api_v1_edu_grades__grade_id__delete | none | 200,422 | 删除年级 | FUNC-teacher-grade-edu-grades-grade-id | unknown | FUNC-teacher-grade-edu-grades-grade-id | unknown | openapi.json + source code |
| API-op-0075 | GET | /api/v1/edu/subjects | REST | inbound | backend | FUNC-teacher-subject-edu-subjects | list_subjects_api_v1_edu_subjects_get | none | 200,422 | 学科列表 | FUNC-teacher-subject-edu-subjects | unknown | FUNC-teacher-subject-edu-subjects | unknown | openapi.json + source code |
| API-op-0076 | POST | /api/v1/edu/subjects | REST | inbound | backend | FUNC-teacher-subject-edu-subjects | create_subject_api_v1_edu_subjects_post | application/json | 200,422 | 新增学科 | FUNC-teacher-subject-edu-subjects | unknown | FUNC-teacher-subject-edu-subjects | unknown | openapi.json + source code |
| API-op-0077 | PUT | /api/v1/edu/subjects/{subject_id} | REST | inbound | backend | FUNC-teacher-subject-edu-subjects-subject-id | update_subject_api_v1_edu_subjects__subject_id__put | application/json | 200,422 | 编辑学科 | FUNC-teacher-subject-edu-subjects-subject-id | unknown | FUNC-teacher-subject-edu-subjects-subject-id | unknown | openapi.json + source code |
| API-op-0078 | DELETE | /api/v1/edu/subjects/{subject_id} | REST | inbound | backend | FUNC-teacher-subject-edu-subjects-subject-id | delete_subject_api_v1_edu_subjects__subject_id__delete | none | 200,422 | 删除学科 | FUNC-teacher-subject-edu-subjects-subject-id | unknown | FUNC-teacher-subject-edu-subjects-subject-id | unknown | openapi.json + source code |
| API-op-0079 | POST | /api/v1/edu/subjects/{subject_id}/clone | REST | inbound | backend | FUNC-teacher-subject-edu-subjects-subject-id-clone | clone_subject_api_v1_edu_subjects__subject_id__clone_post | application/json | 200,422 | 跨年级复制学科 | FUNC-teacher-subject-edu-subjects-subject-id-clone | unknown | FUNC-teacher-subject-edu-subjects-subject-id-clone | unknown | openapi.json + source code |
| API-op-0080 | GET | /api/v1/edu/classes/public | REST | inbound | backend | FUNC-teacher-class-edu-classes-public | list_classes_public_api_v1_edu_classes_public_get | none | 200 | 班级列表（注册页匿名可用） | FUNC-teacher-class-edu-classes-public | unknown | FUNC-teacher-class-edu-classes-public | unknown | openapi.json + source code |
| API-op-0081 | GET | /api/v1/edu/classes | REST | inbound | backend | FUNC-teacher-class-edu-classes | list_classes_api_v1_edu_classes_get | none | 200,422 | 班级列表 | FUNC-teacher-class-edu-classes | unknown | FUNC-teacher-class-edu-classes | unknown | openapi.json + source code |
| API-op-0082 | POST | /api/v1/edu/classes | REST | inbound | backend | FUNC-teacher-class-edu-classes | create_class_api_v1_edu_classes_post | application/json | 200,422 | 新增班级 | FUNC-teacher-class-edu-classes | unknown | FUNC-teacher-class-edu-classes | unknown | openapi.json + source code |
| API-op-0083 | GET | /api/v1/edu/classes/stats | REST | inbound | backend | FUNC-teacher-class-edu-classes-stats | class_stats_api_v1_edu_classes_stats_get | none | 200,422 | 班级统计（管理页顶部卡片） | FUNC-teacher-class-edu-classes-stats | unknown | FUNC-teacher-class-edu-classes-stats | unknown | openapi.json + source code |
| API-op-0084 | PUT | /api/v1/edu/classes/{class_id} | REST | inbound | backend | FUNC-teacher-class-edu-classes-class-id | update_class_api_v1_edu_classes__class_id__put | application/json | 200,422 | 编辑班级 | FUNC-teacher-class-edu-classes-class-id | unknown | FUNC-teacher-class-edu-classes-class-id | unknown | openapi.json + source code |
| API-op-0085 | DELETE | /api/v1/edu/classes/{class_id} | REST | inbound | backend | FUNC-teacher-class-edu-classes-class-id | delete_class_api_v1_edu_classes__class_id__delete | none | 200,422 | 删除班级 | FUNC-teacher-class-edu-classes-class-id | unknown | FUNC-teacher-class-edu-classes-class-id | unknown | openapi.json + source code |
| API-op-0086 | POST | /api/v1/edu/classes/batch | REST | inbound | backend | FUNC-teacher-class-edu-classes-batch | batch_classes_api_v1_edu_classes_batch_post | application/json | 200,422 | 批量启用/停用/删除班级 | FUNC-teacher-class-edu-classes-batch | unknown | FUNC-teacher-class-edu-classes-batch | unknown | openapi.json + source code |
| API-op-0087 | POST | /api/v1/edu/classes/{class_id}/students | REST | inbound | backend | FUNC-teacher-class-edu-classes-class-id-students | import_students_api_v1_edu_classes__class_id__students_post | application/json | 200,422 | 批量导入学生 | FUNC-teacher-class-edu-classes-class-id-students | unknown | FUNC-teacher-class-edu-classes-class-id-students | unknown | openapi.json + source code |
| API-op-0088 | GET | /api/v1/edu/classes/{class_id}/students | REST | inbound | backend | FUNC-teacher-class-edu-classes-class-id-students | list_class_students_api_v1_edu_classes__class_id__students_get | none | 200,422 | 班级学生列表（分页/搜索） | FUNC-teacher-class-edu-classes-class-id-students | unknown | FUNC-teacher-class-edu-classes-class-id-students | unknown | openapi.json + source code |
| API-op-0089 | GET | /api/v1/edu/classes/{class_id}/students/export | REST | inbound | backend | FUNC-teacher-class-edu-classes-class-id-students-export | export_class_students_api_v1_edu_classes__class_id__students_export_get | none | 200,422 | 导出班级学生 CSV | FUNC-teacher-class-edu-classes-class-id-students-export | unknown | FUNC-teacher-class-edu-classes-class-id-students-export | unknown | openapi.json + source code |
| API-op-0090 | POST | /api/v1/edu/classes/{class_id}/students/batch-remove | REST | inbound | backend | FUNC-teacher-class-edu-classes-class-id-students-batch-remove | batch_remove_students_api_v1_edu_classes__class_id__students_batch_remove_post | application/json | 200,422 | 批量移出班级 | FUNC-teacher-class-edu-classes-class-id-students-batch-remove | unknown | FUNC-teacher-class-edu-classes-class-id-students-batch-remove | unknown | openapi.json + source code |
| API-op-0091 | DELETE | /api/v1/edu/classes/{class_id}/students/{student_id} | REST | inbound | backend | FUNC-teacher-class-edu-classes-class-id-students-student-id | remove_student_api_v1_edu_classes__class_id__students__student_id__delete | none | 200,422 | 移出班级 | FUNC-teacher-class-edu-classes-class-id-students-student-id | unknown | FUNC-teacher-class-edu-classes-class-id-students-student-id | unknown | openapi.json + source code |
| API-op-0092 | GET | /api/v1/edu/people/brief | REST | inbound | backend | FUNC-other-edu-people-brief | people_brief_api_v1_edu_people_brief_get | none | 200,422 | 人员简表（仅 id/姓名/账号，教师端下拉用） | FUNC-other-edu-people-brief | unknown | FUNC-other-edu-people-brief | unknown | openapi.json + source code |
| API-op-0093 | POST | /api/v1/edu/class-requests | REST | inbound | backend | FUNC-teacher-class-request-edu-class-requests | create_class_request_api_v1_edu_class_requests_post | application/json | 200,422 | 教师提交建班申请 | FUNC-teacher-class-request-edu-class-requests | unknown | FUNC-teacher-class-request-edu-class-requests | unknown | openapi.json + source code |
| API-op-0094 | GET | /api/v1/edu/class-requests | REST | inbound | backend | FUNC-teacher-class-request-edu-class-requests | list_class_requests_api_v1_edu_class_requests_get | none | 200,422 | 建班申请列表（管理员审核用） | FUNC-teacher-class-request-edu-class-requests | unknown | FUNC-teacher-class-request-edu-class-requests | unknown | openapi.json + source code |
| API-op-0095 | GET | /api/v1/edu/class-requests/mine | REST | inbound | backend | FUNC-teacher-class-request-edu-class-requests-mine | my_class_requests_api_v1_edu_class_requests_mine_get | none | 200 | 我的建班申请 | FUNC-teacher-class-request-edu-class-requests-mine | unknown | FUNC-teacher-class-request-edu-class-requests-mine | unknown | openapi.json + source code |
| API-op-0096 | POST | /api/v1/edu/class-requests/{req_id}/review | REST | inbound | backend | FUNC-teacher-class-request-edu-class-requests-req-id-review | review_class_request_api_v1_edu_class_requests__req_id__review_post | application/json | 200,422 | 审核建班申请 | FUNC-teacher-class-request-edu-class-requests-req-id-review | unknown | FUNC-teacher-class-request-edu-class-requests-req-id-review | unknown | openapi.json + source code |
| API-op-0097 | DELETE | /api/v1/edu/class-requests/{req_id} | REST | inbound | backend | FUNC-teacher-class-request-edu-class-requests-req-id | withdraw_class_request_api_v1_edu_class_requests__req_id__delete | none | 200,422 | 撤回我的建班申请 | FUNC-teacher-class-request-edu-class-requests-req-id | unknown | FUNC-teacher-class-request-edu-class-requests-req-id | unknown | openapi.json + source code |
| API-op-0098 | GET | /api/v1/edu/teaching-matrix | REST | inbound | backend | FUNC-teacher-teaching-edu-teaching-matrix | teaching_matrix_api_v1_edu_teaching_matrix_get | none | 200,422 | 任课总览：年级 → 班级 → 科目 → 任教教师 | FUNC-teacher-teaching-edu-teaching-matrix | unknown | FUNC-teacher-teaching-edu-teaching-matrix | unknown | openapi.json + source code |
| API-op-0099 | GET | /api/v1/edu/teaching-assignments | REST | inbound | backend | FUNC-teacher-teaching-edu-teaching-assignments | list_teaching_assignments_api_v1_edu_teaching_assignments_get | none | 200,422 | 任课关系列表 | FUNC-teacher-teaching-edu-teaching-assignments | unknown | FUNC-teacher-teaching-edu-teaching-assignments | unknown | openapi.json + source code |
| API-op-0100 | POST | /api/v1/edu/teaching-assignments | REST | inbound | backend | FUNC-teacher-teaching-edu-teaching-assignments | create_teaching_assignment_api_v1_edu_teaching_assignments_post | application/json | 200,422 | 新增任课关系 | FUNC-teacher-teaching-edu-teaching-assignments | unknown | FUNC-teacher-teaching-edu-teaching-assignments | unknown | openapi.json + source code |
| API-op-0101 | DELETE | /api/v1/edu/teaching-assignments/{asg_id} | REST | inbound | backend | FUNC-teacher-teaching-edu-teaching-assignments-asg-id | delete_teaching_assignment_api_v1_edu_teaching_assignments__asg_id__delete | none | 200,422 | 解除任课关系 | FUNC-teacher-teaching-edu-teaching-assignments-asg-id | unknown | FUNC-teacher-teaching-edu-teaching-assignments-asg-id | unknown | openapi.json + source code |
| API-op-0102 | GET | /api/v1/edu/knowledge/graph | REST | inbound | backend | FUNC-knowledge-edu-knowledge-graph | knowledge_graph_api_v1_edu_knowledge_graph_get | none | 200,422 | 知识点关系图（先修 + 层级） | FUNC-knowledge-edu-knowledge-graph | unknown | FUNC-knowledge-edu-knowledge-graph | unknown | openapi.json + source code |
| API-op-0103 | GET | /api/v1/edu/knowledge/tree | REST | inbound | backend | FUNC-knowledge-edu-knowledge-tree | knowledge_tree_api_v1_edu_knowledge_tree_get | none | 200,422 | 知识点树 | FUNC-knowledge-edu-knowledge-tree | unknown | FUNC-knowledge-edu-knowledge-tree | unknown | openapi.json + source code |
| API-op-0104 | GET | /api/v1/edu/knowledge | REST | inbound | backend | FUNC-knowledge-edu-knowledge | knowledge_flat_api_v1_edu_knowledge_get | none | 200,422 | 知识点平铺列表（兼容旧接口） | FUNC-knowledge-edu-knowledge | unknown | FUNC-knowledge-edu-knowledge | unknown | openapi.json + source code |
| API-op-0105 | POST | /api/v1/edu/knowledge | REST | inbound | backend | FUNC-knowledge-edu-knowledge | create_knowledge_api_v1_edu_knowledge_post | application/json | 200,422 | 新增知识点 | FUNC-knowledge-edu-knowledge | unknown | FUNC-knowledge-edu-knowledge | unknown | openapi.json + source code |
| API-op-0106 | GET | /api/v1/edu/knowledge/list | REST | inbound | backend | FUNC-knowledge-edu-knowledge-list | knowledge_list_api_v1_edu_knowledge_list_get | none | 200,422 | 知识点平铺列表（兼容旧接口） | FUNC-knowledge-edu-knowledge-list | unknown | FUNC-knowledge-edu-knowledge-list | unknown | openapi.json + source code |
| API-op-0107 | GET | /api/v1/edu/knowledge/stats | REST | inbound | backend | FUNC-knowledge-edu-knowledge-stats | knowledge_stats_api_v1_edu_knowledge_stats_get | none | 200,422 | 知识点统计 | FUNC-knowledge-edu-knowledge-stats | unknown | FUNC-knowledge-edu-knowledge-stats | unknown | openapi.json + source code |
| API-op-0108 | GET | /api/v1/edu/knowledge/template | REST | inbound | backend | FUNC-knowledge-edu-knowledge-template | knowledge_template_api_v1_edu_knowledge_template_get | none | 200 | 下载知识点导入模板 | FUNC-knowledge-edu-knowledge-template | unknown | FUNC-knowledge-edu-knowledge-template | unknown | openapi.json + source code |
| API-op-0109 | GET | /api/v1/edu/knowledge/export | REST | inbound | backend | FUNC-knowledge-edu-knowledge-export | knowledge_export_api_v1_edu_knowledge_export_get | none | 200,422 | 导出知识点 | FUNC-knowledge-edu-knowledge-export | unknown | FUNC-knowledge-edu-knowledge-export | unknown | openapi.json + source code |
| API-op-0110 | GET | /api/v1/edu/knowledge/mastery-overview | REST | inbound | backend | FUNC-knowledge-edu-knowledge-mastery-overview | knowledge_mastery_overview_api_v1_edu_knowledge_mastery_overview_get | none | 200,422 | 班级知识点掌握概览（教师端） | FUNC-knowledge-edu-knowledge-mastery-overview | unknown | FUNC-knowledge-edu-knowledge-mastery-overview | unknown | openapi.json + source code |
| API-op-0111 | GET | /api/v1/edu/knowledge/search | REST | inbound | backend | FUNC-knowledge-edu-knowledge-search | knowledge_search_api_v1_edu_knowledge_search_get | none | 200,422 | 知识点语义搜索（RAG） | FUNC-knowledge-edu-knowledge-search | unknown | FUNC-knowledge-edu-knowledge-search | unknown | openapi.json + source code |
| API-op-0112 | GET | /api/v1/edu/knowledge/rag-status | REST | inbound | backend | FUNC-knowledge-edu-knowledge-rag-status | knowledge_rag_status_api_v1_edu_knowledge_rag_status_get | none | 200 | 知识点 RAG 索引状态 | FUNC-knowledge-edu-knowledge-rag-status | unknown | FUNC-knowledge-edu-knowledge-rag-status | unknown | openapi.json + source code |
| API-op-0113 | GET | /api/v1/edu/knowledge/{kp_id} | REST | inbound | backend | FUNC-knowledge-edu-knowledge-kp-id | knowledge_detail_api_v1_edu_knowledge__kp_id__get | none | 200,422 | 知识点详情 | FUNC-knowledge-edu-knowledge-kp-id | unknown | FUNC-knowledge-edu-knowledge-kp-id | unknown | openapi.json + source code |
| API-op-0114 | PUT | /api/v1/edu/knowledge/{kp_id} | REST | inbound | backend | FUNC-knowledge-edu-knowledge-kp-id | update_knowledge_api_v1_edu_knowledge__kp_id__put | application/json | 200,422 | 编辑知识点 | FUNC-knowledge-edu-knowledge-kp-id | unknown | FUNC-knowledge-edu-knowledge-kp-id | unknown | openapi.json + source code |
| API-op-0115 | DELETE | /api/v1/edu/knowledge/{kp_id} | REST | inbound | backend | FUNC-knowledge-edu-knowledge-kp-id | delete_knowledge_api_v1_edu_knowledge__kp_id__delete | none | 200,422 | 删除知识点 | FUNC-knowledge-edu-knowledge-kp-id | unknown | FUNC-knowledge-edu-knowledge-kp-id | unknown | openapi.json + source code |
| API-op-0116 | GET | /api/v1/edu/knowledge/{kp_id}/attachments | REST | inbound | backend | FUNC-knowledge-edu-knowledge-kp-id-attachments | list_knowledge_attachments_api_v1_edu_knowledge__kp_id__attachments_get | none | 200,422 | 知识点附件列表 | FUNC-knowledge-edu-knowledge-kp-id-attachments | unknown | FUNC-knowledge-edu-knowledge-kp-id-attachments | unknown | openapi.json + source code |
| API-op-0117 | POST | /api/v1/edu/knowledge/{kp_id}/attachments | REST | inbound | backend | FUNC-knowledge-edu-knowledge-kp-id-attachments | upload_knowledge_attachment_api_v1_edu_knowledge__kp_id__attachments_post | multipart/form-data | 200,422 | 上传知识点附件 | FUNC-knowledge-edu-knowledge-kp-id-attachments | unknown | FUNC-knowledge-edu-knowledge-kp-id-attachments | unknown | openapi.json + source code |
| API-op-0118 | PUT | /api/v1/edu/knowledge/{kp_id}/attachments/{att_id} | REST | inbound | backend | FUNC-knowledge-edu-knowledge-kp-id-attachments-att-id | update_knowledge_attachment_api_v1_edu_knowledge__kp_id__attachments__att_id__put | application/json | 200,422 | 更新知识点附件可见性 | FUNC-knowledge-edu-knowledge-kp-id-attachments-att-id | unknown | FUNC-knowledge-edu-knowledge-kp-id-attachments-att-id | unknown | openapi.json + source code |
| API-op-0119 | DELETE | /api/v1/edu/knowledge/{kp_id}/attachments/{att_id} | REST | inbound | backend | FUNC-knowledge-edu-knowledge-kp-id-attachments-att-id | delete_knowledge_attachment_api_v1_edu_knowledge__kp_id__attachments__att_id__delete | none | 200,422 | 删除知识点附件 | FUNC-knowledge-edu-knowledge-kp-id-attachments-att-id | unknown | FUNC-knowledge-edu-knowledge-kp-id-attachments-att-id | unknown | openapi.json + source code |
| API-op-0120 | POST | /api/v1/edu/knowledge/batch | REST | inbound | backend | FUNC-knowledge-edu-knowledge-batch | batch_knowledge_api_v1_edu_knowledge_batch_post | application/json | 200,422 | 批量操作知识点 | FUNC-knowledge-edu-knowledge-batch | unknown | FUNC-knowledge-edu-knowledge-batch | unknown | openapi.json + source code |
| API-op-0121 | POST | /api/v1/edu/knowledge/import | REST | inbound | backend | FUNC-knowledge-edu-knowledge-import | import_knowledge_api_v1_edu_knowledge_import_post | multipart/form-data | 200,422 | 导入知识点 | FUNC-knowledge-edu-knowledge-import | unknown | FUNC-knowledge-edu-knowledge-import | unknown | openapi.json + source code |
| API-op-0122 | POST | /api/v1/edu/knowledge/reindex | REST | inbound | backend | FUNC-knowledge-edu-knowledge-reindex | reindex_api_v1_edu_knowledge_reindex_post | none | 200 | 重建向量索引 | FUNC-knowledge-edu-knowledge-reindex | unknown | FUNC-knowledge-edu-knowledge-reindex | unknown | openapi.json + source code |
| API-op-0123 | POST | /api/v1/edu/knowledge/purge-generic | REST | inbound | backend | FUNC-knowledge-edu-knowledge-purge-generic | purge_generic_nodes_api_v1_edu_knowledge_purge_generic_post | application/json | 200,422 | 清理「通用训练栏目」节点（预览/执行） | FUNC-knowledge-edu-knowledge-purge-generic | unknown | FUNC-knowledge-edu-knowledge-purge-generic | unknown | openapi.json + source code |
| API-op-0124 | GET | /api/v1/edu/knowledge/diagnosis/targets | REST | inbound | backend | FUNC-knowledge-edu-knowledge-diagnosis-targets | diagnosis_targets_api_v1_edu_knowledge_diagnosis_targets_get | none | 200,422 | 可诊断知识点（按年级/学科） | FUNC-knowledge-edu-knowledge-diagnosis-targets | unknown | FUNC-knowledge-edu-knowledge-diagnosis-targets | unknown | openapi.json + source code |
| API-op-0125 | POST | /api/v1/edu/knowledge/diagnosis/sessions | REST | inbound | backend | FUNC-knowledge-edu-knowledge-diagnosis-sessions | create_diagnosis_session_api_v1_edu_knowledge_diagnosis_sessions_post | application/json | 200,422 | 创建诊断会话 | FUNC-knowledge-edu-knowledge-diagnosis-sessions | unknown | FUNC-knowledge-edu-knowledge-diagnosis-sessions | unknown | openapi.json + source code |
| API-op-0126 | GET | /api/v1/edu/knowledge/diagnosis/sessions/{session_id} | REST | inbound | backend | FUNC-knowledge-edu-knowledge-diagnosis-sessions-session-id | get_diagnosis_session_api_v1_edu_knowledge_diagnosis_sessions__session_id__get | none | 200,422 | 诊断会话详情 | FUNC-knowledge-edu-knowledge-diagnosis-sessions-session-id | unknown | FUNC-knowledge-edu-knowledge-diagnosis-sessions-session-id | unknown | openapi.json + source code |
| API-op-0127 | GET | /api/v1/edu/knowledge/diagnosis/sessions/{session_id}/next | REST | inbound | backend | FUNC-knowledge-edu-knowledge-diagnosis-sessions-session-id-next | get_next_diagnosis_item_api_v1_edu_knowledge_diagnosis_sessions__session_id__next_get | none | 200,422 | 下一道诊断题 | FUNC-knowledge-edu-knowledge-diagnosis-sessions-session-id-next | unknown | FUNC-knowledge-edu-knowledge-diagnosis-sessions-session-id-next | unknown | openapi.json + source code |
| API-op-0128 | POST | /api/v1/edu/knowledge/diagnosis/sessions/{session_id}/answers | REST | inbound | backend | FUNC-knowledge-edu-knowledge-diagnosis-sessions-session-id-answers | answer_diagnosis_api_v1_edu_knowledge_diagnosis_sessions__session_id__answers_post | application/json | 200,422 | 提交诊断作答 | FUNC-knowledge-edu-knowledge-diagnosis-sessions-session-id-answers | unknown | FUNC-knowledge-edu-knowledge-diagnosis-sessions-session-id-answers | unknown | openapi.json + source code |
| API-op-0129 | GET | /api/v1/edu/knowledge/diagnosis/sessions/{session_id}/summary | REST | inbound | backend | FUNC-knowledge-edu-knowledge-diagnosis-sessions-session-id-summary | diagnosis_summary_api_v1_edu_knowledge_diagnosis_sessions__session_id__summary_get | none | 200,422 | 诊断结果 | FUNC-knowledge-edu-knowledge-diagnosis-sessions-session-id-summary | unknown | FUNC-knowledge-edu-knowledge-diagnosis-sessions-session-id-summary | unknown | openapi.json + source code |
| API-op-0130 | GET | /api/v1/edu/knowledge/{kp_id}/prerequisites | REST | inbound | backend | FUNC-knowledge-edu-knowledge-kp-id-prerequisites | list_prerequisites_api_v1_edu_knowledge__kp_id__prerequisites_get | none | 200,422 | 知识点先修关系 | FUNC-knowledge-edu-knowledge-kp-id-prerequisites | unknown | FUNC-knowledge-edu-knowledge-kp-id-prerequisites | unknown | openapi.json + source code |
| API-op-0131 | POST | /api/v1/edu/knowledge/{kp_id}/prerequisites | REST | inbound | backend | FUNC-knowledge-edu-knowledge-kp-id-prerequisites | add_prerequisite_api_v1_edu_knowledge__kp_id__prerequisites_post | application/json | 200,422 | 新增先修关系 | FUNC-knowledge-edu-knowledge-kp-id-prerequisites | unknown | FUNC-knowledge-edu-knowledge-kp-id-prerequisites | unknown | openapi.json + source code |
| API-op-0132 | GET | /api/v1/edu/knowledge/{kp_id}/dependents | REST | inbound | backend | FUNC-knowledge-edu-knowledge-kp-id-dependents | list_dependents_api_v1_edu_knowledge__kp_id__dependents_get | none | 200,422 | 知识点后继关系 | FUNC-knowledge-edu-knowledge-kp-id-dependents | unknown | FUNC-knowledge-edu-knowledge-kp-id-dependents | unknown | openapi.json + source code |
| API-op-0133 | DELETE | /api/v1/edu/knowledge/{kp_id}/prerequisites/{prerequisite_id} | REST | inbound | backend | FUNC-knowledge-edu-knowledge-kp-id-prerequisites-prerequisite-id | remove_prerequisite_api_v1_edu_knowledge__kp_id__prerequisites__prerequisite_id__delete | none | 200,422 | 删除先修关系 | FUNC-knowledge-edu-knowledge-kp-id-prerequisites-prerequisite-id | unknown | FUNC-knowledge-edu-knowledge-kp-id-prerequisites-prerequisite-id | unknown | openapi.json + source code |
| API-op-0134 | POST | /api/v1/edu/knowledge/ai/generate | REST | inbound | backend | FUNC-knowledge-edu-knowledge-ai-generate | ai_generate_api_v1_edu_knowledge_ai_generate_post | application/json | 200,422 | AI 生成知识点预览 | FUNC-knowledge-edu-knowledge-ai-generate | unknown | FUNC-knowledge-edu-knowledge-ai-generate | unknown | openapi.json + source code |
| API-op-0135 | POST | /api/v1/edu/knowledge/ai/enrich | REST | inbound | backend | FUNC-knowledge-edu-knowledge-ai-enrich | ai_enrich_api_v1_edu_knowledge_ai_enrich_post | application/json | 200,422 | AI 批量补全知识点建议 | FUNC-knowledge-edu-knowledge-ai-enrich | unknown | FUNC-knowledge-edu-knowledge-ai-enrich | unknown | openapi.json + source code |
| API-op-0136 | GET | /api/v1/question/questions | REST | inbound | backend | FUNC-question-question-questions | list_questions_api_v1_question_questions_get | none | 200,422 | 题目列表 | FUNC-question-question-questions | unknown | FUNC-question-question-questions | unknown | openapi.json + source code |
| API-op-0137 | POST | /api/v1/question/questions | REST | inbound | backend | FUNC-question-question-questions | create_question_api_v1_question_questions_post | application/json | 200,422 | 新增题目 | FUNC-question-question-questions | unknown | FUNC-question-question-questions | unknown | openapi.json + source code |
| API-op-0138 | GET | /api/v1/question/questions/stats | REST | inbound | backend | FUNC-question-question-questions-stats | question_stats_api_v1_question_questions_stats_get | none | 200,422 | 题库统计 | FUNC-question-question-questions-stats | unknown | FUNC-question-question-questions-stats | unknown | openapi.json + source code |
| API-op-0139 | POST | /api/v1/question/questions/batch-create | REST | inbound | backend | FUNC-question-question-questions-batch-create | batch_create_questions_api_v1_question_questions_batch_create_post | application/json | 200,422 | 批量新增题目 | FUNC-question-question-questions-batch-create | unknown | FUNC-question-question-questions-batch-create | unknown | openapi.json + source code |
| API-op-0140 | POST | /api/v1/question/questions/batch | REST | inbound | backend | FUNC-question-question-questions-batch | batch_questions_api_v1_question_questions_batch_post | application/json | 200,422 | 批量操作题目 | FUNC-question-question-questions-batch | unknown | FUNC-question-question-questions-batch | unknown | openapi.json + source code |
| API-op-0141 | GET | /api/v1/question/questions/template | REST | inbound | backend | FUNC-question-question-questions-template | import_template_api_v1_question_questions_template_get | none | 200 | 下载批量导入模板 | FUNC-question-question-questions-template | unknown | FUNC-question-question-questions-template | unknown | openapi.json + source code |
| API-op-0142 | PUT | /api/v1/question/questions/{q_id} | REST | inbound | backend | FUNC-question-question-questions-q-id | update_question_api_v1_question_questions__q_id__put | application/json | 200,422 | 编辑题目 | FUNC-question-question-questions-q-id | unknown | FUNC-question-question-questions-q-id | unknown | openapi.json + source code |
| API-op-0143 | DELETE | /api/v1/question/questions/{q_id} | REST | inbound | backend | FUNC-question-question-questions-q-id | delete_question_api_v1_question_questions__q_id__delete | none | 200,422 | 删除题目 | FUNC-question-question-questions-q-id | unknown | FUNC-question-question-questions-q-id | unknown | openapi.json + source code |
| API-op-0144 | GET | /api/v1/question/questions/{q_id} | REST | inbound | backend | FUNC-question-question-questions-q-id | get_question_api_v1_question_questions__q_id__get | none | 200,422 | 题目详情 | FUNC-question-question-questions-q-id | unknown | FUNC-question-question-questions-q-id | unknown | openapi.json + source code |
| API-op-0145 | PUT | /api/v1/question/questions/{q_id}/status | REST | inbound | backend | FUNC-question-question-questions-q-id-status | change_status_api_v1_question_questions__q_id__status_put | application/json | 200,422 | 上下架 / 审核 | FUNC-question-question-questions-q-id-status | unknown | FUNC-question-question-questions-q-id-status | unknown | openapi.json + source code |
| API-op-0146 | GET | /api/v1/question/questions/{q_id}/duplicates | REST | inbound | backend | FUNC-question-question-questions-q-id-duplicates | check_duplicate_api_v1_question_questions__q_id__duplicates_get | none | 200,422 | 题目查重 | FUNC-question-question-questions-q-id-duplicates | unknown | FUNC-question-question-questions-q-id-duplicates | unknown | openapi.json + source code |
| API-op-0147 | POST | /api/v1/question/questions/import | REST | inbound | backend | FUNC-question-question-questions-import | import_questions_api_v1_question_questions_import_post | multipart/form-data | 200,422 | Excel 批量导入题目 | FUNC-question-question-questions-import | unknown | FUNC-question-question-questions-import | unknown | openapi.json + source code |
| API-op-0148 | GET | /api/v1/question/questions/export | REST | inbound | backend | FUNC-question-question-questions-export | export_questions_api_v1_question_questions_export_get | none | 200,422 | 导出题目为 Excel | FUNC-question-question-questions-export | unknown | FUNC-question-question-questions-export | unknown | openapi.json + source code |
| API-op-0149 | GET | /api/v1/question/papers | REST | inbound | backend | FUNC-question-question-papers | list_papers_api_v1_question_papers_get | none | 200,422 | 试卷列表 | FUNC-question-question-papers | unknown | FUNC-question-question-papers | unknown | openapi.json + source code |
| API-op-0150 | POST | /api/v1/question/papers | REST | inbound | backend | FUNC-question-question-papers | create_paper_api_v1_question_papers_post | application/json | 200,422 | 手动组卷 | FUNC-question-question-papers | unknown | FUNC-question-question-papers | unknown | openapi.json + source code |
| API-op-0151 | GET | /api/v1/question/papers/stats | REST | inbound | backend | FUNC-question-question-papers-stats | paper_stats_api_v1_question_papers_stats_get | none | 200,422 | 试卷统计 | FUNC-question-question-papers-stats | unknown | FUNC-question-question-papers-stats | unknown | openapi.json + source code |
| API-op-0152 | POST | /api/v1/question/papers/batch | REST | inbound | backend | FUNC-question-question-papers-batch | batch_papers_api_v1_question_papers_batch_post | application/json | 200,422 | 批量操作试卷 | FUNC-question-question-papers-batch | unknown | FUNC-question-question-papers-batch | unknown | openapi.json + source code |
| API-op-0153 | GET | /api/v1/question/papers/{paper_id} | REST | inbound | backend | FUNC-question-question-papers-paper-id | get_paper_api_v1_question_papers__paper_id__get | none | 200,422 | 试卷详情（含题目） | FUNC-question-question-papers-paper-id | unknown | FUNC-question-question-papers-paper-id | unknown | openapi.json + source code |
| API-op-0154 | PUT | /api/v1/question/papers/{paper_id} | REST | inbound | backend | FUNC-question-question-papers-paper-id | update_paper_api_v1_question_papers__paper_id__put | application/json | 200,422 | 编辑试卷 | FUNC-question-question-papers-paper-id | unknown | FUNC-question-question-papers-paper-id | unknown | openapi.json + source code |
| API-op-0155 | DELETE | /api/v1/question/papers/{paper_id} | REST | inbound | backend | FUNC-question-question-papers-paper-id | delete_paper_api_v1_question_papers__paper_id__delete | none | 200,422 | 删除试卷 | FUNC-question-question-papers-paper-id | unknown | FUNC-question-question-papers-paper-id | unknown | openapi.json + source code |
| API-op-0156 | POST | /api/v1/question/papers/{paper_id}/archive | REST | inbound | backend | FUNC-question-question-papers-paper-id-archive | archive_paper_api_v1_question_papers__paper_id__archive_post | application/json | 200,422 | 停用 / 恢复试卷 | FUNC-question-question-papers-paper-id-archive | unknown | FUNC-question-question-papers-paper-id-archive | unknown | openapi.json + source code |
| API-op-0157 | POST | /api/v1/question/papers/{paper_id}/copy | REST | inbound | backend | FUNC-question-question-papers-paper-id-copy | copy_paper_api_v1_question_papers__paper_id__copy_post | application/json | 200,422 | 试卷复制复用 | FUNC-question-question-papers-paper-id-copy | unknown | FUNC-question-question-papers-paper-id-copy | unknown | openapi.json + source code |
| API-op-0158 | POST | /api/v1/question/papers/{paper_id}/share | REST | inbound | backend | FUNC-question-question-papers-paper-id-share | share_paper_api_v1_question_papers__paper_id__share_post | application/json | 200,422 | 共享试卷给同科教师 | FUNC-question-question-papers-paper-id-share | unknown | FUNC-question-question-papers-paper-id-share | unknown | openapi.json + source code |
| API-op-0159 | GET | /api/v1/question/papers/{paper_id}/export | REST | inbound | backend | FUNC-question-question-papers-paper-id-export | export_paper_api_v1_question_papers__paper_id__export_get | none | 200,422 | 导出试卷（Excel/Word/PDF/HTML） | FUNC-question-question-papers-paper-id-export | unknown | FUNC-question-question-papers-paper-id-export | unknown | openapi.json + source code |
| API-op-0160 | POST | /api/v1/question/questions/ai/variants | REST | inbound | backend | FUNC-question-question-questions-ai-variants | question_variants_api_v1_question_questions_ai_variants_post | application/json | 200,422 | AI 生成同考点变式题（预览） | FUNC-question-question-questions-ai-variants | unknown | FUNC-question-question-questions-ai-variants | unknown | openapi.json + source code |
| API-op-0161 | POST | /api/v1/question/questions/ai/enrich | REST | inbound | backend | FUNC-question-question-questions-ai-enrich | question_enrich_api_v1_question_questions_ai_enrich_post | application/json | 200,422 | AI 批量补全题目解析/知识点（预览） | FUNC-question-question-questions-ai-enrich | unknown | FUNC-question-question-questions-ai-enrich | unknown | openapi.json + source code |
| API-op-0162 | POST | /api/v1/question/questions/ai/quality | REST | inbound | backend | FUNC-question-question-questions-ai-quality | question_quality_api_v1_question_questions_ai_quality_post | application/json | 200,422 | AI 批量质检题目（预览） | FUNC-question-question-questions-ai-quality | unknown | FUNC-question-question-questions-ai-quality | unknown | openapi.json + source code |
| API-op-0163 | POST | /api/v1/question/papers/{paper_id}/ai/analyze | REST | inbound | backend | FUNC-question-question-papers-paper-id-ai-analyze | analyze_paper_api_v1_question_papers__paper_id__ai_analyze_post | none | 200,422 | AI 分析试卷（规则 + 建议） | FUNC-question-question-papers-paper-id-ai-analyze | unknown | FUNC-question-question-papers-paper-id-ai-analyze | unknown | openapi.json + source code |
| API-op-0164 | POST | /api/v1/question/papers/{paper_id}/ai/recommend | REST | inbound | backend | FUNC-question-question-papers-paper-id-ai-recommend | recommend_questions_api_v1_question_papers__paper_id__ai_recommend_post | application/json | 200,422 | AI 推荐候选题 | FUNC-question-question-papers-paper-id-ai-recommend | unknown | FUNC-question-question-papers-paper-id-ai-recommend | unknown | openapi.json + source code |
| API-op-0165 | GET | /api/v1/question/standards | REST | inbound | backend | FUNC-question-question-standards | list_standards_api_v1_question_standards_get | none | 200,422 | 命题标准列表 | FUNC-question-question-standards | unknown | FUNC-question-question-standards | unknown | openapi.json + source code |
| API-op-0166 | POST | /api/v1/question/standards | REST | inbound | backend | FUNC-question-question-standards | create_standard_api_v1_question_standards_post | application/json | 200,422 | 新建命题标准 | FUNC-question-question-standards | unknown | FUNC-question-question-standards | unknown | openapi.json + source code |
| API-op-0167 | GET | /api/v1/question/standards/options | REST | inbound | backend | FUNC-question-question-standards-options | standard_options_api_v1_question_standards_options_get | none | 200,422 | 组卷用标准选项（按学段学科分组） | FUNC-question-question-standards-options | unknown | FUNC-question-question-standards-options | unknown | openapi.json + source code |
| API-op-0168 | GET | /api/v1/question/standards/{std_id} | REST | inbound | backend | FUNC-question-question-standards-std-id | get_standard_api_v1_question_standards__std_id__get | none | 200,422 | 命题标准详情 | FUNC-question-question-standards-std-id | unknown | FUNC-question-question-standards-std-id | unknown | openapi.json + source code |
| API-op-0169 | PUT | /api/v1/question/standards/{std_id} | REST | inbound | backend | FUNC-question-question-standards-std-id | update_standard_api_v1_question_standards__std_id__put | application/json | 200,422 | 编辑命题标准 | FUNC-question-question-standards-std-id | unknown | FUNC-question-question-standards-std-id | unknown | openapi.json + source code |
| API-op-0170 | DELETE | /api/v1/question/standards/{std_id} | REST | inbound | backend | FUNC-question-question-standards-std-id | delete_standard_api_v1_question_standards__std_id__delete | none | 200,422 | 删除命题标准 | FUNC-question-question-standards-std-id | unknown | FUNC-question-question-standards-std-id | unknown | openapi.json + source code |
| API-op-0171 | POST | /api/v1/question/standards/{std_id}/duplicate | REST | inbound | backend | FUNC-question-question-standards-std-id-duplicate | duplicate_standard_api_v1_question_standards__std_id__duplicate_post | application/json | 200,422 | 复制命题标准 | FUNC-question-question-standards-std-id-duplicate | unknown | FUNC-question-question-standards-std-id-duplicate | unknown | openapi.json + source code |
| API-op-0172 | POST | /api/v1/question/standards/generate-missing | REST | inbound | backend | FUNC-question-question-standards-generate-missing | generate_missing_standards_api_v1_question_standards_generate_missing_post | none | 200 | 为缺失学科批量生成标准草案 | FUNC-question-question-standards-generate-missing | unknown | FUNC-question-question-standards-generate-missing | unknown | openapi.json + source code |
| API-op-0173 | POST | /api/v1/question/standards/seed | REST | inbound | backend | FUNC-question-question-standards-seed | reseed_standards_api_v1_question_standards_seed_post | none | 200,422 | 播种/补齐内置湖北标准 | FUNC-question-question-standards-seed | unknown | FUNC-question-question-standards-seed | unknown | openapi.json + source code |
| API-op-0174 | POST | /api/v1/question/standards/{std_id}/reset | REST | inbound | backend | FUNC-question-question-standards-std-id-reset | reset_standard_api_v1_question_standards__std_id__reset_post | none | 200,422 | 重置为内置标准 | FUNC-question-question-standards-std-id-reset | unknown | FUNC-question-question-standards-std-id-reset | unknown | openapi.json + source code |
| API-op-0175 | POST | /api/v1/question/papers/compose/regenerate | REST | inbound | backend | FUNC-question-question-papers-compose-regenerate | compose_regenerate_api_v1_question_papers_compose_regenerate_post | application/json | 200,422 | 组卷预览：重新生成单题或某题型 | FUNC-question-question-papers-compose-regenerate | unknown | FUNC-question-question-papers-compose-regenerate | unknown | openapi.json + source code |
| API-op-0176 | POST | /api/v1/question/papers/compose/preview | REST | inbound | backend | FUNC-question-question-papers-compose-preview | compose_preview_api_v1_question_papers_compose_preview_post | application/json | 200,422 | 自定义参数组卷（预览，不落库） | FUNC-question-question-papers-compose-preview | unknown | FUNC-question-question-papers-compose-preview | unknown | openapi.json + source code |
| API-op-0177 | POST | /api/v1/question/papers/compose/ai | REST | inbound | backend | FUNC-question-question-papers-compose-ai | compose_ai_api_v1_question_papers_compose_ai_post | application/json | 200,422 | AI 一键智能组卷 | FUNC-question-question-papers-compose-ai | unknown | FUNC-question-question-papers-compose-ai | unknown | openapi.json + source code |
| API-op-0178 | POST | /api/v1/question/papers/compose/save | REST | inbound | backend | FUNC-question-question-papers-compose-save | compose_save_api_v1_question_papers_compose_save_post | application/json | 200,422 | 保存组卷结果为新试卷 | FUNC-question-question-papers-compose-save | unknown | FUNC-question-question-papers-compose-save | unknown | openapi.json + source code |
| API-op-0179 | GET | /api/v1/question/papers/{paper_id}/preview | REST | inbound | backend | FUNC-question-question-papers-paper-id-preview | preview_paper_api_v1_question_papers__paper_id__preview_get | none | 200,422 | 试卷预览（按大题分组，含答案解析） | FUNC-question-question-papers-paper-id-preview | unknown | FUNC-question-question-papers-paper-id-preview | unknown | openapi.json + source code |
| API-op-0180 | POST | /api/v1/question/papers/{paper_id}/items | REST | inbound | backend | FUNC-question-question-papers-paper-id-items | update_items_api_v1_question_papers__paper_id__items_post | application/json | 200,422 | 保存题目列表（增删/排序/改分） | FUNC-question-question-papers-paper-id-items | unknown | FUNC-question-question-papers-paper-id-items | unknown | openapi.json + source code |
| API-op-0181 | POST | /api/v1/question/papers/{paper_id}/items/{item_id}/regenerate | REST | inbound | backend | FUNC-question-question-papers-paper-id-items-item-id-regenerate | regenerate_item_api_v1_question_papers__paper_id__items__item_id__regenerate_post | application/json | 200,422 | AI 重新生成单题 | FUNC-question-question-papers-paper-id-items-item-id-regenerate | unknown | FUNC-question-question-papers-paper-id-items-item-id-regenerate | unknown | openapi.json + source code |
| API-op-0182 | DELETE | /api/v1/question/papers/{paper_id}/items/{item_id} | REST | inbound | backend | FUNC-question-question-papers-paper-id-items-item-id | remove_item_api_v1_question_papers__paper_id__items__item_id__delete | none | 200,422 | 移除单题 | FUNC-question-question-papers-paper-id-items-item-id | unknown | FUNC-question-question-papers-paper-id-items-item-id | unknown | openapi.json + source code |
| API-op-0183 | POST | /api/v1/question/papers/{paper_id}/sections/rename | REST | inbound | backend | FUNC-question-question-papers-paper-id-sections-rename | rename_section_api_v1_question_papers__paper_id__sections_rename_post | application/json | 200,422 | 大题改名 | FUNC-question-question-papers-paper-id-sections-rename | unknown | FUNC-question-question-papers-paper-id-sections-rename | unknown | openapi.json + source code |
| API-op-0184 | POST | /api/v1/question/papers/{paper_id}/restructure | REST | inbound | backend | FUNC-question-question-papers-paper-id-restructure | restructure_paper_api_v1_question_papers__paper_id__restructure_post | application/json | 200,422 | 一键重构大题结构 | FUNC-question-question-papers-paper-id-restructure | unknown | FUNC-question-question-papers-paper-id-restructure | unknown | openapi.json + source code |
| API-op-0185 | GET | /api/v1/question/papers/{paper_id}/versions | REST | inbound | backend | FUNC-question-question-papers-paper-id-versions | list_versions_api_v1_question_papers__paper_id__versions_get | none | 200,422 | 版本列表 | FUNC-question-question-papers-paper-id-versions | unknown | FUNC-question-question-papers-paper-id-versions | unknown | openapi.json + source code |
| API-op-0186 | GET | /api/v1/question/papers/{paper_id}/versions/{version} | REST | inbound | backend | FUNC-question-question-papers-paper-id-versions-version | get_version_api_v1_question_papers__paper_id__versions__version__get | none | 200,422 | 版本详情 | FUNC-question-question-papers-paper-id-versions-version | unknown | FUNC-question-question-papers-paper-id-versions-version | unknown | openapi.json + source code |
| API-op-0187 | GET | /api/v1/question/papers/{paper_id}/versions/{version}/diff | REST | inbound | backend | FUNC-question-question-papers-paper-id-versions-version-diff | diff_version_api_v1_question_papers__paper_id__versions__version__diff_get | none | 200,422 | 版本对比（回溯前先看差异） | FUNC-question-question-papers-paper-id-versions-version-diff | unknown | FUNC-question-question-papers-paper-id-versions-version-diff | unknown | openapi.json + source code |
| API-op-0188 | POST | /api/v1/question/papers/{paper_id}/versions/{version}/restore | REST | inbound | backend | FUNC-question-question-papers-paper-id-versions-version-restore | restore_version_api_v1_question_papers__paper_id__versions__version__restore_post | application/json | 200,422 | 回溯到指定版本 | FUNC-question-question-papers-paper-id-versions-version-restore | unknown | FUNC-question-question-papers-paper-id-versions-version-restore | unknown | openapi.json + source code |
| API-op-0189 | GET | /api/v1/question/papers/library/list | REST | inbound | backend | FUNC-question-question-papers-library-list | paper_library_api_v1_question_papers_library_list_get | none | 200,422 | 试卷库（我的/共享/公共/收藏） | FUNC-question-question-papers-library-list | unknown | FUNC-question-question-papers-library-list | unknown | openapi.json + source code |
| API-op-0190 | POST | /api/v1/question/papers/{paper_id}/favorite | REST | inbound | backend | FUNC-question-question-papers-paper-id-favorite | toggle_favorite_api_v1_question_papers__paper_id__favorite_post | application/json | 200,422 | 收藏/取消收藏 | FUNC-question-question-papers-paper-id-favorite | unknown | FUNC-question-question-papers-paper-id-favorite | unknown | openapi.json + source code |
| API-op-0191 | POST | /api/v1/question/papers/{paper_id}/share-scope | REST | inbound | backend | FUNC-question-question-papers-paper-id-share-scope | set_share_scope_api_v1_question_papers__paper_id__share_scope_post | application/json | 200,422 | 设置共享范围（私有/年级/全校） | FUNC-question-question-papers-paper-id-share-scope | unknown | FUNC-question-question-papers-paper-id-share-scope | unknown | openapi.json + source code |
| API-op-0192 | GET | /api/v1/question/papers/{paper_id}/share-info | REST | inbound | backend | FUNC-question-question-papers-paper-id-share-info | share_info_api_v1_question_papers__paper_id__share_info_get | none | 200,422 | 查看共享范围与协作者 | FUNC-question-question-papers-paper-id-share-info | unknown | FUNC-question-question-papers-paper-id-share-info | unknown | openapi.json + source code |
| API-op-0193 | POST | /api/v1/question/papers/{paper_id}/review | REST | inbound | backend | FUNC-question-question-papers-paper-id-review | review_paper_api_v1_question_papers__paper_id__review_post | application/json | 200,422 | 提交审核 / 审核通过 / 驳回 | FUNC-question-question-papers-paper-id-review | unknown | FUNC-question-question-papers-paper-id-review | unknown | openapi.json + source code |
| API-op-0194 | GET | /api/v1/question/papers/{paper_id}/export/docx | REST | inbound | backend | FUNC-question-question-papers-paper-id-export-docx | export_docx_api_v1_question_papers__paper_id__export_docx_get | none | 200,422 | 导出 Word（教师卷/学生卷） | FUNC-question-question-papers-paper-id-export-docx | unknown | FUNC-question-question-papers-paper-id-export-docx | unknown | openapi.json + source code |
| API-op-0195 | GET | /api/v1/question/papers/{paper_id}/export/pdf | REST | inbound | backend | FUNC-question-question-papers-paper-id-export-pdf | export_pdf_api_v1_question_papers__paper_id__export_pdf_get | none | 200,422 | 导出 PDF（教师卷/学生卷） | FUNC-question-question-papers-paper-id-export-pdf | unknown | FUNC-question-question-papers-paper-id-export-pdf | unknown | openapi.json + source code |
| API-op-0196 | GET | /api/v1/question/papers/{paper_id}/export/answer-sheet | REST | inbound | backend | FUNC-question-question-papers-paper-id-export-answer-sheet | export_answer_sheet_api_v1_question_papers__paper_id__export_answer_sheet_get | none | 200,422 | 导出答题卡 | FUNC-question-question-papers-paper-id-export-answer-sheet | unknown | FUNC-question-question-papers-paper-id-export-answer-sheet | unknown | openapi.json + source code |
| API-op-0197 | GET | /api/v1/question/papers/{paper_id}/export/html | REST | inbound | backend | FUNC-question-question-papers-paper-id-export-html | export_html_api_v1_question_papers__paper_id__export_html_get | none | 200,422 | 导出可打印 HTML | FUNC-question-question-papers-paper-id-export-html | unknown | FUNC-question-question-papers-paper-id-export-html | unknown | openapi.json + source code |
| API-op-0198 | POST | /api/v1/question/papers/{paper_id}/export/jobs | REST | inbound | backend | FUNC-question-question-papers-paper-id-export-jobs | create_export_job_api_v1_question_papers__paper_id__export_jobs_post | application/json | 200,422 | 提交导出任务（异步，推荐） | FUNC-question-question-papers-paper-id-export-jobs | unknown | FUNC-question-question-papers-paper-id-export-jobs | unknown | openapi.json + source code |
| API-op-0199 | GET | /api/v1/question/papers/export/jobs/{job_id} | REST | inbound | backend | FUNC-question-question-papers-export-jobs-job-id | get_export_job_api_v1_question_papers_export_jobs__job_id__get | none | 200,422 | 查询导出任务状态 | FUNC-question-question-papers-export-jobs-job-id | unknown | FUNC-question-question-papers-export-jobs-job-id | unknown | openapi.json + source code |
| API-op-0200 | GET | /api/v1/question/papers/export/jobs/{job_id}/file | REST | inbound | backend | FUNC-question-question-papers-export-jobs-job-id-file | download_export_job_api_v1_question_papers_export_jobs__job_id__file_get | none | 200,422 | 下载导出文件（30 分钟有效） | FUNC-question-question-papers-export-jobs-job-id-file | unknown | FUNC-question-question-papers-export-jobs-job-id-file | unknown | openapi.json + source code |
| API-op-0201 | POST | /api/v1/question/papers/compose/ai/async | REST | inbound | backend | FUNC-question-question-papers-compose-ai-async | compose_ai_async_api_v1_question_papers_compose_ai_async_post | application/json | 200,422 | AI 一键组卷（异步任务，推荐） | FUNC-question-question-papers-compose-ai-async | unknown | FUNC-question-question-papers-compose-ai-async | unknown | openapi.json + source code |
| API-op-0202 | GET | /api/v1/question/papers/compose/jobs/{job_id} | REST | inbound | backend | FUNC-question-question-papers-compose-jobs-job-id | get_compose_job_api_v1_question_papers_compose_jobs__job_id__get | none | 200,422 | 查询组卷任务状态与结果 | FUNC-question-question-papers-compose-jobs-job-id | unknown | FUNC-question-question-papers-compose-jobs-job-id | unknown | openapi.json + source code |
| API-op-0203 | POST | /api/v1/question/papers/compose/jobs/{job_id}/cancel | REST | inbound | backend | FUNC-question-question-papers-compose-jobs-job-id-cancel | cancel_compose_job_api_v1_question_papers_compose_jobs__job_id__cancel_post | none | 200,422 | 取消组卷任务 | FUNC-question-question-papers-compose-jobs-job-id-cancel | unknown | FUNC-question-question-papers-compose-jobs-job-id-cancel | unknown | openapi.json + source code |
| API-op-0204 | GET | /api/v1/task/tasks | REST | inbound | backend | FUNC-task-task-tasks | list_tasks_api_v1_task_tasks_get | none | 200,422 | 作业考试列表（教师） | FUNC-task-task-tasks | unknown | FUNC-task-task-tasks | unknown | openapi.json + source code |
| API-op-0205 | POST | /api/v1/task/tasks | REST | inbound | backend | FUNC-task-task-tasks | create_task_api_v1_task_tasks_post | application/json | 200,422 | 发布作业 / 考试 | FUNC-task-task-tasks | unknown | FUNC-task-task-tasks | unknown | openapi.json + source code |
| API-op-0206 | GET | /api/v1/task/tasks/stats | REST | inbound | backend | FUNC-task-task-tasks-stats | task_stats_api_v1_task_tasks_stats_get | none | 200,422 | 作业考试统计 | FUNC-task-task-tasks-stats | unknown | FUNC-task-task-tasks-stats | unknown | openapi.json + source code |
| API-op-0207 | POST | /api/v1/task/tasks/batch | REST | inbound | backend | FUNC-task-task-tasks-batch | batch_tasks_api_v1_task_tasks_batch_post | application/json | 200,422 | 批量操作作业考试 | FUNC-task-task-tasks-batch | unknown | FUNC-task-task-tasks-batch | unknown | openapi.json + source code |
| API-op-0208 | GET | /api/v1/task/tasks/{task_id} | REST | inbound | backend | FUNC-task-task-tasks-task-id | get_task_api_v1_task_tasks__task_id__get | none | 200,422 | 任务详情 | FUNC-task-task-tasks-task-id | unknown | FUNC-task-task-tasks-task-id | unknown | openapi.json + source code |
| API-op-0209 | PUT | /api/v1/task/tasks/{task_id} | REST | inbound | backend | FUNC-task-task-tasks-task-id | update_task_api_v1_task_tasks__task_id__put | application/json | 200,422 | 编辑任务 | FUNC-task-task-tasks-task-id | unknown | FUNC-task-task-tasks-task-id | unknown | openapi.json + source code |
| API-op-0210 | DELETE | /api/v1/task/tasks/{task_id} | REST | inbound | backend | FUNC-task-task-tasks-task-id | delete_task_api_v1_task_tasks__task_id__delete | none | 200,422 | 删除任务 | FUNC-task-task-tasks-task-id | unknown | FUNC-task-task-tasks-task-id | unknown | openapi.json + source code |
| API-op-0211 | GET | /api/v1/task/tasks/{task_id}/submissions | REST | inbound | backend | FUNC-task-task-tasks-task-id-submissions | task_submissions_api_v1_task_tasks__task_id__submissions_get | none | 200,422 | 任务提交情况 | FUNC-task-task-tasks-task-id-submissions | unknown | FUNC-task-task-tasks-task-id-submissions | unknown | openapi.json + source code |
| API-op-0212 | GET | /api/v1/task/my/tasks | REST | inbound | backend | FUNC-task-task-my-tasks | my_tasks_api_v1_task_my_tasks_get | none | 200,422 | 我的作业考试 | FUNC-task-task-my-tasks | unknown | FUNC-task-task-my-tasks | unknown | openapi.json + source code |
| API-op-0213 | GET | /api/v1/task/tasks/{task_id}/paper | REST | inbound | backend | FUNC-task-task-tasks-task-id-paper | get_task_paper_api_v1_task_tasks__task_id__paper_get | none | 200,422 | 获取试卷（作答用，不含答案） | FUNC-task-task-tasks-task-id-paper | unknown | FUNC-task-task-tasks-task-id-paper | unknown | openapi.json + source code |
| API-op-0214 | POST | /api/v1/task/tasks/{task_id}/submit | REST | inbound | backend | FUNC-task-task-tasks-task-id-submit | submit_answers_api_v1_task_tasks__task_id__submit_post | application/json | 200,422 | 提交作答 | FUNC-task-task-tasks-task-id-submit | unknown | FUNC-task-task-tasks-task-id-submit | unknown | openapi.json + source code |
| API-op-0215 | POST | /api/v1/task/tasks/{task_id}/heartbeat | REST | inbound | backend | FUNC-task-task-tasks-task-id-heartbeat | heartbeat_api_v1_task_tasks__task_id__heartbeat_post | application/json | 200,422 | 作答心跳（防切屏计时） | FUNC-task-task-tasks-task-id-heartbeat | unknown | FUNC-task-task-tasks-task-id-heartbeat | unknown | openapi.json + source code |
| API-op-0216 | GET | /api/v1/task/submissions/{submission_id} | REST | inbound | backend | FUNC-task-task-submissions-submission-id | submission_detail_api_v1_task_submissions__submission_id__get | none | 200,422 | 作答详情（含解析） | FUNC-task-task-submissions-submission-id | unknown | FUNC-task-task-submissions-submission-id | unknown | openapi.json + source code |
| API-op-0217 | GET | /api/v1/task/my/scores | REST | inbound | backend | FUNC-task-task-my-scores | my_scores_api_v1_task_my_scores_get | none | 200,422 | 我的成绩中心 | FUNC-task-task-my-scores | unknown | FUNC-task-task-my-scores | unknown | openapi.json + source code |
| API-op-0218 | GET | /api/v1/task/tasks/{task_id}/pending-students | REST | inbound | backend | FUNC-task-task-tasks-task-id-pending-students | pending_students_endpoint_api_v1_task_tasks__task_id__pending_students_get | none | 200,422 | 待交名单 | FUNC-task-task-tasks-task-id-pending-students | unknown | FUNC-task-task-tasks-task-id-pending-students | unknown | openapi.json + source code |
| API-op-0219 | POST | /api/v1/task/tasks/{task_id}/urge | REST | inbound | backend | FUNC-task-task-tasks-task-id-urge | urge_task_students_api_v1_task_tasks__task_id__urge_post | application/json | 200,422 | 催交考试 / 作业 | FUNC-task-task-tasks-task-id-urge | unknown | FUNC-task-task-tasks-task-id-urge | unknown | openapi.json + source code |
| API-op-0220 | GET | /api/v1/grading/pending | REST | inbound | backend | FUNC-grading-grading-pending | pending_submissions_api_v1_grading_pending_get | none | 200,422 | 待批改列表 | FUNC-grading-grading-pending | unknown | FUNC-grading-grading-pending | unknown | openapi.json + source code |
| API-op-0221 | GET | /api/v1/grading/submissions | REST | inbound | backend | FUNC-grading-grading-submissions | submission_list_api_v1_grading_submissions_get | none | 200,422 | 作答提交列表（兼容/按任务、班级筛选） | FUNC-grading-grading-submissions | unknown | FUNC-grading-grading-submissions | unknown | openapi.json + source code |
| API-op-0222 | GET | /api/v1/grading/stats | REST | inbound | backend | FUNC-grading-grading-stats | grading_stats_api_v1_grading_stats_get | none | 200,422 | 批改统计 | FUNC-grading-grading-stats | unknown | FUNC-grading-grading-stats | unknown | openapi.json + source code |
| API-op-0223 | GET | /api/v1/grading/submissions/{submission_id} | REST | inbound | backend | FUNC-grading-grading-submissions-submission-id | grading_detail_api_v1_grading_submissions__submission_id__get | none | 200,422 | 批改详情 | FUNC-grading-grading-submissions-submission-id | unknown | FUNC-grading-grading-submissions-submission-id | unknown | openapi.json + source code |
| API-op-0224 | POST | /api/v1/grading/submissions/{submission_id}/grade | REST | inbound | backend | FUNC-grading-grading-submissions-submission-id-grade | grade_submission_api_v1_grading_submissions__submission_id__grade_post | application/json | 200,422 | 手动批改 / 采纳 AI 建议 | FUNC-grading-grading-submissions-submission-id-grade | unknown | FUNC-grading-grading-submissions-submission-id-grade | unknown | openapi.json + source code |
| API-op-0225 | POST | /api/v1/grading/submissions/{submission_id}/reject | REST | inbound | backend | FUNC-grading-grading-submissions-submission-id-reject | reject_submission_api_v1_grading_submissions__submission_id__reject_post | application/json | 200,422 | 打回重做 | FUNC-grading-grading-submissions-submission-id-reject | unknown | FUNC-grading-grading-submissions-submission-id-reject | unknown | openapi.json + source code |
| API-op-0226 | POST | /api/v1/grading/submissions/{submission_id}/publish | REST | inbound | backend | FUNC-grading-grading-submissions-submission-id-publish | publish_score_api_v1_grading_submissions__submission_id__publish_post | none | 200,422 | 发布成绩 | FUNC-grading-grading-submissions-submission-id-publish | unknown | FUNC-grading-grading-submissions-submission-id-publish | unknown | openapi.json + source code |
| API-op-0227 | POST | /api/v1/grading/batch/grade | REST | inbound | backend | FUNC-grading-grading-batch-grade | batch_grade_api_v1_grading_batch_grade_post | application/json | 200,422 | 批量采纳当前分数（快速批改） | FUNC-grading-grading-batch-grade | unknown | FUNC-grading-grading-batch-grade | unknown | openapi.json + source code |
| API-op-0228 | POST | /api/v1/grading/batch/publish | REST | inbound | backend | FUNC-grading-grading-batch-publish | batch_publish_api_v1_grading_batch_publish_post | application/json | 200,422 | 批量发布成绩 | FUNC-grading-grading-batch-publish | unknown | FUNC-grading-grading-batch-publish | unknown | openapi.json + source code |
| API-op-0229 | POST | /api/v1/grading/unpublish | REST | inbound | backend | FUNC-grading-grading-unpublish | unpublish_scores_api_v1_grading_unpublish_post | application/json | 200,422 | 退回已发布成绩（仅发布权限） | FUNC-grading-grading-unpublish | unknown | FUNC-grading-grading-unpublish | unknown | openapi.json + source code |
| API-op-0230 | POST | /api/v1/grading/tasks/{task_id}/report | REST | inbound | backend | FUNC-grading-grading-tasks-task-id-report | class_report_api_v1_grading_tasks__task_id__report_post | none | 200,422 | 生成班级学情报告 | FUNC-grading-grading-tasks-task-id-report | unknown | FUNC-grading-grading-tasks-task-id-report | unknown | openapi.json + source code |
| API-op-0231 | POST | /api/v1/grading/tasks/{task_id}/ai-comment | REST | inbound | backend | FUNC-grading-grading-tasks-task-id-ai-comment | ai_teaching_advice_api_v1_grading_tasks__task_id__ai_comment_post | none | 200,422 | AI 生成学情教学建议 | FUNC-grading-grading-tasks-task-id-ai-comment | unknown | FUNC-grading-grading-tasks-task-id-ai-comment | unknown | openapi.json + source code |
| API-op-0232 | GET | /api/v1/learning/notes | REST | inbound | backend | FUNC-learning-learning-notes | list_notes_api_v1_learning_notes_get | none | 200,422 | 我的笔记列表 | FUNC-learning-learning-notes | unknown | FUNC-learning-learning-notes | unknown | openapi.json + source code |
| API-op-0233 | POST | /api/v1/learning/notes | REST | inbound | backend | FUNC-learning-learning-notes | create_note_api_v1_learning_notes_post | application/json | 200,422 | 创建笔记 | FUNC-learning-learning-notes | unknown | FUNC-learning-learning-notes | unknown | openapi.json + source code |
| API-op-0234 | GET | /api/v1/learning/notes/shared | REST | inbound | backend | FUNC-learning-learning-notes-shared | shared_notes_api_v1_learning_notes_shared_get | none | 200,422 | 同学共享的笔记 | FUNC-learning-learning-notes-shared | unknown | FUNC-learning-learning-notes-shared | unknown | openapi.json + source code |
| API-op-0235 | GET | /api/v1/learning/notes/{note_id} | REST | inbound | backend | FUNC-learning-learning-notes-note-id | get_note_api_v1_learning_notes__note_id__get | none | 200,422 | 笔记详情 | FUNC-learning-learning-notes-note-id | unknown | FUNC-learning-learning-notes-note-id | unknown | openapi.json + source code |
| API-op-0236 | PUT | /api/v1/learning/notes/{note_id} | REST | inbound | backend | FUNC-learning-learning-notes-note-id | update_note_api_v1_learning_notes__note_id__put | application/json | 200,422 | 更新笔记 | FUNC-learning-learning-notes-note-id | unknown | FUNC-learning-learning-notes-note-id | unknown | openapi.json + source code |
| API-op-0237 | DELETE | /api/v1/learning/notes/{note_id} | REST | inbound | backend | FUNC-learning-learning-notes-note-id | delete_note_api_v1_learning_notes__note_id__delete | none | 200,422 | 删除笔记 | FUNC-learning-learning-notes-note-id | unknown | FUNC-learning-learning-notes-note-id | unknown | openapi.json + source code |
| API-op-0238 | PUT | /api/v1/learning/notes/{note_id}/share | REST | inbound | backend | FUNC-learning-learning-notes-note-id-share | share_note_api_v1_learning_notes__note_id__share_put | application/json | 200,422 | 分享笔记给同学 | FUNC-learning-learning-notes-note-id-share | unknown | FUNC-learning-learning-notes-note-id-share | unknown | openapi.json + source code |
| API-op-0239 | POST | /api/v1/learning/notes/{note_id}/organize | REST | inbound | backend | FUNC-learning-learning-notes-note-id-organize | organize_note_api_v1_learning_notes__note_id__organize_post | none | 200,422 | AI 整理笔记 | FUNC-learning-learning-notes-note-id-organize | unknown | FUNC-learning-learning-notes-note-id-organize | unknown | openapi.json + source code |
| API-op-0240 | GET | /api/v1/learning/notes/{note_id}/export | REST | inbound | backend | FUNC-learning-learning-notes-note-id-export | export_note_api_v1_learning_notes__note_id__export_get | none | 200,422 | 导出笔记为 HTML/PDF 预览 | FUNC-learning-learning-notes-note-id-export | unknown | FUNC-learning-learning-notes-note-id-export | unknown | openapi.json + source code |
| API-op-0241 | GET | /api/v1/learning/wrong-questions | REST | inbound | backend | FUNC-learning-learning-wrong-questions | list_wrong_api_v1_learning_wrong_questions_get | none | 200,422 | 错题本列表 | FUNC-learning-learning-wrong-questions | unknown | FUNC-learning-learning-wrong-questions | unknown | openapi.json + source code |
| API-op-0242 | PUT | /api/v1/learning/wrong-questions/{wid} | REST | inbound | backend | FUNC-learning-learning-wrong-questions-wid | update_wrong_api_v1_learning_wrong_questions__wid__put | application/json | 200,422 | 标注错因 / 标记掌握 | FUNC-learning-learning-wrong-questions-wid | unknown | FUNC-learning-learning-wrong-questions-wid | unknown | openapi.json + source code |
| API-op-0243 | POST | /api/v1/learning/wrong-questions/{wid}/analyze | REST | inbound | backend | FUNC-learning-learning-wrong-questions-wid-analyze | analyze_wrong_api_v1_learning_wrong_questions__wid__analyze_post | none | 200,422 | AI 分析错因 | FUNC-learning-learning-wrong-questions-wid-analyze | unknown | FUNC-learning-learning-wrong-questions-wid-analyze | unknown | openapi.json + source code |
| API-op-0244 | POST | /api/v1/learning/wrong-questions/{wid}/redo | REST | inbound | backend | FUNC-learning-learning-wrong-questions-wid-redo | redo_wrong_api_v1_learning_wrong_questions__wid__redo_post | none | 200,422 | 错题重做（生成专项练习） | FUNC-learning-learning-wrong-questions-wid-redo | unknown | FUNC-learning-learning-wrong-questions-wid-redo | unknown | openapi.json + source code |
| API-op-0245 | GET | /api/v1/learning/wrong-questions/export | REST | inbound | backend | FUNC-learning-learning-wrong-questions-export | export_wrong_api_v1_learning_wrong_questions_export_get | none | 200,422 | 导出错题 | FUNC-learning-learning-wrong-questions-export | unknown | FUNC-learning-learning-wrong-questions-export | unknown | openapi.json + source code |
| API-op-0246 | GET | /api/v1/learning/review/plans | REST | inbound | backend | FUNC-learning-learning-review-plans | review_plans_api_v1_learning_review_plans_get | none | 200,422 | 我的复习计划 | FUNC-learning-learning-review-plans | unknown | FUNC-learning-learning-review-plans | unknown | openapi.json + source code |
| API-op-0247 | PUT | /api/v1/learning/review/plans/{plan_id}/complete | REST | inbound | backend | FUNC-learning-learning-review-plans-plan-id-complete | complete_review_api_v1_learning_review_plans__plan_id__complete_put | application/json | 200,422 | 完成复习 | FUNC-learning-learning-review-plans-plan-id-complete | unknown | FUNC-learning-learning-review-plans-plan-id-complete | unknown | openapi.json + source code |
| API-op-0248 | GET | /api/v1/learning/review/mastery | REST | inbound | backend | FUNC-learning-learning-review-mastery | mastery_map_api_v1_learning_review_mastery_get | none | 200,422 | 知识点掌握地图 | FUNC-learning-learning-review-mastery | unknown | FUNC-learning-learning-review-mastery | unknown | openapi.json + source code |
| API-op-0249 | POST | /api/v1/learning/review/plan | REST | inbound | backend | FUNC-learning-learning-review-plan | generate_plan_api_v1_learning_review_plan_post | application/json | 200,422 | AI 生成复习计划 | FUNC-learning-learning-review-plan | unknown | FUNC-learning-learning-review-plan | unknown | openapi.json + source code |
| API-op-0250 | POST | /api/v1/learning/practice | REST | inbound | backend | FUNC-learning-learning-practice | create_practice_api_v1_learning_practice_post | application/json | 200,422 | 创建随机练习 | FUNC-learning-learning-practice | unknown | FUNC-learning-learning-practice | unknown | openapi.json + source code |
| API-op-0251 | GET | /api/v1/learning/practice/history | REST | inbound | backend | FUNC-learning-learning-practice-history | practice_history_api_v1_learning_practice_history_get | none | 200,422 | 练习历史 | FUNC-learning-learning-practice-history | unknown | FUNC-learning-learning-practice-history | unknown | openapi.json + source code |
| API-op-0252 | GET | /api/v1/learning/practice/{task_id} | REST | inbound | backend | FUNC-learning-learning-practice-task-id | get_practice_api_v1_learning_practice__task_id__get | none | 200,422 | 获取练习题目 | FUNC-learning-learning-practice-task-id | unknown | FUNC-learning-learning-practice-task-id | unknown | openapi.json + source code |
| API-op-0253 | GET | /api/v1/learning/favorites | REST | inbound | backend | FUNC-learning-learning-favorites | list_favorites_api_v1_learning_favorites_get | none | 200,422 | 我的收藏夹 | FUNC-learning-learning-favorites | unknown | FUNC-learning-learning-favorites | unknown | openapi.json + source code |
| API-op-0254 | POST | /api/v1/learning/favorites | REST | inbound | backend | FUNC-learning-learning-favorites | add_favorite_api_v1_learning_favorites_post | application/json | 200,422 | 收藏题目 | FUNC-learning-learning-favorites | unknown | FUNC-learning-learning-favorites | unknown | openapi.json + source code |
| API-op-0255 | DELETE | /api/v1/learning/favorites/{fav_id} | REST | inbound | backend | FUNC-learning-learning-favorites-fav-id | remove_favorite_api_v1_learning_favorites__fav_id__delete | none | 200,422 | 取消收藏 | FUNC-learning-learning-favorites-fav-id | unknown | FUNC-learning-learning-favorites-fav-id | unknown | openapi.json + source code |
| API-op-0256 | DELETE | /api/v1/learning/favorites/by-question/{question_id} | REST | inbound | backend | FUNC-learning-learning-favorites-by-question-question-id | remove_favorite_by_question_api_v1_learning_favorites_by_question__question_id__delete | none | 200,422 | 按题目取消收藏 | FUNC-learning-learning-favorites-by-question-question-id | unknown | FUNC-learning-learning-favorites-by-question-question-id | unknown | openapi.json + source code |
| API-op-0257 | GET | /api/v1/learning/favorites/check-batch | REST | inbound | backend | FUNC-learning-learning-favorites-check-batch | check_favorites_batch_api_v1_learning_favorites_check_batch_get | none | 200,422 | 批量检查收藏状态 | FUNC-learning-learning-favorites-check-batch | unknown | FUNC-learning-learning-favorites-check-batch | unknown | openapi.json + source code |
| API-op-0258 | GET | /api/v1/learning/favorites/check/{question_id} | REST | inbound | backend | FUNC-learning-learning-favorites-check-question-id | check_favorite_api_v1_learning_favorites_check__question_id__get | none | 200,422 | 检查是否已收藏 | FUNC-learning-learning-favorites-check-question-id | unknown | FUNC-learning-learning-favorites-check-question-id | unknown | openapi.json + source code |
| API-op-0259 | POST | /api/v1/learning/favorites/practice | REST | inbound | backend | FUNC-learning-learning-favorites-practice | favorites_practice_api_v1_learning_favorites_practice_post | application/json | 200,422 | 收藏题目生成专项练习 | FUNC-learning-learning-favorites-practice | unknown | FUNC-learning-learning-favorites-practice | unknown | openapi.json + source code |
| API-op-0260 | POST | /api/v1/learning/wrong-questions/{wid}/variant | REST | inbound | backend | FUNC-learning-learning-wrong-questions-wid-variant | wrong_variant_api_v1_learning_wrong_questions__wid__variant_post | none | 200,422 | 错题变式练习（AI 生成同类题） | FUNC-learning-learning-wrong-questions-wid-variant | unknown | FUNC-learning-learning-wrong-questions-wid-variant | unknown | openapi.json + source code |
| API-op-0261 | POST | /api/v1/learning/custom-paper | REST | inbound | backend | FUNC-learning-learning-custom-paper | create_custom_paper_api_v1_learning_custom_paper_post | application/json | 200,422 | 学生自主组卷 | FUNC-learning-learning-custom-paper | unknown | FUNC-learning-learning-custom-paper | unknown | openapi.json + source code |
| API-op-0262 | GET | /api/v1/learning/goals | REST | inbound | backend | FUNC-learning-learning-goals | list_goals_api_v1_learning_goals_get | none | 200 | 我的学习目标 | FUNC-learning-learning-goals | unknown | FUNC-learning-learning-goals | unknown | openapi.json + source code |
| API-op-0263 | POST | /api/v1/learning/goals | REST | inbound | backend | FUNC-learning-learning-goals | create_goal_api_v1_learning_goals_post | application/json | 200,422 | 创建学习目标 | FUNC-learning-learning-goals | unknown | FUNC-learning-learning-goals | unknown | openapi.json + source code |
| API-op-0264 | PUT | /api/v1/learning/goals/{goal_id} | REST | inbound | backend | FUNC-learning-learning-goals-goal-id | update_goal_api_v1_learning_goals__goal_id__put | application/json | 200,422 | 更新目标 | FUNC-learning-learning-goals-goal-id | unknown | FUNC-learning-learning-goals-goal-id | unknown | openapi.json + source code |
| API-op-0265 | DELETE | /api/v1/learning/goals/{goal_id} | REST | inbound | backend | FUNC-learning-learning-goals-goal-id | delete_goal_api_v1_learning_goals__goal_id__delete | none | 200,422 | 删除目标 | FUNC-learning-learning-goals-goal-id | unknown | FUNC-learning-learning-goals-goal-id | unknown | openapi.json + source code |
| API-op-0266 | POST | /api/v1/learning/goals/{goal_id}/checkin | REST | inbound | backend | FUNC-learning-learning-goals-goal-id-checkin | checkin_api_v1_learning_goals__goal_id__checkin_post | application/json | 200,422 | 每日打卡 | FUNC-learning-learning-goals-goal-id-checkin | unknown | FUNC-learning-learning-goals-goal-id-checkin | unknown | openapi.json + source code |
| API-op-0267 | GET | /api/v1/learning/path/recommend | REST | inbound | backend | FUNC-learning-learning-path-recommend | recommend_path_api_v1_learning_path_recommend_get | none | 200,422 | AI 个性化学习路径推荐 | FUNC-learning-learning-path-recommend | unknown | FUNC-learning-learning-path-recommend | unknown | openapi.json + source code |
| API-op-0268 | GET | /api/v1/learning/flashcards | REST | inbound | backend | FUNC-learning-learning-flashcards | get_flashcards_api_v1_learning_flashcards_get | none | 200,422 | 知识闪卡（知识点速记） | FUNC-learning-learning-flashcards | unknown | FUNC-learning-learning-flashcards | unknown | openapi.json + source code |
| API-op-0269 | GET | /api/v1/agent/list | REST | inbound | backend | FUNC-ai-agent-agent-list | list_agents_api_v1_agent_list_get | none | 200 | Agent 列表 | FUNC-ai-agent-agent-list | unknown | FUNC-ai-agent-agent-list | unknown | openapi.json + source code |
| API-op-0270 | GET | /api/v1/agent/status | REST | inbound | backend | FUNC-ai-agent-agent-status | agent_status_api_v1_agent_status_get | none | 200 | AI 引擎状态 | FUNC-ai-agent-agent-status | unknown | FUNC-ai-agent-agent-status | unknown | openapi.json + source code |
| API-op-0271 | POST | /api/v1/agent/chat | REST | inbound | backend | FUNC-ai-agent-agent-chat | chat_api_v1_agent_chat_post | application/json | 200,422 | AI 统一对话（自动路由） | FUNC-ai-agent-agent-chat | unknown | FUNC-ai-agent-agent-chat | unknown | openapi.json + source code |
| API-op-0272 | POST | /api/v1/agent/chat/stream | REST | inbound | backend | FUNC-ai-agent-agent-chat-stream | chat_stream_api_v1_agent_chat_stream_post | application/json | 200,422 | AI 统一对话（SSE 流式） | FUNC-ai-agent-agent-chat-stream | unknown | FUNC-ai-agent-agent-chat-stream | unknown | openapi.json + source code |
| API-op-0273 | POST | /api/v1/agent/question-generator | REST | inbound | backend | FUNC-ai-agent-agent-question-generator | question_generator_api_v1_agent_question_generator_post | application/json | 200,422 | 题库生成 Agent | FUNC-ai-agent-agent-question-generator | unknown | FUNC-ai-agent-agent-question-generator | unknown | openapi.json + source code |
| API-op-0274 | POST | /api/v1/agent/paper-composer | REST | inbound | backend | FUNC-ai-agent-agent-paper-composer | paper_composer_api_v1_agent_paper_composer_post | application/json | 200,422 | 智能组卷 Agent | FUNC-ai-agent-agent-paper-composer | unknown | FUNC-ai-agent-agent-paper-composer | unknown | openapi.json + source code |
| API-op-0275 | POST | /api/v1/agent/grading | REST | inbound | backend | FUNC-ai-agent-agent-grading | agent_grading_api_v1_agent_grading_post | application/json | 200,422 | 智能批改 Agent | FUNC-ai-agent-agent-grading | unknown | FUNC-ai-agent-agent-grading | unknown | openapi.json + source code |
| API-op-0276 | POST | /api/v1/agent/study-planner | REST | inbound | backend | FUNC-ai-agent-agent-study-planner | study_planner_api_v1_agent_study_planner_post | application/json | 200,422 | 学习规划 Agent | FUNC-ai-agent-agent-study-planner | unknown | FUNC-ai-agent-agent-study-planner | unknown | openapi.json + source code |
| API-op-0277 | POST | /api/v1/agent/tutor | REST | inbound | backend | FUNC-ai-agent-agent-tutor | tutor_api_v1_agent_tutor_post | application/json | 200,422 | 答疑助教 Agent | FUNC-ai-agent-agent-tutor | unknown | FUNC-ai-agent-agent-tutor | unknown | openapi.json + source code |
| API-op-0278 | POST | /api/v1/agent/note-organizer | REST | inbound | backend | FUNC-ai-agent-agent-note-organizer | note_organizer_api_v1_agent_note_organizer_post | application/json | 200,422 | 笔记整理 Agent | FUNC-ai-agent-agent-note-organizer | unknown | FUNC-ai-agent-agent-note-organizer | unknown | openapi.json + source code |
| API-op-0279 | POST | /api/v1/agent/jobs | REST | inbound | backend | FUNC-ai-agent-agent-jobs | create_job_api_v1_agent_jobs_post | application/json | 200,422 | 提交长任务（异步出题/组卷） | FUNC-ai-agent-agent-jobs | unknown | FUNC-ai-agent-agent-jobs | unknown | openapi.json + source code |
| API-op-0280 | GET | /api/v1/agent/jobs | REST | inbound | backend | FUNC-ai-agent-agent-jobs | list_jobs_api_v1_agent_jobs_get | none | 200,422 | 我的任务列表 | FUNC-ai-agent-agent-jobs | unknown | FUNC-ai-agent-agent-jobs | unknown | openapi.json + source code |
| API-op-0281 | GET | /api/v1/agent/jobs/{job_id} | REST | inbound | backend | FUNC-ai-agent-agent-jobs-job-id | get_job_api_v1_agent_jobs__job_id__get | none | 200,422 | 查询任务状态与结果 | FUNC-ai-agent-agent-jobs-job-id | unknown | FUNC-ai-agent-agent-jobs-job-id | unknown | openapi.json + source code |
| API-op-0282 | GET | /api/v1/agent/logs | REST | inbound | backend | FUNC-ai-agent-agent-logs | agent_logs_api_v1_agent_logs_get | none | 200,422 | AI 调用日志 | FUNC-ai-agent-agent-logs | unknown | FUNC-ai-agent-agent-logs | unknown | openapi.json + source code |
| API-op-0283 | GET | /api/v1/report/student/overview | REST | inbound | backend | FUNC-report-report-student-overview | student_overview_api_v1_report_student_overview_get | none | 200 | 个人学习总览 | FUNC-report-report-student-overview | unknown | FUNC-report-report-student-overview | unknown | openapi.json + source code |
| API-op-0284 | GET | /api/v1/report/student/score-trend | REST | inbound | backend | FUNC-report-report-student-score-trend | score_trend_api_v1_report_student_score_trend_get | none | 200,422 | 成绩趋势 | FUNC-report-report-student-score-trend | unknown | FUNC-report-report-student-score-trend | unknown | openapi.json + source code |
| API-op-0285 | GET | /api/v1/report/student/knowledge-radar | REST | inbound | backend | FUNC-report-report-student-knowledge-radar | knowledge_radar_api_v1_report_student_knowledge_radar_get | none | 200,422 | 知识点掌握雷达图 | FUNC-report-report-student-knowledge-radar | unknown | FUNC-report-report-student-knowledge-radar | unknown | openapi.json + source code |
| API-op-0286 | GET | /api/v1/report/student/wrong-analysis | REST | inbound | backend | FUNC-report-report-student-wrong-analysis | wrong_analysis_api_v1_report_student_wrong_analysis_get | none | 200,422 | 错题分析 | FUNC-report-report-student-wrong-analysis | unknown | FUNC-report-report-student-wrong-analysis | unknown | openapi.json + source code |
| API-op-0287 | GET | /api/v1/report/student/learning-suggestion | REST | inbound | backend | FUNC-report-report-student-learning-suggestion | learning_suggestion_api_v1_report_student_learning_suggestion_get | none | 200 | 个性化学习建议 | FUNC-report-report-student-learning-suggestion | unknown | FUNC-report-report-student-learning-suggestion | unknown | openapi.json + source code |
| API-op-0288 | GET | /api/v1/report/teacher/class-overview | REST | inbound | backend | FUNC-report-report-teacher-class-overview | class_overview_api_v1_report_teacher_class_overview_get | none | 200,422 | 班级学情概览 | FUNC-report-report-teacher-class-overview | unknown | FUNC-report-report-teacher-class-overview | unknown | openapi.json + source code |
| API-op-0289 | GET | /api/v1/report/teacher/student-comparison | REST | inbound | backend | FUNC-report-report-teacher-student-comparison | student_comparison_api_v1_report_teacher_student_comparison_get | none | 200,422 | 学生横向对比 | FUNC-report-report-teacher-student-comparison | unknown | FUNC-report-report-teacher-student-comparison | unknown | openapi.json + source code |
| API-op-0290 | GET | /api/v1/report/teacher/student-detail | REST | inbound | backend | FUNC-report-report-teacher-student-detail | student_detail_api_v1_report_teacher_student_detail_get | none | 200,422 | 学生个体分析 | FUNC-report-report-teacher-student-detail | unknown | FUNC-report-report-teacher-student-detail | unknown | openapi.json + source code |
| API-op-0291 | GET | /api/v1/report/teacher/knowledge-effect | REST | inbound | backend | FUNC-report-report-teacher-knowledge-effect | knowledge_effect_api_v1_report_teacher_knowledge_effect_get | none | 200,422 | 知识点教学效果评估 | FUNC-report-report-teacher-knowledge-effect | unknown | FUNC-report-report-teacher-knowledge-effect | unknown | openapi.json + source code |
| API-op-0292 | GET | /api/v1/report/teacher/class-weak-points | REST | inbound | backend | FUNC-report-report-teacher-class-weak-points | class_weak_points_api_v1_report_teacher_class_weak_points_get | none | 200,422 | 班级薄弱知识点聚合 | FUNC-report-report-teacher-class-weak-points | unknown | FUNC-report-report-teacher-class-weak-points | unknown | openapi.json + source code |
| API-op-0293 | GET | /api/v1/report/admin/overview | REST | inbound | backend | FUNC-report-report-admin-overview | admin_overview_api_v1_report_admin_overview_get | none | 200 | 系统总览 | FUNC-report-report-admin-overview | unknown | FUNC-report-report-admin-overview | unknown | openapi.json + source code |
| API-op-0294 | GET | /api/v1/report/admin/grade-comparison | REST | inbound | backend | FUNC-report-report-admin-grade-comparison | grade_comparison_api_v1_report_admin_grade_comparison_get | none | 200 | 各年级教学数据对比 | FUNC-report-report-admin-grade-comparison | unknown | FUNC-report-report-admin-grade-comparison | unknown | openapi.json + source code |
| API-op-0295 | GET | /api/v1/report/admin/subject-comparison | REST | inbound | backend | FUNC-report-report-admin-subject-comparison | subject_comparison_api_v1_report_admin_subject_comparison_get | none | 200,422 | 各学科教学数据对比 | FUNC-report-report-admin-subject-comparison | unknown | FUNC-report-report-admin-subject-comparison | unknown | openapi.json + source code |
| API-op-0296 | GET | /api/v1/report/admin/system-runtime | REST | inbound | backend | FUNC-report-report-admin-system-runtime | system_runtime_api_v1_report_admin_system_runtime_get | none | 200 | 系统运行报表 | FUNC-report-report-admin-system-runtime | unknown | FUNC-report-report-admin-system-runtime | unknown | openapi.json + source code |
| API-op-0297 | GET | /api/v1/report/export/excel | REST | inbound | backend | FUNC-report-report-export-excel | export_excel_api_v1_report_export_excel_get | none | 200,422 | 报表导出 Excel | FUNC-report-report-export-excel | unknown | FUNC-report-report-export-excel | unknown | openapi.json + source code |
| API-op-0298 | GET | /api/v1/logs/login | REST | inbound | backend | FUNC-log-logs-login | login_logs_api_v1_logs_login_get | none | 200,422 | 登录日志 | FUNC-log-logs-login | unknown | FUNC-log-logs-login | unknown | openapi.json + source code |
| API-op-0299 | GET | /api/v1/logs/operation | REST | inbound | backend | FUNC-log-logs-operation | operation_logs_api_v1_logs_operation_get | none | 200,422 | 操作日志 | FUNC-log-logs-operation | unknown | FUNC-log-logs-operation | unknown | openapi.json + source code |
| API-op-0300 | GET | /api/v1/logs/error | REST | inbound | backend | FUNC-log-logs-error | error_logs_api_v1_logs_error_get | none | 200,422 | 错误日志 | FUNC-log-logs-error | unknown | FUNC-log-logs-error | unknown | openapi.json + source code |
| API-op-0301 | GET | /api/v1/logs/export | REST | inbound | backend | FUNC-log-logs-export | export_logs_api_v1_logs_export_get | none | 200,422 | 导出日志为 Excel | FUNC-log-logs-export | unknown | FUNC-log-logs-export | unknown | openapi.json + source code |
| API-op-0302 | GET | /api/v1/jobs/handlers | REST | inbound | backend | FUNC-job-jobs-handlers | list_job_handlers_api_v1_jobs_handlers_get | none | 200 | 可用的执行逻辑清单 | FUNC-job-jobs-handlers | unknown | FUNC-job-jobs-handlers | unknown | openapi.json + source code |
| API-op-0303 | GET | /api/v1/jobs | REST | inbound | backend | FUNC-job-jobs | list_jobs_api_v1_jobs_get | none | 200,422 | 任务列表 | FUNC-job-jobs | unknown | FUNC-job-jobs | unknown | openapi.json + source code |
| API-op-0304 | POST | /api/v1/jobs | REST | inbound | backend | FUNC-job-jobs | create_job_api_v1_jobs_post | application/json | 200,422 | 新增自定义任务 | FUNC-job-jobs | unknown | FUNC-job-jobs | unknown | openapi.json + source code |
| API-op-0305 | PUT | /api/v1/jobs/{job_id} | REST | inbound | backend | FUNC-job-jobs-job-id | update_job_api_v1_jobs__job_id__put | application/json | 200,422 | 编辑任务 | FUNC-job-jobs-job-id | unknown | FUNC-job-jobs-job-id | unknown | openapi.json + source code |
| API-op-0306 | DELETE | /api/v1/jobs/{job_id} | REST | inbound | backend | FUNC-job-jobs-job-id | delete_job_api_v1_jobs__job_id__delete | none | 200,422 | 删除任务 | FUNC-job-jobs-job-id | unknown | FUNC-job-jobs-job-id | unknown | openapi.json + source code |
| API-op-0307 | PUT | /api/v1/jobs/{job_id}/toggle | REST | inbound | backend | FUNC-job-jobs-job-id-toggle | toggle_job_api_v1_jobs__job_id__toggle_put | none | 200,422 | 启用 / 停用任务 | FUNC-job-jobs-job-id-toggle | unknown | FUNC-job-jobs-job-id-toggle | unknown | openapi.json + source code |
| API-op-0308 | POST | /api/v1/jobs/{job_id}/run | REST | inbound | backend | FUNC-job-jobs-job-id-run | run_job_now_api_v1_jobs__job_id__run_post | none | 200,422 | 手动执行任务 | FUNC-job-jobs-job-id-run | unknown | FUNC-job-jobs-job-id-run | unknown | openapi.json + source code |
| API-op-0309 | GET | /api/v1/jobs/status | REST | inbound | backend | FUNC-job-jobs-status | scheduler_status_api_v1_jobs_status_get | none | 200 | 调度器状态 | FUNC-job-jobs-status | unknown | FUNC-job-jobs-status | unknown | openapi.json + source code |
| API-op-0310 | GET | /api/v1/jobs/{job_id}/executions | REST | inbound | backend | FUNC-job-jobs-job-id-executions | job_executions_api_v1_jobs__job_id__executions_get | none | 200,422 | 任务执行记录 | FUNC-job-jobs-job-id-executions | unknown | FUNC-job-jobs-job-id-executions | unknown | openapi.json + source code |
| API-op-0311 | POST | /api/v1/attachments/public-upload | REST | inbound | backend | FUNC-attachment-attachments-public-upload | public_upload_api_v1_attachments_public_upload_post | multipart/form-data | 200,422 | 注册证明材料上传（匿名，仅图片） | FUNC-attachment-attachments-public-upload | unknown | FUNC-attachment-attachments-public-upload | unknown | openapi.json + source code |
| API-op-0312 | POST | /api/v1/attachments/upload | REST | inbound | backend | FUNC-attachment-attachments-upload | upload_api_v1_attachments_upload_post | multipart/form-data | 200,422 | 上传附件 | FUNC-attachment-attachments-upload | unknown | FUNC-attachment-attachments-upload | unknown | openapi.json + source code |
| API-op-0313 | POST | /api/v1/attachments/batch | REST | inbound | backend | FUNC-attachment-attachments-batch | batch_upload_api_v1_attachments_batch_post | multipart/form-data | 200,422 | 批量上传 | FUNC-attachment-attachments-batch | unknown | FUNC-attachment-attachments-batch | unknown | openapi.json + source code |
| API-op-0314 | GET | /api/v1/attachments | REST | inbound | backend | FUNC-attachment-attachments | list_attachments_api_v1_attachments_get | none | 200,422 | 附件列表 | FUNC-attachment-attachments | unknown | FUNC-attachment-attachments | unknown | openapi.json + source code |
| API-op-0315 | GET | /api/v1/attachments/{att_id}/preview | REST | inbound | backend | FUNC-attachment-attachments-att-id-preview | preview_api_v1_attachments__att_id__preview_get | none | 200,422 | 在线预览 | FUNC-attachment-attachments-att-id-preview | unknown | FUNC-attachment-attachments-att-id-preview | unknown | openapi.json + source code |
| API-op-0316 | GET | /api/v1/attachments/{att_id}/download | REST | inbound | backend | FUNC-attachment-attachments-att-id-download | download_api_v1_attachments__att_id__download_get | none | 200,422 | 下载附件 | FUNC-attachment-attachments-att-id-download | unknown | FUNC-attachment-attachments-att-id-download | unknown | openapi.json + source code |
| API-op-0317 | PUT | /api/v1/attachments/{att_id}/bind | REST | inbound | backend | FUNC-attachment-attachments-att-id-bind | bind_api_v1_attachments__att_id__bind_put | application/json | 200,422 | 绑定业务（转正式附件） | FUNC-attachment-attachments-att-id-bind | unknown | FUNC-attachment-attachments-att-id-bind | unknown | openapi.json + source code |
| API-op-0318 | DELETE | /api/v1/attachments/{att_id} | REST | inbound | backend | FUNC-attachment-attachments-att-id | delete_api_v1_attachments__att_id__delete | none | 200,422 | 删除附件 | FUNC-attachment-attachments-att-id | unknown | FUNC-attachment-attachments-att-id | unknown | openapi.json + source code |
| API-op-0319 | GET | /api/v1/lesson/plans | REST | inbound | backend | FUNC-lesson-lesson-plans | list_plans_api_v1_lesson_plans_get | none | 200,422 | 教案列表（教师） | FUNC-lesson-lesson-plans | unknown | FUNC-lesson-lesson-plans | unknown | openapi.json + source code |
| API-op-0320 | POST | /api/v1/lesson/plans | REST | inbound | backend | FUNC-lesson-lesson-plans | create_plan_api_v1_lesson_plans_post | application/json | 200,422 | 新建教案 | FUNC-lesson-lesson-plans | unknown | FUNC-lesson-lesson-plans | unknown | openapi.json + source code |
| API-op-0321 | GET | /api/v1/lesson/plans/stats | REST | inbound | backend | FUNC-lesson-lesson-plans-stats | plan_stats_api_v1_lesson_plans_stats_get | none | 200 | 教案统计 | FUNC-lesson-lesson-plans-stats | unknown | FUNC-lesson-lesson-plans-stats | unknown | openapi.json + source code |
| API-op-0322 | GET | /api/v1/lesson/plans/{plan_id} | REST | inbound | backend | FUNC-lesson-lesson-plans-plan-id | get_plan_api_v1_lesson_plans__plan_id__get | none | 200,422 | 教案详情 | FUNC-lesson-lesson-plans-plan-id | unknown | FUNC-lesson-lesson-plans-plan-id | unknown | openapi.json + source code |
| API-op-0323 | PUT | /api/v1/lesson/plans/{plan_id} | REST | inbound | backend | FUNC-lesson-lesson-plans-plan-id | update_plan_api_v1_lesson_plans__plan_id__put | application/json | 200,422 | 编辑教案 | FUNC-lesson-lesson-plans-plan-id | unknown | FUNC-lesson-lesson-plans-plan-id | unknown | openapi.json + source code |
| API-op-0324 | DELETE | /api/v1/lesson/plans/{plan_id} | REST | inbound | backend | FUNC-lesson-lesson-plans-plan-id | delete_plan_api_v1_lesson_plans__plan_id__delete | none | 200,422 | 删除教案 | FUNC-lesson-lesson-plans-plan-id | unknown | FUNC-lesson-lesson-plans-plan-id | unknown | openapi.json + source code |
| API-op-0325 | POST | /api/v1/lesson/plans/{plan_id}/copy | REST | inbound | backend | FUNC-lesson-lesson-plans-plan-id-copy | copy_plan_api_v1_lesson_plans__plan_id__copy_post | application/json | 200,422 | 复制教案 | FUNC-lesson-lesson-plans-plan-id-copy | unknown | FUNC-lesson-lesson-plans-plan-id-copy | unknown | openapi.json + source code |
| API-op-0326 | POST | /api/v1/lesson/plans/{plan_id}/share | REST | inbound | backend | FUNC-lesson-lesson-plans-plan-id-share | toggle_share_api_v1_lesson_plans__plan_id__share_post | application/json | 200,422 | 共享/取消共享 | FUNC-lesson-lesson-plans-plan-id-share | unknown | FUNC-lesson-lesson-plans-plan-id-share | unknown | openapi.json + source code |
| API-op-0327 | POST | /api/v1/lesson/plans/batch | REST | inbound | backend | FUNC-lesson-lesson-plans-batch | batch_plans_api_v1_lesson_plans_batch_post | application/json | 200,422 | 批量操作教案 | FUNC-lesson-lesson-plans-batch | unknown | FUNC-lesson-lesson-plans-batch | unknown | openapi.json + source code |
| API-op-0328 | POST | /api/v1/lesson/plans/{plan_id}/attachments | REST | inbound | backend | FUNC-lesson-lesson-plans-plan-id-attachments | upload_plan_attachment_api_v1_lesson_plans__plan_id__attachments_post | multipart/form-data | 200,422 | 上传教案附件（图片/PPT/文档） | FUNC-lesson-lesson-plans-plan-id-attachments | unknown | FUNC-lesson-lesson-plans-plan-id-attachments | unknown | openapi.json + source code |
| API-op-0329 | GET | /api/v1/lesson/plans/{plan_id}/attachments | REST | inbound | backend | FUNC-lesson-lesson-plans-plan-id-attachments | list_plan_attachments_api_v1_lesson_plans__plan_id__attachments_get | none | 200,422 | 教案附件列表 | FUNC-lesson-lesson-plans-plan-id-attachments | unknown | FUNC-lesson-lesson-plans-plan-id-attachments | unknown | openapi.json + source code |
| API-op-0330 | DELETE | /api/v1/lesson/plans/{plan_id}/attachments/{att_id} | REST | inbound | backend | FUNC-lesson-lesson-plans-plan-id-attachments-att-id | delete_plan_attachment_api_v1_lesson_plans__plan_id__attachments__att_id__delete | none | 200,422 | 删除教案附件 | FUNC-lesson-lesson-plans-plan-id-attachments-att-id | unknown | FUNC-lesson-lesson-plans-plan-id-attachments-att-id | unknown | openapi.json + source code |
| API-op-0331 | POST | /api/v1/lesson/ai/generate | REST | inbound | backend | FUNC-lesson-lesson-ai-generate | generate_lesson_api_v1_lesson_ai_generate_post | application/json | 200,422 | 提交 AI 教案生成任务 | FUNC-lesson-lesson-ai-generate | unknown | FUNC-lesson-lesson-ai-generate | unknown | openapi.json + source code |
| API-op-0332 | GET | /api/v1/lesson/ai/jobs/{job_id} | REST | inbound | backend | FUNC-lesson-lesson-ai-jobs-job-id | get_lesson_job_api_v1_lesson_ai_jobs__job_id__get | none | 200,422 | 查询 AI 教案生成进度 | FUNC-lesson-lesson-ai-jobs-job-id | unknown | FUNC-lesson-lesson-ai-jobs-job-id | unknown | openapi.json + source code |
| API-op-0333 | POST | /api/v1/lesson/ai/jobs/{job_id}/cancel | REST | inbound | backend | FUNC-lesson-lesson-ai-jobs-job-id-cancel | cancel_lesson_job_api_v1_lesson_ai_jobs__job_id__cancel_post | none | 200,422 | 取消 AI 教案生成任务 | FUNC-lesson-lesson-ai-jobs-job-id-cancel | unknown | FUNC-lesson-lesson-ai-jobs-job-id-cancel | unknown | openapi.json + source code |
| API-op-0334 | GET | /api/v1/lesson/ai/jobs | REST | inbound | backend | FUNC-lesson-lesson-ai-jobs | list_lesson_jobs_api_v1_lesson_ai_jobs_get | none | 200,422 | 我的 AI 教案生成记录 | FUNC-lesson-lesson-ai-jobs | unknown | FUNC-lesson-lesson-ai-jobs | unknown | openapi.json + source code |
| API-op-0335 | POST | /api/v1/lesson/ai/jobs/{job_id}/save | REST | inbound | backend | FUNC-lesson-lesson-ai-jobs-job-id-save | save_lesson_from_job_api_v1_lesson_ai_jobs__job_id__save_post | application/json | 200,422 | 把生成结果保存到教案库 | FUNC-lesson-lesson-ai-jobs-job-id-save | unknown | FUNC-lesson-lesson-ai-jobs-job-id-save | unknown | openapi.json + source code |
| API-op-0336 | GET | /api/v1/lesson/ai/jobs/{job_id}/export | REST | inbound | backend | FUNC-lesson-lesson-ai-jobs-job-id-export | export_lesson_api_v1_lesson_ai_jobs__job_id__export_get | none | 200,422 | 导出生成的教案（Markdown） | FUNC-lesson-lesson-ai-jobs-job-id-export | unknown | FUNC-lesson-lesson-ai-jobs-job-id-export | unknown | openapi.json + source code |
| API-op-0337 | GET | /api/v1/lesson/ai/options | REST | inbound | backend | FUNC-lesson-lesson-ai-options | get_options_api_v1_lesson_ai_options_get | none | 200,422 | 可选条件（学科按年级过滤） | FUNC-lesson-lesson-ai-options | unknown | FUNC-lesson-lesson-ai-options | unknown | openapi.json + source code |
| API-op-0338 | GET | /api/v1/health | REST | inbound | backend | FUNC-health-health | health_api_v1_health_get | none | 200 | 健康检查 | FUNC-health-health | unknown | FUNC-health-health | unknown | openapi.json + source code |
| API-op-0339 | GET | /api/v1/ready | REST | inbound | backend | FUNC-ready-ready | ready_api_v1_ready_get | none | 200 | 服务就绪检查 | FUNC-ready-ready | unknown | FUNC-ready-ready | unknown | openapi.json + source code |

## JOB-clean-expired-exams
- ID: JOB-clean-expired-exams
- 类型: BATCH
- 方向: internal
- 协议标识: app.services.task_jobs.clean_expired_exams
- 提供者: APScheduler / task_jobs
- 消费者功能: scheduled cleanup function
- Controller/Provider/Consumer/Client: task_jobs.run_job
- 请求对象: none
- 响应对象: execution result dict
- 认证与权限: system internal
- 幂等与重放: DB job lock
- 调用下游: SQLAlchemy, notification
- 物理表操作: TBL-edu-task U; TBL-sys-job-execution-log C; TBL-sys-notification C
- 兼容性风险: none
- 证据: init_db.DEFAULT_JOBS, task_jobs.JOB_HANDLERS

## API-health-ready
- ID: API-health-ready
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/health and GET /api/v1/ready
- 提供者: backend
- 消费者功能: Docker healthcheck, readiness probe
- Controller/Provider/Consumer/Client: backend/app/main.py, services/readiness.py
- 请求对象: none
- 响应对象: health/readiness JSON
- 认证与权限: public
- 幂等与重放: read-only
- 调用下游: DB, filesystem
- 物理表操作: R
- 兼容性风险: none
- 证据: source code, Dockerfile healthcheck

## 主定义索引

## API-flow-todo
- ID: API-flow-todo
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/flow/todo
- 提供者: backend
- 消费者功能: FlowTodo.vue
- Controller/Provider/Consumer/Client: backend/app/api/v1/flow.py
- 请求对象: query params
- 响应对象: list
- 认证与权限: auth + role
- 幂等与重放: read-only
- 调用下游: flow_engine
- 物理表操作: TBL-edu-flow-task R; TBL-edu-flow-instance R
- 兼容性风险: none
- 证据: source code

## API-flow-approve
- ID: API-flow-approve
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/flow/tasks/{task_id}/approve
- 提供者: backend
- 消费者功能: FlowTodo.vue
- Controller/Provider/Consumer/Client: backend/app/api/v1/flow.py
- 请求对象: comment/action body
- 响应对象: task/result
- 认证与权限: assignee/permission
- 幂等与重放: engine-managed
- 调用下游: flow_engine, rule_engine, notification
- 物理表操作: TBL-edu-flow-task U; TBL-edu-flow-instance U; TBL-edu-flow-history C
- 兼容性风险: none
- 证据: source code

## API-op-0001
- ID: API-op-0001
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/auth/captcha
- 提供者: backend
- 消费者功能: login/register
- Controller/Provider/Consumer/Client: auth.py
- 请求对象: none
- 响应对象: captcha JSON
- 认证与权限: public
- 幂等与重放: none
- 调用下游: security_cache
- 物理表操作: TBL-sys-captcha C
- 兼容性风险: none
- 证据: openapi.json

## JOB-generate-daily-report
- ID: JOB-generate-daily-report
- 类型: BATCH
- 方向: internal
- 协议标识: app.services.task_jobs.generate_daily_report
- 提供者: APScheduler / task_jobs
- 消费者功能: non-menu scheduled function
- Controller/Provider/Consumer/Client: task_jobs.run_job
- 请求对象: none
- 响应对象: execution result dict
- 认证与权限: system internal
- 幂等与重放: DB job lock
- 调用下游: SQLAlchemy, notification
- 物理表操作: TBL-sys-job-execution-log C; TBL-sys-notification C
- 兼容性风险: none
- 证据: init_db.DEFAULT_JOBS, task_jobs.JOB_HANDLERS

## JOB-clean-temp-attachments
- ID: JOB-clean-temp-attachments
- 类型: BATCH
- 方向: internal
- 协议标识: app.services.task_jobs.clean_temp_attachments
- 提供者: APScheduler / task_jobs
- 消费者功能: non-menu scheduled function
- Controller/Provider/Consumer/Client: task_jobs.run_job
- 请求对象: none
- 响应对象: execution result dict
- 认证与权限: system internal
- 幂等与重放: DB job lock
- 调用下游: SQLAlchemy, notification
- 物理表操作: TBL-sys-job-execution-log C; TBL-sys-notification C
- 兼容性风险: none
- 证据: init_db.DEFAULT_JOBS, task_jobs.JOB_HANDLERS

## JOB-push-review-reminders
- ID: JOB-push-review-reminders
- 类型: BATCH
- 方向: internal
- 协议标识: app.services.task_jobs.push_review_reminders
- 提供者: APScheduler / task_jobs
- 消费者功能: non-menu scheduled function
- Controller/Provider/Consumer/Client: task_jobs.run_job
- 请求对象: none
- 响应对象: execution result dict
- 认证与权限: system internal
- 幂等与重放: DB job lock
- 调用下游: SQLAlchemy, notification
- 物理表操作: TBL-sys-job-execution-log C; TBL-sys-notification C
- 兼容性风险: none
- 证据: init_db.DEFAULT_JOBS, task_jobs.JOB_HANDLERS

## JOB-generate-weekly-report
- ID: JOB-generate-weekly-report
- 类型: BATCH
- 方向: internal
- 协议标识: app.services.task_jobs.generate_weekly_report
- 提供者: APScheduler / task_jobs
- 消费者功能: non-menu scheduled function
- Controller/Provider/Consumer/Client: task_jobs.run_job
- 请求对象: none
- 响应对象: execution result dict
- 认证与权限: system internal
- 幂等与重放: DB job lock
- 调用下游: SQLAlchemy, notification
- 物理表操作: TBL-sys-job-execution-log C; TBL-sys-notification C
- 兼容性风险: none
- 证据: init_db.DEFAULT_JOBS, task_jobs.JOB_HANDLERS

## JOB-publish-scheduled-tasks
- ID: JOB-publish-scheduled-tasks
- 类型: BATCH
- 方向: internal
- 协议标识: app.services.task_jobs.publish_scheduled_tasks
- 提供者: APScheduler / task_jobs
- 消费者功能: non-menu scheduled function
- Controller/Provider/Consumer/Client: task_jobs.run_job
- 请求对象: none
- 响应对象: execution result dict
- 认证与权限: system internal
- 幂等与重放: DB job lock
- 调用下游: SQLAlchemy, notification
- 物理表操作: TBL-sys-job-execution-log C; TBL-sys-notification C
- 兼容性风险: none
- 证据: init_db.DEFAULT_JOBS, task_jobs.JOB_HANDLERS

## JOB-clean-old-logs
- ID: JOB-clean-old-logs
- 类型: BATCH
- 方向: internal
- 协议标识: app.services.task_jobs.clean_old_logs
- 提供者: APScheduler / task_jobs
- 消费者功能: non-menu scheduled function
- Controller/Provider/Consumer/Client: task_jobs.run_job
- 请求对象: none
- 响应对象: execution result dict
- 认证与权限: system internal
- 幂等与重放: DB job lock
- 调用下游: SQLAlchemy, notification
- 物理表操作: TBL-sys-job-execution-log C; TBL-sys-notification C
- 兼容性风险: none
- 证据: init_db.DEFAULT_JOBS, task_jobs.JOB_HANDLERS

## JOB-clean-ai-draft-questions
- ID: JOB-clean-ai-draft-questions
- 类型: BATCH
- 方向: internal
- 协议标识: app.services.task_jobs.clean_ai_draft_questions
- 提供者: APScheduler / task_jobs
- 消费者功能: non-menu scheduled function
- Controller/Provider/Consumer/Client: task_jobs.run_job
- 请求对象: none
- 响应对象: execution result dict
- 认证与权限: system internal
- 幂等与重放: DB job lock
- 调用下游: SQLAlchemy, notification
- 物理表操作: TBL-sys-job-execution-log C; TBL-sys-notification C
- 兼容性风险: none
- 证据: init_db.DEFAULT_JOBS, task_jobs.JOB_HANDLERS


## API-flow-transfer-candidates
- ID: API-flow-transfer-candidates
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/flow/tasks/{task_id}/transfer-candidates
- 提供者: backend
- 消费者功能: FlowTodo.vue
- Controller/Provider/Consumer/Client: backend/app/api/v1/flow.py
- 请求对象: unknown
- 响应对象: unknown
- 认证与权限: auth/role/assignee
- 幂等与重放: engine-managed or read-only
- 调用下游: flow_engine
- 物理表操作: TBL-edu-flow-task; TBL-edu-flow-instance; TBL-edu-flow-history
- 兼容性风险: none
- 证据: source code

## API-flow-instance-detail
- ID: API-flow-instance-detail
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/flow/instances/{instance_id}
- 提供者: backend
- 消费者功能: FlowTodo.vue
- Controller/Provider/Consumer/Client: backend/app/api/v1/flow.py
- 请求对象: unknown
- 响应对象: unknown
- 认证与权限: auth/role/assignee
- 幂等与重放: engine-managed or read-only
- 调用下游: flow_engine
- 物理表操作: TBL-edu-flow-task; TBL-edu-flow-instance; TBL-edu-flow-history
- 兼容性风险: none
- 证据: source code

## API-flow-sync
- ID: API-flow-sync
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/flow/definitions/sync
- 提供者: backend
- 消费者功能: FlowTodo.vue
- Controller/Provider/Consumer/Client: backend/app/api/v1/flow.py
- 请求对象: unknown
- 响应对象: unknown
- 认证与权限: auth/role/assignee
- 幂等与重放: engine-managed or read-only
- 调用下游: flow_engine
- 物理表操作: TBL-edu-flow-task; TBL-edu-flow-instance; TBL-edu-flow-history
- 兼容性风险: none
- 证据: source code

## API-flow-return
- ID: API-flow-return
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/flow/tasks/{task_id}/return
- 提供者: backend
- 消费者功能: FlowTodo.vue
- Controller/Provider/Consumer/Client: backend/app/api/v1/flow.py
- 请求对象: unknown
- 响应对象: unknown
- 认证与权限: auth/role/assignee
- 幂等与重放: engine-managed or read-only
- 调用下游: flow_engine
- 物理表操作: TBL-edu-flow-task; TBL-edu-flow-instance; TBL-edu-flow-history
- 兼容性风险: none
- 证据: source code

## API-flow-cancel
- ID: API-flow-cancel
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/flow/tasks/{task_id}/cancel
- 提供者: backend
- 消费者功能: FlowTodo.vue
- Controller/Provider/Consumer/Client: backend/app/api/v1/flow.py
- 请求对象: unknown
- 响应对象: unknown
- 认证与权限: auth/role/assignee
- 幂等与重放: engine-managed or read-only
- 调用下游: flow_engine
- 物理表操作: TBL-edu-flow-task; TBL-edu-flow-instance; TBL-edu-flow-history
- 兼容性风险: none
- 证据: source code

## API-flow-claim
- ID: API-flow-claim
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/flow/tasks/{task_id}/claim
- 提供者: backend
- 消费者功能: FlowTodo.vue
- Controller/Provider/Consumer/Client: backend/app/api/v1/flow.py
- 请求对象: unknown
- 响应对象: unknown
- 认证与权限: auth/role/assignee
- 幂等与重放: engine-managed or read-only
- 调用下游: flow_engine
- 物理表操作: TBL-edu-flow-task; TBL-edu-flow-instance; TBL-edu-flow-history
- 兼容性风险: none
- 证据: source code

## API-flow-urge
- ID: API-flow-urge
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/flow/tasks/{task_id}/urge
- 提供者: backend
- 消费者功能: FlowTodo.vue
- Controller/Provider/Consumer/Client: backend/app/api/v1/flow.py
- 请求对象: unknown
- 响应对象: unknown
- 认证与权限: auth/role/assignee
- 幂等与重放: engine-managed or read-only
- 调用下游: flow_engine
- 物理表操作: TBL-edu-flow-task; TBL-edu-flow-instance; TBL-edu-flow-history
- 兼容性风险: none
- 证据: source code

## API-flow-overdue
- ID: API-flow-overdue
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/flow/overdue
- 提供者: backend
- 消费者功能: FlowTodo.vue
- Controller/Provider/Consumer/Client: backend/app/api/v1/flow.py
- 请求对象: unknown
- 响应对象: unknown
- 认证与权限: auth/role/assignee
- 幂等与重放: engine-managed or read-only
- 调用下游: flow_engine
- 物理表操作: TBL-edu-flow-task; TBL-edu-flow-instance; TBL-edu-flow-history
- 兼容性风险: none
- 证据: source code

## API-flow-instances
- ID: API-flow-instances
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/flow/instances
- 提供者: backend
- 消费者功能: FlowTodo.vue
- Controller/Provider/Consumer/Client: backend/app/api/v1/flow.py
- 请求对象: unknown
- 响应对象: unknown
- 认证与权限: auth/role/assignee
- 幂等与重放: engine-managed or read-only
- 调用下游: flow_engine
- 物理表操作: TBL-edu-flow-task; TBL-edu-flow-instance; TBL-edu-flow-history
- 兼容性风险: none
- 证据: source code

## API-flow-done
- ID: API-flow-done
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/flow/done
- 提供者: backend
- 消费者功能: FlowTodo.vue
- Controller/Provider/Consumer/Client: backend/app/api/v1/flow.py
- 请求对象: unknown
- 响应对象: unknown
- 认证与权限: auth/role/assignee
- 幂等与重放: engine-managed or read-only
- 调用下游: flow_engine
- 物理表操作: TBL-edu-flow-task; TBL-edu-flow-instance; TBL-edu-flow-history
- 兼容性风险: none
- 证据: source code

## API-flow-transfer
- ID: API-flow-transfer
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/flow/tasks/{task_id}/transfer
- 提供者: backend
- 消费者功能: FlowTodo.vue
- Controller/Provider/Consumer/Client: backend/app/api/v1/flow.py
- 请求对象: unknown
- 响应对象: unknown
- 认证与权限: auth/role/assignee
- 幂等与重放: engine-managed or read-only
- 调用下游: flow_engine
- 物理表操作: TBL-edu-flow-task; TBL-edu-flow-instance; TBL-edu-flow-history
- 兼容性风险: none
- 证据: source code

## API-flow-reject
- ID: API-flow-reject
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/flow/tasks/{task_id}/reject
- 提供者: backend
- 消费者功能: FlowTodo.vue
- Controller/Provider/Consumer/Client: backend/app/api/v1/flow.py
- 请求对象: unknown
- 响应对象: unknown
- 认证与权限: auth/role/assignee
- 幂等与重放: engine-managed or read-only
- 调用下游: flow_engine
- 物理表操作: TBL-edu-flow-task; TBL-edu-flow-instance; TBL-edu-flow-history
- 兼容性风险: none
- 证据: source code

## API-flow-deadline
- ID: API-flow-deadline
- 类型: REST
- 方向: inbound
- 协议标识: PUT /api/v1/flow/tasks/{task_id}/deadline
- 提供者: backend
- 消费者功能: FlowTodo.vue
- Controller/Provider/Consumer/Client: backend/app/api/v1/flow.py
- 请求对象: unknown
- 响应对象: unknown
- 认证与权限: auth/role/assignee
- 幂等与重放: engine-managed or read-only
- 调用下游: flow_engine
- 物理表操作: TBL-edu-flow-task; TBL-edu-flow-instance; TBL-edu-flow-history
- 兼容性风险: none
- 证据: source code


## 主定义索引

## API-op-0002
- ID: API-op-0002
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/auth/register
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: register_api_v1_auth_register_post
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: 用户注册（待审批）
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0003
- ID: API-op-0003
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/auth/registrations
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: list_registrations_api_v1_auth_registrations_get
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 注册申请列表（管理员）
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0004
- ID: API-op-0004
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/auth/registrations/audit
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: audit_registration_api_v1_auth_registrations_audit_post
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: 审批注册申请（管理员）
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0005
- ID: API-op-0005
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/auth/login
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: login_api_v1_auth_login_post
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: 账号密码登录
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0006
- ID: API-op-0006
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/auth/refresh
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: refresh_token_api_v1_auth_refresh_post
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: 刷新访问令牌
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0007
- ID: API-op-0007
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/auth/profile
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: profile_api_v1_auth_profile_get
- 请求对象: none
- 响应对象: 200
- 认证与权限: 获取当前用户信息
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0008
- ID: API-op-0008
- 类型: REST
- 方向: inbound
- 协议标识: PUT /api/v1/auth/profile
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: update_profile_api_v1_auth_profile_put
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: 更新个人资料
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0009
- ID: API-op-0009
- 类型: REST
- 方向: inbound
- 协议标识: PUT /api/v1/auth/password
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: change_password_api_v1_auth_password_put
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: 修改密码
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0010
- ID: API-op-0010
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/auth/logout
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: logout_api_v1_auth_logout_post
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: 退出登录
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0011
- ID: API-op-0011
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/auth/forgot-password
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: forgot_password_api_v1_auth_forgot_password_post
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: 找回密码（发送验证码）
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0012
- ID: API-op-0012
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/auth/reset-password
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: reset_password_api_v1_auth_reset_password_post
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: 重置密码（验证码）
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0013
- ID: API-op-0013
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/flow/todo
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: todo_list_api_v1_flow_todo_get
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 我的待办
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0014
- ID: API-op-0014
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/flow/done
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: done_list_api_v1_flow_done_get
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 我的已办
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0015
- ID: API-op-0015
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/flow/instances
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: my_instances_api_v1_flow_instances_get
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 我发起的流程
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0016
- ID: API-op-0016
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/flow/instances/{instance_id}
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: instance_detail_api_v1_flow_instances__instance_id__get
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 流程实例详情
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0017
- ID: API-op-0017
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/flow/tasks/{task_id}/claim
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: claim_task_api_v1_flow_tasks__task_id__claim_post
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 认领待办
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0018
- ID: API-op-0018
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/flow/tasks/{task_id}/approve
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: approve_task_api_v1_flow_tasks__task_id__approve_post
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: 审批通过
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0019
- ID: API-op-0019
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/flow/tasks/{task_id}/reject
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: reject_task_api_v1_flow_tasks__task_id__reject_post
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: 审批驳回
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0020
- ID: API-op-0020
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/flow/tasks/{task_id}/return
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: return_task_api_v1_flow_tasks__task_id__return_post
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: 退回重填
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0021
- ID: API-op-0021
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/flow/tasks/{task_id}/cancel
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: cancel_task_api_v1_flow_tasks__task_id__cancel_post
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: 取消流程
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0022
- ID: API-op-0022
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/flow/definitions/sync
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: sync_definitions_api_v1_flow_definitions_sync_post
- 请求对象: none
- 响应对象: 200
- 认证与权限: 同步流程定义
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0023
- ID: API-op-0023
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/flow/overdue
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: overdue_list_api_v1_flow_overdue_get
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 逾期待办
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0024
- ID: API-op-0024
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/flow/tasks/{task_id}/transfer-candidates
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: transfer_candidates_api_v1_flow_tasks__task_id__transfer_candidates_get
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 可转办人员
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0025
- ID: API-op-0025
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/flow/tasks/{task_id}/transfer
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: transfer_task_api_v1_flow_tasks__task_id__transfer_post
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: 转办待办
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0026
- ID: API-op-0026
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/flow/tasks/{task_id}/urge
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: urge_task_api_v1_flow_tasks__task_id__urge_post
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: 催办
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0027
- ID: API-op-0027
- 类型: REST
- 方向: inbound
- 协议标识: PUT /api/v1/flow/tasks/{task_id}/deadline
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: set_deadline_task_api_v1_flow_tasks__task_id__deadline_put
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: 设置待办截止时间
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0028
- ID: API-op-0028
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/learning/remediation
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: plans_api_v1_learning_remediation_get
- 请求对象: none
- 响应对象: 200
- 认证与权限: Plans
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0029
- ID: API-op-0029
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/learning/remediation
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: create_plan_api_v1_learning_remediation_post
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: Create Plan
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0030
- ID: API-op-0030
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/learning/remediation/{plan_id}
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: plan_api_v1_learning_remediation__plan_id__get
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: Plan
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0031
- ID: API-op-0031
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/learning/remediation/{plan_id}/quizzes
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: start_api_v1_learning_remediation__plan_id__quizzes_post
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: Start
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0032
- ID: API-op-0032
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/learning/remediation/{plan_id}/answers
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: answer_api_v1_learning_remediation__plan_id__answers_post
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: Answer
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0033
- ID: API-op-0033
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/teaching/graph
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: graph_api_v1_teaching_graph_get
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: Graph
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0034
- ID: API-op-0034
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/teaching/graph/assign
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: assign_api_v1_teaching_graph_assign_post
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: Assign
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0035
- ID: API-op-0035
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/question/quality
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: inventory_api_v1_question_quality_get
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: Inventory
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0036
- ID: API-op-0036
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/question/quality/publish
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: publish_api_v1_question_quality_publish_post
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: Publish
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0037
- ID: API-op-0037
- 类型: REST
- 方向: inbound
- 协议标识: PUT /api/v1/question/quality/{question_id}/visual
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: visual_api_v1_question_quality__question_id__visual_put
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: Visual
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0038
- ID: API-op-0038
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/learning/tutor
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: ask_api_v1_learning_tutor_post
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: Ask
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0039
- ID: API-op-0039
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/learning/tutor/feedback
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: feedback_api_v1_learning_tutor_feedback_post
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: Feedback
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0040
- ID: API-op-0040
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/learning/tutor/feedback
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: feedback_list_api_v1_learning_tutor_feedback_get
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: Feedback List
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0041
- ID: API-op-0041
- 类型: REST
- 方向: inbound
- 协议标识: PUT /api/v1/learning/tutor/feedback/{feedback_id}
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: review_api_v1_learning_tutor_feedback__feedback_id__put
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: Review
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0042
- ID: API-op-0042
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/system/taxonomy-sync
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: history_api_v1_system_taxonomy_sync_get
- 请求对象: none
- 响应对象: 200
- 认证与权限: History
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0043
- ID: API-op-0043
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/system/taxonomy-sync/preview
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: preview_api_v1_system_taxonomy_sync_preview_post
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: Preview
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0044
- ID: API-op-0044
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/system/taxonomy-sync/apply
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: apply_api_v1_system_taxonomy_sync_apply_post
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: Apply
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0045
- ID: API-op-0045
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/system/taxonomy-sync/{run_id}/restore
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: restore_api_v1_system_taxonomy_sync__run_id__restore_post
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: Restore
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0046
- ID: API-op-0046
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/system/users
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: list_users_api_v1_system_users_get
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 用户列表
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0047
- ID: API-op-0047
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/system/users
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: create_user_api_v1_system_users_post
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: 新增用户
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0048
- ID: API-op-0048
- 类型: REST
- 方向: inbound
- 协议标识: PUT /api/v1/system/users/{user_id}
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: update_user_api_v1_system_users__user_id__put
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: 编辑用户
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0049
- ID: API-op-0049
- 类型: REST
- 方向: inbound
- 协议标识: DELETE /api/v1/system/users/{user_id}
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: delete_user_api_v1_system_users__user_id__delete
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 删除用户
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0050
- ID: API-op-0050
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/system/users/{user_id}/teachings
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: user_teachings_api_v1_system_users__user_id__teachings_get
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 教师授课关系
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0051
- ID: API-op-0051
- 类型: REST
- 方向: inbound
- 协议标识: PUT /api/v1/system/password/reset
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: reset_password_api_v1_system_password_reset_put
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: 重置用户密码（管理员）
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0052
- ID: API-op-0052
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/system/users/{user_id}/unlock
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: unlock_user_api_v1_system_users__user_id__unlock_post
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 解除账号锁定
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0053
- ID: API-op-0053
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/system/roles
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: list_roles_api_v1_system_roles_get
- 请求对象: none
- 响应对象: 200
- 认证与权限: 角色列表
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0054
- ID: API-op-0054
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/system/roles
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: create_role_api_v1_system_roles_post
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: 新增角色
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0055
- ID: API-op-0055
- 类型: REST
- 方向: inbound
- 协议标识: PUT /api/v1/system/roles/{role_id}
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: update_role_api_v1_system_roles__role_id__put
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: 编辑角色
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0056
- ID: API-op-0056
- 类型: REST
- 方向: inbound
- 协议标识: DELETE /api/v1/system/roles/{role_id}
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: delete_role_api_v1_system_roles__role_id__delete
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 删除角色
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0057
- ID: API-op-0057
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/system/roles/{role_id}/copy
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: copy_role_api_v1_system_roles__role_id__copy_post
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: 复制角色
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0058
- ID: API-op-0058
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/system/permissions
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: list_permissions_api_v1_system_permissions_get
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 权限点列表 / 树
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0059
- ID: API-op-0059
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/system/notifications
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: my_notifications_api_v1_system_notifications_get
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 我的通知
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0060
- ID: API-op-0060
- 类型: REST
- 方向: inbound
- 协议标识: PUT /api/v1/system/notifications/{notif_id}/read
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: read_notification_api_v1_system_notifications__notif_id__read_put
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 标记通知已读
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0061
- ID: API-op-0061
- 类型: REST
- 方向: inbound
- 协议标识: PUT /api/v1/system/notifications/read-all
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: read_all_api_v1_system_notifications_read_all_put
- 请求对象: none
- 响应对象: 200
- 认证与权限: 全部标记已读
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0062
- ID: API-op-0062
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/system/notification-prefs
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: get_notification_prefs_api_v1_system_notification_prefs_get
- 请求对象: none
- 响应对象: 200
- 认证与权限: 我的通知订阅偏好
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0063
- ID: API-op-0063
- 类型: REST
- 方向: inbound
- 协议标识: PUT /api/v1/system/notification-prefs
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: save_notification_prefs_api_v1_system_notification_prefs_put
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: 保存通知订阅偏好
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0064
- ID: API-op-0064
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/system/config
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: get_config_api_v1_system_config_get
- 请求对象: none
- 响应对象: 200
- 认证与权限: 系统配置（可编辑项 + 运行态只读项）
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0065
- ID: API-op-0065
- 类型: REST
- 方向: inbound
- 协议标识: PUT /api/v1/system/config
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: update_config_api_v1_system_config_put
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: 更新系统配置（管理员）
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0066
- ID: API-op-0066
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/system/version
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: get_version_info_api_v1_system_version_get
- 请求对象: none
- 响应对象: 200
- 认证与权限: 版本信息（版本号 / 构建号 / 最后更新时间）
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0067
- ID: API-op-0067
- 类型: REST
- 方向: inbound
- 协议标识: DELETE /api/v1/system/config/{key}
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: delete_config_api_v1_system_config__key__delete
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 删除系统配置
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0068
- ID: API-op-0068
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/system/ai-config
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: get_ai_config_route_api_v1_system_ai_config_get
- 请求对象: none
- 响应对象: 200
- 认证与权限: AI 大模型配置
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0069
- ID: API-op-0069
- 类型: REST
- 方向: inbound
- 协议标识: PUT /api/v1/system/ai-config
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: save_ai_config_route_api_v1_system_ai_config_put
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: 保存 AI 大模型配置
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0070
- ID: API-op-0070
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/system/ai-config/test
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: test_ai_config_route_api_v1_system_ai_config_test_post
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: 测试 AI 大模型连接
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0071
- ID: API-op-0071
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/edu/grades
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: list_grades_api_v1_edu_grades_get
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 年级列表
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0072
- ID: API-op-0072
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/edu/grades
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: create_grade_api_v1_edu_grades_post
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: 新增年级
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0073
- ID: API-op-0073
- 类型: REST
- 方向: inbound
- 协议标识: PUT /api/v1/edu/grades/{grade_id}
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: update_grade_api_v1_edu_grades__grade_id__put
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: 编辑年级
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0074
- ID: API-op-0074
- 类型: REST
- 方向: inbound
- 协议标识: DELETE /api/v1/edu/grades/{grade_id}
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: delete_grade_api_v1_edu_grades__grade_id__delete
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 删除年级
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0075
- ID: API-op-0075
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/edu/subjects
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: list_subjects_api_v1_edu_subjects_get
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 学科列表
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0076
- ID: API-op-0076
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/edu/subjects
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: create_subject_api_v1_edu_subjects_post
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: 新增学科
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0077
- ID: API-op-0077
- 类型: REST
- 方向: inbound
- 协议标识: PUT /api/v1/edu/subjects/{subject_id}
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: update_subject_api_v1_edu_subjects__subject_id__put
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: 编辑学科
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0078
- ID: API-op-0078
- 类型: REST
- 方向: inbound
- 协议标识: DELETE /api/v1/edu/subjects/{subject_id}
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: delete_subject_api_v1_edu_subjects__subject_id__delete
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 删除学科
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0079
- ID: API-op-0079
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/edu/subjects/{subject_id}/clone
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: clone_subject_api_v1_edu_subjects__subject_id__clone_post
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: 跨年级复制学科
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0080
- ID: API-op-0080
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/edu/classes/public
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: list_classes_public_api_v1_edu_classes_public_get
- 请求对象: none
- 响应对象: 200
- 认证与权限: 班级列表（注册页匿名可用）
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0081
- ID: API-op-0081
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/edu/classes
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: list_classes_api_v1_edu_classes_get
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 班级列表
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0082
- ID: API-op-0082
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/edu/classes
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: create_class_api_v1_edu_classes_post
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: 新增班级
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0083
- ID: API-op-0083
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/edu/classes/stats
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: class_stats_api_v1_edu_classes_stats_get
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 班级统计（管理页顶部卡片）
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0084
- ID: API-op-0084
- 类型: REST
- 方向: inbound
- 协议标识: PUT /api/v1/edu/classes/{class_id}
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: update_class_api_v1_edu_classes__class_id__put
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: 编辑班级
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0085
- ID: API-op-0085
- 类型: REST
- 方向: inbound
- 协议标识: DELETE /api/v1/edu/classes/{class_id}
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: delete_class_api_v1_edu_classes__class_id__delete
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 删除班级
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0086
- ID: API-op-0086
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/edu/classes/batch
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: batch_classes_api_v1_edu_classes_batch_post
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: 批量启用/停用/删除班级
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0087
- ID: API-op-0087
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/edu/classes/{class_id}/students
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: import_students_api_v1_edu_classes__class_id__students_post
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: 批量导入学生
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0088
- ID: API-op-0088
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/edu/classes/{class_id}/students
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: list_class_students_api_v1_edu_classes__class_id__students_get
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 班级学生列表（分页/搜索）
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0089
- ID: API-op-0089
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/edu/classes/{class_id}/students/export
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: export_class_students_api_v1_edu_classes__class_id__students_export_get
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 导出班级学生 CSV
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0090
- ID: API-op-0090
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/edu/classes/{class_id}/students/batch-remove
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: batch_remove_students_api_v1_edu_classes__class_id__students_batch_remove_post
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: 批量移出班级
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0091
- ID: API-op-0091
- 类型: REST
- 方向: inbound
- 协议标识: DELETE /api/v1/edu/classes/{class_id}/students/{student_id}
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: remove_student_api_v1_edu_classes__class_id__students__student_id__delete
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 移出班级
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0092
- ID: API-op-0092
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/edu/people/brief
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: people_brief_api_v1_edu_people_brief_get
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 人员简表（仅 id/姓名/账号，教师端下拉用）
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0093
- ID: API-op-0093
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/edu/class-requests
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: create_class_request_api_v1_edu_class_requests_post
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: 教师提交建班申请
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0094
- ID: API-op-0094
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/edu/class-requests
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: list_class_requests_api_v1_edu_class_requests_get
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 建班申请列表（管理员审核用）
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0095
- ID: API-op-0095
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/edu/class-requests/mine
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: my_class_requests_api_v1_edu_class_requests_mine_get
- 请求对象: none
- 响应对象: 200
- 认证与权限: 我的建班申请
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0096
- ID: API-op-0096
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/edu/class-requests/{req_id}/review
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: review_class_request_api_v1_edu_class_requests__req_id__review_post
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: 审核建班申请
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0097
- ID: API-op-0097
- 类型: REST
- 方向: inbound
- 协议标识: DELETE /api/v1/edu/class-requests/{req_id}
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: withdraw_class_request_api_v1_edu_class_requests__req_id__delete
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 撤回我的建班申请
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0098
- ID: API-op-0098
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/edu/teaching-matrix
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: teaching_matrix_api_v1_edu_teaching_matrix_get
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 任课总览：年级 → 班级 → 科目 → 任教教师
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0099
- ID: API-op-0099
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/edu/teaching-assignments
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: list_teaching_assignments_api_v1_edu_teaching_assignments_get
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 任课关系列表
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0100
- ID: API-op-0100
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/edu/teaching-assignments
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: create_teaching_assignment_api_v1_edu_teaching_assignments_post
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: 新增任课关系
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0101
- ID: API-op-0101
- 类型: REST
- 方向: inbound
- 协议标识: DELETE /api/v1/edu/teaching-assignments/{asg_id}
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: delete_teaching_assignment_api_v1_edu_teaching_assignments__asg_id__delete
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 解除任课关系
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0102
- ID: API-op-0102
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/edu/knowledge/graph
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: knowledge_graph_api_v1_edu_knowledge_graph_get
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 知识点关系图（先修 + 层级）
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0103
- ID: API-op-0103
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/edu/knowledge/tree
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: knowledge_tree_api_v1_edu_knowledge_tree_get
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 知识点树
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0104
- ID: API-op-0104
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/edu/knowledge
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: knowledge_flat_api_v1_edu_knowledge_get
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 知识点平铺列表（兼容旧接口）
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0105
- ID: API-op-0105
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/edu/knowledge
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: create_knowledge_api_v1_edu_knowledge_post
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: 新增知识点
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0106
- ID: API-op-0106
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/edu/knowledge/list
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: knowledge_list_api_v1_edu_knowledge_list_get
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 知识点平铺列表（兼容旧接口）
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0107
- ID: API-op-0107
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/edu/knowledge/stats
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: knowledge_stats_api_v1_edu_knowledge_stats_get
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 知识点统计
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0108
- ID: API-op-0108
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/edu/knowledge/template
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: knowledge_template_api_v1_edu_knowledge_template_get
- 请求对象: none
- 响应对象: 200
- 认证与权限: 下载知识点导入模板
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0109
- ID: API-op-0109
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/edu/knowledge/export
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: knowledge_export_api_v1_edu_knowledge_export_get
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 导出知识点
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0110
- ID: API-op-0110
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/edu/knowledge/mastery-overview
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: knowledge_mastery_overview_api_v1_edu_knowledge_mastery_overview_get
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 班级知识点掌握概览（教师端）
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0111
- ID: API-op-0111
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/edu/knowledge/search
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: knowledge_search_api_v1_edu_knowledge_search_get
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 知识点语义搜索（RAG）
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0112
- ID: API-op-0112
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/edu/knowledge/rag-status
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: knowledge_rag_status_api_v1_edu_knowledge_rag_status_get
- 请求对象: none
- 响应对象: 200
- 认证与权限: 知识点 RAG 索引状态
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0113
- ID: API-op-0113
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/edu/knowledge/{kp_id}
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: knowledge_detail_api_v1_edu_knowledge__kp_id__get
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 知识点详情
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0114
- ID: API-op-0114
- 类型: REST
- 方向: inbound
- 协议标识: PUT /api/v1/edu/knowledge/{kp_id}
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: update_knowledge_api_v1_edu_knowledge__kp_id__put
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: 编辑知识点
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0115
- ID: API-op-0115
- 类型: REST
- 方向: inbound
- 协议标识: DELETE /api/v1/edu/knowledge/{kp_id}
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: delete_knowledge_api_v1_edu_knowledge__kp_id__delete
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 删除知识点
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0116
- ID: API-op-0116
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/edu/knowledge/{kp_id}/attachments
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: list_knowledge_attachments_api_v1_edu_knowledge__kp_id__attachments_get
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 知识点附件列表
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0117
- ID: API-op-0117
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/edu/knowledge/{kp_id}/attachments
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: upload_knowledge_attachment_api_v1_edu_knowledge__kp_id__attachments_post
- 请求对象: multipart/form-data
- 响应对象: 200,422
- 认证与权限: 上传知识点附件
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0118
- ID: API-op-0118
- 类型: REST
- 方向: inbound
- 协议标识: PUT /api/v1/edu/knowledge/{kp_id}/attachments/{att_id}
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: update_knowledge_attachment_api_v1_edu_knowledge__kp_id__attachments__att_id__put
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: 更新知识点附件可见性
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0119
- ID: API-op-0119
- 类型: REST
- 方向: inbound
- 协议标识: DELETE /api/v1/edu/knowledge/{kp_id}/attachments/{att_id}
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: delete_knowledge_attachment_api_v1_edu_knowledge__kp_id__attachments__att_id__delete
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 删除知识点附件
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0120
- ID: API-op-0120
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/edu/knowledge/batch
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: batch_knowledge_api_v1_edu_knowledge_batch_post
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: 批量操作知识点
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0121
- ID: API-op-0121
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/edu/knowledge/import
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: import_knowledge_api_v1_edu_knowledge_import_post
- 请求对象: multipart/form-data
- 响应对象: 200,422
- 认证与权限: 导入知识点
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0122
- ID: API-op-0122
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/edu/knowledge/reindex
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: reindex_api_v1_edu_knowledge_reindex_post
- 请求对象: none
- 响应对象: 200
- 认证与权限: 重建向量索引
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0123
- ID: API-op-0123
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/edu/knowledge/purge-generic
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: purge_generic_nodes_api_v1_edu_knowledge_purge_generic_post
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: 清理「通用训练栏目」节点（预览/执行）
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0124
- ID: API-op-0124
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/edu/knowledge/diagnosis/targets
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: diagnosis_targets_api_v1_edu_knowledge_diagnosis_targets_get
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 可诊断知识点（按年级/学科）
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0125
- ID: API-op-0125
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/edu/knowledge/diagnosis/sessions
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: create_diagnosis_session_api_v1_edu_knowledge_diagnosis_sessions_post
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: 创建诊断会话
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0126
- ID: API-op-0126
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/edu/knowledge/diagnosis/sessions/{session_id}
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: get_diagnosis_session_api_v1_edu_knowledge_diagnosis_sessions__session_id__get
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 诊断会话详情
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0127
- ID: API-op-0127
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/edu/knowledge/diagnosis/sessions/{session_id}/next
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: get_next_diagnosis_item_api_v1_edu_knowledge_diagnosis_sessions__session_id__next_get
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 下一道诊断题
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0128
- ID: API-op-0128
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/edu/knowledge/diagnosis/sessions/{session_id}/answers
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: answer_diagnosis_api_v1_edu_knowledge_diagnosis_sessions__session_id__answers_post
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: 提交诊断作答
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0129
- ID: API-op-0129
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/edu/knowledge/diagnosis/sessions/{session_id}/summary
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: diagnosis_summary_api_v1_edu_knowledge_diagnosis_sessions__session_id__summary_get
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 诊断结果
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0130
- ID: API-op-0130
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/edu/knowledge/{kp_id}/prerequisites
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: list_prerequisites_api_v1_edu_knowledge__kp_id__prerequisites_get
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 知识点先修关系
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0131
- ID: API-op-0131
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/edu/knowledge/{kp_id}/prerequisites
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: add_prerequisite_api_v1_edu_knowledge__kp_id__prerequisites_post
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: 新增先修关系
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0132
- ID: API-op-0132
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/edu/knowledge/{kp_id}/dependents
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: list_dependents_api_v1_edu_knowledge__kp_id__dependents_get
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 知识点后继关系
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0133
- ID: API-op-0133
- 类型: REST
- 方向: inbound
- 协议标识: DELETE /api/v1/edu/knowledge/{kp_id}/prerequisites/{prerequisite_id}
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: remove_prerequisite_api_v1_edu_knowledge__kp_id__prerequisites__prerequisite_id__delete
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 删除先修关系
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0134
- ID: API-op-0134
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/edu/knowledge/ai/generate
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: ai_generate_api_v1_edu_knowledge_ai_generate_post
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: AI 生成知识点预览
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0135
- ID: API-op-0135
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/edu/knowledge/ai/enrich
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: ai_enrich_api_v1_edu_knowledge_ai_enrich_post
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: AI 批量补全知识点建议
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0136
- ID: API-op-0136
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/question/questions
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: list_questions_api_v1_question_questions_get
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 题目列表
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0137
- ID: API-op-0137
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/question/questions
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: create_question_api_v1_question_questions_post
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: 新增题目
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0138
- ID: API-op-0138
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/question/questions/stats
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: question_stats_api_v1_question_questions_stats_get
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 题库统计
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0139
- ID: API-op-0139
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/question/questions/batch-create
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: batch_create_questions_api_v1_question_questions_batch_create_post
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: 批量新增题目
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0140
- ID: API-op-0140
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/question/questions/batch
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: batch_questions_api_v1_question_questions_batch_post
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: 批量操作题目
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0141
- ID: API-op-0141
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/question/questions/template
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: import_template_api_v1_question_questions_template_get
- 请求对象: none
- 响应对象: 200
- 认证与权限: 下载批量导入模板
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0142
- ID: API-op-0142
- 类型: REST
- 方向: inbound
- 协议标识: PUT /api/v1/question/questions/{q_id}
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: update_question_api_v1_question_questions__q_id__put
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: 编辑题目
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0143
- ID: API-op-0143
- 类型: REST
- 方向: inbound
- 协议标识: DELETE /api/v1/question/questions/{q_id}
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: delete_question_api_v1_question_questions__q_id__delete
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 删除题目
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0144
- ID: API-op-0144
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/question/questions/{q_id}
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: get_question_api_v1_question_questions__q_id__get
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 题目详情
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0145
- ID: API-op-0145
- 类型: REST
- 方向: inbound
- 协议标识: PUT /api/v1/question/questions/{q_id}/status
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: change_status_api_v1_question_questions__q_id__status_put
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: 上下架 / 审核
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0146
- ID: API-op-0146
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/question/questions/{q_id}/duplicates
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: check_duplicate_api_v1_question_questions__q_id__duplicates_get
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 题目查重
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0147
- ID: API-op-0147
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/question/questions/import
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: import_questions_api_v1_question_questions_import_post
- 请求对象: multipart/form-data
- 响应对象: 200,422
- 认证与权限: Excel 批量导入题目
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0148
- ID: API-op-0148
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/question/questions/export
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: export_questions_api_v1_question_questions_export_get
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 导出题目为 Excel
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0149
- ID: API-op-0149
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/question/papers
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: list_papers_api_v1_question_papers_get
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 试卷列表
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0150
- ID: API-op-0150
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/question/papers
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: create_paper_api_v1_question_papers_post
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: 手动组卷
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0151
- ID: API-op-0151
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/question/papers/stats
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: paper_stats_api_v1_question_papers_stats_get
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 试卷统计
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0152
- ID: API-op-0152
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/question/papers/batch
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: batch_papers_api_v1_question_papers_batch_post
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: 批量操作试卷
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0153
- ID: API-op-0153
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/question/papers/{paper_id}
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: get_paper_api_v1_question_papers__paper_id__get
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 试卷详情（含题目）
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0154
- ID: API-op-0154
- 类型: REST
- 方向: inbound
- 协议标识: PUT /api/v1/question/papers/{paper_id}
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: update_paper_api_v1_question_papers__paper_id__put
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: 编辑试卷
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0155
- ID: API-op-0155
- 类型: REST
- 方向: inbound
- 协议标识: DELETE /api/v1/question/papers/{paper_id}
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: delete_paper_api_v1_question_papers__paper_id__delete
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 删除试卷
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0156
- ID: API-op-0156
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/question/papers/{paper_id}/archive
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: archive_paper_api_v1_question_papers__paper_id__archive_post
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: 停用 / 恢复试卷
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0157
- ID: API-op-0157
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/question/papers/{paper_id}/copy
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: copy_paper_api_v1_question_papers__paper_id__copy_post
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: 试卷复制复用
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0158
- ID: API-op-0158
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/question/papers/{paper_id}/share
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: share_paper_api_v1_question_papers__paper_id__share_post
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: 共享试卷给同科教师
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0159
- ID: API-op-0159
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/question/papers/{paper_id}/export
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: export_paper_api_v1_question_papers__paper_id__export_get
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 导出试卷（Excel/Word/PDF/HTML）
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0160
- ID: API-op-0160
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/question/questions/ai/variants
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: question_variants_api_v1_question_questions_ai_variants_post
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: AI 生成同考点变式题（预览）
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0161
- ID: API-op-0161
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/question/questions/ai/enrich
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: question_enrich_api_v1_question_questions_ai_enrich_post
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: AI 批量补全题目解析/知识点（预览）
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0162
- ID: API-op-0162
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/question/questions/ai/quality
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: question_quality_api_v1_question_questions_ai_quality_post
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: AI 批量质检题目（预览）
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0163
- ID: API-op-0163
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/question/papers/{paper_id}/ai/analyze
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: analyze_paper_api_v1_question_papers__paper_id__ai_analyze_post
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: AI 分析试卷（规则 + 建议）
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0164
- ID: API-op-0164
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/question/papers/{paper_id}/ai/recommend
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: recommend_questions_api_v1_question_papers__paper_id__ai_recommend_post
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: AI 推荐候选题
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0165
- ID: API-op-0165
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/question/standards
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: list_standards_api_v1_question_standards_get
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 命题标准列表
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0166
- ID: API-op-0166
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/question/standards
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: create_standard_api_v1_question_standards_post
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: 新建命题标准
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0167
- ID: API-op-0167
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/question/standards/options
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: standard_options_api_v1_question_standards_options_get
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 组卷用标准选项（按学段学科分组）
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0168
- ID: API-op-0168
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/question/standards/{std_id}
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: get_standard_api_v1_question_standards__std_id__get
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 命题标准详情
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0169
- ID: API-op-0169
- 类型: REST
- 方向: inbound
- 协议标识: PUT /api/v1/question/standards/{std_id}
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: update_standard_api_v1_question_standards__std_id__put
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: 编辑命题标准
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0170
- ID: API-op-0170
- 类型: REST
- 方向: inbound
- 协议标识: DELETE /api/v1/question/standards/{std_id}
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: delete_standard_api_v1_question_standards__std_id__delete
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 删除命题标准
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0171
- ID: API-op-0171
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/question/standards/{std_id}/duplicate
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: duplicate_standard_api_v1_question_standards__std_id__duplicate_post
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: 复制命题标准
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0172
- ID: API-op-0172
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/question/standards/generate-missing
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: generate_missing_standards_api_v1_question_standards_generate_missing_post
- 请求对象: none
- 响应对象: 200
- 认证与权限: 为缺失学科批量生成标准草案
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0173
- ID: API-op-0173
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/question/standards/seed
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: reseed_standards_api_v1_question_standards_seed_post
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 播种/补齐内置湖北标准
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0174
- ID: API-op-0174
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/question/standards/{std_id}/reset
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: reset_standard_api_v1_question_standards__std_id__reset_post
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 重置为内置标准
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0175
- ID: API-op-0175
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/question/papers/compose/regenerate
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: compose_regenerate_api_v1_question_papers_compose_regenerate_post
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: 组卷预览：重新生成单题或某题型
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0176
- ID: API-op-0176
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/question/papers/compose/preview
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: compose_preview_api_v1_question_papers_compose_preview_post
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: 自定义参数组卷（预览，不落库）
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0177
- ID: API-op-0177
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/question/papers/compose/ai
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: compose_ai_api_v1_question_papers_compose_ai_post
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: AI 一键智能组卷
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0178
- ID: API-op-0178
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/question/papers/compose/save
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: compose_save_api_v1_question_papers_compose_save_post
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: 保存组卷结果为新试卷
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0179
- ID: API-op-0179
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/question/papers/{paper_id}/preview
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: preview_paper_api_v1_question_papers__paper_id__preview_get
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 试卷预览（按大题分组，含答案解析）
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0180
- ID: API-op-0180
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/question/papers/{paper_id}/items
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: update_items_api_v1_question_papers__paper_id__items_post
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: 保存题目列表（增删/排序/改分）
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0181
- ID: API-op-0181
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/question/papers/{paper_id}/items/{item_id}/regenerate
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: regenerate_item_api_v1_question_papers__paper_id__items__item_id__regenerate_post
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: AI 重新生成单题
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0182
- ID: API-op-0182
- 类型: REST
- 方向: inbound
- 协议标识: DELETE /api/v1/question/papers/{paper_id}/items/{item_id}
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: remove_item_api_v1_question_papers__paper_id__items__item_id__delete
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 移除单题
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0183
- ID: API-op-0183
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/question/papers/{paper_id}/sections/rename
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: rename_section_api_v1_question_papers__paper_id__sections_rename_post
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: 大题改名
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0184
- ID: API-op-0184
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/question/papers/{paper_id}/restructure
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: restructure_paper_api_v1_question_papers__paper_id__restructure_post
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: 一键重构大题结构
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0185
- ID: API-op-0185
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/question/papers/{paper_id}/versions
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: list_versions_api_v1_question_papers__paper_id__versions_get
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 版本列表
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0186
- ID: API-op-0186
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/question/papers/{paper_id}/versions/{version}
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: get_version_api_v1_question_papers__paper_id__versions__version__get
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 版本详情
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0187
- ID: API-op-0187
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/question/papers/{paper_id}/versions/{version}/diff
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: diff_version_api_v1_question_papers__paper_id__versions__version__diff_get
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 版本对比（回溯前先看差异）
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0188
- ID: API-op-0188
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/question/papers/{paper_id}/versions/{version}/restore
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: restore_version_api_v1_question_papers__paper_id__versions__version__restore_post
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: 回溯到指定版本
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0189
- ID: API-op-0189
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/question/papers/library/list
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: paper_library_api_v1_question_papers_library_list_get
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 试卷库（我的/共享/公共/收藏）
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0190
- ID: API-op-0190
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/question/papers/{paper_id}/favorite
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: toggle_favorite_api_v1_question_papers__paper_id__favorite_post
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: 收藏/取消收藏
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0191
- ID: API-op-0191
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/question/papers/{paper_id}/share-scope
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: set_share_scope_api_v1_question_papers__paper_id__share_scope_post
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: 设置共享范围（私有/年级/全校）
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0192
- ID: API-op-0192
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/question/papers/{paper_id}/share-info
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: share_info_api_v1_question_papers__paper_id__share_info_get
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 查看共享范围与协作者
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0193
- ID: API-op-0193
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/question/papers/{paper_id}/review
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: review_paper_api_v1_question_papers__paper_id__review_post
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: 提交审核 / 审核通过 / 驳回
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0194
- ID: API-op-0194
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/question/papers/{paper_id}/export/docx
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: export_docx_api_v1_question_papers__paper_id__export_docx_get
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 导出 Word（教师卷/学生卷）
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0195
- ID: API-op-0195
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/question/papers/{paper_id}/export/pdf
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: export_pdf_api_v1_question_papers__paper_id__export_pdf_get
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 导出 PDF（教师卷/学生卷）
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0196
- ID: API-op-0196
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/question/papers/{paper_id}/export/answer-sheet
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: export_answer_sheet_api_v1_question_papers__paper_id__export_answer_sheet_get
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 导出答题卡
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0197
- ID: API-op-0197
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/question/papers/{paper_id}/export/html
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: export_html_api_v1_question_papers__paper_id__export_html_get
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 导出可打印 HTML
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0198
- ID: API-op-0198
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/question/papers/{paper_id}/export/jobs
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: create_export_job_api_v1_question_papers__paper_id__export_jobs_post
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: 提交导出任务（异步，推荐）
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0199
- ID: API-op-0199
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/question/papers/export/jobs/{job_id}
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: get_export_job_api_v1_question_papers_export_jobs__job_id__get
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 查询导出任务状态
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0200
- ID: API-op-0200
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/question/papers/export/jobs/{job_id}/file
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: download_export_job_api_v1_question_papers_export_jobs__job_id__file_get
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 下载导出文件（30 分钟有效）
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0201
- ID: API-op-0201
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/question/papers/compose/ai/async
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: compose_ai_async_api_v1_question_papers_compose_ai_async_post
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: AI 一键组卷（异步任务，推荐）
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0202
- ID: API-op-0202
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/question/papers/compose/jobs/{job_id}
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: get_compose_job_api_v1_question_papers_compose_jobs__job_id__get
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 查询组卷任务状态与结果
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0203
- ID: API-op-0203
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/question/papers/compose/jobs/{job_id}/cancel
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: cancel_compose_job_api_v1_question_papers_compose_jobs__job_id__cancel_post
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 取消组卷任务
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0204
- ID: API-op-0204
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/task/tasks
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: list_tasks_api_v1_task_tasks_get
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 作业考试列表（教师）
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0205
- ID: API-op-0205
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/task/tasks
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: create_task_api_v1_task_tasks_post
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: 发布作业 / 考试
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0206
- ID: API-op-0206
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/task/tasks/stats
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: task_stats_api_v1_task_tasks_stats_get
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 作业考试统计
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0207
- ID: API-op-0207
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/task/tasks/batch
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: batch_tasks_api_v1_task_tasks_batch_post
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: 批量操作作业考试
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0208
- ID: API-op-0208
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/task/tasks/{task_id}
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: get_task_api_v1_task_tasks__task_id__get
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 任务详情
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0209
- ID: API-op-0209
- 类型: REST
- 方向: inbound
- 协议标识: PUT /api/v1/task/tasks/{task_id}
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: update_task_api_v1_task_tasks__task_id__put
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: 编辑任务
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0210
- ID: API-op-0210
- 类型: REST
- 方向: inbound
- 协议标识: DELETE /api/v1/task/tasks/{task_id}
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: delete_task_api_v1_task_tasks__task_id__delete
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 删除任务
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0211
- ID: API-op-0211
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/task/tasks/{task_id}/submissions
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: task_submissions_api_v1_task_tasks__task_id__submissions_get
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 任务提交情况
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0212
- ID: API-op-0212
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/task/my/tasks
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: my_tasks_api_v1_task_my_tasks_get
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 我的作业考试
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0213
- ID: API-op-0213
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/task/tasks/{task_id}/paper
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: get_task_paper_api_v1_task_tasks__task_id__paper_get
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 获取试卷（作答用，不含答案）
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0214
- ID: API-op-0214
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/task/tasks/{task_id}/submit
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: submit_answers_api_v1_task_tasks__task_id__submit_post
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: 提交作答
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0215
- ID: API-op-0215
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/task/tasks/{task_id}/heartbeat
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: heartbeat_api_v1_task_tasks__task_id__heartbeat_post
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: 作答心跳（防切屏计时）
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0216
- ID: API-op-0216
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/task/submissions/{submission_id}
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: submission_detail_api_v1_task_submissions__submission_id__get
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 作答详情（含解析）
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0217
- ID: API-op-0217
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/task/my/scores
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: my_scores_api_v1_task_my_scores_get
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 我的成绩中心
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0218
- ID: API-op-0218
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/task/tasks/{task_id}/pending-students
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: pending_students_endpoint_api_v1_task_tasks__task_id__pending_students_get
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 待交名单
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0219
- ID: API-op-0219
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/task/tasks/{task_id}/urge
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: urge_task_students_api_v1_task_tasks__task_id__urge_post
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: 催交考试 / 作业
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0220
- ID: API-op-0220
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/grading/pending
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: pending_submissions_api_v1_grading_pending_get
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 待批改列表
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0221
- ID: API-op-0221
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/grading/submissions
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: submission_list_api_v1_grading_submissions_get
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 作答提交列表（兼容/按任务、班级筛选）
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0222
- ID: API-op-0222
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/grading/stats
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: grading_stats_api_v1_grading_stats_get
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 批改统计
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0223
- ID: API-op-0223
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/grading/submissions/{submission_id}
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: grading_detail_api_v1_grading_submissions__submission_id__get
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 批改详情
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0224
- ID: API-op-0224
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/grading/submissions/{submission_id}/grade
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: grade_submission_api_v1_grading_submissions__submission_id__grade_post
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: 手动批改 / 采纳 AI 建议
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0225
- ID: API-op-0225
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/grading/submissions/{submission_id}/reject
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: reject_submission_api_v1_grading_submissions__submission_id__reject_post
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: 打回重做
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0226
- ID: API-op-0226
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/grading/submissions/{submission_id}/publish
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: publish_score_api_v1_grading_submissions__submission_id__publish_post
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 发布成绩
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0227
- ID: API-op-0227
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/grading/batch/grade
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: batch_grade_api_v1_grading_batch_grade_post
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: 批量采纳当前分数（快速批改）
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0228
- ID: API-op-0228
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/grading/batch/publish
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: batch_publish_api_v1_grading_batch_publish_post
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: 批量发布成绩
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0229
- ID: API-op-0229
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/grading/unpublish
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: unpublish_scores_api_v1_grading_unpublish_post
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: 退回已发布成绩（仅发布权限）
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0230
- ID: API-op-0230
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/grading/tasks/{task_id}/report
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: class_report_api_v1_grading_tasks__task_id__report_post
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 生成班级学情报告
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0231
- ID: API-op-0231
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/grading/tasks/{task_id}/ai-comment
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: ai_teaching_advice_api_v1_grading_tasks__task_id__ai_comment_post
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: AI 生成学情教学建议
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0232
- ID: API-op-0232
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/learning/notes
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: list_notes_api_v1_learning_notes_get
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 我的笔记列表
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0233
- ID: API-op-0233
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/learning/notes
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: create_note_api_v1_learning_notes_post
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: 创建笔记
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0234
- ID: API-op-0234
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/learning/notes/shared
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: shared_notes_api_v1_learning_notes_shared_get
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 同学共享的笔记
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0235
- ID: API-op-0235
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/learning/notes/{note_id}
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: get_note_api_v1_learning_notes__note_id__get
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 笔记详情
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0236
- ID: API-op-0236
- 类型: REST
- 方向: inbound
- 协议标识: PUT /api/v1/learning/notes/{note_id}
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: update_note_api_v1_learning_notes__note_id__put
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: 更新笔记
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0237
- ID: API-op-0237
- 类型: REST
- 方向: inbound
- 协议标识: DELETE /api/v1/learning/notes/{note_id}
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: delete_note_api_v1_learning_notes__note_id__delete
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 删除笔记
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0238
- ID: API-op-0238
- 类型: REST
- 方向: inbound
- 协议标识: PUT /api/v1/learning/notes/{note_id}/share
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: share_note_api_v1_learning_notes__note_id__share_put
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: 分享笔记给同学
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0239
- ID: API-op-0239
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/learning/notes/{note_id}/organize
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: organize_note_api_v1_learning_notes__note_id__organize_post
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: AI 整理笔记
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0240
- ID: API-op-0240
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/learning/notes/{note_id}/export
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: export_note_api_v1_learning_notes__note_id__export_get
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 导出笔记为 HTML/PDF 预览
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0241
- ID: API-op-0241
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/learning/wrong-questions
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: list_wrong_api_v1_learning_wrong_questions_get
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 错题本列表
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0242
- ID: API-op-0242
- 类型: REST
- 方向: inbound
- 协议标识: PUT /api/v1/learning/wrong-questions/{wid}
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: update_wrong_api_v1_learning_wrong_questions__wid__put
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: 标注错因 / 标记掌握
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0243
- ID: API-op-0243
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/learning/wrong-questions/{wid}/analyze
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: analyze_wrong_api_v1_learning_wrong_questions__wid__analyze_post
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: AI 分析错因
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0244
- ID: API-op-0244
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/learning/wrong-questions/{wid}/redo
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: redo_wrong_api_v1_learning_wrong_questions__wid__redo_post
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 错题重做（生成专项练习）
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0245
- ID: API-op-0245
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/learning/wrong-questions/export
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: export_wrong_api_v1_learning_wrong_questions_export_get
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 导出错题
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0246
- ID: API-op-0246
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/learning/review/plans
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: review_plans_api_v1_learning_review_plans_get
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 我的复习计划
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0247
- ID: API-op-0247
- 类型: REST
- 方向: inbound
- 协议标识: PUT /api/v1/learning/review/plans/{plan_id}/complete
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: complete_review_api_v1_learning_review_plans__plan_id__complete_put
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: 完成复习
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0248
- ID: API-op-0248
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/learning/review/mastery
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: mastery_map_api_v1_learning_review_mastery_get
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 知识点掌握地图
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0249
- ID: API-op-0249
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/learning/review/plan
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: generate_plan_api_v1_learning_review_plan_post
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: AI 生成复习计划
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0250
- ID: API-op-0250
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/learning/practice
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: create_practice_api_v1_learning_practice_post
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: 创建随机练习
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0251
- ID: API-op-0251
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/learning/practice/history
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: practice_history_api_v1_learning_practice_history_get
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 练习历史
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0252
- ID: API-op-0252
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/learning/practice/{task_id}
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: get_practice_api_v1_learning_practice__task_id__get
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 获取练习题目
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0253
- ID: API-op-0253
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/learning/favorites
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: list_favorites_api_v1_learning_favorites_get
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 我的收藏夹
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0254
- ID: API-op-0254
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/learning/favorites
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: add_favorite_api_v1_learning_favorites_post
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: 收藏题目
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0255
- ID: API-op-0255
- 类型: REST
- 方向: inbound
- 协议标识: DELETE /api/v1/learning/favorites/{fav_id}
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: remove_favorite_api_v1_learning_favorites__fav_id__delete
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 取消收藏
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0256
- ID: API-op-0256
- 类型: REST
- 方向: inbound
- 协议标识: DELETE /api/v1/learning/favorites/by-question/{question_id}
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: remove_favorite_by_question_api_v1_learning_favorites_by_question__question_id__delete
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 按题目取消收藏
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0257
- ID: API-op-0257
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/learning/favorites/check-batch
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: check_favorites_batch_api_v1_learning_favorites_check_batch_get
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 批量检查收藏状态
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0258
- ID: API-op-0258
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/learning/favorites/check/{question_id}
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: check_favorite_api_v1_learning_favorites_check__question_id__get
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 检查是否已收藏
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0259
- ID: API-op-0259
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/learning/favorites/practice
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: favorites_practice_api_v1_learning_favorites_practice_post
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: 收藏题目生成专项练习
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0260
- ID: API-op-0260
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/learning/wrong-questions/{wid}/variant
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: wrong_variant_api_v1_learning_wrong_questions__wid__variant_post
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 错题变式练习（AI 生成同类题）
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0261
- ID: API-op-0261
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/learning/custom-paper
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: create_custom_paper_api_v1_learning_custom_paper_post
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: 学生自主组卷
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0262
- ID: API-op-0262
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/learning/goals
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: list_goals_api_v1_learning_goals_get
- 请求对象: none
- 响应对象: 200
- 认证与权限: 我的学习目标
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0263
- ID: API-op-0263
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/learning/goals
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: create_goal_api_v1_learning_goals_post
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: 创建学习目标
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0264
- ID: API-op-0264
- 类型: REST
- 方向: inbound
- 协议标识: PUT /api/v1/learning/goals/{goal_id}
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: update_goal_api_v1_learning_goals__goal_id__put
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: 更新目标
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0265
- ID: API-op-0265
- 类型: REST
- 方向: inbound
- 协议标识: DELETE /api/v1/learning/goals/{goal_id}
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: delete_goal_api_v1_learning_goals__goal_id__delete
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 删除目标
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0266
- ID: API-op-0266
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/learning/goals/{goal_id}/checkin
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: checkin_api_v1_learning_goals__goal_id__checkin_post
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: 每日打卡
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0267
- ID: API-op-0267
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/learning/path/recommend
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: recommend_path_api_v1_learning_path_recommend_get
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: AI 个性化学习路径推荐
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0268
- ID: API-op-0268
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/learning/flashcards
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: get_flashcards_api_v1_learning_flashcards_get
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 知识闪卡（知识点速记）
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0269
- ID: API-op-0269
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/agent/list
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: list_agents_api_v1_agent_list_get
- 请求对象: none
- 响应对象: 200
- 认证与权限: Agent 列表
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0270
- ID: API-op-0270
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/agent/status
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: agent_status_api_v1_agent_status_get
- 请求对象: none
- 响应对象: 200
- 认证与权限: AI 引擎状态
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0271
- ID: API-op-0271
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/agent/chat
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: chat_api_v1_agent_chat_post
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: AI 统一对话（自动路由）
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0272
- ID: API-op-0272
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/agent/chat/stream
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: chat_stream_api_v1_agent_chat_stream_post
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: AI 统一对话（SSE 流式）
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0273
- ID: API-op-0273
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/agent/question-generator
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: question_generator_api_v1_agent_question_generator_post
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: 题库生成 Agent
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0274
- ID: API-op-0274
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/agent/paper-composer
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: paper_composer_api_v1_agent_paper_composer_post
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: 智能组卷 Agent
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0275
- ID: API-op-0275
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/agent/grading
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: agent_grading_api_v1_agent_grading_post
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: 智能批改 Agent
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0276
- ID: API-op-0276
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/agent/study-planner
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: study_planner_api_v1_agent_study_planner_post
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: 学习规划 Agent
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0277
- ID: API-op-0277
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/agent/tutor
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: tutor_api_v1_agent_tutor_post
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: 答疑助教 Agent
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0278
- ID: API-op-0278
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/agent/note-organizer
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: note_organizer_api_v1_agent_note_organizer_post
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: 笔记整理 Agent
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0279
- ID: API-op-0279
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/agent/jobs
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: create_job_api_v1_agent_jobs_post
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: 提交长任务（异步出题/组卷）
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0280
- ID: API-op-0280
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/agent/jobs
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: list_jobs_api_v1_agent_jobs_get
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 我的任务列表
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0281
- ID: API-op-0281
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/agent/jobs/{job_id}
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: get_job_api_v1_agent_jobs__job_id__get
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 查询任务状态与结果
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0282
- ID: API-op-0282
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/agent/logs
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: agent_logs_api_v1_agent_logs_get
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: AI 调用日志
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0283
- ID: API-op-0283
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/report/student/overview
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: student_overview_api_v1_report_student_overview_get
- 请求对象: none
- 响应对象: 200
- 认证与权限: 个人学习总览
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0284
- ID: API-op-0284
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/report/student/score-trend
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: score_trend_api_v1_report_student_score_trend_get
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 成绩趋势
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0285
- ID: API-op-0285
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/report/student/knowledge-radar
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: knowledge_radar_api_v1_report_student_knowledge_radar_get
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 知识点掌握雷达图
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0286
- ID: API-op-0286
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/report/student/wrong-analysis
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: wrong_analysis_api_v1_report_student_wrong_analysis_get
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 错题分析
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0287
- ID: API-op-0287
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/report/student/learning-suggestion
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: learning_suggestion_api_v1_report_student_learning_suggestion_get
- 请求对象: none
- 响应对象: 200
- 认证与权限: 个性化学习建议
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0288
- ID: API-op-0288
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/report/teacher/class-overview
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: class_overview_api_v1_report_teacher_class_overview_get
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 班级学情概览
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0289
- ID: API-op-0289
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/report/teacher/student-comparison
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: student_comparison_api_v1_report_teacher_student_comparison_get
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 学生横向对比
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0290
- ID: API-op-0290
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/report/teacher/student-detail
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: student_detail_api_v1_report_teacher_student_detail_get
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 学生个体分析
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0291
- ID: API-op-0291
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/report/teacher/knowledge-effect
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: knowledge_effect_api_v1_report_teacher_knowledge_effect_get
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 知识点教学效果评估
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0292
- ID: API-op-0292
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/report/teacher/class-weak-points
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: class_weak_points_api_v1_report_teacher_class_weak_points_get
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 班级薄弱知识点聚合
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0293
- ID: API-op-0293
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/report/admin/overview
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: admin_overview_api_v1_report_admin_overview_get
- 请求对象: none
- 响应对象: 200
- 认证与权限: 系统总览
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0294
- ID: API-op-0294
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/report/admin/grade-comparison
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: grade_comparison_api_v1_report_admin_grade_comparison_get
- 请求对象: none
- 响应对象: 200
- 认证与权限: 各年级教学数据对比
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0295
- ID: API-op-0295
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/report/admin/subject-comparison
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: subject_comparison_api_v1_report_admin_subject_comparison_get
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 各学科教学数据对比
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0296
- ID: API-op-0296
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/report/admin/system-runtime
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: system_runtime_api_v1_report_admin_system_runtime_get
- 请求对象: none
- 响应对象: 200
- 认证与权限: 系统运行报表
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0297
- ID: API-op-0297
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/report/export/excel
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: export_excel_api_v1_report_export_excel_get
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 报表导出 Excel
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0298
- ID: API-op-0298
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/logs/login
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: login_logs_api_v1_logs_login_get
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 登录日志
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0299
- ID: API-op-0299
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/logs/operation
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: operation_logs_api_v1_logs_operation_get
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 操作日志
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0300
- ID: API-op-0300
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/logs/error
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: error_logs_api_v1_logs_error_get
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 错误日志
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0301
- ID: API-op-0301
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/logs/export
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: export_logs_api_v1_logs_export_get
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 导出日志为 Excel
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0302
- ID: API-op-0302
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/jobs/handlers
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: list_job_handlers_api_v1_jobs_handlers_get
- 请求对象: none
- 响应对象: 200
- 认证与权限: 可用的执行逻辑清单
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0303
- ID: API-op-0303
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/jobs
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: list_jobs_api_v1_jobs_get
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 任务列表
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0304
- ID: API-op-0304
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/jobs
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: create_job_api_v1_jobs_post
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: 新增自定义任务
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0305
- ID: API-op-0305
- 类型: REST
- 方向: inbound
- 协议标识: PUT /api/v1/jobs/{job_id}
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: update_job_api_v1_jobs__job_id__put
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: 编辑任务
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0306
- ID: API-op-0306
- 类型: REST
- 方向: inbound
- 协议标识: DELETE /api/v1/jobs/{job_id}
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: delete_job_api_v1_jobs__job_id__delete
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 删除任务
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0307
- ID: API-op-0307
- 类型: REST
- 方向: inbound
- 协议标识: PUT /api/v1/jobs/{job_id}/toggle
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: toggle_job_api_v1_jobs__job_id__toggle_put
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 启用 / 停用任务
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0308
- ID: API-op-0308
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/jobs/{job_id}/run
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: run_job_now_api_v1_jobs__job_id__run_post
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 手动执行任务
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0309
- ID: API-op-0309
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/jobs/status
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: scheduler_status_api_v1_jobs_status_get
- 请求对象: none
- 响应对象: 200
- 认证与权限: 调度器状态
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0310
- ID: API-op-0310
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/jobs/{job_id}/executions
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: job_executions_api_v1_jobs__job_id__executions_get
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 任务执行记录
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0311
- ID: API-op-0311
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/attachments/public-upload
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: public_upload_api_v1_attachments_public_upload_post
- 请求对象: multipart/form-data
- 响应对象: 200,422
- 认证与权限: 注册证明材料上传（匿名，仅图片）
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0312
- ID: API-op-0312
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/attachments/upload
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: upload_api_v1_attachments_upload_post
- 请求对象: multipart/form-data
- 响应对象: 200,422
- 认证与权限: 上传附件
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0313
- ID: API-op-0313
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/attachments/batch
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: batch_upload_api_v1_attachments_batch_post
- 请求对象: multipart/form-data
- 响应对象: 200,422
- 认证与权限: 批量上传
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0314
- ID: API-op-0314
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/attachments
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: list_attachments_api_v1_attachments_get
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 附件列表
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0315
- ID: API-op-0315
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/attachments/{att_id}/preview
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: preview_api_v1_attachments__att_id__preview_get
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 在线预览
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0316
- ID: API-op-0316
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/attachments/{att_id}/download
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: download_api_v1_attachments__att_id__download_get
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 下载附件
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0317
- ID: API-op-0317
- 类型: REST
- 方向: inbound
- 协议标识: PUT /api/v1/attachments/{att_id}/bind
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: bind_api_v1_attachments__att_id__bind_put
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: 绑定业务（转正式附件）
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0318
- ID: API-op-0318
- 类型: REST
- 方向: inbound
- 协议标识: DELETE /api/v1/attachments/{att_id}
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: delete_api_v1_attachments__att_id__delete
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 删除附件
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0319
- ID: API-op-0319
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/lesson/plans
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: list_plans_api_v1_lesson_plans_get
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 教案列表（教师）
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0320
- ID: API-op-0320
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/lesson/plans
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: create_plan_api_v1_lesson_plans_post
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: 新建教案
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0321
- ID: API-op-0321
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/lesson/plans/stats
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: plan_stats_api_v1_lesson_plans_stats_get
- 请求对象: none
- 响应对象: 200
- 认证与权限: 教案统计
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0322
- ID: API-op-0322
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/lesson/plans/{plan_id}
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: get_plan_api_v1_lesson_plans__plan_id__get
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 教案详情
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0323
- ID: API-op-0323
- 类型: REST
- 方向: inbound
- 协议标识: PUT /api/v1/lesson/plans/{plan_id}
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: update_plan_api_v1_lesson_plans__plan_id__put
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: 编辑教案
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0324
- ID: API-op-0324
- 类型: REST
- 方向: inbound
- 协议标识: DELETE /api/v1/lesson/plans/{plan_id}
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: delete_plan_api_v1_lesson_plans__plan_id__delete
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 删除教案
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0325
- ID: API-op-0325
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/lesson/plans/{plan_id}/copy
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: copy_plan_api_v1_lesson_plans__plan_id__copy_post
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: 复制教案
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0326
- ID: API-op-0326
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/lesson/plans/{plan_id}/share
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: toggle_share_api_v1_lesson_plans__plan_id__share_post
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: 共享/取消共享
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0327
- ID: API-op-0327
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/lesson/plans/batch
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: batch_plans_api_v1_lesson_plans_batch_post
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: 批量操作教案
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0328
- ID: API-op-0328
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/lesson/plans/{plan_id}/attachments
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: upload_plan_attachment_api_v1_lesson_plans__plan_id__attachments_post
- 请求对象: multipart/form-data
- 响应对象: 200,422
- 认证与权限: 上传教案附件（图片/PPT/文档）
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0329
- ID: API-op-0329
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/lesson/plans/{plan_id}/attachments
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: list_plan_attachments_api_v1_lesson_plans__plan_id__attachments_get
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 教案附件列表
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0330
- ID: API-op-0330
- 类型: REST
- 方向: inbound
- 协议标识: DELETE /api/v1/lesson/plans/{plan_id}/attachments/{att_id}
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: delete_plan_attachment_api_v1_lesson_plans__plan_id__attachments__att_id__delete
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 删除教案附件
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0331
- ID: API-op-0331
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/lesson/ai/generate
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: generate_lesson_api_v1_lesson_ai_generate_post
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: 提交 AI 教案生成任务
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0332
- ID: API-op-0332
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/lesson/ai/jobs/{job_id}
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: get_lesson_job_api_v1_lesson_ai_jobs__job_id__get
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 查询 AI 教案生成进度
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0333
- ID: API-op-0333
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/lesson/ai/jobs/{job_id}/cancel
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: cancel_lesson_job_api_v1_lesson_ai_jobs__job_id__cancel_post
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 取消 AI 教案生成任务
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0334
- ID: API-op-0334
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/lesson/ai/jobs
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: list_lesson_jobs_api_v1_lesson_ai_jobs_get
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 我的 AI 教案生成记录
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0335
- ID: API-op-0335
- 类型: REST
- 方向: inbound
- 协议标识: POST /api/v1/lesson/ai/jobs/{job_id}/save
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: save_lesson_from_job_api_v1_lesson_ai_jobs__job_id__save_post
- 请求对象: application/json
- 响应对象: 200,422
- 认证与权限: 把生成结果保存到教案库
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0336
- ID: API-op-0336
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/lesson/ai/jobs/{job_id}/export
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: export_lesson_api_v1_lesson_ai_jobs__job_id__export_get
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 导出生成的教案（Markdown）
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0337
- ID: API-op-0337
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/lesson/ai/options
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: get_options_api_v1_lesson_ai_options_get
- 请求对象: none
- 响应对象: 200,422
- 认证与权限: 可选条件（学科按年级过滤）
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0338
- ID: API-op-0338
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/health
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: health_api_v1_health_get
- 请求对象: none
- 响应对象: 200
- 认证与权限: 健康检查
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code

## API-op-0339
- ID: API-op-0339
- 类型: REST
- 方向: inbound
- 协议标识: GET /api/v1/ready
- 提供者: backend
- 消费者功能: unknown
- Controller/Provider/Consumer/Client: ready_api_v1_ready_get
- 请求对象: none
- 响应对象: 200
- 认证与权限: 服务就绪检查
- 幂等与重放: unknown
- 调用下游: unknown
- 物理表操作: unknown
- 兼容性风险: unknown
- 证据: openapi.json + source code


