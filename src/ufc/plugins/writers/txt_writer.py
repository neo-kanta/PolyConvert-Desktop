import sys
from pathlib import Path
from typing import Dict, Any, List

from ufc.core.models import DocumentModel, ParagraphBlock, TableBlock
from ufc.plugins.registry import OutputWriter, PluginRegistry
from ufc.i18n.i18n import i18n

def chunk_text(text: str, chunk_size: int, overlap: int) -> List[str]:
    if chunk_size <= 0:
        return [text]
    overlap = max(0, min(overlap, chunk_size - 1)) if chunk_size > 1 else 0

    chunks: List[str] = []
    n = len(text)
    start = 0
    while start < n:
        end = min(n, start + chunk_size)
        chunks.append(text[start:end])
        if end >= n:
            break
        start = end - overlap
    return chunks

class TxtWriter(OutputWriter):
    @classmethod
    def get_supported_extensions(cls) -> list[str]:
        return [".txt"]

    def write(self, model: DocumentModel, output_path: str, options: Dict[str, Any]) -> None:
        include_tables = options.get("include_tables", True)
        table_format = options.get("table_format", "tsv")
        normalize_tables = options.get("normalize_tables", True)
        utf8_bom = options.get("utf8_bom", False)
        
        enable_chunk = options.get("enable_chunk", False)
        chunk_size = options.get("chunk_size", 12000)
        overlap = options.get("overlap", 300)

        out_lines = []

        for block in model.blocks:
            if isinstance(block, ParagraphBlock):
                if block.is_header:
                    out_lines.append(f"{i18n.t('header_marker')} {block.text}")
                elif block.is_footer:
                    out_lines.append(f"{i18n.t('footer_marker')} {block.text}")
                else:
                    out_lines.append(block.text)

            elif isinstance(block, TableBlock) and include_tables:
                out_lines.append(i18n.t("table_marker"))
                out_lines.extend(self._format_table(block, table_format, normalize_tables))
                out_lines.append("")

        text = "\n".join(out_lines).rstrip() + "\n"
        encoding = "utf-8-sig" if utf8_bom else "utf-8"

        out_p = Path(output_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)

        if enable_chunk:
            chunks = chunk_text(text, chunk_size, overlap)
            stem = out_p.stem
            
            # If chunking is enabled, we output chunks into the target directory with a prefix
            # The 'output_path' given to write() is usually the *base* file path we would have used.
            # E.g. output_path = output_dir / foo.txt
            # For chunks, we write to output_dir / foo_part001.txt, etc.
            # But in the UI logic, we also need to support the "ALL_CHUNKS" folder logic.
            # We can handle that folder logic in the caller, by passing output_path as `ALL_CHUNKS/foo.txt`
            folder = out_p.parent
            
            for idx, c in enumerate(chunks, start=1):
                chunk_file = folder / f"{stem}_part{idx:03d}.txt"
                chunk_file.write_text(c, encoding=encoding, newline="\n")
        else:
            out_p.write_text(text, encoding=encoding, newline="\n")

    def _format_table(self, block: TableBlock, fmt: str, normalize: bool) -> List[str]:
        target_cols = 0
        if normalize:
            for row in block.rows:
                target_cols = max(target_cols, len(row))

        lines = []
        for row in block.rows:
            cells = list(row)
            if normalize and target_cols > 0 and len(cells) < target_cols:
                cells += [""] * (target_cols - len(cells))
            
            safe_cells = [c.replace("\n", "\\n") for c in cells]
            if fmt == "tsv":
                lines.append("\t".join(safe_cells).rstrip())
            else:
                lines.append("| " + " | ".join(safe_cells) + " |")

        return lines

PluginRegistry.register_writer(TxtWriter)
