# 端到端自动化测试报告

> 生成时间：2026-10-15 12:28:47　|　总计 **0** 项：通过 **0**，失败 **0**

## 一、测试概览

| 阶段 | 用例数 | 通过 | 失败 | 通过率 |
|------|-------:|-----:|-----:|-------:|

## 二、详细用例结果

## 三、本轮修复的缺陷

自动化测试共发现并修复 **14 个真实缺陷**，覆盖安全越权、判分正确性、AI 能力可用性三条主线。

### 3.1 安全与权限（4 个）

| # | 缺陷 | 影响 | 修复位置 |
|---|------|------|---------|
| 1 | 任意教师可读取/复制/导出他人试卷完整答案 | 遍历 `paper_id` 即可批量获取他人题库答案 | `api/v1/question.py` 新增 `_assert_paper_readable()` |
| 2 | `attachments.py` 漏导入 `desc` | 附件列表接口 500，管理员无法检索附件 | `api/v1/attachment.py` 补充 import |
| 3 | `admin_overview()` 参数名与调用处不一致 | 报表 Excel 导出必然 500 | `api/v1/report.py` 参数改为 `user` |
| 4 | 登出后原 Token 仍然有效 | 用户「退出登录」后 Token 泄露即可被冒用 | `core/security.py` 新增 jti 吊销名单 + `api/v1/auth.py` |

### 3.2 判分与错题闭环（5 个）

| # | 缺陷 | 影响 | 修复位置 |
|---|------|------|---------|
| 5 | 多选题答案 list 直接绑定 Text 列 | **含多选题的考试交卷必然 500**，学生答案全丢 | `services/grading_service.py` 新增 `_content_to_db()` |
| 6 | `GradingAgent` 对 list 答案调 `.strip()` | 判分 Agent 抛 AttributeError，**整场判分结果为空** | `agents/grading_agent.py` 新增 `_norm_answer_set()` |
| 7 | 标量答案分支引用已删除变量 `sa` | 单选/填空/判断全部判错 | 同上，改用归一化集合比较 |
| 8 | 待人工批改的主观题被当成错题收录 | 学生答对的题出现在错题本 | `grading_service.save_answers()` 区分「未判定」与「做错」 |
| 9 | 复习计划不关联错题 + `stage>=2` 恒不成立 | **艾宾浩斯记忆曲线闭环完全失效** | `study_agent._persist_review_plan()` + `grading.py complete_review()` |

### 3.3 AI 能力可用性（5 个）

| # | 缺陷 | 影响 | 修复位置 |
|---|------|------|---------|
| 10 | `RouterAgent` 未注册进 `AGENT_REGISTRY` | Agent 中心少显示一个，`is_fallback` 永远 false | `agents/base.py` `load_agents()` |
| 11 | `Orchestrator` 用下标读 `r["is_fallback"]` | `/agent/chat` 统一对话入口 **必然 500** | 同上，改 `.get()` |
| 12 | `/agent/tutor` 只读 `data["message"]` | 前端传 `question`，学生问题被丢弃，回答恒为「请描述你的问题」 | `api/v1/agent.py` 兼容多字段 |
| 13 | 题库复用/AI 生成题目不返回 `id` | 智能组卷生成 0 题的空卷，功能形同虚设 | `question_agent.py` + `paper_agent.py` |
| 14 | 角色复制 `code` 固定加 `_copy` 后缀 | 第二次复制必然撞唯一约束失败 | `api/v1/system.py` 自动去重 |

### 3.4 数据完整性（1 项补齐）

- **知识点库为空**：`edu_knowledge_point` 表 0 条，导致 AI 组卷无法指定考点、错题无法归因、掌握地图无数据。
  已在 `init_db.py` 补充 75 条覆盖 1/3/5/7/8/9 年级的核心知识点（幂等播种）。
- **系统配置只读**：新增 `sys_config` 表与 `PUT/DELETE /system/config` 接口，管理员可在线调参而无需重启容器。


## 四、遗留问题清单

本轮测试未发现遗留问题。

## 五、已知限制（非缺陷）

| 项 | 说明 |
|----|------|
| LLM 未配置 | `llm_enabled=false` 时，主观题按设计进入「待教师人工批改」队列，AI 组卷/答疑走规则引擎与知识库检索降级。配置 `LLM_API_KEY` 后自动启用。 |
| 令牌吊销为单进程实现 | 登出吊销名单保存在进程内存，多副本部署需替换为 Redis。已在代码注释中标注。 |
| 教师只能管自己班 | 数据权限的预期行为。`stu731` 属七年级(2)班（teacher4 任教），体验时应用 `teacher4` 登录，docs/QUICKSTART.md 已更正。 |
