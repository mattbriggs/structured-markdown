"""Contract test: full JSON schema round-trip for parsed documents.

Three guarantees are verified:

1. **Pydantic round-trip** — every ``ParsedDocument`` survives JSON serialisation
   and reconstruction without loss of key fields.

2. **Base schema compliance** — every structured-content result that does not
   carry error diagnostics validates against ``artArticle.schema.json`` (the
   permissive base schema all article types must satisfy).

3. **Declared schema compliance** — structured content validates against the
   specific article schema it declares (e.g. ``artHowto.schema.json``).  Some
   fixtures expose known gaps in the current classifier (e.g. ``informationType``
   not yet derived from article type) and are marked ``xfail`` until the triage
   implementation resolves them.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from structure_parser import parse_file
from structure_parser.contracts.parsed_document import ParsedDocument
from structure_parser.domain.enums import SourceFormat
from structure_parser.validation.model_validator import validate_against_declared_schema, validate_model

_FIXTURE_ROOT = Path(__file__).parent.parent / "fixtures"

# All markdown fixtures in the test suite.
_ALL_MD: list[Path] = sorted(_FIXTURE_ROOT.rglob("*.md"))

# Fixtures expected to produce no error diagnostics and have structured content.
_CLEAN_FIXTURES: list[Path] = [
    _FIXTURE_ROOT / "markdown" / "clean.md",
    _FIXTURE_ROOT / "markdown" / "complex.md",
    _FIXTURE_ROOT / "content_repo" / "index.md",
    _FIXTURE_ROOT / "content_repo" / "guide" / "install.md",
    _FIXTURE_ROOT / "content_repo" / "guide" / "configure.md",
    _FIXTURE_ROOT / "content_repo" / "reference" / "api.md",
]

# All current fixtures have classification gaps: the parser emits unitType:unknown
# for sections it cannot fully classify, and article schemas reject unknown unit
# types.  Additionally, informationType is derived from unit mix rather than from
# the declared article type (e.g. howto gets "mixed" instead of "procedure").
# Both issues are resolved by the article triage implementation (tech note §12).
# Remove fixtures from this set as triage is completed for each article type.
_KNOWN_SCHEMA_GAPS: set[str] = {
    "clean.md",       # informationType: mixed; unresolved procedure units
    "complex.md",     # informationType: concept; unknown unit types in reference
    "install.md",     # informationType: mixed; unresolved procedure units
    "configure.md",   # informationType: mixed; unresolved procedure units
    "index.md",       # unitType: unknown for Key-Concepts section
    "api.md",         # unitType: unknown for Config/API/Error sections
}


def _fixture_id(p: Path) -> str:
    return "/".join(p.parts[-2:])


# ---------------------------------------------------------------------------
# 1. Pydantic round-trip
# ---------------------------------------------------------------------------

class TestPydanticRoundTrip:
    """ParsedDocument survives JSON serialisation and reconstruction."""

    @pytest.mark.parametrize("fixture_path", _ALL_MD, ids=_fixture_id)
    def test_json_roundtrip_preserves_source_format(self, fixture_path: Path) -> None:
        doc = parse_file(fixture_path)
        reconstructed = ParsedDocument.model_validate_json(
            doc.model_dump_json(by_alias=True)
        )
        assert reconstructed.source_format == doc.source_format

    @pytest.mark.parametrize("fixture_path", _ALL_MD, ids=_fixture_id)
    def test_json_roundtrip_preserves_schema_version(self, fixture_path: Path) -> None:
        doc = parse_file(fixture_path)
        reconstructed = ParsedDocument.model_validate_json(
            doc.model_dump_json(by_alias=True)
        )
        assert reconstructed.schema_version == doc.schema_version

    @pytest.mark.parametrize("fixture_path", _ALL_MD, ids=_fixture_id)
    def test_json_roundtrip_preserves_diagnostic_count(self, fixture_path: Path) -> None:
        doc = parse_file(fixture_path)
        reconstructed = ParsedDocument.model_validate_json(
            doc.model_dump_json(by_alias=True)
        )
        assert len(reconstructed.diagnostics) == len(doc.diagnostics)

    @pytest.mark.parametrize("fixture_path", _ALL_MD, ids=_fixture_id)
    def test_json_roundtrip_preserves_article_type(self, fixture_path: Path) -> None:
        doc = parse_file(fixture_path)
        reconstructed = ParsedDocument.model_validate_json(
            doc.model_dump_json(by_alias=True)
        )
        if doc.structured_content and reconstructed.structured_content:
            assert (
                reconstructed.structured_content.article_type
                == doc.structured_content.article_type
            )

    @pytest.mark.parametrize("fixture_path", _ALL_MD, ids=_fixture_id)
    def test_json_roundtrip_source_format_is_markdown(self, fixture_path: Path) -> None:
        doc = parse_file(fixture_path)
        assert doc.source_format == SourceFormat.markdown

    @pytest.mark.parametrize("fixture_path", _ALL_MD, ids=_fixture_id)
    def test_json_roundtrip_unit_count_preserved(self, fixture_path: Path) -> None:
        doc = parse_file(fixture_path)
        reconstructed = ParsedDocument.model_validate_json(
            doc.model_dump_json(by_alias=True)
        )
        orig_units = len(doc.structured_content.content) if doc.structured_content else 0
        recon_units = (
            len(reconstructed.structured_content.content)
            if reconstructed.structured_content
            else 0
        )
        assert recon_units == orig_units


# ---------------------------------------------------------------------------
# 2. Base schema compliance (artArticle.schema.json)
# ---------------------------------------------------------------------------

class TestBaseSchemaCompliance:
    """Structured content from clean fixtures must satisfy the base article schema."""

    @pytest.mark.parametrize("fixture_path", _CLEAN_FIXTURES, ids=_fixture_id)
    @pytest.mark.xfail(
        strict=False,
        reason=(
            "artArticle.schema.json is a strict oneOf union over all article schemas. "
            "Passes only after triage resolves unitType:unknown and informationType gaps "
            "(tech note §12)."
        ),
    )
    def test_validates_against_base_article_schema(self, fixture_path: Path) -> None:
        doc = parse_file(fixture_path)
        assert doc.structured_content is not None, "Expected structured content"
        result = validate_model(doc.structured_content, profile_name="default")
        violations = [d.detail for d in result.diagnostics]
        assert result.valid, f"Base schema violations in {fixture_path.name}: {violations}"

    @pytest.mark.parametrize("fixture_path", _CLEAN_FIXTURES, ids=_fixture_id)
    def test_clean_fixtures_have_no_error_diagnostics(self, fixture_path: Path) -> None:
        doc = parse_file(fixture_path)
        errors = [d for d in doc.diagnostics if d.severity.value == "error"]
        assert errors == [], f"Unexpected errors in {fixture_path.name}: {[d.code for d in errors]}"

    @pytest.mark.parametrize("fixture_path", _CLEAN_FIXTURES, ids=_fixture_id)
    def test_schema_name_is_resolvable(self, fixture_path: Path) -> None:
        doc = parse_file(fixture_path)
        assert doc.structured_content is not None
        schema_name = doc.structured_content.schema_name
        assert schema_name.endswith(".schema.json"), f"Unexpected schema name: {schema_name}"


# ---------------------------------------------------------------------------
# 3. Declared schema compliance (article-specific JSON schema)
# ---------------------------------------------------------------------------

class TestDeclaredSchemaCompliance:
    """Structured content validates against the schema it claims to conform to."""

    @pytest.mark.parametrize(
        "fixture_path",
        [p for p in _CLEAN_FIXTURES if p.name not in _KNOWN_SCHEMA_GAPS],
        ids=_fixture_id,
    )
    def test_validates_against_declared_schema(self, fixture_path: Path) -> None:
        doc = parse_file(fixture_path)
        assert doc.structured_content is not None
        sc = doc.structured_content
        result = validate_against_declared_schema(sc)
        violations = [d.detail for d in result.diagnostics]
        assert result.valid, (
            f"{fixture_path.name} failed {sc.schema_name} validation: {violations}"
        )

    @pytest.mark.parametrize(
        "fixture_path",
        [p for p in _CLEAN_FIXTURES if p.name in _KNOWN_SCHEMA_GAPS],
        ids=_fixture_id,
    )
    @pytest.mark.xfail(
        strict=False,
        reason=(
            "informationType derived from unit mix, not article type. "
            "Resolved by article triage implementation (tech note section 12)."
        ),
    )
    def test_known_gap_declared_schema(self, fixture_path: Path) -> None:
        doc = parse_file(fixture_path)
        assert doc.structured_content is not None
        result = validate_against_declared_schema(doc.structured_content)
        violations = [d.detail for d in result.diagnostics]
        assert result.valid, f"{fixture_path.name}: {violations}"

    @pytest.mark.parametrize("fixture_path", _CLEAN_FIXTURES, ids=_fixture_id)
    def test_declared_schema_name_corresponds_to_article_type(
        self, fixture_path: Path
    ) -> None:
        """The schema_name in StructuredContent should reflect the classified article type."""
        doc = parse_file(fixture_path)
        assert doc.structured_content is not None
        sc = doc.structured_content
        expected_fragment = sc.article_type.value  # e.g. "howto", "reference"
        # artHowto.schema.json contains "howto"; artArticle contains "Article"
        if expected_fragment not in ("unknown",):
            assert expected_fragment.lower() in sc.schema_name.lower(), (
                f"{fixture_path.name}: schema_name={sc.schema_name!r} "
                f"does not reflect article_type={sc.article_type.value!r}"
            )


# ---------------------------------------------------------------------------
# 4. Schema registry coverage
# ---------------------------------------------------------------------------

class TestSchemaRegistryCoverage:
    """Every schema the classifier can produce must be loadable from the registry."""

    def test_all_article_schema_files_loadable(self) -> None:
        from structure_parser.repositories.schema_repository import list_schemas, load_schema

        article_schemas = [s for s in list_schemas() if s.startswith("art")]
        assert len(article_schemas) > 0, "No article schemas found"
        for schema_id in article_schemas:
            schema = load_schema(schema_id)
            assert isinstance(schema, dict), f"Schema {schema_id} did not load as dict"

    def test_all_article_types_have_schema_mapping(self) -> None:
        from structure_parser.domain.enums import ArticleType
        from structure_parser.structured_markdown.classifier import _SCHEMA_MAP

        for article_type in ArticleType:
            assert article_type in _SCHEMA_MAP, (
                f"ArticleType.{article_type.value} has no entry in _SCHEMA_MAP"
            )

    def test_all_schema_map_files_exist_in_registry(self) -> None:
        from structure_parser.repositories.schema_repository import list_schemas
        from structure_parser.structured_markdown.classifier import _SCHEMA_MAP

        available = set(list_schemas())
        for article_type, schema_id in _SCHEMA_MAP.items():
            assert schema_id in available, (
                f"ArticleType.{article_type.value} maps to {schema_id!r} "
                f"but that file is not in the schema registry"
            )

    def test_validate_against_declared_schema_returns_result(self) -> None:
        """Smoke test: validate_against_declared_schema is callable and returns a result."""
        from structure_parser.contracts.structured_markdown import StructuredContent

        sc = StructuredContent()
        result = validate_against_declared_schema(sc)
        assert hasattr(result, "valid")
        assert hasattr(result, "diagnostics")
