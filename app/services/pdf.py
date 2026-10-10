import os
import uuid
from datetime import date

from reportlab.graphics import renderPDF
from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.graphics.shapes import Drawing
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas

from app.config import GENERATED_DIR


def build_output_path(job_id: str, cert_id: str) -> str:
    job_part = str(uuid.UUID(job_id))
    cert_part = str(uuid.UUID(cert_id))
    return os.path.join(GENERATED_DIR, job_part, f"{cert_part}.pdf")


def fit_font_size(text: str, font: str, max_size: float, max_width: float, min_size: float = 4) -> float:
    size = max_size
    while size > min_size and stringWidth(text, font, size) > max_width:
        size -= 1
    return size


def draw_qr(c: canvas.Canvas, url: str, x: float, y: float, size: float) -> None:
    widget = QrCodeWidget(url)
    x0, y0, x1, y1 = widget.getBounds()
    drawing = Drawing(size, size, transform=[size / (x1 - x0), 0, 0, size / (y1 - y0), 0, 0])
    drawing.add(widget)
    renderPDF.draw(drawing, c, x, y)


def generate_certificate(
    name: str, event: str, issue_date: date, out_path: str, verify_url: str | None = None
) -> None:
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    width, height = landscape(A4)
    c = canvas.Canvas(out_path, pagesize=(width, height))

    c.setLineWidth(4)
    c.rect(30, 30, width - 60, height - 60)
    c.setLineWidth(1)
    c.rect(40, 40, width - 80, height - 80)

    c.setFont("Helvetica-Bold", 40)
    c.drawCentredString(width / 2, height - 130, "Certificate of Participation")

    c.setFont("Helvetica", 18)
    c.drawCentredString(width / 2, height - 200, "This is to certify that")

    c.setFont("Helvetica-Bold", fit_font_size(name, "Helvetica-Bold", 34, width - 200))
    c.drawCentredString(width / 2, height / 2, name)

    c.setFont("Helvetica", 18)
    c.drawCentredString(width / 2, height / 2 - 60, "has participated in")

    c.setFont("Helvetica-Bold", fit_font_size(event, "Helvetica-Bold", 24, width - 200))
    c.drawCentredString(width / 2, height / 2 - 100, event)

    c.setFont("Helvetica", 16)
    c.drawCentredString(width / 2, 100, f"Issued on {issue_date.strftime('%d %B %Y')}")

    if verify_url:
        qr_size = 70
        qr_x = width - 40 - qr_size - 15
        draw_qr(c, verify_url, qr_x, 62, qr_size)
        c.setFont("Helvetica", 8)
        c.drawCentredString(qr_x + qr_size / 2, 50, "Scan to verify")

    c.showPage()
    c.save()
