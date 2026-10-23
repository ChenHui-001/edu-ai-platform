# 知识点资料附件（1.3.0）

## 需求

知识点可上传附件（课件/讲义/习题/拓展资料），学生在学习时能在线预览与下载。经确认：**学生允许下载附件**。

## 设计

- 复用 `sys_attachment`：`category="knowledge"`、`biz_type="knowledge_point"`、`biz_id=kp_id`、`is_temp=0`；新增 `visible_to_student`（默认 1），供教师逐份控制学生可见性。
- 上传入口：知识点详情页「资料附件」；仅 `resource:knowledge:write` 且通过知识点写 scope（教师仅任教学科/年级，grade_admin 本年级，sys_admin 全部）。
- 文件限制：沿用 `ALLOWED_UPLOAD_TYPES`（pdf/图片/Office/文本等）与 `MAX_UPLOAD_SIZE=50MB`；随机存储名、路径穿越校验、上传人记录。
- 读取：
  - 学生：仅本年级、已发布知识点、`visible_to_student=1` 的附件；列表自动过滤，直接访问 preview/download 也会校验。
  - 教师：已发布知识点附件可读；草稿/归档仅 sys_admin/grade_admin 或可写 scope 教师可读。
  - 预览/下载继续走带 Authorization 的 blob 接口，不暴露静态文件 URL；下载计数累加。
- 删除：知识点删除不级联删附件（保留审计），附件单独删除；删除时清理物理文件。
- 学生入口：新增「学习中心 → 知识资料」页面（`/student/knowledge`），按本年级知识点树浏览资料，支持预览/下载。

## API

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/edu/knowledge/{kp_id}/attachments` | 按身份过滤的附件列表 |
| POST | `/edu/knowledge/{kp_id}/attachments` | multipart 上传；form `visible_to_student` |
| PUT | `/edu/knowledge/{kp_id}/attachments/{att_id}` | 更新学生可见性 |
| DELETE | `/edu/knowledge/{kp_id}/attachments/{att_id}` | 删除附件与物理文件 |
| GET | `/attachments/{att_id}/preview` | 鉴权预览（PDF/图片内联） |
| GET | `/attachments/{att_id}/download` | 鉴权下载（学生可用） |

## 前端

- 管理端知识点详情：资料附件表格（文件名/大小/学生可见开关/下载次数/上传时间），上传、预览（PDF/图片）、下载、删除；Office/文本提示下载查看。
- 学生端 `KnowledgeLibrary.vue`：本年级知识点树 + 资料列表 + 预览/下载。
- 权限：学生端菜单由 `student:knowledge` 权限控制；管理端写按钮仍由 `resource:knowledge:write` 控制。

## 安全边界

- 学生跨年级读取附件 403；`visible_to_student=0` 时列表不返回、直接访问 preview/download 也 403。
- 教师跨 scope 上传 403；学生不能上传/删除。
- 预览 `Content-Disposition` 对中文文件名做 URL 编码，避免 Header latin-1 500。
- 文件类型/大小/空文件校验；存储名随机化，数据库不向前端返回物理路径。

## 验证

- 动态：admin 上传 PDF → 学生列表/预览(200, application/pdf)/下载(200)；教师跨年级上传 403；隐藏后学生列表为空且下载 403；教师本学科上传/删除 200。
- 后端全量 E2E 851/837/0/14；前端 build/lint/test/bundle 通过；学生端知识资料页与 47 页浏览器冒烟。
