#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""工作区明文凭据门禁。

只匹配“生产形态”的口令/密钥特征，避免把 README 里的本地演示账号误判：
  - 生产管理员/教师口令：*@Admin2026、*@2026! 等
  - 长 API Key：sk- 开头且长度足够
  - 私钥文件头
  - deploy_scripts/.deploy_pass 等专用凭据文件是否存在

命中时只输出文件与行号，不回显命中内容。
"""
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORKSPACE = os.path.dirname(ROOT)

PATTERNS = [
    ("prod_password", re.compile(r"(?:Prod|Sys)@[A-Za-z0-9]+2026!?[A-Za-z0-9]*")),
    ("prod_teacher", re.compile(r"Teacher@2026!?[A-Za-z0-9]*")),
    ("prod_student", re.compile(r"Student@2026!?[A-Za-z0-9]*")),
    ("api_key", re.compile(r"sk-[A-Za-z0-9]{32,}")),
    ("private_key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
]

SKIP_DIRS = {".git", "node_modules", "dist", "__pycache__", ".venv", "venv", "data"}
SKIP_EXTS = {".db", ".db-wal", ".db-shm", ".sqlite", ".sqlite3", ".png", ".jpg", ".jpeg",
             ".gif", ".webp", ".pdf", ".zip", ".7z", ".gz", ".pyc"}


def _iter_files(base):
    for root, dirs, files in os.walk(base):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for name in files:
            if os.path.splitext(name)[1].lower() in SKIP_EXTS:
                continue
            yield os.path.join(root, name)


def _tracked_files():
    try:
        out = subprocess.check_output(["git", "-C", ROOT, "ls-files", "-z"])
    except Exception:
        return list(_iter_files(ROOT))
    return [os.path.join(ROOT, p.decode("utf-8", "replace"))
            for p in out.split(b"\0") if p]


def _scan_file(path, findings):
    try:
        with open(path, encoding="utf-8", errors="ignore") as fh:
            for lineno, line in enumerate(fh, 1):
                for label, pattern in PATTERNS:
                    if pattern.search(line):
                        findings.append((os.path.relpath(path, WORKSPACE), lineno, label))
    except OSError:
        pass


def main():
    findings = []
    files = _tracked_files()
    # 工作区级补充：deploy_scripts / .workbuddy 不进应用仓库，但可能被误同步
    for extra in ("deploy_scripts", ".workbuddy"):
        base = os.path.join(WORKSPACE, extra)
        if os.path.isdir(base):
            files.extend(_iter_files(base))

    for path in files:
        _scan_file(path, findings)

    for rel in ("deploy_scripts/.deploy_pass", "deploy_scripts/deploy_pass"):
        if os.path.exists(os.path.join(WORKSPACE, rel)):
            findings.append((rel, 0, "plaintext_password_file"))

    if findings:
        print("[FAIL] 发现疑似明文凭据（只显示位置，不回显内容）：")
        for rel, lineno, label in findings:
            print(f"  - {rel}:{lineno}  [{label}]")
        print("\n处置：立即轮换对应口令/密钥，改为环境变量或操作系统凭据存储；不要只删文本。")
        return 1
    print(f"[OK] 未发现明文生产凭据（扫描 {len(files)} 个文件）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
