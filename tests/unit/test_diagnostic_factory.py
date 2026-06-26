"""Tests for DiagnosticFactory — all MVP diagnostic codes."""
from structure_parser.contracts.diagnostics import Diagnostic, DiagnosticFactory
from structure_parser.domain.diagnostic_codes import DIAGNOSTIC_CODES
from structure_parser.domain.enums import DiagnosticCategory, Severity


class TestDiagnosticCodes:
    def test_all_codes_present(self):
        required = {"SP-001", "SP-002", "SP-003", "SP-010", "SP-011",
                    "SP-020", "SP-021", "SP-030", "SP-031", "SP-032",
                    "SP-040", "SP-041", "SP-050", "SP-060", "SP-099"}
        assert required.issubset(set(DIAGNOSTIC_CODES.keys()))

    def test_code_definitions_have_required_fields(self):
        for code, defn in DIAGNOSTIC_CODES.items():
            assert defn.code == code
            assert defn.severity in Severity
            assert defn.category in DiagnosticCategory
            assert defn.message_template
            assert defn.remediation


class TestDiagnosticFactory:
    def test_source_file_not_found(self):
        d = DiagnosticFactory.source_file_not_found("/path/to/file.md")
        assert d.code == "SP-001"
        assert d.severity == Severity.error
        assert "/path/to/file.md" in d.message

    def test_unsupported_format(self):
        d = DiagnosticFactory.unsupported_format(".docx")
        assert d.code == "SP-002"
        assert d.severity == Severity.error

    def test_parse_failed(self):
        d = DiagnosticFactory.parse_failed("syntax error")
        assert d.code == "SP-003"
        assert "syntax error" in d.message

    def test_malformed_front_matter(self):
        d = DiagnosticFactory.malformed_front_matter(
            "invalid YAML", source_path="x.md", start_line=1
        )
        assert d.code == "SP-010"
        assert d.severity == Severity.warning
        assert d.start_line == 1
        assert d.source_path == "x.md"

    def test_front_matter_absent(self):
        d = DiagnosticFactory.front_matter_absent(source_path="x.md")
        assert d.code == "SP-011"
        assert d.severity == Severity.info

    def test_missing_title(self):
        d = DiagnosticFactory.missing_title(source_path="x.md")
        assert d.code == "SP-020"
        assert d.severity == Severity.warning

    def test_heading_level_skipped(self):
        d = DiagnosticFactory.heading_level_skipped(2, 4, source_path="x.md", start_line=10)
        assert d.code == "SP-021"
        assert d.start_line == 10

    def test_schema_validation_failed(self):
        d = DiagnosticFactory.schema_validation_failed("missing field", source_path="x.md")
        assert d.code == "SP-030"

    def test_schema_file_not_found(self):
        d = DiagnosticFactory.schema_file_not_found("missing.schema.json")
        assert d.code == "SP-031"
        assert d.severity == Severity.error

    def test_unknown_classification(self):
        d = DiagnosticFactory.unknown_classification("content", source_path="x.md")
        assert d.code == "SP-040"
        assert d.severity == Severity.info

    def test_unknown_article_type(self):
        d = DiagnosticFactory.unknown_article_type(source_path="x.md")
        assert d.code == "SP-041"
        assert d.severity == Severity.warning

    def test_unresolved_reference(self):
        d = DiagnosticFactory.unresolved_reference("./missing.md", source_path="x.md", start_line=5)
        assert d.code == "SP-050"
        assert "./missing.md" in d.message

    def test_internal_error(self):
        d = DiagnosticFactory.internal_error("unexpected failure")
        assert d.code == "SP-099"
        assert d.severity == Severity.error

    def test_all_factories_return_diagnostic(self):
        factories = [
            lambda: DiagnosticFactory.source_file_not_found("x"),
            lambda: DiagnosticFactory.unsupported_format(".xyz"),
            lambda: DiagnosticFactory.parse_failed("err"),
            lambda: DiagnosticFactory.malformed_front_matter("err"),
            lambda: DiagnosticFactory.front_matter_absent(),
            lambda: DiagnosticFactory.missing_title(),
            lambda: DiagnosticFactory.heading_level_skipped(1, 3),
            lambda: DiagnosticFactory.schema_validation_failed("err"),
            lambda: DiagnosticFactory.schema_file_not_found("x"),
            lambda: DiagnosticFactory.unsupported_schema_version("0"),
            lambda: DiagnosticFactory.unknown_classification("x"),
            lambda: DiagnosticFactory.unknown_article_type(),
            lambda: DiagnosticFactory.unresolved_reference("x"),
            lambda: DiagnosticFactory.transform_readiness("dita", "blocked"),
            lambda: DiagnosticFactory.internal_error("err"),
        ]
        for fn in factories:
            d = fn()
            assert isinstance(d, Diagnostic)
            assert d.code.startswith("SP-")
