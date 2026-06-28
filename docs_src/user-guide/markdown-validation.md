# Validating Markdown

Validation compares the `StructuredContent` produced by the parse pipeline against a JSON schema that encodes the structural rules for a particular article type. The schemas live in `model/articles/` and ship with the package, so no external setup is required.

---

## What Validation Checks

The parser produces a `StructuredContent` object — a hierarchy of article, units, and components — from the Markdown source. Validation takes that hierarchy and checks it against the constraints declared in a schema file: which unit types are required, which are forbidden, how many of each may appear, and what metadata fields must be present. The result is a set of SP-030 diagnostics (one per violation) attached to the parsed document.

Validation does not re-read the source file. It operates entirely on the already-parsed model, which means the same document can be validated against multiple schemas without re-parsing.

---

## Advisory vs. Strict Mode

`structure_parser` runs in advisory mode by default. In advisory mode, schema violations produce SP-030 warnings, but the command exits with code 0. The document is still parsed and fully usable — validation findings are informational.

In strict mode (`--strict`), any SP-030 warning causes the command to exit with code 1. Use strict mode in CI gates where a violation must block the pipeline. Use advisory mode during authoring, where you want to see the full diagnostic picture without stopping a script.

The mode is controlled by the `--strict` flag on `validate-markdown` or by setting `validation_mode = "strict"` in a `ParserConfig`:

```python
from structure_parser import parse_file
from structure_parser.contracts.config import ParserConfig

config = ParserConfig(validation_mode="strict")
doc = parse_file("my-article.md", config=config)
```

---

## Available Schemas

Each schema targets a specific article type. Choose the schema that matches what the author intended to write.

| Schema | Use when... |
|--------|-------------|
| `artArticle.schema.json` | You want to accept any valid article type. This is the default and the most permissive. |
| `artTopic.schema.json` | The article is a general-purpose topic that does not conform to a more specific type. |
| `artConcept.schema.json` | The article explains a concept — background knowledge that a reader needs before taking action. |
| `artHowto.schema.json` | The article provides a procedure for accomplishing a specific goal. Requires a procedure unit. |
| `artReference.schema.json` | The article provides lookup content — parameters, options, API signatures — intended for scanning rather than reading. |
| `artTroubleshooting.schema.json` | The article diagnoses and resolves a known problem. Requires symptom and resolution structure. |
| `artGlossary.schema.json` | The article is a collection of glossary entries. |
| `artGlossentry.schema.json` | The article defines a single glossary term. |
| `artOverview.schema.json` | The article introduces a product, feature, or concept area at a high level. |
| `artQuickstart.schema.json` | The article provides the shortest possible path to a working result. |
| `artTutorial.schema.json` | The article teaches a concept or skill through a guided, multi-step exercise. |

When you are not sure which schema to use, start with `artArticle.schema.json` to get a pass/fail result for the loosest possible constraints, then move to the specific schema for the target article type.

---

## Validating a File: Step by Step

**1. Write the article.** Here is a minimal howto that passes `artHowto.schema.json`:

````markdown
---
articleType: howto
title: Install the CLI
description: How to install the structure-parser CLI on macOS and Linux.
---

# Install the CLI

## Prerequisites

- Python 3.11 or later
- `pip` available in your shell

## Install the package

Run the following command to install the package from PyPI:

```bash
pip install structure-parser
```

Verify the installation:

```bash
structure-parser --help
```

## Next steps

- Configure the parser
- Validate your first article
````

**2. Run validation:**

```bash
structure-parser validate-markdown install-cli.md --schema artHowto.schema.json
```

Output for the article above:

```
PASS  install-cli.md

Summary: 1 file, 0 warnings, 0 errors
```

**3. Run in strict mode to confirm CI compatibility:**

```bash
structure-parser validate-markdown install-cli.md --schema artHowto.schema.json --strict
```

A `PASS` with exit code 0 confirms the article will pass the same check in CI.

---

## Reading Validation Output

The `validate-markdown` command groups its output by file. Each file entry shows `PASS` or `FAIL`, followed by the list of diagnostics. Each diagnostic line includes the code, severity, the message, and the remediation.

```
FAIL  docs/overview.md
  [SP-041] warning  Article type could not be determined
                    Remediation: Add articleType metadata or conform to a known article pattern.
  [SP-030] warning  Schema validation failed: required unit type 'unitProcedure' is missing
                    Remediation: Review the authoring model and fix reported violations.
```

The SP-030 `detail` field names the specific constraint that failed. In the example above, `artHowto.schema.json` requires at least one `unitProcedure`, and none was found. That maps directly to the "Install the package" section needing to use an ordered list (which the parser recognizes as a procedure).

---

## Common Validation Failures and Fixes

**SP-041 — Article type not determined**

The parser could not determine the article type from recognized metadata or from the content structure.

Fix: Add `articleType: howto` (or the appropriate type) to the YAML front matter block, or revise the H2 sections so their unit types match a known article pattern.

```yaml
---
articleType: howto
title: My Article
---
```

**SP-030 — Schema constraint violated**

A required structural element is missing or a forbidden element is present. The detail field names the violated constraint. For `artHowto.schema.json`, the most common cause is the absence of a `unitProcedure` — the parser requires at least one ordered list in the article body to classify a procedure unit.

Fix: Add an ordered list under an H2 section. The parser maps ordered lists to `unitProcedure` with `procedureRepresentation = ordered-list`.

**SP-020 — No H1 heading**

The article body contains no H1 heading. The parser cannot extract a document title, which blocks multiple downstream operations.

Fix: Add an H1 as the first content element after the front matter block.

```markdown
---
articleType: howto
---

# Install the CLI
```

**SP-021 — Heading level skipped**

A heading jumps from H1 to H3 (or from H2 to H4, and so on) without the intermediate level. The parser records the skip and emits SP-021 with the source line.

Fix: Insert the missing heading level, or change the deeper heading to the correct level. For example, if you have `## Section` followed by `#### Subsection`, change the subsection to `### Subsection`.
