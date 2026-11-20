# 业务架构

- Output Language: zh-CN
- Status: in-progress

## 业务域

## DOM-identity-access
- ID: DOM-identity-access
- 说明: 注册、登录、角色权限、审批

## DOM-teaching-content
- ID: DOM-teaching-content
- 说明: 年级、学科、班级、任课、知识点

## DOM-question-paper
- ID: DOM-question-paper
- 说明: 题库、命题标准、组卷、试卷、导出

## DOM-task-assessment
- ID: DOM-task-assessment
- 说明: 作业考试、作答、批改、成绩

## DOM-learning-support
- ID: DOM-learning-support
- 说明: 笔记、复习、错题、收藏、目标、诊断、补弱

## DOM-ai-services
- ID: DOM-ai-services
- 说明: 对话、出题、组卷、批改、规划、答疑、整理

## DOM-reporting
- ID: DOM-reporting
- 说明: 学生、教师、管理员报表与导出

## DOM-flow-todo
- ID: DOM-flow-todo
- 说明: 流程待办、审批、转办、催办

## DOM-platform-ops
- ID: DOM-platform-ops
- 说明: 日志、定时任务、附件、配置、同步、版本

## 能力分组

## CAP-identity
- ID: CAP-identity
- 说明: 登录、注册、审批、账号管理、权限

## CAP-teaching-basics
- ID: CAP-teaching-basics
- 说明: 年级、学科、班级、任课

## CAP-knowledge-management
- ID: CAP-knowledge-management
- 说明: 知识点维护、图谱、RAG、诊断

## CAP-question-bank
- ID: CAP-question-bank
- 说明: 题库维护、AI 扩充、质检、统计

## CAP-paper-composition
- ID: CAP-paper-composition
- 说明: 标准组卷、AI 组卷、版本、共享、导出

## CAP-task-management
- ID: CAP-task-management
- 说明: 作业发布、学生作答、心跳、催交

## CAP-grading
- ID: CAP-grading
- 说明: 批改、发布、重做、报告

## CAP-learning-tools
- ID: CAP-learning-tools
- 说明: 笔记、复习、错题、收藏、目标、闪卡

## CAP-ai-assistance
- ID: CAP-ai-assistance
- 说明: 对话、任务、生成、答疑

## CAP-reporting
- ID: CAP-reporting
- 说明: 报表、分析、导出

## CAP-flow-approval
- ID: CAP-flow-approval
- 说明: 待办、审批、转办、催办

## CAP-platform-administration
- ID: CAP-platform-administration
- 说明: 用户、角色、配置、日志、任务、附件

## 场景

## SCN-login-register
- ID: SCN-login-register
- 说明: 登录与注册审批

## SCN-teacher-prepare
- ID: SCN-teacher-prepare
- 说明: 资源、知识点、题库、组卷准备

## SCN-teacher-teach
- ID: SCN-teacher-teach
- 说明: 任务发布、批改、学情分析

## SCN-student-learn
- ID: SCN-student-learn
- 说明: 练习、考试、复习、错题与目标

## SCN-student-diagnose
- ID: SCN-student-diagnose
- 说明: 诊断、补弱、路径推荐

## SCN-admin-manage
- ID: SCN-admin-manage
- 说明: 用户、权限、配置、运维

## SCN-flow-review
- ID: SCN-flow-review
- 说明: 流程审批与催办

## SCN-ai-assist
- ID: SCN-ai-assist
- 说明: AI 生成与答疑

## 入口分组

## MENU-main-dashboard
- ID: MENU-main-dashboard
- 说明: /dashboard

## MENU-admin
- ID: MENU-admin
- 说明: 管理端菜单集合

## MENU-teacher
- ID: MENU-teacher
- 说明: 教师端菜单集合

## MENU-student
- ID: MENU-student
- 说明: 学生端菜单集合

## MENU-agent
- ID: MENU-agent
- 说明: AI 助手菜单集合

## ENTRY-public-login
- ID: ENTRY-public-login
- 说明: /login

## ENTRY-public-register
- ID: ENTRY-public-register
- 说明: /register

## ENTRY-flow-todo
- ID: ENTRY-flow-todo
- 说明: /admin/flow-todo

## ENTRY-profile
- ID: ENTRY-profile
- 说明: /profile

## ENTRY-error-403
- ID: ENTRY-error-403
- 说明: /403

## ENTRY-error-404
- ID: ENTRY-error-404
- 说明: /:pathMatch(.*)*

## ENTRY-startup-lifecycle
- ID: ENTRY-startup-lifecycle
- 说明: backend startup lifecycle

## ENTRY-frontend-lifecycle
- ID: ENTRY-frontend-lifecycle
- 说明: frontend SPA initialization
