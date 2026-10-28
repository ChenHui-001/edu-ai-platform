"""试卷导出服务：Word(.docx) / PDF / 答题卡 / 可打印 HTML。

排版能力
--------
- 学生卷：无答案与解析；教师卷：含答案、解析、知识点标注
- A3 双栏 / A4 单栏
- 密封线（装订线）、页眉（试卷名）、页脚页码
- 答题卡：客观题涂卡格 + 主观题作答框

中文字体
--------
reportlab 内置字体不含中文，直接用会输出黑块。这里按优先级尝试系统 CJK
字体（Linux 容器用 Noto/文泉驿，Windows 用宋体/黑体），全部找不到时退回
内置 CID 字体 STSong-Light（reportlab 自带的中日韩字体包，无需字体文件）。
**这一步不能省**：汉字渲染成方块是导出功能最常见的"看起来成功其实不可用"。
"""
import io
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------- 常量
A4_WIDTH, A4_HEIGHT = 595.28, 841.89      # pt
A3_WIDTH, A3_HEIGHT = 841.89, 1190.55     # pt

_CN_FONT_CANDIDATES = [
    # Linux（Docker 容器常见）
    ("NotoSansCJK", "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
    ("NotoSansSC", "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc"),
    ("WenQuanYi", "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"),
    ("WenQuanYiMicro", "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc"),
    # Windows（本地开发）
    ("SimSun", "C:/Windows/Fonts/simsun.ttc"),
    ("SimHei", "C:/Windows/Fonts/simhei.ttf"),
    ("MicrosoftYaHei", "C:/Windows/Fonts/msyh.ttc"),
]

_CN_FONT_NAME: Optional[str] = None
_CN_FONT_READY = False


def _ensure_cn_font() -> str:
    """注册中文字体并返回字体名。找不到字体文件时回落到 STSong-Light。"""
    global _CN_FONT_NAME, _CN_FONT_READY
    if _CN_FONT_READY and _CN_FONT_NAME:
        return _CN_FONT_NAME

    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    import os

    for name, path in _CN_FONT_CANDIDATES:
        if not os.path.exists(path):
            continue
        try:
            # .ttc 是字体集合，reportlab 需指定 subfontIndex
            if path.lower().endswith(".ttc"):
                pdfmetrics.registerFont(TTFont(name, path, subfontIndex=0))
            else:
                pdfmetrics.registerFont(TTFont(name, path))
            _CN_FONT_NAME = name
            _CN_FONT_READY = True
            logger.info("PDF 导出使用中文字体：%s (%s)", name, path)
            return name
        except Exception as exc:  # noqa: BLE001
            logger.warning("注册中文字体失败 %s: %s", path, exc)

    # 兜底：reportlab 自带 CID 字体，无需字体文件
    try:
        from reportlab.pdfbase.cidfonts import UnicodeCIDFont
        pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
        _CN_FONT_NAME = "STSong-Light"
        _CN_FONT_READY = True
        logger.warning("未找到系统中文字体，PDF 使用内置 STSong-Light")
        return _CN_FONT_NAME
    except Exception as exc:  # noqa: BLE001
        logger.error("中文字体全部不可用，PDF 中文将无法正常显示: %s", exc)
        _CN_FONT_NAME = "Helvetica"
        _CN_FONT_READY = True
        return _CN_FONT_NAME


# ---------------------------------------------------------------- 文本工具
def _plain(text: Any) -> str:
    """把可能含 HTML/富文本的题干转成纯文本（导出用）。"""
    if text is None:
        return ""
    s = str(text)
    # 去标签（题干可能来自富文本编辑器）
    import re
    s = re.sub(r"<br\s*/?>", "\n", s, flags=re.IGNORECASE)
    s = re.sub(r"</p>", "\n", s, flags=re.IGNORECASE)
    s = re.sub(r"<[^>]+>", "", s)
    s = s.replace("&nbsp;", " ").replace("&lt;", "<").replace("&gt;", ">")
    s = s.replace("&amp;", "&")
    return s.strip()


def _h(text: Any) -> str:
    """`_plain` 之后再按 HTML 语义转义（供 build_print_html 这类拼 HTML 的场景）。

    **不能直接把 `_plain` 的结果塞进 HTML**：`_plain` 会把 `&lt;` 反解成 `<`，
    于是题干里的 `&lt;script&gt;alert(1)&lt;/script&gt;` 会变成可执行标签。
    导出页由前端 `document.write` 打开（about:blank 继承同源），可窃取登录态。
    docx/pdf 走的是纯文本 API，不能用本函数（否则会打印出 &lt; 字面量）。
    """
    import html as _html
    return _html.escape(_plain(text), quote=False)


def _option_text(options: Any) -> List[str]:
    if not options:
        return []
    if isinstance(options, list):
        out = []
        for o in options:
            if isinstance(o, dict):
                key = o.get("key") or o.get("label") or ""
                text = _plain(o.get("text") or o.get("content") or "")
                out.append(f"{key}. {text}".strip(". ").strip() or text)
            else:
                out.append(_plain(o))
        return out
    return [_plain(options)]


def _answer_text(answer: Any, qtype: Optional[str] = None) -> str:
    if answer is None:
        return ""
    if isinstance(answer, list):
        return "".join(str(a) for a in answer)
    if isinstance(answer, dict):
        return str(answer.get("value") or answer.get("text") or "")
    s = str(answer)
    # 判断题的 JSON 字符串 "true"/"false" → 正确/错误
    low = s.strip().strip('"').lower()
    if qtype == "judge" and low in ("true", "false", "a", "b"):
        return {"true": "正确", "false": "错误", "a": "正确", "b": "错误"}[low]
    return s.strip('"')


def _layout_dims(layout: str):
    """返回 (页面宽, 高, 是否双栏)。"""
    if layout == "a3_double":
        return A3_WIDTH, A3_HEIGHT, True
    return A4_WIDTH, A4_HEIGHT, False


# ---------------------------------------------------------------- HTML
_CSS_COMMON = """
@page { size: %(size)s; margin: 18mm 15mm 16mm 15mm; }
* { box-sizing: border-box; }
body { font-family: "SimSun", "Songti SC", "Noto Serif CJK SC", serif;
       font-size: 11pt; line-height: 1.7; color: #000; margin: 0; }
.hdr { text-align: center; margin-bottom: 6mm; }
.hdr h1 { font-size: 18pt; margin: 0 0 3mm 0; letter-spacing: 1px; }
.meta { text-align: center; font-size: 10.5pt; color: #222; margin-bottom: 2mm; }
.meta span { margin: 0 4mm; }
.info-bar { border: 1px solid #000; padding: 2mm 3mm; font-size: 10pt; margin-bottom: 4mm; }
.sec-title { font-size: 13pt; font-weight: bold; margin: 6mm 0 3mm 0;
             border-bottom: 1px solid #000; padding-bottom: 1mm; }
.sec-note { font-size: 9.5pt; color: #333; font-weight: normal; margin-left: 3mm; }
.q { margin: 0 0 4mm 0; page-break-inside: avoid; break-inside: avoid; }
.q-stem { text-align: justify; }
.q-no { font-weight: bold; margin-right: 1mm; }
.opts { margin: 1.5mm 0 0 6mm; }
.opt { display: inline-block; min-width: 45%%; margin-right: 4mm; }
.ans { margin: 1.5mm 0 0 6mm; padding: 1.5mm 2mm; background: #f4f4f4;
       border-left: 2px solid #666; font-size: 10pt; }
.ans b { color: #000; }
.blank-line { display: inline-block; border-bottom: 1px solid #000;
              min-width: 30mm; height: 1em; }
/* 密封线 */
.seal { position: fixed; left: 0; top: 0; bottom: 0; width: 14mm;
        border-right: 1px dashed #000; font-size: 9pt; }
.seal-inner { writing-mode: vertical-rl; text-orientation: upright;
              padding: 20mm 0 0 3mm; letter-spacing: 3mm; }
/* 双栏 */
.twocol { column-count: 2; column-gap: 10mm; column-rule: 1px dashed #999; }
.twocol .q { break-inside: avoid; }
.foot { position: fixed; bottom: 4mm; left: 0; right: 0; text-align: center;
        font-size: 9pt; color: #444; }
.answerbox { border: 1px solid #000; min-height: 18mm; margin: 1mm 0 4mm 6mm; }
.sheet-grid { border-collapse: collapse; width: 100%%; font-size: 10pt; }
.sheet-grid th, .sheet-grid td { border: 1px solid #000; padding: 1.5mm 2mm; }
.sheet-grid th { background: #eee; }
.bubble { display: inline-block; width: 6mm; height: 6mm; border: 1px solid #000;
          border-radius: 50%%; text-align: center; line-height: 6mm;
          margin-right: 2mm; font-size: 8pt; }
@media print { .no-print { display: none; } body { margin: 0; } }
"""


def build_print_html(preview: Dict[str, Any], *, mode: str = "teacher",
                     layout: str = "a4_single") -> str:
    """生成可打印 HTML（不依赖 Word/PDF 引擎，浏览器 Ctrl+P 即可）。"""
    size = "A3" if layout == "a3_double" else "A4"
    css = _CSS_COMMON % {"size": size}
    paper = preview
    two = layout == "a3_double"

    parts: List[str] = [
        "<!DOCTYPE html><html><head><meta charset='utf-8'>",
        f"<title>{_h(paper.get('name'))}</title>",
        f"<style>{css}</style></head><body>",
    ]

    parts.append("<div class='hdr'>")
    parts.append(f"<h1>{_h(paper.get('name'))}</h1>")
    meta = (f"{paper.get('grade_name') or ''} {paper.get('subject_name') or ''}"
            f"<span>总分：{paper.get('total_score')}</span>"
            f"<span>时间：{paper.get('duration')} 分钟</span>")
    parts.append(f"<div class='meta'>{meta}</div>")
    parts.append("</div>")

    # 学生信息栏
    parts.append(
        "<div class='info-bar'>姓名：<span class='blank-line'></span>　"
        "班级：<span class='blank-line'></span>　"
        "学号：<span class='blank-line'></span>　"
        "得分：<span class='blank-line'></span></div>")

    body_parts: List[str] = []
    qno = 0
    for sec in paper.get("sections") or []:
        body_parts.append(
            f"<div class='sec-title'>{_h(sec.get('section_name'))}"
            f"<span class='sec-note'>（共 {sec.get('item_count')} 题，"
            f"共 {sec.get('section_score')} 分）</span></div>")
        for it in sec.get("items") or []:
            qno += 1
            body_parts.append("<div class='q'>")
            stem = _h(it.get("stem"))
            body_parts.append(
                f"<div class='q-stem'><span class='q-no'>{qno}.</span>"
                f"<span style='color:#555;font-size:9.5pt'>（{it.get('score')}分）</span>"
                f" {stem}</div>")
            opts = _option_text(it.get("options"))
            if opts:
                body_parts.append("<div class='opts'>")
                for o in opts:
                    body_parts.append(f"<span class='opt'>{_h(o)}</span>")
                body_parts.append("</div>")
            if mode == "teacher":
                ans = _answer_text(it.get("answer"), it.get("type"))
                ana = _h(it.get("analysis"))
                kp = it.get("knowledge_point_name")
                block = f"<div class='ans'><b>答案：</b>{_h(ans) or '（略）'}"
                if ana:
                    block += f"<br/><b>解析：</b>{ana}"
                if kp:
                    block += f"<br/><b>知识点：</b>{_h(kp)}"
                block += "</div>"
                body_parts.append(block)
            body_parts.append("</div>")

    if two:
        parts.append("<div class='twocol'>" + "".join(body_parts) + "</div>")
    else:
        parts.append("".join(body_parts))

    parts.append(f"<div class='foot'>{_h(paper.get('name'))}</div>")
    parts.append("</body></html>")
    return "\n".join(parts)


# ---------------------------------------------------------------- DOCX
def build_docx(preview: Dict[str, Any], *, mode: str = "teacher",
               layout: str = "a4_single", with_seal_line: bool = True,
               with_page_number: bool = True) -> io.BytesIO:
    """生成 .docx。

    python-docx 不直接支持「双栏」与「页码域」，用底层 OOXML 补充：
    - 双栏：`w:cols w:num="2"`
    - 页码：`PAGE` 域（否则 docx 里页码是死文本）
    """
    from docx import Document
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.shared import Cm, Pt

    doc = Document()

    # 页面设置
    sec0 = doc.sections[0]
    if layout == "a3_double":
        sec0.page_width = Cm(42.0)
        sec0.page_height = Cm(29.7)
        sec0.orientation = 1  # landscape
    else:
        sec0.page_width = Cm(21.0)
        sec0.page_height = Cm(29.7)
    sec0.left_margin = Cm(2.2 if with_seal_line else 2.0)
    sec0.right_margin = Cm(2.0)
    sec0.top_margin = Cm(2.0)
    sec0.bottom_margin = Cm(1.8)

    # 双栏
    if layout == "a3_double":
        sect_pr = sec0._sectPr
        cols = sect_pr.find(qn("w:cols"))
        if cols is None:
            cols = OxmlElement("w:cols")
            sect_pr.append(cols)
        cols.set(qn("w:num"), "2")
        cols.set(qn("w:space"), "425")

    # 中文字体
    style = doc.styles["Normal"]
    style.font.name = "宋体"
    style.font.size = Pt(11)
    style.element.rPr.rFonts.set(qn("w:eastAsia"), "宋体")

    # 标题
    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = title.add_run(_plain(preview.get("name")))
    run.font.size = Pt(18)
    run.bold = True
    run.font.name = "黑体"
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "黑体")

    meta = doc.add_paragraph()
    meta.alignment = WD_ALIGN_PARAGRAPH.CENTER
    meta_run = meta.add_run(
        f"{preview.get('grade_name') or ''} {preview.get('subject_name') or ''}　"
        f"总分：{preview.get('total_score')}　时间：{preview.get('duration')} 分钟")
    meta_run.font.size = Pt(10.5)

    # 学生信息栏
    info = doc.add_paragraph()
    info.add_run("姓名：____________　班级：____________　"
                 "学号：____________　得分：__________").font.size = Pt(10)
    _add_bottom_border(info)

    qno = 0
    for sec in preview.get("sections") or []:
        sp = doc.add_paragraph()
        srun = sp.add_run(_plain(sec.get("section_name")))
        srun.bold = True
        srun.font.size = Pt(13)
        srun.font.name = "黑体"
        srun._element.rPr.rFonts.set(qn("w:eastAsia"), "黑体")
        note = sp.add_run(f"（共 {sec.get('item_count')} 题，共 {sec.get('section_score')} 分）")
        note.font.size = Pt(9.5)

        for it in sec.get("items") or []:
            qno += 1
            stem_p = doc.add_paragraph()
            stem_p.paragraph_format.space_after = Pt(2)
            num = stem_p.add_run(f"{qno}. ")
            num.bold = True
            stem_p.add_run(f"（{it.get('score')}分）").font.size = Pt(9.5)
            stem_p.add_run(_plain(it.get("stem")))
            for o in _option_text(it.get("options")):
                opt_p = doc.add_paragraph()
                opt_p.paragraph_format.left_indent = Cm(0.6)
                opt_p.paragraph_format.space_after = Pt(0)
                opt_p.add_run(o).font.size = Pt(10.5)
            if mode == "teacher":
                ans_p = doc.add_paragraph()
                ans_p.paragraph_format.left_indent = Cm(0.6)
                ans = _answer_text(it.get("answer"), it.get("type"))
                ar = ans_p.add_run(f"答案：{ans or '（略）'}")
                ar.font.size = Pt(9.5)
                ar.bold = True
                ana = _plain(it.get("analysis"))
                if ana:
                    ans_p.add_run(f"　解析：{ana}").font.size = Pt(9.5)
                if it.get("knowledge_point_name"):
                    ans_p.add_run(
                        f"　知识点：{it['knowledge_point_name']}").font.size = Pt(9)

    # 页眉 / 页脚页码
    _add_header(sec0, _plain(preview.get("name")))
    if with_page_number:
        _add_page_number(sec0)

    # 密封线（用页边距里的文本框实现成本高，这里用首段落竖排提示）
    if with_seal_line:
        seal = doc.add_paragraph()
        seal_run = seal.add_run("考生答题不得超过此密封线　"
                                "———————————————")
        seal_run.font.size = Pt(8)
        seal_run.font.color.rgb = None
        seal.alignment = WD_ALIGN_PARAGRAPH.LEFT
        # 移到文首
        seal._element.getparent().remove(seal._element)
        doc.element.body.insert(0, seal._element)

    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf


