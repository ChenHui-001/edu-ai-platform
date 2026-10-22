# -*- coding: utf-8 -*-
"""
端到端自动化测试统一入口

用法：
    python tests/run_all.py            # 跑全部三个阶段
    python tests/run_all.py admin      # 只跑管理员
    python tests/run_all.py teacher    # 只跑教师
    python tests/run_all.py student    # 只跑学生
"""
import importlib
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("PYTHONIOENCODING", "utf-8")

from e2e_framework import R  # noqa: E402

FIXED_SECTION = """## 三、本轮修复的缺陷

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

"""

KNOWN_LIMITS = """## 五、已知限制（非缺陷）

| 项 | 说明 |
|----|------|
| LLM 未配置 | `llm_enabled=false` 时，主观题按设计进入「待教师人工批改」队列，AI 组卷/答疑走规则引擎与知识库检索降级。配置 `LLM_API_KEY` 后自动启用。 |
| 令牌吊销为单进程实现 | 登出吊销名单保存在进程内存，多副本部署需替换为 Redis。已在代码注释中标注。 |
| 教师只能管自己班 | 数据权限的预期行为。`stu731` 属七年级(2)班（teacher4 任教），体验时应用 `teacher4` 登录，docs/QUICKSTART.md 已更正。 |
"""

# ---------------------------------------------------------------- 门禁阈值
# 这两个数字是「假绿」的兜底保险，不是性能指标：
# - ENV_SKIP_RATIO_MAX：环境跳过占比上限。服务宕机/数据缺失时用例会走
#   R.env()，该状态既不算 PASS 也不算 FAIL。若不设上限，「服务全挂了」
#   也会输出「失败 0」。
# - MIN_EXPECTED_CASES：全量通过用例数下限。阶段被静默跳过或中途中断时
#   用例数会骤降（811 → 200），同样表现为「失败 0」。
# 阈值取比当前基线略宽松的值，避免正常波动误报；基线更新后同步调整。
#
# ⚠️ 比例判断必须配**最小样本量**：单阶段只有 16 项时，1 条 ENV 就是 6.2%，
# 会被误判为「环境大面积失效」。ENV 比例的目的是发现「成片跳过」，
# 样本太小时统计意义不足，直接跳过比例校验（用例数下限另行把关全量）。
ENV_SKIP_RATIO_MAX = 0.05
ENV_RATIO_MIN_SAMPLE = 100
MIN_EXPECTED_CASES = 730

STAGES = [    ("admin", "阶段一 · 管理员视角", "test_admin"),
    ("teacher", "阶段二 · 教师建题组卷", "test_teacher"),
    ("student", "阶段三 · 学生答题与 AI 批改", "test_student"),
    ("learning", "阶段四 · 学习中心专项", "test_learning"),
    ("requirements", "阶段五 · 需求覆盖补充", "test_requirements"),
    ("teaching_mgmt", "阶段六 · 教师端教学管理专项", "test_teaching_mgmt"),
    ("lesson_plan", "阶段七 · 教师端教案管理专项", "test_lesson_plan"),
    ("resource", "阶段八 · 管理员教学资源专项", "test_resource_manage"),
    ("teaching", "阶段九 · 教学管理模块专项", "test_teaching_module"),
    ("learning_hub", "阶段十 · 学习中心权限专项", "test_learning_hub"),
    ("analysis", "阶段十一 · 学情分析专项", "test_analysis"),
    ("agent", "阶段十二 · AI 智能专项", "test_agent"),
    ("agent_opt", "阶段十三 · AI 优化项验证", "test_agent_opt"),
    ("agent_struct", "阶段十四 · AI 结构性优化", "test_agent_struct"),
    ("system", "阶段十五 · 系统管理专项", "test_system"),
]


def banner():
    print("\033[1;95m" + "#" * 70)
    print("#   九年义务教育 AI 学习管理系统 · 端到端自动化测试")
    print("#   admin → teacher1 → stu731 全链路验证")
    print("#" * 70 + "\033[0m")


def summary_md():
    lines = []
    lines.append("# 端到端自动化测试报告\n")
    # ⚠️ ENV（环境故障/跳过）必须**单独列出**，不能悄悄丢掉。
    # 以前只报 PASS+FAIL，ENV 既不入总数也不入失败，于是「服务宕机导致大量用例
    # 走 R.env」时报告仍显示「失败 0」→ 门禁放行。这是最危险的假绿。
    env_n = R.env_failed
    lines.append(f"> 生成时间：{time.strftime('%Y-%m-%d %H:%M:%S')}　|　"
                 f"总计 **{R.passed + R.failed + env_n}** 项：通过 **{R.passed}**，"
                 f"失败 **{R.failed}**，环境跳过 **{env_n}**\n")

    by_phase = {}
    for phase, name, status, ms, detail in R.cases:
        by_phase.setdefault(phase, []).append((name, status, ms, detail))

    lines.append("## 一、测试概览\n")
    lines.append("| 阶段 | 用例数 | 通过 | 失败 | 跳过 | 通过率 |")
    lines.append("|------|-------:|-----:|-----:|-----:|-------:|")
    for phase, rows in by_phase.items():
        p = sum(1 for r in rows if r[1] == "PASS")
        f = sum(1 for r in rows if r[1] == "FAIL")
        e = sum(1 for r in rows if r[1] == "ENV")
        rate = round(p / len(rows) * 100, 1) if rows else 0
        lines.append(f"| {phase} | {len(rows)} | {p} | {f} | {e} | {rate}% |")
    lines.append("")

    lines.append("## 二、详细用例结果\n")
    idx = 0
    for phase, rows in by_phase.items():
        lines.append(f"### {phase}\n")
        lines.append("| # | 用例 | 结果 | 耗时 | 说明 |")
        lines.append("|--:|------|:----:|-----:|------|")
        for name, status, ms, detail in rows:
            idx += 1
            icon = "✅" if status == "PASS" else "❌"
            d = (detail or "").replace("|", "\\|").replace("\n", " ")[:110]
            lines.append(f"| {idx} | {name} | {icon} {status} | {ms}ms | {d} |")
        lines.append("")

    lines.append(FIXED_SECTION)

    if R.issues:
        lines.append("## 四、遗留问题清单\n")
        order = {"高": 0, "中": 1, "低": 2}
        for i, it in enumerate(sorted(R.issues, key=lambda x: order.get(x["severity"], 9)), 1):
            lines.append(f"### {i}. [{it['severity']}] {it['title']}\n")
            lines.append(f"**描述**：{it['detail']}\n")
            if it.get("repro"):
                lines.append(f"**复现路径**：`{it['repro']}`\n")
        lines.append("")
    else:
        lines.append("## 四、遗留问题清单\n\n本轮测试未发现遗留问题。\n")

    lines.append(KNOWN_LIMITS)
    return "\n".join(lines)


