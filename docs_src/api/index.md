# Python API Reference

## Top-Level Imports

The public API surface is small by design. Import the two entry-point functions directly from the package root, and import contract models from their individual modules:

```python
from structure_parser import parse_file, parse_files
from structure_parser.contracts.config import ParserConfig
from structure_parser.contracts.pipeline import PipelineConfig, PipelineRunResult
from structure_parser.contracts.parsed_document import ParsedDocument
from structure_parser.contracts.parse_run_result import ParseRunResult, ParseStats
from structure_parser.contracts.structured_markdown import StructuredContent, Unit, Component, Attribute
from structure_parser.contracts.diagnostics import Diagnostic
from structure_parser.contracts.references import Reference
from structure_parser.contracts.validation import ModelValidationResult
from structure_parser.contracts.transform_readiness import TransformReadiness, TargetReadiness
from structure_parser.contracts.provenance import DocumentProvenance, SourceSpan
from structure_parser.domain.enums import (
    Severity, SourceFormat, ArticleType, UnitType, ComponentType, AttributeType,
    InformationType, TriageStatus, ReadinessStatus, ResolutionState, ProvenanceStatus
)
from structure_parser.pipeline import run_pipeline
from structure_parser.pipeline.reporting import CsvInventoryReporter
```

Everything else is internal. Do not import from `structure_parser.adapters`, `structure_parser.application`, `structure_parser.enrichment`, or `structure_parser.structured_markdown` directly; those namespaces are private and may change without notice.

## parse_file()

Parses a single source file and returns a `ParsedDocument`.

```python
def parse_file(
    path: str | Path,
    config: ParserConfig | None = None,
) -> ParsedDocument:
```

**Parameters**

| Parameter | Type | Description |
|---|---|---|
| `path` | `str \| Path` | Absolute or relative path to the source file. Relative paths are resolved against the current working directory. |
| `config` | `ParserConfig \| None` | Configuration for this parse run. When `None`, a default `ParserConfig` is used. |

**Returns** `ParsedDocument` — always returns a document object, even when the file is missing or unparseable. Failures are recorded as diagnostics rather than raised as exceptions.

**Raises** nothing. The function is designed to be safe: all errors (missing file, unsupported format, internal failure) produce SP-NNN diagnostics on the returned `ParsedDocument`.

**Side effects** none. The function is pure and stateless; calling it multiple times on the same path produces identical results given the same file contents and configuration.

**Example**

```python
from structure_parser import parse_file

doc = parse_file("docs/install.md")
if doc.has_errors:
    for d in doc.diagnostics:
        if d.severity == "error":
            print(f"[{d.code}] {d.message}")
else:
    print(f"Title: {doc.title}")
    print(f"Article type: {doc.structured_content.article_type}")
```

## parse_files()

Parses a list of source files in sequence and returns a `ParseRunResult` containing one `ParsedDocument` per input path plus aggregate statistics.

```python
def parse_files(
    paths: list[str | Path],
    config: ParserConfig | None = None,
) -> ParseRunResult:
```

**Parameters**

| Parameter | Type | Description |
|---|---|---|
| `paths` | `list[str \| Path]` | Ordered list of source file paths. May mix strings and `Path` objects. |
| `config` | `ParserConfig \| None` | Shared configuration applied to every file in the list. |

**Returns** `ParseRunResult` — always returns a result object. `result.documents` has the same length as `paths` and preserves order. `result.stats` summarizes the run.

**Example**

```python
from pathlib import Path
from structure_parser import parse_files

paths = list(Path("docs/").glob("**/*.md"))
result = parse_files(paths)
print(f"Parsed {result.stats.file_count} files in {result.stats.duration_ms:.0f} ms")
print(f"Errors: {result.stats.error_count}, Warnings: {result.stats.warning_count}")
if not result.success:
    for doc in result.documents:
        if doc.has_errors:
            print(f"  {doc.source_path}: {doc.error_count} error(s)")
```

## run_pipeline()

`run_pipeline()` processes a Markdown content repository and returns a `PipelineRunResult`.

```python
def run_pipeline(config: PipelineConfig) -> PipelineRunResult:
```

