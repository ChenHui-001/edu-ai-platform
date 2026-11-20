"""流程引擎的共享常量。

**为什么单独成文件**：flow_engine 与 flow_escalation 都需要这些常量。
若 flow_escalation 从 flow_engine 导入，而 flow_engine 又要继承
flow_escalation 的 mixin —— 循环导入，谁都导不全（Python 报
partially initialized module）。

把常量抽到独立模块后，依赖方向变成单向：
    flow_constants <- flow_engine
    flow_constants <- flow_escalation
两边互不依赖，循环消失。
"""

# 实例状态
INSTANCE_RUNNING = "RUNNING"
INSTANCE_APPROVED = "APPROVED"
INSTANCE_REJECTED = "REJECTED"
INSTANCE_RETURNED = "RETURNED"
INSTANCE_CANCELLED = "CANCELLED"

TERMINAL_INSTANCE_STATUS = frozenset({
    INSTANCE_APPROVED, INSTANCE_REJECTED, INSTANCE_CANCELLED,
})

# 待办任务状态
TASK_TODO = "TODO"
TASK_CLAIMED = "CLAIMED"
TASK_DONE = "DONE"
TASK_CANCEL = "CANCEL"

# 活动类型
ACT_START = "START"
ACT_END = "END"
ACT_GATEWAY = "GATEWAY"
ACT_USER_TASK = "USER_TASK"
ACT_APPROVAL_TASK = "APPROVAL_TASK"
ACT_BEHAVIOR_CALL = "BEHAVIOR_CALL"
ACT_SYSTEM_TASK = "SYSTEM_TASK"
ACT_SUB_FLOW_CALL = "SUB_FLOW_CALL"

# 需要生成待办任务的活动类型（人工介入点）
HUMAN_ACTIVITY_TYPES = frozenset({ACT_USER_TASK, ACT_APPROVAL_TASK})

# 业务对象类型 -> 中文标签。前端展示用：只在前端硬编码会让后端新增
# 业务类型时前端必须跟着改，否则显示原始英文标识。
BIZ_LABELS = {
    "paper": "试卷",
    "question": "题目",
    "registration": "用户注册",
    "task": "教学任务",
}

# 催办频次限制：同一待办两次催办之间的最小间隔（分钟）。
# 没有限制时，管理员可以在待办页连点几十次催办，把学生的通知列表刷爆——
# 这类「功能可用但会伤害用户」的行为比没有功能更糟。
URGE_COOLDOWN_MINUTES = 30

# 本体角色 id <-> 数据库 role code 的翻译表（本体侧用稳定 id，
# 运行时侧用 sys_role.code，两者是不同命名空间，不能直接比）。
ROLE_ID_TO_CODE = {
    "ROLE-SYS-ADMIN": "sys_admin",
    "ROLE-GRADE-ADMIN": "grade_admin",
    "ROLE-TEACHER": "teacher",
    "ROLE-STUDENT": "student",
    "ROLE-GUEST": "guest",
}

# 反向映射：code -> 本体 id。给「查这个角色能办哪些待办」用。
ROLE_CODE_TO_ID = {code: rid for rid, code in ROLE_ID_TO_CODE.items()}
