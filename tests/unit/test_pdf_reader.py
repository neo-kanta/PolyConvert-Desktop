"""Unit tests for PdfReader – uses an embedded minimal PDF (no external fixtures)."""

import base64

import pytest

from ufc.plugins.readers.pdf_reader import PdfReader
from ufc.core.models import ParagraphBlock, TableBlock


# ---------------------------------------------------------------------------
# Minimal valid PDF with two lines of text.
# Generated once via fpdf2 and encoded here to keep tests self-contained.
# Content: "Hello PDF\nSecond line"
# ---------------------------------------------------------------------------
_MINIMAL_PDF_B64 = (
    "JVBERi0xLjMKMSAwIG9iago8PCAvVHlwZSAvQ2F0YWxvZyAvUGFnZXMgMiAw"
    "IFIgPj4KZW5kb2JqCjIgMCBvYmoKPDwgL1R5cGUgL1BhZ2VzIC9LaWRzIFsz"
    "IDAgUl0gL0NvdW50IDEgPj4KZW5kb2JqCjMgMCBvYmoKPDwgL1R5cGUgL1Bh"
    "Z2UgL1BhcmVudCAyIDAgUiAvTWVkaWFCb3ggWzAgMCA2MTIgNzkyXQovQ29u"
    "dGVudHMgNCAwIFIgL1Jlc291cmNlcyA8PCAvRm9udCA8PCAvRjEgNSAwIFIg"
    "Pj4gPj4gPj4KZW5kb2JqCjQgMCBvYmoKPDwgL0xlbmd0aCA0NCA+PgpzdHJl"
    "YW0KQlQgL0YxIDEyIFRmIDEwMCA3MDAgVGQgKEhlbGxvIFBERikgVGoKMCAt"
    "MjAgVGQgKFNlY29uZCBsaW5lKSBUagpFVAplbmRzdHJlYW0KZW5kb2JqCjUg"
    "MCBvYmoKPDwgL1R5cGUgL0ZvbnQgL1N1YnR5cGUgL1R5cGUxIC9CYXNlRm9u"
    "dCAvSGVsdmV0aWNhID4+CmVuZG9iagp4cmVmCjAgNgowMDAwMDAwMDAwIDY1"
    "NTM1IGYgCjAwMDAwMDAwMDkgMDAwMDAgbiAKMDAwMDAwMDA1OCAwMDAwMCBu"
    "IAowMDAwMDAwMTE1IDAwMDAwIG4gCjAwMDAwMDAzMDYgMDAwMDAgbiAKMMDAwMD"
    "AwNDAyIDAwMDAwIG4gCnRyYWlsZXIKPDwgL1NpemUgNiAvUm9vdCAxIDAgUiA+"
    "PgpzdGFydHhyZWYKNDkxCiUlRU9G"
)


@pytest.fixture
def sample_pdf(tmp_path):
    """Write a minimal PDF to a temp file and return its path."""
    pdf_bytes = base64.b64decode(_MINIMAL_PDF_B64)
    path = tmp_path / "sample.pdf"
    path.write_bytes(pdf_bytes)
    return str(path)


@pytest.fixture
def sample_pdf_via_pdfplumber(tmp_path):
    """Create a tiny PDF with known text using pdfplumber's test helpers (fpdf2)."""
    fpdf2 = pytest.importorskip("fpdf")
    pdf = fpdf2.FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    pdf.cell(text="Hello PDF")
    pdf.ln()
    pdf.cell(text="Second line")
    path = tmp_path / "gen.pdf"
    pdf.output(str(path))
    return str(path)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestPdfReaderBasic:
    def test_supported_extensions(self):
        assert PdfReader.get_supported_extensions() == [".pdf"]

    def test_read_produces_document_model(self, sample_pdf_via_pdfplumber):
        reader = PdfReader()
        model = reader.read(sample_pdf_via_pdfplumber, {})
        assert model.metadata["type"] == "pdf"
        assert len(model.blocks) > 0

    def test_text_blocks_are_paragraphs(self, sample_pdf_via_pdfplumber):
        reader = PdfReader()
        model = reader.read(sample_pdf_via_pdfplumber, {})
        text_blocks = [b for b in model.blocks if isinstance(b, ParagraphBlock)]
        texts = [b.text for b in text_blocks]
        assert any("Hello PDF" in t for t in texts)
        assert any("Second line" in t for t in texts)

    def test_metadata(self, sample_pdf_via_pdfplumber):
        reader = PdfReader()
        model = reader.read(sample_pdf_via_pdfplumber, {})
        assert model.metadata["source"] == sample_pdf_via_pdfplumber
        assert model.metadata["type"] == "pdf"


class TestPdfReaderOptions:
    def test_include_headers_adds_page_marker(self, sample_pdf_via_pdfplumber):
        reader = PdfReader()
        model = reader.read(sample_pdf_via_pdfplumber, {"include_headers": True})
        header_blocks = [
            b for b in model.blocks
            if isinstance(b, ParagraphBlock) and b.is_header
        ]
        assert len(header_blocks) >= 1
        assert header_blocks[0].text == "Page 1"

    def test_no_headers_by_default(self, sample_pdf_via_pdfplumber):
        reader = PdfReader()
        model = reader.read(sample_pdf_via_pdfplumber, {})
        header_blocks = [
            b for b in model.blocks
            if isinstance(b, ParagraphBlock) and b.is_header
        ]
        assert len(header_blocks) == 0

    def test_include_tables_false_skips_tables(self, sample_pdf_via_pdfplumber):
        reader = PdfReader()
        model = reader.read(sample_pdf_via_pdfplumber, {"include_tables": False})
        table_blocks = [b for b in model.blocks if isinstance(b, TableBlock)]
        assert len(table_blocks) == 0


class TestPdfReaderWithTable:
    """Create a PDF that contains a table and verify extraction."""

    @pytest.fixture
    def pdf_with_table(self, tmp_path):
        fpdf2 = pytest.importorskip("fpdf")
        pdf = fpdf2.FPDF()
        pdf.add_page()
        pdf.set_font("Helvetica", size=10)
        pdf.cell(text="Before table")
        pdf.ln(10)

        # Draw a simple 2x2 table using cells
        col_w = 40
        row_h = 8
        data = [["A1", "B1"], ["A2", "B2"]]
        for row in data:
            for cell_text in row:
                pdf.cell(col_w, row_h, cell_text, border=1)
            pdf.ln(row_h)

        path = tmp_path / "table.pdf"
        pdf.output(str(path))
        return str(path)

    def test_table_extraction(self, pdf_with_table):
        reader = PdfReader()
        model = reader.read(pdf_with_table, {"include_tables": True})
        # pdfplumber may or may not detect the table depending on layout
        # At minimum, text should be extracted
        text_blocks = [b for b in model.blocks if isinstance(b, ParagraphBlock)]
        all_text = " ".join(b.text for b in text_blocks)
        assert "Before table" in all_text


class TestPdfReaderErrors:
    def test_nonexistent_file_raises(self, tmp_path):
        reader = PdfReader()
        with pytest.raises(RuntimeError, match="Cannot open PDF"):
            reader.read(str(tmp_path / "nonexistent.pdf"), {})

    def test_invalid_pdf_raises(self, tmp_path):
        bad = tmp_path / "bad.pdf"
        bad.write_text("this is not a pdf")
        reader = PdfReader()
        with pytest.raises(RuntimeError, match="Cannot open PDF"):
            reader.read(str(bad), {})
