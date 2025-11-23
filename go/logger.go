package commonlog

import (
	"log"

	"github.com/alvianhanif/commonlog/go/providers"
	"github.com/alvianhanif/commonlog/go/types"
)

// ====================
// Main Logger
// ====================

// createProvider creates a provider instance by name
func createProvider(providerName string) types.Provider {
	switch providerName {
	case "slack":
		return &providers.SlackProvider{}
	case "lark":
		return &providers.LarkProvider{}
	default:
		return &providers.SlackProvider{}
	}
}

// Logger is the main struct
type Logger struct {
	config   types.Config
	provider types.Provider
}

// NewLogger creates a new Logger with the appropriate provider
func NewLogger(cfg types.Config) *Logger {
	providerName := createProvider(cfg.Provider)
	return &Logger{config: cfg, provider: providerName}
}

// resolveChannel resolves the channel for the given alert level
func (l *Logger) resolveChannel(level int) string {
	if l.config.ChannelResolver != nil {
		return l.config.ChannelResolver.ResolveChannel(level)
	}
	return l.config.Channel
}

// Send sends a message with alert level, optional attachment, and optional trace log
func (l *Logger) Send(level int, message string, attachment *types.Attachment, trace string) error {
	return l.SendToChannel(level, message, attachment, trace, "")
}

// SendToChannel sends a message to a specific channel, overriding the default/channel resolver
func (l *Logger) SendToChannel(level int, message string, attachment *types.Attachment, trace string, channel string) error {
	if level == types.INFO {
		log.Printf("[INFO] %s", message)
		return nil
	}

	resolvedChannel := channel
	if resolvedChannel == "" {
		resolvedChannel = l.resolveChannel(level)
	}

	sendConfig := l.config
	sendConfig.Channel = resolvedChannel

	if trace != "" {
		traceAttachment := &types.Attachment{
			FileName: "trace.log",
			Content:  trace,
		}
		if attachment != nil {
			if attachment.Content != "" {
				attachment.Content += "\n\n--- Trace Log ---\n" + trace
			} else {
				attachment.Content = trace
				attachment.FileName = "trace.log"
			}
		} else {
			attachment = traceAttachment
		}
	}

	return l.provider.SendToChannel(level, message, attachment, sendConfig, resolvedChannel)
}

// CustomSend sends a message with a custom provider, allowing override of the default provider
func (l *Logger) CustomSend(provider string, level int, message string, attachment *types.Attachment, trace string, channel string) error {
	customProvider := createProvider(provider)
	if customProvider == nil {
		log.Printf("[ERROR] Unknown provider: %s, defaulting to slack", provider)
		customProvider = createProvider("slack")
	}

	if level == types.INFO {
		log.Printf("[INFO] %s", message)
		return nil
	}

	resolvedChannel := channel
	if resolvedChannel == "" {
		resolvedChannel = l.resolveChannel(level)
	}

	sendConfig := l.config
	sendConfig.Channel = resolvedChannel

	if trace != "" {
		traceAttachment := &types.Attachment{
			FileName: "trace.log",
			Content:  trace,
		}
		if attachment != nil {
			if attachment.Content != "" {
				attachment.Content += "\n\n--- Trace Log ---\n" + trace
			} else {
				attachment.Content = trace
				attachment.FileName = "trace.log"
			}
		} else {
			attachment = traceAttachment
		}
	}

	return customProvider.SendToChannel(level, message, attachment, sendConfig, resolvedChannel)
}
