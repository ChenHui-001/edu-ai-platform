#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""确保三个「固定验收账号」存在且可用 —— 幂等，可反复执行。

## 为什么要这个脚本

项目需要**三个长期固定**的账号（管理员 / 教师 / 学生），密码永不变化，
用于日常使用与测试。但账号是**数据**，不是代码：

- 换环境（阶段 1 迁 PostgreSQL、开发机重建库）后，账号会丢；
- 手工重建容易漏绑角色 / 班级 / 授课关系，导致「能登录但什么都看不到」；
- 密码写在代码里会泄露，写在文档里又容易和实际不符。

这个脚本把「账号该长什么样」固化成代码：跑一次就把账号、角色、
班级、授课关系全部对齐，密码从**受控来源**读，不落进代码与文档。

## 密码来源（优先级从高到低）

1. `--password-file <路径>`：服务器上的受限文件（0600），推荐。
2. 环境变量 `ACCEPTANCE_PASSWORD`。
3. `ACCEPTANCE_PASSWORD_FILE` 环境变量指向的文件。
4. 都没有 → 报错退出（**绝不**回退到弱默认口令）。

## 为什么口令可以长期固定而不违背安全要求

这三个账号是**私有验收账号**：不对公网开放用途，密码保存在
仓库外的受限文件里，且：
- `must_change_password` 强制置 False（否则每次登录都要改，违背「固定」）；
- 锁定状态与失败计数每次执行时清零（避免测试中输错导致账号被锁）；
- 脚本只重置密码哈希，**不打印**密码。

真实生产用户仍走正常注册 + 审批 + 首登改密流程，不受影响。

## 用法

    # 服务器上（密码文件已放在 /opt/edu-ai-platform/.acceptance_password，chmod 600）
    python tools/ensure_acceptance_accounts.py --password-file /opt/edu-ai-platform/.acceptance_password

    # 本地开发
    python tools/ensure_acceptance_accounts.py --password-file D:/secure/pwd.txt

    # 只看会做什么，不写库
    python tools/ensure_acceptance_accounts.py --password-file ... --dry-run

