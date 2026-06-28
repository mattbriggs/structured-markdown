---
title: Understanding the Pipeline
description: Overview and reference for the pipeline system.
---

# Understanding the Pipeline

## Overview

The pipeline system parses Markdown and HTML files and produces structured
content with semantic classification, unit tagging, and transform readiness.

## Architecture

The pipeline follows a layered design with adapters, classifiers, validators,
and readiness evaluators as independent modules.

## Key Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `source` | `.` | Source directory to scan |
| `output` | `./output` | Output directory for results |
| `format` | `json` | Output format |

## Next Steps

- [How to configure settings](./configure.md)
- [API reference](./api.md)
