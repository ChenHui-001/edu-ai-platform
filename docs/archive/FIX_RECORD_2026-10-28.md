# 修复记录（2026-10-28）· 第二批性能与并发修复

> 对象：v2.1.12（commit `f983deb`）
> 前提：在第一批（`5a5e33e`）性能修复基础上继续，把「审查 → 修复 → 验证 → 发布」走完一整轮。
> 纪律：**每个问题一次独立提交**，全部修完再跑全量回归，测试不过不推送、不构镜像、不部署。
> 测试文件：`tests/test_unit_perf_batch1.py`（27 → 135 条断言，10 个 section）

---

## 一、修复清单总览

| # | 模块 | 问题类型 | 旧查询数 | 新查询数 | commit |
|---|---|---|---|---|---|
| 1 | `question.py` 题库统计 | 8 次全表扫描 | 8 | 2 | `5a5e33e` |
| 2 | `task.py` 学生任务列表 | N+1 + selectin 超取 | 30（N=14 时） | 4 | `ef043f2` |
| 3 | `knowledge.py` 知识点统计 | 整行载入 + 应用层筛 | 取回 1800 行 | 聚合下推 | `8755e4f` |
| 4 | `grading.py` 批量采纳批改 | 4N 条查询 | 33（N=8 时） | 9 | `08f483d` |
| 5 | `attachment.py` 下载计数 | 读-改-写丢更新 | 并发丢计数 | 原子自增 | `c87391d` |

生产规模基准库（知识点 1800 / 题目 9000 / 下发记录 8000 / 提交 3000 / 学生 200 / 任务 40）实测：

| 接口 | 旧 | 新 | 倍数 |
|---|---|---|---|
| `question_stats` | 37.38 ms | 15.60 ms | **2.4×** |
| `my_tasks` | 139.37 ms | 10.66 ms | **13.1×** |
| `knowledge_stats` | 15.49 ms | 3.30 ms | **4.7×** |

---

## 二、逐项说明

### 1. 题库统计：8 次扫描 → 2 次（`5a5e33e`）

- **问题**：`total` / `with_analysis` / `with_knowledge` / `ai_source` 四个计数各发一条 SQL，
  四个维度的分布（题型 / 难度 / 状态 / 题库）又各发一条 —— 八次全表扫描，每次都要过一遍同样的 WHERE。
- **改法**：条件聚合下推。

```python
def _sum_case(cond):
    """统计满足 cond 的行数；空集时为 0 而不是 None。"""
    return func.coalesce(func.sum(case((cond, 1), else_=0)), 0)

# ① total + 三个条件计数，一次扫描
total, with_analysis, with_knowledge, ai_source = db.execute(
    stmt.with_only_columns(
        func.count(),
        _sum_case(and_(Question.analysis.isnot(None), Question.analysis != "")),
        _sum_case(Question.knowledge_point_id.isnot(None)),
        _sum_case(Question.source.like("ai%")),
    ).select_from(Question)
).one()
```

- **关键点一**：空集时 `SUM` 返回 `NULL` 而不是 0，必须 `coalesce` 兜底，否则前端拿到 `null`。
- **关键点二**：四维分布合并成一次 **组合 GROUP BY**（题型×难度×状态×题库），
  再沿各维度把计数**回卷**成边缘分布。行数上界 = 8×3×3×2 = 144，远小于全表。
  因为每行恰好落入一个组合分组，沿任一维度求和可**精确**还原该维度的边缘分布。

### 2. 学生端任务列表：30 → 4（`ef043f2`）

- **问题**：列表里每个 task 都要单独查「我的提交」和「作答次数」，2+2N；加上 `Task.paper`、
  `Task.assignments`、`Submission.answers` 都是 `lazy="selectin"`，一次列表把关联表全预加载了。
- **改法**：

```python
my_ids = set(db.scalars(select(TaskAssignment.task_id).where(assign_cond)).all())
...
q = q.options(noload(Task.paper), noload(Task.assignments))
...
# 分页后一次性取本页所有提交，内存里归并
subs = db.scalars(
    select(Submission).where(
        Submission.student_id == user.id,
        Submission.task_id.in_(page_task_ids),
    ).order_by(Submission.task_id, Submission.attempt)
    .options(noload(Submission.answers))
).all()
```

- **关键点**：出参走 `dictify()`，只读 `__table__.columns`，所以 selectin 预加载**全是浪费**，
  必须显式 `noload(...)`。这是本项目最容易反复踩的性能坑。
- **顺带修掉一个语义 bug**：旧实现用 `order_by(attempt.desc()).limit(1)` 取最新一次作答，
  并列时由 SQLite 自行决定返回哪条。改成按 `(attempt, id)` 显式取最大，同数据同结果。

### 3. 知识点统计：整行载入 → 聚合下推（`8755e4f`）

- **问题**：把符合条件的所有知识点**整行取回**，再在 Python 里按 grade/subject/status 分组计数。
  生产 1800 行、每行几十列，取回后 99% 的字段被丢弃。
- **改法**：权限过滤下推到 SQL（非管理员强制 `status == "published"`），
  统计走 `group_by(grade_id, subject_id, status)`，只回三列 + 计数。

### 4. 批量采纳批改：4N → 固定 9（`08f483d`）

- **问题**：循环里对每个 submission 各查 4 次（submission / task / answers / question type），
  N=8 就是 33 条 SQL。