退出码：0 成功 / 1 参数或环境错误 / 2 数据库操作失败
"""
from __future__ import annotations

import argparse
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _locate_backend_root() -> str:
    """找到「装着 app 包」的根目录。

    脚本本体的位置不可靠：仓库里是 `<repo>/tools/x.py`，但生产环境是把它
    `docker cp` 进容器跑（`/tmp/x.py`），此时按脚本位置推算出来的根目录
    根本不存在 `app/` —— 表现是 `ModuleNotFoundError: No module named
    'app.core'`，而脚本已经进了容器、路径却指错了地方。

    判据只有一个：**哪个目录下真的存在 `app/core/database.py`**。
    候选顺序：脚本的仓库根 → 脚本同级的父目录 → 当前工作目录 → 容器内
    的 /app。命中即用；全不命中就退回脚本的仓库根（让报错信息指向
    真正缺失的东西，而不是路径猜错）。
    """
    here = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        ROOT,
        os.path.dirname(here),
        os.getcwd(),
        os.path.join(os.getcwd(), "backend"),
        os.path.dirname(os.getcwd()),
        "/app",
    ]
    for cand in candidates:
        if cand and os.path.isfile(os.path.join(cand, "app", "core", "database.py")):
            return cand
    return ROOT


BACKEND_ROOT = _locate_backend_root()
for _p in (BACKEND_ROOT, os.path.join(BACKEND_ROOT, "backend")):
    if _p and os.path.isdir(_p) and _p not in sys.path:
        sys.path.insert(0, _p)

# ---- 三个固定账号的定义（唯一真源）----
# identity  : sys_admin / teacher / student
# role_code : sys_role.code
# class_name: 教师与学生绑定的班级（同一个班，教师才看得到学生）
# subject   : 教师授课的学科
ACCOUNTS = [
    {
        "username": "owner_admin",
        "real_name": "验收管理员",
        "identity": "sys_admin",
        "role_code": "sys_admin",
        "class_name": None,
        "subject_name": None,
    },
    {
        "username": "owner_teacher",
        "real_name": "验收教师",
        "identity": "teacher",
        "role_code": "teacher",
        "class_name": "一年级(1)班",
        "subject_name": "数学",
    },
    {
        "username": "owner_student",
        "real_name": "验收学生",
        "identity": "student",
        "role_code": "student",
        "class_name": "一年级(1)班",
        "subject_name": None,
    },
]


def read_passwords(args) -> dict:
    """从受控来源读口令；读不到就报错，不回退到弱默认值。

    支持两种文件格式：
    1. **每行一个**（顺序：管理员 / 教师 / 学生）—— 简单直接，推荐；
    2. **key=value**（`owner_admin=xxx`）—— 顺序无关，更不容易错位。

    也接受环境变量 `ACCEPTANCE_PASSWORD`（三个账号共用同一个口令）。
    """
    sources = []
    if args.password_file:
        sources.append(args.password_file)
    if os.environ.get("ACCEPTANCE_PASSWORD_FILE"):
        sources.append(os.environ["ACCEPTANCE_PASSWORD_FILE"])
    for path in sources:
        if not os.path.isfile(path):
            continue
        with open(path, encoding="utf-8") as fh:
            lines = [ln.strip() for ln in fh.read().splitlines()]
        values = [ln for ln in lines if ln and not ln.startswith("#")]
        if not values:
            raise SystemExit(f"[FAIL] 口令文件为空: {path}")
        # 先按 key=value 解析
        mapping = {}
        plain = []
        for ln in values:
            if "=" in ln:
                k, _, v = ln.partition("=")
                k = k.strip()
                if k in {a["username"] for a in ACCOUNTS}:
                    mapping[k] = v.strip()
            else:
                plain.append(ln)
        if mapping and len(mapping) == len(ACCOUNTS):
            return mapping
        if mapping:
            raise SystemExit(
                "[FAIL] 口令文件用了 key=value 格式，但只覆盖了 "
                f"{sorted(mapping)}，需要 {sorted(a['username'] for a in ACCOUNTS)} 全部三个。"
            )
        # 否则按「每行一个」：顺序 = 管理员 / 教师 / 学生
        if len(plain) < len(ACCOUNTS):
            raise SystemExit(
                f"[FAIL] 口令文件只有 {len(plain)} 行，需要 {len(ACCOUNTS)} 行"
                "（顺序：管理员 / 教师 / 学生），或改用 key=value 格式。"
            )
        return {a["username"]: plain[i] for i, a in enumerate(ACCOUNTS)}

    env = os.environ.get("ACCEPTANCE_PASSWORD", "").strip()
    if env:
        return {a["username"]: env for a in ACCOUNTS}

    raise SystemExit(
        "[FAIL] 没有口令来源。请用 --password-file <路径>、"
        "ACCEPTANCE_PASSWORD_FILE 或 ACCEPTANCE_PASSWORD 环境变量提供。\n"
        "       本脚本刻意**不**内置默认口令 —— 固定口令必须由你自己保管。"
    )


def main() -> int:
    ap = argparse.ArgumentParser(description="确保三个固定验收账号存在且可用（幂等）")
    ap.add_argument("--password-file", help="存放口令的文件（每行一个，首个非注释行为口令）")
    ap.add_argument("--dry-run", action="store_true", help="只打印将要做的改动，不写库")
    args = ap.parse_args()

    passwords = read_passwords(args)

    from sqlalchemy import select
    from app.core.database import SessionLocal, engine
    from app.core.database import Base
    from app.core.security import hash_password
    from app.models.system import User, Role, UserRole, UserStatus
    from app.models.edu import TeachingAssignment, Class as EduClass, Subject, Grade

    Base.metadata.create_all(bind=engine)

    changed = []
    with SessionLocal() as db:
        # 角色/年级/学科可能还没初始化（全新库 / 迁库后）。这些 init_* 都是
        # 幂等的：只新建缺失项、不动管理员已有的定制。这样「换环境后一键
        # 就绪」才成立 —— 否则新库里根本没有角色可绑、没有班级可挂。
        from app.services.init_db import init_roles, init_grades_subjects
        init_roles(db)
        init_grades_subjects(db)

        for spec in ACCOUNTS:
            user = db.scalar(select(User).where(User.username == spec["username"]))
            action = "创建"
            if user is None:
                user = User(
                    username=spec["username"],
                    password=hash_password(passwords[spec["username"]]),
                    real_name=spec["real_name"],
                    identity=spec["identity"],
                    status=UserStatus.ACTIVE.value,
                    must_change_password=False,
                )
                db.add(user)
                db.flush()
            else:
                action = "重置"
                user.password = hash_password(passwords[spec["username"]])
                user.real_name = spec["real_name"]
                user.identity = spec["identity"]
                user.status = UserStatus.ACTIVE.value
                # 固定账号不要求首登改密，否则违背「密码固定」的用途
                user.must_change_password = False
                # 测试中输错口令可能把账号锁住，每次执行都清零
                user.locked_until = None
                user.login_fail_count = 0

            # 角色
            role = db.scalar(select(Role).where(Role.code == spec["role_code"]))
            if role is None:
                print(f"[FAIL] 缺少内置角色 {spec['role_code']}，请先跑初始化脚本")
                return 1
            has_role = db.scalar(
                select(UserRole).where(UserRole.user_id == user.id, UserRole.role_id == role.id)
            )
            if has_role is None:
                db.add(UserRole(user_id=user.id, role_id=role.id))

            # 班级 + 授课关系
            if spec["class_name"]:
                klass = db.scalar(select(EduClass).where(EduClass.name == spec["class_name"]))
                if klass is None:
                    # 全新库 / 迁库后可能一个班级都没有。演示数据受
                    # SEED_DEMO_DATA 开关控制且只覆盖 1、7 年级，
                    # 不能指望它。这里自己按年级名补一个班级 ——
                    # 班级是「验收账号能用」的前置条件，不是可选项。
                    grade = db.scalar(select(Grade).where(Grade.grade_num == 1))
                    if grade is None:
                        print("[FAIL] 找不到一年级，无法创建验收班级。请先导入基础数据。")
                        return 1
                    klass = EduClass(name=spec["class_name"], grade_id=grade.id)
                    db.add(klass)
                    db.flush()
                user.class_id = klass.id
                user.grade_id = klass.grade_id
                if spec["subject_name"]:
                    subject = db.scalar(select(Subject).where(Subject.name == spec["subject_name"]))
                    if subject is None:
                        # edu_subject 的唯一约束是 (grade_id, name)，grade_id 非空 ——
                        # 学科是「按年级配置」的。优先复用本班年级已有的同名学科，
                        # 没有就按本班年级建一个。
                        subject = db.scalar(
                            select(Subject).where(
                                Subject.grade_id == klass.grade_id,
                                Subject.name == spec["subject_name"],
                            )
                        )
                        if subject is None:
                            subject = Subject(
                                name=spec["subject_name"], grade_id=klass.grade_id
                            )
                            db.add(subject)
                            db.flush()
                    ta = db.scalar(
                        select(TeachingAssignment).where(
                            TeachingAssignment.teacher_id == user.id,
                            TeachingAssignment.class_id == klass.id,
                            TeachingAssignment.subject_id == subject.id,
                        )
                    )
                    if ta is None:
                        db.add(TeachingAssignment(
                            teacher_id=user.id, class_id=klass.id,
                            subject_id=subject.id, grade_id=klass.grade_id,
                            is_active=True,
                        ))

            changed.append((spec["username"], action, spec["role_code"], spec["class_name"]))

        if args.dry_run:
            print("[dry-run] 将执行：")
            for row in changed:
                print("   ", row)
            db.rollback()
            return 0

        db.commit()

    print("[OK] 三个固定验收账号已就绪：")
    for username, action, role_code, class_name in changed:
        extra = f" 班级={class_name}" if class_name else ""
        print(f"   {username:16s} {action}  角色={role_code}{extra}")
    print("[提示] 口令未打印；来源文件请保持 0600 权限。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
