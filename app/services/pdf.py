from datetime import date

from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas


def generate_certificate(name: str, event: str, issue_date: date, out_path: str) -> None:
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

    c.setFont("Helvetica-Bold", 34)
    c.drawCentredString(width / 2, height / 2, name)

    c.setFont("Helvetica", 18)
    c.drawCentredString(width / 2, height / 2 - 60, "has participated in")

    c.setFont("Helvetica-Bold", 24)
    c.drawCentredString(width / 2, height / 2 - 100, event)

    c.setFont("Helvetica", 16)
    c.drawCentredString(width / 2, 100, f"Issued on {issue_date.strftime('%d %B %Y')}")

    c.showPage()
    c.save()
