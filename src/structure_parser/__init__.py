"""Structure-aware parser for structured Markdown and rendered HTML."""

from structure_parser.api import parse_file, parse_files
from structure_parser.contracts.config import ParserConfig
from structure_parser.contracts.parse_run_result import ParseRunResult
from structure_parser.contracts.parsed_document import ParsedDocument

__version__ = "0.1.0"
__all__ = ["parse_file", "parse_files", "ParsedDocument", "ParseRunResult", "ParserConfig"]
