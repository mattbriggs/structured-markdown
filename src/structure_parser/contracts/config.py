"""Public execution configuration for the structure parser."""

from pathlib import Path

from pydantic import BaseModel, Field

from structure_parser.domain.enums import SourceFormat


class ParserConfig(BaseModel):
    """Public execution configuration for the structure parser."""

    schema_version: str = Field(default="1", description="Parser contract schema version.")
    source_format: SourceFormat | None = Field(
        default=None, description="Override format detection."
    )
    enable_structured_markdown: bool = Field(default=True)
    validation_mode: str = Field(default="advisory", description="advisory or strict")
    resolve_local_references: bool = Field(default=False)
    model_schema_dir: Path | None = Field(
        default=None, description="Path to model JSON schemas. Defaults to bundled model/."
    )
    emit_debug_logs: bool = Field(default=False)
    max_diagnostic_count: int = Field(default=500)

    model_config = {"frozen": True}
