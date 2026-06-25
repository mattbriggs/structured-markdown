"""Adapter registry — selects the correct format adapter for a source file."""
from __future__ import annotations
from pathlib import Path
from structure_parser.adapters.markdown import MarkdownAdapter
from structure_parser.adapters.html import HtmlAdapter
from structure_parser.adapters.dita_xml import DitaXmlAdapter
from structure_parser.adapters.base import IFormatAdapter
from structure_parser.contracts.config import ParserConfig
from structure_parser.domain.enums import SourceFormat
from structure_parser.domain.errors import UnsupportedFormatError

_ADAPTERS: dict[str, IFormatAdapter] = {}


def _build_registry() -> dict[str, IFormatAdapter]:
    registry: dict[str, IFormatAdapter] = {}
    for adapter in (MarkdownAdapter(), HtmlAdapter(), DitaXmlAdapter()):
        for ext in adapter.supported_extensions:
            registry[ext] = adapter  # type: ignore[assignment]
    return registry


def get_adapter(path: Path, config: ParserConfig) -> IFormatAdapter:
    """Select the appropriate adapter for a source file.

    :param path: Source file path.
    :param config: Parser config. source_format override takes precedence.
    :raises UnsupportedFormatError: If no adapter supports the file extension.
    """
    global _ADAPTERS
    if not _ADAPTERS:
        _ADAPTERS = _build_registry()

    # Config override
    if config.source_format:
        fmt = config.source_format
        if fmt == SourceFormat.markdown:
            return MarkdownAdapter()  # type: ignore[return-value]
        elif fmt == SourceFormat.html5:
            return HtmlAdapter()  # type: ignore[return-value]
        else:
            raise UnsupportedFormatError(
                f"Source format {fmt.value!r} is not supported in MVP.",
                path=str(path),
            )

    ext = path.suffix.lower()
    adapter = _ADAPTERS.get(ext)
    if adapter is None:
        raise UnsupportedFormatError(
            f"No adapter for extension {ext!r}. Supported: .md, .markdown, .html, .htm",
            path=str(path),
        )
    return adapter
