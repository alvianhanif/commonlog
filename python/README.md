# unilog (Python)

A unified logging and alerting library for Python, supporting Slack and Lark integrations via WebClient. Features configurable providers, alert levels, and file attachment support.

## Installation

Install via pip:

```bash
pip install unilog
```

Or copy the `python/` directory to your project.


## Usage

```python
from python import Unilog, Config, SendMethod, AlertLevel, Attachment

# Configure logger
config = Config(
    provider="lark", # or "slack"
    send_method=SendMethod.WEBCLIENT,
    token="app_id++app_secret", # for Lark, use "app_id++app_secret" format
    channel="your_lark_channel_id",
    redis_host="localhost", # required for Lark
    redis_port="6379",      # required for Lark
)
logger = Unilog(config)

# Send error with attachment
logger.send(AlertLevel.ERROR, "System error occurred", Attachment(url="https://example.com/log.txt"))

 # Send info (logs only)
logger.send(AlertLevel.INFO, "Info message")

# Send to a specific channel
logger.send_to_channel(AlertLevel.ERROR, "Send to another channel", channel="another-channel-id")
```

### Lark Token Caching

When using Lark, the tenant_access_token is cached in Redis. The expiry is set dynamically from the API response minus 10 minutes. You must set `redis_host` and `redis_port` in your config.

## Channel Mapping

You can configure different channels for different alert levels using a channel resolver:

```python
from unilog import Unilog, Config, SendMethod, AlertLevel, DefaultChannelResolver

# Create a channel resolver
resolver = DefaultChannelResolver(
    channel_map={
        AlertLevel.INFO: "#general",
        AlertLevel.WARN: "#warnings",
        AlertLevel.ERROR: "#alerts",
    },
    default_channel="#general"
)

# Create config with channel resolver
config = Config(
    provider="slack",
    send_method=SendMethod.WEBCLIENT,
    token="xoxb-your-slack-bot-token",
    channel_resolver=resolver,
    service_name="user-service",
    environment="production"
)

logger = Unilog(config)

# These will go to different channels based on level
logger.send(AlertLevel.INFO, "Info message")    # goes to #general
logger.send(AlertLevel.WARN, "Warning message") # goes to #warnings
logger.send(AlertLevel.ERROR, "Error message")  # goes to #alerts
```

### Custom Channel Resolver

You can implement custom channel resolution logic:

```python
class CustomResolver(ChannelResolver):
    def resolve_channel(self, level):
        if level == AlertLevel.ERROR:
            return "#critical-alerts"
        elif level == AlertLevel.WARN:
            return "#monitoring"
        else:
            return "#general"
```

## Configuration Options

### Common Settings

- **provider**: `"slack"` or `"lark"`
- **send_method**: `"webclient"` (token-based authentication)
- **channel**: Target channel or chat ID (used if no resolver)
- **channel_resolver**: Optional resolver for dynamic channel mapping
- **service_name**: Name of the service sending alerts
- **environment**: Environment (dev, staging, production)

### Provider-Specific

- **token**: API token for WebClient authentication (required)

## Alert Levels

- **INFO**: Logs locally only
- **WARN**: Logs + sends alert
- **ERROR**: Always sends alert

## File Attachments

Provide a public URL. The library appends it to the message for simplicity.

```python
attachment = Attachment(url="https://example.com/log.txt")
logger.send(AlertLevel.ERROR, "Error with log", attachment)
```

## Trace Log Section

When `include_trace` is set to `True`, you can pass trace information as the fourth parameter to `send()`:

```python
trace = """Traceback (most recent call last):
  File "app.py", line 10, in main
    raise ValueError("Something went wrong")
ValueError: Something went wrong"""

logger.send(AlertLevel.ERROR, "System error occurred", None, trace)
```

This will format the trace as a code block in the alert message.

## Testing

```bash
cd python
PYTHONPATH=.. python -m unittest test_unilog.py
```

## API Reference

### Classes

- `Config`: Configuration class
- `Attachment`: File attachment class
- `Provider`: Abstract base class for alert providers
- `Unilog`: Main logger class

### Constants

- `SendMethod.WEBCLIENT`: Send method (token-based authentication)
- `AlertLevel.INFO`, `AlertLevel.WARN`, `AlertLevel.ERROR`: Alert levels

### Methods

- `Unilog(config)`: Create a new logger
- `Unilog.send(level, message, attachment=None, trace="")`: Send alert with optional trace