**Parameters**

| Parameter | Type | Description |
|---|---|---|
| `config` | `PipelineConfig` | Repository pipeline configuration, including inputs, output directory, include/exclude patterns, dry-run behavior, and parser configuration. |

**Returns** `PipelineRunResult` — always returns a run result with file-level statuses, run diagnostics, and aggregate statistics.

**Side effects** include reading source files and writing parsed JSON outputs unless `dry_run=True`. The function does not write the CSV inventory report; the CLI `pipe` command writes the report after orchestration, and Python callers can use `CsvInventoryReporter` when they need the same report.

**Example**

```python
from pathlib import Path

from structure_parser.contracts.pipeline import PipelineConfig
from structure_parser.pipeline import run_pipeline
from structure_parser.pipeline.reporting import CsvInventoryReporter

config = PipelineConfig(
    inputs=[Path("docs_src")],
    output_dir=Path("build/parsed"),
)

result = run_pipeline(config)
CsvInventoryReporter().write(result, config.effective_report_path())

print(f"Discovered: {result.stats.discovered_count}")
print(f"Parsed: {result.stats.parsed_count}")
print(f"Failed: {result.stats.failed_count}")
```

## PipelineConfig

`PipelineConfig` is the public configuration model for repository-scale Markdown processing.

| Field | Type | Default | Effect |
|---|---|---|---|
| `inputs` | `list[Path]` | required | Source files or folders to process. |
| `output_dir` | `Path` | required | Directory for parsed JSON outputs. |
| `report_path` | `Path \| None` | `None` | CSV report path. Defaults to `output_dir / "pipeline-inventory.csv"`. |
| `include_patterns` | `list[str]` | `["*.md", "*.markdown"]` | File include patterns. |
| `exclude_patterns` | `list[str]` | `[]` | Relative path exclude patterns. |
| `log_file` | `Path \| None` | `None` | Optional log file path for the CLI command. |
| `log_format` | `str` | `"text"` | Log file format: `text` or `jsonl`. |
| `strict` | `bool` | `False` | Treat warnings as failures for CLI exit-code purposes. |
| `dry_run` | `bool` | `False` | Discover files and calculate targets without writing parsed JSON outputs. |
| `parser_config` | `ParserConfig` | default parser config | Parser configuration applied to each source file. |

## PipelineRunResult

`PipelineRunResult` is the operational output of a repository pipeline run.

| Field | Type | Description |
|---|---|---|
| `schema_version` | `str` | Pipeline result contract version. |
| `run_id` | `str` | Unique identifier for one pipeline invocation. |
| `files` | `list[PipelineFileResult]` | One result for each discovered source file. |
| `run_diagnostics` | `list[Diagnostic]` | Run-level pipeline diagnostics, such as missing input or unsafe output overlap. |
| `stats` | `PipelineRunStats` | Aggregate counts and elapsed time. |

`PipelineRunResult` describes repository execution state. It references parser diagnostic codes in file results but does not redefine article, unit, component, attribute, or information-type semantics.

## ParserConfig

A frozen Pydantic model. All fields are keyword-only and all have defaults; you never need to supply all of them.

| Field | Type | Default | Effect |
|---|---|---|---|
| `schema_version` | `str` | `"1"` | Output contract version. Do not change. |
| `source_format` | `SourceFormat \| None` | `None` | Force a specific adapter. `None` = auto-detect by file extension. |
| `enable_structured_markdown` | `bool` | `True` | When `False`, the classifier and enricher are skipped; `structured_content` is `None`. |
| `validation_mode` | `str` | `"advisory"` | `"advisory"` = schema failures are warnings; `"strict"` = schema failures are errors that set `has_errors=True`. |
| `resolve_local_references` | `bool` | `False` | When `True`, relative `href` values are resolved against the source file's parent directory and `Reference.state` is updated. |
| `model_schema_dir` | `Path \| None` | `None` | Override the directory scanned for `.schema.json` files. `None` = the built-in `model/articles/` directory. |
| `emit_debug_logs` | `bool` | `False` | When `True`, the parser emits `debug`-severity diagnostics with internal pipeline detail. |
| `max_diagnostic_count` | `int` | `100` | Maximum number of diagnostics accumulated per document before further diagnostics are dropped. |

