"""PDF reader plugin – extracts text and basic tables from text-based PDFs."""

import re
from typing import Any, Dict, List

import pdfplumber

from ufc.core.models import DocumentModel, ParagraphBlock, TableBlock
from ufc.plugins.registry import InputReader, PluginRegistry

_WS_RE = re.compile(r"[ \t]+")


def _clean_text(s: str) -> str:
    """Collapse whitespace and trim each line (mirrors docx_reader behaviour)."""
    s = s.replace("\r\n", "\n").replace("\r", "\n")
    lines = [_WS_RE.sub(" ", line).strip() for line in s.split("\n")]
    return "\n".join(lines).strip("\n")


class PdfReader(InputReader):
    """Read text-based PDFs into the intermediate DocumentModel."""

    @classmethod
    def get_supported_extensions(cls) -> list[str]:
        return [".pdf"]

    def read(self, file_path: str, options: Dict[str, Any]) -> DocumentModel:
        include_headers = options.get("include_headers", False)
        include_tables = options.get("include_tables", True)
        keep_empty = options.get("keep_empty_paragraphs", False)

        model = DocumentModel(metadata={"source": file_path, "type": "pdf"})

        try:
            pdf = pdfplumber.open(file_path)
        except Exception as exc:
            raise RuntimeError(
                f"Cannot open PDF '{file_path}'. "
                "If the file is encrypted or scanned, note that scanned PDFs "
                "require OCR which is not supported."
            ) from exc

        with pdf:
            if not pdf.pages:
                return model

            for page_num, page in enumerate(pdf.pages, start=1):
                # Optional page-number header block
                if include_headers:
                    model.blocks.append(
                        ParagraphBlock(text=f"Page {page_num}", is_header=True)
                    )

                # --- Text extraction ---
                raw_text = page.extract_text()
                if raw_text:
                    cleaned = _clean_text(raw_text)
                    for line in cleaned.split("\n"):
                        if line or keep_empty:
                            model.blocks.append(ParagraphBlock(text=line))
                elif keep_empty:
                    # Page yielded no text at all – still emit one empty block
                    model.blocks.append(ParagraphBlock(text=""))

                # --- Table extraction ---
                if include_tables:
                    try:
                        tables: List[List[List[str | None]]] = page.extract_tables()
                    except Exception:
                        tables = []

                    for table in tables or []:
                        rows: List[List[str]] = []
                        for row in table:
                            rows.append([
                                _clean_text(cell) if cell else ""
                                for cell in row
                            ])
                        model.blocks.append(TableBlock(rows=rows))

        return model


PluginRegistry.register_reader(PdfReader)
