"""Model validator — validates StructuredContent against a schema profile."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from structure_parser.contracts.diagnostics import DiagnosticFactory
from structure_parser.contracts.structured_markdown import StructuredContent
from structure_parser.contracts.validation import ModelValidationResult
from structure_parser.validation.schema_validator import validate_against_schema
from structure_parser.validation.validation_profiles import get_profile


def validate_against_declared_schema(
    content: StructuredContent,
    model_dir: Path | None = None,
    timeout_seconds: int | None = None,
) -> ModelValidationResult:
    """Validate StructuredContent against the article schema it declares.

    Unlike :func:`validate_model`, this ignores profile-level rules (required
    metadata fields, allowed article types) and validates only the JSON shape
    against the specific schema named in ``content.schema_name``.  This is the
    primary entry point for JSON schema round-trip contract tests.

    :param content:
        The structured content produced by the parser for one document.
    :param model_dir:
        Override the default model schema directory.
    :returns:
        A :class:`ModelValidationResult` with ``valid=True`` or a list of
        diagnostics describing each JSON Schema violation.
    :side effects:
        Reads schema files from disk on first call per model directory.
    """
    source_path = content.source.get("sourcePath") if content.source else None
    data = _to_schema_dict(content)
    return validate_against_schema(
        data=data,
        schema_id=content.schema_name,
        model_dir=model_dir,
        source_path=source_path,
        timeout_seconds=timeout_seconds,
    )


def validate_model(
    content: StructuredContent,
    profile_name: str = "default",
    model_dir: Path | None = None,
    timeout_seconds: int | None = None,
) -> ModelValidationResult:
    """Validate a StructuredContent against a named validation profile.

    Args:
        content: The structured content to validate.
        profile_name: One of the named profiles in validation_profiles.PROFILES.
        model_dir: Override the default model schema directory.

    Returns:
        A ModelValidationResult (valid flag + any diagnostic messages).
    """
    profile = get_profile(profile_name)
    source_path = content.source.get("sourcePath") if content.source else None

    data = _to_schema_dict(content)
    result = validate_against_schema(
        data=data,
        schema_id=profile.schema_id,
        model_dir=model_dir,
        source_path=source_path,
        timeout_seconds=timeout_seconds,
    )

    # Extra profile-level checks that JSON Schema cannot express
    extra_diags = []

    for field in profile.required_metadata_fields:
        if field == "title":
            if not content.title and "title" not in content.metadata:
                extra_diags.append(
                    DiagnosticFactory.schema_validation_failed(
                        detail="Required metadata field missing: title",
                        source_path=source_path,
                    )
                )
        elif field not in content.metadata:
            extra_diags.append(
                DiagnosticFactory.schema_validation_failed(
                    detail=f"Required metadata field missing: {field}",
                    source_path=source_path,
                )
            )

    if profile.allowed_article_types and (
        content.article_type.value not in profile.allowed_article_types
    ):
        extra_diags.append(
            DiagnosticFactory.schema_validation_failed(
                detail=(
                    f"Article type {content.article_type.value!r} not allowed "
                    f"by profile {profile.name!r}"
                ),
                source_path=source_path,
            )
        )

    if extra_diags:
        return ModelValidationResult(
            schema_id=result.schema_id,
            valid=False,
            source_path=result.source_path,
            diagnostics=result.diagnostics + extra_diags,
        )

    return result


def _to_schema_dict(content: StructuredContent) -> dict:
    """Convert a StructuredContent to a JSON-serialisable dict matching the schema shape."""
    units = []
    for unit in content.content:
        u_dict: dict = {
            "unitType": unit.unit_type.value,
            "informationType": unit.information_type.value,
            "triageStatus": unit.triage_status.value,
        }
        if unit.unit_id:
            u_dict["unitId"] = unit.unit_id
        if unit.title:
            u_dict["title"] = unit.title
        if unit.metadata:
            u_dict["metadata"] = unit.metadata
        if unit.procedure_representation is not None:
            u_dict["procedureRepresentation"] = unit.procedure_representation.value
        if unit.term:
            u_dict["term"] = unit.term

        u_dict["content"] = [_component_to_dict(c) for c in unit.content]
        units.append(u_dict)

    result: dict = {
        "schema": content.schema_name,
        "version": content.version,
        "articleType": content.article_type.value,
        "informationType": content.information_type.value,
        "triageStatus": content.triage_status.value,
        "content": units,
    }
    if content.article_id:
        result["articleId"] = content.article_id
    if content.title:
        result["title"] = content.title
    if content.dita_type:
        result["ditaType"] = content.dita_type
    if content.metadata:
        result["metadata"] = content.metadata
    return result


def _component_to_dict(comp: Any) -> dict:
    """Serialise a Component to a schema-aligned dict.

    Only fields that appear in the JSON schema (camelCase) are emitted, and only
    required-or-present fields are included so that optional-but-absent fields do
    not trip ``additionalProperties`` validators.
    """
    from structure_parser.contracts.structured_markdown import Component
    from structure_parser.domain.enums import ComponentType

    c: Component = comp
    ct = c.component_type

    d: dict = {"componentType": ct.value}

    # Common optional fields included when present
    if c.markdown:
        d["markdown"] = c.markdown
    if c.text:
        d["text"] = c.text
    if c.triage_status and c.triage_status.value != "known":
        d["triageStatus"] = c.triage_status.value

    # compUnknown always needs triageStatus
    if ct == ComponentType.compUnknown:
        d["triageStatus"] = c.triage_status.value if c.triage_status else "unknown"

    # Header components require level
    if ct in (
        ComponentType.compHeaderH1, ComponentType.compHeaderH2, ComponentType.compHeaderH3,
        ComponentType.compHeaderH4, ComponentType.compHeaderH5, ComponentType.compHeaderH6,
    ):
        if c.level is not None:
            d["level"] = c.level

    # Code block requires code field
    if ct == ComponentType.compBlockCode:
        if c.code is not None:
            d["code"] = c.code
        if c.language:
            d["language"] = c.language

    # List components require count and content (list items)
    if ct in (ComponentType.compListOrdered, ComponentType.compListUnordered):
        if c.count is not None:
            d["count"] = c.count
        d["content"] = [_component_to_dict(item) for item in c.content]

    # List item requires order; content may be attributes or nested block components
    if ct == ComponentType.compListItem:
        if c.order is not None:
            d["order"] = c.order
        if c.content:
            d["content"] = [_mixed_to_dict(item) for item in c.content]

    # Alert requires alertType
    if ct == ComponentType.compAlert:
        if c.alert_type:
            d["alertType"] = c.alert_type
        if c.content:
            d["content"] = [_component_to_dict(child) for child in c.content]

    # Block quote may have content
    if ct == ComponentType.compBlockQuote:
        if c.content:
            d["content"] = [_component_to_dict(child) for child in c.content]

    # Table requires columnCount, rowCount, content (rows)
    if ct == ComponentType.compTable:
        if c.column_count is not None:
            d["columnCount"] = c.column_count
        if c.row_count is not None:
            d["rowCount"] = c.row_count
        d["content"] = [_component_to_dict(row) for row in c.content]

    # Table row requires rowIndex, rowRole, content (cells)
    if ct == ComponentType.compTableRow:
        if c.row_index is not None:
            d["rowIndex"] = c.row_index
        if c.row_role:
            d["rowRole"] = c.row_role
        d["content"] = [_component_to_dict(cell) for cell in c.content]

    # Table cell requires cellRole, columnIndex
    if ct == ComponentType.compTableCell:
        if c.cell_role:
            d["cellRole"] = c.cell_role
        if c.column_index is not None:
            d["columnIndex"] = c.column_index
        if c.colspan is not None:
            d["colspan"] = c.colspan
        if c.rowspan is not None:
            d["rowspan"] = c.rowspan
        if c.content:
            d["content"] = [_mixed_to_dict(a) for a in c.content]

    return d


def _mixed_to_dict(item: Any) -> dict:
    """Serialise either an Attribute or a Component to a schema-aligned dict."""
    from structure_parser.contracts.structured_markdown import Attribute, Component

    if isinstance(item, Component):
        return _component_to_dict(item)
    return _attr_to_dict(item)


def _attr_to_dict(attr: Any) -> dict:
    """Serialise an Attribute to a schema-aligned dict."""
    from structure_parser.contracts.structured_markdown import Attribute
    from structure_parser.domain.enums import AttributeType

    a: Attribute = attr
    d: dict = {"attType": a.att_type.value}
    if a.text:
        d["text"] = a.text
    if a.markdown:
        d["markdown"] = a.markdown
    if a.href:
        d["href"] = a.href
    if a.alt_text:
        d["altText"] = a.alt_text
    if a.source:
        d["source"] = a.source
    # attUnknown requires triageStatus
    if a.att_type == AttributeType.attUnknown and a.triage_status:
        d["triageStatus"] = a.triage_status.value
    if a.content:
        d["content"] = [_attr_to_dict(child) for child in a.content]
    return d
