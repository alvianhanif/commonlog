package unilog

import (
	"log"

	"gitlab.com/pasarpolis/unilog/go/providers"
	"gitlab.com/pasarpolis/unilog/go/types"
)

// ====================
// Main Logger
// ====================

// Logger is the main struct
type Logger struct {
	config   types.Config
	provider types.Provider
}

// NewLogger creates a new Logger with the appropriate provider
func NewLogger(cfg types.Config) *Logger {
	var provider types.Provider
	switch cfg.Provider {
	case "slack":
		provider = &providers.SlackProvider{}
	case "lark":
		provider = &providers.LarkProvider{}
	default:
		provider = &providers.SlackProvider{}
	}
	return &Logger{config: cfg, provider: provider}
}

// resolveChannel resolves the channel for the given alert level
func (l *Logger) resolveChannel(level int) string {
	if l.config.ChannelResolver != nil {
		return l.config.ChannelResolver.ResolveChannel(level)
	}
	return l.config.Channel
}

// Send sends a message with alert level, optional attachment, and optional trace log
func (l *Logger) Send(level int, message string, attachment *types.Attachment, trace string) {
	if level == types.INFO {
		log.Printf("[INFO] %s", message)
		return
	}

	// Resolve the channel for this alert level
	resolvedChannel := l.resolveChannel(level)

	// Create a config with the resolved channel for this send operation
	sendConfig := l.config
	sendConfig.Channel = resolvedChannel

	// If trace is provided, create a trace attachment
	if trace != "" {
		traceAttachment := &types.Attachment{
			FileName: "trace.log",
			Content:  trace,
		}
		// If there's already an attachment, combine the trace content
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

	if err := l.provider.Send(level, message, attachment, sendConfig); err != nil {
		log.Printf("[ERROR] Failed to send alert: %v", err)
	}
}
