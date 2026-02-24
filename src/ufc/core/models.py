from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class Block:
    """Base block in a document."""
    pass

@dataclass
class ParagraphBlock(Block):
    text: str
    is_header: bool = False
    is_footer: bool = False

@dataclass
class TableBlock(Block):
    # Rows of cells, where each cell is a string
    rows: List[List[str]] = field(default_factory=list)
    is_header: bool = False
    is_footer: bool = False

@dataclass
class DocumentModel:
    """Represents an intermediate parsed document."""
    blocks: List[Block] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
