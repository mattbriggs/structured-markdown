# UML System Model

The diagrams on this page provide a structural and behavioral picture of `structure_parser` at different levels of abstraction. The component diagram shows subsystem boundaries and dependencies, the sequence diagrams show runtime message flows, and the class diagrams show the contract object graphs that carry data between subsystems.

## Component Diagram

The component diagram below shows the major subsystems of `structure_parser` and the dependencies between them. The CLI and Python API are the two entry points; both delegate immediately to the Orchestrator, which coordinates all other subsystems. The Orchestrator never calls adapters, enrichment steps, or validators directly — it goes through the registry and pipeline objects that own those responsibilities.

```mermaid
graph LR
    subgraph "Entry Points"
        CLI["CLI\ncommands.py"]
        API["Python API\norchestrator.py"]
    end

    subgraph "Application"
        ORCH["Orchestrator\norchestrator.py"]
    end

    subgraph "Adapters"
        REG["AdapterRegistry"]
        MD["MarkdownAdapter\nmarkdown-it-py"]
        HTML["HTMLAdapter\nlxml"]
    end

    subgraph "Enrichment"
        SE["SemanticEnricher"]
        ME["MetadataExtractor"]
        SB["StructureBuilder"]
        RC["ReferenceClassifier"]
        LFR["LocalFileResolver"]
    end

    subgraph "Classification"
        CLS["StructuredMarkdownClassifier\nclassifier.py"]
        CM["ComponentMapper"]
        AM["AttributeMapper"]
    end

    subgraph "Validation"
        VAL["SchemaValidator\nDraft7Validator"]
        SR["SchemaRepository"]
    end

    subgraph "Readiness"
        RE["ReadinessEvaluator"]
        DITA["DitaReadinessEvaluator"]
        SORG["SchemaOrgReadinessEvaluator"]
        RAG["RagIngestionReadinessEvaluator"]
    end

    subgraph "Repositories"
        SRCR["SourceRepository"]
    end

    subgraph "Reporting"
        DR["DiagnosticReporter"]
        STR["StructureReporter"]
        MR["ModelReporter"]
    end

    subgraph "Repository Pipeline"
        PORCH["PipelineOrchestrator"]
        DISC["MarkdownDiscoveryService"]
        OUT["ParsedDocumentWriter"]
        CSV["CsvInventoryReporter"]
    end

    CLI --> ORCH
    API --> ORCH
    ORCH --> REG
    ORCH --> SE
    ORCH --> CLS
    ORCH --> VAL
    ORCH --> RE
    ORCH --> SRCR
    ORCH --> DR
    ORCH --> STR
    ORCH --> MR
    CLI --> PORCH
    PORCH --> DISC
    PORCH --> ORCH
    PORCH --> OUT
    CLI --> CSV
    REG --> MD
    REG --> HTML
    SE --> ME
    SE --> SB
    SE --> RC
    SE --> LFR
    CLS --> CM
    CLS --> AM
    VAL --> SR
    RE --> DITA
    RE --> SORG
    RE --> RAG
```

The Repositories subsystem (`SourceRepository`, `SchemaRepository`) handles parser file I/O. Adapters receive source bytes from `SourceRepository` rather than reading files directly, which keeps adapters testable with in-memory strings. `SchemaRepository` pre-loads all JSON schemas at startup and hands the pre-built schema store to `SchemaValidator`, eliminating repeated file reads during batch processing.

The Repository Pipeline subsystem handles repository-scale operations. It discovers Markdown files, delegates each file to the parser orchestrator, writes parsed JSON output, and writes the CSV inventory report through the CLI command.

## Sequence Diagram

The sequence diagram below shows the complete message flow for a call to `parse_file("my-article.md")` through the Python API. Each vertical lifeline represents one object; each arrow represents one method call or return value.

