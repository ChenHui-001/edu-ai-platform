# -*- coding: utf-8 -*-
"""
功能测试规范化用例集（单一来源）

覆盖：管理员 / 教师 / 学生 三角色全部菜单及其内部按钮、输入框、对话框、表格操作。
每个用例为 AAA 结构（前置条件 / 操作步骤 / 预期结果），并带 automation 字段可直接驱动接口自动化。

用法：
    python functional_cases.py --emit          # 生成 FUNCTIONAL_TEST_CASES.json + .csv
    python functional_cases.py --run           # 连 BASE_URL 执行 api 类用例，输出结果 JSON
    python functional_cases.py --coverage      # 打印 菜单×用例数 覆盖矩阵
"""
import argparse
import csv
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------- 用例构造器
def C(role, module, menu, element, action, priority, precond, steps, expected,
      api, method=None, path=None, body=None, assert_=None, locator=None):
    return {
        "id": None,  # 由 emit 统一编号
        "role": role,
        "module": module,
        "menu": menu,
        "element": element,
        "action": action,
        "priority": priority,
        "precondition": precond,
        "steps": steps if isinstance(steps, list) else [steps],
        "expected": expected,
        "api": api,
        "automation": {
            "type": "api" if method else ("ui" if locator else "manual"),
            "method": method,
            "path": path,
            "body": body,
            "assert": assert_,
            "locator": locator,
        },
    }


CASES = []

# ============================================================== 管理员 (admin / grade_admin)
# ---- 工作台 Dashboard
CASES += [
    C("admin", "系统基础", "工作台", "工作台页面", "访问渲染", "P0",
      "已登录 sys_admin 账号",
      ["1. 访问 /dashboard", "2. 等待页面加载"],
      "展示统计卡片与快捷入口，无 JS 报错，左侧菜单含全部管理员菜单",
      "GET /dashboard", locator=".dashboard"),
]

# ---- 用户管理
CASES += [
    C("admin", "系统基础/用户管理", "用户管理", "页面访问", "访问渲染", "P0",
      "sys_admin 登录", ["1. 点击菜单『用户管理』"], "表格加载用户列表，列含用户名/姓名/身份/状态",
      "GET /system/users", locator="text=用户管理"),
    C("admin", "系统基础/用户管理", "用户管理", "筛选(关键词/身份/状态/年级)+查询", "筛选", "P1",
      "用户列表已有数据", ["1. 填关键词/选身份/状态/年级", "2. 点『查询』"],
      "列表仅返回符合条件记录，分页总数更新",
      "GET /system/users?keyword=&identity=&status=&grade_id=", method="GET",
      path="/system/users", assert_="resp.data.list 长度随筛选变化"),
    C("admin", "系统基础/用户管理", "用户管理", "重置筛选", "点击", "P2",
      "已设置筛选条件", ["1. 点『重置』"], "所有筛选条件清空，恢复全量列表",
      "GET /system/users", locator="text=重置"),
    C("admin", "系统基础/用户管理", "用户管理", "新增用户", "打开对话框并保存", "P0",
      "sys_admin 登录", ["1. 点『新增用户』", "2. 填用户名/姓名/初始密码(≥8含字母数字)/身份", "3. 点『保存』"],
      "提示成功，列表新增该用户；密码经 PBKDF2 哈希落库",
      "POST /system/users", method="POST", path="/system/users",
      body={"username": "t1", "real_name": "测试", "password": "Test@1234", "identity": "teacher", "role_codes": ["teacher"]},
      assert_="status==200 且返回 id"),
    C("admin", "系统基础/用户管理", "用户管理", "新增用户-校验", "负向校验", "P1",
      "sys_admin 登录，打开新增对话框", ["1. 用户名留空或密码<8位纯数字", "2. 点保存"],
      "前端拦截并提示必填/格式错误，不发请求",
      "POST /system/users", method="POST", path="/system/users",
      body={"username": "", "password": "123"}, assert_="前端校验失败，HTTP 未发出或 422"),
    C("admin", "系统基础/用户管理", "用户管理", "编辑用户", "打开对话框并保存", "P1",
      "存在目标用户", ["1. 行内『编辑』", "2. 改姓名/状态/角色", "3. 保存"],
      "提示成功，列表对应行更新",
      "PUT /system/users/{id}", method="PUT", path="/system/users/{id}", body={"real_name": "x"}, assert_="200"),
    C("admin", "系统基础/用户管理", "用户管理", "重置密码", "对话框操作", "P1",
      "存在目标用户", ["1. 行内『重置密码』", "2. 填新密码或留空(自动生成)", "3. 确认重置"],
      "该用户下次登录须用新密码；留空时系统生成强密码并提示",
      "POST /system/users/reset-password", method="POST", path="/system/users/reset-password",
      body={"user_id": 1, "new_password": "New@1234"}, assert_="200"),
    C("admin", "系统基础/用户管理", "用户管理", "启用/禁用", "行内开关", "P1",
      "存在目标用户", ["1. 切换状态开关"], "状态变更即时生效，禁用后该账号无法登录",
      "PUT /system/users/{id}", method="PUT", path="/system/users/{id}", body={"status": "disabled"}, assert_="200"),
    C("admin", "系统基础/用户管理", "用户管理", "删除用户", "二次确认", "P1",
      "存在可删用户", ["1. 行内『删除』", "2. 确认框点确认"],
      "提示成功，用户从列表移除；内置 admin 不可删",
      "DELETE /system/users/{id}", method="DELETE", path="/system/users/{id}", assert_="200"),
    C("admin", "系统基础/用户管理", "用户管理", "分页", "翻页", "P2",
      "用户数>10", ["1. 改每页条数/翻页"], "列表与分页总数正确联动",
      "GET /system/users?page=&page_size=", locator=".el-pagination"),
]

# ---- 角色权限
CASES += [
    C("admin", "系统基础/角色权限", "角色权限", "页面访问", "访问渲染", "P0",
      "sys_admin 登录", ["1. 点『角色权限』"], "展示角色列表与权限树",
      "GET /system/roles", locator="text=角色权限"),
    C("admin", "系统基础/角色权限", "角色权限", "新增角色", "对话框保存", "P1",
      "sys_admin 登录", ["1. 点『新增角色』", "2. 填名称/标识/描述", "3. 保存"],
      "新角色出现在列表", "POST /system/roles", method="POST", path="/system/roles",
      body={"name": "班主任", "code": "head_teacher", "description": "x"}, assert_="200"),
    C("admin", "系统基础/角色权限", "角色权限", "复制角色", "prompt 新名", "P2",
      "存在角色", ["1. 点『复制角色』", "2. 输入新名称确认"], "生成同名权限副本的新角色",
      "POST /system/roles/copy", method="POST", path="/system/roles/copy", body={"id": 1, "name": "副本"}, assert_="200"),
    C("admin", "系统基础/角色权限", "角色权限", "编辑/删除", "对话框", "P1",
      "存在自定义角色", ["1. 编辑改名保存", "2. 删除并确认"], "编辑生效；删除后列表移除；内置角色不可操作",
      "PUT /system/roles/{id}", method="PUT", path="/system/roles/{id}", assert_="200"),
    C("admin", "系统基础/角色权限", "角色权限", "权限树勾选+保存", "勾选并保存", "P0",
      "已选中某角色", ["1. 勾选/取消权限节点", "2. 点『保存权限』"],
      "该角色的 permissions 更新；RBAC 菜单/操作级生效",
      "PUT /system/roles/{id}", method="PUT", path="/system/roles/{id}",
      body={"permissions": ["question:bank:list"]}, assert_="200"),
    C("admin", "系统基础/角色权限", "角色权限", "清空/展开/折叠", "树操作", "P2",
      "权限树已加载", ["1. 点『清空』", "2. 点『展开全部/折叠全部』"],
      "清空后无勾选；展开/折叠改变树展示", "—", locator=".el-tree"),
]

