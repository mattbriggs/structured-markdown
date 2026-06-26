# CLI Reference

The `structure-parser` CLI exposes commands for parsing, validating, and inspecting Markdown and HTML documents from the terminal. The entry point is the `structure-parser` executable installed by `pip install structure-parser`.

**Global flag:** `--debug` is available on every command. It enables verbose structured logging to stderr, including pipeline stage timing, classifier decisions, and schema resolution paths. Use it when a parse result is unexpected and you need to trace the cause.

**Exit codes:**

| Code | Meaning |
|------|---------|
| 0    | No errors. Warnings are present only if not in strict mode. |
| 1    | Parse errors, or validation violations in strict mode. |
| 2    | Unsupported schema version or configuration error. |
| 3    | Internal controlled failure. |

---

## parse

`parse` reads one or more Markdown or HTML files, runs the full parse pipeline, and prints a summary of the results. It is the entry point for confirming that a file is parseable and inspecting top-level metadata.

**Syntax:**

```
structure-parser parse PATH... [--json] [--debug]
```

**Flags:**

| Flag | Effect |
|------|--------|
| `--json` | Emit the full `ParsedDocument` as JSON instead of the human-readable summary. |
| `--debug` | Enable debug logging. |

**Example:**

```bash
structure-parser parse docs/deploy-agent.md
```

Output:

```
docs/deploy-agent.md
  format       : markdown
  title        : Deploy the Agent
  article_type : howto
  units        : 4
  diagnostics  : 1 warning, 0 errors
```

**JSON output:**

```bash
structure-parser parse docs/deploy-agent.md --json
```

The `--json` flag emits the complete `ParsedDocument` contract, including `structured_content`, `references`, `diagnostics`, and `readiness`. This output is suitable for piping to `jq` or loading in downstream scripts:

```bash
structure-parser parse docs/deploy-agent.md --json | jq '.diagnostics[].code'
```

---

## validate-markdown

`validate-markdown` parses each file and compares the resulting `StructuredContent` against a JSON schema from the bundled authoring model. It reports pass or fail for each file with the diagnostics that caused failures.

**Syntax:**

```
structure-parser validate-markdown PATH... [--schema ID] [--strict] [--debug]
```

**Flags:**

| Flag | Effect |
|------|--------|
| `--schema ID` | Schema file name to validate against. Defaults to `artArticle.schema.json`. |
| `--strict` | Exit with code 1 on any warning, not just errors. |
| `--debug` | Enable debug logging. |

**Example — advisory mode (default):**

```bash
structure-parser validate-markdown docs/deploy-agent.md --schema artHowto.schema.json
```

Output:

```
PASS  docs/deploy-agent.md

Summary: 1 file, 0 warnings, 0 errors
```

**Example — strict mode with failures:**

```bash
structure-parser validate-markdown docs/**/*.md --schema artHowto.schema.json --strict
```

Output:

```
PASS  docs/deploy-agent.md
FAIL  docs/overview.md
  [SP-041] warning  Article type could not be determined
                    Remediation: Add articleType metadata or conform to a known article pattern.
  [SP-030] warning  Schema validation failed: required unit type 'unitProcedure' is missing
                    Remediation: Review the authoring model and fix reported violations.
FAIL  docs/intro.md
  [SP-020] warning  Missing document title (H1)
                    Remediation: Add an H1 heading as the first content element.

Summary: 3 files, 3 warnings, 0 errors
Exit code: 1 (strict mode — warnings treated as errors)
```

In advisory mode, warnings are reported but exit code 0 is returned. In strict mode, any warning produces exit code 1. Use strict mode in CI gates; use advisory mode for local authoring checks.

---

## inspect-structure

`inspect-structure` displays the heading tree of a parsed document. It shows every heading (H1 through H6) in document order, indented to reflect nesting depth. This command is the fastest way to confirm heading level consistency before running validation.

**Syntax:**

```
structure-parser inspect-structure PATH [--debug]
```

**Example:**

```bash
structure-parser inspect-structure docs/deploy-agent.md
```

Output:

```
Heading structure: docs/deploy-agent.md

H1  Deploy the Agent
  H2  Prerequisites
  H2  Install the package
    H3  Verify the installation
  H2  Configure the agent
  H2  Next steps
```

A heading level skip — for example, an H3 appearing directly under an H1 — appears visually as an unexpected indentation jump. The SP-021 diagnostic that follows identifies the exact line. Use `inspect-structure` before `validate-markdown` to catch heading hierarchy problems quickly.

---

## inspect-model

`inspect-model` displays the full `Article → Unit → Component` classification for a parsed document. It shows the article type, DITA type, triage status, and for each unit, its `unit_type`, `information_type`, and title. Unknown types are labeled `[unknown]`.

**Syntax:**

```
structure-parser inspect-model PATH [--debug]
```

**Example:**

```bash
structure-parser inspect-model docs/deploy-agent.md
```

Output:

