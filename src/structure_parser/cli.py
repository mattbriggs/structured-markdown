"""Typer CLI entry point for the structure-parser tool."""
from __future__ import annotations
import json
import sys
from pathlib import Path
from typing import Optional

import typer
from typing_extensions import Annotated

from structure_parser.contracts.config import ParserConfig
from structure_parser.logging_config import configure_logging
from structure_parser.application.commands import (
    ParseCommand,
    ValidateMarkdownCommand,
    InspectStructureCommand,
    InspectModelCommand,
    InspectReferencesCommand,
    InspectDiagnosticsCommand,
    TransformReadinessCommand,
    ValidateContractCommand,
)

app = typer.Typer(
    name="structure-parser",
    help="Structure-aware parser and validator for structured Markdown and HTML.",
    add_completion=False,
)

_JsonOption = Annotated[bool, typer.Option("--json", help="Emit JSON output.")]
_StrictOption = Annotated[bool, typer.Option("--strict", help="Exit 1 on warnings in addition to errors.")]
_DebugOption = Annotated[bool, typer.Option("--debug", help="Enable debug logging.")]
_SchemaOption = Annotated[Optional[str], typer.Option("--schema", help="Schema ID for validation.")]
_TargetOption = Annotated[Optional[list[str]], typer.Option("--target", help="Readiness target (repeatable).")]


def _config(debug: bool = False) -> ParserConfig:
    if debug:
        configure_logging(debug=True)
    return ParserConfig(emit_debug_logs=debug)


@app.command("parse")
def cmd_parse(
    paths: Annotated[list[Path], typer.Argument(help="Files to parse.")],
    json_out: _JsonOption = False,
    debug: _DebugOption = False,
) -> None:
    """Parse one or more Markdown or HTML files."""
    text, exit_code = ParseCommand().run(paths, _config(debug), json_output=json_out)
    typer.echo(text)
    raise typer.Exit(exit_code)


@app.command("validate-markdown")
def cmd_validate(
    paths: Annotated[list[Path], typer.Argument(help="Files to validate.")],
    schema: _SchemaOption = None,
    strict: _StrictOption = False,
    debug: _DebugOption = False,
) -> None:
    """Validate structured Markdown against an authoring model schema."""
    schema_id = schema or "artArticle.schema.json"
    text, exit_code = ValidateMarkdownCommand().run(paths, schema_id, _config(debug), strict=strict)
    typer.echo(text)
    raise typer.Exit(exit_code)


@app.command("inspect-structure")
def cmd_inspect_structure(
    path: Annotated[Path, typer.Argument(help="File to inspect.")],
    debug: _DebugOption = False,
) -> None:
    """Display the heading structure tree of a parsed document."""
    text, exit_code = InspectStructureCommand().run(path, _config(debug))
    typer.echo(text)
    raise typer.Exit(exit_code)


@app.command("inspect-model")
def cmd_inspect_model(
    path: Annotated[Path, typer.Argument(help="File to inspect.")],
    debug: _DebugOption = False,
) -> None:
    """Display the article/unit/component classification of a parsed document."""
    text, exit_code = InspectModelCommand().run(path, _config(debug))
    typer.echo(text)
    raise typer.Exit(exit_code)


@app.command("inspect-references")
def cmd_inspect_references(
    path: Annotated[Path, typer.Argument(help="File to inspect.")],
    debug: _DebugOption = False,
) -> None:
    """Display all references and their resolution states."""
    text, exit_code = InspectReferencesCommand().run(path, _config(debug))
    typer.echo(text)
    raise typer.Exit(exit_code)


@app.command("inspect-diagnostics")
def cmd_inspect_diagnostics(
    path: Annotated[Path, typer.Argument(help="File to inspect.")],
    debug: _DebugOption = False,
) -> None:
    """Display all diagnostics grouped by severity."""
    text, exit_code = InspectDiagnosticsCommand().run(path, _config(debug))
    typer.echo(text)
    raise typer.Exit(exit_code)


@app.command("transform-readiness")
def cmd_readiness(
    path: Annotated[Path, typer.Argument(help="File to evaluate.")],
    targets: _TargetOption = None,
    debug: _DebugOption = False,
) -> None:
    """Evaluate transform-readiness preconditions for a document."""
    text, exit_code = TransformReadinessCommand().run(path, _config(debug), targets=targets)
    typer.echo(text)
    raise typer.Exit(exit_code)


@app.command("validate-contract")
def cmd_validate_contract(
    paths: Annotated[list[Path], typer.Argument(help="Fixture files to check.")],
    debug: _DebugOption = False,
) -> None:
    """Validate fixture files against expected contract behavior."""
    text, exit_code = ValidateContractCommand().run(paths, _config(debug))
    typer.echo(text)
    raise typer.Exit(exit_code)


if __name__ == "__main__":
    app()
