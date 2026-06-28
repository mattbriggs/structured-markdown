# Use Cases

`structure_parser` is a general-purpose library and CLI for parsing, classifying, and validating structured Markdown. The four use cases below cover its most common applications — from blocking bad content at the CI gate to preprocessing documentation for AI pipelines.

---

## CI/CD Content Quality Gate

A documentation engineering team maintains a large Markdown repository and publishes content through an automated pipeline. Authors submit pull requests, and the pipeline converts approved Markdown to HTML for delivery. The team uses the howto article pattern across all procedural content — a pattern that requires a title, a prerequisites section, and at least one ordered procedure.

The problem is consistency. Individual authors skip heading levels, omit explicit `articleType` declarations, or submit articles whose structure matches nothing the authoring model recognizes. These errors surface only after publishing, when fixing them requires a second PR and a second review cycle.

`structure_parser` addresses this by running `validate-markdown` as a required CI step. When a file violates the `artHowto.schema.json` schema in strict mode, the command exits with code 1, blocking the PR from merging. Authors read the diagnostic output directly in the CI log and fix the violations before re-pushing.

**Procedure:**

1. Install the package in the CI environment:

    ```bash
    pip install structure-parser
    ```

2. Add a CI step to your pipeline configuration (GitHub Actions example):

    ```yaml
    - name: Validate structured Markdown
      run: |
        structure-parser validate-markdown docs/**/*.md \
          --schema artHowto.schema.json \
          --strict
    ```

3. When a file fails validation, the command exits with code 1 and prints a diagnostic report. A typical failure looks like this:

    ```
    FAIL  docs/procedures/deploy-service.md
      [SP-041] warning  Article type could not be determined
                        Remediation: Add articleType metadata or conform to a known article pattern.
      [SP-030] warning  Schema validation failed: required unit type 'unitProcedure' is missing
                        Remediation: Review the authoring model and fix reported violations.
      [SP-020] warning  Missing document title (H1)
                        Remediation: Add an H1 heading as the first content element.

    Summary: 1 file, 3 warnings, 0 errors
    Exit code: 1 (strict mode)
    ```

4. Authors read the diagnostic codes, fix the violations in their branch, and push again. SP-041 tells the author to add `articleType: howto` or restructure the H2 sections so the article matches a known pattern. SP-030 identifies a missing procedure unit. SP-020 identifies an absent H1.

5. After fixing all violations, the CI step passes and exits with code 0.

This pattern makes content standards machine-enforceable without requiring reviewers to manually inspect structure.

---

## RAG Ingestion Preprocessing

A machine learning engineer is building a retrieval-augmented generation pipeline over a corpus of technical documentation. The pipeline embeds each chunk, stores it in a vector database, and uses the stored chunks to answer developer questions. The quality of retrieval depends directly on the quality of chunk boundaries and the accuracy of chunk labels.

The problem is that raw Markdown files carry no semantic structure. A naive chunker splits on token count or paragraph breaks, producing chunks that mix conceptual explanation with procedural steps — a mix that confuses both the embedding model and the retriever. What the engineer needs is a chunker that splits on semantic unit boundaries and labels each chunk by its information type.

`structure_parser` solves this by parsing each file into an `Article → Unit → Component` hierarchy. Each `Unit` corresponds to a semantically coherent section of the article — a concept, a procedure, a reference table, a set of prerequisites — and carries a `unit_type` and `information_type` label. The engineer uses those units as pre-computed chunk boundaries.

**Procedure:**

1. Parse all documentation files in a single call:

    ```python
    import glob
    from structure_parser import parse_files

    paths = glob.glob("docs/**/*.md", recursive=True)
    result = parse_files(paths)
    ```

2. Filter for files that are ready for RAG ingestion. A document is ready when it has a title, at least one classified unit, and no parse errors:

    ```python
    from structure_parser.domain.enums import ReadinessStatus

    rag_ready = [
        doc for doc in result.documents
        if doc.readiness is not None
        and any(
            t.target == "rag-ingestion" and t.status == ReadinessStatus.ready
            for t in doc.readiness.targets
        )
    ]
    ```

3. Extract units as chunks. Each unit in `doc.structured_content.content` is a semantically bounded section:

    ```python
    chunks = []
    for doc in rag_ready:
        if doc.structured_content is None:
            continue
        for unit in doc.structured_content.content:
            chunks.append({
                "source": doc.source_path,
                "article_type": doc.structured_content.article_type.value,
                "unit_type": unit.unit_type.value,
                "information_type": unit.information_type.value,
                "title": unit.title,
                "content": [c.text for c in unit.content if c.text],
            })
    ```

