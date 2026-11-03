# 遗留 7 项问题处置报告

- **日期**：2026-11-03
- **基线**：v2.2.21（`97a5c41`）
- **结果**：**4 项已修**（含 1 项调整方案）、**2 项经实测判定不成立**、**1 项改为提示**（后端不支持覆盖语义）

---

## 处置总表

| # | 项 | 结论 | 依据 |
|---|---|---|---|
| P1 | 权限快照缓存 | **改方案：合并查询，不加缓存** | 实测鉴权 4 条 SQL 仅占响应约 10%，缓存收益 <10% 而引入撤权延迟 |
| P2 | `Grade` 的 selectin | **已修** | 全项目无任何读取点，`select(Grade)` 白拉 83 条子记录 |
| P3 | `PaperShare.from_user_id` 索引 | **已修**（含迁移） | 老库 `create_all` 不会补索引，需独立迁移清单 |
| P4 | 知识点树全量返回 | **不成立** | 2560 节点原始 995KB，**gzip 后仅 80KB**，GZip 中间件已生效 |
| P5 | 三表无默认 limit | **不成立** | `agent_logs` / `list_attachments` 均有 `PageParams + offset/limit`，且 `page_size` 有上限收敛 |
| 6 | `createVariants` 串行 | **已修**（限并发 3） | 10 条串行 ≈ 10 个 RTT；全并发会撞 SQLite 写锁 |
| 7 | 导入覆盖策略 | **改为明确提示** | 后端语义是「按题干指纹查重 → 跳过」，没有覆盖能力，加开关是假功能 |

---

## P1：为什么不做缓存（实测推翻原估算）

架构评估里的建议是「权限快照加 TTL 缓存，预期 +30~40% 吞吐」。**实测不支持这个估算**：

```
/auth/profile（纯鉴权）  p50 5.70ms   4 条 SQL
  ├ sys_revoked_token（主键查）
  ├ sys_user（主键查）
  ├ sys_user_role + sys_role（selectin）
  └ sys_role_permission + sys_permission（selectin）
```

SQLite 单条约 0.15ms，4 条约 0.6ms，占 5.7ms 的 10%。即便全部缓存，也只能省 0.3~0.5ms。

而缓存的代价是硬性的：需要覆盖 **6 个权限变更入口**（建用户分角色、改用户角色、改角色权限、建角色、注册分配默认角色、种子）逐一失效，漏一个就是「撤权后仍可操作」的越权漏洞，只能靠 TTL 兜底（30~60s 窗口）。

**改为等价但零风险的优化**：把 `roles` + `permissions` 两条 selectin 合并成一条 `joinedload` JOIN。

```python
user = db.execute(
    select(User)
    .options(joinedload(User.roles).joinedload(Role.permissions))
    .where(User.id == int(payload["sub"]))
).unique().scalar_one_or_none()
```

`unique()` 必需：joinedload 对集合会产生多行（1 用户 × N 角色 × M 权限）。

**效果**：鉴权 4 → **2 条**（1 JOIN + 1 revoked），`/auth/profile` p50 5.70 → **4.15ms**。

---

## P2：Grade 的两个 selectin 关系

```python
# 修改前
subjects: Mapped[List["Subject"]] = relationship(back_populates="grade", lazy="selectin")
classes:  Mapped[List["Class"]]   = relationship(back_populates="grade", lazy="selectin")
```

`selectin` 的语义是「加载 Grade 就自动多发一条 IN 查询」。全项目 grep 确认**没有任何代码访问 `grade.subjects` / `grade.classes`** —— 于是每次 `select(Grade)` 都白拉 60 条学科 + 23 条班级。

改为默认懒加载（保留关系本身，`Subject.grade` 的 `back_populates` 需要它）：

**效果**：`/edu/grades` 10 → **6 条**；`/edu/teaching-matrix` 11 → **7 条**。

---

## P3：索引迁移机制

`index=True` 只对**新建库**生效 —— `create_all` 不会给已存在的表补索引，与「补列」是同一类问题。

