# Transform Readiness

Transform readiness is an assessment of whether a parsed document satisfies the prerequisites for a given output transformation target. The assessment does not perform the transformation — it reports which conditions are met, which are missing, and whether the target can proceed at all.

---

## Readiness Statuses

Every target produces one of four statuses:

| Status | Meaning |
|--------|---------|
| `ready` | All prerequisites are satisfied. The transformation can proceed. |
| `degraded` | Required prerequisites are met, but optional prerequisites are missing. The transformation can proceed, but output quality may be reduced. |
| `blocked` | One or more required prerequisites are not met. The transformation cannot proceed without remediation. |
| `not_evaluated` | The target was not evaluated for this document (for example, because a parse error occurred first). |

A `degraded` status means the output is producible but imperfect. A `blocked` status means the transformation cannot run at all until the missing prerequisites are addressed.

---

## DITA Readiness

DITA readiness checks three prerequisites for DITA transformation.

**Required prerequisites (block if missing):**

- **Title present.** The document must have an H1 heading or a `title` field in front matter. A missing title produces SP-020 and blocks DITA readiness.
- **Article type known.** The `article_type` must not be `unknown`. An unknown article type produces SP-041 and blocks DITA readiness because the DITA type mapping — which determines whether the output is a `<concept>`, `<task>`, `<reference>`, or `<topic>` — depends on it.
- **DITA type mapped.** The article type must have a valid entry in the DITA type mapping table. All named article types (`howto`, `concept`, `reference`, `troubleshooting`, `glossary`, `glossentry`, `overview`, `quickstart`, `tutorial`, `topic`) have a defined mapping. Only `unknown` lacks one.

**Degrading conditions:**

- Some units are classified as `unknown`. The DITA transform can still generate output for the article, but unknown units will be wrapped in a generic container rather than a semantic DITA element.

A `howto` article maps to a DITA `<task>` topic. A `concept` maps to `<concept>`. A `reference` maps to `<reference>`. A `troubleshooting` maps to `<troubleshooting>`.

---

## Schema.org Readiness

Schema.org readiness checks whether the document has enough metadata to generate meaningful Schema.org markup. This target never blocks — the Schema.org transform can always produce partial output.

**Prerequisites that degrade if missing:**

- **Title present.** A missing title degrades Schema.org output because the `name` property cannot be populated from structure.
- **Description metadata present.** A missing `description` in front matter degrades output because the `description` property is omitted from the markup.

Both missing title and missing description are non-blocking. The Schema.org transform can generate markup with whatever metadata is available, but the output will be incomplete and less useful for search indexing.

---

## RAG Ingestion Readiness

RAG ingestion readiness checks whether the document is suitable for chunking and embedding in a retrieval-augmented generation pipeline.

**Required prerequisites (block if missing):**

- **Title present.** A missing title (SP-020) blocks RAG ingestion because the chunk metadata cannot be labeled.
- **No parse errors.** Any SP-001, SP-002, or SP-003 diagnostic blocks RAG ingestion because the parse output is incomplete or unreliable.

**Degrading conditions:**

- **Units are unclassified.** When some units have `unit_type = "unknown"`, chunk boundaries are less semantically reliable. The document can still be ingested, but unclassified chunks will have weaker retrieval signals.

A document with a title, no parse errors, and fully classified units is `ready` for RAG ingestion. A document with unclassified units is `degraded` but still ingestible.

---

## Using the transform-readiness Command

Evaluate all three targets at once by omitting `--target`:

```bash
structure-parser transform-readiness docs/deploy-agent.md
```

Output for a well-formed article:

```
Transform readiness: docs/deploy-agent.md

dita
  status: ready
  prerequisites met:
    - title present (Deploy the Agent)
    - article type known (howto)
    - dita type mapped (task)

schema-org
  status: degraded
  prerequisites met:
    - title present
  prerequisites missing:
    - description metadata absent (non-blocking)

rag-ingestion
  status: ready
  prerequisites met:
    - title present
    - no parse errors
    - all units classified (4 units)
```

Output for a poorly-formed article (missing front matter and H1):

```
Transform readiness: docs/draft-notes.md

dita
  status: blocked
  prerequisites met:    (none)
  prerequisites missing:
    - title absent (SP-020)
    - article type unknown (SP-041)

schema-org
  status: degraded
  prerequisites met:    (none)
  prerequisites missing:
    - title absent (non-blocking for schema-org)
    - description absent (non-blocking for schema-org)

rag-ingestion
  status: blocked
  prerequisites met:    (none)
  prerequisites missing:
    - title absent (SP-020)
```

Evaluate a single target when you only care about one pipeline:

```bash
structure-parser transform-readiness docs/deploy-agent.md --target rag-ingestion
```

---

## Using Readiness in Python

The `ParsedDocument.readiness` field holds a `TransformReadiness` object with a `targets` list. Each entry is a `TargetReadiness` with `target`, `status`, `prerequisites_met`, and `prerequisites_missing` fields.

```python
from structure_parser import parse_file
from structure_parser.domain.enums import ReadinessStatus

doc = parse_file("docs/deploy-agent.md")

if doc.readiness:
    for target in doc.readiness.targets:
        print(f"{target.target}: {target.status.value}")
        if target.status == ReadinessStatus.blocked:
            for missing in target.prerequisites_missing:
                print(f"  MISSING: {missing}")
```

Filter across a corpus by target and status:

```python
from structure_parser import parse_files
from structure_parser.domain.enums import ReadinessStatus

result = parse_files(all_paths)

dita_ready = [
    doc for doc in result.documents
    if doc.readiness and any(
        t.target == "dita" and t.status == ReadinessStatus.ready
        for t in doc.readiness.targets
    )
]
```

---

## Fixing Common Readiness Blocks

**Missing title (SP-020) — blocks DITA and RAG ingestion**

Add an H1 heading as the first content element in the article body. Alternatively, add `title:` to the front matter block. The parser uses front matter `title` as a fallback when no H1 is present.

```markdown
---
title: Deploy the Agent
articleType: howto
---

# Deploy the Agent
```

**Unknown article type (SP-041) — blocks DITA**

Add `articleType` to the front matter, or revise the H2 sections so the parser can infer a known article type from the unit population. Choose the type or section pattern that matches the article's purpose.

```yaml
---
articleType: howto
---
```

**Parse errors (SP-001, SP-002, SP-003) — block RAG ingestion**

Resolve the underlying parse error first. SP-001 means the file path is wrong or the file does not exist. SP-002 means the file format is not supported. SP-003 means the file content is not valid Markdown or HTML. Fix the source issue and re-run.
