# 教学链路功能与校验排查报告

- **日期**：2026-11-03
- **基线**：v2.2.23（`84fabdb`）
- **范围**：年级 → 学科/班级 → 知识点 → 任课 → 题库 → 组卷 → 考试 → 作答 → 批改 → 成绩
- **方法**：写/删/状态流转三类入口逐个读实现 + 关键假设实测（TestClient 真实调用）

---

## 1. 链路各节点的功能与校验现状

| 节点 | 写入口 | 关键校验 | 现状 |
|---|---|---|---|
| 年级 | `POST/PUT/DELETE /edu/grades` | 重名、序号重复、被引用阻断 | 完整 |
| 学科 | `POST/PUT/DELETE /edu/subjects` | 同年级重名、被引用阻断 | 完整 |
| 班级 | `POST/PUT/DELETE /edu/classes` | 同年级重名、**仅拦学生数** | ⚠️ 缺级联检查 |
| 知识点 | CRUD + 导入/批量 | 四类引用一次性报出（题/掌握度/复习/子节点） | 优秀 |
| 任课关系 | **无写入口** | — | ❌ 只有种子数据 |
| 题库 | CRUD + 导入 + AI | 知识点归属、删除拦试卷引用 | 完整 |
| 组卷 | `/question/papers` | 缺口上报、分数网格分配 | 完整 |
| 考试任务 | `POST/PUT/batch` | 时长>0、及格分范围、截止>开始、必须选下发对象、班级权限 | 完整 |
| 作答 | `/task/{id}/submit` | 时间窗、重复交卷 | 完整 |
| 批改 | `/grading/*` | 分数夹紧到 `[0, full_score]` | 完整 |
| 成绩发布 | `/grading/publish` | 未批改阻断 + 主观题复核（含 auto 未采纳也算未批） | 优秀 |

**横向观察：校验质量分布极不均匀。** 教学实体（知识点、班级、试卷、命题标准）的删除保护做得很细，甚至会在一条消息里列出全部阻断原因；而**账号与任务这两个入口几乎是空白**。不是团队不会做，是漏了几个写入口。

---

## 2. 校验缺口

### P0-1｜删除用户无任何保护（实测确认）

**位置**：`backend/app/api/v1/system.py:171`

```python
def delete_user(user_id, db, admin):
    if user_id == admin.id:
        raise BusinessException("不能删除自己")
    user = db.get(User, user_id)
    if not user:
        raise NotFoundException("用户不存在")
    db.delete(user)          # ← 直接删，无引用检查
    db.commit()
    return ok(message="用户已删除")
```

**实测**：teacher1 创建 1 道题后，admin 删除该账号：

```
删除前: {'Question': 1, 'Paper': 0, 'Task': 0, 'User': 17}
删除教师: 200 用户已删除
删除后: {'Question': 0, 'Paper': 0, 'Task': 0, 'User': 16}
→ 用户 -1  题目 -1
```

**波及范围**（`sys_user.id` 的 `ondelete="CASCADE"` 共 18 处）：

| 被级联删除 | 后果 |
|---|---|
| `Question.owner_id` | 该教师创建的**全部题目**消失 |
| `Paper.creator_id` | 全部试卷消失（连带 PaperItem） |
| `Task.creator_id` | 全部作业/考试消失（连带学生成绩） |
| `LessonPlan.creator_id` | 全部教案消失 |
| `TeachingAssignment.teacher_id` | 任课关系消失 |
| `Submission.student_id` | **学生的全部作答与成绩**消失 |
| learning 8 张表 | 笔记/错题/复习计划/掌握度/打卡全清 |

**前端提示同样缺失**：`UserManage.vue:293`

```js
`确认删除用户「${row.real_name}」？此操作不可恢复。`
```

只说"不可恢复"，没说要删掉多少资产。

**补全内容**：

