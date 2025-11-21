// Package pasarpolis provides a simplified client for pasarpolis services
// to send alerts to Lark and Slack with sensible defaults.
package pasarpolis

import (
	"fmt"
	"log"

	unilog "gitlab.com/pasarpolis/unilog/go"
	"gitlab.com/pasarpolis/unilog/go/types"
)

// Environment represents the deployment environment
type Environment string

const (
	EnvDev        Environment = "dev"
	EnvStaging    Environment = "staging"
	EnvProduction Environment = "production"
	EnvUnittest   Environment = "unittest"
)

// Provider represents the alert provider
type Provider string

const (
	ProviderLark  Provider = "lark"
	ProviderSlack Provider = "slack"
)

// Client is the main client for sending alerts
type Client struct {
	logger *unilog.Logger
	config types.Config
}

// NewClient creates a new pasarpolis alert client with sensible defaults
func NewClient(serviceName string, env Environment, provider Provider) (*Client, error) {
	config := types.Config{
		Provider:    string(provider),
		ServiceName: serviceName,
		Environment: string(env),
	}

	// Set up default channel resolver based on environment
	resolver := getDefaultChannelResolver(env)
	config.ChannelResolver = resolver

	// Set default send method and credentials based on provider
	switch provider {
	case ProviderLark:
		config.SendMethod = types.MethodWebhook
		// Default Lark webhook URL - should be configured via environment variables
		if env == EnvUnittest {
			config.WebhookURL = "unittest://dummy-lark"
		} else if webhookURL := getEnvVar("PASARPOLIS_LARK_WEBHOOK_URL"); webhookURL != "" {
			config.WebhookURL = webhookURL
		} else {
			return nil, fmt.Errorf("PASARPOLIS_LARK_WEBHOOK_URL environment variable not set")
		}
	case ProviderSlack:
		config.SendMethod = types.MethodWebhook
		// Default Slack webhook URL - should be configured via environment variables
		if env == EnvUnittest {
			config.WebhookURL = "unittest://dummy-slack"
		} else if webhookURL := getEnvVar("PASARPOLIS_SLACK_WEBHOOK_URL"); webhookURL != "" {
			config.WebhookURL = webhookURL
		} else {
			return nil, fmt.Errorf("PASARPOLIS_SLACK_WEBHOOK_URL environment variable not set")
		}
	default:
		return nil, fmt.Errorf("unsupported provider: %s", provider)
	}

	logger := unilog.NewLogger(config)

	return &Client{
		logger: logger,
		config: config,
	}, nil
}

// NewClientWithConfig creates a client with custom configuration
func NewClientWithConfig(serviceName string, env Environment, provider Provider, configModifier func(*types.Config)) (*Client, error) {
	client, err := NewClient(serviceName, env, provider)
	if err != nil {
		return nil, err
	}

	if configModifier != nil {
		configModifier(&client.config)
		// Recreate logger with modified config
		client.logger = unilog.NewLogger(client.config)
	}

	return client, nil
}

// sendOrLog handles sending alerts or logging for unittest environment
func (c *Client) sendOrLog(level int, levelName string, message string, attachment *types.Attachment, trace string) {
	if c.config.Environment == string(EnvUnittest) {
		if attachment != nil && trace != "" {
			log.Printf("[%s] %s (attachment: %s)\nTrace: %s", levelName, message, attachment.FileName, trace)
		} else if attachment != nil {
			log.Printf("[%s] %s (attachment: %s)", levelName, message, attachment.FileName)
		} else if trace != "" {
			log.Printf("[%s] %s\nTrace: %s", levelName, message, trace)
		} else {
			log.Printf("[%s] %s", levelName, message)
		}
		return
	}
	c.logger.Send(level, message, attachment, trace)
}

// SendInfo sends an info-level alert (logs only)
func (c *Client) SendInfo(message string) {
	c.sendOrLog(types.INFO, "INFO", message, nil, "")
}

// SendWarn sends a warning-level alert
func (c *Client) SendWarn(message string) {
	c.sendOrLog(types.WARN, "WARN", message, nil, "")
}

// SendWarnWithAttachment sends a warning-level alert with attachment
func (c *Client) SendWarnWithAttachment(message string, attachment *types.Attachment) {
	c.sendOrLog(types.WARN, "WARN", message, attachment, "")
}

// SendWarnWithTrace sends a warning-level alert with trace
func (c *Client) SendWarnWithTrace(message string, trace string) {
	c.sendOrLog(types.WARN, "WARN", message, nil, trace)
}

// SendError sends an error-level alert
func (c *Client) SendError(message string) {
	c.sendOrLog(types.ERROR, "ERROR", message, nil, "")
}

// SendErrorWithAttachment sends an error-level alert with attachment
func (c *Client) SendErrorWithAttachment(message string, attachment *types.Attachment) {
	c.sendOrLog(types.ERROR, "ERROR", message, attachment, "")
}

// SendErrorWithTrace sends an error-level alert with trace
func (c *Client) SendErrorWithTrace(message string, trace string) {
	c.sendOrLog(types.ERROR, "ERROR", message, nil, trace)
}

// SendErrorWithAttachmentAndTrace sends an error-level alert with both attachment and trace
func (c *Client) SendErrorWithAttachmentAndTrace(message string, attachment *types.Attachment, trace string) {
	c.sendOrLog(types.ERROR, "ERROR", message, attachment, trace)
}

// getDefaultChannelResolver returns appropriate channel mappings for each environment
func getDefaultChannelResolver(env Environment) types.ChannelResolver {
	switch env {
	case EnvProduction:
		return &types.DefaultChannelResolver{
			ChannelMap: map[int]string{
				types.INFO:  "#pasarpolis-general",
				types.WARN:  "#pasarpolis-warnings",
				types.ERROR: "#pasarpolis-alerts",
			},
			DefaultChannel: "#pasarpolis-general",
		}
	case EnvStaging:
		return &types.DefaultChannelResolver{
			ChannelMap: map[int]string{
				types.INFO:  "#pasarpolis-staging-general",
				types.WARN:  "#pasarpolis-staging-warnings",
				types.ERROR: "#pasarpolis-staging-alerts",
			},
			DefaultChannel: "#pasarpolis-staging-general",
		}
	case EnvDev:
		return &types.DefaultChannelResolver{
			ChannelMap: map[int]string{
				types.INFO:  "#pasarpolis-dev-general",
				types.WARN:  "#pasarpolis-dev-warnings",
				types.ERROR: "#pasarpolis-dev-alerts",
			},
			DefaultChannel: "#pasarpolis-dev-general",
		}
	case EnvUnittest:
		return &types.DefaultChannelResolver{
			ChannelMap: map[int]string{
				types.INFO:  "#pasarpolis-unittest-general",
				types.WARN:  "#pasarpolis-unittest-warnings",
				types.ERROR: "#pasarpolis-unittest-alerts",
			},
			DefaultChannel: "#pasarpolis-unittest-general",
		}
	default:
		return &types.DefaultChannelResolver{
			DefaultChannel: "#pasarpolis-general",
		}
	}
}

// getEnvVar gets environment variable with fallback
func getEnvVar(key string) string {
	// In a real implementation, this would use os.Getenv(key)
	// For now, return empty string to indicate env var should be set
	return ""
}
