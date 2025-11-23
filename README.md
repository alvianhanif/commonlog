# commonlog

[![Go Version](https://img.shields.io/badge/Go-1.19+-00ADD8?style=flat&logo=go)](https://golang.org/)
[![Python Version](https://img.shields.io/badge/Python-3.6+-3776AB?style=flat&logo=python)](https://www.python.org/)
[![PyPI Version](https://img.shields.io/pypi/v/commonlog.svg)](https://pypi.org/project/commonlog/)

A unified logging and alerting library supporting Slack and Lark integrations via WebClient and Webhook. Features configurable providers, alert levels, and file attachment support.

Available in [Go](./go/README.md) and [Python](./python/README.md).



## Features

- **Multi-Provider**: Slack and Lark
- **Multiple Send Methods**: WebClient (API-based) and Webhook (simple HTTP POST)
- **Secure Authentication**: WebClient with token-based authentication
- **Provider-Specific Tokens**: Dedicated `SlackToken` and `LarkToken` fields for secure, provider-specific authentication
- **Dynamic Provider Selection**: Use `CustomSend` (Go) or `custom_send` (Python) to send messages to different providers dynamically
- **Alert Levels**: INFO (log only), WARN (log + send), ERROR (always send)
- **File Attachments**: Public URL attachments
- **Trace Log Section**: Optional detailed trace information in alerts
- **Extensible**: Easy to add new alert providers
- **Send to Specific Channel**: Use `SendToChannel` (Go) or `send_to_channel` (Python) to override the default channel for any alert.
- **Redis Token Caching for Lark**: Lark tenant_access_token is cached in Redis for performance. Expiry is set dynamically from the API response minus 10 minutes.
- **Environment-Aware Chat ID Caching**: Lark chat IDs are cached per environment to prevent cross-environment conflicts.
- **Debug Mode**: Enable detailed logging of all internal processes and values for troubleshooting

## Redis Configuration (Lark)

Both Go and Python versions require Redis configuration for Lark token caching:

- **Go**: Set `RedisHost` and `RedisPort` in your `Config` struct.
- **Python**: Set `redis_host` and `redis_port` in your `Config` object.

If these fields are missing, Lark token caching will fail.

## Authentication

### Send Methods

commonlog supports two send methods:

#### WebClient (API-based)

- **Slack**: Uses Slack's Web API with bot tokens
- **Lark**: Uses Lark's Open API with app credentials and token caching
- **Authentication**: Requires API tokens and proper authentication
- **Features**: Full API features, channel management, rich formatting

#### Webhook (Simple HTTP POST)

- **Slack**: Uses Slack Incoming Webhooks
- **Lark**: Uses Lark Webhooks
- **Authentication**: Just provide the webhook URL as the token
- **Features**: Simple, no authentication setup required, perfect for basic alerting

**Webhook Usage:**

**Go:**

```go
config := commonlog.Config{
    Provider:   "slack",
    SendMethod: commonlog.MethodWebhook,
    Token:      "https://hooks.slack.com/services/YOUR/WEBHOOK/URL",
    Channel:    "optional-channel-override", // optional
}
```

**Python:**

```python
config = Config(
    provider="slack",
    send_method=SendMethod.WEBHOOK,
    token="https://hooks.slack.com/services/YOUR/WEBHOOK/URL",
    channel="optional-channel-override",  # optional
)
```

### Dynamic Provider Selection

Use `CustomSend` (Go) or `custom_send` (Python) to send messages to different providers dynamically, overriding the default provider:

**Go:**

```go
logger.CustomSend("slack", commonlog.ERROR, "Message via Slack", nil, "", "slack-channel")
```

**Python:**

```python
logger.custom_send("slack", AlertLevel.ERROR, "Message via Slack", channel="slack-channel")
```

## Debug Mode

Enable debug mode to get detailed logging of all internal processes and values for troubleshooting:

**Go:**

```go
config := commonlog.Config{
    Provider:   "slack",
    SendMethod: commonlog.MethodWebhook,
    Token:      "https://hooks.slack.com/services/YOUR/WEBHOOK/URL",
    Debug:      true,  // Enable debug logging
}
```

**Python:**

```python
config = Config(
    provider="slack",
    send_method=SendMethod.WEBHOOK,
    token="https://hooks.slack.com/services/YOUR/WEBHOOK/URL",
    debug=True,  # Enable debug logging
)
```

When debug mode is enabled, commonlog will log:

- Logger initialization details
- Provider creation and method selection
- Message formatting and processing
- HTTP request/response details
- Token fetching and caching operations
- Channel resolution processes
- Attachment handling

Debug logs are prefixed with `[COMMONLOG DEBUG]` and include file location information.

## Documentation

- [Go Documentation](./go/README.md)
- [Python Documentation](./python/README.md)

Both clients support all environments (dev, staging, production, unittest) and automatically configure appropriate channels. The unittest environment logs locally without making external API calls, making it safe for testing.
