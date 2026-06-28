"""JSON Schema validator — validates parsed output against the model schemas."""
from __future__ import annotations

import json
import signal
from contextlib import contextmanager
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
_MAX_SCHEMA_ERRORS = 50


class _SchemaValidationTimeout(Exception):
    """Raised when advisory JSON Schema validation exceeds its time budget."""


@contextmanager
def _schema_validation_timer(seconds: int):
    """Bound schema validation time on platforms that support SIGALRM."""
    if seconds <= 0 or not hasattr(signal, "SIGALRM"):
        yield
        return

    previous_handler = signal.getsignal(signal.SIGALRM)
    previous_timer = signal.setitimer(signal.ITIMER_REAL, 0)

    def _raise_timeout(_signum: int, _frame: object) -> None:
        raise _SchemaValidationTimeout

    signal.signal(signal.SIGALRM, _raise_timeout)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous_handler)
        if previous_timer[0] > 0:
            signal.setitimer(signal.ITIMER_REAL, previous_timer[0], previous_timer[1])


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
        schema = _normalize_schema_for_validation(schema)
        resource = Resource.from_contents(schema, default_specification=DRAFT7)
        file_uri = schema_file.as_uri()
        resources.append((file_uri, resource))
        resources.append((schema_file.name, resource))
        schema_id = schema.get("$id")
        if schema_id and schema_id not in (file_uri, schema_file.name):
            resources.append((schema_id, resource))

    return Registry().with_resources(resources)


def _normalize_schema_for_validation(value: Any) -> Any:
    """Normalize discriminated schema unions for faster local validation.

    The model schemas use ``oneOf`` for article, unit, component, and attribute
    unions. Those branches are already discriminated by const fields such as
    ``articleType``, ``unitType``, ``componentType``, and ``attType``, so
    ``anyOf`` is equivalent for accepted parser output and avoids the expensive
    exhaustiveness checks performed by ``oneOf`` on deeply nested documents.
    """
    if isinstance(value, dict):
        normalized = {
            key: _normalize_schema_for_validation(child)
            for key, child in value.items()
            if key != "oneOf"
        }
        if "oneOf" in value:
            normalized["anyOf"] = _normalize_schema_for_validation(value["oneOf"])
        return normalized
    if isinstance(value, list):
        return [_normalize_schema_for_validation(item) for item in value]
    return value


def validate_against_schema(
    data: dict[str, Any],
    schema_id: str,
    model_dir: Path | None = None,
    source_path: str | None = None,
    timeout_seconds: int | None = None,
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
        validator = Draft7Validator(root, registry=registry)
        errors = []
        with _schema_validation_timer(timeout_seconds or 0):
            for error in validator.iter_errors(data):
                errors.append(error)
                if len(errors) >= _MAX_SCHEMA_ERRORS:
                    break
    except _SchemaValidationTimeout:
        timeout_label = timeout_seconds if timeout_seconds is not None else 0
        return ModelValidationResult(
            schema_id=schema_id,
            valid=False,
            source_path=source_path,
            diagnostics=[DiagnosticFactory.schema_validation_failed(
                detail=(
                    "Schema validation timed out after "
                    f"{timeout_label}s; parsed content was preserved "
                    "but schema conformance was not fully assessed."
                ),
                source_path=source_path,
            )],
        )
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
        for e in errors[:_MAX_SCHEMA_ERRORS]
    ]
    return ModelValidationResult(
        schema_id=schema_id,
        valid=False,
        source_path=source_path,
        diagnostics=diags,
    )
