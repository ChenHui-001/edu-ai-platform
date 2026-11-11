"""2.5.6 六项缺陷修复的回归验证（不起服务、不依赖大模型）。

覆盖：
  1. 移除单题：有学生作答时默认拒绝（作答不被级联删），force 才删且回传 dropped
  2. 改密/管理员重置：旧 access + 旧 refresh 立即失效，新令牌可用
  3. 前端四处：解包层数、request 字段名、非 JSON 响应豁免、导出参数空值过滤
     （静态源码断言 —— 这些是模板/契约错误，编译期即可判定）

用法：python tools/verify_bugfix_256.py
"""
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "backend"))

FAILED = []


def check(name, ok, detail=""):
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  -> {detail}" if detail else ""))
    if not ok:
        FAILED.append(name)
    return ok


def verify_backend():
    from sqlalchemy import create_engine, event, func, select
    from sqlalchemy.orm import sessionmaker

    from app.core.database import Base
    from app.core.exception import BusinessException
    from app.core.security import (
        create_access_token, create_refresh_token, decode_token,
        hash_password, is_user_token_revoked, revoke_user_tokens,
    )
    from app.models import (
        Answer, Grade, Paper, PaperItem, Question, Subject, Submission, Task, User,
    )
    from app.services import auth_service
    from app.api.v1.paper_compose import remove_item
    import app.models  # noqa: F401  确保全部模型注册，create_all 才建得全

    tmp = tempfile.mkdtemp(prefix="fix256_")
    engine = create_engine(f"sqlite:///{os.path.join(tmp, 't.db')}")

    # 与 app/core/database.py 的 connect 钩子保持一致：不开 foreign_keys，
    # Answer.paper_item_id 的 ON DELETE CASCADE 不会生效，级联删除就测不出来。
    @event.listens_for(engine, "connect")
    def _sqlite_fk_on(conn, _record):
        cur = conn.cursor()
        cur.execute("PRAGMA foreign_keys=ON")
        cur.close()

    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()

    grade = Grade(name="七年级", stage="junior", grade_num=7)
    db.add(grade)
    db.flush()
    subject = Subject(name="数学", grade_id=grade.id)
    db.add(subject)
    db.flush()
    user = User(username="t_fix256", password=hash_password("OldPass@2026!Xy"),
                real_name="修复验证教师", identity="teacher",
                status="active", grade_id=grade.id)
    db.add(user)
    db.flush()

    def make_question(tag):
        q = Question(type="single", stem=f"修复验证题 {tag}",
                     options='[{"key":"A","text":"甲"},{"key":"B","text":"乙"}]',
                     answer="A", analysis="验证", score=5, difficulty="medium",
                     grade_id=grade.id, subject_id=subject.id,
                     bank_type="private", owner_id=user.id,
                     status="published", fingerprint=f"fix256-{tag}",
                     source="manual")
        db.add(q)
        db.flush()
        return q

    q1, q2 = make_question("1"), make_question("2")
    paper = Paper(name="修复验证卷", grade_id=grade.id, subject_id=subject.id,
                  creator_id=user.id, total_score=10)
    db.add(paper)
    db.flush()
    it1 = PaperItem(paper_id=paper.id, question_id=q1.id, sort_order=1, score=5)
    it2 = PaperItem(paper_id=paper.id, question_id=q2.id, sort_order=2, score=5)
    db.add_all([it1, it2])
    db.flush()
    # Answer.submission_id 是非空 FK，必须按真实链路补齐 Task → Submission
    task = Task(title="修复验证任务", paper_id=paper.id, subject_id=subject.id,
                grade_id=grade.id, creator_id=user.id)
    db.add(task)
    db.flush()
    sub = Submission(task_id=task.id, student_id=user.id, attempt=1)
    db.add(sub)
    db.flush()
    # 一条学生作答挂在 it1 上：删 it1 会被 CASCADE 清掉
    ans = Answer(paper_item_id=it1.id, question_id=q1.id,
                 submission_id=sub.id, content="A", full_score=5)
    db.add(ans)
    db.commit()

    print("\n=== 1. 移除单题不得静默清空学生作答 ===")
    before = db.scalar(select(func.count()).select_from(Answer))
    check("准备：有 1 条学生作答", before == 1, str(before))

    try:
        remove_item(paper.id, it1.id, force=False, db=db, user=user)
        rejected = False
        msg = ""
    except BusinessException as exc:
        rejected, msg = True, str(exc)
    check("有作答且未确认 → 拒绝删除", rejected, msg)
    check("拒绝原因写明作答条数", "1 条学生作答" in msg, msg)
    check("拒绝原因写明后果（永久删除）", "永久删除" in msg, msg)
    check("拒绝后作答仍在（未被级联清空）",
          db.scalar(select(func.count()).select_from(Answer)) == 1)

    res = remove_item(paper.id, it1.id, force=True, db=db, user=user)
    data = res.get("data") or {}
    check("force=true 才允许删除", bool(data), str(res)[:120])
    check("响应回传 dropped=1（如实上报作废条数）",
          data.get("dropped") == 1, str(data))
    check("提示文案写明作废条数", "作废 1 条" in str(res.get("message")),
          str(res.get("message")))
    check("删除后作答确已级联清空",
          db.scalar(select(func.count()).select_from(Answer)) == 0)

    print("\n=== 2. 改密 / 管理员重置后旧令牌立即失效 ===")
    # 用 db=None 解码避免吊销名单干扰（这里只测水位）
    old_access = create_access_token(user.id, role="teacher")
    old_refresh = create_refresh_token(user.id)
    p_access = decode_token(old_access, check_revocation=False)
    p_refresh = decode_token(old_refresh, check_revocation=False)
    check("改密前 access 未被水位拦截",
          not is_user_token_revoked(db, p_access))
    check("改密前 refresh 未被水位拦截",
          not is_user_token_revoked(db, p_refresh))

    # 刻意不等跨秒：改密后立即重签 / 立刻重登是真实场景。
    # JWT 标准 iat 只有整秒精度，若拿它与浮点水位直接比，新令牌必被误杀。
    auth_service.change_password(db, user, "OldPass@2026!Xy", "NewPass@2026!Xy")
    check("改密后 access 立即失效",
          is_user_token_revoked(db, p_access))
    check("改密后 refresh 立即失效（不能续 7 天）",
          is_user_token_revoked(db, p_refresh))
    fresh = decode_token(create_access_token(user.id, role="teacher"),
                         check_revocation=False)
    check("改密后同一秒内新签发的令牌可用（整秒 iat 不误杀）",
          not is_user_token_revoked(db, fresh))
    # 反向验证：拿掉浮点签发时刻，退回「整秒 iat 比浮点水位」的旧算法，
    # 同一个新令牌应当立刻被误杀 —— 证明该字段不是冗余而是必需。
    fresh_legacy = dict(fresh)
    fresh_legacy.pop("iat_precise", None)
    check("反向验证：去掉 iat_precise 后同秒新令牌会被误杀",
          is_user_token_revoked(db, fresh_legacy))
    legacy_old = dict(p_access)
    legacy_old.pop("iat_precise", None)
    check("部署前签发的旧格式令牌仍被水位拦下（无安全空窗）",
          is_user_token_revoked(db, legacy_old))

    auth_service.reset_password_by_admin(db, user.id, "ResetPass@2026!Xy")
    check("管理员重置后新令牌也失效",
          is_user_token_revoked(db, fresh))
    fresh2 = decode_token(create_access_token(user.id, role="teacher"),
                          check_revocation=False)
    check("重置后重新登录的令牌可用",
          not is_user_token_revoked(db, fresh2))

    # 水位表每个用户只有一行（覆盖写，不无限增长）
    from app.models import UserTokenRevocation
    cnt = db.scalar(select(func.count()).select_from(UserTokenRevocation)
                    .where(UserTokenRevocation.user_id == user.id))
    check("重复改密只留一行水位（覆盖写）", cnt == 1, str(cnt))

    # 口径：iat 与水位同为 UTC epoch，不能用本地时间比较
    check("水位记录时间单位是 UTC epoch（与 iat 同量级）",
          1e9 < float(db.scalar(select(UserTokenRevocation.invalid_before_ts)
                               .where(UserTokenRevocation.user_id == user.id))) < 1e11)

    # 直接调 revoke_user_tokens 的独立行为（找回密码走这条路）
    revoke_user_tokens(db, user.id)
    check("find-password 用的独立吊销入口生效",
          is_user_token_revoked(db, fresh2))

    db.close()
    engine.dispose()


