"""Source file repository — handles file-system intake and validation."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

from structure_parser.domain.errors import SourceFileNotFoundError


@dataclass(frozen=True)
class SourceFile:
    """Represents a located, readable source file."""
    path: Path
    content: str
    content_hash: str
    size_bytes: int


def load_source_file(path: str | Path) -> SourceFile:
    """Load a source file and return a SourceFile with content and hash.

    :raises SourceFileNotFoundError: If the path does not exist or is not a file.
    """
    p = Path(path)
    if not p.exists():
        raise SourceFileNotFoundError(f"Source file not found: {p}", path=str(p))
    if not p.is_file():
        raise SourceFileNotFoundError(f"Path is not a file: {p}", path=str(p))

    content = p.read_text(encoding="utf-8")
    content_hash = hashlib.sha256(content.encode()).hexdigest()

    return SourceFile(
        path=p,
        content=content,
        content_hash=content_hash,
        size_bytes=len(content.encode("utf-8")),
    )


def detect_format(path: Path) -> str:
    """Detect the source format from the file extension."""
    suffix = path.suffix.lower()
    if suffix in (".md", ".markdown"):
        return "markdown"
    if suffix in (".html", ".htm"):
        return "html5"
    if suffix in (".dita", ".ditamap", ".xml"):
        return "dita_xml"
    return "unknown"
