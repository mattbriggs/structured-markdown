"""JSON Schema validator — validates parsed output against the model schemas."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft7Validator, RefResolver

from structure_parser.contracts.diagnostics import DiagnosticFactory
from structure_parser.contracts.validation import ModelValidationResult
from structure_parser.domain.errors import SchemaRepositoryError
from structure_parser.repositories.schema_repository import get_default_model_dir, load_schema


def _build_schema_store(model_dir: Path) -> dict[str, Any]:
    """Pre-load all .schema.json files so RefResolver never hits the filesystem directly.

    Registers each schema under three keys so all $ref forms resolve:
      1. The bare filename ("artHowto.schema.json")
      2. The file:// URI of the actual file
      3. The $id value if it differs from the filename
    """
    store: dict[str, Any] = {}
    for schema_file in model_dir.rglob("*.schema.json"):
        try:
            schema = json.loads(schema_file.read_text(encoding="utf-8"))
        except Exception:
            continue
        file_uri = schema_file.as_uri()
        store[file_uri] = schema
        # Also register by bare filename so relative $refs resolve
        store[schema_file.name] = schema
        # Register by $id if present
        schema_id = schema.get("$id")
        if schema_id and schema_id not in store:
            store[schema_id] = schema
    return store


def validate_against_schema(
    data: dict[str, Any],
    schema_id: str,
    model_dir: Path | None = None,
    source_path: str | None = None,
) -> ModelValidationResult:
    """Validate a dict against a named JSON Schema from the model directory.

    :param data: The JSON-serialisable dict to validate.
    :param schema_id: Filename of the schema (e.g. ``"artHowto.schema.json"``).
    :param model_dir: Override the default model directory.
    :param source_path: Optional path for diagnostic context.
    :returns: A ``ModelValidationResult`` with ``valid=True`` or a list of diagnostics.
    """
    base = model_dir or get_default_model_dir()

    try:
        schema = load_schema(schema_id, base)
    except SchemaRepositoryError as exc:
        return ModelValidationResult(
            schema_id=schema_id,
            valid=False,
            source_path=source_path,
            diagnostics=[DiagnosticFactory.schema_file_not_found(str(exc))],
        )

    # Locate the schema file to anchor the RefResolver's base URI
    matches = list(base.rglob(schema_id))
    if not matches:
        return ModelValidationResult(
            schema_id=schema_id,
            valid=False,
            source_path=source_path,
            diagnostics=[DiagnosticFactory.schema_file_not_found(schema_id)],
        )

    schema_path = matches[0]
    store = _build_schema_store(base)

    resolver = RefResolver(
        base_uri=schema_path.as_uri(),
        referrer=schema,
        store=store,
    )

    try:
        errors = list(Draft7Validator(schema, resolver=resolver).iter_errors(data))
    except Exception as exc:
        return ModelValidationResult(
            schema_id=schema_id,
            valid=False,
            source_path=source_path,
            diagnostics=[DiagnosticFactory.schema_validation_failed(
                detail=f"Validator error: {exc}",
                source_path=source_path,
            )],
        )

    if not errors:
        return ModelValidationResult(schema_id=schema_id, valid=True, source_path=source_path)

    diags = [
        DiagnosticFactory.schema_validation_failed(
            detail=f"{e.json_path}: {e.message}",
            source_path=source_path,
        )
        for e in errors[:50]
    ]
    return ModelValidationResult(
        schema_id=schema_id,
        valid=False,
        source_path=source_path,
        diagnostics=diags,
    )
