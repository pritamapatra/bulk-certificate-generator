from datetime import date
from unittest.mock import patch

from reportlab.lib.pagesizes import A4, landscape

from app.services import pdf
from app.services.pdf import generate_certificate


def _make(tmp_path, name, verify_url):
    out = tmp_path / name
    generate_certificate("Asha Rao", "QR Test", date(2026, 10, 1), str(out), verify_url)
    return out


def test_qr_drawn_with_exact_url(tmp_path):
    url = "https://example.com/verify/abc-123"
    with patch.object(pdf, "draw_qr", wraps=pdf.draw_qr) as spy:
        _make(tmp_path, "a.pdf", url)
    spy.assert_called_once()
    assert spy.call_args.args[1] == url


def test_qr_not_drawn_without_url(tmp_path):
    with patch.object(pdf, "draw_qr") as spy:
        _make(tmp_path, "b.pdf", None)
    spy.assert_not_called()


def test_qr_stays_inside_border(tmp_path):
    width, height = landscape(A4)
    with patch.object(pdf, "draw_qr") as spy:
        _make(tmp_path, "c.pdf", "https://example.com/verify/x")
    _, _, x, y, size = spy.call_args.args
    assert 40 < x and x + size < width - 40
    assert 40 < y and y + size < height - 40


def test_pdf_with_qr_is_valid_and_larger(tmp_path):
    with_qr = _make(tmp_path, "d.pdf", "https://example.com/verify/x")
    without = _make(tmp_path, "e.pdf", None)
    assert with_qr.read_bytes().startswith(b"%PDF")
    assert with_qr.stat().st_size > without.stat().st_size
