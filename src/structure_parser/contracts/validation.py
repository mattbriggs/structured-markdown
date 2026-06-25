"""Model validation result contract."""

from pydantic import BaseModel

from structure_parser.contracts.diagnostics import Diagnostic


class ModelValidationResult(BaseModel):
    schema_version: str = "1"
    schema_id: str | None = None
    valid: bool
    diagnostics: list[Diagnostic] = []
    source_path: str | None = None
