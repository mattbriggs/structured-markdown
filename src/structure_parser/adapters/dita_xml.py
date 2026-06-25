"""DITA/XML adapter — deferred per A-004. Placeholder for future implementation."""
from pathlib import Path
from structure_parser.contracts.config import ParserConfig
from structure_parser.contracts.raw import RawParseModel
from structure_parser.domain.enums import SourceFormat
from structure_parser.domain.errors import UnsupportedFormatError


class DitaXmlAdapter:
    """Deferred DITA/XML adapter. Not implemented in MVP."""

    source_format = "dita_xml"
    supported_extensions = (".dita", ".ditamap", ".xml")

    def parse(self, path: Path, config: ParserConfig) -> RawParseModel:
        """Not implemented — DITA parsing is deferred per assumption A-004."""
        raise UnsupportedFormatError(
            "DITA/XML parsing is deferred. Only Markdown and HTML are supported in MVP.",
            path=str(path),
        )