# ---- 注册审批
CASES += [
    C("admin", "系统基础/注册审批", "注册审批", "页面访问", "渲染", "P0",
      "sys_admin 登录", ["1. 点『注册审批』"], "默认展示『待审批』列表",
      "GET /auth/registrations?status=pending", locator="text=注册审批"),
    C("admin", "系统基础/注册审批", "注册审批", "筛选/搜索", "筛选", "P1",
      "存在多状态申请", ["1. 选状态/输关键词", "2. 查询"], "列表按条件过滤",
      "GET /auth/registrations", method="GET", path="/auth/registrations", assert_="list 已过滤"),
    C("admin", "系统基础/注册审批", "注册审批", "通过", "行内操作", "P0",
      "存在待审批申请", ["1. 行内『通过』"], "该申请状态变已通过，对应账号激活可登录",
      "POST /auth/registrations/audit", method="POST", path="/auth/registrations/audit",
      body={"registration_id": 1, "approved": True}, assert_="200"),
    C("admin", "系统基础/注册审批", "注册审批", "拒绝", "prompt 理由", "P0",
      "存在待审批申请", ["1. 行内『拒绝』", "2. 填理由(≥2字)确认"],
      "状态变已拒绝；理由入库；理由为空时报错",
      "POST /auth/registrations/audit", method="POST", path="/auth/registrations/audit",
      body={"registration_id": 1, "approved": False, "reason": "资料不实"}, assert_="200"),
    C("admin", "系统基础/注册审批", "注册审批", "详情", "对话框", "P2",
      "存在申请", ["1. 点『详情』"], "弹窗展示申请只读信息", "GET /auth/registrations/{id}", locator="text=详情"),
]

# ---- 年级管理
CASES += [
    C("admin", "教学资源/年级", "年级管理", "页面访问", "渲染", "P0",
      "有 resource:grade:list 权限", ["1. 点『年级管理』"], "年级表格加载，含学段/序号/状态",
      "GET /edu/grades", locator="text=年级管理"),
    C("admin", "系统基础/年级管理", "年级管理", "新增年级", "对话框", "P1",
      "有写权限", ["1. 点『新增年级』", "2. 选学段/序号", "3. 保存"],
      "新年级入库（名称自动生成，唯一键 grade 序号）",
      "POST /edu/grades", method="POST", path="/edu/grades", body={"stage": "primary", "grade_no": 3}, assert_="200"),
    C("admin", "系统基础/年级管理", "年级管理", "编辑/删除", "对话框", "P1",
      "存在年级", ["1. 编辑改状态保存", "2. 删除确认"], "编辑生效；删除级联处理班级前需无引用",
      "PUT /edu/grades/{id}", method="PUT", path="/edu/grades/{id}", assert_="200"),
    C("admin", "系统基础/年级管理", "年级管理", "筛选/分页", "筛选", "P2",
      "年级多", ["1. 选学段/关键词查询"], "列表过滤正确", "GET /edu/grades", method="GET", path="/edu/grades"),
]

# ---- 学科管理（同文件 ResourceManage）
CASES += [
    C("admin", "教学资源/学科", "学科管理", "页面访问", "渲染", "P0",
      "有 resource:subject:list 权限", ["1. 点『学科管理』"], "默认按年级视图或平铺，展示学科列表",
      "GET /edu/subjects", locator="text=学科管理"),
    C("admin", "教学资源/学科", "学科管理", "视图切换", "单选", "P2",
      "学科页", ["1. 切『按年级查看/平铺列表』"], "两种视图正确渲染", "—", locator=".el-radio"),
    C("admin", "教学资源/学科", "学科管理", "跨年级复制", "对话框", "P1",
      "存在学科", ["1. 点『跨年级复制』", "2. 选目标年级", "3. 确认"],
      "目标年级生成同名学科", "POST /edu/subjects/clone", method="POST", path="/edu/subjects/clone",
      body={"id": 1, "target_grade_ids": [2]}, assert_="200"),
    C("admin", "教学资源/学科", "学科管理", "新增学科", "对话框", "P0",
      "有写权限", ["1. 点新增", "2. 选年级/填名称(≤32)/代码/版本", "3. 保存"],
      "学科入库；唯一键(grade_id,name)；七年级无物理(dead data 已剔除)",
      "POST /edu/subjects", method="POST", path="/edu/subjects", body={"grade_id": 1, "name": "数学"}, assert_="200"),
    C("admin", "教学资源/学科", "学科管理", "编辑/删除", "对话框", "P1",
      "存在学科", ["1. 编辑保存", "2. 删除确认"], "编辑生效；删除需无关联题目/班级",
      "PUT /edu/subjects/{id}", method="PUT", path="/edu/subjects/{id}", assert_="200"),
]

