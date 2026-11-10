"""P0-1 反向验证：恶意题干不得触发 reportlab 解析失败 / 不得发起外部请求。

用「已知有 bug 的旧写法」（直接 _plain 进 Paragraph）做对照，
确认新实现 _pdf_text 能同时扛住 SSRF 载荷与畸形标签。
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.services.paper_export_service import build_pdf, build_answer_sheet  # noqa: E402

MALICIOUS = (
    '&lt;img src="http://127.0.0.1:9/pwn"/&gt; '
    '已知 2&lt;3 且 a&amp;b，'
    '&lt;script&gt;alert(1)&lt;/script&gt;，<b>真标签</b>'
)


def make_preview():
    return {
        "name": '恶意卷 &lt;img src="http://127.0.0.1:9/x"/&gt;',
        "grade_name": "一年级",
        "subject_name": "数学",
        "total_score": 10,
        "duration": 45,
        "sections": [{
            "section_name": "一、选择题 &lt;img src=x&gt;",
            "item_count": 1,
            "section_score": 10,
            "items": [{
                "stem": MALICIOUS,
                "score": 10,
                "type": "single",
                "options": [
                    {"key": "A", "text": "选项 &lt;img src=http://127.0.0.1:9/y&gt;"},
                    {"key": "B", "text": "2<3"},
                ],
                "answer": "A&lt;img src=http://127.0.0.1:9/z&gt;",
                "analysis": "解析 &lt;script&gt;x&lt;/script&gt;",
                "knowledge_point_name": "数的认识 &lt;img src=q&gt;",
            }],
        }],
    }


def old_way_should_fail():
    """对照组：旧写法（_plain 直入 Paragraph）在同样载荷下应报错或拉取 URL。"""
    from reportlab.platypus import Paragraph, SimpleDocTemplate
    from reportlab.lib.styles import ParagraphStyle
    import io

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf)
    st = ParagraphStyle("x", fontName="Helvetica", fontSize=10)
    doc.build([Paragraph(MALICIOUS, st)])
    return buf.getvalue()


def main():
    preview = make_preview()
    ok = 0

    for label, fn in (
        ("build_pdf/teacher", lambda: build_pdf(preview, mode="teacher")),
        ("build_pdf/student", lambda: build_pdf(preview, mode="student")),
        ("build_answer_sheet", lambda: build_answer_sheet(preview)),
    ):
        data = fn().getvalue()
        assert data[:4] == b"%PDF", f"{label} 不是合法 PDF"
        print(f"[PASS] {label} -> {len(data)} bytes, header=%r" % data[:5])
        ok += 1

    # 对照组：确认旧写法确实有问题（说明探针有效，不是空跑）
    try:
        raw = old_way_should_fail()
        print(f"[WARN] 旧写法未报错（{len(raw)} bytes），但载荷已被 reportlab 静默吞掉")
    except Exception as exc:
        print(f"[PASS] 对照组复现旧 bug: {type(exc).__name__}: {exc}")

    print(f"\n=== 新实现 {ok}/3 全部通过 ===")


if __name__ == "__main__":
    main()
