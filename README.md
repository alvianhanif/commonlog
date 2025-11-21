# unilog

A unified logging and alerting library supporting Slack and Lark integrations via WebClient. Features configurable providers, alert levels, and file attachment support.

Available in [Go](./go/README.md) and [Python](./python/README.md).

## Features

- **Multi-Provider**: Slack and Lark
- **Secure Authentication**: WebClient with token-based authentication
- **Alert Levels**: INFO (log only), WARN (log + send), ERROR (always send)
- **File Attachments**: Public URL attachments
- **Trace Log Section**: Optional detailed trace information in alerts
- **Extensible**: Easy to add new alert providers

## Documentation

- [Go Documentation](./go/README.md)
- [Python Documentation](./python/README.md)

## Pasarpolis Client Libraries

For simplified integration with pasarpolis services, we provide easy-to-use client libraries that handle common configurations and provide sensible defaults:

- **[Go Client](./pasarpolis_client/go/README.md)**: Simplified Go client with environment-based channel mappings
- **[Python Client](./pasarpolis_client/python/README.md)**: Simplified Python client with environment-based channel mappings

### Quick Start

**Go:**

```go
client, err := pasarpolis.NewClient("my-service", pasarpolis.Production, pasarpolis.Slack)
// Send alerts...
```

**Python:**

```python
client = Client.create("my-service", Environment.PRODUCTION, Provider.SLACK)
# Send alerts...
```

Both clients support all environments (dev, staging, production, unittest) and automatically configure appropriate channels. The unittest environment logs locally without making external API calls, making it safe for testing.