# ---- 知识点管理（最重）
CASES += [
    C("admin", "教学资源/知识点", "知识点管理", "页面访问", "渲染", "P0",
      "sys_admin 登录", ["1. 点『知识点管理』"], "展示树/列表 + RAG 状态标签 + 顶部按钮",
      "GET /edu/knowledge/tree", locator="text=知识点管理"),
    C("admin", "教学资源/知识点", "知识点管理", "筛选(年级/学科/学期/状态/关键词)", "筛选", "P1",
      "有数据", ["1. 选年级→学科联动", "2. 输关键词查询"], "列表/树按条件过滤；学科随年级联动",
      "GET /edu/knowledge", method="GET", path="/edu/knowledge", assert_="list 已过滤"),
    C("admin", "教学资源/知识点", "知识点管理", "新增根节点", "对话框", "P0",
      "sys_admin", ["1. 点『新增根节点』", "2. 填年级/学科/名称(≤128)/难度", "3. 保存"],
      "根节点入库", "POST /edu/knowledge", method="POST", path="/edu/knowledge",
      body={"grade_id": 1, "subject_id": 1, "name": "数与代数"}, assert_="200"),
    C("admin", "教学资源/知识点", "知识点管理", "新增子级", "节点操作", "P1",
      "存在父节点", ["1. 节点悬停『子级』", "2. 填名称保存"], "子节点挂在父节点下，path/level 正确",
      "POST /edu/knowledge", method="POST", path="/edu/knowledge", body={"parent_id": 1, "name": "x"}, assert_="200"),
    C("admin", "教学资源/知识点", "知识点管理", "编辑详情并保存", "详情表单", "P1",
      "存在节点", ["1. 点节点→详情", "2. 改难度/说明", "3. 保存"], "节点属性更新",
      "PUT /edu/knowledge/{id}", method="PUT", path="/edu/knowledge/{id}", assert_="200"),
    C("admin", "教学资源/知识点", "知识点管理", "移动到其他年级/学科", "移动对话框", "P1",
      "sys_admin", ["1. 详情『移动』", "2. 选目标年级/学科/父节点", "3. 确认"],
      "节点归属变更；code 唯一约束(grade_id,subject_id,code)仍满足",
      "PUT /edu/knowledge/batch", method="PUT", path="/edu/knowledge/batch", body={"action": "move"}, assert_="200"),
    C("admin", "教学资源/知识点", "知识点管理", "AI 补全", "对话框", "P2",
      "LLM 可用", ["1. 详情『AI 补全』", "2. 应用选中建议"], "节点内容被补全更新（仅预览不落库，确认才写）",
      "POST /edu/knowledge/ai/enrich", method="POST", path="/edu/knowledge/ai/enrich", assert_="200"),
    C("admin", "教学资源/知识点", "知识点管理", "附件上传+可见性", "附件区", "P1",
      "存在节点", ["1. 上传附件", "2. 切『学生可见』开关", "3. 预览/下载"],
      "附件入库可预览下载；可见性开关控制学生端是否可见",
      "POST /attachments/batch-upload", method="POST", path="/attachments/batch-upload", assert_="200"),
    C("admin", "教学资源/知识点", "知识点管理", "批量发布/归档/删除", "批量栏", "P1",
      "勾选多条", ["1. 勾选→批量发布", "2. 批量删除(确认)"], "状态批量变更；删除需确认",
      "PUT /edu/knowledge/batch", method="PUT", path="/edu/knowledge/batch", body={"action": "publish"}, assert_="200"),
    C("admin", "教学资源/知识点", "知识点管理", "导入(预检→确认)", "导入对话框", "P1",
      "准备 xlsx 模板", ["1. 下载模板", "2. 上传", "3. 预检", "4. 确认导入"],
      "预检展示跳过/错误；确认后入库；编码用父 id，禁止批量套模板",
      "POST /edu/knowledge/import", method="POST", path="/edu/knowledge/import", body={"dry_run": False}, assert_="200"),
    C("admin", "教学资源/知识点", "知识点管理", "AI 生成", "对话框", "P2",
      "LLM 可用", ["1. 点『AI 生成』填年级/学科/数量(3-12)", "2. 生成预览", "3. 创建选中"],
      "生成知识点预览，确认后入库", "POST /edu/knowledge/ai/generate", method="POST", path="/edu/knowledge/ai/generate", assert_="200"),
    C("admin", "教学资源/知识点", "知识点管理", "导出", "点击", "P2",
      "有数据", ["1. 点『导出』"], "下载知识点 xlsx，带 Authorization",
      "GET /edu/knowledge/export", method="GET", path="/edu/knowledge/export", assert_="blob 200"),
    C("admin", "教学资源/知识点", "知识点管理", "重建索引", "确认框", "P2",
      "RAG 启用", ["1. 点『重建索引』确认"], "Chroma 索引重建，状态标签更新",
      "POST /edu/knowledge/reindex", method="POST", path="/edu/knowledge/reindex", assert_="200"),
    C("admin", "教学资源/知识点", "知识点管理", "语义搜索", "自然语言搜索", "P2",
      "RAG 启用", ["1. 输自然语言查询", "2. 点搜索", "3. 结果『定位』"], "返回相关片段并可定位到树节点",
      "POST /edu/knowledge/search", method="POST", path="/edu/knowledge/search", body={"query": "分数加减"}, assert_="200"),
]

# ---- 班级管理
CASES += [
    C("admin", "教学资源/班级", "班级管理", "页面访问", "渲染", "P0",
      "有 resource:class:list 或 manager", ["1. 点『班级管理』"], "班级表格加载",
      "GET /edu/classes", locator="text=班级管理"),
    C("admin", "教学资源/班级", "班级管理", "新增班级", "对话框", "P0",
      "有写权限", ["1. 点新增", "2. 选年级/填名称(正则校验)/序号/班主任", "3. 保存"],
      "班级入库；名称正则 [\\u4e00-\\u9fa5A-Za-z0-9()（）·\\-_ ]{2,32}",
      "POST /edu/classes", method="POST", path="/edu/classes", body={"grade_id": 1, "name": "一班"}, assert_="200"),
    C("admin", "教学资源/班级", "班级管理", "申请建班/审核", "抽屉", "P1",
      "无写权限教师", ["1. 点『申请建班』提交", "2. manager 『建班审核』通过"], "申请经审核后自动建班",
      "POST /edu/class-requests", method="POST", path="/edu/class-requests", body={"grade_id": 1, "name": "x"}, assert_="200"),
    C("admin", "教学资源/班级", "班级管理", "学生管理抽屉", "抽屉", "P1",
      "存在班级", ["1. 点『学生数』开抽屉", "2. 批量导入/导出/移出"], "学生名单增删正确；导入按 学号,姓名,密码",
      "POST /edu/classes/{id}/students/import", method="POST", path="/edu/classes/{id}/students/import", assert_="200"),
    C("admin", "教学资源/班级", "班级管理", "启用/停用/删除", "行内", "P1",
      "存在班级", ["1. 切状态", "2. 删除(有学生不可删)"], "状态变更；有学生删除被拒",
      "PUT /edu/classes/{id}", method="PUT", path="/edu/classes/{id}", assert_="200"),
    C("admin", "教学资源/班级", "班级管理", "批量启用/停用/删除", "批量栏", "P2",
      "勾选多条", ["1. 批量操作并确认"], "批量状态变更", "PUT /edu/classes/batch", method="PUT", path="/edu/classes/batch", assert_="200"),
]

# ---- 日志审计
CASES += [
    C("admin", "系统基础/日志", "日志审计", "页面访问", "渲染", "P0",
      "sys_admin/grade_admin", ["1. 点『日志审计』"], "默认展示操作日志 Tab",
      "GET /logs/operation", locator="text=日志审计"),
    C("admin", "系统基础/日志", "日志审计", "Tab 切换", "切换", "P1",
      "已登录", ["1. 切登录/操作/错误日志"], "对应日志接口数据加载",
      "GET /logs/login", method="GET", path="/logs/login", assert_="list 非空或空"),
    C("admin", "系统基础/日志", "日志审计", "筛选/导出", "筛选+导出", "P1",
      "有数据", ["1. 选日期/模块/结果", "2. 导出 Excel"], "列表过滤；导出带鉴权的 xlsx",
      "GET /logs/export", method="GET", path="/logs/export", assert_="blob 200"),
]

# ---- 定时任务
CASES += [
    C("admin", "系统基础/定时任务", "定时任务", "页面访问", "渲染", "P1",
      "sys_admin 登录", ["1. 点『定时任务』"], "统计卡+任务表(含状态开关/执行记录)",
      "GET /jobs", locator="text=定时任务"),
    C("admin", "系统基础/定时任务", "定时任务", "新增任务", "对话框", "P1",
      "sys_admin", ["1. 点新增", "2. 填名称/执行逻辑(白名单)/Cron", "3. 保存"],
      "任务入库；func_path 必须在 jobHandlers 白名单",
      "POST /jobs", method="POST", path="/jobs", body={"name": "x", "func_path": "push_review_reminders", "cron": "0 8 * * *"}, assert_="200"),
    C("admin", "系统基础/定时任务", "定时任务", "开关/立即执行", "行内", "P1",
      "存在任务", ["1. 切状态开关", "2. 点『立即执行』确认"], "状态变更；立即触发一次执行并记录",
      "POST /jobs/{id}/run", method="POST", path="/jobs/{id}/run", assert_="200"),
    C("admin", "系统基础/定时任务", "定时任务", "编辑/删除", "对话框", "P1",
      "存在任务", ["1. 编辑保存", "2. 删除确认"], "编辑生效；删除后不再调度",
      "PUT /jobs/{id}", method="PUT", path="/jobs/{id}", assert_="200"),
    C("admin", "系统基础/定时任务", "定时任务", "执行记录抽屉", "抽屉", "P2",
      "任务曾执行", ["1. 点『执行记录』"], "展示历史执行结果", "GET /jobs/{id}/executions", method="GET", path="/jobs/{id}/executions"),
]

