"""Format adapter protocol and shared types."""
from __future__ import annotations
from pathlib import Path
from typing import Protocol
from structure_parser.contracts.raw import RawParseModel
from structure_parser.contracts.config import ParserConfig


class IFormatAdapter(Protocol):
    """Protocol for source-format adapters. Adapters parse syntax only; no authoring validation."""

    source_format: str  # e.g. "markdown", "html5"
    supported_extensions: tuple[str, ...]  # e.g. (".md", ".markdown")

    def parse(self, path: Path, config: ParserConfig) -> RawParseModel:
        """Parse a source file into a RawParseModel.

        :param path: Source file path. Treated as untrusted; loaded only through the adapter.
        :param config: Parser configuration for this run.
        :returns: A RawParseModel containing raw syntax nodes. May include parse_errors.
        :raises AdapterError: On unrecoverable parse failure.
        """
        ...
