---
title: Reference Guide
articleType: reference
description: Complete reference for all API endpoints and configuration options.
ms.topic: reference
version: 2.0.0
---

# Reference Guide

## Introduction

This reference guide covers all available configuration options and API endpoints.

> [!NOTE]
> All configuration values are case-sensitive.

## Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `host` | string | `localhost` | Server hostname |
| `port` | integer | `8080` | Server port |
| `debug` | boolean | `false` | Enable debug mode |
| `timeout` | integer | `30` | Request timeout in seconds |

## API Endpoints

### GET /health

Returns the health status of the service.

```json
{
  "status": "healthy",
  "version": "2.0.0"
}
```

### POST /configure

Applies configuration changes at runtime.

**Request body:**

```json
{
  "host": "string",
  "port": "integer"
}
```

## Error Codes

| Code | Meaning |
|------|---------|
| `400` | Bad request |
| `401` | Unauthorized |
| `500` | Internal server error |

## Related Topics

- [Getting Started Guide](./getting-started.md)
- [How to Configure Settings](./howto-settings.md)
