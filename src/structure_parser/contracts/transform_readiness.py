"""Transform readiness contracts for evaluating output target prerequisites."""

from pydantic import BaseModel

from structure_parser.contracts.diagnostics import Diagnostic
from structure_parser.domain.enums import ReadinessStatus


class TargetReadiness(BaseModel):
    target: str
    status: ReadinessStatus
    prerequisites_met: list[str] = []
    prerequisites_missing: list[str] = []
    diagnostics: list[Diagnostic] = []


class TransformReadiness(BaseModel):
    schema_version: str = "1"
    source_path: str | None = None
    targets: list[TargetReadiness] = []
