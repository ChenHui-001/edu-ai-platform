"""把 .bat 统一规范化为 **纯 ASCII、无 BOM、CRLF**。

背景（踩坑记录）：
  cmd.exe 解析 .bat 时，UTF-8 BOM 会粘在第一行命令上，导致
      '<BOM>@echo' 不是内部或外部命令
  → `@echo off` 没生效 → 整个脚本逐行回显 → 撞上中文行直接闪退。
  中文在 .bat 里必须靠 BOM 才能正确显示，但 BOM 又会破坏首行，
  两者不可兼得。解法：**bat 全部不含中文**（纯 ASCII 无 BOM），
  中文输出交给 start.ps1（ps1 可以安全持有 BOM，因为首行是 `<#` 注释块）。

用法：python tools/fix_bat_encoding.py
"""
import io
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOM = b"\xef\xbb\xbf"
TARGETS = ["start.bat", "stop.bat", "manage.bat", "tools/auto_ship.bat"]


def normalize(path: str) -> bool:
    """规范化为纯 ASCII 无 BOM + CRLF。返回是否发生了修改。"""
    raw = open(path, "rb").read()
    changed = False

    # 1) 剥离所有 BOM（可能在开头，也可能因多次写入而重复出现）
    while raw.startswith(BOM):
        raw = raw[len(BOM):]
        changed = True

    # 2) 统一行尾为 CRLF
    unified = raw.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
    if unified != raw:
        changed = True

    # 3) 校验纯 ASCII；非 ASCII 的行转注释，彻底移除中文
    try:
        unified.decode("ascii")
    except UnicodeDecodeError as exc:
        bad = unified.split(b"\r\n")[exc.start // 2] if b"\r\n" in unified[:exc.start] else b""
        raise SystemExit(
            f"[FAIL] {os.path.relpath(path)} 仍含非 ASCII 字符，请手工处理：{bad!r}"
        )

    if changed:
        open(path, "wb").write(unified)
    return changed


def main() -> None:
    for rel in TARGETS:
        p = os.path.join(ROOT, rel)
        if not os.path.exists(p):
            print(f"  [SKIP] {rel} 不存在")
            continue
        before = open(p, "rb").read()
        normalize(p)
        after = open(p, "rb").read()
        status = "已修复" if before != after else "本来就合规"
        bom_ok = not after.startswith(BOM)
        try:
            after.decode("ascii")
            ascii_ok = True
        except UnicodeDecodeError:
            ascii_ok = False
        crlf_ok = b"\n" not in after.replace(b"\r\n", b"")
        flag = "OK" if (bom_ok and ascii_ok and crlf_ok) else "FAIL"
        print(f"  [{flag}] {rel:22s} 无BOM={bom_ok} 纯ASCII={ascii_ok} "
              f"CRLF={crlf_ok} ({status})")


if __name__ == "__main__":
    main()