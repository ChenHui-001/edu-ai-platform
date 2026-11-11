"""门禁：非归档文档不许自己声明「当前版本号」（Q-02）。

## 为什么需要

`docs/RELEASE_CONSISTENCY.md` 曾有一张「当前状态（2.1.12）」的表，手写之后
再没人跟着发版更新。读者据此判断"线上在跑 2.1.12"，而实际早已是 2.5.x ——
`audit-reports/structured-assessment-2.5.19` 把它点名为「文档基线漂移」。

同类漂移在 README 出现过一次：`docker pull ...:2.0.0` 写死在快速开始里，
照着抄的人会拉到一年前的镜像。

靠"记得每次发版改文档"是解决不了的 —— 人会忘，而且没人知道该改哪几处。
所以规则改成：**版本号只有一个出处（`VERSION`），文档只许指向 `docs/STATUS.md`。**

## 查什么

1. **现状卡自洽**（机械校验，无豁免）：`docs/STATUS.md` 的 auto 区块里
   `| 版本 | X |` 必须等于 `VERSION`。不加 `--write` 就不会自动修，
   所以这一条等于强制「bump 版本后必须重跑 status_snapshot.py」。
2. **"当前版本"类声明**：非归档文档里出现 `当前版本 / 最新版本 / 线上版本 /
   版本基线 / 部署版本 / 正在运行` 等词，同行又带着一个 `2.x.y`，
   且该值 ≠ `VERSION` → FAIL。要么改成指向 `docs/STATUS.md`，要么补时间标记。
3. **版本快照表**：`| 版本 | 2.x.y |` 这种表格行只允许出现在 `docs/STATUS.md`
   （它就是那张卡）。别处出现即视为"又手写了一份版本快照"。

## 刻意不查的部分

- `docs/archive/**` 与 `audit-reports/**`：历史报告本来就该保留当时的版本号，
  改了反而毁掉证据。
- 行内出现 `历史 / 当时 / 曾 / 旧版 / 已废弃 / 上轮 / 示例 / 成文于 /
  决策时点 / 归档 / 勿当作 / 快照` 之一的行：这些是明确的时间标记。
- 「已于 2.4.1 修复」「2.5.10 加的 B9 接口」这类**变更史**表述：它们不含
  "当前"语义，跟漂移无关。真去管它只会逼人写一堆无意义豁免。

用法：
    python tools/check_doc_versions.py
退出码：0 通过 / 1 有漂移
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VERSION_FILE = os.path.join(ROOT, "VERSION")
STATUS = os.path.join(ROOT, "docs", "STATUS.md")

# 扫描范围：仓库根的 Markdown + docs/ 下（不含 archive/）
# 只在 docs/ 一层，不递归 —— 递归会把以后新加的 audit 报告一起扫进来。
DOCS_DIR = os.path.join(ROOT, "docs")
SKIP_DIRS = {"archive"}

# 声明"当前版本"的词。刻意收窄：宁可漏，不要逼人写豁免。
CLAIM_WORDS = (
    "当前版本", "最新版本", "线上版本", "当前线上", "当前部署",
    "部署版本", "版本基线", "正在运行", "线上在跑",
)
CLAIM_RE = re.compile("|".join(re.escape(w) for w in CLAIM_WORDS))
VER_RE = re.compile(r"(?<![\d.])v?(\d+\.\d+\.\d+)(?![\d.])")

# 表格里的版本快照行：`| 版本 | 2.5.24 |` / `| **版本** | 2.5.24 |`
SNAPSHOT_ROW_RE = re.compile(r"^\s*\|\s*\**\s*版本\s*\**\s*\|\s*v?(\d+\.\d+\.\d+)\s*\|")

# 同一行出现这些词即视为"明确的时间标记"，跳过。
EXEMPT_MARKERS = (
    "历史", "当时", "曾", "旧版", "已废弃", "上轮", "示例", "成文于",
    "决策时点", "归档", "勿当作", "快照",
)

# 现状卡自己就是那张卡，允许有 `| 版本 | X |` 行（且第 1 条规则单独校验它）
SNAPSHOT_ALLOWED = {os.path.join("docs", "STATUS.md").replace("\\", "/")}


def read_version():
    with open(VERSION_FILE, encoding="utf-8") as fh:
        return fh.read().strip()


def status_card_version():
    """读 docs/STATUS.md auto 区块里的版本值；找不到返回 None。"""
    if not os.path.exists(STATUS):
        return None
    with open(STATUS, encoding="utf-8") as fh:
        text = fh.read()
    m = re.search(r"<!-- status:auto:begin -->(.*?)<!-- status:auto:end -->", text, re.S)
    if not m:
        return None
    row = re.search(r"^\s*\|\s*版本\s*\|\s*([\d.]+)\s*\|", m.group(1), re.M)
    return row.group(1).strip() if row else None


def iter_docs():
    readme = os.path.join(ROOT, "README.md")
    if os.path.exists(readme):
        yield "README.md", readme
    if not os.path.isdir(DOCS_DIR):
        return
    for name in sorted(os.listdir(DOCS_DIR)):
        if not name.endswith(".md"):
            continue
        full = os.path.join(DOCS_DIR, name)
        if not os.path.isfile(full):
            continue
        if name in SKIP_DIRS:
            continue
        yield "docs/" + name, full


def scan():
    """返回 (硬错, 声明漂移)。硬错无豁免，声明漂移可被 EXEMPT_MARKERS 放过。"""
    version = read_version()
    hard = []
    drift = []

    card = status_card_version()
    if card != version:
        hard.append(("docs/STATUS.md", 0,
                     f"现状卡写着 {card or '缺失'}，VERSION 是 {version}"
                     "（跑 python tools/status_snapshot.py --write 重算）"))

    for rel, full in iter_docs():
        with open(full, encoding="utf-8") as fh:
            for lineno, line in enumerate(fh, start=1):
                if not line.strip():
                    continue
                exempt = any(mk in line for mk in EXEMPT_MARKERS)

                # 规则 3：版本快照表（只许出现在现态卡）
                m = SNAPSHOT_ROW_RE.match(line)
                if m and rel not in SNAPSHOT_ALLOWED:
                    if m.group(1) != version and not exempt:
                        drift.append((rel, lineno, line.strip()[:110],
                                      "版本快照表只许在 docs/STATUS.md"))
                    continue

                # 规则 2：当前版本声明
                if exempt or not CLAIM_RE.search(line):
                    continue
                for vm in VER_RE.finditer(line):
                    if vm.group(1) != version:
                        drift.append((rel, lineno, line.strip()[:110],
                                      f"声称 {vm.group(1)}，VERSION 是 {version}"))
                        break

    return hard, drift


def main() -> int:
    hard, drift = scan()
    if not hard and not drift:
        print(f"[OK] 文档版本基线一致（VERSION={read_version()}），"
              "无非归档的『当前版本』声明")
        return 0

    if hard:
        print("[FAIL] 现状卡与 VERSION 不一致：")
        for rel, lineno, text in hard:
            print(f"  {rel}:{lineno}  {text}")
        print()

    if drift:
        print("[FAIL] 非归档文档在声明『当前版本』，请改为指向 docs/STATUS.md：")
        for rel, lineno, text, why in drift:
            print(f"  {rel}:{lineno}  {text}")
            print(f"      → {why}")
        print("\n  改法二选一：")
        print("    a) 删掉具体版本号，写「见 docs/STATUS.md」；")
        print("    b) 确认是历史陈述，就在同一行补个时间标记（当时/已废弃/成文于…）。")

    return 1


if __name__ == "__main__":
    sys.exit(main())
