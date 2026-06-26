# Inspecting Parse Output

The four `inspect-*` commands and the `--json` flag on `parse` each expose a different layer of the parse pipeline. Use them to understand how the parser classified your content, where structural problems originate, and whether references are healthy — before running validation.

---

## inspect-structure

`inspect-structure` shows the heading tree for a parsed document. Every heading in the source — H1 through H6 — appears in document order, indented to reflect nesting depth.

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
    H3  Basic configuration
    H3  Advanced options
  H2  Next steps
```

Use `inspect-structure` as the first diagnostic step when you suspect heading hierarchy problems. A heading level skip — for example, an H3 appearing directly under an H1 — appears visually as an unexpected indentation jump in this output. The SP-021 diagnostic that follows will name the exact line, but the tree view makes the structure problem immediately legible.

This command is also useful for confirming that the parser sees the article as having a single H1. Multiple H1 headings do not produce an error, but they are unusual and may affect unit classification.

---

## inspect-model

`inspect-model` shows the full `Article → Unit → Component` classification for a parsed document. It is the most informative of the inspection commands for understanding how the parser mapped your content to the authoring model.

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
       components: compHeaderH2, compListUnordered(3 items)
  [2] unit_type=procedure      info_type=procedure    title="Install the package"
       components: compHeaderH2, compParagraph, compBlockCode, compListOrdered(4 items)
  [3] unit_type=procedure      info_type=procedure    title="Configure the agent"
       components: compHeaderH2, compListOrdered(5 items)
  [4] unit_type=link-nextstep  info_type=unknown      title="Next steps"
       components: compHeaderH2, compListUnordered(2 items)
```

Units labeled `[unknown]` indicate sections the parser could not classify. This usually means the section heading does not match any recognized pattern and the content does not conform to a known unit structure. Unknown units degrade DITA and RAG readiness. They are a prompt to inspect the source content and either restructure it or confirm that the unknown classification is acceptable.

Each component entry shows the `ComponentType` — `compParagraph`, `compListOrdered`, `compBlockCode`, and so on. Use this to verify that a procedure you intended to write as an ordered list was actually classified as `compListOrdered` rather than `compListUnordered`.

---

## inspect-references

`inspect-references` lists every link and image reference in the document with its href and resolution state.

```bash
structure-parser inspect-references docs/deploy-agent.md
```

Output:

```
References: docs/deploy-agent.md

  [link]  ./prerequisites.md                not_attempted
  [link]  ./configure.md                    not_attempted
  [link]  https://pypi.org/project/sp/      not_attempted
  [image] ./images/architecture.png         not_attempted
```

By default, `resolve_local_references` is `False` in `ParserConfig`, so all references appear as `not_attempted`. To check local file existence, enable resolution:

```python
from structure_parser import parse_file
from structure_parser.contracts.config import ParserConfig

config = ParserConfig(resolve_local_references=True)
doc = parse_file("docs/deploy-agent.md", config=config)

broken = [r for r in doc.references if r.resolution_state.value == "unresolved"]
for ref in broken:
    print(f"Broken: {ref.href}")
```

With resolution enabled, files that do not exist on disk appear as `unresolved` and produce SP-050 diagnostics. Remote URLs (`https://`) and unsupported schemes (`mailto:`) appear as `unsupported` and do not produce diagnostics.

Use `inspect-references` when you are preparing a document for publishing and want to audit link health before committing.

---

## inspect-diagnostics

`inspect-diagnostics` shows all SP-NNN diagnostics for a parsed document, grouped by severity in descending order: errors first, then warnings, then info. This is the most actionable command for authors during drafting.

```bash
structure-parser inspect-diagnostics docs/draft-article.md
```

Output:

```
Diagnostics for docs/draft-article.md

WARNINGS (3)
  SP-041  Article type could not be determined
          Remediation: Add articleType metadata or conform to a known article pattern.
  SP-020  Missing document title (H1)
          Remediation: Add an H1 heading as the first content element.
  SP-021  Heading level skipped: 1 to 3  [line 14]
          Remediation: Do not skip heading levels.

INFO (1)
  SP-011  Front matter absent
          Remediation: Add a YAML front matter block with at least a title field.
```

Read the output from top to bottom and address items in that order. Fixing SP-011 (add front matter) and SP-020 (add H1) often resolves SP-041 (unknown article type) as a downstream consequence, because the parser uses `articleType` from front matter and the H1 to classify the article.

Use `inspect-diagnostics` immediately after making structural changes to confirm that each fix removes its corresponding diagnostic.

---

## --json Flag on parse

The `--json` flag on the `parse` command emits the complete `ParsedDocument` as a JSON object. It includes every field: `source_path`, `source_format`, `metadata`, `title`, `structure`, `structured_content`, `references`, `diagnostics`, and `readiness`.

```bash
structure-parser parse docs/deploy-agent.md --json
```

The JSON output is the raw contract. Use it to:

- Pipe to `jq` for targeted field extraction:

    ```bash
    structure-parser parse docs/deploy-agent.md --json \
      | jq '[.diagnostics[] | {code, severity, message}]'
    ```

- Inspect the raw unit and component classification, including all `triage_status` and `procedure_representation` values that the human-readable commands abbreviate.

- Write post-processing scripts that consume `ParsedDocument` without going through the Python API.

- Capture a snapshot of the parse output for debugging a regression — save the JSON and compare it to the output after a code change.

The JSON schema version is `"1"` and is stable within the current release. The `schema_version` field in the top-level object and in `structured_content` reflects this.
