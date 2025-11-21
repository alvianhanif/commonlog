# unilog

A unified logging and alerting library supporting Slack and Lark integrations via WebClient, webhook, or direct HTTP. Features configurable providers, alert levels, and file attachment support.

Available in [Go](./go/README.md) and [Python](./python/README.md).

## Features

- **Multi-Provider**: Slack and Lark
- **Multiple Interfaces**: WebClient, webhook, Direct HTTP
- **Alert Levels**: INFO (log only), WARN (log + send), ERROR (always send)
- **File Attachments**: Public URL attachments
- **Trace Log Section**: Optional detailed trace information in alerts
- **Extensible**: Easy to add new alert providers

## Documentation

- [Go Documentation](./go/README.md)
- [Python Documentation](./python/README.md)
