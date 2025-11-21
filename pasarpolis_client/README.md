# Pasarpolis Alert Clients

Simplified client libraries for pasarpolis services to easily integrate alerting to Lark and Slack with sensible defaults.

## Overview

These clients provide a simplified interface over the full unilog library, making it easy for pasarpolis services to add alerting with minimal configuration. They include:

- **Sensible defaults** for channel mappings based on environment
- **Environment variable configuration** for API tokens
- **Full customization options** when needed
- **Support for both Lark and Slack**

## Languages Supported

- [Go](./go/) - Go client library
- [Python](./python/) - Python client library

## Quick Start

### Go

```go
client, err := pasarpolis.NewClient("my-service", pasarpolis.Production, pasarpolis.Slack)
// Send alerts...
```

### Python

```python
client = Client.create("my-service", Environment.PRODUCTION, Provider.SLACK)
# Send alerts...
```

## Environment Variables

Both clients require API tokens to be set via environment variables:

```bash
export PASARPOLIS_SLACK_TOKEN="xoxb-your-slack-bot-token"
export PASARPOLIS_LARK_TOKEN="your-lark-app-token"
```

## Default Behavior

The clients automatically configure appropriate channels for each environment:

- **Production**: Alerts go to production channels
- **Staging**: Alerts go to staging channels
- **Development**: Alerts go to development channels
- **Unittest**: Alerts are logged locally (safe for testing, no external API calls)

See the language-specific READMEs for detailed channel mappings.

## Customization

Both clients support full customization while maintaining the simplified interface:

```go
// Go - modify config before creating client
configModifier := func(config *types.Config) {
    config.ChannelResolver = &go.DefaultChannelResolver{...}
}
client, _ := pasarpolis.NewClientWithConfig("service", pasarpolis.Prod, pasarpolis.Slack, configModifier)
```

```python
# Python - modify config before creating client
def config_modifier(config):
    config.channel_resolver = DefaultChannelResolver(...)
client = Client.create_with_config("service", Environment.PRODUCTION, Provider.SLACK, config_modifier)
```

## Integration Examples

See the language-specific READMEs for complete usage examples and API documentation.