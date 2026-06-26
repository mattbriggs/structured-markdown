"""JSON Schema validator — validates parsed output against the model schemas."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft7Validator
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT7

from structure_parser.contracts.diagnostics import DiagnosticFactory
from structure_parser.contracts.validation import ModelValidationResult
from structure_parser.repositories.schema_repository import get_default_model_dir

# Meta-schema URIs stubbed offline so the registry never hits the network.
_OFFLINE_META_URIS = [
    "https://json-schema.org/draft/2019-09/schema",
    "https://json-schema.org/draft-07/schema",
    "https://json-schema.org/draft-07/schema#",
    "http://json-schema.org/draft-07/schema#",
    "http://json-schema.org/draft-07/schema",
]
_META_STUB: dict[str, Any] = {"type": "object"}


def _build_registry(model_dir: Path) -> Registry:
    """Build a referencing.Registry with all model schemas pre-loaded.

    Each schema is registered under its absolute file:// URI so that relative
    ``$ref`` values resolve correctly within the model directory tree.  Schemas
    are also indexed under their bare filename and ``$id`` for flexible lookup.
    """
    resources: list[tuple[str, Resource[Any]]] = []

    stub = Resource.from_contents(_META_STUB, default_specification=DRAFT7)
    for uri in _OFFLINE_META_URIS:
        resources.append((uri, stub))

    for schema_file in model_dir.rglob("*.schema.json"):
        try:
            schema = json.loads(schema_file.read_text(encoding="utf-8"))
        except Exception:
            continue
        resource = Resource.from_contents(schema, default_specification=DRAFT7)
        file_uri = schema_file.as_uri()
        resources.append((file_uri, resource))
        resources.append((schema_file.name, resource))
        schema_id = schema.get("$id")
        if schema_id and schema_id not in (file_uri, schema_file.name):
            resources.append((schema_id, resource))

    return Registry().with_resources(resources)


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

    matches = list(base.rglob(schema_id))
    if not matches:
        return ModelValidationResult(
            schema_id=schema_id,
            valid=False,
            source_path=source_path,
            diagnostics=[DiagnosticFactory.schema_file_not_found(schema_id)],
        )

    registry = _build_registry(base)
    schema_file_uri = matches[0].as_uri()

    try:
        # Use a $ref wrapper so the validator retrieves the schema from the registry
        # by its file:// URI — this gives relative $refs the correct directory context.
        root = {"$ref": schema_file_uri}
        errors = list(Draft7Validator(root, registry=registry).iter_errors(data))
    except Exception as exc:
        return ModelValidationResult(
            schema_id=schema_id,
            valid=False,
            source_path=source_path,
            diagnostics=[DiagnosticFactory.schema_validation_failed(
                detail=f"Schema resolution inconclusive: {exc}",
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