# ---- 附件管理
CASES += [
    C("admin", "系统基础/附件", "附件管理", "页面访问", "渲染", "P1",
      "sys_admin/grade_admin", ["1. 点『附件管理』"], "附件表格加载",
      "GET /attachments", locator="text=附件管理"),
    C("admin", "系统基础/附件", "附件管理", "上传/预览/下载/删除", "对话框+行操作", "P1",
      "已登录", ["1. 点上传拖入文件", "2. 行内预览/下载", "3. 删除确认"],
      "附件入库；预览/下载带鉴权；删除后列表移除",
      "POST /attachments/batch-upload", method="POST", path="/attachments/batch-upload", assert_="200"),
]

# ---- 系统报表 / 系统配置 / AI 配置 / AI 日志
CASES += [
    C("admin", "系统基础/系统报表", "系统报表", "页面访问", "渲染", "P1",
      "sys_admin/grade_admin", ["1. 点『系统报表』"], "统计卡+图表渲染，无报错",
      "GET /report/admin/overview", locator="text=系统报表"),
    C("admin", "系统基础/系统报表", "系统报表", "导出 Excel", "点击", "P2",
      "有数据", ["1. 点导出"], "下载 admin_overview xlsx", "GET /report/export/excel?report_type=admin_overview", method="GET", path="/report/export/excel", assert_="blob 200"),
    C("admin", "系统基础/系统配置", "系统配置", "页面访问+契约", "渲染", "P0",
      "sys_admin 登录", ["1. 点『系统配置』"], "全部字段有值（小写键绑定），可编辑项表格正确展示",
      "GET /system/config", locator="text=系统配置"),
    C("admin", "系统基础/AI配置", "AI 大模型配置", "页面访问", "渲染", "P1",
      "sys_admin 登录", ["1. 点『AI 大模型配置』"], "展示启用开关/提供商/Key(脱敏)/温度滑块",
      "GET /system/ai-config", locator="text=AI 大模型配置"),
    C("admin", "系统基础/AI配置", "AI 大模型配置", "测试连接", "点击", "P1",
      "已填 API Key/地址", ["1. 点『测试连接』"], "返回连通结果；失败提示原因不崩溃",
      "POST /system/ai-config/test", method="POST", path="/system/ai-config/test", assert_="返回 success/fail"),
    C("admin", "系统基础/AI配置", "AI 大模型配置", "保存配置", "点击", "P1",
      "已改参数", ["1. 点『保存配置』"], "配置落库；勾选清除 Key 时清空，未勾选空值不误清",
      "PUT /system/ai-config", method="PUT", path="/system/ai-config", body={"llm_enabled": True}, assert_="200"),
    C("admin", "系统基础/AI配置", "AI 大模型配置", "参数边界", "负向", "P2",
      "打开页面", ["1. 温度设超 0-2 / 最大输出超 256-32768"], "控件限制边界，保存不越界",
      "PUT /system/ai-config", method="PUT", path="/system/ai-config"),
    C("admin", "系统基础/AI日志", "AI 调用日志", "页面访问+筛选", "渲染+筛选", "P1",
      "sys_admin/grade_admin", ["1. 点『AI 调用日志』", "2. 选 Agent/状态筛选"], "日志表加载并按条件过滤",
      "GET /agent/logs", locator="text=AI 调用日志"),
    C("admin", "系统基础/AI日志", "AI 调用日志", "详情/引擎状态", "对话框+抽屉", "P2",
      "存在日志", ["1. 点详情", "2. 点引擎状态"], "展示调用明细与已注册 Agent",
      "GET /agent/logs/{id}", method="GET", path="/agent/logs/{id}"),
]

# ---- 版本信息（新增功能）
CASES += [
    C("admin", "系统基础/版本信息", "系统配置-版本卡片", "渲染", "访问渲染", "P1",
      "任意登录用户", ["1. 翻到『系统配置』页底部『版本信息』卡片"], "展示版本号/构建号/构建时间/最后更新时间四块，文字清晰",
      "GET /system/version", locator="text=版本信息"),
    C("admin", "系统基础/版本信息", "全站页脚", "渲染", "访问渲染", "P2",
      "任意登录用户", ["1. 查看任意页面底部页脚"], "紧凑显示 应用名 v版本 · 构建 短哈希 · 更新于 时间",
      "GET /system/version", locator=".ver-footer"),
    C("admin", "系统基础/版本信息", "更新时间戳自动记录", "接口验证", "升级触发", "P1",
      "部署新版本号/构建号", ["1. 重启服务", "2. 查 GET /system/version"], "updated_at 更新且 prior_version 记录上一版；同版本重启不刷新",
      "GET /system/version", method="GET", path="/system/version", assert_="updated_at 仅版本/构建变化时变"),
]

# ============================================================== 教师 (teacher)
# ---- 题库管理
CASES += [
    C("teacher", "教学资源/题库", "题库管理", "页面访问", "渲染", "P0",
      "teacher 登录", ["1. 点『题库管理』"], "题目表格加载，含题型/难度/状态/题库",
      "GET /question/questions", locator="text=题库管理"),
    C("teacher", "教学资源/题库", "题库管理", "筛选(年级/学科/知识点/题型/难度/状态/来源/关键词)", "筛选", "P1",
      "有数据", ["1. 逐级选年级→学科→知识点", "2. 选题型/难度", "3. 查询"],
      "列表按条件过滤；学科随年级联动；知识点随年级+学科联动",
      "GET /question/questions", method="GET", path="/question/questions", assert_="list 已过滤"),
    C("teacher", "教学资源/题库", "题库管理", "新增题目", "对话框保存", "P0",
      "有写权限", ["1. 点新增", "2. 填题干/题型/学科/年级/选项/答案/分值", "3. 保存"],
      "题目入库；8 种题型校验；模型给的 id 不可信，知识点经三重校验",
      "POST /question/questions", method="POST", path="/question/questions",
      body={"stem": "1+1=?", "type": "single", "subject_id": 1, "grade_id": 1, "options": [{"key": "A", "text": "2"}]}, assert_="200"),
    C("teacher", "教学资源/题库", "题库管理", "题目校验(必填)", "负向", "P1",
      "打开新增", ["1. 题干/题型/学科留空保存"], "前端拦截提示必填",
      "POST /question/questions", method="POST", path="/question/questions", body={"stem": ""}, assert_="校验失败/422"),
    C("teacher", "教学资源/题库", "题库管理", "编辑/详情/删除", "行内", "P1",
      "存在题目", ["1. 详情", "2. 编辑保存", "3. 删除确认"], "编辑生效；删除需确认",
      "PUT /question/questions/{id}", method="PUT", path="/question/questions/{id}", assert_="200"),
    C("teacher", "教学资源/题库", "题库管理", "状态开关", "行内", "P1",
      "存在题目", ["1. 切状态开关"], "题目上/下架即时生效",
      "POST /question/questions/{id}/status", method="POST", path="/question/questions/{id}/status", body={"status": "published"}, assert_="200"),
    C("teacher", "教学资源/题库", "题库管理", "批量(发布/下架/移动/分配知识点/改难度/删除)", "批量栏", "P1",
      "勾选多条", ["1. 选批量操作并确认"], "批量状态/归属变更；仅本人创建可被批量改",
      "POST /question/questions/batch", method="POST", path="/question/questions/batch", body={"action": "publish"}, assert_="200"),
    C("teacher", "教学资源/题库", "题库管理", "查重/AI变式", "行内", "P2",
      "存在题目", ["1. 点查重", "2. 点 AI 变式→创建选中"], "查重返回相似题；变式预览后入库",
      "GET /question/questions/{id}/duplicates", method="GET", path="/question/questions/{id}/duplicates"),
    C("teacher", "教学资源/题库", "题库管理", "批量导入", "对话框", "P1",
      "下载模板填好", ["1. 下载模板", "2. 上传 xlsx", "3. 开始导入"], "解析入库；结果展示成功/跳过",
      "POST /question/questions/import", method="POST", path="/question/questions/import", assert_="200"),
    C("teacher", "教学资源/题库", "题库管理", "导出/AI出题/AI质检", "对话框", "P2",
      "有数据/LLM可用", ["1. 导出", "2. AI 智能出题生成入库", "3. AI 质检定位"],
      "导出 xlsx；AI 出题存私有草稿；质检返回结果", "GET /question/questions/export", method="GET", path="/question/questions/export", assert_="blob 200"),
]

