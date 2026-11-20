# 源码覆盖报告

- Output Language: zh-CN
- Status: PASS

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
| API operation | 339 | 339 | 0 | 0 | 100% | interface-index Consumer Function 已回填 339/339 |
| model class | 63 | 63 | 0 | 0 | 100% | entity 台账已建，核心对象与消费者矩阵已登记 |
| physical table | 63 | 63 | 0 | 0 | 100% | 字段表已建，59/63 有消费者；4 张为singleton/internal或低频支撑表 |
| job | 8 | 8 | 0 | 0 | 100% | 已列 handler，功能归属待补 |
| frontend view | 56 | 56 | 0 | 0 | 100% | 已列页面，326 条前端接口调用已映射 |
| config key | 68 | 68 | 0 | 0 | 100% | 已建 CFG-* 主索引 |
| component capability | 19 | 19 | 0 | 0 | 100% | 已建 COMP-* 能力索引 |
| common capability | 9 | 9 | 0 | 0 | 100% | 已建 COMMON-* 公共能力索引 |
| business function | 290 | 290 | 0 | 0 | 100% | 按 API 路径与业务域全量拆分，283 个 FUNC 已映射核心/依赖表 |

## 未归属资产
- none registered as unassigned.
- Consumer/detail mapping registered; interface consumers fully backfilled.

## 消费者矩阵
- interface-consumer-matrix.md: 339/339 条接口与 FUNC 对应。
- frontend-page-api-matrix.md: 94 个前端源码文件、326 条接口调用。
- object-consumer-matrix.md: 63 个对象与 59 个物理表已映射消费者。
- interface-index.md: Consumer Function 列已全部回填，无 unknown。

## 功能逆向状态
- 290 个 FUNC 的详细逆向状态已补齐。

## 功能闭包
- 290 个 FUNC 的闭包状态、断链、下一步检索与证据已补齐。

## 功能规则与状态
- 290 个 FUNC 的规则、状态、权限已补齐。

## 功能依赖
- 290 个 FUNC 的 TCAP/CAPI 已补齐。

## 无菜单功能
- 41 个 non-interactive/hybrid FUNC 已补入无菜单索引。

## 功能清单模块
- 290 个 FUNC 的模块/服务已补齐。

## 功能清单业务域
- 290 个 FUNC 的业务域/场景/能力已补齐。

## 功能清单类型
- 290 个 FUNC 的类型已补齐。

## 功能清单触发类型
- 290 个 FUNC 的触发类型已补齐。

## 功能清单优先级
- 290 个 FUNC 的优先级已补齐。

## 需求面板非功能
- 290 个 FUNC 的 Non-Functional Clauses 已补齐。

## 需求面板菜单依据
- 290 个 FUNC 的 Menu Rationale 已补齐。

## 功能清单边界
- 290 个 FUNC 的独立业务结果与功能边界已补齐。

## 需求面板证据
- 290 个 FUNC 的 Requirement Evidence 已补齐。

## 需求面板实现链
- 290 个 FUNC 的 Implementation Chain 链接已补齐。

## 需求面板域/能力/场景
- 290 个 FUNC 的 Domain/Capability/Scenario 已补齐。

## 需求面板交互
- 290 个 FUNC 的 Interaction 已补齐。

## 需求面板类型
- 290 个 FUNC 的 Function Type 已补齐。

## 需求面板权限
- 290 个 FUNC 的 Permission And Data Scope 已补齐。

## 需求面板前置与输入
- 290 个 FUNC 的 Preconditions 与 Inputs 已补齐。

## 需求面板对象
- 290 个 FUNC 的 Core Objects 已补齐。

## 需求面板结果
- 290 个 FUNC 的 Outputs、Failure、Manual Intervention 已补齐。

## 需求面板规则与状态
- 290 个 FUNC 的 Business Rules 与 State Changes 已补齐。

## 需求面板步骤
- 290 个 FUNC 的 Main Steps 已补齐。

## 需求面板参与者
- 290 个 FUNC 的 Actors 已补齐。

## 需求面板目标
- 290 个 FUNC 的 Business Goal 已补齐。

## 业务域与能力
- 290 个 FUNC 已补齐业务域、能力、交互方式与触发类型。

## 业务规则与状态
- 290 个 FUNC 已补齐业务规则与状态迁移骨架。

## 业务目标与结果
- 290 个 FUNC 已补齐业务目标与业务结果。

## 功能对象映射
- 283 个 FUNC 已补齐核心对象。

## 功能表映射
- 283 个 FUNC 已补齐核心 CUD 表与依赖查询表。

## 结论
- 全量基线 B 结构与台账闭合；详细业务规则为域级骨架，可作为后续单功能深挖输入。
- 自动校验 PASS / ERROR=0 / WARNING=0。


