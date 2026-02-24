import pytest
from ufc.plugins.readers.docx_reader import DocxReader
from ufc.core.models import ParagraphBlock, TableBlock

def test_docx_reader_basic(sample_docx):
    reader = DocxReader()
    model = reader.read(sample_docx, {})
    
    # Basic paras + table (header/footer off by default)
    assert len(model.blocks) == 3
    assert isinstance(model.blocks[0], ParagraphBlock)
    assert model.blocks[0].text == "Hello World"
    
    assert isinstance(model.blocks[1], ParagraphBlock)
    assert model.blocks[1].text == "這是中文測試"
    
    assert isinstance(model.blocks[2], TableBlock)
    assert model.blocks[2].rows == [["A1", "B1"], ["A2", "B2"]]

def test_docx_reader_with_headers_footers(sample_docx):
    reader = DocxReader()
    model = reader.read(sample_docx, {"include_headers": True, "include_footers": True})
    
    # Expected:
    # Header: "Section 1", "Header text"
    # Footer: "Section 1", "Footer text"
    # Body: 2 paras, 1 table
    assert any(b.text == "Header text" and getattr(b, "is_header", False) for b in model.blocks if isinstance(b, ParagraphBlock))
    assert any(b.text == "Footer text" and getattr(b, "is_footer", False) for b in model.blocks if isinstance(b, ParagraphBlock))