# ---- 试卷管理 + 向导 + 编辑
CASES += [
    C("teacher", "教学资源/试卷", "试卷管理", "页面访问", "渲染", "P0",
      "teacher 登录", ["1. 点『试卷管理』"], "试卷表格加载",
      "GET /question/papers", locator="text=试卷管理"),
    C("teacher", "教学资源/试卷", "试卷管理", "新建试卷(向导)", "跳转", "P0",
      "有写权限", ["1. 点『新建试卷』"], "跳转到标准组卷向导 Step1",
      "GET /teacher/papers/new", locator="text=新建试卷"),
    C("teacher", "教学资源/试卷", "试卷管理", "AI 智能组卷", "跳转", "P1",
      "有 AI 权限", ["1. 点『AI 智能组卷』"], "向导以 AI 模式打开",
      "GET /teacher/papers/new?mode=ai"),
    C("teacher", "教学资源/试卷", "试卷管理", "详情/编辑/复制/共享/导出/删除", "行内", "P1",
      "存在试卷", ["1. 详情", "2. 编辑跳编辑页", "3. 复制", "4. 共享", "5. 导出(Excel/Word/PDF/HTML)", "6. 删除"],
      "各操作生效；导出带鉴权 blob；共享走教师多选",
      "GET /question/papers/{id}", method="GET", path="/question/papers/{id}"),
    C("teacher", "教学资源/试卷", "试卷管理", "批量(复制/共享/删除)", "批量栏", "P2",
      "勾选多条", ["1. 批量操作确认"], "批量生效", "POST /question/papers/batch", method="POST", path="/question/papers/batch", assert_="200"),
    C("teacher", "教学资源/试卷", "新建试卷(向导)", "Step1 选模式", "向导", "P0",
      "向导页", ["1. 选自定义组卷 / AI 一键组卷", "2. 下一步"], "进入 Step2 对应表单",
      "—", locator=".el-step"),
    C("teacher", "教学资源/试卷", "新建试卷(向导)", "Step2 参数(自定义)", "表单", "P0",
      "自定义模式", ["1. 选年级/学科/命题标准", "2. 编辑题型结构(名称/题型/题量/分值)", "3. 设总分/时长/难度分布/知识点树", "4. 生成预览"],
      "难度合计=100% 且卷面分=总分才可生成；否则按钮置灰",
      "POST /question/papers/compose/preview", method="POST", path="/question/papers/compose/preview", assert_="200 或 422(校验)"),
    C("teacher", "教学资源/试卷", "新建试卷(向导)", "Step2 参数(AI)", "表单", "P1",
      "AI 模式", ["1. 填需求描述/年级/学科", "2. AI 一键组卷"], "调用 paperComposer；难度滑块禁用不下发",
      "POST /agent/paper-composer", method="POST", path="/agent/paper-composer", assert_="200"),
    C("teacher", "教学资源/试卷", "新建试卷(向导)", "Step3 预览调整", "向导", "P1",
      "已生成预览", ["1. 每题编辑/移除", "2. 重新生成/重构大题", "3. 下一步"], "本地预览可调整；缺失缺口有提示",
      "—", locator="text=预览"),
    C("teacher", "教学资源/试卷", "新建试卷(向导)", "Step4 保存", "向导", "P0",
      "预览完成", ["1. 填名称/说明/时长", "2. 保存试卷"], "试卷落库并跳编辑页/列表；usage_count 对称递增",
      "POST /question/papers/compose/save", method="POST", path="/question/papers/compose/save", assert_="200"),
    C("teacher", "教学资源/试卷", "编辑试卷", "元信息/逐题改分/换题/移除", "编辑", "P1",
      "编辑页", ["1. 改试卷名/时长", "2. 每题改分值", "3. 换一题/移除", "4. 保存并重算成绩"],
      "题目项分值更新；移除题作答迁移/计数；CASCADE 不丢学生作答",
      "PUT /question/papers/{id}/items", method="PUT", path="/question/papers/{id}/items", assert_="200"),
    C("teacher", "教学资源/试卷", "编辑试卷", "导出/版本/收藏", "顶部操作", "P2",
      "编辑页", ["1. 导出(多格式)", "2. 版本记录回溯", "3. 收藏"], "导出带鉴权；版本可回溯(禁当前)；收藏切换",
      "GET /question/papers/{id}/export", method="GET", path="/question/papers/{id}/export", assert_="blob 200"),
]

# ---- 作业考试
CASES += [
    C("teacher", "教学/作业考试", "作业与考试", "页面访问", "渲染", "P0",
      "teacher 登录", ["1. 点『作业与考试』"], "任务表格加载",
      "GET /task/tasks", locator="text=作业与考试"),
    C("teacher", "教学/作业考试", "作业与考试", "发布作业/考试", "对话框", "P0",
      "有写权限", ["1. 点发布", "2. 填标题/类型/试卷/起止时间/时长/及格分/下发班级", "3. 确定"],
      "任务发布；选试卷自动收敛及格分；下发关系建立",
      "POST /task/tasks", method="POST", path="/task/tasks",
      body={"title": "单元测试", "type": "exam", "paper_id": 1, "class_ids": [1]}, assert_="200"),
    C("teacher", "教学/作业考试", "作业与考试", "编辑/删除/批量", "行内+批量", "P1",
      "存在任务", ["1. 编辑保存", "2. 批量结束/删除"], "编辑生效；批量操作对仅本人记录生效",
      "PUT /task/tasks/{id}", method="PUT", path="/task/tasks/{id}", assert_="200"),
    C("teacher", "教学/作业考试", "作业与考试", "提交情况/学情报告", "抽屉", "P1",
      "任务有提交", ["1. 点提交情况", "2. 生成学情报告/AI 建议"], "统计卡+学生表；报告与建议生成",
      "GET /task/tasks/{id}/submissions", method="GET", path="/task/tasks/{id}/submissions"),
    C("teacher", "教学/作业考试", "作业与考试", "查看答卷", "对话框", "P2",
      "有提交", ["1. 点查看答卷"], "展示各题学生答案/正确答案/解析", "GET /grading/submissions/{id}", method="GET", path="/grading/submissions/{id}"),
]