4. Use `unit.unit_type` and `unit.information_type` to label chunks for metadata filtering. A unit with `unit_type = "procedure"` and `information_type = "procedure"` is a strong candidate for step-by-step instruction retrieval. A unit with `unit_type = "concept"` suits background context retrieval.

5. Full preprocessing loop with degraded-document handling:

    ```python
    from structure_parser.domain.enums import ReadinessStatus, Severity

    for doc in result.documents:
        if doc.has_errors:
            print(f"SKIP {doc.source_path}: parse errors")
            continue

        target_statuses = {
            t.target: t.status
            for t in (doc.readiness.targets if doc.readiness else [])
        }
        rag_status = target_statuses.get("rag-ingestion", ReadinessStatus.not_evaluated)

        if rag_status == ReadinessStatus.blocked:
            print(f"SKIP {doc.source_path}: RAG ingestion blocked")
            continue

        if rag_status == ReadinessStatus.degraded:
            print(f"WARN {doc.source_path}: degraded — some units are unclassified")

        if doc.structured_content:
            for unit in doc.structured_content.content:
                ingest(doc, unit)
    ```

6. Check `doc.readiness` before processing to distinguish blocked files (which should not be ingested) from degraded files (which can be ingested with a quality flag). A degraded RAG status means some units have `unit_type = "unknown"`, making their chunk boundaries less reliable, but the file still contains usable content.

---

## Author Workflow Feedback

A technical writer is drafting a new howto article in VS Code. The article will be committed to the documentation repository, where it must pass the CI quality gate before merging. Finding validation errors in CI is expensive: the writer must switch context, read CI logs, interpret diagnostic codes, and push a fix. The alternative is to run the same validation locally before committing.

`structure_parser` provides four inspection commands that give authors immediate feedback at any stage of authoring: before the article is finished, while the structure is still being worked out, and before the final commit.

**Procedure:**

1. Write a Markdown article with at least a working draft title and some content.

2. Run `inspect-model` to see how the parser classified the article:

    ```bash
    structure-parser inspect-model my-article.md
    ```

    Output:

    ```
    Article: my-article.md
      article_type : [unknown]
      dita_type    : (none)
      title        : Install the Agent
      triage_status: unknown

    Units:
      [1] unit_type=unknown  info_type=unknown  title="Introduction"
      [2] unit_type=unknown  info_type=unknown  title="Steps"
      [3] unit_type=unknown  info_type=unknown  title="Next steps"
    ```

    The `[unknown]` labels indicate the parser could not determine the article type or unit types. This usually means the metadata does not declare a known `articleType` and the content does not match any recognized structural pattern.

3. Run `inspect-diagnostics` to see the full set of diagnostics for the file:

    ```bash
    structure-parser inspect-diagnostics my-article.md
    ```

    Output:

    ```
    Diagnostics for my-article.md

    WARNINGS (2)
      SP-041  Article type could not be determined
              Remediation: Add articleType metadata or conform to a known article pattern.
      SP-021  Heading level skipped: 1 to 3  [line 12]
              Remediation: Do not skip heading levels.

    INFO (1)
      SP-011  Front matter absent
              Remediation: Add a YAML front matter block with at least a title field.
    ```

4. Interpret the output. SP-011 (front matter absent) tells you to add a YAML block at the top of the article when you want explicit metadata. SP-041 (unknown article type) means neither metadata nor the current unit population identifies the article, so you can fix it by adding `articleType: howto` or by restructuring the sections so they match a known article pattern. SP-021 (heading level skipped) is a structural error at line 12 — you have jumped from H1 directly to H3 somewhere in the article.

5. Run `validate-markdown` against the target schema to confirm which constraints the current article violates:

    ```bash
    structure-parser validate-markdown my-article.md --schema artHowto.schema.json
    ```

    Output:

    ```
    FAIL  my-article.md
      [SP-041] warning  Article type could not be determined
      [SP-030] warning  Schema validation failed: required unit type 'unitProcedure' is missing

    Summary: 1 file, 2 warnings, 0 errors
    ```

6. Fix the reported violations. Add front matter with `articleType: howto` when you want an explicit declaration, restructure the "Steps" section as an ordered list so the parser classifies it as a procedure unit, and correct the H3 that follows an H1 directly.

