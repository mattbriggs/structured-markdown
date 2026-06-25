"""Enumerations for the structure parser domain."""

import enum


class Severity(str, enum.Enum):
    error = "error"
    warning = "warning"
    info = "info"
    debug = "debug"


class ResolutionState(str, enum.Enum):
    not_attempted = "not_attempted"
    resolved = "resolved"
    unresolved = "unresolved"
    unsupported = "unsupported"


class SourceFormat(str, enum.Enum):
    markdown = "markdown"
    html5 = "html5"
    unknown = "unknown"


class TriageStatus(str, enum.Enum):
    known = "known"
    unknown = "unknown"
    ambiguous = "ambiguous"


class ProvenanceStatus(str, enum.Enum):
    available = "available"
    unavailable = "unavailable"
    partial = "partial"


class ReadinessStatus(str, enum.Enum):
    ready = "ready"
    blocked = "blocked"
    degraded = "degraded"
    not_evaluated = "not_evaluated"


class InformationType(str, enum.Enum):
    concept = "concept"
    procedure = "procedure"
    principle = "principle"
    process = "process"
    fact = "fact"
    mixed = "mixed"
    unknown = "unknown"


class ArticleType(str, enum.Enum):
    topic = "topic"
    concept = "concept"
    howto = "howto"
    reference = "reference"
    troubleshooting = "troubleshooting"
    glossary = "glossary"
    glossentry = "glossentry"
    overview = "overview"
    quickstart = "quickstart"
    tutorial = "tutorial"
    unknown = "unknown"


class UnitType(str, enum.Enum):
    introduction = "introduction"
    concept = "concept"
    procedure = "procedure"
    principle = "principle"
    process = "process"
    fact = "fact"
    reference = "reference"
    troubleshooting = "troubleshooting"
    glossary = "glossary"
    glossentry = "glossentry"
    prerequisites = "prerequisites"
    link_nextstep = "link-nextstep"
    link_related = "link-related"
    unknown = "unknown"


class ComponentType(str, enum.Enum):
    compAlert = "compAlert"
    compBlockCode = "compBlockCode"
    compBlockQuote = "compBlockQuote"
    compBlueBox = "compBlueBox"
    compColumns = "compColumns"
    compHeaderH1 = "compHeaderH1"
    compHeaderH2 = "compHeaderH2"
    compHeaderH3 = "compHeaderH3"
    compHeaderH4 = "compHeaderH4"
    compHeaderH5 = "compHeaderH5"
    compHeaderH6 = "compHeaderH6"
    compInclude = "compInclude"
    compLink = "compLink"
    compListOrdered = "compListOrdered"
    compListUnordered = "compListUnordered"
    compListItem = "compListItem"
    compParagraph = "compParagraph"
    compTable = "compTable"
    compTableRow = "compTableRow"
    compTableCell = "compTableCell"
    compUnknown = "compUnknown"
    compVideo = "compVideo"
    compMetadata = "compMetadata"


class AttributeType(str, enum.Enum):
    attText = "attText"
    attLink = "attLink"
    attAnchor = "attAnchor"
    attBold = "attBold"
    attCode = "attCode"
    attEmphasis = "attEmphasis"
    attImage = "attImage"
    attItalic = "attItalic"
    attSpan = "attSpan"
    attStrong = "attStrong"
    attSub = "attSub"
    attSuper = "attSuper"
    attUnknown = "attUnknown"


class DiagnosticCategory(str, enum.Enum):
    parse_error = "parse_error"
    metadata_error = "metadata_error"
    structural_warning = "structural_warning"
    authoring_violation = "authoring_violation"
    reference_error = "reference_error"
    schema_error = "schema_error"
    unknown_classification = "unknown_classification"
    transform_readiness = "transform_readiness"
    internal_error = "internal_error"


class ProcedureRepresentation(str, enum.Enum):
    ordered_list = "ordered-list"
    code_block = "code-block"
    mixed = "mixed"
    unknown = "unknown"
