package providers

import (
	"bytes"
	"encoding/json"
	"fmt"
	"net/http"

	"gitlab.com/pasarpolis/unilog/go/types"
)

// LarkProvider implements Provider for Lark
type LarkProvider struct{}

func (p *LarkProvider) Send(level int, message string, attachment *types.Attachment, cfg types.Config) error {
	switch cfg.SendMethod {
	case types.MethodWebhook:
		return p.sendLarkWebhook(message, attachment, cfg)
	case types.MethodHTTP:
		return p.sendLarkHTTP(message, attachment, cfg)
	case types.MethodWebClient:
		return p.sendLarkWebClient(message, attachment, cfg)
	default:
		return fmt.Errorf("unknown send method for Lark: %s", cfg.SendMethod)
	}
}

// formatMessage formats the alert message with optional attachment
func (p *LarkProvider) formatMessage(message string, attachment *types.Attachment, cfg types.Config) string {
	formatted := ""

	// Add service and environment header
	if cfg.ServiceName != "" && cfg.Environment != "" {
		formatted += fmt.Sprintf("**[%s - %s]**\n", cfg.ServiceName, cfg.Environment)
	} else if cfg.ServiceName != "" {
		formatted += fmt.Sprintf("**[%s]**\n", cfg.ServiceName)
	} else if cfg.Environment != "" {
		formatted += fmt.Sprintf("**[%s]**\n", cfg.Environment)
	}

	formatted += message

	if attachment != nil {
		if attachment.Content != "" {
			// Inline content - show as expandable code block
			filename := attachment.FileName
			if filename == "" {
				filename = "attachment.txt"
			}
			formatted += fmt.Sprintf("\n\n**%s:**\n```\n%s\n```", filename, attachment.Content)
		}
		if attachment.URL != "" {
			// External URL attachment
			formatted += fmt.Sprintf("\n\n**Attachment:** %s", attachment.URL)
		}
	}

	return formatted
}

func (p *LarkProvider) sendLarkWebhook(message string, attachment *types.Attachment, cfg types.Config) error {
	payload := map[string]interface{}{
		"msg_type": "text",
		"content": map[string]string{
			"text": message,
		},
	}
	if attachment != nil {
		if attachment.Content != "" {
			// For inline content, use text message with formatted content
			formattedMessage := p.formatMessage(message, attachment, cfg)
			payload["content"] = map[string]string{
				"text": formattedMessage,
			}
		} else if attachment.URL != "" {
			// External URL attachment
			payload["msg_type"] = "post"
			payload["content"] = map[string]interface{}{
				"post": map[string]interface{}{
					"zh_cn": map[string]interface{}{
						"title": "Message",
						"content": [][]map[string]interface{}{
							{
								{"tag": "text", "text": message},
								{"tag": "a", "text": "Attachment", "href": attachment.URL},
							},
						},
					},
				},
			}
		}
	}
	data, _ := json.Marshal(payload)
	resp, err := http.Post(cfg.WebhookURL, "application/json", bytes.NewBuffer(data))
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	if resp.StatusCode != 200 {
		return fmt.Errorf("lark webhook response: %d", resp.StatusCode)
	}
	return nil
}

func (p *LarkProvider) sendLarkHTTP(message string, attachment *types.Attachment, cfg types.Config) error {
	formattedMessage := p.formatMessage(message, attachment, cfg)
	payload := map[string]interface{}{
		"msg_type": "text",
		"content": map[string]string{
			"text": formattedMessage,
		},
	}
	data, _ := json.Marshal(payload)
	resp, err := http.Post(cfg.HTTPURL, "application/json", bytes.NewBuffer(data))
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	if resp.StatusCode != 200 {
		return fmt.Errorf("lark HTTP response: %d", resp.StatusCode)
	}
	return nil
}

func (p *LarkProvider) sendLarkWebClient(message string, attachment *types.Attachment, cfg types.Config) error {
	formattedMessage := p.formatMessage(message, attachment, cfg)
	url := "https://open.larksuite.com/open-apis/im/v1/messages"
	headers := map[string]string{"Authorization": "Bearer " + cfg.Token, "Content-Type": "application/json"}
	content := fmt.Sprintf(`{"text":"%s"}`, formattedMessage)
	payload := map[string]interface{}{
		"receive_id": cfg.Channel,
		"msg_type":   "text",
		"content":    json.RawMessage(content),
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
		return fmt.Errorf("lark WebClient response: %d", resp.StatusCode)
	}
	return nil
}