```python
# system.py delete_user 内，db.delete(user) 之前
refs = []
q_cnt = db.scalar(select(func.count()).select_from(Question).where(Question.owner_id == user_id)) or 0
p_cnt = db.scalar(select(func.count()).select_from(Paper).where(Paper.creator_id == user_id)) or 0
t_cnt = db.scalar(select(func.count()).select_from(Task).where(Task.creator_id == user_id)) or 0
l_cnt = db.scalar(select(func.count()).select_from(LessonPlan).where(LessonPlan.creator_id == user_id)) or 0
s_cnt = db.scalar(select(func.count()).select_from(Submission).where(Submission.student_id == user_id)) or 0
for label, n in (("题目", q_cnt), ("试卷", p_cnt), ("作业/考试", t_cnt),
                 ("教案", l_cnt), ("作答记录", s_cnt)):
    if n:
        refs.append(f"{n} 个{label}")
if refs:
    raise BusinessException(
        f"该账号仍关联 {'、'.join(refs)}，删除会一并清除且不可恢复。"
        f"请改用「停用」（账号保留、禁止登录），或先转移资产。"
    )
```

前端同步：

```js
`确认删除用户「${row.real_name}」？\n该账号创建的题目/试卷/作业/教案将一并删除，学生成绩也会丢失。\n如只是离职或转岗，建议改用「停用」。`
```

**更根本的建议**：把「停用」作为默认动作、删除作为兜底。`User.is_active` / `status` 已存在，停用不影响任何历史数据，也不会让 `creator_id` 悬空。

---

### P0-2｜单条删除任务不检查提交记录（与批量入口行为不一致）

**位置**：`backend/app/api/v1/task.py:693`

```python
def delete_task(task_id, db, user):
    task = db.get(Task, task_id)
    if not _task_editable(task, user):
        raise PermissionException("无权限删除该任务")
    db.delete(task)          # ← 无 Submission 检查，成绩随 CASCADE 消失
    db.commit()
```

**对照**：批量入口 `task.py:338` 有这个检查：

```python
if action == "delete":
    sub_counts = dict(db.execute(
        select(Submission.task_id, func.count()) ...
    ).all())
    for t in tasks:
        count = int(sub_counts.get(t.id, 0) or 0)
        if count:
            skipped.append({"id": t.id,
                "reason": f"该任务已有 {count} 份提交，删除会连带丢失成绩"})
            continue
```

**同一操作、两个入口、两种行为**：批量删会跳过有成绩的任务，列表里点单条删除会直接删掉。

**前端文案还自相矛盾**：

- `TaskManage.vue:388`（批量）："已有提交记录的任务会被**跳过**（不级联删除成绩）"
- `TaskManage.vue:511`（单条）："相关提交记录将**一并删除**"

两句话都在描述同一个"删除任务"，用户无法判断哪个是真的。

**补全内容**：

```python
# delete_task 内，权限校验之后
sub_cnt = db.scalar(
    select(func.count()).select_from(Submission).where(Submission.task_id == task_id)
) or 0
if sub_cnt:
    raise BusinessException(
        f"该任务已有 {sub_cnt} 份提交记录，删除会连带丢失学生成绩。"
        f"如需终止，请使用「结束」；确需删除请先导出成绩。"
    )
```

前端单条文案改为与批量一致：

```js
`确认删除任务「${row.title}」？已有提交记录的任务不可删除。`
```

---

### P1-1｜任课关系只有读接口，没有写入口（结构性断层）

**证据**：

```
GET  /edu/teaching-matrix            （只读总览）
GET  /system/users/{id}/teachings    （只读该教师任课）
TeachingAssignment(...) 的写入       → 仅 init_db.py:479（种子数据）
```

全项目**没有任何 API 能创建/修改/删除任课关系**，前端也只有 `teachingMatrix` 一个只读调用。

**影响**：教师端的数据范围由 `DataScope.class_ids()` 从 `TeachingAssignment` 查出。新入职教师登录后：

