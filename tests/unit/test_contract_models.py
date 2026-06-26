"""Tests for Pydantic contract models."""
import pytest
from pydantic import ValidationError

from structure_parser.contracts.config import ParserConfig
from structure_parser.contracts.diagnostics import Diagnostic, DiagnosticFactory
from structure_parser.contracts.parse_run_result import ParseRunResult, ParseStats
from structure_parser.contracts.parsed_document import ParsedDocument
from structure_parser.contracts.references import Reference
from structure_parser.contracts.structured_markdown import (
    Attribute,
    Component,
    StructuredContent,
    Unit,
)
from structure_parser.contracts.transform_readiness import TargetReadiness, TransformReadiness
from structure_parser.domain.enums import (
    ArticleType,
    AttributeType,
    ComponentType,
    DiagnosticCategory,
    ReadinessStatus,
    ResolutionState,
    Severity,
    SourceFormat,
    TriageStatus,
    UnitType,
)


class TestParserConfig:
    def test_defaults(self):
        cfg = ParserConfig()
        assert cfg.schema_version == "1"
        assert cfg.enable_structured_markdown is True
        assert cfg.validation_mode == "advisory"
        assert cfg.resolve_local_references is False

    def test_immutable(self):
        cfg = ParserConfig()
        with pytest.raises(ValidationError):
            cfg.schema_version = "2"  # type: ignore


class TestDiagnostic:
    def test_required_fields(self):
        d = Diagnostic(
            code="SP-001",
            severity=Severity.error,
            category=DiagnosticCategory.parse_error,
            message="File not found",
        )
        assert d.schema_version == "1"
        assert d.code == "SP-001"

    def test_has_remediation_by_default(self):
        d = Diagnostic(
            code="SP-001",
            severity=Severity.error,
            category=DiagnosticCategory.parse_error,
            message="msg",
        )
        assert d.remediation == ""

    def test_factory_source_not_found(self):
        d = DiagnosticFactory.source_file_not_found("/tmp/x.md")
        assert d.code == "SP-001"
        assert d.severity == Severity.error
        assert "/tmp/x.md" in d.message

    def test_factory_missing_title(self):
        d = DiagnosticFactory.missing_title(source_path="x.md")
        assert d.code == "SP-020"
        assert d.severity == Severity.warning

    def test_factory_unresolved_reference(self):
        d = DiagnosticFactory.unresolved_reference("./foo.md", source_path="x.md")
        assert d.code == "SP-050"
        assert "./foo.md" in d.message


class TestReference:
    def test_defaults(self):
        ref = Reference(ref_type="link", href="./foo.md")
        assert ref.state == ResolutionState.not_attempted
        assert ref.schema_version == "1"

    def test_resolved_state(self):
        ref = Reference(ref_type="image", href="./img.png", state=ResolutionState.resolved)
        assert ref.state == ResolutionState.resolved


class TestStructuredContent:
    def test_defaults(self):
        sc = StructuredContent()
        assert sc.article_type == ArticleType.unknown
        assert sc.triage_status == TriageStatus.unknown
        assert sc.content == []

    def test_with_units(self):
        unit = Unit(unit_type=UnitType.introduction, title="Intro")
        sc = StructuredContent(content=[unit])
        assert len(sc.content) == 1
        assert sc.content[0].unit_type == UnitType.introduction

    def test_component_types(self):
        comp = Component(
            component_type=ComponentType.compParagraph,
            text="Hello",
        )
        assert comp.component_type == ComponentType.compParagraph

    def test_attribute_types(self):
        attr = Attribute(att_type=AttributeType.attText, text="Hello")
        assert attr.att_type == AttributeType.attText


class TestParsedDocument:
    def test_has_errors_empty(self):
        doc = ParsedDocument(source_path="x.md", source_format=SourceFormat.markdown)
        assert not doc.has_errors
        assert doc.error_count == 0
        assert doc.warning_count == 0

    def test_has_errors_with_error(self):
        d = DiagnosticFactory.source_file_not_found("x.md")
        doc = ParsedDocument(
            source_path="x.md",
            source_format=SourceFormat.markdown,
            diagnostics=[d],
        )
        assert doc.has_errors
        assert doc.error_count == 1

    def test_schema_version(self):
        doc = ParsedDocument(source_path="x.md", source_format=SourceFormat.markdown)
        assert doc.schema_version == "1"


class TestParseRunResult:
    def test_empty_success(self):
        result = ParseRunResult()
        assert result.success
        assert result.stats.file_count == 0

    def test_success_with_clean_docs(self):
        doc = ParsedDocument(source_path="x.md", source_format=SourceFormat.markdown)
        result = ParseRunResult(documents=[doc], stats=ParseStats(file_count=1))
        assert result.success


class TestTransformReadiness:
    def test_defaults(self):
        tr = TransformReadiness()
        assert tr.targets == []

    def test_with_targets(self):
        t = TargetReadiness(
            target="dita",
            status=ReadinessStatus.ready,
            prerequisites_met=["Has title"],
        )
        tr = TransformReadiness(targets=[t])
        assert tr.targets[0].target == "dita"
        assert tr.targets[0].status == ReadinessStatus.ready
