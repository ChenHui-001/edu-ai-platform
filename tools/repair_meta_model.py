# -*- coding: utf-8 -*-
"""修复 docs/meta-model/ 里被写成字面 `n 的换行。

## 背景

这批文件是「源码逆向」工具的输出产物。工具在某些批次里把换行写成了
**字面量** `` `n ``（两个字符：反引号 + 字母 n），而不是真换行，
于是整段 Markdown 塌陷成一行，标题层级全部失效。

## 为什么不能只重排标题

塌陷的根因是换行本身被破坏了。只要把字面 `` `n `` 换回真换行，
原有的 Markdown 结构（标题、列表、段落）就自然恢复 ——
不需要重新推导任何内容，纯格式还原，无损。

## 附带处理

多行连续空行（\\n\\n\\n\\n+）压成两个 —— 塌陷段落还原后
会出现大段空行，那是「原本有多行内容被挤进一行」的残留。
"""
import os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MM = os.path.join(ROOT, "docs", "meta-model")

# 字面 `n （反引号 + n），但不能误伤 markdown 里的行内代码反引号
LITERAL_NL = re.compile(r"`n")


def repair(text: str) -> tuple[str, int]:
    """还原字面换行 + 压缩连续空行，返回 (新文本, 还原处数)。"""
    count = len(LITERAL_NL.findall(text))
    out = LITERAL_NL.sub("\n", text)
    # 塌陷还原后可能出现连续空行，压到最多两个
    out = re.sub(r"\n{4,}", "\n\n\n", out)
    return out, count


def main() -> int:
    if not os.path.isdir(MM):
        print(f"[FAIL] 找不到目录 {MM}")
        return 1
    changed = []
    for name in sorted(os.listdir(MM)):
        if not name.endswith(".md"):
            continue
        path = os.path.join(MM, name)
        with open(path, encoding="utf-8", errors="replace") as fh:
            old = fh.read()
        new, n = repair(old)
        if n or old != new:
            with open(path, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(new)
            changed.append((name, n))
    if not changed:
        print("[OK] 无需修复")
        return 0
    for name, n in changed:
        print(f"  修复 {name}（还原 {n} 处字面换行）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
