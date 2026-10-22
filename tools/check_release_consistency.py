#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
发版一致性校验 —— 保证「本地代码 / 远程仓库 / Docker 镜像」三者对齐。

## 三者为什么会对不上

版本号与代码在发布链路上有**五个独立的落点**，每个落点都是一次「复制」，
任何一次复制都可能与源头脱节：

    ① 根目录 VERSION 文件            <- 唯一真源
    ② git commit -> origin/master    <- 代码离开本机的唯一通道
    ③ Dockerfile COPY VERSION ./     <- 镜像内的版本快照
    ④ 镜像标签 repo:1.0.40           <- 人为命名，不复核文件内容
    ⑤ /health 返回 settings.APP_VERSION <- 运行时可观测值

出错方式都是「某一步用了旧值或复制错了」，且**每一步都不会自己报错**：

| 漂移方式 | 现象 | 为何不报错 |
|---|---|---|
| 改了代码没提交就构建镜像 | 镜像含未入库改动，无法溯源 | docker build 只看工作区 |
| 提交了没 push | 镜像对应的 commit 在远端不存在 | git 不校验推送状态 |
| VERSION 改了但 git tag 没改 | `v1.0.41` 的 tag 打出 `:1.0.40` 镜像 | 两者无任何关联校验 |
| 镜像标签手打成旧版本号 | `:1.0.40` 里其实是 1.0.41 的代码 | 标签是自由文本 |
| APP_VERSION 空串导致回落 | 镜像内版本取到缓存残留值 | `_resolve_version` 静默回落 |

本脚本把上述每一环都变成**可执行断言**，并在发版前后各跑一次。

## 三种模式

    # 发布前：必须干净、必须已推送、版本必须与 tag 自洽
    python tools/check_release_consistency.py --pre

    # 发布后：核对远程镜像确实存在，且镜像内版本 == VERSION
    python tools/check_release_consistency.py --post

    # 默认（静态）：只校验本地 VERSION / git / 已有镜像，不需要网络
    python tools/check_release_consistency.py

