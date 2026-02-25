"""E2E test: PDF → TXT via CoreEngine.convert()."""

import pytest

import ufc.plugins  # noqa: F401 – ensure plugins are registered
from ufc.core.engine import CoreEngine


@pytest.fixture
def sample_pdf(tmp_path):
    """Create a simple PDF with text using fpdf2."""
    fpdf2 = pytest.importorskip("fpdf")
    pdf = fpdf2.FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    pdf.cell(text="Hello PDF World")
    pdf.ln()
    pdf.cell(text="Testing PDF conversion")
    path = tmp_path / "sample.pdf"
    pdf.output(str(path))
    return str(path)


def test_pdf_to_txt_conversion(sample_pdf, tmp_path):
    """CoreEngine.convert() should produce a .txt file with the expected text."""
    out_path = tmp_path / "output.txt"

    read_opts = {
        "include_headers": False,
        "include_tables": True,
        "keep_empty_paragraphs": False,
    }
    write_opts = {
        "include_tables": True,
        "table_format": "tsv",
        "normalize_tables": True,
        "utf8_bom": False,
        "enable_chunk": False,
        "chunk_size": 12000,
        "overlap": 300,
    }

    CoreEngine.convert(sample_pdf, str(out_path), read_opts, write_opts)

    assert out_path.exists()
    content = out_path.read_text(encoding="utf-8")
    assert "Hello PDF World" in content
    assert "Testing PDF conversion" in content


def test_pdf_to_txt_with_page_headers(sample_pdf, tmp_path):
    """When include_headers is True, output should contain page markers."""
    out_path = tmp_path / "output_hdr.txt"

    read_opts = {"include_headers": True, "include_tables": True}
    write_opts = {
        "include_tables": True,
        "table_format": "tsv",
        "normalize_tables": True,
        "utf8_bom": False,
        "enable_chunk": False,
        "chunk_size": 12000,
        "overlap": 300,
    }

    CoreEngine.convert(sample_pdf, str(out_path), read_opts, write_opts)

    content = out_path.read_text(encoding="utf-8")
    assert "Page 1" in content