- 班级列表为空（`class_ids()` 返回空列表 = 拒绝）
- 无法布置作业/考试
- 学情分析、班级报表全空

而管理员在界面上**没有任何地方能解决这个问题**。

**补全内容**：

```
POST   /edu/teaching-assignments        body: {teacher_id, class_id, subject_id}
DELETE /edu/teaching-assignments/{id}
GET    /edu/teaching-assignments?teacher_id=&class_id=
```

必须做的两条校验：

```python
# 1) 班级与学科必须同年级（跨年级任课在教学上不存在）
if klass.grade_id != subject.grade_id:
    raise BusinessException(
        f"班级「{klass.name}」属于{klass_grade.name}，"
        f"学科「{subject.name}」属于{subject_grade.name}，不能跨年级任课")

# 2) 同班同科已有其他教师时给出明确提示（而不是静默产生两条记录）
existing = db.scalar(select(TeachingAssignment).where(
    TeachingAssignment.class_id == class_id,
    TeachingAssignment.subject_id == subject_id,
    TeachingAssignment.is_active.is_(True)))
if existing and existing.teacher_id != teacher_id:
    raise BusinessException(
        f"该班级的{subject.name}已由{existing_teacher.real_name}任教，"
        f"如需更换请先解除原任课关系")
```

> 注：`teaching-matrix` 里已有"同班同科多条以最后一条为准"的注释，说明数据层允许历史多条；但**写入端必须拦住**，否则教师端可见范围会随记录顺序漂移。

---

### P1-2｜删除班级只拦学生，不拦任课与任务下发

**位置**：`backend/app/api/v1/edu.py:770`

```python
student_cnt = db.scalar(select(func.count()).select_from(User).where(
    User.class_id == class_id, User.identity == "student")) or 0
if student_cnt:
    raise BusinessException(f"该班级仍有 {student_cnt} 名学生，请先转移学生后再删除")
db.delete(k)
```

只检查学生。但 `TeachingAssignment.class_id` 和 `TaskAssignment.class_id` 都是 `CASCADE`：

- 该班的任课记录被静默删除（教师端该班消失，无任何告知）
- 该班的历史任务下发记录被静默删除（学生端已结束的考试从"我的作业"里消失）

**触发条件**：空班级（学生已转走）但有过任课和考试 —— 现实中很常见（毕业班清理）。

**补全内容**：

```python
asg_cnt = db.scalar(select(func.count()).select_from(TeachingAssignment).where(
    TeachingAssignment.class_id == class_id)) or 0
task_cnt = db.scalar(select(func.count()).select_from(TaskAssignment).where(
    TaskAssignment.class_id == class_id)) or 0
if asg_cnt or task_cnt:
    raise BusinessException(
        f"该班级仍有 {asg_cnt} 条任课关系、{task_cnt} 条任务下发记录，"
        f"删除会一并清除且无法恢复。如班级已解散，建议改为「停用」（is_active=false）。")
```

---

### P2-1｜修改题目不检查是否已组卷，会导致试卷总分不一致

**位置**：`backend/app/api/v1/question.py:615`

`update_question` 只校验年级/学科存在、权限归属，**不检查该题是否已被试卷引用**。

而 `delete_question`（同文件 686 行附近）有引用检查：

```python
ref_cnt = db.scalar(select(func.count()).select_from(PaperItem).where(
    PaperItem.question_id == q_id)) or 0
if ref_cnt:
    raise BusinessException(f"该题目已被 {ref_cnt} 份试卷引用，请先从相关试卷中移除")
```

**后果**：删除有保护，**修改没有**。把一道已组卷题目的分值从 5 改成 10：

- `PaperItem.score` 仍是 5（不改）
- `Paper.total_score` 仍是 100（不重算）
- 卷面显示 5 分，但题目本身标 10 分 —— 教师导出时对不上

**补全内容**：

