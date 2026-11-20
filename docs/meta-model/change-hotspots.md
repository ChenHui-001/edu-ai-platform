# Change Hotspots

- Output Language: zh-CN
- Status: in-progress

## 当前未提交变更
- backend/app/api/v1/flow.py, task_urge.py
- backend/app/models/flow.py
- backend/app/services/flow_engine.py, flow_escalation.py, flow_orchestration.py, rule_engine.py, flow_constants.py, task_urge.py
- backend/app/schemas/flow.py
- backend/app/ontology/m3-rule-model.yaml, m6-flow-model.yaml
- backend/migrations/versions/0005_flow_engine.py, 0006_flow_transfer_urge.py
- frontend/src/views/admin/FlowTodo.vue, components/ExamUrgeDialog.vue, utils/flowTodo.js
- tools/check_ontology_consistency.py, verify_flow_engine.py
- backend/qa_flow_engine_suite.py, qa_flow_urge_suite.py

## 版本
- VERSION 2.5.49, uncommitted flow engine and urge changes.

## 影响
- 流程待办、审批、转办、催办为当前最大变更热点。
- 任务催交与流程催办共用通知能力但业务域不同。
- Ontology YAML 与后端模型/API 之间存在一致性校验需求。
