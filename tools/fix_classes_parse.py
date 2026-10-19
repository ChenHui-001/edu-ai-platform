# -*- coding: utf-8 -*-
"""修三个学情页面的 classes 解析：/edu/classes 返回数组而非分页 items。"""
import io

OLD = "classes.value = res.data.data?.items || []"
NEW = (
    "// /edu/classes 返回数组（非分页 items），两种结构都兼容\n"
    "    const _d = res.data.data\n"
    "    classes.value = Array.isArray(_d) ? _d : (_d?.items || [])"
)

FILES = [
    "frontend/src/views/teacher/ClassAnalysis.vue",
    "frontend/src/views/teacher/StudentAnalysis.vue",
    "frontend/src/views/teacher/TeacherReport.vue",
]

for f in FILES:
    s = io.open(f, encoding="utf-8").read()
    n = s.count(OLD)
    s = s.replace(OLD, NEW)
    io.open(f, "w", encoding="utf-8", newline="\n").write(s)
    print(f, "->", n, "match")
