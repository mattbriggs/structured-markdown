"""Schema repository — locates and loads JSON Schema files from the model directory."""
from __future__ import annotations

import json
from importlib import resources
from pathlib import Path
from typing import Any

from structure_parser.domain.errors import SchemaRepositoryError


def get_default_model_dir() -> Path:
    """Return the path to the bundled model schema directory.

    Prefers the package-internal resources (works from a wheel install).
    Falls back to the source-checkout path for development installs.
    """
    # Installed package: schemas live inside the package as resources
    try:
        pkg_resources = resources.files("structure_parser.resources.model.articles")
        candidate = Path(str(pkg_resources))
        if candidate.exists():
            return candidate
    except (ModuleNotFoundError, AttributeError, TypeError):
        pass

    # Source checkout or editable install: schemas live in model/ at the repo root
    repo_root = Path(__file__).parent.parent.parent.parent
    source_dir = repo_root / "model" / "articles"
    if source_dir.exists():
        return source_dir

    raise SchemaRepositoryError(
        "Model schema directory not found. "
        "Install the package properly or run from the source checkout.",
        path="model/articles",
    )


def load_schema(schema_id: str, model_dir: Path | None = None) -> dict[str, Any]:
    """Load a JSON Schema by filename from the model directory.

    Args:
        schema_id: The filename of the schema (e.g. "artHowto.schema.json").
        model_dir: Directory to search. Defaults to the bundled model directory.

    Returns:
        The parsed JSON schema as a dict.

    Raises:
        SchemaRepositoryError: If the schema file cannot be found or parsed.
    """
    base = model_dir or get_default_model_dir()

    matches = list(base.rglob(schema_id))
    if not matches:
        raise SchemaRepositoryError(
            f"Schema {schema_id!r} not found under {base}",
            path=str(base),
        )

    schema_path = matches[0]
    try:
        with schema_path.open(encoding="utf-8") as fh:
            return json.load(fh)
    except (json.JSONDecodeError, OSError) as exc:
        raise SchemaRepositoryError(
            f"Failed to load schema {schema_id!r}: {exc}",
            path=str(schema_path),
        ) from exc


def list_schemas(model_dir: Path | None = None) -> list[str]:
    """Return a sorted list of available schema filenames.

    Args:
        model_dir: Directory to search. Defaults to the bundled model directory.

    Returns:
        Sorted list of .schema.json filenames found in the model directory.
    """
    base = model_dir or get_default_model_dir()
    return sorted(p.name for p in base.rglob("*.schema.json"))
