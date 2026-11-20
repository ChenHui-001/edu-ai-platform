# 源码覆盖报告

- Output Language: zh-CN
- Status: in-progress

## 资产分母
- source-file: 373 registered from source-asset-inventory.md
- API operations: 339 discovered from OpenAPI
- model classes: 63 unique entity definitions discovered from SQLAlchemy model classes
- physical tables: 63 discovered from Base.metadata
- jobs: 8 handlers + 8 default jobs
- frontend views: 56 vue pages
- backend python files: 137

## 覆盖矩阵
| Asset Type | Discovered | Modeled | Excluded | Unassigned | Coverage | Notes |
|---|---:|---:|---:|---:|---:|---|
| source-file | 373 | 373 | 0 | 0 | 100% | 已登记路径，业务归属待细化 |
| API operation | 339 | 339 | 0 | 0 | 100% | 已建 API operation，功能归属通过路径分组覆盖 |
| model class | 63 | 63 | 0 | 0 | 100% | entity 台账已建，283 个 FUNC 已映射核心对象 |
| physical table | 63 | 63 | 0 | 0 | 100% | 字段表已建，59/63 已映射消费者 |
| job | 8 | 8 | 0 | 0 | 100% | 已列 handler，功能归属待补 |
| frontend view | 56 | 56 | 0 | 0 | 100% | 已列页面，326 条前端接口调用已映射 |
| config key | 68 | 68 | 0 | 0 | 100% | 已建 CFG-*，消费者待补 |
| component capability | 19 | 19 | 0 | 0 | 100% | 已建 COMP-*，消费者待补 |
| common capability | 9 | 9 | 0 | 0 | 100% | 已建 COMMON-*，消费者待补 |
| business function | 290 | 290 | 0 | 0 | 100% | 按 API 路径与业务域全量拆分，283 个 FUNC 已映射核心/依赖表 |

## 未归属资产
- none registered as unassigned.
- Current limitation: consumer/detail mapping remains incomplete.

## 新增矩阵`n- interface-consumer-matrix.md: 339 条接口与 FUNC 对应。`n- frontend-page-api-matrix.md: 94 个前端源码文件、326 条接口调用。`n`n## 新增矩阵`n- object-consumer-matrix.md: 63 个对象与 59 个物理表已映射消费者。`n`n## 功能逆向状态`n- 290 个 FUNC 的详细逆向状态已补齐。`n`n## 功能闭包`n- 290 个 FUNC 的闭包状态、断链、下一步检索与证据已补齐。`n`n## 功能规则与状态`n- 290 个 FUNC 的规则、状态、权限已补齐。`n`n## 功能依赖`n- 290 个 FUNC 的 TCAP/CAPI 已补齐。`n`n## 无菜单功能`n- 41 个 non-interactive/hybrid FUNC 已补入无菜单索引。`n`n## 功能清单模块`n- 290 个 FUNC 的模块/服务已补齐。`n`n## 功能清单业务域`n- 290 个 FUNC 的业务域/场景/能力已补齐。`n`n## 功能清单类型`n- 290 个 FUNC 的类型已补齐。`n`n## 功能清单触发类型`n- 290 个 FUNC 的触发类型已补齐。`n`n## 功能清单优先级`n- 290 个 FUNC 的优先级已补齐。`n`n## 需求面板非功能`n- 290 个 FUNC 的 Non-Functional Clauses 已补齐。`n`n## 需求面板菜单依据`n- 290 个 FUNC 的 Menu Rationale 已补齐。`n`n## 功能清单边界`n- 290 个 FUNC 的独立业务结果与功能边界已补齐。`n`n## 需求面板证据`n- 290 个 FUNC 的 Requirement Evidence 已补齐。`n`n## 需求面板实现链`n- 290 个 FUNC 的 Implementation Chain 链接已补齐。`n`n## 需求面板域/能力/场景`n- 290 个 FUNC 的 Domain/Capability/Scenario 已补齐。`n`n## 需求面板交互`n- 290 个 FUNC 的 Interaction 已补齐。`n`n## 需求面板类型`n- 290 个 FUNC 的 Function Type 已补齐。`n`n## 需求面板权限`n- 290 个 FUNC 的 Permission And Data Scope 已补齐。`n`n## 需求面板前置与输入`n- 290 个 FUNC 的 Preconditions 与 Inputs 已补齐。`n`n## 需求面板对象`n- 290 个 FUNC 的 Core Objects 已补齐。`n`n## 需求面板结果`n- 290 个 FUNC 的 Outputs、Failure、Manual Intervention 已补齐。`n`n## 需求面板规则与状态`n- 290 个 FUNC 的 Business Rules 与 State Changes 已补齐。`n`n## 需求面板步骤`n- 290 个 FUNC 的 Main Steps 已补齐。`n`n## 需求面板参与者`n- 290 个 FUNC 的 Actors 已补齐。`n`n## 需求面板目标`n- 290 个 FUNC 的 Business Goal 已补齐。`n`n## 业务域与能力`n- 290 个 FUNC 已补齐业务域、能力、交互方式与触发类型。`n`n## 业务规则与状态`n- 290 个 FUNC 已补齐业务规则与状态迁移骨架。`n`n## 业务目标与结果`n- 290 个 FUNC 已补齐业务目标与业务结果。`n`n## 功能对象映射`n- 283 个 FUNC 已补齐核心对象。`n`n## 功能表映射`n- 283 个 FUNC 已补齐核心 CUD 表与依赖查询表。`n`n## 下一步
- Backfill consumer functions to API/OBJ/TBL/COMP/CAPI.
- Re-run coverage after detail mapping.


































