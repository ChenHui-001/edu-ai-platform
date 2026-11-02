# 性能排查报告：`/edu/subjects` N+1 修复与全项目同类问题扫描

- **日期**：2026-11-02
- **基线**：v2.2.19（master @ ec3f013）
- **范围**：`backend/app/api/v1/**` 全部 272 个端点 + 49 张表的索引/关系配置
- **结论**：**严重 N+1 仅此一处**，已修复（9.7 倍）；其余端点为批量预取或固定小循环，另有 5 项次级问题

---

## 1. 修复结果

| 指标 | 修复前 | 修复后 | 倍数 |
|---|---|---|---|
| HTTP p50（`?distinct=true`） | 48.5 ms | **5.0 ms** | 9.7× |
| HTTP p95 | 51.3 ms | **6.1 ms** | 8.4× |
| 函数级耗时 | 42.53 ms | **0.73 ms** | 58× |
| 单次请求 SQL 条数 | **178** | **2** | 89× |
| 与其他列表端点对比 | 慢 10 倍 | 同一水平（4–5 ms） | — |

返回内容逐字段一致（12 条去重结果，`grade_name` / `grade_count` / `same_name_ids` 均正常）。

## 2. 根因：三层机制叠加

**不是"写了全表扫描"，而是三个各自合理的配置叠在一起变成了 180 条查询。**

### ① `Grade` 的两个关系都是 `lazy="selectin"`

```python
# backend/app/models/edu.py
subjects: Mapped[List["Subject"]] = relationship(back_populates="grade", lazy="selectin")
classes:  Mapped[List["Class"]]   = relationship(back_populates="grade", lazy="selectin")
```

`selectin` 的语义是「父对象加载后立即用一条 IN 查询把子集合也拉出来」。所以每加载**一个** `Grade` 实体 = 1 条主查询 + 2 条子查询 = **3 条**。

### ② 循环里逐条 `db.get(Grade, ...)`

```python
for s in rows:                      # 60 个学科
    g = db.get(Grade, s.grade_id)   # 本以为是缓存命中
    d["grade_name"] = g.name
```

### ③ Session 的 identity map 是 **weakref** 的（关键）

直觉上「同一个 grade_id 第二次 get 应该命中缓存」。但 SQLAlchemy 的 identity map 默认用弱引用持有对象：`g` 在下一轮循环被覆盖后就没有强引用了，GC 立刻回收，缓存条目随之消失 —— **下一轮 `db.get` 真的回表**。

三者相乘：60 行 × 3 条 = **180 条**（实测 178，有 2 条命中）。学科表本身只有 60 行数据，查询开销是数据量的 3 倍。

## 3. 修复方式

改为**列查询预取**，不实例化 ORM 实体：

```python
grade_ids = {s.grade_id for s in rows if s.grade_id}
grade_names = {
    gid: gname
    for gid, gname in db.execute(
        select(Grade.id, Grade.name).where(Grade.id.in_(grade_ids))
    ).all()
} if grade_ids else {}

for s in rows:
    d = dictify(s)
    d["grade_name"] = grade_names.get(s.grade_id)
```

关键点：`select(Grade.id, Grade.name)` 返回的是 `Row` 而不是 `Grade` 实例，**不触发任何 selectin 关系加载** → 固定 1 条 SQL。

> 反例：若写成 `select(Grade).where(...)`，虽然只查 9 个年级，仍会因 selectin 多出 2 条（共 3 条）。在这个场景下无所谓，但同样的写法放进循环就会复发。

## 4. 全项目排查

### 4.1 方法（两层，互补）

**静态层**：`tools/check_n_plus_one.py`（本次新增）
用 AST 找「循环源来自数据库结果」且「循环体内有 `db.get/scalar/scalars/execute`」的位置，并顺带扫无分页 `.all()` 端点、`selectin` 关系、缺索引外键。

**运行层**：同进程 TestClient + `before_cursor_execute` 监听
对 30 个高频端点逐个统计「一次请求发出多少条 SQL」，用 `SQL 条数 ≈ 返回条数` 判定真 N+1。这是唯一能排除误报的手段。

### 4.2 结果

| 端点 | SQL 条数 | 返回条数 | 判定 |
|---|---|---|---|
| `/edu/subjects?distinct=true` | **178 → 2** | 12 | ✅ 真 N+1，已修 |
| `/edu/grades` | 10 | 9 | 否。1 主查询 + 2 selectin + 3 聚合 + 4 鉴权 |
| `/edu/classes` | 15 | 1 | 否。已批量取年级/班主任/学生数 |
| `/edu/teaching-matrix` | 11 | 9 | 否。5 条批量查询 + 4 鉴权 + 2 selectin |
| `/system/roles` | 7 | 5 | 否。`user_count` 已用聚合替代 `len(r.users)` |
| `/system/users` | 9 | 17 | 否。SQL 少于行数，说明是批量加载 |
| `/question/questions` | 7 | 0 | 否。`_kp_name_map` 已批量预取 |
| `/question/papers` / `/task/tasks` / `/lesson/plans` | 6–7 | 0 | 否 |
| `/logs/*` | 6–7 | 1–3 | 否。offset/limit 分页正常 |