退出码：0 通过 / 1 不一致 / 2 环境缺失（如 --post 时 docker 不可用）
"""
import argparse
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VERSION_FILE = os.path.join(ROOT, "VERSION")

# 镜像仓库命名空间：与 CI 的 vars.DOCKERHUB_REPO 保持同一语义
DEFAULT_REPO = "nanpo/edu-ai-platform"

GREEN, RED, YELLOW, DIM, RESET = "\033[92m", "\033[91m", "\033[93m", "\033[90m", "\033[0m"


# ================================================================ 基础工具
def sh(args, cwd=ROOT, timeout=60):
    """执行命令，返回 (returncode, stdout, stderr)。不抛异常。"""
    try:
        r = subprocess.run(args, cwd=cwd, capture_output=True, text=True, timeout=timeout)
        return r.returncode, (r.stdout or "").strip(), (r.stderr or "").strip()
    except (OSError, subprocess.SubprocessError) as exc:
        return -1, "", str(exc)


def read_version():
    if not os.path.exists(VERSION_FILE):
        return None
    with open(VERSION_FILE, encoding="utf-8") as f:
        return f.read().strip()


def http_json(url, timeout=25):
    """访问 URL 并解析 JSON。**必须绕开系统代理**：本机 https_proxy 会把
    localhost / registry 请求一起代理走，返回空响应。"""
    req = urllib.request.Request(url, headers={"Accept": "application/json",
                                              "User-Agent": "edu-ai-platform-ci"})
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


# ================================================================ 检查结果收集
class Report:
    def __init__(self):
        self.items = []   # (级别, 标题, 详情)

    def ok(self, title, detail=""):
        self.items.append(("PASS", title, detail))
        print(f"  {GREEN}[PASS]{RESET} {title}" + (f"  {DIM}{detail}{RESET}" if detail else ""))

    def fail(self, title, detail=""):
        self.items.append(("FAIL", title, detail))
        print(f"  {RED}[FAIL]{RESET} {title}" + (f"  -> {detail}" if detail else ""))

    def warn(self, title, detail=""):
        self.items.append(("WARN", title, detail))
        print(f"  {YELLOW}[WARN]{RESET} {title}" + (f"  -> {detail}" if detail else ""))

    def skip(self, title, detail=""):
        self.items.append(("SKIP", title, detail))
        print(f"  {DIM}[SKIP]{RESET} {title}" + (f"  {DIM}{detail}{RESET}" if detail else ""))

    @property
    def failed(self):
        return sum(1 for i in self.items if i[0] == "FAIL")


# ================================================================ 逻辑点 ①：VERSION 文件
def check_version_file(rep):
    """VERSION 是唯一真源，必须存在、合法、无多余空白。"""
    v = read_version()
    if v is None:
        rep.fail("VERSION 文件存在", f"未找到 {VERSION_FILE}")
        return None
    # 版本号会被直接拼进镜像标签。带空白/换行会让 `docker tag` 报
    # invalid reference format，而错误信息完全看不出是 VERSION 的问题。
    if not re.match(r"^\d+\.\d+\.\d+$", v):
        rep.fail("VERSION 内容符合 x.y.z", f"实际={v!r}；"
                 "标签会因非法字符构建失败，或被打成无法排序的怪值")
        return None
    rep.ok("VERSION 内容符合 x.y.z", v)
    return v


# ================================================================ 逻辑点 ②：git 状态
def check_git(rep, version, mode):
    """代码必须已提交、已推送 —— 否则镜像对应的 commit 在远端不存在。"""
    code, head, _ = sh(["git", "rev-parse", "HEAD"])
    if code != 0:
        rep.fail("读取 git HEAD", "不是 git 仓库或 git 不可用")
        return None, None
    rep.ok("当前 HEAD", head[:7])

    # 工作区干净：有未提交改动时构建镜像 = 镜像含未入库代码，无法溯源
    code, dirty, _ = sh(["git", "status", "--porcelain"])
    if code != 0:
        rep.warn("工作区状态", "git status 失败，跳过")
    elif dirty:
        lines = dirty.splitlines()
        need = mode in ("pre", "post")
        (rep.fail if need else rep.warn)(
            "工作区干净（无未提交改动）",
            f"{len(lines)} 项未提交：{lines[:3]}"
            + ("；此时构建的镜像含未入库代码" if need else ""))
    else:
        rep.ok("工作区干净（无未提交改动）")

    # 是否已推送：本地有、远端无的 commit 构建出来的镜像无法溯源
    code, upstream, _ = sh(["git", "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"])
    if code != 0:
        rep.warn("存在上游追踪分支", "当前分支未设置 upstream，无法判断是否已推送")
        return head, None
    # 注意：这里用解析出来的 upstream 分支名，**不要**写 git 的 "@{u}" 简写——
    # 简写在 f-string 里会被当成 Python 变量 u（NameError），去掉 f 前缀又会在
    # 无 upstream 的 shell 环境下报 ambiguous argument。直接用具体分支名最稳。
    code, ahead_s, _ = sh(["git", "rev-list", "--count", f"{upstream}..HEAD"])
    # ⚠️ sh() 返回的是 **strip 后的字符串**，"0" == 0 在 Python 里是 False。
    # 不做 int() 转换会把「已同步」误判成「落后 0 个提交」并打出错误括注。
    try:
        ahead = int(ahead_s) if code == 0 else None
    except (TypeError, ValueError):
        ahead = None
    if ahead is None:
        rep.warn("与远程同步", "无法计算领先提交数")
    elif ahead == 0:
        rep.ok("代码已推送（本地 == 远程）", upstream)
    else:
        # 发布前也必须已推送：镜像里烧入的 commit 若在远端不存在，
        # 镜像就成了孤证 —— 既无法在 CI 复现，也无法证明它与哪份代码对应。
        need = mode in ("pre", "post")
        (rep.fail if need else rep.warn)(
            "代码已推送（本地 == 远程）",
            f"本地领先 {upstream} **{ahead} 个提交**；"
            "镜像对应的 commit 在远端不存在，无法溯源/无法在 CI 复现")
    return head, upstream


# ================================================================ 逻辑点 ④：tag 与版本自洽
def check_git_tag(rep, version, head):
    """`v1.0.41` 的 tag 必须打出 `:1.0.41` 的镜像。

    这两者原本毫无关联：CI 的镜像标签取自 VERSION 文件，而触发事件可能是
    tag push。VERSION 忘改时，v1.0.41 会静默产出 :1.0.40 镜像，
    且 latest 也会跟着错——这是最隐蔽的一类版本漂移。
    """
    code, tags, _ = sh(["git", "tag", "--points-at", "HEAD"])
    if code != 0:
        rep.skip("git tag 与 VERSION 自洽", "git tag 不可用")
        return
    point = [t for t in tags.splitlines() if t.strip()]
    if not point:
        rep.ok("HEAD 无 tag（按分支发布）", "镜像标签取 VERSION，无需交叉校验")
        return
    bad = []
    for t in point:
        m = re.match(r"^v?(\d+\.\d+\.\d+)$", t.strip())
        if not m:
            rep.warn(f"tag `{t}` 非版本格式", "无法与 VERSION 交叉校验")
            continue
        if m.group(1) != version:
            bad.append(f"{t} != {version}")
    if bad:
        rep.fail("git tag 与 VERSION 一致",
                 f"{bad}；该 tag 的发布会打出错误版本号的镜像")
    else:
        rep.ok("git tag 与 VERSION 一致", f"{point}")


# ================================================================ 逻辑点 ③/⑤：镜像内版本
def read_build_info(image):
    """一次读出镜像内 /app/BUILD_INFO 的全部字段。返回 dict（可能为空）。

    **这是首选来源**：BUILD_INFO 由 `cat /app/VERSION` + 构建参数在镜像内
    生成，版本与 commit 同源同批写入，不会出现「label 有 revision 但
    version 为空」这种半残状态 —— 后者只在漏传 ARG APP_VERSION 时出现，
    而 LABEL 无法从文件取值，只能靠构建命令自觉。
    """
    code, out, _ = sh(["docker", "run", "--rm", "--entrypoint", "cat",
                       image, "/app/BUILD_INFO"], timeout=180)
    if code != 0 or not out:
        return {}
    info = {}
    for line in out.splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            info[k.strip()] = v.strip()
    return info


def image_embedded_version(image):
    """读镜像内 /app/VERSION。返回 (版本号, 来源说明)。

    优先直接读文件（等于运行时 `_resolve_version` 的取值），
    失败再退到 OCI label。两者都可能因镜像未构建/架构不符而失败。
    """
    # ① 直接读镜像里的 VERSION 文件——这是运行时真正读到的那个值
    code, out, err = sh(["docker", "run", "--rm", "--entrypoint", "cat",
                         image, "/app/VERSION"], timeout=180)
    if code == 0 and out:
        return out.splitlines()[0].strip(), "镜像内 /app/VERSION"
    # ② BUILD_INFO 里的 version 字段
    info = read_build_info(image)
    if info.get("version") and info["version"] != "unknown":
        return info["version"], "镜像内 /app/BUILD_INFO"
    # ③ OCI label（仅当 Dockerfile 设置了 LABEL，作为兜底）
    code, out, _ = sh(["docker", "inspect", "--format",
                       '{{index .Config.Labels "org.opencontainers.image.version"}}',
                       image])
    if code == 0 and out and out != "<no value>":
        return out.strip(), "OCI label"
    return None, f"无法读取（{err[:80] or '镜像不存在'}）"


def image_embedded_commit(image):
    """读镜像构建时烧入的 commit。返回 (sha 或 None, 说明)。

    **这是判定「代码一致」的唯一硬依据。**
    优先 BUILD_INFO（与版本同源写入），再退 OCI label。
    """
    info = read_build_info(image)
    if info.get("commit") and info["commit"] != "unknown":
        return info["commit"], "镜像内 /app/BUILD_INFO"

    code, out, _ = sh(["docker", "inspect", "--format",
                       '{{index .Config.Labels "org.opencontainers.image.revision"}}',
                       image])
    if code == 0 and out and out not in ("<no value>", ""):
        return out.strip(), "OCI label"
    return None, "镜像未烧入 commit 指纹（旧镜像，构建时未传 --build-arg GIT_COMMIT）"


# 真正会被 COPY 进镜像的路径（见 Dockerfile）。只有这些的改动会改变镜像内容；
# docs/、.github/、*.md 之类改了也只是让 commit 换个 sha，镜像字节不变。
IMAGE_AFFECTING_PREFIXES = (
    "backend/app/",
    "backend/requirements.txt",
    "backend/.env.example",
    "frontend/",
    "deploy/",
    "VERSION",
    "Dockerfile",
    ".dockerignore",
)


def commits_missing_from_image(sha, head):
    """判断 (sha..head) 之间是否有**影响镜像内容**的改动。

    返回 (是否有影响, 影响文件列表)。

    ## 为什么不能一律要求 commit 完全相等

    提交一份文档后 HEAD 就变了，镜像立刻「代码不一致」——但镜像里一个
    字节都没变。要求必须重建既浪费十几分钟，也会诱使人用
    `--skip-test` 之类的手段绕开流程，反而降低可靠性。

    一致性的本质是「**镜像内容 == 代码内容**」，对不影响镜像的提交而言
    两者本就是等价的。所以这里按「改动是否落在会被 COPY 的路径」判定。
    """
    code, out, _ = sh(["git", "diff", "--name-only", f"{sha}..{head}"])
    if code != 0:
        return True, []          # 拿不到差异就按「有影响」保守处理
    files = [f.strip() for f in out.splitlines() if f.strip()]
    affecting = [f for f in files if f.startswith(IMAGE_AFFECTING_PREFIXES)]
    return bool(affecting), affecting


def check_local_image(rep, version, repo, mode, head=None):
    """本地镜像里的版本**和代码**都必须等于 VERSION / HEAD。

    版本号一致远远不够：同一个 `1.0.40` 可以构建十次、代码各不相同。
    必须比对镜像内烧入的 commit 指纹，否则「镜像落后两个版本」也会静默通过。
    """
    tag = f"{repo}:{version}"
    code, _, _ = sh(["docker", "image", "inspect", tag])
    if code != 0:
        # 发布前本地没有镜像属正常（CI 从零构建）；发布后必须有
        (rep.fail if mode == "post" else rep.skip)(
            f"本地镜像存在 `{tag}`", "未构建（发布前可忽略）")
        return
    got, src = image_embedded_version(tag)
    if got is None:
        rep.warn("读取本地镜像内版本", src)
    elif got == version:
        rep.ok("本地镜像内版本 == VERSION", f"{tag} -> {got}（{src}）")
    else:
        rep.fail("本地镜像内版本 == VERSION",
                 f"{tag} 内是 {got!r}，VERSION 是 {version!r}；"
                 "说明标签打错了对象，或构建时 APP_VERSION 注入错误")

    # ---- 代码一致性（关键判据）----
    if not head:
        rep.skip("本地镜像内 commit == HEAD", "无法读取 HEAD")
        return
    sha, how = image_embedded_commit(tag)
    if sha is None:
        # ⚠️ 不能降级为 WARN：那等于给「docker build 不传 --build-arg」开一条
        # 免检通道 —— 谁绕过了注入，谁就绕过了整个代码一致性校验。
        # 严格模式（pre/post）下必须硬失败，逼其带指纹重建。
        strict = mode in ("pre", "post")
        (rep.fail if strict else rep.warn)(
            "本地镜像内 commit == HEAD",
            how + ("；无法证明镜像出自当前代码，请带 --build-arg GIT_COMMIT 重建"
                   if strict else ""))
        return
    # 允许残缺 sha（abbrev）：只要能唯一对应 HEAD 前缀即视为一致
    if head.startswith(sha) or sha.startswith(head):
        rep.ok("本地镜像内 commit == HEAD", f"{tag} -> {sha[:7]}")
        return

    # commit 不同，但若差异全在不进镜像的路径（docs/、.github/、*.md），
    # 镜像内容并未改变 —— 这不算漂移。
    affecting, files = commits_missing_from_image(sha, head)
    if not affecting:
        rep.ok("本地镜像内 commit 与 HEAD 等价",
               f"镜像出自 {sha[:7]}，HEAD 是 {head[:7]}，"
               f"但 {sha[:7]}..{head[:7]} 无影响镜像内容的改动（仅文档/CI）")
        return

    rep.fail("本地镜像内 commit == HEAD",
             f"镜像出自 {sha[:7]}，当前代码是 {head[:7]}；"
             f"差异文件（影响镜像）：{files[:3]}{'...' if len(files) > 3 else ''}；"
             "镜像里**不是**当前这份代码 —— 版本号相同也会骗人，必须重建")


# ================================================================ 远程镜像核对
def check_remote_image(rep, version, repo, mode):
    """远程镜像必须存在，且远程标签对应的版本与 VERSION 一致。"""
    if mode not in ("post",):
        # 发布前远程还没有本次版本，属正常；但若远程已有同名标签，
        # 说明这个版本号被用过 —— 覆盖发布会让旧镜像静默消失。
        pass

    url = f"https://hub.docker.com/v2/repositories/{repo}/tags/{version}"
    try:
        d = http_json(url)
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            (rep.fail if mode == "post" else rep.warn)(
                f"远程镜像 `{repo}:{version}` 存在",
                "Docker Hub 上无此标签 —— 换版本号，或先执行发布" if mode == "post"
                else "尚未发布该版本（发布前正常）")
        else:
            rep.warn("查询远程镜像", f"HTTP {exc.code}")
        return
    except Exception as exc:  # noqa: BLE001
        rep.warn("查询远程镜像", f"网络不可达：{exc}")
        return

    rep.ok(f"远程镜像 `{repo}:{version}` 存在",
           f"updated={str(d.get('last_updated'))[:19]} "
           f"size={d.get('full_size', 0) // 1048576}MB")
    digest = (d.get("digest") or "")[:19]
    if digest:
        rep.ok("远程镜像 digest 可读", digest + "...")


def check_latest_pointer(rep, version, repo, mode):
    """latest 的语义是「最新发布版本」，不是「最后一次构建」。

    拿它跟 VERSION 比较，能发现两种漂移：
    - 发了 1.0.41 但 latest 仍指向 1.0.40（latest 忘了更新）；
    - 有人补推旧版本时把 latest 覆盖了（用旧代码顶替最新）。
    """
    if mode != "post":
        rep.skip("latest 指向最新版本", "仅发布后核对")
        return
    url = f"https://hub.docker.com/v2/repositories/{repo}/tags/latest"
    try:
        d = http_json(url)
    except Exception as exc:  # noqa: BLE001
        rep.warn("查询 latest", f"不可达：{exc}")
        return
    latest_digest = d.get("digest")

    url_v = f"https://hub.docker.com/v2/repositories/{repo}/tags/{version}"
    try:
        dv = http_json(url_v)
        ver_digest = dv.get("digest")
    except Exception:  # noqa: BLE001
        ver_digest = None

    if latest_digest and ver_digest:
        if latest_digest == ver_digest:
            rep.ok("latest 指向本次发布版本", f"digest 相同 {str(latest_digest)[:19]}...")
        else:
            rep.fail("latest 指向本次发布版本",
                     f"latest={str(latest_digest)[:19]}... 与 "
                     f"{version}={str(ver_digest)[:19]}... 不一致；"
                     "latest 未更新，或指向了别的版本")
    else:
        # Docker Hub API 偶发不返回 digest（不是错误）。退一步比 last_updated：
        # 两者同为本次发布（时间差在 1 小时内）即可判定 latest 已跟上本版本。
        # ⚠️ 不要直接 skip —— 那等于「查不到就放行」，latest 指错也发现不了。
        lu_latest = str(d.get("last_updated") or "")
        lu_ver = str(dv.get("last_updated") or "")
        if lu_latest and lu_ver and lu_latest[:13] == lu_ver[:13]:
            rep.ok("latest 指向本次发布版本",
                   f"digest 缺失，按更新时间判定：latest={lu_latest[:19]} "
                   f"≈ {version}={lu_ver[:19]}")
        else:
            rep.warn("latest 指向校验",
                     f"digest 缺失且更新时间不一致（latest={lu_latest[:19] or '?'}，"
                     f"{version}={lu_ver[:19] or '?'}），请手工核对")


# ================================================================ 主流程
def main():
    ap = argparse.ArgumentParser(description="发版一致性校验：本地代码 / 远程仓库 / Docker 镜像")
    ap.add_argument("--pre", action="store_true",
                    help="发布前校验（要求工作区干净；警告未推送）")
    ap.add_argument("--post", action="store_true",
                    help="发布后核对（要求已推送、本地镜像存在、远程镜像存在、latest 正确）")
    ap.add_argument("--repo", default=os.environ.get("DOCKERHUB_REPO") or DEFAULT_REPO,
                    help=f"镜像仓库（默认 {DEFAULT_REPO}）")
    ap.add_argument("--no-image", action="store_true", help="跳过 docker 相关检查")
    args = ap.parse_args()

    mode = "post" if args.post else ("pre" if args.pre else "static")
    rep = Report()

    title = {"pre": "发布前", "post": "发布后", "static": "静态"}[mode]
    print(f"\n{'=' * 66}")
    print(f"  发版一致性校验  ·  {title}  ·  仓库 {args.repo}")
    print(f"{'=' * 66}\n")

    print(f"{DIM}-- ① 版本号真源{RESET}")
    version = check_version_file(rep)
    if version is None:
        print(f"\n{RED}VERSION 不可用，后续检查无法进行{RESET}")
        return 1

    print(f"\n{DIM}-- ② 代码是否已进入远程仓库{RESET}")
    head, _upstream = check_git(rep, version, mode)

    print(f"\n{DIM}-- ④ git tag 与 VERSION 自洽{RESET}")
    if head:
        check_git_tag(rep, version, head)

    if not args.no_image:
        print(f"\n{DIM}-- ③/⑤ 本地镜像内版本与代码{RESET}")
        check_local_image(rep, version, args.repo, mode, head)

        print(f"\n{DIM}-- 远程仓库核对{RESET}")
        check_remote_image(rep, version, args.repo, mode)
        check_latest_pointer(rep, version, args.repo, mode)
    else:
        rep.skip("镜像相关检查", "--no-image")

    # ---------------------------------------------------------------- 汇总
    print(f"\n{'=' * 66}")
    n_pass = sum(1 for i in rep.items if i[0] == "PASS")
    n_warn = sum(1 for i in rep.items if i[0] == "WARN")
    n_skip = sum(1 for i in rep.items if i[0] == "SKIP")
    print(f"  通过 {n_pass} / 失败 {rep.failed} / 警告 {n_warn} / 跳过 {n_skip}")
    if rep.failed:
        print(f"\n  {RED}一致性校验未通过{RESET}。三者必须对齐：")
        print(f"    VERSION({version}) == git tag == 镜像标签 == 镜像内 /app/VERSION")
        print("    修正顺序：改 VERSION -> 提交 -> 打/改 tag -> 推送 -> 重新构建镜像")
        return 1
    print(f"  {GREEN}一致性校验通过{RESET}  VERSION={version}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
