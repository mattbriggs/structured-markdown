"""Diagnostic code definitions for the structure parser."""

from dataclasses import dataclass

from structure_parser.domain.enums import DiagnosticCategory, Severity


@dataclass(frozen=True)
class DiagnosticCodeDefinition:
    code: str
    severity: Severity
    category: DiagnosticCategory
    message_template: str
    remediation: str


DIAGNOSTIC_CODES: dict[str, DiagnosticCodeDefinition] = {
    "SP-001": DiagnosticCodeDefinition(
        code="SP-001",
        severity=Severity.error,
        category=DiagnosticCategory.parse_error,
        message_template="Source file not found: {path}",
        remediation="Verify the file path exists and is readable.",
    ),
    "SP-002": DiagnosticCodeDefinition(
        code="SP-002",
        severity=Severity.error,
        category=DiagnosticCategory.parse_error,
        message_template="Unsupported source format: {format}",
        remediation="Use .md or .html files.",
    ),
    "SP-003": DiagnosticCodeDefinition(
        code="SP-003",
        severity=Severity.error,
        category=DiagnosticCategory.parse_error,
        message_template="Parse failed: {detail}",
        remediation="Check that the file is valid Markdown or HTML.",
    ),
    "SP-010": DiagnosticCodeDefinition(
        code="SP-010",
        severity=Severity.warning,
        category=DiagnosticCategory.metadata_error,
        message_template="Malformed front matter: {detail}",
        remediation="Ensure YAML front matter is valid and closed with ---.",
    ),
    "SP-011": DiagnosticCodeDefinition(
        code="SP-011",
        severity=Severity.info,
        category=DiagnosticCategory.metadata_error,
        message_template="Front matter absent",
        remediation="Add a YAML front matter block with at least a title field.",
    ),
    "SP-020": DiagnosticCodeDefinition(
        code="SP-020",
        severity=Severity.warning,
        category=DiagnosticCategory.structural_warning,
        message_template="Missing document title (H1)",
        remediation="Add an H1 heading as the first content element.",
    ),
    "SP-021": DiagnosticCodeDefinition(
        code="SP-021",
        severity=Severity.warning,
        category=DiagnosticCategory.structural_warning,
        message_template="Heading level skipped: {from_level} to {to_level}",
        remediation="Do not skip heading levels.",
    ),
    "SP-030": DiagnosticCodeDefinition(
        code="SP-030",
        severity=Severity.warning,
        category=DiagnosticCategory.authoring_violation,
        message_template="Schema validation failed: {detail}",
        remediation="Review the authoring model and fix reported violations.",
    ),
    "SP-031": DiagnosticCodeDefinition(
        code="SP-031",
        severity=Severity.error,
        category=DiagnosticCategory.schema_error,
        message_template="Schema file not found: {path}",
        remediation="Ensure the schema file exists in the model directory.",
    ),
    "SP-032": DiagnosticCodeDefinition(
        code="SP-032",
        severity=Severity.error,
        category=DiagnosticCategory.schema_error,
        message_template="Unsupported schema version: {version}",
        remediation="Use a supported schema version.",
    ),
    "SP-040": DiagnosticCodeDefinition(
        code="SP-040",
        severity=Severity.info,
        category=DiagnosticCategory.unknown_classification,
        message_template="Content classified as unknown: {detail}",
        remediation="Review content structure; it may not match any known pattern.",
    ),
    "SP-041": DiagnosticCodeDefinition(
        code="SP-041",
        severity=Severity.warning,
        category=DiagnosticCategory.unknown_classification,
        message_template="Article type could not be determined",
        remediation="Add articleType metadata or conform to a known article pattern.",
    ),
    "SP-050": DiagnosticCodeDefinition(
        code="SP-050",
        severity=Severity.warning,
        category=DiagnosticCategory.reference_error,
        message_template="Unresolved reference: {href}",
        remediation="Fix or remove the broken link or image reference.",
    ),
    "SP-060": DiagnosticCodeDefinition(
        code="SP-060",
        severity=Severity.info,
        category=DiagnosticCategory.transform_readiness,
        message_template="Transform readiness: {target} is {status}",
        remediation="Review readiness report for blocked prerequisites.",
    ),
    "SP-099": DiagnosticCodeDefinition(
        code="SP-099",
        severity=Severity.error,
        category=DiagnosticCategory.internal_error,
        message_template="Internal parser error: {detail}",
        remediation="Report this issue with the input file.",
    ),
}
