# commonlog

A unified logging and alerting library supporting Slack and Lark integrations via WebClient. Features configurable providers, alert levels, and file attachment support.

Available in [Go](./go/README.md) and [Python](./python/README.md).



## Features

- **Multi-Provider**: Slack and Lark
- **Secure Authentication**: WebClient with token-based authentication
- **Provider-Specific Tokens**: Dedicated `SlackToken` and `LarkToken` fields for secure, provider-specific authentication
- **Dynamic Provider Selection**: Use `CustomSend` (Go) or `custom_send` (Python) to send messages to different providers dynamically
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

## Authentication

### Provider-Specific Tokens

For enhanced security and flexibility, you can use provider-specific token fields:

**Go:**
```go
config := commonlog.Config{
    SlackToken: "xoxb-your-slack-token",
    LarkToken: commonlog.LarkTokenConfig{
        AppID:     "your-app-id", 
        AppSecret: "your-app-secret",
    },
    // ... other config
}
```

**Python:**
```python
config = Config(
    slack_token="xoxb-your-slack-token",
    lark_token=LarkToken(app_id="your-app-id", app_secret="your-app-secret"),
    # ... other config
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

## Documentation

- [Go Documentation](./go/README.md)
- [Python Documentation](./python/README.md)

Both clients support all environments (dev, staging, production, unittest) and automatically configure appropriate channels. The unittest environment logs locally without making external API calls, making it safe for testing.