def _add_bottom_border(paragraph) -> None:
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    pPr = paragraph._p.get_or_add_pPr()
    borders = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), "6")
    borders.append(bottom)
    pPr.append(borders)


def _add_header(section, text: str) -> None:
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.shared import Pt
    header = section.header
    p = header.paragraphs[0] if header.paragraphs else header.add_paragraph()
    p.text = ""
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.add_run(text).font.size = Pt(9)


def _add_page_number(section) -> None:
    """插入真实页码域（PAGE 域），而非静态文本。"""
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.shared import Pt

    footer = section.footer
    p = footer.paragraphs[0] if footer.paragraphs else footer.add_paragraph()
    p.text = ""
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER

    prefix = p.add_run("第 ")
    prefix.font.size = Pt(9)

    run = p.add_run()
    run.font.size = Pt(9)
    fld_begin = OxmlElement("w:fldChar")
    fld_begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = "PAGE"
    fld_end = OxmlElement("w:fldChar")
    fld_end.set(qn("w:fldCharType"), "end")
    run._r.append(fld_begin)
    run._r.append(instr)
    run._r.append(fld_end)

    suffix = p.add_run(" 页")
    suffix.font.size = Pt(9)


# ---------------------------------------------------------------- PDF
def build_pdf(preview: Dict[str, Any], *, mode: str = "teacher",
              layout: str = "a4_single", with_seal_line: bool = True,
              with_page_number: bool = True) -> io.BytesIO:
    """生成 PDF（reportlab platypus）。"""
    from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        BaseDocTemplate, Frame, KeepTogether, PageTemplate, Paragraph,
        Spacer, Table, TableStyle,
    )
    from reportlab.lib import colors

    font = _ensure_cn_font()
    width, height, two_col = _layout_dims(layout)

    buf = io.BytesIO()
    margin_l = 22 * mm if with_seal_line else 18 * mm
    doc = BaseDocTemplate(
        buf, pagesize=(width, height),
        leftMargin=margin_l, rightMargin=16 * mm,
        topMargin=16 * mm, bottomMargin=16 * mm,
        title=_plain(preview.get("name")),
    )

    body_w = width - margin_l - 16 * mm
    if two_col:
        gap = 8 * mm
        col_w = (body_w - gap) / 2
        gap_w = gap
    else:
        col_w = body_w
        gap_w = 0

    # 样式
    st_title = ParagraphStyle("t", fontName=font, fontSize=17, leading=24,
                              alignment=TA_CENTER, spaceAfter=4)
    st_meta = ParagraphStyle("m", fontName=font, fontSize=10.5, leading=16,
                             alignment=TA_CENTER, spaceAfter=6)
    st_sec = ParagraphStyle("s", fontName=font, fontSize=12.5, leading=20,
                            spaceBefore=8, spaceAfter=4)
    st_stem = ParagraphStyle("q", fontName=font, fontSize=10.5, leading=17,
                             alignment=TA_JUSTIFY, spaceAfter=2)
    st_opt = ParagraphStyle("o", fontName=font, fontSize=10.5, leading=16,
                            leftIndent=12, spaceAfter=0)
    st_ans = ParagraphStyle("a", fontName=font, fontSize=9.5, leading=15,
                            leftIndent=12, textColor=colors.HexColor("#333333"),
                            backColor=colors.HexColor("#f4f4f4"), spaceAfter=6)

    def _decorate(canvas, doc_obj):
        canvas.saveState()
        # 页眉
        canvas.setFont(font, 8.5)
        canvas.setFillColor(colors.HexColor("#444444"))
        canvas.drawCentredString(width / 2, height - 10 * mm,
                                 _plain(preview.get("name"))[:60])
        # 页脚页码
        if with_page_number:
            canvas.setFont(font, 9)
            canvas.drawCentredString(width / 2, 8 * mm,
                                     f"第 {doc_obj.page} 页")
        # 密封线（左侧竖排虚线）
        if with_seal_line:
            canvas.setDash(2, 3)
            canvas.setStrokeColor(colors.black)
            canvas.line(14 * mm, 20 * mm, 14 * mm, height - 20 * mm)
            canvas.setDash()
            canvas.setFont(font, 9)
            canvas.saveState()
            canvas.translate(11 * mm, height / 2)
            canvas.rotate(90)
            canvas.drawCentredString(0, 0, "密 封 线 内 不 要 答 题")
            canvas.restoreState()
        canvas.restoreState()

    if two_col:
        frame_l = Frame(margin_l, 16 * mm, col_w, height - 32 * mm,
                        leftPadding=0, rightPadding=0, id="left")
        frame_r = Frame(margin_l + col_w + gap_w, 16 * mm, col_w, height - 32 * mm,
                        leftPadding=0, rightPadding=0, id="right")
        doc.addPageTemplates([
            PageTemplate(id="two", frames=[frame_l, frame_r], onPage=_decorate)])
    else:
        frame = Frame(margin_l, 16 * mm, col_w, height - 32 * mm,
                      leftPadding=0, rightPadding=0, id="main")
        doc.addPageTemplates([PageTemplate(id="one", frames=[frame], onPage=_decorate)])

    story: List[Any] = []
    story.append(Paragraph(_plain(preview.get("name")), st_title))
    story.append(Paragraph(
        f"{preview.get('grade_name') or ''} {preview.get('subject_name') or ''}　"
        f"总分：{preview.get('total_score')}　时间：{preview.get('duration')} 分钟",
        st_meta))
    info_tbl = Table(
        [["姓名：", "", "班级：", "", "学号：", "", "得分：", ""]],
        colWidths=[col_w * x for x in (0.07, 0.18, 0.07, 0.18, 0.07, 0.18, 0.07, 0.18)],
    )
    info_tbl.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), font),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LINEBELOW", (1, 0), (1, 0), 0.5, colors.black),
        ("LINEBELOW", (3, 0), (3, 0), 0.5, colors.black),
        ("LINEBELOW", (5, 0), (5, 0), 0.5, colors.black),
        ("LINEBELOW", (7, 0), (7, 0), 0.5, colors.black),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(info_tbl)
    story.append(Spacer(1, 6))

    qno = 0
    for sec in preview.get("sections") or []:
        story.append(Paragraph(
            f"<b>{_plain(sec.get('section_name'))}</b>"
            f"<font size=9>（共 {sec.get('item_count')} 题，"
            f"共 {sec.get('section_score')} 分）</font>", st_sec))
        for it in sec.get("items") or []:
            qno += 1
            block: List[Any] = []
            block.append(Paragraph(
                f"<b>{qno}.</b><font size=9 color='#555555'>"
                f"（{it.get('score')}分）</font> {_plain(it.get('stem'))}", st_stem))
            for o in _option_text(it.get("options")):
                block.append(Paragraph(o, st_opt))
            if mode == "teacher":
                ans = _answer_text(it.get("answer"), it.get("type"))
                ana = _plain(it.get("analysis"))
                txt = f"<b>答案：</b>{ans or '（略）'}"
                if ana:
                    txt += f"　<b>解析：</b>{ana}"
                if it.get("knowledge_point_name"):
                    txt += f"　<b>知识点：</b>{it['knowledge_point_name']}"
                block.append(Paragraph(txt, st_ans))
            block.append(Spacer(1, 5))
            story.append(KeepTogether(block))

    doc.build(story)
    buf.seek(0)
    return buf


