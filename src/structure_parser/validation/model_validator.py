"""Model validator — validates StructuredContent against a schema profile."""
from __future__ import annotations

from pathlib import Path

from structure_parser.contracts.diagnostics import DiagnosticFactory
from structure_parser.contracts.structured_markdown import StructuredContent
from structure_parser.contracts.validation import ModelValidationResult
from structure_parser.validation.schema_validator import validate_against_schema
from structure_parser.validation.validation_profiles import get_profile


def validate_against_declared_schema(
    content: StructuredContent,
    model_dir: Path | None = None,
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
    )


def validate_model(
    content: StructuredContent,
    profile_name: str = "default",
    model_dir: Path | None = None,
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

        comps = []
        for comp in unit.content:
            c_dict: dict = {"componentType": comp.component_type.value}
            if comp.markdown:
                c_dict["markdown"] = comp.markdown
            if comp.text:
                c_dict["text"] = comp.text
            comps.append(c_dict)
        u_dict["content"] = comps
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
