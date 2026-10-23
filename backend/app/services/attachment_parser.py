"""知识点附件文本提取（供 RAG 索引使用）。

不引入新的重量级依赖：
- PDF 用已安装的 PyMuPDF（fitz）；
- xlsx 用 openpyxl；
- docx/pptx 本质是 zip+XML，直接解析文本节点；
- txt/md/csv 按 UTF-8/GB18030 解码。
图片/旧版 Office（doc/xls/ppt）暂不解析，返回空字符串，不影响附件上传与下载。
"""
from __future__ import annotations

import logging
import os
import zipfile
from typing import List
from xml.etree import ElementTree as ET

logger = logging.getLogger(__name__)

MAX_CHARS = 60000
MAX_PDF_PAGES = 40
MAX_SHEET_ROWS = 500
TEXT_EXTS = {".txt", ".md", ".csv"}


def _truncate(text: str) -> str:
    text = (text or "").strip()
    return text[:MAX_CHARS]


def _pdf_text(path: str) -> str:
    try:
        import fitz  # PyMuPDF
    except Exception as exc:  # noqa: BLE001
        logger.warning("PDF 解析不可用: %s", exc)
        return ""
    parts: List[str] = []
    try:
        with fitz.open(path) as doc:
            for page in doc[:MAX_PDF_PAGES]:
                parts.append(page.get_text("text") or "")
    except Exception as exc:  # noqa: BLE001
        logger.warning("PDF 文本提取失败 %s: %s", path, exc)
        return ""
    return _truncate("\n".join(parts))


def _xlsx_text(path: str) -> str:
    try:
        from openpyxl import load_workbook
    except Exception as exc:  # noqa: BLE001
        logger.warning("xlsx 解析不可用: %s", exc)
        return ""
    parts: List[str] = []
    try:
        wb = load_workbook(path, read_only=True, data_only=True)
        for ws in wb.worksheets:
            parts.append(f"工作表：{ws.title}")
            for i, row in enumerate(ws.iter_rows(values_only=True)):
                if i >= MAX_SHEET_ROWS:
                    break
                cells = [str(c) for c in row if c is not None and str(c).strip()]
                if cells:
                    parts.append(" | ".join(cells))
        wb.close()
    except Exception as exc:  # noqa: BLE001
        logger.warning("xlsx 文本提取失败 %s: %s", path, exc)
        return ""
    return _truncate("\n".join(parts))


def _zip_xml_text(path: str, prefix: str, tag: str) -> str:
    """从 docx/pptx 的 zip 包里提取指定 XML 标签文本。"""
    texts: List[str] = []
    try:
        with zipfile.ZipFile(path) as zf:
            names = [n for n in zf.namelist()
                     if n.startswith(prefix) and n.endswith(".xml") and "/_rels/" not in n]
            for name in sorted(names):
                try:
                    root = ET.fromstring(zf.read(name))
                except ET.ParseError:
                    continue
                for node in root.iter():
                    if node.tag.endswith("}" + tag) or node.tag == tag:
                        if node.text and node.text.strip():
                            texts.append(node.text.strip())
    except Exception as exc:  # noqa: BLE001
        logger.warning("Office XML 文本提取失败 %s: %s", path, exc)
        return ""
    return _truncate("\n".join(texts))


def _plain_text(path: str) -> str:
    try:
        raw = open(path, "rb").read()
    except OSError as exc:
        logger.warning("读取附件失败 %s: %s", path, exc)
        return ""
    for enc in ("utf-8-sig", "utf-8", "gb18030"):
        try:
            return _truncate(raw.decode(enc))
        except UnicodeDecodeError:
            continue
    return _truncate(raw.decode("utf-8", errors="ignore"))


def extract_text(file_path: str, filename: str = "") -> str:
    """提取附件文本；不支持/失败返回空字符串（调用方应视为不可索引）。"""
    if not file_path or not os.path.exists(file_path):
        return ""
    ext = os.path.splitext(filename or file_path)[1].lower()
    if ext == ".pdf":
        return _pdf_text(file_path)
    if ext == ".xlsx":
        return _xlsx_text(file_path)
    if ext == ".docx":
        return _zip_xml_text(file_path, "word/", "t")
    if ext == ".pptx":
        return _zip_xml_text(file_path, "ppt/slides/", "t")
    if ext in TEXT_EXTS:
        return _plain_text(file_path)
    return ""
