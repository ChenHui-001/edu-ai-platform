# 问题清单与修复汇总（QA 第二轮）

> 依据：`BUG_REPORT.md`（首轮审计）。本轮逐条定位、修复并补验证。
> 验证入口：`cd backend && python -m pytest qa_audit_suite.py -q` → **19 passed**。
> 静态门禁：`py_compile` 全通过；`ruff check <改动文件> --select F,E9` → All checks passed。
> 日期：2026-10-29。

## 一、已修复并验证（6 项）

| 编号 | 现象 | 根因 | 修复方式 | 改动文件 | 验证用例 | 结果 |
|------|------|------|----------|----------|----------|------|
| BUG-006 | 认证依赖若漏传 db，登出/改密后旧 token 仍可用 | `decode_token(db=None)` 静默跳过吊销检查 | 改为 **fail-closed**：需吊销校验却无 db 直接拒绝；登出显式 `check_revocation=False` | `core/security.py`、`api/v1/auth.py` | `test_decode_token_fail_closed_without_db`、`test_decode_token_revocation_with_db` | ✅ |
| BUG-009 | 并发 AI 出题时返回的题目 id 可能错配为他人题目 | 落库后用 `order_by(id desc).limit(saved)` 反查，依赖“本请求独占最高 id” | 用**本批落库对象自身 id** 回填（`expire_on_commit=False` 直接可读） | `agents/question_agent.py` | `test_id_backfill_old_vs_new_under_concurrency`（演示旧法取到他人 id，新法取到本批） | ✅ |
| BUG-001 | 多次改卷后 `usage_count` 只增不减，选题偏好失真 | `_write_items` 删除旧题项时不递减计数 | 删除旧题项时逐条 `usage_count -= 1`（floor 0），与插入 +1 对称 | `api/v1/paper_compose.py` | `test_write_items_symmetric_usage_count`（保留 5→5、移除 5→4、新增 0→1） | ✅ |
| BUG-014 | 小数难度占比 round 后合计可能为 99/101 | “已百分制”分支只 `int(round())`，未补余数 | 计算 drift，补给小数部分最大的档，保证合计=100 | `services/paper_compose_service.py` | `test_normalize_decimal_sum_is_100[3 组]` | ✅ |
| BUG-018 | 超时边界判定不可确定性测试，CI 慢机偶发红 | `effective_status`/`apply_timeout` 未透传 `now` | 两函数新增 `now` 参数并转发给 `is_timed_out` | `services/agent_job_state.py` | `test_effective_status_now_injection` | ✅ |
| BUG-015 | 七年级物理为死数据，从未落库却误导维护 | 种子含国家课程不存在的七年级物理 | 删除 `KNOWLEDGE_POINTS[7]["物理"]` 死块并加注释 | `services/init_db.py` | `test_grade7_has_no_physics`（7 无、8/9 有） | ✅ |

> 补充：BUG-006 经核实**认证链路本就传 db**（`deps.py:56`、`auth.py:349`），故非活跃漏洞；本次把“静默默认”改为 fail-closed，消除未来误用风险。登出（`auth.py:428/432`）显式关闭吊销校验，因其本就要拉黑 token。

## 二、未改代码的问题（分类与理由）

