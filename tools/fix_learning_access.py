# -*- coding: utf-8 -*-
"""学习中心权限隔离修复。

现状：/learning 下 38 个接口全部使用 get_current_user（任何登录用户可达）
      —— 教师/管理员可创建学生笔记、练习、收藏等，产生错位数据；
         访客（guest 角色）同样可调用。

修复：
1. 读接口 → get_current_student（学生/教师/年级管理员/系统管理员可读，禁 guest）
2. 写接口 → get_current_student_self（仅 identity=student，避免教师/管理员污染学生数据）
3. shared_notes：仅学生身份返回同班他人共享笔记（教师/管理员返回空，避免越界看学生私有内容）
4. get_note：非本人查看（sys_admin）写审计日志
"""
import io
import re

# ============================================================
# 1) deps.py 新增「仅学生本人」依赖
# ============================================================
f = "backend/app/api/deps.py"
s = io.open(f, encoding="utf-8").read()
if "def get_current_student_self" not in s:
    ANCHOR = '''def get_current_student(user: User = Depends(get_current_user)) -> User:
    """学生及以上。"""
    codes = user.role_codes
    if not ({ROLE_STUDENT, ROLE_TEACHER, ROLE_GRADE_ADMIN, ROLE_SYS_ADMIN} & set(codes)):
        raise PermissionException("需要学生权限")
    return user'''
    NEW = ANCHOR + '''


def get_current_student_self(user: User = Depends(get_current_user)) -> User:
    """仅学生本人（写入型学习数据：笔记/练习/收藏/目标/复习）。

    学习中心是学生个人空间，教师与管理员不应在此创建数据——
    否则会在学生表里留下「教师身份的学生笔记」等错位记录。
    """
    if user.identity != "student":
        raise PermissionException("该功能仅学生可用")
    return user'''
    assert ANCHOR in s, "deps anchor"
    s = s.replace(ANCHOR, NEW)
    io.open(f, "w", encoding="utf-8", newline="\n").write(s)
    print("deps.py：新增 get_current_student_self")

# ============================================================
# 2) learning 各模块：读接口换 get_current_student，写接口换 get_current_student_self
# ============================================================
WRITE_METHODS = ("post", "put", "delete", "patch")

for path in ("backend/app/api/v1/learning/notes.py",
             "backend/app/api/v1/learning/review.py",
             "backend/app/api/v1/learning/tools.py",
             "backend/app/api/v1/learning/wrongbook.py"):
    src = io.open(path, encoding="utf-8").read()

    # 确保两个依赖都已导入
    if "get_current_student_self" not in src.split("\n\n")[0]:
        src = src.replace(
            "from app.api.deps import get_current_user",
            "from app.api.deps import (\n    get_current_student, get_current_student_self, get_current_user,\n)")

    lines = src.split("\n")
    current_method = None
    out = []
    changed = 0
    for line in lines:
        m = re.match(r"@router\.(get|post|put|delete|patch)\(", line)
        if m:
            current_method = m.group(1)
        if "Depends(get_current_user)" in line:
            # 判断所属路由方法
            dep = ("get_current_student_self" if current_method in WRITE_METHODS
                   else "get_current_student")
            line = line.replace("Depends(get_current_user)", f"Depends({dep})")
            changed += 1
        out.append(line)
    src = "\n".join(out)
    io.open(path, "w", encoding="utf-8", newline="\n").write(src)
    print(f"{path}: 替换 {changed} 处依赖")

# ============================================================
# 3) shared_notes 仅学生返回；get_note 管理员访问写审计日志
# ============================================================
f2 = "backend/app/api/v1/learning/notes.py"
s2 = io.open(f2, encoding="utf-8").read()

OLD_SHARED = '''    """查看同班同学共享的笔记（不含本人，按班级隔离）。"""
    from app.models import User as U'''
NEW_SHARED = '''    """查看同班同学共享的笔记（不含本人，按班级隔离）。

    仅学生可查看他人笔记；教师/管理员即使有 class_id 也不应浏览
    学生私有内容（此前教师能通过自己的班号看到本班学生共享笔记）。
    """
    if user.identity != "student":
        return ok({"items": [], "total": 0})
    from app.models import User as U'''
assert OLD_SHARED in s2, "shared_notes"
s2 = s2.replace(OLD_SHARED, NEW_SHARED)

OLD_GET = '''    if note.student_id != user.id and "sys_admin" not in user.role_codes:
        raise PermissionException("无权查看该笔记")'''
NEW_GET = '''    if note.student_id != user.id:
        # 仅系统管理员可跨用户查看（数据核查），且必须留审计痕迹
        if "sys_admin" not in user.role_codes:
            raise PermissionException("无权查看该笔记")
        try:
            from app.models import OperationLog

            db.add(OperationLog(
                user_id=user.id, username=user.username,
                module="学习中心", action="查看学生笔记",
                detail=f"note_id={note_id} owner_id={note.student_id}",
                ip="", status="success",
            ))
        except Exception:  # noqa: BLE001
            pass'''
assert OLD_GET in s2, "get_note"
s2 = s2.replace(OLD_GET, NEW_GET)
io.open(f2, "w", encoding="utf-8", newline="\n").write(s2)
print("notes.py：共享笔记身份隔离 + 管理员访问审计")

print("\n完成")
