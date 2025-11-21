package providers

import (
	"bytes"
	"encoding/json"
	"fmt"
	"net/http"

	"gitlab.com/pasarpolis/commonlog/go/types"
)

// SlackProvider implements Provider for Slack
type SlackProvider struct{}

func (p *SlackProvider) Send(level int, message string, attachment *types.Attachment, cfg types.Config) error {
	return p.SendToChannel(level, message, attachment, cfg, cfg.Channel)
}

func (p *SlackProvider) SendToChannel(level int, message string, attachment *types.Attachment, cfg types.Config, channel string) error {
	cfgCopy := cfg
	cfgCopy.Channel = channel
	switch cfgCopy.SendMethod {
	case types.MethodWebClient:
		return p.sendSlackWebClient(message, attachment, cfgCopy)
	default:
		return fmt.Errorf("unknown send method for Slack: %s", cfgCopy.SendMethod)
	}
}

// formatMessage formats the alert message with optional attachment
func (p *SlackProvider) formatMessage(message string, attachment *types.Attachment, cfg types.Config) string {
	formatted := ""

	// Add service and environment header
	if cfg.ServiceName != "" && cfg.Environment != "" {
		formatted += fmt.Sprintf("*[%s - %s]*\n", cfg.ServiceName, cfg.Environment)
	} else if cfg.ServiceName != "" {
		formatted += fmt.Sprintf("*[%s]*\n", cfg.ServiceName)
	} else if cfg.Environment != "" {
		formatted += fmt.Sprintf("*[%s]*\n", cfg.Environment)
	}

	formatted += message

	if attachment != nil {
		if attachment.Content != "" {
			// Inline content - show as expandable code block
			filename := attachment.FileName
			if filename == "" {
				filename = "attachment.txt"
			}
			formatted += fmt.Sprintf("\n\n*%s:*\n```\n%s\n```", filename, attachment.Content)
		}
		if attachment.URL != "" {
			// External URL attachment
			formatted += fmt.Sprintf("\n\n*Attachment:* %s", attachment.URL)
		}
	}

	return formatted
}

func (p *SlackProvider) sendSlackWebClient(message string, attachment *types.Attachment, cfg types.Config) error {
	formattedMessage := p.formatMessage(message, attachment, cfg)
	url := "https://slack.com/api/chat.postMessage"
	headers := map[string]string{"Authorization": "Bearer " + cfg.Token, "Content-Type": "application/json"}
	payload := map[string]interface{}{
		"channel": cfg.Channel,
		"text":    formattedMessage,
	}
	data, _ := json.Marshal(payload)
	req, _ := http.NewRequest("POST", url, bytes.NewBuffer(data))
	for k, v := range headers {
		req.Header.Set(k, v)
	}
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	if resp.StatusCode != 200 {
		return fmt.Errorf("slack WebClient response: %d", resp.StatusCode)
	}
	return nil
}
