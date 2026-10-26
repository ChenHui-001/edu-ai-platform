# 教学管理 V2 重构契约（2.0.0）

> 范围：教学管理菜单下 作业/考试（TaskManage）、批改中心（GradingCenter）、教案管理（LessonPlanManage）。不删除历史数据。

## 1. 权限
| 能力 | 权限点 |
|---|---|
| 作业/考试列表、详情 | `task:list` |
| 发布/编辑/删除/批量 | `task:write` |
| 批改列表/详情 | `grading:list` |
| 保存批改/打回 | `grading:do` |
| 发布成绩/批量发布 | `grading:publish` |
| 教案列表/详情 | `lesson:plan:list` |
| 教案新建/编辑/删除/附件 | `lesson:plan:write` |
| 教案复制 | `lesson:plan:copy` |
| 教案共享/取消共享 | `lesson:plan:share` |

- 任务：教师只能看/改/删自己创建的任务；sys_admin 全量；grade_admin 可读本年级（按 DataScope）。学生 403。
- 批改：只允许任务创建者/管理员；成绩发布需 `grading:publish`。
- 教案：列表可看自己+已共享+同科共享；编辑/删除仅创建者（或 sys_admin）；共享/取消共享仅创建者 + `lesson:plan:share`；复制需 `lesson:plan:copy`。
- 学生全部 403；前端按钮按权限 + 归属显隐。

## 2. 接口（新增，不改旧响应）
### 2.1 作业/考试
- `GET /task/tasks` 增加 `subject_id`、`class_id`、`sort`；item 增补 `class_names`、`avg_score`、`graded_count`、`published_count`。
- `GET /task/tasks/stats`：同筛选返回 `{total,ongoing,finished,draft,assigned_count,submission_count,avg_completion}`。
- `POST /task/tasks/batch`：`{action:"close"|"publish"|"delete", ids}`：
  - delete：仅 owner/sys_admin；已有提交的任务进 skipped（reason 含「提交」），不级联删除成绩；
  - close：status=finished；publish：草稿 → published；
  - 越权整体 403；返回 `{done,skipped}`。

### 2.2 批改中心
- `GET /grading/stats`（同当前教师范围）：`{pending,grading,graded,published,avg_score,submission_total}`。
- `GET /grading/submissions` 保留；增加 `class_id`、`task_id` 可筛选。
- 现有批量采纳/批量发布保留；补 `POST /grading/unpublish`（把已发布成绩退回 graded，仅 `grading:publish`）可选。
- 权限：pending/detail → `grading:list`；保存/打回 → `grading:do`；发布 → `grading:publish`；仅任务创建者/管理员可操作。

### 2.3 教案管理
- `GET /lesson/plans` 增加 `grade_id`、`subject_id`、`source`（manual/ai）、`shared`、`sort`。
- `GET /lesson/plans/stats`：`{total,mine,shared,ai,mine_shared}`。
- `POST /lesson/plans/batch`：`{action:"delete"|"share"|"unshare", ids}`：
  - 仅创建者/sys_admin；delete 有引用（课程/任务）时 skipped；share 需 share 权限；返回 done/skipped。
- 保留教案详情/AI 生成/复制/附件/共享接口。

## 3. 前端 UI（三页统一风格）
### TaskManage
- 顶部统计卡：任务总数/进行中/已结束/平均提交率。
- 筛选：类型、状态、学科、班级、关键词；分页。
- 表格多选 + 批量栏（task:write）：批量结束/批量删除；结果 done/skipped 汇总。
- 行操作按权限/归属：提交情况、学情报告、编辑、删除；任务状态 tag、提交进度条。
- 保留发布/编辑弹窗、提交抽屉、学情报告、答卷详情；按钮 loading/空态美化。

### GradingCenter
- 顶部统计卡：待批改/批改中/已批改/已发布/平均分。
- 筛选：班级、任务/关键词；队列卡片保留，增加“下一份”与批量采纳/发布；键盘快捷键提示保留。
- 权限按钮 grading:do/publish 控制；空态/加载态美化。

### LessonPlanManage
- 顶部统计卡：我的教案/共享/全部/AI 生成。
- 筛选：年级、学科、来源、共享状态、关键词。
- 多选 + 批量栏：批量共享/取消共享/删除（按权限/归属，结果汇总）。
- 行操作：查看/编辑（可编辑时）、复制、共享、删除；只读教案打开详情不显示保存。
- 保留 AI 生成教案、生成记录、附件预览/下载、阶段编辑。

## 4. 验收
- E2E 全量 0 失败；旧 task/grading/lesson 接口兼容。
- 权限动态验证：学生 403；教师不能看/改他人任务/教案、不能发布未授权成绩；管理员全量。
- 新增 stats/batch 动态验证；前端 build/lint/test/bundle；浏览器三页统计/筛选/批量/AI 正常。
- 版本 2.0.0；镜像构建推送（版本+latest+sha，内置模型缓存）。

## 5. 实现与验收（2.0.0）

- **权限**：任务 list/detail/stats/batch → `task:list`/`task:write`；批改 list/stats → `grading:list`、保存/打回 `grading:do`、发布 `grading:publish`；教案 list/stats → `lesson:plan:list`、写 `lesson:plan:write`、复制 `lesson:plan:copy`、共享 `lesson:plan:share`。教师仅本人任务/教案；grade_admin 任务本年级只读；学生 403。
- **任务**：列表新增学科/班级/排序、班级名/平均分/批改数/发布数；`/tasks/stats`；`/tasks/batch` close/publish/delete（有提交进 skipped）；已结束任务禁止交卷。
- **批改**：`/grading/stats`、`/grading/submissions` 列表筛选；批量采纳/发布、发布退回保留；统计随筛选联动。
- **教案**：列表 source/shared/sort 筛选；`/plans/stats`；`/plans/batch` delete/share/unshare（仅本人/sys_admin，越权整体 403，引用/不存在 skipped）；只读详情禁用编辑。
- **UI**：三页统一统计卡+筛选+多选批量栏+权限/归属按钮；批改队列「下一份」；教案只读态、来源标签、批量归属预校验。
- **验证**：E2E 850/836/0/14；API 动态 stats/batch/权限；前端 build/lint/test/bundle；浏览器三页统计/筛选/列表正常，无 console error。
- **镜像**：2.0.0 构建/推送后回填 digest。

