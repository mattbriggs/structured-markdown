"""Exception hierarchy for the structure parser."""


class StructureParserError(Exception):
    """Base exception for all structure parser errors."""

    def __init__(self, message: str, path: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.path = path

    def __str__(self) -> str:
        if self.path:
            return f"{self.message} (path: {self.path})"
        return self.message


class ParserConfigurationError(StructureParserError):
    """Raised for configuration errors. Exit code 2."""


class UnsupportedFormatError(ParserConfigurationError):
    """Raised when an unsupported source format is specified or detected."""


class UnsupportedSchemaVersionError(ParserConfigurationError):
    """Raised when the schema version is not supported."""


class SourceFileNotFoundError(StructureParserError):
    """Raised when the source file cannot be found. Exit code 1."""


class AdapterError(StructureParserError):
    """Raised when a parse adapter fails to process source content."""


class EnrichmentError(StructureParserError):
    """Raised when an enrichment step fails."""


class SchemaRepositoryError(StructureParserError):
    """Raised when the schema repository cannot be loaded or accessed."""


class InternalParserError(StructureParserError):
    """Raised for unexpected internal failures. Exit code 3."""
