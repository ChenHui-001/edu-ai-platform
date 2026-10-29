# -*- coding: utf-8 -*-
"""CI 门禁：检测前端 res.data.data 陷阱。

axios 响应拦截器 return res（信封 {code, message, success, data}），
组件里 res.data 即业务数据；res.data.data 恒为 undefined，
表现为列表恒空、统计恒 0、详情打不开。曾全站 18 文件 52+ 处踩坑。

用法：
    python tools/check_data_data.py            # 扫描并退出码报错
    python tools/check_data_data.py --whitelist a.vue:b.vue   # 临时豁免

白名单：tools/check_data_data.whitelist 文件，每行一个相对路径（# 注释）。
"""
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCAN_DIRS = ["frontend/src/views", "frontend/src/components"]
PATTERN = re.compile(r"\w+\.data\.data")

WHITELIST_FILE = os.path.join(ROOT, "tools", "check_data_data.whitelist")


def load_whitelist():
    if not os.path.exists(WHITELIST_FILE):
        return set()
    out = set()
    for line in io.open(WHITELIST_FILE, encoding="utf-8"):
        line = line.split("#", 1)[0].strip()
        if line:
            out.add(line.replace("\\", "/"))
    return out


def main():
    whitelist = load_whitelist()
    for arg in sys.argv[1:]:
        if arg == "--whitelist":
            continue
        whitelist.update(a.replace("\\", "/") for a in arg.split(","))

    hits = []
    for sub in SCAN_DIRS:
        base = os.path.join(ROOT, sub)
        for dirpath, _, files in os.walk(base):
            for name in files:
                if not name.endswith(".vue"):
                    continue
                full = os.path.join(dirpath, name)
                rel = os.path.relpath(full, ROOT).replace("\\", "/")
                if rel in whitelist:
                    continue
                for i, line in enumerate(io.open(full, encoding="utf-8"), 1):
                    if PATTERN.search(line):
                        hits.append(f"{rel}:{i}: {line.strip()[:100]}")

    if hits:
        print(f"[check_data_data] 发现 {len(hits)} 处 res.data.data 陷阱：")
        for h in hits:
            print(" ", h)
        print("\n修复：res.data 即业务数据（拦截器已返回信封），"
              "正确写法 res.data / res.data?.items。")
        print("根源：axios 响应拦截器 `return res`（信封 {code,message,success,data}），"
              "组件里 `res.data` 已是业务数据，再点一层 `.data` 恒为 undefined。")
        sys.exit(1)
    print(f"[check_data_data] 通过：views/components 无 res.data.data 陷阱"
          f"（白名单 {len(whitelist)} 个文件）")


if __name__ == "__main__":
    main()