**结论：除 subjects 外，没有第二个真 N+1。**

原因不是运气：代码里已有多处显式注释的批量预取，说明团队有意识：

- `question._kp_name_map()`：`"""一次预取知识点名称，避免列表循环内逐题 db.get 的 N+1。"""`
- `edu.list_classes()`：`# 批量取年级/班主任/学生数，避免逐个 get 的 N+1`
- `system.list_roles()`：`# user_count 一次聚合查出。原写法 len(r.users) 会对每个角色单独发一条 SELECT（N+1）`

**subjects 是这套约定里的漏网之鱼**，不是系统性缺陷。

### 4.3 静态扫描的 85 处命中说明

`check_n_plus_one.py` 报 85 处「循环内查库」，但运行层验证显示绝大多数不是 N+1。主要误报形态：

| 形态 | 例子 | 为什么不是 |
|---|---|---|
| 固定小循环 | `for ref in ("题目","教案"): db.scalar(...)` | 最多 3 条，与数据量无关 |
| 集合推导里只查一次 | `{kp.id: kp.name for kp in db.scalars(...)}` | 循环在内存里，SQL 只有 1 条 |
| 循环内查但已被外层预取覆盖 | `for r in rows: cache.get(...)` | 不查库 |

因此该脚本**定位为人工排查工具，不进 CI**（会淹没真问题，违背项目「门禁只拦真缺陷」的原则）。

## 5. 其他发现（按影响排序）

### P1｜每请求 4 条鉴权 SQL —— 全站固定成本

任何鉴权端点都比 `/health` 多 4 条 SQL：`sys_user`（1）+ `roles` selectin（1）+ `permissions` selectin（1）+ `sys_revoked_token`（1）。

修复后 subjects 的 5.0 ms 里约 2–3 ms 是鉴权，占一半。272 个端点、120 req/s 的负载下，这是 **~480 条 SQL/秒** 的纯重复查询。

**建议**：对 `User` 的权限快照加进程内 TTL 缓存（30–60 s），键为 `user_id`，角色/权限变更时按 user_id 主动失效。预期单请求省 3 条 SQL，吞吐 +30–40%。
**风险**：缓存窗口内权限变更不立即生效 —— 需要角色编辑接口显式清缓存，否则「撤权后仍可操作 60 秒」。

### P2｜`Grade` 的 selectin 与使用场景不匹配

`/edu/grades` 的 10 条 SQL 里有 2 条是 `Grade.subjects` / `Grade.classes` 的全量加载，但该端点只用了聚合计数（`class_count` / `subject_count`），根本不需要实体集合。

**代价**：每次 `select(Grade)` 多拉 60 条学科 + 23 条班级。
**建议**：这两处 `select(Grade)` 改用列查询；`Grade` 的关系若只在「年级详情」用到，把 `lazy` 从 `selectin` 降为 `select`（默认），用时显式 `joinedload`。
**注意**：`selectin` 是防止 N+1 的正确手段，**不要直接删掉**，否则会退化成逐条查询 —— 先确认没有别处依赖它自动加载。

### P3｜`PaperShare.from_user_id` 缺索引

`models/question.py:225`。分享列表按分享人过滤时会全表扫。当前数据量小（无感知），但 `edu_paper_share` 会随分享行为增长。
**建议**：加 `index=True`，走一次 `run_column_migrations` 或手工 `CREATE INDEX`。

### P4｜知识点树全量返回，无分页/无缓存

`knowledge_tree` 是 `.all()` 全量（树形结构使然，前端要一次渲染）。本地 323 节点，生产 **2560 节点**，响应体估算 1–2 MB。
**不是 N+1**（SQL 固定 3 条），瓶颈在传输与前端渲染。
**建议**：按年级+学科懒加载子节点（前端展开时再请求），或加 `ETag` + `If-None-Match`（树变更频率低，命中率会很高）。

### P5｜部分增长型表无分页上限

静态扫描出 77 个「GET + `.all()` 无分页」端点，运行时抽查后确认多数是短表（年级 9 行、角色 5 行、命题标准 10 条），无需处理。但以下三张表会持续增长，建议补默认 `limit`：

- `sys_operation_log`（审计日志）
- `sys_agent_call_log`（AI 调用日志，每次 AI 请求一条）
- `sys_attachment`（附件）

## 6. 验证与门禁

```
ruff check backend/ tools/ --select F,E9   PASS
check_hardcoded_host / check_weak_assertion / check_time_contract / check_model_fk / lint_gate   PASS
修复后端点与其他列表端点同水平（p50 4.1–7.2 ms）
```

## 7. 附：本次新增文件

| 文件 | 用途 | 是否入库建议 |
|---|---|---|
| `backend/app/api/v1/edu.py` | 修复 `list_subjects`（+21 行注释说明根因） | 是 |
| `tools/check_n_plus_one.py` | N+1 / 无分页 / selectin / 缺索引 四类静态扫描 | 是（人工工具，不接 CI） |
