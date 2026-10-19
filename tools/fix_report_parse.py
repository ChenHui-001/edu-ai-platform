# -*- coding: utf-8 -*-
"""修学情三页的响应解析：拦截器已返回信封 {code, data}，
组件里 res.data 即业务数据，res.data.data 恒为 undefined。"""
import io
import re

FILES = [
    "frontend/src/views/teacher/ClassAnalysis.vue",
    "frontend/src/views/teacher/StudentAnalysis.vue",
    "frontend/src/views/teacher/TeacherReport.vue",
]

for f in FILES:
    s = io.open(f, encoding="utf-8").read()
    n = len(re.findall(r"\w+\.data\.data", s))
    # 统一：X.data.data -> X.data（仅学情三页，其它页面不动）
    s = re.sub(r"\b(\w+)\.data\.data", r"\1.data", s)
    io.open(f, "w", encoding="utf-8", newline="\n").write(s)
    print(f, "->", n, "处修复")

# 语法自检：Vue SFC 不好直接 ast，抽查关键行
for f in FILES:
    s = io.open(f, encoding="utf-8").read()
    assert ".data.data" not in s, f
print("全部修复完成")
