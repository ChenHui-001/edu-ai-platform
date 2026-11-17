# 2026-11-17 修复与集成记录

## 本轮目标

按 cn-math-taxonomy「推荐集成方案」完成六步落地，并做功能测试：

1. 数据模型与迁移
2. 外部图谱导入
3. 诊断算法与 API
4. 学生端诊断页面
5. 教师端先修关系管理
6. 集成验证

## 实现内容

### 数据模型

- `KnowledgePoint` 增加 `external_source` / `external_id` 与唯一约束；
- `Question` 增加 `external_source` / `external_id` / `extra_json` 与唯一约束；
- 新增 `KnowledgePrerequisite`（hard/soft、reason、source、自环与唯一约束）；
- 新增 `TaxonomyDiagnosisSession`（目标、模式、题量、确认数、作答、seed）。
- Alembic 新增 `0002_math_taxonomy`，升级/降级/再升级均通过。

### 导入器

- `backend/app/services/math_taxonomy_import.py` + `tools/import_math_taxonomy.py`；
- 教材单元/章节与知识依赖图分离，外部 `parent_id` 不当作先修；
- 题型 `numeric/choice/short/self`、难度 `basic/standard/challenge` 映射；
- 外部 ID 与题干指纹双重去重；拒绝自环、跨学科、成环先修边；
- 默认数学 1–9 年级、题目私有已发布，许可识别为 CC BY-NC 4.0。

### 诊断

- `backend/app/services/knowledge_diagnosis.py`：
  建图、祖先集合、拓扑排序、目标/筛查模式、hard 先修优先、连续答对确认、
  答错回溯、根因、学习路径、章节汇总、按作答历史重放；
- `backend/app/api/v1/knowledge_diagnosis.py`：
  目标列表、会话创建/详情/下一题/作答/结果、先修与后继读写；
- 学生仅能访问本人会话；教师/管理员受 `DataScope` 限制；
  跨年级先修需 `allow_cross_grade=true`，成环返回 400。
- 诊断结果**不写** `KnowledgeMastery`。

### 前端

- 新增 `KnowledgeDiagnosis.vue`，接入学习中心「测」分组；
- 支持学科/目标选择、两种模式、逐题作答、单选/填空/简答自评、
  实时画像、根因、章节排查、建议路径与结果页；
- 学习路径、掌握图谱页增加「知识诊断」入口；
- 知识点管理新增先修关系面板与新增先修弹窗（跨年级确认、错误文案展示）。

## 验证结果

- `python tools/verify_math_taxonomy_integration.py`：**64 项全部通过**
  - 真实数据：599 知识点 / 1067 先修边 / 2520 题 / 23 道重复题干跳过；
  - 二次导入 0 新增；
  - API：学生隔离、教师范围、成环、跨年级确认、学生只读均符合预期。
- `npm run lint` / `test`（129 项）/ `build` / `check:bundle` 全部通过。
- 后端门禁：hardcoded_host / weak_assertion / time_contract / model_fk /
  lint_gate / alembic_sync / migration_columns 全部通过。
- Alembic 临时库：`upgrade head → downgrade 0001_baseline → upgrade head` 通过。

## 发布

- 版本：`2.5.40 → 2.5.42`（2.5.41 为中间构建，2.5.42 为最终发布）；
- 镜像：`ghcr.io/chenhui-001/edu-ai-platform:2.5.42`（CI 构建）；
- 镜像 digest：`sha256:957d8c05…`；Docker Hub `2.5.42` / `latest` 同 digest；
- 清理：本机与生产仅保留 2.5.42；Docker Hub 按保留策略删除 55 个旧标签；
- 四位一体（本地 HEAD / origin/master / 镜像 / 生产容器）校验结果
  见 `docs/RELEASE_CONSISTENCY.md`。

## 边界说明

- 未迁移存量业务数据；本次以功能闭环为主；
- 上游数据许可为 CC BY-NC 4.0，商业部署需另行确认授权；
- 外部完整数据不进入仓库，仅保留导入器与文档。
