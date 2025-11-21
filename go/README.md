# unilog (Go)

A unified logging and alerting library for Go, supporting Slack and Lark integrations via WebClient. Features configurable providers, alert levels, and file attachment support.

## Installation

Add to your `go.mod`:

```bash
go get gitlab.com/pasarpolis/unilog/go
```

## Usage

```go
package main

import (
    "gitlab.com/pasarpolis/unilog/go"
)

func main() {
    cfg := unilog.Config{
        Provider:   "slack",
        SendMethod: unilog.MethodWebClient,
        Token:      "xoxb-your-slack-bot-token",
        Channel:    "#alerts",
    }
    logger := unilog.NewLogger(cfg)

    // Send error with attachment
    logger.Send(unilog.ERROR, "System error occurred", &unilog.Attachment{URL: "https://example.com/log.txt"})

    // Send info (logs only)
    logger.Send(unilog.INFO, "Info message")
}
```

## Channel Mapping

You can configure different channels for different alert levels using a channel resolver:

```go
package main

import (
    "gitlab.com/pasarpolis/unilog/go"
    "gitlab.com/pasarpolis/unilog/go/types"
)

func main() {
    // Create a channel resolver that maps alert levels to different channels
    resolver := &types.DefaultChannelResolver{
        ChannelMap: map[int]string{
            types.INFO:  "#general",
            types.WARN:  "#warnings",
            types.ERROR: "#alerts",
        },
        DefaultChannel: "#general",
    }

    // Create config with channel resolver
    config := types.Config{
        Provider:        "slack",
        SendMethod:      types.MethodWebClient,
        Token:           "xoxb-your-slack-bot-token",
        ChannelResolver: resolver,
        ServiceName:     "user-service",
        Environment:     "production",
    }

    logger := unilog.NewLogger(config)

    // These will go to different channels based on level
    logger.Send(types.INFO, "Info message")    // goes to #general
    logger.Send(types.WARN, "Warning message") // goes to #warnings
    logger.Send(types.ERROR, "Error message")  // goes to #alerts
}
```

### Custom Channel Resolver

You can implement custom channel resolution logic:

```go
type CustomResolver struct{}

func (r *CustomResolver) ResolveChannel(level int) string {
    switch level {
    case types.ERROR:
        return "#critical-alerts"
    case types.WARN:
        return "#monitoring"
    default:
        return "#general"
    }
}
```

## Configuration Options

### Common Settings

- **Provider**: `"slack"` or `"lark"`
- **SendMethod**: `MethodWebClient` (token-based authentication)
- **Channel**: Target channel or chat ID (used if no resolver)
- **ChannelResolver**: Optional resolver for dynamic channel mapping
- **ServiceName**: Name of the service sending alerts
- **Environment**: Environment (dev, staging, production)

### Provider-Specific

- **Token**: API token for WebClient authentication (required)

## Alert Levels

- **INFO**: Logs locally only
- **WARN**: Logs + sends alert
- **ERROR**: Always sends alert

## File Attachments

Provide a public URL. The library appends it to the message for simplicity.

```go
attachment := &unilog.Attachment{URL: "https://example.com/log.txt"}
logger.Send(unilog.ERROR, "Error with log", attachment, "")
```

## Trace Log Section

When `IncludeTrace` is set to `true`, you can pass trace information as the fourth parameter to `Send()`:

```go
trace := "goroutine 1 [running]:\nmain.main()\n    /app/main.go:15 +0x2f"
logger.Send(unilog.ERROR, "System error occurred", nil, trace)
```

This will format the trace as a code block in the alert message.

## Testing

```bash
cd go
go test
```

## API Reference

### Types

- `Config`: Configuration struct
- `Attachment`: File attachment struct
- `Provider`: Interface for alert providers

### Constants

- `MethodWebClient`: Send method (token-based authentication)
- `INFO`, `WARN`, `ERROR`: Alert levels

### Functions

- `NewLogger(cfg Config) *Logger`: Create a new logger
- `(*Logger) Send(level int, message string, attachment *Attachment, trace string)`: Send alert with optional trace
