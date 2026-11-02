# -*- coding: utf-8 -*-
"""确定性测试数据生成脚本（QA 用）。

目标：生成「真实、合理、互相关联」的教学基础数据 + 用户数据，且
**无论在哪台机器 / 哪个环境运行，输出内容完全一致**（需求 #3）。

## 确定性保证（关键）
1. 固定随机种子 `SEED`：所有"随机"选择（姓名、分配）均可复现。
2. 固定基准时间 `BASE_TIME`：所有 created_at/updated_at 用同一常量，不调用 now()。
3. 固定密码盐 `DETERMINISTIC_SALT`：自己构造与 app `verify_password` 兼容的
   `pbkdf2_sha256$<salt>$<digest>` 哈希（app 的 `hash_password` 用随机 salt，
   若直接复用会导致每次哈希不同、违反"内容一致"，故此处用固定盐）。
4. 固定插入顺序：自增 ID 由插入顺序决定，顺序固定 → ID 也确定。
5. 先 `DELETE` 受管表、再按固定顺序 `INSERT`：无论本地/生产初始状态如何，
   最终落库内容完全相同。

## 生成范围
- 年级：9 个（1-9 年级，复用 init_db.GRADES）。
- 学科：按年级复用 init_db.SUBJECTS（共 59 个，含教材版本与 code）。
- 班级：按年级差异化（2-3 班，见 CLASSES_PER_GRADE，共 23 班），
  班主任由本年级教师轮流担任（同年级各班互异）。
- 用户：1 系统管理员 + 9 年级管理员（每级 1）+ 27 教师（每级 3，≥20）+ 184 学生
  （每班 8，≥200 要求下按 23 班计）。各自正确关联年级/学科/班级与角色。
- 授课关系：教师跨年级任教（不跨学段）。学段内按「同号班结对 / 年级环」分配：
  每班 2-3 位教师且至少来自 2 个不同年级，每位教师 ≤2 个班级（含 2 班年级
  时第 3 位教师挂对端同号班或第 1 班），本年级班主任必带本班，共 150 条。

## 安全
- 不触碰 `sys_role` / `sys_permission` / `sys_role_permission` 骨架（只按 code 关联）。
- 运行前若检测到业务表（试卷/题目/作业/提交等）已有数据，默认拒绝，需 `--force`。
- 可用 `--db sqlite:///path` 或环境变量 `DATABASE_URL` 指定目标库；默认临时库。

用法：
    python tools/gen_test_data.py --db sqlite:////tmp/test.db
    python tools/gen_test_data.py --db sqlite:////app/data/edu_platform.db --force
退出码 0 成功；非 0 失败。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import sys
from datetime import datetime
from typing import Dict

# 让脚本在「仓库内直接跑」与「容器内 PYTHONPATH=/app 跑」都能 import app
_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.dirname(_HERE)
_BACKEND = os.path.join(_REPO, "backend")
if os.path.isdir(_BACKEND) and _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

from sqlalchemy import create_engine, select, func, text  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.core.database import Base  # noqa: E402
from app.models import (  # noqa: E402
    Class, Grade, Role, Subject, TeachingAssignment,
    User, UserRole,
)
from app.services.init_db import GRADES, SUBJECTS, init_permissions, init_roles  # noqa: E402


# ---------------------------------------------------------------- 确定性常量
SEED = 20261030
BASE_TIME = datetime(2026, 9, 1, 8, 0, 0)
DETERMINISTIC_SALT = "0" * 32  # 16 字节，与 verify_password 的 bytes.fromhex(salt) 对齐
DEFAULT_PASSWORD = "Test@123456"  # 满足 app 强度校验（长度+字母数字+非弱口令）

# 班级数按年级差异化（2-3 班）：真实学校各年级招生规模不同，
# 全部固定 3 班不真实。上限受 TEACHERS_PER_GRADE 约束（班主任须同年级互异）。
CLASSES_PER_GRADE = {
    1: 3, 2: 3, 3: 2, 4: 2, 5: 3, 6: 2,
    7: 3, 8: 2, 9: 3,
}
TEACHERS_PER_GRADE = 3
STUDENTS_PER_CLASS = 8

# 业务表保护：这些表非空时默认拒绝（避免误清真实数据）
_PROTECTED_TABLES = [
    "edu_paper", "edu_question", "edu_task", "edu_submission",
    "edu_review_plan", "edu_study_record", "edu_wrong_question",
    "edu_lesson_plan", "edu_note",
]


# ---------------------------------------------------------------- 姓名素材
_SURNAMES = list(
    "王李张刘陈杨黄赵周吴徐孙马朱胡郭何高林罗郑梁谢宋唐许韩冯邓曹彭曾"
    "萧田董袁潘于蒋蔡余杜叶程苏魏吕丁任沈姚卢傅钟姜崔谭廖范汪陆金石戴贾"
)
_GIVEN = [
    "伟", "芳", "娜", "秀英", "敏", "静", "丽", "强", "磊", "洋", "勇", "艳",
    "杰", "娟", "涛", "明", "超", "霞", "平", "刚", "桂英", "文", "博", "宇",
    "浩", "欣", "怡", "轩", "睿", "涵", "悦", "晨", "嘉", "泽", "思", "雨",
    "佳", "阳", "雪", "琳", "婷", "昊", "宁", "帆", "彤", "璐", "萌", "琪",
    "源", "辰", "熙", "然", "恩", "悦", "鑫", "岚", "峥", "朗",
]


# ---------------------------------------------------------------- 工具
def make_hash(password: str, salt: str = DETERMINISTIC_SALT) -> str:
    """构造与 app.security.verify_password 兼容的确定性哈希。

    格式：pbkdf2_sha256$<salt>$<digest>，盐固定 → 同一口令永远得到同一哈希。
    """
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"),
                             bytes.fromhex(salt), 100_000)
    return f"pbkdf2_sha256${salt}${dk.hex()}"


def _bootstrap_if_needed(engine) -> None:
    """若目标库尚未建表，先建表并播种 RBAC 骨架（幂等、确定性）。"""
    with Session(engine) as db:
        has_grade = db.scalar(
            text("SELECT name FROM sqlite_master "
                 "WHERE type='table' AND name='edu_grade'")
        )
        if has_grade is None:
            Base.metadata.create_all(engine)
            init_permissions(db)
            init_roles(db)
            db.commit()
        elif db.scalar(select(func.count()).select_from(Role)) == 0:
            # 表在但角色缺失：补骨架
            init_permissions(db)
            init_roles(db)
            db.commit()


def _refuse_if_protected(engine, force: bool) -> None:
    with Session(engine) as db:
        for t in _PROTECTED_TABLES:
            n = db.scalar(text(f"SELECT COUNT(*) FROM {t}"))
            if n:
                if not force:
                    raise SystemExit(
                        f"✗ 业务表 {t} 已有 {n} 行数据；"
                        f"清库将丢失真实数据。确认要重置请加 --force。"
                    )
                print(f"  ! --force：忽略 {t} 现有 {n} 行（受管表仍会被重置）")


def _reset_managed(db: Session) -> None:
    """按 FK 安全顺序清空受管表（子表先于父表）。"""
    for model in (UserRole, TeachingAssignment, User, Class, Subject, Grade):
        db.query(model).delete()
    db.commit()


def _role_id(db: Session, code: str) -> int | None:
    return db.scalar(select(Role.id).where(Role.code == code))


def _sha256_of(manifest: list) -> str:
    """对生成内容的规范化序列化做哈希，用于证明跨环境一致性。"""
    payload = json.dumps(manifest, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------- 生成
def generate(db: Session, rng: random.Random, manifest: list) -> dict:
    """生成全部确定性数据，并把结构化内容追加进 manifest。"""
    # 1) 年级
    grades = []
    for name, stage, num in GRADES:
        g = Grade(name=name, stage=stage, grade_num=num, is_active=True, sort=num)
        db.add(g)
        grades.append(g)
    db.flush()
    for g in grades:
        manifest.append({"t": "grade", "id": g.id, "name": g.name,
                         "stage": g.stage, "grade_num": g.grade_num})

    grade_by_num = {g.grade_num: g for g in grades}

    # 2) 学科（按年级复用规范 SUBJECTS）
    subjects = []
    for num, subs in SUBJECTS.items():
        g = grade_by_num.get(num)
        if not g:
            continue
        for i, (sname, version) in enumerate(subs):
            s = Subject(name=sname, textbook_version=version, grade_id=g.id,
                        code=f"{num}_{sname}", is_active=True, sort=i)
            db.add(s)
            subjects.append(s)
    db.flush()
    for s in subjects:
        manifest.append({"t": "subject", "id": s.id, "name": s.name,
                         "grade_id": s.grade_id, "code": s.code})

    # 3) 用户：管理员 / 年级管理员 / 教师
    users = {}  # key -> User
    pw_hash = make_hash(DEFAULT_PASSWORD)

    admin = User(
        username="admin", password=pw_hash, real_name="系统管理员",
        identity="sys_admin", status="active", school_name="示范学校",
        gender="未知", must_change_password=False,
        created_at=BASE_TIME, updated_at=BASE_TIME,
    )
    db.add(admin)
    db.flush()
    users["admin"] = admin
    manifest.append({"t": "user", "id": admin.id, "username": admin.username,
                     "identity": admin.identity, "grade_id": None,
                     "class_id": None, "grade_admin_grade_id": None,
                     "password": admin.password, "status": admin.status,
                     "must_change_password": admin.must_change_password})

    teachers_by_grade = {g.grade_num: [] for g in grades}
    teacher_seq = 0
    for g in grades:
        # 年级管理员
        # 占位随机 draw：消耗固定随机序列、保证指纹跨环境稳定；姓名不落库
        # （real_name 用年级占位名，便于 QA 肉眼核对归属）。删掉会移动后续
        # 全部随机结果、改变确定性指纹 —— 别删。
        rng.choice(_SURNAMES)
        rng.choice(_GIVEN)
        ga = User(
            username=f"gradeadmin{g.grade_num}", password=pw_hash,
            real_name=f"{g.name}管理员", identity="grade_admin", status="active",
            school_name="示范学校", gender=("男" if g.grade_num % 2 else "女"),
            grade_id=g.id, grade_admin_grade_id=g.id, must_change_password=False,
            created_at=BASE_TIME, updated_at=BASE_TIME,
        )
        db.add(ga)
        db.flush()
        users[f"ga_{g.grade_num}"] = ga
        manifest.append({"t": "user", "id": ga.id, "username": ga.username,
                         "identity": ga.identity, "grade_id": ga.grade_id,
                         "class_id": ga.class_id,
                         "grade_admin_grade_id": ga.grade_admin_grade_id,
                         "password": ga.password, "status": ga.status,
                         "must_change_password": ga.must_change_password})

        # 教师
        for _ in range(TEACHERS_PER_GRADE):
            teacher_seq += 1
            tname = rng.choice(_SURNAMES) + rng.choice(_GIVEN)
            t = User(
                username=f"teacher{teacher_seq:03d}", password=pw_hash,
                real_name=tname, identity="teacher",
                status="active", school_name="示范学校",
                gender=("男" if teacher_seq % 2 else "女"),
                grade_id=g.id, must_change_password=False,
                created_at=BASE_TIME, updated_at=BASE_TIME,
            )
            db.add(t)
            db.flush()
            teachers_by_grade[g.grade_num].append(t)
            users[f"t_{g.grade_num}_{teacher_seq}"] = t
            manifest.append({"t": "user", "id": t.id, "username": t.username,
                             "identity": t.identity, "grade_id": t.grade_id,
                             "class_id": None, "grade_admin_grade_id": None,
                             "password": t.password, "status": t.status,
                             "must_change_password": t.must_change_password})

    # 4) 班级（每级 3 个），班主任按班级序号在该级教师中轮询 → 每班班主任不同
    classes = []
    for g in grades:
        tlist = teachers_by_grade[g.grade_num]
        for c in range(1, CLASSES_PER_GRADE[g.grade_num] + 1):
            head = tlist[(c - 1) % len(tlist)] if tlist else None
            k = Class(name=f"{g.name}({c})班", grade_id=g.id,
                      head_teacher_id=head.id if head else None,
                      is_active=True, remark=f"自动化测试班级 {g.grade_num}-{c}",
                      created_at=BASE_TIME)
            db.add(k)
            classes.append((k, g, c))
    db.flush()
    for k, g, c in classes:
        manifest.append({"t": "class", "id": k.id, "name": k.name,
                         "grade_id": k.grade_id,
                         "head_teacher_id": k.head_teacher_id})

    # 5) 学生（每班 8 人），正确关联年级与班级
    student_seq = 0
    for k, g, c in classes:
        for s in range(1, STUDENTS_PER_CLASS + 1):
            student_seq += 1
            # 占位随机 draw（理由同上：维持随机序列，别删）
            rng.choice(_SURNAMES)
            rng.choice(_GIVEN)
            stu = User(
                username=f"stu{g.grade_num:02d}{c:02d}{s:02d}",
                password=pw_hash, real_name=f"{g.name}学生{student_seq}",
                identity="student", status="active", school_name="示范学校",
                gender=("男" if student_seq % 2 else "女"),
                grade_id=g.id, class_id=k.id, must_change_password=False,
                created_at=BASE_TIME, updated_at=BASE_TIME,
            )
            db.add(stu)
            db.flush()
            manifest.append({"t": "user", "id": stu.id, "username": stu.username,
                             "identity": stu.identity, "grade_id": stu.grade_id,
                             "class_id": stu.class_id,
                             "grade_admin_grade_id": None,
                             "password": stu.password, "status": stu.status,
                             "must_change_password": stu.must_change_password})

    # 6) 授课关系（教师跨年级任教，不跨学段；每位教师最多带 2 个班级）
    # --------------------------------------------------------------
    # 班级数按年级差异化（CLASSES_PER_GRADE），算法需同时兼容 2 班/3 班：
    #   - 偶数年级（小学 1-6）两两结对 (1,2)(3,4)(5,6)：第 k 号班的两位教师
    #     固定为「A 年级第 k 位 + B 年级第 k 位」，两边互为跨年级授课；
    #   - 奇数年级（初中 7-9）按年级环轮转：G 的教师 k → G(k)班 + 下一级(k)班，
    #     班级 k 的两位教师 = 本级 k + 上一级 k（9→7 收尾，贴合升学带班）；
    #   - 某年级只有 2 班时，第 3 位教师改挂到对端同级号班；两端都无同号班
    #     （均为 2 班且 k=3）时挂到对端第 1 班（该班会有 3 位教师，允许）。
    #   结果：每班 2-3 位教师且至少来自 2 个不同年级；每位教师 ≤2 个班级；
    #   班主任（本级第 k 位教师）必带本班；班级内学科在教师间轮询；全覆盖。
    # 约束锚点：teacher.grade_id 仍记「归属年级」，TeachingAssignment.grade_id
    #   记班级所属年级，二者可不同级但必同学段。
    ta_count = 0
    classes_by_grade: Dict[int, list] = {}
    for k, g, _c in classes:
        classes_by_grade.setdefault(g.grade_num, []).append(k)

    slots: list = []  # (teacher, class)

    def _slot(t, c):
        if t is not None and c is not None:
            slots.append((t, c))

    def _pair(ga, gb):
        ta = teachers_by_grade[ga.grade_num]
        tb = teachers_by_grade[gb.grade_num]
        ca = classes_by_grade[ga.grade_num]
        cb = classes_by_grade[gb.grade_num]
        for k in range(1, max(len(ta), len(tb)) + 1):
            ak = ta[k - 1] if k <= len(ta) else None
            bk = tb[k - 1] if k <= len(tb) else None
            ha = ca[k - 1] if k <= len(ca) else None
            hb = cb[k - 1] if k <= len(cb) else None
            # 同号班配对：A_k 教 A(k)+B(k)，B_k 教 B(k)+A(k)；两端都无同号班时
            # （均为 2 班且 k=3）只挂到对端第 1 班一次（否则会出现单班 4 师）
            for t, own, partner, idle_to in (
                    (ak, ha, hb, cb[0] if cb else None),
                    (bk, hb, ha, ca[0] if ca else None)):
                if t is None:
                    continue
                if own is not None:
                    _slot(t, own)
                if partner is not None:
                    _slot(t, partner)
                if own is None and partner is None:
                    _slot(t, idle_to)

    def _cycle(glist):
        n = len(glist)
        for j, g in enumerate(glist):
            gnext = glist[(j + 1) % n]
            tg = teachers_by_grade[g.grade_num]
            cg = classes_by_grade[g.grade_num]
            cn = classes_by_grade[gnext.grade_num]
            for k in range(1, len(tg) + 1):
                t = tg[k - 1]
                own = cg[k - 1] if k <= len(cg) else None
                nxt = cn[k - 1] if k <= len(cn) else None
                if own is not None:
                    _slot(t, own)
                if nxt is not None:
                    _slot(t, nxt)
                if own is None and nxt is None:
                    _slot(t, cg[0] if cg else None)

    # ⚠️ 必须用确定序遍历学段：set 迭代序受 PYTHONHASHSEED 影响，
    # 会直接打碎跨环境指纹（差点上线）。
    for stage in sorted({g.stage for g in grades}):
        glist = sorted((g for g in grades if g.stage == stage),
                       key=lambda x: x.grade_num)
        if len(glist) % 2 == 0:
            for i in range(0, len(glist), 2):
                _pair(glist[i], glist[i + 1])
        else:
            _cycle(glist)

    # class_id -> [teacher, ...]（同一班级内按插入序轮询分科）
    class_teachers: Dict[int, list] = {}
    for t, c in slots:
        bucket = class_teachers.setdefault(c.id, [])
        if t not in bucket:
            bucket.append(t)

    for k, g, _c in classes:
        grade_obj = grade_by_num[g.grade_num]
        subs = [s for s in subjects if s.grade_id == grade_obj.id]
        tlist = class_teachers.get(k.id, [])
        for idx, s in enumerate(subs):
            if not tlist:
                continue
            teacher = tlist[idx % len(tlist)]
            ta = TeachingAssignment(
                teacher_id=teacher.id, class_id=k.id, subject_id=s.id,
                grade_id=grade_obj.id, school_year="2026-2027",
                is_active=True, created_at=BASE_TIME,
            )
            db.add(ta)
            ta_count += 1
            manifest.append({"t": "teach", "teacher_id": teacher.id,
                             "class_id": k.id, "subject_id": s.id,
                             "grade_id": grade_obj.id})
    db.flush()

    # 7) 角色关联（按 code 取 ID，跨环境稳定）
    links = [
        ("admin", "sys_admin"),
        *[(f"ga_{g.grade_num}", "grade_admin") for g in grades],
        *[(f"t_{g.grade_num}_{i}", "teacher")
          for g in grades for i in range(1, len(teachers_by_grade[g.grade_num]) + 1)],
    ]
    # 学生角色链接：所有 identity=student 的用户
    student_ids = [u["id"] for u in manifest if u["t"] == "user" and u["identity"] == "student"]
    role_links = []
    for key, code in links:
        u = users.get(key)
        rid = _role_id(db, code)
        if u and rid:
            db.add(UserRole(user_id=u.id, role_id=rid))
            role_links.append((u.id, rid))
    for sid in student_ids:
        rid = _role_id(db, "student")
        if rid:
            db.add(UserRole(user_id=sid, role_id=rid))
            role_links.append((sid, rid))
    db.flush()
    for uid, rid in role_links:
        manifest.append({"t": "user_role", "user_id": uid, "role_id": rid})

    db.commit()
    return {
        "grades": len(grades),
        "subjects": len(subjects),
        "classes": len(classes),
        "teachers": sum(len(v) for v in teachers_by_grade.values()),
        "grade_admins": len(grades),
        "students": student_seq,
        "teaching_assignments": ta_count,
        "user_roles": len(role_links),
    }


# ---------------------------------------------------------------- 主流程
def main() -> int:
    ap = argparse.ArgumentParser(description="确定性教学测试数据生成器")
    ap.add_argument("--db", default=None,
                    help="目标库 URL，如 sqlite:////tmp/test.db；缺省取环境变量 DATABASE_URL，再缺省为临时库")
    ap.add_argument("--force", action="store_true",
                    help="即使业务表已有数据也继续（会重置受管表）")
    args = ap.parse_args()

    db_url = args.db or os.environ.get("DATABASE_URL") or "sqlite:////tmp/gen_test_data_tmp.db"
    engine = create_engine(db_url, future=True, connect_args={"check_same_thread": False})

    print(f"目标库：{db_url}")
    _bootstrap_if_needed(engine)
    _refuse_if_protected(engine, args.force)

    rng = random.Random(SEED)
    manifest: list = []
    with Session(engine) as db:
        print("→ 重置受管表（grade/subject/class/teaching/user/user_role）…")
        _reset_managed(db)
        print("→ 生成数据…")
        stats = generate(db, rng, manifest)

    digest = _sha256_of(manifest)
    print("\n===== 生成结果 =====")
    for k, v in stats.items():
        print(f"  {k:22s}: {v}")
    print(f"  总用户数            : {stats['grade_admins'] + stats['teachers'] + stats['students'] + 1}")
    print(f"\n★ 确定性指纹(sha256) : {digest}")
    print("  （在任何机器/环境运行，只要输入相同，该指纹必须一致）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
