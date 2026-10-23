# 1.5.0 UI 优化：知识点附件上传区 + 班级管理

## 1. 知识点管理 · 资料附件 UI

- 附件区改为独立视觉块：标题「资料附件」+ 数量 tag + 左侧提示（支持 PDF/图片/Office/文本、≤50MB、学生可见说明）。
- 右侧工具栏：
  - 主按钮「上传附件」（primary + Upload，支持多选 `el-upload multiple`，accept 覆盖后端允许类型）；
  - 刷新按钮（只刷新附件列表与 RAG 状态）。
- 上传：逐文件 `http-request` + 计数 loading「上传附件（N）」；前端先校验扩展名/50MB；全部完成后统一刷新列表与 RAG 状态。
- 表格：
  - 文件名前类型 tag（PDF/图片/Office/文本/其他），PDF/图片文件名可点击预览；
  - 大小格式化、下载次数、上传时间精确到分钟；
  - 操作列改为图标按钮（预览/下载/删除）+ tooltip；不可预览类型禁用并说明；
  - 「学生可见」switch 带 tooltip；
  - 空态 `el-empty` + 上传 CTA。
- 权限：上传/删除/可见性仅 `canWrite` 可用；只读用户可预览/下载。

## 2. 班级管理

### 后端（`backend/app/api/v1/edu.py`）

- `GET /edu/classes`：支持 `page/page_size/status` 分页；不传分页仍返回数组（兼容旧调用/E2E）；批量查询年级/班主任/学生数，去掉 N+1。
- `GET /edu/classes/stats`：班级数/学生数/启用数/班主任覆盖率/按年级分布。
- `GET /edu/classes/{id}/students`：分页 + 学号/姓名搜索。
- `GET /edu/classes/{id}/students/export`：鉴权 CSV 导出（中文文件名）。
- `POST /edu/classes/{id}/students/batch-remove`：批量移出学生。
- `POST /edu/classes/batch`：批量启用/停用/删除（有学生不可删）。
- `POST /edu/classes` / `PUT`：
  - 班主任必须是启用教师；
  - 支持 `description` 兼容 `remark`、`is_active`；
  - 编辑年级时同步迁移班内学生 `grade_id`；
  - 改名/改年级都做同年级重名校验。
- 非管理员列表默认只返回 DataScope 内班级（教师任教/年级管理员本年级）。

### 前端（`ClassManage.vue` 重写）

- 顶部统计卡：班级总数、学生总数、启用班级、班主任覆盖率。
- 筛选：年级、班主任、状态、关键词；服务端分页（10/20/50/100）。
- 列表：多选 + 批量启用/停用/删除；状态标签；启用/停用快捷操作；学生数可点击进入抽屉。
- 班级表单：名称、年级、班主任、状态、说明；编辑年级提示会同步迁学生。
- 学生抽屉：
  - 搜索学号/姓名、分页；
  - 批量导入（支持默认密码、失败原因汇总）、下载 CSV 模板；
  - 导出名单 CSV；
  - 多选批量移出、单人移出；
  - 统计当前班级学生数。
- 保留教师「申请建班 / 我的申请 / 建班审核」流程。

## 3. 验证

- 后端全量 E2E：851 项 / 通过 837 / 失败 0 / 环境跳过 14。
- 动态 API：分页 total=4、stats、学生分页/导出、教师 scope、班级换年级后学生 grade_id 同步、批量启停/删除跳过有学生班级，均通过。
- 前端 build/lint/test/check:bundle 通过。
- 真实浏览器：班级页统计/表格/分页/学生抽屉 20 行；知识点附件区可见，实际上传 PDF → 出现类型 tag → 预览弹窗 → 删除成功；无 console error。
- 镜像 1.5.0：构建/推送后回填 digest。
