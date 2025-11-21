# Pasarpolis Alert Client - Python

A simplified Python client for pasarpolis services to send alerts to Lark and Slack with sensible defaults.

## Installation

This client is part of the unilog library. Make sure you have the unilog Python package installed.

## Quick Start

```python
from pasarpolis_client.python import Client, Environment, Provider

# Create a client with defaults for production
client = Client.create(
    service_name="my-service",
    env=Environment.PRODUCTION,
    provider=Provider.SLACK
)

# Send alerts
client.send_error("Something went wrong!")
client.send_warn("This is a warning")
```

## Environment Variables

Set the following environment variables for API tokens:

- `PASARPOLIS_SLACK_TOKEN`: Slack bot token (starts with `xoxb-`)
- `PASARPOLIS_LARK_TOKEN`: Lark app token

## Default Channel Mappings

The client automatically maps alert levels to appropriate channels based on environment:

### Production
- INFO: `#pasarpolis-general`
- WARN: `#pasarpolis-warnings`
- ERROR: `#pasarpolis-alerts`

### Staging
- INFO: `#pasarpolis-staging-general`
- WARN: `#pasarpolis-staging-warnings`
- ERROR: `#pasarpolis-staging-alerts`

### Development
- INFO: `#pasarpolis-dev-general`
- WARN: `#pasarpolis-dev-warnings`
- ERROR: `#pasarpolis-dev-alerts`

### Unittest
- INFO: `#pasarpolis-unittest-general`
- WARN: `#pasarpolis-unittest-warnings`
- ERROR: `#pasarpolis-unittest-alerts`

**Note**: The unittest environment logs alerts locally instead of sending to external APIs, making it safe for testing without requiring webhook URLs.

## Advanced Usage

For full customization, use `create_with_config`:

```python
from pasarpolis_client.python import Client, Environment, Provider
from unilog.python import Config, DefaultChannelResolver, AlertLevel

def customize_config(config):
    # Custom channel resolver
    config.channel_resolver = DefaultChannelResolver(
        channel_map={
            AlertLevel.ERROR: "#my-custom-alerts"
        },
        default_channel="#my-general"
    )
    # Custom webhook URL
    config.webhook_url = "https://hooks.slack.com/services/..."

client = Client.create_with_config(
    service_name="my-service",
    env=Environment.PRODUCTION,
    provider=Provider.SLACK,
    config_modifier=customize_config
)
```

## API Reference

### Client Methods

- `send_info(message)`: Send info-level alert (logs only)
- `send_warn(message)`: Send warning alert
- `send_warn_with_attachment(message, attachment)`: Send warning with attachment
- `send_warn_with_trace(message, trace)`: Send warning with trace
- `send_error(message)`: Send error alert
- `send_error_with_attachment(message, attachment)`: Send error with attachment
- `send_error_with_trace(message, trace)`: Send error with trace
- `send_error_with_attachment_and_trace(message, attachment, trace)`: Send error with both attachment and trace

### Enums

- `Environment`: DEV, STAGING, PRODUCTION
- `Provider`: LARK, SLACK