7. After fixing, confirm transform readiness to catch any remaining gaps before committing:

    ```bash
    structure-parser transform-readiness my-article.md --target dita
    ```

    Output:

    ```
    Transform readiness: my-article.md

    dita
      status: ready
      prerequisites met:
        - title present
        - article type known (howto)
        - dita type mapped (task)
    ```

    A `ready` status for the DITA target means the article satisfies all prerequisites for DITA transformation, which also covers the prerequisites the CI howto schema checks.

---

## DITA Publishing Pipeline Preparation

A content engineering team is migrating a Markdown-based documentation site to a DITA publishing toolchain. The migration requires each article to have a mapped DITA type, a declared article type, and a title. The team has approximately 500 Markdown files in the repository and cannot inspect them manually. They need a programmatic readiness report that identifies which articles are ready to transform, which are degraded (partially ready), and which are blocked.

`structure_parser` produces DITA readiness assessments for every parsed document. The `transform-readiness` evaluator checks three prerequisites: a title (SP-020 blocks if absent), a non-unknown article type (SP-041 blocks if absent), and a valid DITA type mapping from the article type. Files that pass all three are `ready`. Files with a missing title or unknown article type are `blocked`. Files with unknown units (but a valid article type and title) are `degraded`.

**Procedure:**

1. Parse all Markdown files in the repository:

    ```python
    import glob
    from structure_parser import parse_files

    all_files = glob.glob("docs/**/*.md", recursive=True)
    result = parse_files(all_files)
    print(f"Parsed {result.stats.file_count} files in {result.stats.duration_ms:.0f} ms")
    ```

2. Separate documents by DITA readiness status:

    ```python
    from structure_parser.domain.enums import ReadinessStatus

    def dita_status(doc):
        if doc.readiness is None:
            return ReadinessStatus.not_evaluated
        for t in doc.readiness.targets:
            if t.target == "dita":
                return t.status
        return ReadinessStatus.not_evaluated

    ready     = [d for d in result.documents if dita_status(d) == ReadinessStatus.ready]
    degraded  = [d for d in result.documents if dita_status(d) == ReadinessStatus.degraded]
    blocked   = [d for d in result.documents if dita_status(d) == ReadinessStatus.blocked]
    unknown   = [d for d in result.documents if dita_status(d) == ReadinessStatus.not_evaluated]

    print(f"Ready: {len(ready)}, Degraded: {len(degraded)}, Blocked: {len(blocked)}, Unknown: {len(unknown)}")
    ```

    **Ready** means all DITA prerequisites are satisfied and the file can be passed directly to the DITA transformation step. **Degraded** means the article has a title and article type but contains units the parser classified as unknown; the DITA transform may produce output, but some sections will be mapped generically. **Blocked** means at least one hard prerequisite is missing — typically the title or the article type — and the DITA transform cannot proceed for that file.

3. Group blocked files by article type to find the most common remediation patterns:

    ```python
    from collections import Counter

    type_counts = Counter(
        d.structured_content.article_type.value
        for d in blocked
        if d.structured_content is not None
    )
    for article_type, count in type_counts.most_common():
        print(f"  {article_type}: {count} blocked files")
    ```

4. Collect the diagnostic codes that caused blocking, for each blocked document:

    ```python
    BLOCKING_CODES = {"SP-020", "SP-041", "SP-030"}

    for doc in blocked:
        violations = [d for d in doc.diagnostics if d.code in BLOCKING_CODES]
        for v in violations:
            print(f"{doc.source_path}  [{v.code}] {v.message}")
    ```

5. Generate a remediation report as a CSV:

    ```python
    import csv, sys

    writer = csv.writer(sys.stdout)
    writer.writerow(["path", "dita_status", "article_type", "blocking_codes", "messages"])

    for doc in result.documents:
        status = dita_status(doc).value
        art_type = (
            doc.structured_content.article_type.value
            if doc.structured_content else "none"
        )
        blocking = [d for d in doc.diagnostics if d.code in {"SP-020", "SP-041", "SP-030"}]
        codes = "|".join(d.code for d in blocking)
        messages = "|".join(d.message for d in blocking)
        writer.writerow([doc.source_path, status, art_type, codes, messages])
    ```

6. Use the CSV to prioritize remediation work. Files with only SP-041 are often the fastest to fix because they need either one explicit `articleType` line or clearer H2 unit patterns. Files with SP-020 (no H1) and SP-041 together need structural editing and are more expensive. Files with SP-030 (schema constraint violations) need the most attention because the content structure itself does not match the selected article type.
