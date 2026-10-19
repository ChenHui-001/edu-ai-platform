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

STAGES = [
    ("admin", "阶段一 · 管理员视角", "test_admin"),
    ("teacher", "阶段二 · 教师建题组卷", "test_teacher"),
    ("student", "阶段三 · 学生答题与 AI 批改", "test_student"),
    ("learning", "阶段四 · 学习中心专项", "test_learning"),
    ("requirements", "阶段五 · 需求覆盖补充", "test_requirements"),
    ("teaching_mgmt", "阶段六 · 教师端教学管理专项", "test_teaching_mgmt"),
    ("lesson_plan", "阶段七 · 教师端教案管理专项", "test_lesson_plan"),
]


def banner():
    print("\033[1;95m" + "#" * 70)
    print("#   九年义务教育 AI 学习管理系统 · 端到端自动化测试")
    print("#   admin → teacher1 → stu731 全链路验证")
    print("#" * 70 + "\033[0m")


def summary_md():
    lines = []
    lines.append("# 端到端自动化测试报告\n")
    lines.append(f"> 生成时间：{time.strftime('%Y-%m-%d %H:%M:%S')}　|　"
                 f"总计 **{R.passed + R.failed}** 项：通过 **{R.passed}**，失败 **{R.failed}**\n")

    by_phase = {}
    for phase, name, status, ms, detail in R.cases:
        by_phase.setdefault(phase, []).append((name, status, ms, detail))

    lines.append("## 一、测试概览\n")
    lines.append("| 阶段 | 用例数 | 通过 | 失败 | 通过率 |")
    lines.append("|------|-------:|-----:|-----:|-------:|")
    for phase, rows in by_phase.items():
        p = sum(1 for r in rows if r[1] == "PASS")
        f = len(rows) - p
        rate = round(p / len(rows) * 100, 1) if rows else 0
        lines.append(f"| {phase} | {len(rows)} | {p} | {f} | {rate}% |")
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
    print("\n" + "\033[1;95m" + "=" * 70)
    print(f"  测试完成：共 {R.passed + R.failed} 项 | \033[92m通过 {R.passed}\033[0m | "
          f"\033[91m失败 {R.failed}\033[0m | 发现问题 {len(R.issues)} 个 | 耗时 {dur}ms")
    print("=" * 70 + "\033[0m")

    if R.failed:
        print("\n\033[91m失败用例：\033[0m")
        for phase, name, status, ms, detail in R.cases:
            if status == "FAIL":
                print(f"  [{phase}] {name} -> {detail}")

    if R.issues:
        print("\n\033[95m问题清单：\033[0m")
        for it in R.issues:
            print(f"  [{it['severity']}] {it['title']}")

    for mod, tb in errors:
        print(f"\n\033[91m[{mod}] 异常：\033[0m\n{tb}")

    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "E2E_REPORT.md")
    with open(out, "w", encoding="utf-8") as f:
        f.write(summary_md())
    print(f"\n报告已生成：{out}")
    return 0 if R.failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
