#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试数据确定性门禁：生成器两次运行指纹一致 + 关联不变式全绿。

## 为什么需要它

tools/gen_test_data.py 是 QA 铺底数据的唯一来源，其核心承诺是
「任何机器/环境运行，输出内容完全一致」。这个承诺此前只靠
人工跑两次比对（deploy_scripts/verify_gen_determinism.py，在仓库外）
来守护 —— 改一次生成逻辑就要记得手动验一次，忘了就带着
非确定性或坏关联上生产（真实发生过：同年级班主任全同、
单年级 3 师扛 7~10 门课的过载分配，2026-10-30 / 11-02 各修一轮）。

本门禁把「确定性 + 合理性」固化进 CI：
  1) 同一环境内连续两次生成（两个独立临时库）→ 指纹必须一致；
  2) 对每个库做关联不变式断言：
     - 行数契约：9 年级 / 59 学科 / 27 班 / 27 师 / 216 生 / 177 授课；
     - 结构不变式：学生-班级-年级一致、授课-班级年级一致、
       学科/班级不悬空、同年级各班班主任互异（bad_head）；
     - 任课约束（2026-11-02 重构引入）：不跨学段（小学1-6/初中7-9）、
       每位教师带班 ≤2、(班级,学科) 对全覆盖无缺口。
  3) 任一断言失败立即非零退出，阻止带病数据模型合入。

⚠️ 与 deploy_scripts/run_gen_prod.py 的 EXPECTED_FINGERPRINT 分工：
   那里钉「生产铺底时的具体内容指纹」（内容变更需人工确认后更新），
   这里只锁「确定性 + 约束满足」，不钉具体指纹 —— 否则每次合理的
   数据模型演进都会误杀 CI。

⚠️ 维护提示：行数期望值来自 init_db 的 GRADES/SUBJECTS 与本生成器常量
   （每级 3 班 3 师、每班 8 生）。若有意调整这些源头，请同步更新
   EXPECTED，别为了让 CI 变绿而盲改。

## 用法

    python tools/check_gen_data_determinism.py           # 常规校验
    python tools/check_gen_data_determinism.py --keep    # 保留临时库便于排查
    python tools/check_gen_data_determinism.py --gen X   # 指定生成器（反向验证用：
                                                         #   喂入已知有 bug 的变体，
                                                         #   门禁必须能红）

