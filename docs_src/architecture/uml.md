# UML System Model

The three diagrams on this page provide a complete structural and behavioral picture of `structure_parser` at different levels of abstraction. The component diagram shows subsystem boundaries and dependencies. The sequence diagram shows the runtime message flow for a single file parse. The class diagram shows the contract object graph that carries data between subsystems.

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

The Repositories subsystem (`SourceRepository`, `SchemaRepository`) handles all file I/O. Adapters receive source bytes from `SourceRepository` rather than reading files directly, which keeps adapters testable with in-memory strings. `SchemaRepository` pre-loads all JSON schemas at startup and hands the pre-built schema store to `SchemaValidator`, eliminating repeated file reads during batch processing. The Reporting subsystem formats `ParsedDocument` fields for terminal output; it has no access to the pipeline and depends only on the contracts.

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

The class diagram below shows the contract object graph. It is the authoritative picture of how `ParsedDocument` — the pipeline's primary output — relates to every other contract type. Cardinalities on association lines indicate how many instances of the target type a source instance may carry.

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