- **改法**：按依赖顺序**批量预取成字典**，循环内纯内存访问。四次 `IN` 查询 + 若干固定查询，取 9 条。
- **注意**：这是「批量预取」而非「JOIN 大宽表」——后者会把 answers 的数量乘到 submission 上，
  反而放大传输量。

### 5. 附件下载计数：读-改-写 → 原子自增（`c87391d`）

- **问题**：`att.download_count += 1` 是读-改-写三步，并发下互相覆盖，计数偏少。
- **改法**：交给数据库端自增。

```python
def _bump_download_count(db: Session, att_id: int) -> None:
    """下载计数原子自增。"""
    db.execute(
        update(Attachment)
        .where(Attachment.id == att_id)
        .values(download_count=Attachment.download_count + 1)
    )
    db.commit()
```

- `preview` 与 `download` 两个入口都改为调用它，行为统一。

---

## 三、验证方法：双向反向验证

这一轮最大的收获不是性能数字，而是**「断言有没有判别力」**。每个修复都做了双向验证：

- **退回旧实现 → 复杂度断言必须变红**（证明断言真的能发现回归）
- **注入语义 bug → 等价性断言必须变红**（证明断言真的在比对结果）

过程中连续踩到 7 类「断言假绿/假红」，全部记在下面，供后续写测试时避坑：

| # | 现象 | 根因 | 修法 |
|---|---|---|---|
| 1 | 注入 bug 后测试**全绿** | `source` 只造了 `ai_gen` 一个值，`LIKE 'ai%'` 与 `== 'ai_gen'` 无法区分 | 改成 `ai / ai_import / manual / manual` 循环 |
| 2 | 新实现自己**被判违规** | 「整行载入」判据 `>= 3` 个 `table.` 引用，撞上 3 维 GROUP BY | 阈值提到 `>= 8`（接近表总列数） |
| 3 | 新旧结果差 12 倍 | oracle 漏抄它调用的 `_forced_grade`，学生被强制收敛到本年级 | oracle 必须**逐字复制，含辅助函数** |
| 4 | 测试栈溢出 | `sed` 把 `_forced_grade_ref` 内部调用也替换成自己 → 递归 | 手工改回 |
| 5 | `A < B` 断言无判别力 | 退回旧实现时 A、B 同源一起变大，比值不变 | 改**绝对上界** `新 <= 10 and 旧 >= 32` |
| 6 | SET 子句断言**假红** | SQLite 把常量 1 参数化成 `+ ?`，字面找不到 `download_count + 1` | 改判「SET 子句里出现自身列引用」 |
| 7 | `IntegrityError: FOREIGN KEY` | `Answer.paper_item_id` 有 FK，直接写 1 | 先造 `PaperItem` 再引用 |

> 第 5 条最值得警惕：**只要断言的两侧来自同一份代码，回退时它们会一起漂移**，
> 比值永远不变 —— 这类断言写多少条都是废的。

---

## 四、明确不做的优化

**SQLite PRAGMA 调优（`mmap_size` / `cache_size` / `synchronous`）—— 经 A/B 实测后拒绝。**

| 配置 | 只读耗时 | 并发写耗时 |
|---|---|---|
| 默认 | 0.56 ms | 1.31 ms |
| 调优 A | 0.50 ms | 1.65 ms |
| 调优 B | 0.71 ms | 1.21 ms |

全部落在噪声区间内，并发写还有一组**变慢**。本项目瓶颈不在页缓存，
加这些 PRAGMA 只是增加「看起来优化过了」的错觉，故不加。

---

## 五、回归与发布

| 环节 | 结果 |
|---|---|
| 全量 e2e | **863 项 / 通过 849 / 失败 0 / 环境跳过 14** |
| 静态门禁 | 五道全过（`lint_gate` / 三个 check 脚本 / `check_model_fk`） |
| CI（`f983deb`） | 全 job success：前端构建 / 后端检查 / 210 项 e2e / 镜像构建 / 发布三步 |
| 四层一致性 | `verify_consistency.py --host` → **11 通过 / 0 不一致** |
| 生产抽验 | `/health`、`/auth/login`、`/question/questions/stats`、`/edu/knowledge/stats`、`/task/my/tasks`、`/system/users`、`/logs/operation`、`/report/student/overview` 全 200 |

### 发布中踩到的一个误报

首轮四层校验报 `sha256 不一致 ['app/api/v1/grading.py', 'VERSION']`，但四层 commit 完全一致。
**commit 一致而文件不同**这个组合说明：参与比对的容器不是镜像本身。

根因：`_ctr_hashes()` 取的是**本机同名容器**，而本机容器还停在 `2.1.7`（跑了 20 小时），
`.env` 里 `IMAGE_TAG` 更是更早的 `2.0.6` —— 三重版本各自飘移。

处理：`.env` 的 `IMAGE_TAG` 对齐 `VERSION` → 重建本地容器 → 重跑得 `11/11`。
归类为**本地开发容器的滞后**，与发布漂移无关；但报错文案容易被误读，已在
`docs/RELEASE_CONSISTENCY.md` 记下语义说明。

---

## 六、遗留候选（本轮未做）

- 登录验证码「仅在客户端主动提交时校验」（`auth.py:163`，`register` 同一模式）
- 每次请求 `has_perm` 触发 `role.permissions`（selectin）的开销
- `paper_version_service` 的 JSON 快照体积
- 前端 JWT 存 localStorage 的 XSS 面
- `defusedxml` 加固
