"""Contract tests: parser-emitted known units validate against their unit schemas.

These tests enforce the primary acceptance criterion from the b2 implementation
notes: a parser-emitted known unit should validate against the JSON Schema for
that unit type.  A schema failure should indicate authoring noncompliance, not
an internal mismatch between the parser and its own model contract.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from structure_parser import parse_file
from structure_parser.domain.enums import ArticleType, UnitType
from structure_parser.validation.model_validator import validate_against_declared_schema
from structure_parser.validation.schema_validator import validate_against_schema

_FIXTURE_ROOT = Path(__file__).parent.parent / "fixtures"
_MD = _FIXTURE_ROOT / "markdown"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_UNIT_SCHEMA_MAP = {
    UnitType.introduction: "unitIntroduction.schema.json",
    UnitType.prerequisites: "unitPrerequisites.schema.json",
    UnitType.procedure: "unitProcedure.schema.json",
    UnitType.concept: "unitConcept.schema.json",
    UnitType.reference: "unitReference.schema.json",
    UnitType.fact: "unitFact.schema.json",
    UnitType.principle: "unitPrinciple.schema.json",
    UnitType.link_nextstep: "unitLinkNextstep.schema.json",
    UnitType.link_related: "unitLinkRelated.schema.json",
}


def _validate_unit(unit_dict: dict, schema_id: str) -> list[str]:
    """Return a list of validation error messages (empty if valid)."""
    result = validate_against_schema(data=unit_dict, schema_id=schema_id)
    if result.valid:
        return []
    return [d.message for d in result.diagnostics]


# ---------------------------------------------------------------------------
# 1. Known units in clean fixtures validate against their unit schemas
# ---------------------------------------------------------------------------

class TestKnownUnitValidation:
    """Parser-emitted known units must pass their corresponding unit schemas."""

    def test_procedure_unit_validates(self) -> None:
        """A procedure unit with an ordered list validates against unitProcedure."""
        doc = parse_file(_MD / "procedure_unit.md")
        sc = doc.structured_content
        assert sc is not None
        proc_units = [u for u in sc.content if u.unit_type == UnitType.procedure]
        assert proc_units, "Expected at least one procedure unit in procedure_unit.md"

        from structure_parser.validation.model_validator import _to_schema_dict
        full = _to_schema_dict(sc)
        unit_dicts = {
            sc.content[i].unit_type.value: full["content"][i]
            for i in range(len(sc.content))
        }

        proc_dict = next(
            full["content"][i]
            for i, u in enumerate(sc.content)
            if u.unit_type == UnitType.procedure
        )
        errors = _validate_unit(proc_dict, "unitProcedure.schema.json")
        assert not errors, f"Procedure unit failed schema: {errors[:3]}"

    def test_prerequisites_unit_validates(self) -> None:
        """A prerequisites unit validates against unitPrerequisites."""
        doc = parse_file(_MD / "procedure_unit.md")
        sc = doc.structured_content
        assert sc is not None

        from structure_parser.validation.model_validator import _to_schema_dict
        full = _to_schema_dict(sc)

        prereq_dicts = [
            full["content"][i]
            for i, u in enumerate(sc.content)
            if u.unit_type == UnitType.prerequisites
        ]
        assert prereq_dicts, "Expected a prerequisites unit in procedure_unit.md"
        errors = _validate_unit(prereq_dicts[0], "unitPrerequisites.schema.json")
        assert not errors, f"Prerequisites unit failed schema: {errors[:3]}"

    def test_introduction_unit_validates(self) -> None:
        """A named introduction unit validates against unitIntroduction."""
        doc = parse_file(_MD / "clean.md")
        sc = doc.structured_content
        assert sc is not None

        from structure_parser.validation.model_validator import _to_schema_dict
        full = _to_schema_dict(sc)

        intro_dicts = [
            full["content"][i]
            for i, u in enumerate(sc.content)
            if u.unit_type == UnitType.introduction
        ]
        assert intro_dicts, "Expected an introduction unit in clean.md"
        errors = _validate_unit(intro_dicts[0], "unitIntroduction.schema.json")
        assert not errors, f"Introduction unit failed schema: {errors[:3]}"

    def test_link_nextstep_unit_validates(self) -> None:
        """A link-nextstep unit validates against unitLinkNextstep."""
        doc = parse_file(_MD / "clean.md")
        sc = doc.structured_content
        assert sc is not None

        from structure_parser.validation.model_validator import _to_schema_dict
        full = _to_schema_dict(sc)

        nextstep_dicts = [
            full["content"][i]
            for i, u in enumerate(sc.content)
            if u.unit_type == UnitType.link_nextstep
        ]
        assert nextstep_dicts, "Expected a link-nextstep unit in clean.md"
        errors = _validate_unit(nextstep_dicts[0], "unitLinkNextstep.schema.json")
        assert not errors, f"Link-nextstep unit failed schema: {errors[:3]}"


# ---------------------------------------------------------------------------
# 2. Article-level informationType matches schema expectation
# ---------------------------------------------------------------------------

class TestArticleInfoType:
    """Article-level informationType must match the canonical value for each article type."""

    def test_howto_has_procedure_info_type(self) -> None:
        doc = parse_file(_MD / "clean.md")
        sc = doc.structured_content
        assert sc is not None
        assert sc.article_type == ArticleType.howto
        assert sc.information_type.value == "procedure", (
            f"howto article must have informationType=procedure, got {sc.information_type.value!r}"
        )

    def test_reference_has_fact_info_type(self) -> None:
        doc = parse_file(_FIXTURE_ROOT / "content_repo" / "reference" / "api.md")
        sc = doc.structured_content
        assert sc is not None
        assert sc.article_type == ArticleType.reference
        assert sc.information_type.value == "fact", (
            f"reference article must have informationType=fact, got {sc.information_type.value!r}"
        )


# ---------------------------------------------------------------------------
# 3. Conservative howto selection
# ---------------------------------------------------------------------------

class TestConservativeHowtoSelection:
    """howto requires procedure dominance; mixed content defaults to topic."""

    def test_nextstep_only_doc_is_not_howto(self) -> None:
        """A document with only a Next Steps section and concept content is not howto."""
        doc = parse_file(_MD / "nextstep_only.md")
        sc = doc.structured_content
        assert sc is not None
        assert sc.article_type != ArticleType.howto, (
            f"nextstep_only.md should not be howto (got {sc.article_type.value!r}). "
            "A Next Steps section alone is not procedure evidence."
        )

    def test_multiple_procedure_units_is_howto(self) -> None:
        """A document with multiple ordered-list procedure units should be howto."""
        doc = parse_file(_MD / "clean.md")
        sc = doc.structured_content
        assert sc is not None
        proc_count = sum(1 for u in sc.content if u.unit_type == UnitType.procedure)
        assert proc_count >= 1, "clean.md should have at least one procedure unit"
        assert sc.article_type == ArticleType.howto, (
            f"clean.md with procedure units should be howto, got {sc.article_type.value!r}"
        )


# ---------------------------------------------------------------------------
# 4. Topic fallback for mixed content
# ---------------------------------------------------------------------------

class TestTopicFallback:
    """Mixed content without a dominant article type defaults to topic."""

    def test_mixed_content_is_topic(self) -> None:
        """A document with overview, reference, and navigation units defaults to topic."""
        doc = parse_file(_MD / "topic_mixed.md")
        sc = doc.structured_content
        assert sc is not None
        assert sc.article_type == ArticleType.topic, (
            f"topic_mixed.md (mixed concept/reference/nav) should be topic, "
            f"got {sc.article_type.value!r}"
        )


# ---------------------------------------------------------------------------
# 5. Full article schema compliance for clean fixtures
# ---------------------------------------------------------------------------

class TestFullArticleCompliance:
    """Parser-emitted known articles validate against their declared article schemas."""

    @pytest.mark.parametrize("fixture_name", [
        "clean.md",
        "install.md",
        "configure.md",
    ])
    def test_howto_fixtures_validate(self, fixture_name: str) -> None:
        """Howto fixtures with authoritative metadata must validate against artHowto."""
        f = _FIXTURE_ROOT / "markdown" / fixture_name
        if not f.exists():
            f = _FIXTURE_ROOT / "content_repo" / "guide" / fixture_name
        doc = parse_file(f)
        sc = doc.structured_content
        assert sc is not None
        result = validate_against_declared_schema(sc)
        violations = [d.message for d in result.diagnostics]
        assert result.valid, (
            f"{fixture_name} failed {sc.schema_name}: {violations[:3]}"
        )