# ---------------------------------------------------------------- 答题卡
def build_answer_sheet(preview: Dict[str, Any], *, layout: str = "a4_single") -> io.BytesIO:
    """生成答题卡 PDF：客观题涂卡格 + 主观题作答框。"""
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        BaseDocTemplate, Frame, PageTemplate, Paragraph, Spacer, Table, TableStyle,
    )

    font = _ensure_cn_font()
    width, height, _two = _layout_dims(layout)
    buf = io.BytesIO()
    margin = 18 * mm
    doc = BaseDocTemplate(
        buf, pagesize=(width, height),
        leftMargin=margin, rightMargin=margin,
        topMargin=16 * mm, bottomMargin=16 * mm,
        title=f"答题卡-{_plain(preview.get('name'))}",
    )
    body_w = width - 2 * margin

    def _decorate(canvas, doc_obj):
        canvas.saveState()
        canvas.setFont(font, 9)
        canvas.drawCentredString(width / 2, 8 * mm, f"第 {doc_obj.page} 页")
        canvas.restoreState()

    doc.addPageTemplates([PageTemplate(
        id="one", frames=[Frame(margin, 16 * mm, body_w, height - 32 * mm,
                                leftPadding=0, rightPadding=0)],
        onPage=_decorate)])

    st_title = ParagraphStyle("t", fontName=font, fontSize=16, leading=22,
                              alignment=TA_CENTER, spaceAfter=4)
    st_meta = ParagraphStyle("m", fontName=font, fontSize=10, leading=15,
                             alignment=TA_CENTER, spaceAfter=8)
    st_sec = ParagraphStyle("s", fontName=font, fontSize=12, leading=18,
                            spaceBefore=8, spaceAfter=4)
    st_norm = ParagraphStyle("n", fontName=font, fontSize=10, leading=16)

    story: List[Any] = [
        Paragraph(f"答题卡　{_plain(preview.get('name'))}", st_title),
        Paragraph(
            f"{preview.get('grade_name') or ''} {preview.get('subject_name') or ''}　"
            f"总分：{preview.get('total_score')}　时间：{preview.get('duration')} 分钟",
            st_meta),
    ]

    # 考生信息
    info = Table([["姓名", "", "班级", "", "考号", ""]],
                 colWidths=[body_w * x for x in (0.08, 0.25, 0.08, 0.25, 0.08, 0.26)])
    info.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), font),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("GRID", (0, 0), (-1, -1), 0.6, colors.black),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(info)
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "<b>注意事项：</b>1. 答题前请填写姓名、班级、考号。"
        "2. 客观题请用 2B 铅笔填涂，主观题用 0.5mm 黑色签字笔书写。"
        "3. 请在对应题号区域内作答，超出部分无效。", st_norm))
    story.append(Spacer(1, 8))

    # 客观题涂卡区
    objective = []
    subjective = []
    for sec in preview.get("sections") or []:
        for it in sec.get("items") or []:
            qtype = it.get("type")
            if qtype in ("single", "multiple", "judge", "blank"):
                objective.append(it)
            else:
                subjective.append(it)

    qno = 0
    if objective:
        story.append(Paragraph("一、客观题填涂区", st_sec))
        rows = []
        buf_row: List[str] = []
        for it in objective:
            qno += 1
            n_opts = len(_option_text(it.get("options"))) or 4
            letters = "ABCD"[:max(2, min(n_opts, 4))]
            cells = " ".join(f"○{c}" for c in letters)
            buf_row.append(f"{qno}. {cells}")
            if len(buf_row) == 4:
                rows.append(buf_row)
                buf_row = []
        if buf_row:
            rows.append(buf_row + [""] * (4 - len(buf_row)))
        if rows:
            grid = Table(rows, colWidths=[body_w / 4] * 4)
            grid.setStyle(TableStyle([
                ("FONTNAME", (0, 0), (-1, -1), font),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#999999")),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]))
            story.append(grid)
        story.append(Spacer(1, 8))

    if subjective:
        story.append(Paragraph("二、主观题作答区", st_sec))
        for idx, it in enumerate(subjective, start=qno + 1):
            story.append(Paragraph(
                f"<b>{idx}.</b>（{it.get('score')}分）"
                f"<font size=9 color='#666666'>"
                f"{_plain(it.get('stem'))[:80]}</font>", st_norm))
            box_h = max(22 * mm, min(60 * mm, float(it.get("score") or 5) * 4 * mm))
            box = Table([[""]], colWidths=[body_w], rowHeights=[box_h])
            box.setStyle(TableStyle([
                ("GRID", (0, 0), (-1, -1), 0.6, colors.black),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]))
            story.append(box)
            story.append(Spacer(1, 6))

    doc.build(story)
    buf.seek(0)
    return buf