# ---- 批改中心
CASES += [
    C("teacher", "教学/批改", "批改中心", "页面访问", "渲染", "P0",
      "grading:list", ["1. 点『批改中心』"], "待批改队列加载",
      "GET /grading/pending", locator="text=批改中心"),
    C("teacher", "教学/批改", "批改中心", "逐题评分", "工作区", "P0",
      "选中一份", ["1. 每题设满分/零分或填分值", "2. 填评语"], "分值与评语写入工作区",
      "PUT /grading/submissions/{id}", method="PUT", path="/grading/submissions/{id}", body={"scores": {}}, assert_="200"),
    C("teacher", "教学/批改", "批改中心", "保存/发布", "底部操作", "P0",
      "已评分", ["1. 保存批改结果", "2. 发布成绩"], "客观题自动判分；主观题 LLM 批改；发布后学生可见成绩",
      "POST /grading/submissions/{id}/grade", method="POST", path="/grading/submissions/{id}/grade", assert_="200"),
    C("teacher", "教学/批改", "批改中心", "打回重做", "prompt", "P1",
      "选中一份", ["1. 点打回重做填原因"], "学生收到重做任务", "POST /grading/submissions/{id}/reject", method="POST", path="/grading/submissions/{id}/reject", assert_="200"),
    C("teacher", "教学/批改", "批改中心", "批量采纳/发布", "批量栏", "P1",
      "勾选多份", ["1. 批量采纳", "2. 批量发布"], "批量生效", "POST /grading/batch/grade", method="POST", path="/grading/batch/grade", assert_="200"),
    C("teacher", "教学/批改", "批改中心", "键盘快捷键", "键盘", "P2",
      "批改工作区", ["1. Ctrl+Enter 保存下一份", "2. Alt+F/Z 满分零分"], "快捷键触发对应动作",
      "—", locator=".grading-workspace"),
]

# ---- 教案管理
CASES += [
    C("teacher", "教学/教案", "教案管理", "页面访问", "渲染", "P1",
      "lesson:plan:list", ["1. 点『教案管理』"], "教案表格加载",
      "GET /lesson/plans", locator="text=教案管理"),
    C("teacher", "教学/教案", "教案管理", "新建/编辑教案", "对话框", "P1",
      "有写权限", ["1. 新建", "2. 填标题/学科/年级/课时/教学目标/过程 stage 动态表", "3. 保存"],
      "教案入库；stage 可增删；附件可上传",
      "POST /lesson/plans", method="POST", path="/lesson/plans", body={"title": "x", "subject_id": 1}, assert_="200"),
    C("teacher", "教学/教案", "教案管理", "复制/共享/删除", "行内", "P1",
      "存在教案", ["1. 复制", "2. 共享开关", "3. 删除"], "复制生成副本；共享切换；删除需确认",
      "POST /lesson/plans/{id}/copy", method="POST", path="/lesson/plans/{id}/copy", assert_="200"),
    C("teacher", "教学/教案", "教案管理", "AI 生成教案", "向导", "P2",
      "LLM 可用", ["1. 点 AI 生成", "2. 填条件→开始生成", "3. 预览编辑→存入教案库"],
      "两段式生成；结构兜底；确认后入库", "POST /lesson/ai/generate", method="POST", path="/lesson/ai/generate", assert_="200"),
    C("teacher", "教学/教案", "教案管理", "生成记录", "抽屉", "P2",
      "有生成任务", ["1. 点生成记录", "2. 查看/原因"], "展示任务状态与错误", "GET /lesson/ai/jobs", method="GET", path="/lesson/ai/jobs"),
]

# ---- 学情/报表
CASES += [
    C("teacher", "教学/学情", "班级学情", "页面访问+筛选", "渲染", "P1",
      "analysis:class", ["1. 点班级学情", "2. 选班级"], "统计卡+图表加载；可跳个体分析",
      "GET /report/teacher/class-overview", locator="text=班级学情"),
    C("teacher", "教学/学情", "学生分析", "页面访问+筛选", "渲染", "P1",
      "analysis:student", ["1. 点学生分析", "2. 选班级→学生"], "概览/趋势/雷达/薄弱点展示",
      "GET /report/student/overview", method="GET", path="/report/student/overview"),
    C("teacher", "教学/报表", "教学报表", "页面访问+导出", "渲染+导出", "P2",
      "report:teacher", ["1. 点教学报表", "2. 选班级", "3. 导出"], "报表渲染；导出 xlsx 带鉴权",
      "GET /report/export/excel?report_type=teacher_overview", method="GET", path="/report/export/excel", assert_="blob 200"),
]

# ---- AI 出题组卷 / 智能助手（教师可用）
CASES += [
    C("teacher", "AI/Agent", "AI 出题组卷", "页面访问+能力选择", "渲染", "P1",
      "teacher 登录", ["1. 点『AI 出题组卷』", "2. 左侧选能力"], "展示对应表单；未启用 AI 仅降级",
      "GET /agent/status", locator="text=AI 出题组卷"),
    C("teacher", "AI/Agent", "AI 出题组卷", "出题生成+保存", "生成", "P1",
      "LLM 可用", ["1. 选出题", "2. 填学科/年级/题型/数量(1-30)", "3. 开始生成", "4. 保存到私有题库"],
      "生成题目预览；保存入库（二次确认）",
      "POST /agent/question-generator", method="POST", path="/agent/question-generator", assert_="200"),
    C("teacher", "AI/Agent", "AI 出题组卷", "组卷/答疑/规划", "生成", "P2",
      "LLM 可用", ["1. 选 paper_composer/tutor/study_planner", "2. 填参生成"], "对应 Agent 返回结果",
      "POST /agent/paper-composer", method="POST", path="/agent/paper-composer", assert_="200"),
    C("teacher", "AI/Agent", "AI 智能助手", "对话/重生成/停止", "对话", "P1",
      "agent:chat", ["1. 输消息发送", "2. 重新生成", "3. 停止生成"], "流式回复；重生成/停止生效；降级走规则引擎",
      "POST /agent/chat", method="POST", path="/agent/chat", body={"message": "什么是分数"}, assert_="200"),
]

# ============================================================== 学生 (student)
# ---- 随机练习
CASES += [
    C("student", "学习/练习", "随机练习", "页面访问", "渲染", "P1",
      "student 登录", ["1. 点『随机练习』"], "配置区(学科/年级/数量/题型/难度/知识点)加载",
      "GET /task/practice", locator="text=随机练习"),
    C("student", "学习/练习", "随机练习", "生成练习", "点击", "P0",
      "已选条件", ["1. 设学科/数量/题型", "2. 点生成练习"], "生成练习卷进入答题区",
      "POST /task/practice", method="POST", path="/task/practice", body={"subject_id": 1, "count": 5}, assert_="200"),
    C("student", "学习/练习", "随机练习", "答题+收藏+提交", "交互", "P0",
      "练习进行中", ["1. 逐题作答", "2. 星标收藏", "3. 提交并查看结果"], "答案保存；收藏入库；提交后显示对错/解析",
      "POST /task/submit", method="POST", path="/task/submit", body={"answers": {}}, assert_="200"),
    C("student", "学习/练习", "随机练习", "练习历史/再来一组", "抽屉", "P2",
      "有历史", ["1. 点练习历史", "2. 再来一组"], "历史列表；重置到配置区", "GET /learning/practice/history", method="GET", path="/learning/practice/history"),
    C("student", "学习/练习", "随机练习", "番茄钟", "子组件", "P2",
      "练习中", ["1. 开始/暂停/重置专注", "2. 改时长"], "倒计时运行；时长限制 10-50/3-15", "—", locator=".pomodoro"),
]