def verify_frontend():
    FE = os.path.join(ROOT, "frontend", "src")

    def read(rel):
        with open(os.path.join(FE, rel), encoding="utf-8") as fh:
            return fh.read()

    print("\n=== 3. 前端四处契约修复（静态断言）===")
    pm = read("views/teacher/PaperManage.vue")
    # 这条守的是 P0-2 的**真正原因**：页面把 `res.data` 又解了一层，
    # 于是 `envelope.success` 恒为 undefined，卷子明明落库却弹「组卷失败」。
    # 原来的写法断言 `parseAgentEnvelope(res) in pm`，而那个 composable 的
    # 最后一个消费方正是 PaperManage 里那段从未被触达的 AI 组卷死代码
    # （P2-3 已删）。断言盯着"某个辅助函数有没有被调用"，一旦这段代码被清理
    # 就变成假红 —— 现在改为直接盯"有没有人再手动多解一层"，与实现形式解耦。
    check("PaperManage 不再手动多解一层 res.data",
          "res.data.data" not in pm and "parseAgentEnvelope" not in pm)
    check("AgentGenerate 也不多解一层",
          "res.data.data" not in read("views/agent/AgentGenerate.vue"))

    ag = read("views/agent/AgentGenerate.vue")
    check("AgentGenerate 发的是 request（不是 requirement）",
          "request: paperReq.value" in ag and "requirement: paperReq" not in ag)
    check("AgentGenerate 同步+异步两条路径都用同一参数构造",
          ag.count("paperParams()") >= 2)
    check("AgentGenerate 提供年级/学科自救下拉",
          "paperGradeId" in ag and "paperSubjects" in ag)

    rq = read("api/request.js")
    check("request.js 不再只豁免 blob",
          "RAW_RESPONSE_TYPES" in rq and "'text'" in rq)
    check("非 JSON 响应返回整个 response（保留 headers 给下载取文件名）",
          "if (isRawResponse(response)) return response" in rq)

    wb = read("views/student/WrongBook.vue")
    check("错题本导出过滤 null / 空串",
          "v !== null && v !== undefined && v !== ''" in wb)


def main():
    verify_backend()
    verify_frontend()
    print("\n" + "=" * 60)
    if FAILED:
        print(f"失败 {len(FAILED)} 项：")
        for f in FAILED:
            print("  -", f)
        return 1
    print("全部通过：2.5.6 六项缺陷修复均生效")
    return 0


if __name__ == "__main__":
    sys.exit(main())
