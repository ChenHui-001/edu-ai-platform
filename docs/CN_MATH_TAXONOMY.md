# cn-math-taxonomy 集成说明

## 来源与许可

- 上游仓库：<https://github.com/xiaoyang111222/cn-math-taxonomy>
- 数据许可：CC BY-NC 4.0（署名—非商业性使用）
- 上游 README 明确商业使用需单独授权。`package.json` 中的 ISC 声明与
  LICENSE 不一致，集成时以 LICENSE / README 的 CC BY-NC 为准。

本平台只提供**导入能力**，不把完整外部数据硬编码进业务代码。是否将数据
用于商业部署，由部署方在上线前确认授权。

## 数据映射

| 外部字段 | 本地字段 |
| --- | --- |
| `topics.json.id` | `KnowledgePoint.external_id` |
| `topics.json.name` | `KnowledgePoint.name` |
| `topics.json.chapter` | 单元 / 章节节点 |
| `topics.json.grade` | `Grade.grade_num` |
| `topics.json.subject` / ID 前缀 | `Subject.name` |
| `dependencies.json` | `KnowledgePrerequisite` |
| `questions.json.id` | `Question.external_id` |

先修关系**不写入** `KnowledgePoint.parent_id`：后者是教材包含树，
前者是学习依赖图。两者混用会破坏知识点树并产生错误的诊断路径。

题型映射：`numeric → blank`、`choice → single`、`short/self → short`。
难度映射：`basic → easy`、`standard/medium → medium`、
`challenge/advanced → hard`。

## 导入命令

先做 dry-run 核对数量与错误：

```powershell
python tools/import_math_taxonomy.py --source-dir C:\path\to\cn-math-taxonomy --dry-run
```

确认后正式导入：

```powershell
python tools/import_math_taxonomy.py --source-dir C:\path\to\cn-math-taxonomy
```

默认只导入数学 1–9 年级；题目作为**私有、已发布**题导入，避免未经教师
审核直接进入公共题库。可用 `--bank-type public` 与 `--status draft`
显式调整。重复导入按 `(external_source, external_id)` 与题干指纹幂等。

## 诊断边界

- 诊断结果只展示薄弱根因、先修路径和会话统计；
- 不直接写 `KnowledgeMastery`，正式掌握度仍由作业、练习和判分累计；
- 导入题目保留 `extra_json`（`accept` / `verify` / `figure` /
  `unordered` / `topicId` 等），用于服务端判分与图谱追溯。

## 平台内使用

- 学生端：`学习中心 → 测 → 知识诊断`（`/student/diagnosis`）。
  选择学科与目标知识点后可做「目标诊断」或「范围筛查」；答错会按硬先修
  优先回溯，结束后给出根因、建议顺序与章节统计。
- 教师端：`知识点管理 → 节点详情 → 先修关系`。可查看先修/后继，
  新增或删除先修边；跨年级先修需二次确认，成环与跨学科由后端拒绝。
- 诊断会话按作答历史重放，刷新页面不会丢失进度；同一会话仅本人或
  `DataScope` 内的教师/管理员可读。

## 验证

```powershell
python tools\verify_math_taxonomy_integration.py
```

脚本使用临时 SQLite，覆盖导入映射、幂等、去重、先修图完整性、诊断算法、
HTTP 权限隔离，以及真实数据规模（599 知识点 / 1067 先修边 / 2520 题 /
23 道重复题干跳过）。上游数据目录通过 `--source-dir` 或
`CN_MATH_TAXONOMY_DATA` 指定；缺失时该段自动跳过，不影响其余用例。