```
Article: docs/deploy-agent.md
  article_type : howto
  dita_type    : task
  title        : Deploy the Agent
  triage_status: known

Units:
  [1] unit_type=prerequisites  info_type=fact         title="Prerequisites"
  [2] unit_type=procedure      info_type=procedure    title="Install the package"
       components: compHeaderH2, compListOrdered(5 items), compParagraph
  [3] unit_type=procedure      info_type=procedure    title="Configure the agent"
       components: compHeaderH2, compListOrdered(3 items), compBlockCode
  [4] unit_type=link-nextstep  info_type=unknown      title="Next steps"
       components: compHeaderH2, compListUnordered(2 items)
```

Use this command to understand how the parser classified your content, to verify that a procedure was recognized as `unit_type=procedure`, and to identify units labeled `[unknown]` that may need structural correction.

---

## inspect-references

`inspect-references` lists every link and image reference found in a parsed document, along with the href and its resolution state.

**Syntax:**

```
structure-parser inspect-references PATH [--debug]
```

**Resolution states:**

| State | Meaning |
|-------|---------|
| `not_attempted` | Local reference resolution is disabled (default). |
| `resolved` | The referenced file exists and was confirmed readable. |
| `unresolved` | The referenced file could not be found. |
| `unsupported` | The href scheme is not supported for resolution (e.g., `mailto:`). |

**Example:**

```bash
structure-parser inspect-references docs/deploy-agent.md
```

Output:

```
References: docs/deploy-agent.md

  [link]  ./install.md                      not_attempted
  [link]  ./configure.md                    not_attempted
  [link]  https://example.com/docs          not_attempted
  [image] ./images/architecture-diagram.png not_attempted
```

To resolve local `./` references, enable `resolve_local_references` in a `ParserConfig` or run the parser with a config that sets it to `True`. When local resolution is enabled, files that do not exist on disk appear as `unresolved` and produce SP-050 diagnostics.

---

## inspect-diagnostics

`inspect-diagnostics` displays all diagnostics for a parsed document, grouped by severity in descending order: errors first, then warnings, then info, then debug. Each entry shows the SP-NNN code, the message, an optional source line, and the remediation text.

**Syntax:**

```
structure-parser inspect-diagnostics PATH [--debug]
```

**Example:**

```bash
structure-parser inspect-diagnostics docs/overview.md
```

Output:

```
Diagnostics for docs/overview.md

WARNINGS (2)
  SP-041  Article type could not be determined
          Remediation: Add articleType metadata or conform to a known article pattern.
  SP-021  Heading level skipped: 1 to 3  [line 18]
          Remediation: Do not skip heading levels.

INFO (1)
  SP-011  Front matter absent
          Remediation: Add a YAML front matter block with at least a title field.
```

This is the most actionable command for authors during drafting. It surfaces all issues in a single view, ordered so the most severe problems appear first. Each remediation message explains exactly what to change.

---

## transform-readiness

`transform-readiness` evaluates whether a parsed document satisfies the prerequisites for one or more output transformation targets. It reports a status of `ready`, `degraded`, or `blocked` for each target, listing which prerequisites are met and which are missing.

**Syntax:**

```
structure-parser transform-readiness PATH [--target TARGET] [--debug]
```

The `--target` flag is repeatable. Supported values are `dita`, `schema-org`, and `rag-ingestion`. When no `--target` is specified, all three targets are evaluated.

**Example — single target:**

```bash
structure-parser transform-readiness docs/deploy-agent.md --target dita
```

Output:

```
Transform readiness: docs/deploy-agent.md

dita
  status: ready
  prerequisites met:
    - title present
    - article type known (howto)
    - dita type mapped (task)
```

**Example — all targets:**

```bash
structure-parser transform-readiness docs/overview.md
```

Output:

```
Transform readiness: docs/overview.md

dita
  status: blocked
  prerequisites met:
    - title present
  prerequisites missing:
    - article type unknown (SP-041)

schema-org
  status: degraded
  prerequisites met:
    - title present
  prerequisites missing:
    - description metadata absent (non-blocking)

rag-ingestion
  status: degraded
  prerequisites met:
    - title present
    - no parse errors
  prerequisites missing:
    - 3 of 4 units are unclassified (chunking boundaries unreliable)
```

---

## validate-contract

`validate-contract` runs fixture files against the expected contract behavior defined in the test suite. It is primarily a developer tool for verifying that a fixture produces the expected parse output after a code change.

**Syntax:**

```
structure-parser validate-contract PATH... [--debug]
```

**Example:**

```bash
structure-parser validate-contract tests/fixtures/howto-basic.md
```

Output:

```
PASS  tests/fixtures/howto-basic.md
  contract: artHowto.schema.json
  expected: valid
  actual  : valid

Summary: 1 fixture, 1 passed, 0 failed
```

Fixture files declare their expected behavior through front matter annotations that the contract validator reads. When an actual parse result diverges from the expected contract, the command reports the mismatch and exits with code 1.
