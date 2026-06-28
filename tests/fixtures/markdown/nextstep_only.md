---
title: What Is the Parser
description: Conceptual overview of the structured-markdown parser.
---

# What Is the Parser

## Overview

The parser converts Markdown files into a structured article hierarchy.
It applies semantic classification to each logical section.

## Key Concepts

The parser uses a layered architecture: adapters read source files, classifiers
assign semantic labels, validators check schema compliance, and readiness
evaluators report downstream transform risk.

## Next Steps

- [Install the parser](./install.md)
- [Configure settings](./configure.md)