Because `ParserConfig` is frozen, you cannot mutate it after construction. Create a new instance to adjust settings:

```python
strict_config = ParserConfig(validation_mode="strict", resolve_local_references=True)
```

## ParsedDocument

The primary output of `parse_file()`. All fields are optional except `source_path` and `source_format`.

| Field | Type | Description |
|---|---|---|
| `schema_version` | `str` | Always `"1"` in this release. |
| `source_path` | `str` | Absolute path to the source file as a string. |
| `source_format` | `SourceFormat` | Detected or configured format: `markdown`, `html5`, or `unknown`. |
| `provenance` | `DocumentProvenance \| None` | Content hash, parse timestamp, and adapter version. |
| `metadata` | `dict[str, Any]` | Front matter fields extracted from the source file. |
| `title` | `str \| None` | Document title extracted from the first H1 heading or front matter. |
| `structure` | `DocumentStructure \| None` | Structural outline of the document (heading tree). |
| `structured_content` | `StructuredContent \| None` | Classified content hierarchy; `None` when `enable_structured_markdown=False`. |
| `references` | `list[Reference]` | All links and images found in the document. |
| `diagnostics` | `list[Diagnostic]` | All parse, classification, validation, and readiness diagnostics. |
| `validation` | `ModelValidationResult \| None` | JSON Schema validation result; `None` when validation was not attempted. |
| `readiness` | `TransformReadiness \| None` | Per-target readiness assessment; `None` when not evaluated. |

**Computed properties**

- `has_errors` — `True` when any diagnostic has `severity == "error"`.
- `error_count` — count of error-severity diagnostics.
- `warning_count` — count of warning-severity diagnostics.

## StructuredContent, Unit, Component, Attribute

These four models represent the classified content hierarchy. A `StructuredContent` contains a list of `Unit` objects; each `Unit` contains a list of `Component` objects; each `Component` may contain a list of `Attribute` or nested `Component` objects.

**StructuredContent** top-level fields of interest:

| Field | Description |
|---|---|
| `article_type` | Classified article type (e.g., `"howto"`, `"concept"`, `"reference"`) |
| `information_type` | Dominant information type across the document |
| `title` | Article title |
| `triage_status` | `"known"`, `"unknown"`, or `"ambiguous"` — reflects classification confidence |
| `content` | Ordered list of `Unit` objects |

**Unit** key fields:

| Field | Description |
|---|---|
| `unit_type` | E.g., `"introduction"`, `"procedure"`, `"concept"`, `"prerequisites"` |
| `title` | Section heading text |
| `information_type` | Information type for this unit |
| `procedure_representation` | For procedure units: `"ordered-list"`, `"code-block"`, `"mixed"`, or `"unknown"` |
| `content` | List of `Component` objects |

**Iterating units and components**

```python
doc = parse_file("guide.md")
if doc.structured_content:
    for unit in doc.structured_content.content:
        print(f"Unit: {unit.unit_type} — {unit.title}")
        for comp in unit.content:
            print(f"  {comp.component_type}: {comp.text or comp.markdown or ''!r:.60}")
```

**Component** carries different fields depending on `component_type`. The fields `markdown`, `html`, and `text` hold the rendered or raw content for most block types. For tables, `row_count`, `column_count`, `row_role`, and `cell_role` are set on the relevant row and cell components. For code blocks, `language` and `code` are set.

**Attribute** represents inline markup within a component: `att_type` distinguishes `attText`, `attBold`, `attItalic`, `attCode`, `attLink`, `attImage`, and so on. The `href` field is set on links; `source` and `alt_text` are set on images.

## Diagnostic

A `Diagnostic` records a single issue found during parsing, classification, validation, or readiness evaluation.