```python
# update_question 内，改 score/type 前
if "score" in data or "type" in data:
    ref_cnt = db.scalar(select(func.count()).select_from(PaperItem).where(
        PaperItem.question_id == q_id)) or 0
    if ref_cnt:
        raise BusinessException(
            f"该题目已被 {ref_cnt} 份试卷引用，修改分值或题型会导致试卷总分不一致。"
            f"请先在试卷中调整，或复制一份新题再改。")
```

---

### P2-2｜唯一约束冲突的提示过于通用

**位置**：`backend/app/core/exception.py:82`

```python
return JSONResponse(status_code=400,
    content=_body(400, "数据冲突，请检查唯一性字段或关联数据"))
```

好的一面：不会 500，业务不会崩。差的一面：用户不知道**哪条数据**冲突了（是学科重名？账号重复？外键不存在？）。

**优化方向**：解析 `exc.orig` 提取表名与约束名，映射成中文：

```python
TABLE_LABELS = {"edu_subject": "学科", "sys_user": "账号", "edu_class": "班级", ...}
# 从 "UNIQUE constraint failed: edu_subject.grade_id, edu_subject.name" 提取
```

已有先例可参考：`api/v1/logs.py:200` 的注释明确写了"name 是唯一约束：不先查一次会抛 IntegrityError → 500 + 前端只看到「服务器错误」"，说明团队知道这个问题，只是没做成全局能力。

---

## 3. 提示信息补全清单

| 位置 | 现状 | 补全内容 |
|---|---|---|
| `UserManage.vue:293` | "此操作不可恢复" | 列出将删除的题目/试卷/任务/教案/成绩数量；引导用「停用」 |
| `TaskManage.vue:511` | "提交记录将一并删除" | 改为"已有提交记录不可删除"，与批量口径一致 |
| `TaskManage.vue:388` | 批量文案是对的 | 无需改 |
| `delete_user` 后端 | "用户已删除" | 附带"已停用/已删除 N 项资产" |
| `delete_class` 后端 | 只报学生数 | 追加任课/任务下发条数 |
| `update_question` 后端 | 无 | 已组卷的题目改分值时提示引用数 |
| 学科/班级创建 | 已有"该年级下已存在…" | 保持 |
| 任课关系 | 无接口 | 冲突时提示"已由 XX 任教" |

---

## 4. 优化方向（功能层面）

1. **删除 → 停用优先**。`User`、`Class`、`Subject` 都有 `is_active` 字段，停用不破坏历史数据，也不会让 `creator_id` 悬空。把"删除"降级为"仅当无任何引用时可用"。
2. **统一删除前的引用清单口径**。现在只有知识点做到了"一次报全所有阻断原因"，其余各处都是遇到第一个问题就返回。建议抽一个 `collect_delete_blockers()` 工具，各实体登记自己的检查项，一次返回全部。
3. **补齐任课关系的写入闭环**（P1-1）。这是链路里唯一"有模型、有查询、没入口"的节点。
4. **账号删除改为软删除**。教育系统的成绩与作答是有留存价值的档案，物理删除一个学生等于销毁其学业记录。
5. **任务删除与"结束"语义分离**。应明确：结束 = 停止作答、保留成绩；删除 = 仅草稿可用。

---

## 5. 建议修复顺序

| 顺序 | 项 | 理由 |
|---|---|---|
| 1 | P0-1 用户删除保护 | 破坏半径最大，一次误操作即不可恢复 |
| 2 | P0-2 任务单条删除检查 | 与批量入口行为不一致，用户按提示操作反而丢数据 |
| 3 | P1-2 班级删除引用检查 | 同上，属于"删了不该删的" |
| 4 | P1-1 任课关系 CRUD | 功能性缺失，不补则新教师无法使用系统 |
| 5 | P2-1 题目编辑引用检查 | 数据一致性问题，影响导出与核对 |
| 6 | P2-2 冲突提示细化 | 体验问题，不影响正确性 |

前三项都是**只加检查、不改数据结构**，风险低；第 4 项需要新增接口与前端页面，工作量最大。