新增 `MIGRATION_INDEXES` 清单 + `run_index_migrations()`，在启动锁内、补列之后执行：

```python
MIGRATION_INDEXES = [
    ("ix_edu_paper_share_from_user_id", "edu_paper_share", "from_user_id"),
]
```

**踩坑（已修）**：索引名最初写成 `ix_edu_paper_share_from_user`，与 SQLAlchemy 默认命名 `ix_<表>_<列>` 不一致 → 新库会同时存在两个等价索引。改成同名后「已有则跳过」才真正生效。

**验证**：
- 新建库：`from_user_id` 索引数量 = 1（不重复）
- 手动 `DROP INDEX` 后重启：日志 `已执行索引迁移: ['edu_paper_share.from_user_id']`，索引被补回

---

## P4：实测数据（不成立）

```
节点数=2560  查询=59.2ms  原始=995KB  gzip=80KB
```

`GZipMiddleware(minimum_size=1000)` 已启用，实际传输 **80KB**。后端序列化成本约 10~20ms，不是瓶颈。

真正的成本在浏览器渲染 2560 个树节点 —— 那是前端问题，解法是 `el-tree` 的 `lazy` 或虚拟滚动，属产品交互改造，不该在后端加 ETag（对 1MB payload 做哈希本身就要 5~10ms，反而更慢）。

**结论**：不加任何东西。

---

## P5：复查结论（不成立）

静态扫描报「77 个 GET + `.all()` 无分页」，抽查后确认是扫描器只匹配 `.all()` 而没识别 `PageParams`：

```python
def agent_logs(params: PageParams = Depends(), ...):
    rows = db.scalars(stmt.offset(params.offset).limit(params.page_size)).all()
```

`PageParams.page_size` 还有 `MAX_PAGE_SIZE` 收敛（越界自动钳制，不报 422）。不需要改。

---

## 6：变式创建限并发 3

```js
const CONCURRENCY = 3
let cursor = 0
async function worker() {
  while (cursor < rows.length) {
    const item = rows[cursor++]
    try { await questionApi.create(build(item)); success++ }
    catch { failed.push(...) }
  }
}
await Promise.all(Array.from({ length: Math.min(CONCURRENCY, rows.length) }, () => worker()))
```

为什么是 3：后端 SQLite 单写者，全并发只会排队等锁（`busy_timeout` 5s），压太满更容易撞 `database is locked`；3 是「填满 RTT 又不积压写锁」的折中。

**逻辑验证**（独立脚本，与组件同构）：

```
success=9 failed=1 maxConcurrent=3 耗时=184ms
串行预期约 400ms，限并发 3 预期约 160ms
PASS 并发不超限、计数正确
```

---

## 7：导入重复策略

后端 `import_questions` 的实际语义：

```python
fp = _fingerprint(str(stem))
if db.scalar(select(Question).where(Question.fingerprint == fp)):
    skipped.append({"line": line_no, "reason": "题目重复", ...})
```

**只跳过，不覆盖**。加「覆盖/跳过」开关需要后端新增删除+重建逻辑，属功能开发而非修复。

改为在导入弹窗明确告知规则，避免用户导入后发现「少了几道」却不知道为什么：

> 题干指纹相同的重复题会被**跳过**（不会覆盖已有题目），导入结果里逐行给出原因。

---

## 验证汇总

| 项 | 方法 | 结果 |
|---|---|---|
| 鉴权 SQL 数 | TestClient + `before_cursor_execute` 计数 | 4 → **2** |
| grades / teaching-matrix | 同上 | 10 → **6** / 11 → **7** |
| 权限判定正确性 | 教师访问 admin 端点 | 403 ✅（仍拒绝） |
| 索引迁移 | 新建库 + 删索引后重启 | 各 1 次，幂等 ✅ |
| 关键端点回归 | 6 个端点状态码 | 全部符合预期 |
| 变式并发逻辑 | 独立脚本 | 并发 ≤3、计数正确 ✅ |
| 前端 | eslint / `npm run build` | 通过（10.8s） |
| 静态门禁 | 后端 5 道 + 前端 3 道 | 8/8 PASS |
