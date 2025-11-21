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
- **Send to Specific Channel**: Use `SendToChannel` (Go) or `send_to_channel` (Python) to override the default channel for any alert.
- **Redis Token Caching for Lark**: Lark tenant_access_token is cached in Redis for performance. Expiry is set dynamically from the API response minus 10 minutes.

## Redis Configuration (Lark)

Both Go and Python versions require Redis configuration for Lark token caching:

- **Go**: Set `RedisHost` and `RedisPort` in your `Config` struct.
- **Python**: Set `redis_host` and `redis_port` in your `Config` object.

If these fields are missing, Lark token caching will fail.

## Documentation

- [Go Documentation](./go/README.md)
- [Python Documentation](./python/README.md)

Both clients support all environments (dev, staging, production, unittest) and automatically configure appropriate channels. The unittest environment logs locally without making external API calls, making it safe for testing.