```mermaid
sequenceDiagram
    participant Caller
    participant Orchestrator
    participant AdapterRegistry
    participant MarkdownAdapter
    participant SemanticEnricher
    participant MetadataExtractor
    participant StructureBuilder
    participant ReferenceClassifier
    participant StructuredMarkdownClassifier
    participant SchemaValidator
    participant ReadinessEvaluator

    Caller->>Orchestrator: parse_file("my-article.md", config)
    Orchestrator->>AdapterRegistry: get_adapter("markdown")
    AdapterRegistry-->>Orchestrator: MarkdownAdapter
    Orchestrator->>MarkdownAdapter: parse(source_bytes, path)
    MarkdownAdapter-->>Orchestrator: RawParseModel

    Orchestrator->>SemanticEnricher: enrich(raw_model, config)
    SemanticEnricher->>MetadataExtractor: extract(raw_model)
    MetadataExtractor-->>SemanticEnricher: metadata + diagnostics
    SemanticEnricher->>StructureBuilder: build(raw_model)
    StructureBuilder-->>SemanticEnricher: DocumentStructure + diagnostics
    SemanticEnricher->>ReferenceClassifier: classify(raw_model)
    ReferenceClassifier-->>SemanticEnricher: list[Reference] + diagnostics
    SemanticEnricher-->>Orchestrator: partial ParsedDocument fields

    Orchestrator->>StructuredMarkdownClassifier: classify(raw_model, metadata)
    StructuredMarkdownClassifier-->>Orchestrator: StructuredContent + diagnostics

    Orchestrator->>SchemaValidator: validate(structured_content, config)
    SchemaValidator-->>Orchestrator: ModelValidationResult + diagnostics

    Orchestrator->>ReadinessEvaluator: evaluate(parsed_document)
    ReadinessEvaluator-->>Orchestrator: TransformReadiness + diagnostics

    Orchestrator-->>Caller: ParsedDocument
```

The orchestrator is the only component that sees all five layer outputs simultaneously. It assembles them into a single `ParsedDocument` at the end, merging all diagnostics from every layer into `ParsedDocument.diagnostics`. This assembly step is the only place in the codebase where cross-layer data is combined; every other component operates on its own input contract in isolation.

## Class Diagram

The class diagram below shows the parser contract object graph. It is the authoritative picture of how `ParsedDocument` — the parser's primary output — relates to every other contract type. Cardinalities on association lines indicate how many instances of the target type a source instance may carry.

```mermaid
classDiagram
    class ParsedDocument {
        +schema_version: str
        +source_path: str
        +source_format: str
        +metadata: dict
        +title: str
        +has_errors: bool
        +error_count: int
        +warning_count: int
    }

    class DocumentProvenance {
        +content_hash: str
        +parse_timestamp: str
        +adapter_version: str
        +schema_version: str
    }

    class DocumentStructure {
        +headings: list
    }

    class StructuredContent {
        +article_type: str
        +units: list[Unit]
    }

    class Unit {
        +unit_type: str
        +title: str
        +source_span: SourceSpan
    }

    class Component {
        +component_type: str
        +content: str
        +source_span: SourceSpan
    }

    class Attribute {
        +attribute_type: str
        +content: str
    }

    class Reference {
        +ref_type: str
        +href: str
        +text: str
        +state: str
        +resolved_path: str
    }

    class Diagnostic {
        +code: str
        +severity: str
        +category: str
        +message: str
        +remediation: str
        +start_line: int
        +end_line: int
    }

    class ModelValidationResult {
        +schema_id: str
        +valid: bool
        +source_path: str
        +diagnostics: list[Diagnostic]
    }

    class TransformReadiness {
        +targets: list[TargetReadiness]
    }

    class TargetReadiness {
        +target: str
        +status: str
        +reasons: list[str]
        +missing: list[str]
    }

    class ParseRunResult {
        +documents: list[ParsedDocument]
        +run_diagnostics: list[Diagnostic]
        +success: bool
    }

    class ParseStats {
        +total_files: int
        +success_count: int
        +error_count: int
        +elapsed_seconds: float
    }

    class SourceSpan {
        +source_path: str
        +start_line: int
        +end_line: int
        +provenance_status: str
    }

    ParsedDocument "1" --> "1" DocumentProvenance : provenance
    ParsedDocument "1" --> "1" DocumentStructure : structure
    ParsedDocument "1" --> "0..1" StructuredContent : structured_content
    ParsedDocument "1" --> "0..*" Reference : references
    ParsedDocument "1" --> "0..*" Diagnostic : diagnostics
    ParsedDocument "1" --> "0..1" ModelValidationResult : validation
    ParsedDocument "1" --> "0..1" TransformReadiness : readiness
    StructuredContent "1" --> "0..*" Unit : units
    Unit "1" --> "0..*" Component : components
    Unit "1" --> "1" SourceSpan : source_span
    Component "1" --> "0..*" Attribute : attributes
    Component "1" --> "1" SourceSpan : source_span
    TransformReadiness "1" --> "1..*" TargetReadiness : targets
    ParseRunResult "1" --> "0..*" ParsedDocument : documents
    ParseRunResult "1" --> "1" ParseStats : stats
```

