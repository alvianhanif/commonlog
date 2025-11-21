# Pasarpolis Alert Client - Go

A simplified Go client for pasarpolis services to send alerts to Lark and Slack with sensible defaults.

## Installation

This client is part of the unilog library. Make sure you have the unilog Go module available.

## Quick Start

```go
package main

import (
    "log"
    "github.com/your-org/unilog/pasarpolis_client/go"
)

func main() {
    // Create a client with defaults for production
    client, err := pasarpolis.NewClient("my-service", pasarpolis.Production, pasarpolis.Slack)
    if err != nil {
        log.Fatal(err)
    }

    // Send alerts
    client.SendError("Something went wrong!")
    client.SendWarn("This is a warning")
}
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

**Note**: The unittest environment logs alerts locally instead of sending to external APIs, making it safe for testing without requiring API tokens.

## Advanced Usage

For full customization, use `NewClientWithConfig`:

```go
package main

import (
    "github.com/your-org/unilog/pasarpolis_client/go"
    "github.com/your-org/unilog/go"
    "github.com/your-org/unilog/go/types"
)

func main() {
    configModifier := func(config *types.Config) {
        // Custom channel resolver
        config.ChannelResolver = &go.DefaultChannelResolver{
            ChannelMap: map[types.AlertLevel]string{
                types.Error: "#my-custom-alerts",
            },
            DefaultChannel: "#my-general",
        }
        // Custom API token
        config.Token = "xoxb-your-custom-slack-token"
    }

    client, err := pasarpolis.NewClientWithConfig(
        "my-service",
        pasarpolis.Production,
        pasarpolis.Slack,
        configModifier,
    )
    if err != nil {
        log.Fatal(err)
    }
}
```

## API Reference

### Client Methods

- `SendInfo(message string)`: Send info-level alert (logs only)
- `SendWarn(message string)`: Send warning alert
- `SendWarnWithAttachment(message string, attachment types.Attachment)`: Send warning with attachment
- `SendWarnWithTrace(message string, trace string)`: Send warning with trace
- `SendError(message string)`: Send error alert
- `SendErrorWithAttachment(message string, attachment types.Attachment)`: Send error with attachment
- `SendErrorWithTrace(message string, trace string)`: Send error with trace
- `SendErrorWithAttachmentAndTrace(message string, attachment types.Attachment, trace string)`: Send error with both attachment and trace

### Types

- `Environment`: Dev, Staging, Production
- `Provider`: Lark, Slack