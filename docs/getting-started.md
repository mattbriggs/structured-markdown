# Getting Started

## Installation

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install structure-parser
```

## Parse a File

```bash
structure-parser parse my-article.md
```

## Inspect the Model

```bash
structure-parser inspect-model my-article.md
structure-parser inspect-structure my-article.md
structure-parser inspect-references my-article.md
structure-parser inspect-diagnostics my-article.md
```

## Validate Against a Schema

```bash
structure-parser validate-markdown my-article.md --schema artHowto.schema.json
```

## Python API

```python
from structure_parser import parse_file

doc = parse_file("my-article.md")
print(doc.title)
print(doc.structured_content.article_type)
for unit in doc.structured_content.content:
    print(f"  {unit.unit_type}: {unit.title}")
```

## Development Setup

```bash
git clone https://github.com/mb/structured-markdown
cd structured-markdown
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pre-commit install
```

## Run Tests

```bash
pytest
pytest --cov=structure_parser --cov-report=term-missing
```
