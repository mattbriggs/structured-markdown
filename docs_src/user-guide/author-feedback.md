# Author Feedback

Every issue the parser detects is represented as a `Diagnostic` — a structured record with a code, severity, category, message, detail, remediation, and optional source location. The diagnostic model is the primary interface between the parse pipeline and the author.

---

## The Diagnostic Model

A `Diagnostic` carries seven fields that together describe the issue and tell the author what to do about it:

| Field | Type | Description |
|-------|------|-------------|
| `code` | `str` | The SP-NNN identifier. Stable across releases. |
| `severity` | `Severity` | `error`, `warning`, `info`, or `debug`. |
| `category` | `DiagnosticCategory` | The pipeline stage that produced the diagnostic. |
| `message` | `str` | A human-readable description of the issue. |
| `detail` | `str` | Specific detail, such as the offending href or the violated constraint. |
| `remediation` | `str` | The action the author should take to resolve the issue. |
| `start_line` | `int \| None` | The source line where the issue begins, when available. |
| `end_line` | `int \| None` | The source line where the issue ends, when available. |

Not every diagnostic carries a source location. Issues detected at the whole-document level — such as a missing H1 or absent front matter — do not have line numbers. Issues detected at the element level — such as a heading level skip or an unresolved reference — include `start_line` when the parser could determine it.

---

## Severity Levels

Severity tells the author how urgent the issue is and what action is expected.

**error** — the parse failed or a required resource is missing. An error means the document could not be fully processed. Files with errors should not proceed through the publishing pipeline. Common error codes: SP-001 (file not found), SP-002 (unsupported format), SP-003 (parse failed), SP-031 (schema not found).

**warning** — a structural or authoring violation that will likely block publishing or degrade output quality. Warnings do not prevent parsing, but they indicate a problem the author should address before the article reaches a CI gate or a downstream transformation. Common warning codes: SP-010 (malformed front matter), SP-020 (missing H1), SP-021 (heading level skipped), SP-030 (schema constraint violated), SP-041 (unknown article type), SP-050 (unresolved reference).

**info** — an observation about the content that may indicate a gap, but does not constitute a violation. Info diagnostics are advisory. The author should review them, but they do not require action in all cases. Common info codes: SP-011 (front matter absent), SP-040 (content classified as unknown), SP-060 (transform readiness status).

**debug** — internal pipeline detail generated during parse execution. Debug diagnostics are visible only when `--debug` is passed on the CLI or `emit_debug_logs = True` is set in `ParserConfig`. Authors do not need to act on debug diagnostics.

---

## Reading inspect-diagnostics Output

`inspect-diagnostics` groups all diagnostics for a file by severity, with errors at the top and info at the bottom. Each entry shows the code, the message, the source line (when available), and the remediation.

```bash
structure-parser inspect-diagnostics docs/configure-agent.md
```

Output:

```
Diagnostics for docs/configure-agent.md

WARNINGS (3)
  SP-020  Missing document title (H1)
          Remediation: Add an H1 heading as the first content element.
  SP-021  Heading level skipped: 1 to 3  [line 12]
          Remediation: Do not skip heading levels.
  SP-041  Article type could not be determined
          Remediation: Add articleType metadata or conform to a known article pattern.

INFO (1)
  SP-011  Front matter absent
          Remediation: Add a YAML front matter block with at least a title field.
```

Read from top to bottom. Fix errors first, then warnings. Info items are last and may require judgment — SP-011 (front matter absent) is an info diagnostic because the parser can still extract a title from an H1, but adding front matter is strongly recommended for structured publishing pipelines.

---

## Common Diagnostic Codes for Authors

**SP-011 — Front matter absent**

Message: `Front matter absent`
Remediation: Add a YAML front matter block with at least a `title` field.

The article has no YAML front matter block. The parser can still parse the article and can still infer article type from construction evidence, but metadata-dependent features such as description extraction and explicit article-type declaration will be limited. Add a front matter block at the top of the file:

```yaml
---
articleType: howto
title: My Article Title
description: One-sentence summary.
---
```

**SP-020 — Missing H1**

Message: `Missing document title (H1)`
Remediation: Add an H1 heading as the first content element.

The article body has no H1 heading. The parser cannot extract a document title from the structure. This blocks DITA and RAG readiness. The H1 should be the first element after the front matter.

**SP-021 — Heading level skipped**

Message: `Heading level skipped: 1 to 3`
Remediation: Do not skip heading levels.

A heading jumps from one level to a non-consecutive deeper level — for example, from H1 directly to H3. The source line is reported when available. Fix by inserting the missing intermediate heading or by changing the deeper heading to the correct level.

**SP-041 — Article type unknown**

Message: `Article type could not be determined`
Remediation: Add `articleType` metadata or conform to a known article pattern.

The parser could not determine the article type from metadata or from the content structure. This blocks DITA transformation and schema validation against type-specific schemas. Add `articleType: howto` (or the appropriate type) to the front matter, or revise the H2 sections so they match a known article pattern.

**SP-030 — Schema constraint violated**

Message: `Schema validation failed: <detail>`
Remediation: Review the authoring model and fix reported violations.

The parsed `StructuredContent` does not satisfy a constraint in the target schema. The `detail` field names the specific constraint — for example, `required unit type 'unitProcedure' is missing`. Check the schema documentation for the required structural elements.

**SP-050 — Unresolved reference**

Message: `Unresolved reference: ./install.md`
Remediation: Fix or remove the broken link or image reference.

A link or image href could not be resolved. This diagnostic is only produced when `resolve_local_references = True` in the `ParserConfig` — by default, local references are not checked. Enable resolution when auditing link health before publishing.

---

## Using Diagnostics in CI

Exit codes tell automated systems how to respond to parse output. In advisory mode (the default), the command exits 0 even when warnings are present. In strict mode (`--strict`), any warning produces exit code 1, which blocks a CI merge gate.

| Mode | Exit 0 | Exit 1 |
|------|--------|--------|
| Advisory | No errors (warnings allowed) | Errors only |
| Strict | No errors and no warnings | Any error or warning |

Design your CI gate around the mode that fits your content policy. A documentation team that enforces all authoring rules uses strict mode. A team that is still migrating content to a structured model may prefer advisory mode during the transition.

---

## Accessing Diagnostics in Python

Every `ParsedDocument` carries a `diagnostics` list. Filter it by severity to build custom gates or reports:

```python
from structure_parser import parse_file
from structure_parser.domain.enums import Severity

doc = parse_file("my-article.md")

errors   = [d for d in doc.diagnostics if d.severity == Severity.error]
warnings = [d for d in doc.diagnostics if d.severity == Severity.warning]

if errors:
    print(f"Parse failed: {errors[0].message}")
elif warnings:
    print(f"{len(warnings)} warning(s); review before publishing")
else:
    print("Clean — no diagnostics")
```

The `DiagnosticFactory` class produces `Diagnostic` instances with correct severity, category, and remediation text for each SP-NNN code. Developers building extensions or post-processors should use `DiagnosticFactory` rather than constructing `Diagnostic` objects directly, to ensure all fields are populated from the canonical code definitions.
