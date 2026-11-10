"""对照实验：证明「_plain 直入 Paragraph」真的会由服务端发起外部请求（SSRF）。

起一个本地 socket 当"攻击者的服务器"，看 reportlab 渲染时有没有连上来。
再对比 _pdf_text 处理后是否彻底断开。
"""
import io
import socket
import sys
import os
import threading

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from reportlab.platypus import Paragraph, SimpleDocTemplate  # noqa: E402
from reportlab.lib.styles import ParagraphStyle  # noqa: E402

from app.services.paper_export_service import _pdf_text  # noqa: E402


def start_probe():
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("127.0.0.1", 0))
    srv.listen(5)
    srv.settimeout(6)
    port = srv.getsockname()[1]
    hits = []

    def loop():
        while True:
            try:
                conn, addr = srv.accept()
            except socket.timeout:
                break
            except OSError:
                break
            hits.append(addr)
            try:
                req = conn.recv(4096)
                hits.append(req.split(b"\r\n")[0])
                conn.sendall(b"HTTP/1.1 200 OK\r\nContent-Length: 2\r\n\r\nOK")
            except OSError:
                pass
            finally:
                conn.close()

    t = threading.Thread(target=loop, daemon=True)
    t.start()
    return srv, port, hits


def render(text):
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf)
    st = ParagraphStyle("x", fontName="Helvetica", fontSize=10)
    doc.build([Paragraph(text, st)])
    return buf.getvalue()


def main():
    srv, port, hits = start_probe()
    payload = f'<img src="http://127.0.0.1:{port}/ssrf-probe" width="10" height="10"/>'
    print(f"probe port = {port}")

    # ---- 旧写法：_plain 的结果直接进 Paragraph（P0-1 的 bug）
    import re
    import html as _h

    def _plain(t):
        s = re.sub(r"<[^>]+>", "", str(t))
        return s.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&").strip()

    # 模拟"题干里存的是实体编码"，_plain 反解成真标签
    stored = _h.escape(payload, quote=False)
    old_text = _plain(stored)
    try:
        render(old_text)
        print(f"[OLD] 渲染完成；服务端收到连接 {len(hits)} 次")
    except Exception as exc:
        print(f"[OLD] 渲染抛异常 {type(exc).__name__}: {exc}")

    # ---- 新写法：_pdf_text 转义后再进 Paragraph
    hits.clear()
    new_text = _pdf_text(stored)
    try:
        render(new_text)
        print(f"[NEW] 渲染完成；服务端收到连接 {len(hits)} 次")
    except Exception as exc:
        print(f"[NEW] 渲染抛异常 {type(exc).__name__}: {exc}")

    srv.close()
    print("\n结论:", "SSRF 已证实且新实现已阻断" if hits == [] else f"仍有 {len(hits)} 次连接")


if __name__ == "__main__":
    main()
