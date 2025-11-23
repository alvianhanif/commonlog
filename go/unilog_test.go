package commonlog

import (
	"testing"

	"github.com/alvianhanif/commonlog/go/types"
)

func TestNewLogger(t *testing.T) {
	cfg := types.Config{
		Provider:   "slack",
		SendMethod: types.MethodWebClient,
		Token:      "dummy-token",
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
	if err := logger.Send(types.INFO, "Test info message", nil, ""); err != nil {
		t.Errorf("Expected no error for INFO level, got %v", err)
	}
}
