"""Fixture repository — loads test fixtures and expected contract outputs."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_FIXTURE_DIR = Path(__file__).parent.parent.parent.parent / "tests" / "fixtures"


def get_fixture_dir() -> Path:
    """Return the test fixtures directory."""
    return _FIXTURE_DIR


def load_markdown_fixture(name: str) -> str:
    """Load a Markdown fixture file by name (without extension)."""
    path = _FIXTURE_DIR / "markdown" / f"{name}.md"
    return path.read_text(encoding="utf-8")


def load_html_fixture(name: str) -> str:
    """Load an HTML fixture file by name (without extension)."""
    path = _FIXTURE_DIR / "html" / f"{name}.html"
    return path.read_text(encoding="utf-8")


def load_expected_json(name: str) -> dict[str, Any]:
    """Load an expected JSON contract fixture."""
    # Try various naming patterns
    for pattern in [f"{name}.json", f"{name}.parse.json", f"{name}.diagnostics.json"]:
        path = _FIXTURE_DIR / "expected" / pattern
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    raise FileNotFoundError(f"Expected fixture not found: {name}")