# ---- 模拟考试 / 答题
CASES += [
    C("student", "学习/考试", "模拟考试", "页面访问+Tab", "渲染", "P0",
      "student 登录", ["1. 点『模拟考试』", "2. 切待完成/已完成"], "卡片列表按状态分组",
      "GET /task/my-tasks", locator="text=模拟考试"),
    C("student", "学习/考试", "模拟考试", "开始答题", "卡片", "P0",
      "有待完成", ["1. 点开始答题(canStart)"], "跳答题页；不可开始时禁用并提示原因",
      "GET /task/tasks/{id}/paper", method="GET", path="/task/tasks/{id}/paper"),
    C("student", "学习/考试", "模拟考试", "查看解析/重考", "卡片", "P1",
      "有已完成", ["1. 查看解析", "2. 重考(left>0)"], "展示逐题解析；剩余次数内可重考",
      "GET /task/submissions/{id}", method="GET", path="/task/submissions/{id}"),
    C("student", "学习/考试", "答题", "作答+题号导航", "交互", "P0",
      "答题页", ["1. 逐题作答", "2. 点题号跳转"], "答案写入；题号状态(todo/done)更新",
      "POST /task/submit", method="POST", path="/task/submit", body={"answers": {}}, assert_="200"),
    C("student", "学习/考试", "答题", "交卷(手动/超时)", "交卷", "P0",
      "答题中", ["1. 点交卷确认", "2. (或倒计时归零)"], "交卷判分；超时自动交卷；次数用尽显示 exhausted",
      "POST /task/submit", method="POST", path="/task/submit", assert_="200"),
    C("student", "学习/考试", "答题", "防切屏心跳", "隐式", "P1",
      "考试且 anti_cheat", ["1. 切后台再回", "2. 等待 30s"], "切屏次数+1；心跳上报；草稿 30 分钟可恢复",
      "POST /task/heartbeat", method="POST", path="/task/heartbeat", assert_="200"),
]

# ---- 错题本
CASES += [
    C("student", "学习/错题", "错题本", "页面访问+筛选", "渲染", "P0",
      "student 登录", ["1. 点错题本", "2. 选学科/错因/掌握状态/关键词"], "错题卡片按条件过滤",
      "GET /learning/wrong-questions", locator="text=错题本"),
    C("student", "学习/错题", "错题本", "AI 分析错因/重做/变式", "行内", "P1",
      "存在错题", ["1. AI 分析错因", "2. 重做同类", "3. 变式练习"], "错因分析弹窗；重做/变式跳答题页",
      "POST /learning/wrong-questions/analyze", method="POST", path="/learning/wrong-questions/analyze", assert_="200"),
    C("student", "学习/错题", "错题本", "标注错因/标记掌握", "行内", "P1",
      "存在错题", ["1. 标注错因", "2. 标记已掌握"], "错因/掌握状态更新",
      "PUT /learning/wrong-questions/{id}", method="PUT", path="/learning/wrong-questions/{id}", assert_="200"),
    C("student", "学习/错题", "错题本", "导出", "点击", "P2",
      "有错题", ["1. 点导出"], "下载 .md 带鉴权", "GET /learning/wrong-questions/export", method="GET", path="/learning/wrong-questions/export", assert_="blob 200"),
]

# ---- 学习笔记
CASES += [
    C("student", "学习/笔记", "学习笔记", "页面访问+筛选", "渲染", "P1",
      "student 登录", ["1. 点学习笔记", "2. 筛选"], "笔记卡片列表",
      "GET /learning/notes", locator="text=学习笔记"),
    C("student", "学习/笔记", "学习笔记", "新建/编辑笔记", "对话框", "P1",
      "已登录", ["1. 新建", "2. 填标题/学科/标签/正文", "3. 保存"], "笔记入库；正文 sanitizeHtml 防 XSS",
      "POST /learning/notes", method="POST", path="/learning/notes", body={"title": "x", "content": "<p>1</p>"}, assert_="200"),
    C("student", "学习/笔记", "学习笔记", "AI 整理/收藏/删除", "卡片", "P1",
      "存在笔记", ["1. AI 整理", "2. 收藏切换", "3. 删除确认"], "AI 整理写回 ai_*；收藏切换；删除移除",
      "POST /learning/notes/{id}/organize", method="POST", path="/learning/notes/{id}/organize", assert_="200"),
]

# ---- 智能复习 / 学习报表 / 成绩中心
CASES += [
    C("student", "学习/复习", "智能复习", "页面访问+AI生成", "渲染", "P1",
      "student 登录", ["1. 点智能复习", "2. 点 AI 生成复习计划填天数/时长"], "计划列表；AI 生成艾宾浩斯计划",
      "POST /learning/review-plans/generate", method="POST", path="/learning/review-plans/generate", body={"days": 7, "daily_minutes": 30}, assert_="200"),
    C("student", "学习/复习", "智能复习", "完成复习", "行内", "P1",
      "存在计划", ["1. 点完成复习"], "标记完成(quality=good)", "POST /learning/review-plans/{id}/complete", method="POST", path="/learning/review-plans/{id}/complete", assert_="200"),
    C("student", "学习/报表", "学习报表", "页面访问+导出+AI建议", "渲染", "P1",
      "student 登录", ["1. 点学习报表", "2. 选学科趋势", "3. 重新生成 AI 建议", "4. 导出"], "图表渲染；建议生成；导出带鉴权",
      "GET /report/student/overview", locator="text=学习报表"),
    C("student", "学习/成绩", "成绩中心", "页面访问+查看解析", "渲染", "P0",
      "student 登录", ["1. 点成绩中心", "2. 查看解析"], "成绩列表；解析弹窗含得分/排名/逐题",
      "GET /task/my/scores", locator="text=成绩中心"),
]

