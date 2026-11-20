# Flow Index

- Output Language: zh-CN
- Status: in-progress

## 流程定义
- 流程定义表已定义于 database-model.md。

## 流程实例与任务
- 所有实例/任务/转办/历史表已定义于 database-model.md。

## API Actions
- API-flow-todo: /flow/todo
- API-flow-done: /flow/done
- API-flow-instances: /flow/instances
- API-flow-instance-detail: /flow/instances/{instance_id}
- API-flow-claim: /flow/tasks/{task_id}/claim
- API-flow-approve: /flow/tasks/{task_id}/approve
- API-flow-reject: /flow/tasks/{task_id}/reject
- API-flow-return: /flow/tasks/{task_id}/return
- API-flow-cancel: /flow/tasks/{task_id}/cancel
- API-flow-sync: /flow/definitions/sync
- API-flow-overdue: /flow/overdue
- API-flow-transfer-candidates: /flow/tasks/{task_id}/transfer-candidates
- API-flow-transfer: /flow/tasks/{task_id}/transfer
- API-flow-urge: /flow/tasks/{task_id}/urge
- API-flow-deadline: /flow/tasks/{task_id}/deadline

## 状态
- documented with table and API evidence, business rule mapping pending