| Field | Type | Description |
|---|---|---|
| `code` | `str` | SP-NNN code, e.g. `"SP-021"` |
| `severity` | `Severity` | `"error"`, `"warning"`, `"info"`, or `"debug"` |
| `category` | `DiagnosticCategory` | E.g., `"structural_warning"`, `"schema_error"`, `"reference_error"` |
| `message` | `str` | Human-readable description |
| `detail` | `str` | Additional context, such as the affected field or value |
| `remediation` | `str` | Suggested fix |
| `source_path` | `str \| None` | File where the issue was found |
| `start_line` | `int \| None` | 1-based line number of the issue |
| `end_line` | `int \| None` | 1-based end line (when the issue spans multiple lines) |

**Filtering by severity**

```python
errors = [d for d in doc.diagnostics if d.severity == "error"]
warnings = [d for d in doc.diagnostics if d.severity == "warning"]
```

## Reference

A `Reference` records every link and image found in the document.

| Field | Type | Description |
|---|---|---|
| `ref_type` | `str` | `"link"` or `"image"` |
| `href` | `str` | The raw `href` or `src` value from the source |
| `text` | `str \| None` | Link text or image alt text |
| `state` | `ResolutionState` | `"not_attempted"`, `"resolved"`, `"unresolved"`, or `"unsupported"` |
| `resolved_path` | `str \| None` | Absolute path when `state == "resolved"` |
| `source_path` | `str \| None` | Source file containing the reference |
| `start_line` | `int \| None` | Line number of the reference in the source |

**Finding unresolved references**

```python
config = ParserConfig(resolve_local_references=True)
doc = parse_file("guide.md", config=config)
broken = [r for r in doc.references if r.state == "unresolved"]
for ref in broken:
    print(f"Line {ref.start_line}: broken link → {ref.href}")
```

## ModelValidationResult

`ModelValidationResult` records the outcome of JSON Schema validation applied to the classified content.

| Field | Type | Description |
|---|---|---|
| `valid` | `bool` | `True` if the document passed schema validation |
| `schema_id` | `str \| None` | Schema filename used, e.g. `"artHowto.schema.json"` |
| `diagnostics` | `list[Diagnostic]` | SP-030 violations, or SP-031/SP-032 for infrastructure failures |
| `source_path` | `str \| None` | Source file path attached for context |

```python
if doc.validation and not doc.validation.valid:
    print(f"Schema: {doc.validation.schema_id}")
    for d in doc.validation.diagnostics:
        print(f"  [{d.code}] {d.detail}")
```

## TransformReadiness and TargetReadiness

`TransformReadiness` holds one `TargetReadiness` entry per evaluated downstream target.

| Field | Type | Description |
|---|---|---|
| `targets` | `list[TargetReadiness]` | One entry per evaluated target |

`TargetReadiness` fields:

| Field | Type | Description |
|---|---|---|
| `target` | `str` | `"dita"`, `"schema-org"`, or `"rag-ingestion"` |
| `status` | `ReadinessStatus` | `"ready"`, `"blocked"`, `"degraded"`, or `"not_evaluated"` |
| `reasons` | `list[str]` | Human-readable explanations for the status |
| `missing` | `list[str]` | Required fields or properties that are absent |

**Checking DITA readiness**

```python
if doc.readiness:
    for target in doc.readiness.targets:
        if target.target == "dita" and target.status == "blocked":
            print("DITA export blocked:")
            for reason in target.reasons:
                print(f"  - {reason}")
```

## Common Patterns

**Parse a file and check for errors**

```python
from structure_parser import parse_file

doc = parse_file("article.md")
if doc.has_errors:
    for d in doc.diagnostics:
        if d.severity == "error":
            print(f"[{d.code}] line {d.start_line}: {d.message}")
```

**Parse multiple files and get statistics**

```python
from pathlib import Path
from structure_parser import parse_files

result = parse_files(list(Path("content/").glob("**/*.md")))
print(f"{result.stats.file_count} files, {result.stats.error_count} errors, "
      f"{result.stats.warning_count} warnings, {result.stats.duration_ms:.0f} ms")
```

**Use strict validation mode**

```python
from structure_parser import parse_file
from structure_parser.contracts.config import ParserConfig

doc = parse_file("article.md", config=ParserConfig(validation_mode="strict"))
assert not doc.has_errors, f"{doc.error_count} schema error(s) found"
```
