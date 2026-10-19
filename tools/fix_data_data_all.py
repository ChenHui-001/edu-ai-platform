# -*- coding: utf-8 -*-
"""全站修复 res.data.data 陷阱（18 文件 52 处）。

背景：axios 响应拦截器 return res（信封 {code,message,success,data}），
组件里 res.data 即业务数据，res.data.data 恒为 undefined。

替换规则（保守，逐类处理）：
  X.data.data?.items  ->  X.data?.items
  X.data.data || {}   ->  X.data || {}
  X.data.data || []   ->  X.data || []
  X.data.data         ->  X.data
"""
import io
import re
import glob

FILES = set()
for pat in ("frontend/src/views/**/*.vue", "frontend/src/components/**/*.vue"):
    for f in glob.glob(pat, recursive=True):
        s = io.open(f, encoding="utf-8").read()
        if re.search(r"\w+\.data\.data", s):
            FILES.add(f)

total = 0
report = []
for f in sorted(FILES):
    s = io.open(f, encoding="utf-8").read()
    orig = s
    n_before = len(re.findall(r"\w+\.data\.data", s))
    # 顺序很重要：先具体后一般
    s = re.sub(r"\b(\w+)\.data\.data\?\.items", r"\1.data?.items", s)
    s = re.sub(r"\b(\w+)\.data\.data\?\.", r"\1.data?.", s)
    s = re.sub(r"\b(\w+)\.data\.data", r"\1.data", s)
    n_after = len(re.findall(r"\w+\.data\.data", s))
    if s != orig:
        io.open(f, "w", encoding="utf-8", newline="\n").write(s)
        total += n_before - n_after
        report.append(f"{f}: {n_before} -> {n_after}")
    else:
        report.append(f"{f}: 无变化?")

for line in report:
    print(line)
print(f"\n共修复 {total} 处")

# 最终校验：全站不再有 data.data
left = []
for f in glob.glob("frontend/src/views/**/*.vue", recursive=True) + \
         glob.glob("frontend/src/components/**/*.vue", recursive=True):
    s = io.open(f, encoding="utf-8").read()
    for i, line in enumerate(s.splitlines(), 1):
        if re.search(r"\w+\.data\.data", line):
            left.append(f"{f}:{i}: {line.strip()[:90]}")
if left:
    print("仍有残留：")
    for l in left:
        print(" ", l)
else:
    print("全站 res.data.data 已清零")