# ---- 收藏 / 掌握图谱 / 自主组卷 / 打卡 / 路径 / 闪卡 / 知识资料
CASES += [
    C("student", "学习/收藏", "题目收藏", "页面访问+改标签/取消", "渲染", "P2",
      "student 登录", ["1. 点题目收藏", "2. 改标签保存", "3. 取消收藏"], "标签更新；取消后移除",
      "PUT /learning/favorites/{id}", method="PUT", path="/learning/favorites/{id}", assert_="200"),
    C("student", "学习/收藏", "题目收藏", "收藏专项练习", "点击", "P2",
      "有收藏", ["1. 点收藏专项练习"], "生成专项练习跳答题页", "POST /learning/favorites/practice", method="POST", path="/learning/favorites/practice", assert_="200"),
    C("student", "学习/掌握", "掌握图谱", "页面访问+薄弱练习", "渲染", "P1",
      "student 登录", ["1. 点掌握图谱选学科", "2. 薄弱专项练习"], "雷达/条形图；跳练习",
      "GET /learning/mastery-map", locator="text=掌握图谱"),
    C("student", "学习/自主组卷", "自主组卷", "生成自测卷+答题", "表单", "P1",
      "student 登录", ["1. 填名称/学科/数量/题型/难度/知识点", "2. 生成自测卷", "3. 立即开始答题"], "生成自测卷跳答题页",
      "POST /learning/custom-paper", method="POST", path="/learning/custom-paper", body={"subject_id": 1, "count": 10}, assert_="200"),
    C("student", "学习/打卡", "学习打卡", "新建目标+打卡", "对话框", "P2",
      "student 登录", ["1. 新建目标(名称/周期/值/单位)", "2. 今日打卡"], "目标入库；打卡记录",
      "POST /learning/goals", method="POST", path="/learning/goals", body={"title": "每日10题", "target_type": "daily", "target_value": 10, "unit": "题数"}, assert_="200"),
    C("student", "学习/路径", "学习路径", "页面访问+去练习", "渲染", "P2",
      "student 登录", ["1. 点学习路径选学科", "2. 去练习(基础/中/难)"], "路径时间线；跳练习",
      "GET /learning/learning-path", locator="text=学习路径"),
    C("student", "学习/闪卡", "闪卡速记", "翻面+认识/不认识", "交互", "P2",
      "student 登录", ["1. 点卡片翻面", "2. 认识/不认识", "3. 再来一轮"], "翻面显示答案；进度推进；可只练不认识",
      "GET /learning/flashcards", locator="text=闪卡速记"),
    C("student", "学习/知识资料", "知识资料", "树+附件预览/下载", "渲染", "P2",
      "student 登录", ["1. 点知识资料", "2. 搜知识点选节点", "3. 预览/下载附件"], "树加载；附件预览/下载带鉴权",
      "GET /edu/knowledge/{kp_id}/attachments", method="GET", path="/edu/knowledge/{kp_id}/attachments"),
]

# ---- 学生端 AI 助手
CASES += [
    C("student", "AI/Agent", "AI 智能助手", "对话+上下文", "对话", "P1",
      "student 登录", ["1. 点 AI 智能助手", "2. 选年级/学科上下文", "3. 发送消息"], "流式回复含上下文；降级走规则引擎",
      "POST /agent/chat", method="POST", path="/agent/chat", body={"message": "讲讲解方程"}, assert_="200"),
]

# ============================================================== 公共（登录/注册/顶栏/个人中心）
CASES += [
    C("public", "系统基础/认证", "登录", "登录成功", "提交", "P0",
      "已注册账号", ["1. 输账号/密码/验证码", "2. 点登录"], "签发双令牌；跳 dashboard；localStorage 存 user",
      "POST /auth/login", method="POST", path="/auth/login", body={"username": "admin", "password": "x", "captcha_key": "k", "captcha": "v"}, assert_="200 且 data.access_token"),
    C("public", "系统基础/认证", "登录", "验证码必填/错误", "负向", "P0",
      "登录页", ["1. 验证码留空或错误提交"], "提示验证码错误，不签发令牌",
      "POST /auth/login", method="POST", path="/auth/login", body={"captcha": "bad"}, assert_="4xx"),
    C("public", "系统基础/认证", "注册", "提交注册申请", "提交", "P0",
      "注册页", ["1. 选身份/填账号(3-32)/密码(≥8含字母数字)/确认/姓名/班级/验证码", "2. 提交"], "进入审批流；密码一致性校验",
      "POST /auth/register", method="POST", path="/auth/register", body={"identity": "student", "username": "s1", "password": "Test@1234"}, assert_="200"),
    C("public", "系统基础/认证", "登出", "退出", "点击", "P0",
      "已登录", ["1. 点退出登录确认"], "令牌写入吊销名单；跳登录页",
      "POST /auth/logout", method="POST", path="/auth/logout", assert_="200"),
    C("admin", "系统基础/个人中心", "个人中心", "改密/资料", "渲染", "P1",
      "已登录", ["1. 点个人中心", "2. 改密码(用 new_password 契约)"], "资料/密码更新；契约用 new_password 字段",
      "PUT /auth/password", method="PUT", path="/auth/password", body={"old_password": "x", "new_password": "New@1234"}, assert_="200"),
    C("admin", "系统基础/通知", "顶栏通知", "全部已读/单条", "点击", "P2",
      "有未读通知", ["1. 点全部已读", "2. 单条标记已读"], "通知状态更新",
      "POST /system/notifications/read-all", method="POST", path="/system/notifications/read-all", assert_="200"),
    C("public", "系统基础/权限", "越权访问", "403 校验", "负向", "P0",
      "student 令牌", ["1. 用 student 令牌访问 /system/users"], "返回 403，不泄露数据",
      "GET /system/users", method="GET", path="/system/users", assert_="403"),
]

# ============================================================== 编号与导出
PRIO_ORDER = {"P0": 0, "P1": 1, "P2": 2}
ROLE_ORDER = {"admin": 0, "teacher": 1, "student": 2, "public": 3}


def emit():
    # 统一编号：按角色→模块稳定排序
    ordered = sorted(
        CASES,
        key=lambda c: (ROLE_ORDER.get(c["role"], 9), PRIO_ORDER.get(c["priority"], 9),
                       c["module"], c["menu"], c["element"]),
    )
    seq = {}
    for c in ordered:
        seq.setdefault(c["role"], 0)
        seq[c["role"]] += 1
        prefix = {"admin": "ADM", "teacher": "TCH", "student": "STU", "public": "PUB"}[c["role"]]
        c["id"] = f"FUNC-{prefix}-{seq[c['role']]:03d}"

    out_json = os.path.join(HERE, "FUNCTIONAL_TEST_CASES.json")
    out_csv = os.path.join(HERE, "FUNCTIONAL_TEST_CASES.csv")
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(ordered, f, ensure_ascii=False, indent=2)

    cols = ["id", "role", "module", "menu", "element", "action", "priority",
            "precondition", "steps", "expected", "api", "auto_type", "auto_method",
            "auto_path", "auto_assert", "auto_locator"]
    with open(out_csv, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for c in ordered:
            a = c["automation"]
            w.writerow([
                c["id"], c["role"], c["module"], c["menu"], c["element"], c["action"], c["priority"],
                c["precondition"], " | ".join(c["steps"]), c["expected"], c["api"],
                a["type"], a.get("method") or "", a.get("path") or "",
                a.get("assert") or "", a.get("locator") or "",
            ])
    print(f"[emit] {len(ordered)} cases -> {out_json}\n        {out_csv}")
    return ordered


def coverage():
    from collections import defaultdict
    m = defaultdict(int)
    for c in CASES:
        m[(c["role"], c["menu"])] += 1
    print(f"{'role':<8}{'menu':<16}{'cases':>6}")
    for (role, menu), n in sorted(m.items(), key=lambda x: (ROLE_ORDER.get(x[0][0], 9), x[0][1])):
        print(f"{role:<8}{menu:<16}{n:>6}")
    print(f"TOTAL={len(CASES)}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--emit", action="store_true")
    ap.add_argument("--coverage", action="store_true")
    ap.add_argument("--run", action="store_true")
    args = ap.parse_args()
    if args.coverage:
        coverage()
    elif args.emit:
        emit()
    elif args.run:
        # 延迟导入执行器，避免无依赖时报错
        sys.path.insert(0, HERE)
        import functional_runner  # noqa: F401
        functional_runner.main()
    else:
        coverage()
        emit()