The class diagram reveals a key structural property of the design: `ParsedDocument` is the single root of the entire output graph. There is no other way for a caller to obtain a `StructuredContent`, `TransformReadiness`, or `ModelValidationResult` except through a `ParsedDocument`. This means callers always have full context available — they never hold a validation result without the document it came from, and they never hold a readiness assessment without the diagnostics that explain it.

## Repository Pipeline Sequence Diagram

The repository pipeline sequence diagram shows the runtime message flow for `structure-parser pipe`. The CLI command owns CSV report writing, while `PipelineOrchestrator` owns discovery, parser calls, JSON output writing, and run statistics.

```mermaid
sequenceDiagram
    actor User
    participant CLI as cmd_pipe
    participant Cmd as PipelineCommand
    participant Orch as PipelineOrchestrator
    participant Disc as MarkdownDiscoveryService
    participant Parser as parse_one
    participant Writer as ParsedDocumentWriter
    participant CSV as CsvInventoryReporter

    User->>CLI: structure-parser pipe INPUT --out OUTPUT
    CLI->>Cmd: run(PipelineConfig)
    Cmd->>Orch: run(config)
    Orch->>Disc: discover(config)
    Disc-->>Orch: DiscoveredSource[] + diagnostics
    loop each discovered source
        Orch->>Parser: parse_one(source_path, parser_config)
        Parser-->>Orch: ParsedDocument
        Orch->>Writer: write(document, target_path, dry_run)
        Writer-->>Orch: PIPE-005 or success
    end
    Orch-->>Cmd: PipelineRunResult
    Cmd->>CSV: write(result, report_path)
    CSV-->>Cmd: PIPE-003 or success
    Cmd-->>CLI: summary text + exit code
```

The pipeline sequence makes the boundary with the parser explicit. The parser decides article, unit, component, attribute, and information types; the pipeline only schedules files and preserves those parser results.

## Repository Pipeline Class Diagram

The repository pipeline class diagram shows the operational contracts added for folder-scale processing. These contracts describe run state and file routing rather than structured content semantics.

```mermaid
classDiagram
    class PipelineConfig {
        +inputs: list[Path]
        +output_dir: Path
        +report_path: Path
        +include_patterns: list[str]
        +exclude_patterns: list[str]
        +log_file: Path
        +log_format: str
        +strict: bool
        +dry_run: bool
    }

    class DiscoveredSource {
        +source_root: Path
        +source_path: Path
        +relative_path: Path
        +source_format: SourceFormat
    }

    class PipelineFileResult {
        +source: DiscoveredSource
        +target_path: Path
        +status: PipelineFileStatus
        +parser_codes: list[str]
        +pipeline_code: str
        +error_count: int
        +warning_count: int
        +duration_ms: float
    }

    class PipelineRunStats {
        +discovered_count: int
        +parsed_count: int
        +failed_count: int
        +skipped_count: int
        +error_count: int
        +warning_count: int
        +duration_ms: float
    }

    class PipelineRunResult {
        +schema_version: str
        +run_id: str
        +files: list[PipelineFileResult]
        +run_diagnostics: list[Diagnostic]
        +stats: PipelineRunStats
    }

    PipelineRunResult "1" --> "0..*" PipelineFileResult : files
    PipelineRunResult "1" --> "1" PipelineRunStats : stats
    PipelineFileResult "1" --> "1" DiscoveredSource : source
```

The pipeline class diagram shows why pipeline contracts should remain operational. The graph references parser diagnostics but does not include `Article`, `Unit`, `Component`, or `Attribute` classes because those belong to the parser/model contract graph.