退出码：0 = 通过；1 = 指纹不一致或不变式失败；2 = 运行异常
"""
import argparse
import os
import re
import sqlite3
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_GEN = os.path.join(ROOT, "tools", "gen_test_data.py")

# ---- 行数契约（与 init_db.GRADES/SUBJECTS 及生成器常量联动）----
EXPECTED = {
    "grades": 9,        # GRADES：1-9 年级
    "subjects": 59,     # SUBJECTS 全年级合计（1-5 级各 5 门、6/7 级 7 门、8/9 级 10 门）
    "classes": 23,      # CLASSES_PER_GRADE 差异化合计（3+3+2+2+3+2+3+2+3）
    "teachers": 27,     # 每级 3 师 × 9
    "students": 184,    # 每班 8 生 × 23 班
    "teaching": 150,    # 全部 (班级,学科) 对：小学 79 + 初中 71
}

FINGERPRINT_RE = re.compile(r"^[0-9a-f]{64}$")


def _db_url(path: str) -> str:
    """Windows/Linux 通吃的 sqlite 绝对路径 URL（正斜杠，三斜杠前缀）。"""
    return "sqlite:///" + path.replace("\\", "/")


def _run_generator(gen_path: str, db_path: str) -> str:
    """跑一次生成器，返回 stdout（失败抛 RuntimeError）。"""
    proc = subprocess.run(
        [sys.executable, gen_path, "--db", _db_url(db_path)],
        capture_output=True, text=True, timeout=300, cwd=ROOT,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"生成器退出码 {proc.returncode}\n[stdout 尾部]\n{proc.stdout[-800:]}"
            f"\n[stderr 尾部]\n{proc.stderr[-800:]}"
        )
    return proc.stdout


def _fingerprint_of(stdout: str) -> str:
    for line in stdout.splitlines():
        if "确定性指纹" in line and ":" in line:
            fp = line.split(":")[-1].strip()
            if FINGERPRINT_RE.match(fp):
                return fp
    raise RuntimeError("stdout 中未找到合法指纹（64 位十六进制）")


def _one(cur: sqlite3.Cursor, sql: str) -> int:
    return cur.execute(sql).fetchone()[0]


def _check_invariants(db_path: str, label: str) -> None:
    """对一个生成结果库断言全部不变式；失败抛 AssertionError。"""
    con = sqlite3.connect(f"file:{db_path.replace(chr(92), '/')}?mode=ro", uri=True)
    try:
        cur = con.cursor()
        # ---- 行数契约 ----
        actual = {
            "grades": _one(cur, "SELECT COUNT(*) FROM edu_grade"),
            "subjects": _one(cur, "SELECT COUNT(*) FROM edu_subject"),
            "classes": _one(cur, "SELECT COUNT(*) FROM edu_class"),
            "teachers": _one(cur, "SELECT COUNT(*) FROM sys_user WHERE identity='teacher'"),
            "students": _one(cur, "SELECT COUNT(*) FROM sys_user WHERE identity='student'"),
            "teaching": _one(cur, "SELECT COUNT(*) FROM edu_teaching_assignment"),
        }
        for key, want in EXPECTED.items():
            assert actual[key] == want, (
                f"{label}: {key} 期望 {want} 实得 {actual[key]}"
                f"（若有意调整 SUBJECTS/生成常量，请同步更新本门禁 EXPECTED）"
            )
        # ---- 结构不变式 ----
        bad_stu = _one(cur, "SELECT COUNT(*) FROM sys_user u JOIN edu_class c "
                            "ON u.class_id=c.id WHERE u.identity='student' "
                            "AND u.grade_id<>c.grade_id")
        assert bad_stu == 0, f"{label}: {bad_stu} 个学生班级归属与年级不一致"
        bad_ta = _one(cur, "SELECT COUNT(*) FROM edu_teaching_assignment t "
                           "JOIN edu_class c ON t.class_id=c.id "
                           "WHERE t.grade_id<>c.grade_id")
        assert bad_ta == 0, f"{label}: {bad_ta} 条授课记录的年级与班级不一致"
        bad_sub = _one(cur, "SELECT COUNT(*) FROM edu_subject WHERE grade_id IS NULL")
        assert bad_sub == 0, f"{label}: {bad_sub} 个学科悬空（无年级）"
        bad_cls = _one(cur, "SELECT COUNT(*) FROM edu_class WHERE grade_id IS NULL")
        assert bad_cls == 0, f"{label}: {bad_cls} 个班级悬空（无年级）"
        bad_head = _one(cur, "SELECT COUNT(*) FROM (SELECT grade_id FROM edu_class "
                             "GROUP BY grade_id HAVING COUNT(DISTINCT head_teacher_id) "
                             "< COUNT(*))")
        assert bad_head == 0, f"{label}: {bad_head} 个年级存在多班同一班主任"
        # ---- 任课约束（2026-11-02 重构）----
        bad_cross = _one(cur, "SELECT COUNT(*) FROM edu_teaching_assignment t "
                              "JOIN sys_user u ON t.teacher_id=u.id "
                              "JOIN edu_class c ON t.class_id=c.id "
                              "JOIN edu_grade g1 ON u.grade_id=g1.id "
                              "JOIN edu_grade g2 ON c.grade_id=g2.id "
                              "WHERE g1.stage<>g2.stage")
        assert bad_cross == 0, f"{label}: {bad_cross} 条授课跨学段（小学/初中混排）"
        max_cls = _one(cur, "SELECT COALESCE(MAX(cnt),0) FROM "
                            "(SELECT teacher_id, COUNT(DISTINCT class_id) cnt "
                            "FROM edu_teaching_assignment GROUP BY teacher_id)")
        assert max_cls <= 2, f"{label}: 存在教师带 {max_cls} 个班级（约束上限 2）"
        # 跨年级任教（班级粒度必须成立）：每个班级至少 2 位教师、且至少来自
        # 2 个不同年级。班级数差异化（2-3 班/年级）后，部分教师只带 1 个班
        # （单年级）不可避免，故教师粒度放宽为「占比不超过 1/3」。
        bad_same_grade_class = _one(cur, "SELECT COUNT(*) FROM ("
            "SELECT t.class_id FROM edu_teaching_assignment t "
            "JOIN sys_user u ON u.id=t.teacher_id "
            "GROUP BY t.class_id "
            "HAVING COUNT(DISTINCT t.teacher_id) < 2 "
            "OR COUNT(DISTINCT u.grade_id) < 2)")
        assert bad_same_grade_class == 0, (
            f"{label}: {bad_same_grade_class} 个班级的教师不足 2 人或来自单一年级")
        total_teachers = _one(cur, "SELECT COUNT(*) FROM sys_user WHERE identity='teacher'")
        single_grade = _one(cur, "SELECT COUNT(*) FROM ("
                                 "SELECT teacher_id FROM edu_teaching_assignment "
                                 "GROUP BY teacher_id "
                                 "HAVING COUNT(DISTINCT grade_id) < 2)")
        assert single_grade <= max(1, total_teachers // 3), (
            f"{label}: {single_grade}/{total_teachers} 名教师只在单一年级任教，"
            f"超过 1/3 上限（跨年级设计被破坏）")
        pairs = _one(cur, "SELECT COUNT(*) FROM edu_class c JOIN edu_subject s "
                          "ON s.grade_id=c.grade_id")
        assigned = _one(cur, "SELECT COUNT(*) FROM (SELECT DISTINCT class_id, "
                             "subject_id FROM edu_teaching_assignment)")
        assert pairs == assigned == EXPECTED["teaching"], (
            f"{label}: 课程覆盖缺口 pairs={pairs} assigned={assigned} "
            f"期望={EXPECTED['teaching']}"
        )
        print(f"  [{label}] 不变式全绿：行数契约 ✓ 班主任互异 ✓ "
              f"不跨学段 ✓ 每师≤{max_cls}班 ✓ 每班跨年级 ✓ "
              f"覆盖 {assigned}/{pairs} ✓")
    finally:
        con.close()


def main() -> int:
    ap = argparse.ArgumentParser(description="测试数据确定性门禁")
    ap.add_argument("--gen", default=DEFAULT_GEN,
                    help="生成器脚本路径（默认 tools/gen_test_data.py）")
    ap.add_argument("--keep", action="store_true", help="保留临时库便于排查")
    args = ap.parse_args()

    if not os.path.isfile(args.gen):
        print(f"[FAIL] 生成器不存在: {args.gen}")
        return 2

    tmpdir = tempfile.mkdtemp(prefix="gen_gate_")
    db1 = os.path.join(tmpdir, "run1.db")
    db2 = os.path.join(tmpdir, "run2.db")
    try:
        # 1) 两次独立生成
        try:
            out1 = _run_generator(args.gen, db1)
            out2 = _run_generator(args.gen, db2)
        except RuntimeError as exc:
            print(f"[FAIL] 生成器运行失败：{exc}")
            return 2
        fp1 = _fingerprint_of(out1)
        fp2 = _fingerprint_of(out2)
        print(f"  run1 指纹: {fp1}")
        print(f"  run2 指纹: {fp2}")

        # 2) 确定性：两次指纹必须一致
        if fp1 != fp2:
            print("[FAIL] 两次运行指纹不一致 → 生成器存在非确定性！")
            print("       排查方向：随机源是否用了全局 random / 时间是否取了 now() /")
            print("       salt 是否固定。修好前不要合入。")
            return 1
        print("  [OK] 两次指纹一致 → 确定性成立")

        # 3) 关联不变式（两个库都查，防止「校验的库和比对的不知是谁」）
        _check_invariants(db1, "run1")
        _check_invariants(db2, "run2")

        print("[OK] 测试数据确定性门禁通过（指纹一致 + 行数契约 + 关联不变式）")
        return 0
    except AssertionError as exc:
        print(f"[FAIL] {exc}")
        return 1
    finally:
        if args.keep:
            print(f"  临时库已保留: {db1} , {db2}")
        else:
            import shutil
            shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