def main():
    banner()
    only = sys.argv[1:] or [s[0] for s in STAGES]
    t0 = time.time()
    errors = []

    for key, title, mod in STAGES:
        if key not in only:
            continue
        try:
            m = importlib.import_module(mod)
            importlib.reload(m)
            m.run()
        except Exception as e:
            import traceback
            errors.append((mod, traceback.format_exc()))
            R.add(f"{title} 阶段异常中断", False, f"{type(e).__name__}: {e}")

    dur = int((time.time() - t0) * 1000)
    total = R.passed + R.failed + R.env_failed
    print("\n" + "\033[1;95m" + "=" * 70)
    print(f"  测试完成：共 {total} 项 | \033[92m通过 {R.passed}\033[0m | "
          f"\033[91m失败 {R.failed}\033[0m | \033[93m跳过 {R.env_failed}\033[0m | "
          f"发现问题 {len(R.issues)} 个 | 耗时 {dur}ms")
    print("=" * 70 + "\033[0m")

    if R.failed:
        print("\n\033[91m失败用例：\033[0m")
        for phase, name, status, ms, detail in R.cases:
            if status == "FAIL":
                print(f"  [{phase}] {name} -> {detail}")

    # ⚠️ 只有**全量**运行才覆盖 E2E_REPORT.md。
    # 单阶段调试（`run_all.py admin`）以前也会写同一份文件，于是把上一次
    # 811 项的全量报告覆盖成「共 97 项」，git 里看起来像报告被删了一大半。
    # 部分阶段改写到 E2E_REPORT.partial.md，既有输出可看，又不动交付物。
    _full = set(only) == {s[0] for s in STAGES}

    # ---------------------------------------------------------------- 门禁
    # ⚠️ 只判 `R.failed == 0` 会放过两类「假绿」：
    #   1) 服务宕机/前置缺失 → 大量用例走 R.env 被跳过 → 失败仍是 0；
    #   2) 阶段被静默跳过 → 用例数骤降（811 → 200）→ 失败仍是 0。
    # 这两种情况下报告都显示「通过 N、失败 0」，门禁直接放行，非常危险。
    # 因此额外校验「跳过占比」与「用例数下限」。
    gate_errors = []
    # ① 「一条用例都没过」是最强的假绿信号：服务不可达时每条用例都走 R.env，
    #    样本量极小（常常只有 1 条），比例校验因样本不足而跳过，于是
    #    「通过 0、失败 0」竟然退出码 0 —— 门禁完全失效。
    #    实测：E2E_BASE 指向不存在的端口时，曾返回 EXIT=0。
    if R.passed == 0:
        gate_errors.append(
            f"零用例通过（共 {total} 项，全部为环境跳过）—— 服务很可能不可达，"
            f"请先确认 /health 正常")
    # ② 环境跳过占比（仅在有足够样本时统计，避免小样本误判）
    elif R.env_failed and total >= ENV_RATIO_MIN_SAMPLE:
        ratio = R.env_failed / total
        if ratio > ENV_SKIP_RATIO_MAX:
            gate_errors.append(
                f"环境跳过用例占比 {ratio:.1%} 超过上限 {ENV_SKIP_RATIO_MAX:.0%}"
                f"（{R.env_failed}/{total}）—— 多为服务不可达或前置数据缺失，"
                f"此时「失败 0」不代表通过")
    # 用例数下限只对**全量**有意义：单阶段天然少，不能拿来卡。
    if _full and R.passed < MIN_EXPECTED_CASES:
        gate_errors.append(
            f"通过用例数 {R.passed} 低于基线下限 {MIN_EXPECTED_CASES}"
            f"—— 疑似阶段被跳过或中途中断，不能视为通过")

    if gate_errors:
        print("\n\033[91m门禁未通过：\033[0m")
        for g in gate_errors:
            print(f"  ✘ {g}")

    if R.issues:
        print("\n\033[95m问题清单：\033[0m")
        for it in R.issues:
            print(f"  [{it['severity']}] {it['title']}")

    # 阶段异常中断的回溯必须打印：这是「用例数骤降」的常见原因，
    # 只报个数量下降而看不到栈，等于让人盲猜。
    for mod, tb in errors:
        print(f"\n\033[91m[{mod}] 异常：\033[0m\n{tb}")

    out = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "E2E_REPORT.md" if _full else "E2E_REPORT.partial.md")
    with open(out, "w", encoding="utf-8") as f:
        f.write(summary_md())
    print(f"\n报告已生成：{out}" + ("" if _full else "（部分阶段，未覆盖全量报告）"))
    return 0 if (R.failed == 0 and not gate_errors) else 1


if __name__ == "__main__":
    sys.exit(main())