| 编号 | 现象 | 根因 | 处理结论 |
|------|------|------|----------|
| BUG-003 | ~42/59 学科无知识点，AI 出题挂不上、掌握度失效 | 种子数据缺口（数据问题） | **非代码修复**。代码已正确降级（kp_id=None 不编造）。需运营用「教学资源→知识点 / 知识点 AI 生成」补齐；建议后续在无知识点学科的出题响应加教师侧提示（增强项）。 |
| BUG-005 | 限流冷却期 `/health` 仍报 enabled=true | `is_available()` 语义不含冷却 | **已覆盖，非缺陷**。`/agent/status` 已暴露 `breaker`/`cooldown_remaining`（agent.py:201-203）；`/health` 刻意不复读以避免探针每次打 DB。 |
| BUG-007 | Windows Docker 9p 下 sys_config 读取失败静默回落 | 9p 不支持 SQLite 多连接/WAL | **环境配置问题**。生产用命名卷无此问题；代码 fallback 已 fail-open。本地须用命名卷（DB/日志）。 |
| BUG-008 | 部署脚本 LLM 配置可能与 DB 漂移 | 双配置源 | **需现场核查**。脚本在仓库外 `deploy_scripts/`（不入 git），本次会话无法读取修改；部署后应以 `/agent/status` 与 DB sys_config 一致性为准。 |
| BUG-010 | 无 alembic，历史库难平滑迁移 | 早期未引入迁移框架 | **架构技术债**，超出本次修复范围；新库无碍，历史库升级需人工补迁移。 |
| BUG-016 | `/edu/subjects` 不传 grade_id 返回重名 | 学科唯一键 `(grade_id,name)` | **契约问题**。改默认去重会影响精确场景，保持现状并在契约文档标注（前端纯下拉传 `distinct=true`）。 |
| BUG-017 | 无单题 GET 详情端点 | 接口设计偏列表 | **功能增强项**，非缺陷，列入 backlog（便于 e2e 精确断言与前端详情）。 |

## 三、MEMORY.md 整理说明

**规模**：16,836 → 8,141 字节（−52%），66 行，按主题（交付纪律 / 核心不变量 / 数据契约 / 生产运维 / 门禁）重组。

**删除 / 合并的条目及原因**：

1. **mihomo SSH 的 PowerShell 路由代码块（约 15 行）** → 合并为「见 GOTCHAS.md」。原因：`GOTCHAS.md` 已有完整判定方法与命令，两份维护必漂移。
2. **9p / Windows 挂载说明的重复段落**（MEMORY 与 GOTCHAS 各一份）→ 精简为一条结论。原因：重复。
3. **LLM 坑位的长篇因果叙述**（33 秒 401、920 分蒸发等过程）→ 压缩为“结论+根因+关键数字”，细节留在代码注释与 GOTCHAS。原因：篇幅冗长、信息不丢。
4. **`PROVIDERS[].env_key` 死元数据的长句** → 一行。原因：低信息密度。
5. **「子代理完成通知 ≠ 报告已收」** → 删除。原因：通用协作提醒，与本项目无关且易过时。
6. **更名说明重复出现** → 合并到首行。原因：重复。
7. **「容器内查 SQLite / 本地容器重建」** → 不在 MEMORY 保留（GOTCHAS 已有完整版）。原因：重复、易随容器形态变化而失效。

**保留并强化的关键信息**：所有阈值（8192 tokens、300/600s、1800s、30→300s 退避）、四层一致交付纪律、LLM 熔断三层不变量、组卷 CASCADE 顺序与 usage_count 对称、时区契约、JWT fail-closed、权限模型、知识点缺口、9p 限制、生产服务器/凭据/账号、五道门禁与反向验证纪律。

> 说明：本轮未发现明确“与现实不符”的事实性错误条目，主要问题是**重复与篇幅超限**；已按上表处理。

## 四、复现验证命令

```bash
cd backend
"C:/Program Files/Python312/python.exe" -m pytest qa_audit_suite.py -q      # 19 passed
"C:/Program Files/Python312/python.exe" -m py_compile \
  app/core/security.py app/api/v1/auth.py app/agents/question_agent.py \
  app/api/v1/paper_compose.py app/services/paper_compose_service.py \
  app/services/agent_job_state.py app/services/init_db.py qa_audit_suite.py  # OK
"C:/Program Files/Python312/python.exe" -m ruff check <上述文件> --select F,E9  # All checks passed
```

## 五、交付纪律提示

本次仅做**本地代码修复 + 验证**，未提交/推送/发布。按项目最高纪律，若要上线需执行
`bash tools/auto_ship.sh --bump patch`（回归→commit→push→等 CI→拉 ghcr→校验四层一致），并在推送后逐个 job 确认 CI success。
