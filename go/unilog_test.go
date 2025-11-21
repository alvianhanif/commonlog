package unilog

import (
	"testing"

	"gitlab.com/pasarpolis/unilog/go/types"
)

func TestNewLogger(t *testing.T) {
	cfg := types.Config{
		Provider:   "slack",
		SendMethod: types.MethodWebhook,
		WebhookURL: "https://example.com",
		Channel:    "#test",
	}
	logger := NewLogger(cfg)
	if logger.config.Provider != "slack" {
		t.Errorf("Expected provider %s, got %s", "slack", logger.config.Provider)
	}
}

func TestSendInfo(t *testing.T) {
	cfg := types.Config{}
	logger := NewLogger(cfg)
	// INFO level should not send, just log
	logger.Send(types.INFO, "Test info message", nil, "")
}
