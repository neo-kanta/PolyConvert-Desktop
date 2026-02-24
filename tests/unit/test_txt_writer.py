import pytest
from pathlib import Path
from ufc.plugins.writers.txt_writer import TxtWriter
from ufc.core.models import DocumentModel, ParagraphBlock, TableBlock
import sys

def test_txt_writer_basic(tmp_path):
    model = DocumentModel(blocks=[
        ParagraphBlock(text="Hello"),
        TableBlock(rows=[["1", "2"], ["3", "4"]])
    ])
    
    writer = TxtWriter()
    out_file = tmp_path / "out.txt"
    writer.write(model, str(out_file), {"include_tables": True, "table_format": "tsv"})
    
    content = out_file.read_text(encoding="utf-8")
    assert "Hello" in content
    assert "[TABLE]" in content
    assert "1\t2" in content
    assert "3\t4" in content

def test_txt_writer_chunking(tmp_path):
    # A single paragraph with 15 chars
    model = DocumentModel(blocks=[ParagraphBlock(text="Hello World 123")])
    writer = TxtWriter()
    
    # Chunk size 5, overlap 1
    # Note: text output adds a newline. "Hello World 123\n" is 16 chars.
    out_file = tmp_path / "out.txt"
    writer.write(model, str(out_file), {"enable_chunk": True, "chunk_size": 5, "overlap": 1})
    
    # Because enable_chunk=True, they should go to part files
    # Output is written to out_file.parent / {stem}_part001.txt, etc.
    chunks = sorted(list(tmp_path.glob("out_part*.txt")))
    assert len(chunks) > 1
    
    full_reconstructed = ""
    # Just check parts exist and have content
    for c in chunks:
        assert c.stat().st_size > 0
