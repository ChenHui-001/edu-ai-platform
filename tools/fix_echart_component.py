# -*- coding: utf-8 -*-
"""全站替换 echarts-for-react(React) -> components/EChart.vue(Vue3)。
涉及 8 个页面；组件名两种大小写（ReactEcharts / ReactECharts）都要换。"""
import io

FILES = [
    "frontend/src/views/admin/AdminReport.vue",
    "frontend/src/views/Dashboard.vue",
    "frontend/src/views/student/MyReport.vue",
    "frontend/src/views/student/ScoreCenter.vue",
    "frontend/src/views/student/SmartReview.vue",
    "frontend/src/views/teacher/ClassAnalysis.vue",
    "frontend/src/views/teacher/StudentAnalysis.vue",
    "frontend/src/views/teacher/TeacherReport.vue",
]

for f in FILES:
    s = io.open(f, encoding="utf-8").read()
    orig = s
    # import 替换（两种命名）
    s = s.replace(
        "import ReactEcharts from 'echarts-for-react'",
        "import EChart from '@/components/EChart.vue'")
    s = s.replace(
        'import ReactECharts from "echarts-for-react"',
        'import EChart from "@/components/EChart.vue"')
    s = s.replace(
        "import ReactECharts from 'echarts-for-react'",
        "import EChart from '@/components/EChart.vue'")
    # 标签替换（开/闭标签、自闭合），两种命名
    for name in ("ReactEcharts", "ReactECharts"):
        s = s.replace(f"<{name} ", "<EChart ").replace(f"<{name}\n", "<EChart\n")
        s = s.replace(f"</{name}>", "</EChart>")
    if s != orig:
        io.open(f, "w", encoding="utf-8", newline="\n").write(s)
        print(f, "已替换")
    else:
        print(f, "无变化（检查 import 写法）")

# 残留检查
for f in FILES:
    s = io.open(f, encoding="utf-8").read()
    assert "echarts-for-react" not in s, f"{f} 仍有 echarts-for-react"
    assert "ReactEchart" not in s, f"{f} 仍有 ReactEchart 残留"
print("全部替换完成，无残留")
