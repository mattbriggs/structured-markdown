"""Diagnostic models and factory for structure parser diagnostics."""

from pydantic import BaseModel, Field

from structure_parser.domain.diagnostic_codes import DIAGNOSTIC_CODES
from structure_parser.domain.enums import DiagnosticCategory, ProvenanceStatus, Severity


class Diagnostic(BaseModel):
    schema_version: str = "1"
    code: str
    severity: Severity
    category: DiagnosticCategory
    message: str
    detail: str = ""
    remediation: str = ""
    provenance_status: ProvenanceStatus = ProvenanceStatus.unavailable
    source_path: str | None = None
    start_line: int | None = Field(default=None, ge=1)
    end_line: int | None = Field(default=None, ge=1)


class DiagnosticFactory:
    """Factory class for creating Diagnostic instances from defined codes."""

    @classmethod
    def _build(
        cls,
        code: str,
        message: str,
        detail: str = "",
        source_path: str | None = None,
        start_line: int | None = None,
        end_line: int | None = None,
        provenance_status: ProvenanceStatus = ProvenanceStatus.unavailable,
    ) -> Diagnostic:
        definition = DIAGNOSTIC_CODES[code]
        return Diagnostic(
            code=code,
            severity=definition.severity,
            category=definition.category,
            message=message,
            detail=detail,
            remediation=definition.remediation,
            provenance_status=provenance_status,
            source_path=source_path,
            start_line=start_line,
            end_line=end_line,
        )

    @classmethod
    def source_file_not_found(cls, path: str) -> Diagnostic:
        defn = DIAGNOSTIC_CODES["SP-001"]
        return cls._build(
            code="SP-001",
            message=defn.message_template.format(path=path),
            detail=path,
            source_path=path,
        )

    @classmethod
    def unsupported_format(
        cls, format_name: str, source_path: str | None = None
    ) -> Diagnostic:
        defn = DIAGNOSTIC_CODES["SP-002"]
        return cls._build(
            code="SP-002",
            message=defn.message_template.format(format=format_name),
            detail=format_name,
            source_path=source_path,
        )

    @classmethod
    def parse_failed(
        cls, detail: str, source_path: str | None = None
    ) -> Diagnostic:
        defn = DIAGNOSTIC_CODES["SP-003"]
        return cls._build(
            code="SP-003",
            message=defn.message_template.format(detail=detail),
            detail=detail,
            source_path=source_path,
        )

    @classmethod
    def malformed_front_matter(
        cls,
        detail: str,
        source_path: str | None = None,
        start_line: int | None = None,
    ) -> Diagnostic:
        defn = DIAGNOSTIC_CODES["SP-010"]
        return cls._build(
            code="SP-010",
            message=defn.message_template.format(detail=detail),
            detail=detail,
            source_path=source_path,
            start_line=start_line,
        )

    @classmethod
    def front_matter_absent(cls, source_path: str | None = None) -> Diagnostic:
        defn = DIAGNOSTIC_CODES["SP-011"]
        return cls._build(
            code="SP-011",
            message=defn.message_template,
            source_path=source_path,
        )

    @classmethod
    def missing_title(cls, source_path: str | None = None) -> Diagnostic:
        defn = DIAGNOSTIC_CODES["SP-020"]
        return cls._build(
            code="SP-020",
            message=defn.message_template,
            source_path=source_path,
        )

    @classmethod
    def heading_level_skipped(
        cls,
        from_level: int,
        to_level: int,
        source_path: str | None = None,
        start_line: int | None = None,
    ) -> Diagnostic:
        defn = DIAGNOSTIC_CODES["SP-021"]
        return cls._build(
            code="SP-021",
            message=defn.message_template.format(from_level=from_level, to_level=to_level),
            detail=f"from H{from_level} to H{to_level}",
            source_path=source_path,
            start_line=start_line,
        )

    @classmethod
    def schema_validation_failed(
        cls, detail: str, source_path: str | None = None
    ) -> Diagnostic:
        defn = DIAGNOSTIC_CODES["SP-030"]
        return cls._build(
            code="SP-030",
            message=defn.message_template.format(detail=detail),
            detail=detail,
            source_path=source_path,
        )

    @classmethod
    def schema_file_not_found(cls, path: str) -> Diagnostic:
        defn = DIAGNOSTIC_CODES["SP-031"]
        return cls._build(
            code="SP-031",
            message=defn.message_template.format(path=path),
            detail=path,
            source_path=path,
        )

    @classmethod
    def unsupported_schema_version(cls, version: str) -> Diagnostic:
        defn = DIAGNOSTIC_CODES["SP-032"]
        return cls._build(
            code="SP-032",
            message=defn.message_template.format(version=version),
            detail=version,
        )

    @classmethod
    def unknown_classification(
        cls,
        detail: str,
        source_path: str | None = None,
        start_line: int | None = None,
    ) -> Diagnostic:
        defn = DIAGNOSTIC_CODES["SP-040"]
        return cls._build(
            code="SP-040",
            message=defn.message_template.format(detail=detail),
            detail=detail,
            source_path=source_path,
            start_line=start_line,
        )

    @classmethod
    def unknown_article_type(cls, source_path: str | None = None) -> Diagnostic:
        defn = DIAGNOSTIC_CODES["SP-041"]
        return cls._build(
            code="SP-041",
            message=defn.message_template,
            source_path=source_path,
        )

    @classmethod
    def unresolved_reference(
        cls,
        href: str,
        source_path: str | None = None,
        start_line: int | None = None,
    ) -> Diagnostic:
        defn = DIAGNOSTIC_CODES["SP-050"]
        return cls._build(
            code="SP-050",
            message=defn.message_template.format(href=href),
            detail=href,
            source_path=source_path,
            start_line=start_line,
        )

    @classmethod
    def transform_readiness(
        cls,
        target: str,
        status: str,
        source_path: str | None = None,
    ) -> Diagnostic:
        defn = DIAGNOSTIC_CODES["SP-060"]
        return cls._build(
            code="SP-060",
            message=defn.message_template.format(target=target, status=status),
            detail=f"{target}={status}",
            source_path=source_path,
        )

    @classmethod
    def internal_error(
        cls, detail: str, source_path: str | None = None
    ) -> Diagnostic:
        defn = DIAGNOSTIC_CODES["SP-099"]
        return cls._build(
            code="SP-099",
            message=defn.message_template.format(detail=detail),
            detail=detail,
            source_path=source_path,
        )
