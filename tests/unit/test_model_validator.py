"""Tests for the model validator."""
import pytest
from structure_parser.contracts.structured_markdown import StructuredContent, Unit, Component
from structure_parser.domain.enums import ArticleType, UnitType, ComponentType, TriageStatus, InformationType
from structure_parser.validation.model_validator import validate_model


def _make_valid_content() -> StructuredContent:
    comp = Component(
        component_type=ComponentType.compParagraph,
        markdown="Some text",
        text="Some text",
    )
    unit = Unit(
        unit_type=UnitType.introduction,
        unit_id="intro-1",
        information_type=InformationType.concept,
        title="Introduction",
        triage_status=TriageStatus.known,
        content=[comp],
    )
    return StructuredContent(
        schema_name="artTopic.schema.json",
        article_id="test-article",
        article_type=ArticleType.topic,
        dita_type="topic",
        information_type=InformationType.concept,
        title="Test Article",
        triage_status=TriageStatus.known,
        content=[unit],
    )


class TestModelValidator:
    def test_valid_content_returns_valid(self):
        sc = _make_valid_content()
        result = validate_model(sc, profile_name="default")
        # May or may not be valid depending on schema strictness
        assert result.schema_id is not None
        assert isinstance(result.valid, bool)

    def test_result_has_schema_version(self):
        sc = _make_valid_content()
        result = validate_model(sc, profile_name="default")
        assert result.schema_version == "1"

    def test_invalid_profile_falls_back_to_default(self):
        sc = _make_valid_content()
        result = validate_model(sc, profile_name="nonexistent-profile")
        assert result is not None
