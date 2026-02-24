import subprocess
import sys
from pathlib import Path

def test_cli_convert_basic(sample_docx, tmp_path):
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    
    # Run CLI via subprocess to ensure full E2E coverage
    cmd = [
        sys.executable, "-m", "ufc.cli",
        "convert", sample_docx,
        "--in-type", "docx",
        "--out-type", "txt",
        "--output-dir", str(out_dir)
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert result.returncode == 0
    assert "Successfully converted" in result.stdout
    
    # Check output file exists
    expected_out = out_dir / (Path(sample_docx).stem + ".txt")
    assert expected_out.exists()
    
    content = expected_out.read_text(encoding="utf-8")
    assert "Hello World" in content
    assert "這是中文測試" in content
    assert "[TABLE]" in content
    assert "A1" in content

def test_cli_convert_chunking(sample_docx, tmp_path):
    out_dir = tmp_path / "out_chunk"
    out_dir.mkdir()
    
    cmd = [
        sys.executable, "-m", "ufc.cli",
        "convert", sample_docx,
        "--in-type", "docx",
        "--out-type", "txt",
        "--output-dir", str(out_dir),
        "--enable-chunk",
        "--chunk-size", "10"  # Small chunk size so it definitely splits
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert result.returncode == 0
    
    # Chunking writes to out_dir / ALL_CHUNKS / {stem}_part001.txt, etc.
    all_chunks_dir = out_dir / "ALL_CHUNKS"
    assert all_chunks_dir.exists()
    
    parts = list(all_chunks_dir.glob("*_part*.txt"))
    assert len(parts) > 1
