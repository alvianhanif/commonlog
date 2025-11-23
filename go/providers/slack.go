package providers

import (
	"bytes"
	"encoding/json"
	"fmt"
	"net/http"

	"github.com/alvianhanif/commonlog/go/types"
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
	case types.MethodWebhook:
		return p.sendSlackWebhook(message, attachment, cfgCopy)
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
				filename = "Trace Logs"
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

func (p *SlackProvider) sendSlackWebhook(message string, attachment *types.Attachment, cfg types.Config) error {
	formattedMessage := p.formatMessage(message, attachment, cfg)

	// For webhook, the token field contains the webhook URL
	webhookURL := cfg.Token
	if webhookURL == "" {
		return fmt.Errorf("webhook URL is required for Slack webhook method")
	}

	payload := map[string]interface{}{
		"text": formattedMessage,
	}
	// If channel is specified, include it in the payload
	if cfg.Channel != "" {
		payload["channel"] = cfg.Channel
	}

	data, _ := json.Marshal(payload)
	fmt.Printf("[SlackProvider] Sending webhook to URL: %s, payload: %s\n", webhookURL, string(data))
	req, _ := http.NewRequest("POST", webhookURL, bytes.NewBuffer(data))
	req.Header.Set("Content-Type", "application/json")

	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		fmt.Printf("[SlackProvider] Error sending webhook request: %v\n", err)
		return err
	}
	defer resp.Body.Close()

	// Log response data
	respData := new(bytes.Buffer)
	respData.ReadFrom(resp.Body)
	fmt.Printf("[SlackProvider] Slack webhook response status: %d, body: %s\n", resp.StatusCode, respData.String())

	if resp.StatusCode != 200 {
		return fmt.Errorf("slack webhook response: %d", resp.StatusCode)
	}
	fmt.Println("[SlackProvider] Webhook sent successfully")
	return nil
}

func (p *SlackProvider) sendSlackWebClient(message string, attachment *types.Attachment, cfg types.Config) error {
	formattedMessage := p.formatMessage(message, attachment, cfg)

	// Use SlackToken if available, otherwise fall back to Token
	token := cfg.Token
	if cfg.SlackToken != "" {
		token = cfg.SlackToken
	}

	url := "https://slack.com/api/chat.postMessage"
	headers := map[string]string{"Authorization": "Bearer " + token, "Content-Type": "application/json; charset=utf-8"}
	payload := map[string]interface{}{
		"channel": cfg.Channel,
		"text":    formattedMessage,
	}
	data, _ := json.Marshal(payload)
	fmt.Printf("[SlackProvider] Sending to channel: %s, payload: %s\n", cfg.Channel, string(data))
	req, _ := http.NewRequest("POST", url, bytes.NewBuffer(data))
	for k, v := range headers {
		req.Header.Set(k, v)
	}
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		fmt.Printf("[SlackProvider] Error sending request: %v\n", err)
		return err
	}
	defer resp.Body.Close()

	// Log response data
	respData := new(bytes.Buffer)
	respData.ReadFrom(resp.Body)
	fmt.Printf("[SlackProvider] Slack WebClient response status: %d, body: %s\n", resp.StatusCode, respData.String())

	if resp.StatusCode != 200 {
		return fmt.Errorf("slack WebClient response: %d", resp.StatusCode)
	}
	fmt.Println("[SlackProvider] Message sent successfully")
	return nil
}
