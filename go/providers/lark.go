package providers

import (
	"bytes"
	"encoding/json"
	"fmt"
	"net/http"
	"time"

	"github.com/alvianhanif/commonlog/go/types"

	redis "github.com/go-redis/redis"
)

// getRedisClient returns a Redis client using host/port from cfg, env, or default
func getRedisClient(cfg types.Config) (*redis.Client, error) {
	host := cfg.RedisHost
	port := cfg.RedisPort
	if host == "" || port == "" {
		return nil, fmt.Errorf("RedisHost and RedisPort must be set in commonlog config")
	}
	addr := host + ":" + port
	return redis.NewClient(&redis.Options{
		Addr: addr,
	}), nil
}

func cacheLarkToken(cfg types.Config, appID, appSecret, token string) error {
	key := "commonlog_lark_token:" + appID + ":" + appSecret
	client, err := getRedisClient(cfg)
	if err != nil {
		return err
	}
	return client.Set(key, token, 90*time.Minute).Err()
}

func getCachedLarkToken(cfg types.Config, appID, appSecret string) (string, error) {
	key := "commonlog_lark_token:" + appID + ":" + appSecret
	client, err := getRedisClient(cfg)
	if err != nil {
		return "", err
	}
	return client.Get(key).Result()
}

// getChatIDFromChannelName fetches the chat_id for a given channel name
func getChatIDFromChannelName(cfg types.Config, token, channelName string) (string, error) {
	url := "https://open.larksuite.com/open-apis/im/v1/chats?user_id_type=open_id"
	headers := map[string]string{"Authorization": "Bearer " + token}

	req, err := http.NewRequest("GET", url, nil)
	if err != nil {
		return "", err
	}
	for k, v := range headers {
		req.Header.Set(k, v)
	}

	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return "", err
	}
	defer resp.Body.Close()

	if resp.StatusCode != 200 {
		return "", fmt.Errorf("lark chats API response: %d", resp.StatusCode)
	}

	var result struct {
		Items []struct {
			ChatID string `json:"chat_id"`
			Name   string `json:"name"`
		} `json:"items"`
	}

	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return "", err
	}

	// Find the chat with matching name
	for _, item := range result.Items {
		if item.Name == channelName {
			return item.ChatID, nil
		}
	}

	return "", fmt.Errorf("channel '%s' not found", channelName)
}

// LarkProvider implements Provider for Lark
type LarkProvider struct{}

func getTenantAccessToken(cfg types.Config, appID, appSecret string) (string, error) {
	// Try Redis cache first
	cached, err := getCachedLarkToken(cfg, appID, appSecret)
	if err != nil {
		return "", fmt.Errorf("failed to get Redis client: %w", err)
	}
	if cached != "" {
		return cached, nil
	}
	url := "https://open.larksuite.com/open-apis/auth/v3/tenant_access_token/internal"
	payload := map[string]string{"app_id": appID, "app_secret": appSecret}
	data, _ := json.Marshal(payload)
	req, err := http.NewRequest("POST", url, bytes.NewBuffer(data))
	if err != nil {
		return "", err
	}
	req.Header.Set("Content-Type", "application/json")
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return "", err
	}
	defer resp.Body.Close()
	var result struct {
		Code   int    `json:"code"`
		Msg    string `json:"msg"`
		Token  string `json:"tenant_access_token"`
		Expire int    `json:"expire"`
	}
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return "", err
	}
	if result.Code != 0 {
		return "", fmt.Errorf("lark token error: %s", result.Msg)
	}
	// Cache the token for (expire - 10 minutes)
	expireSeconds := result.Expire - 600
	if expireSeconds <= 0 {
		expireSeconds = 60 // fallback to 1 minute if API returns too low
	}
	key := "commonlog_lark_token:" + appID + ":" + appSecret
	client, err := getRedisClient(cfg)
	if err != nil {
		return "", fmt.Errorf("failed to get Redis client: %w", err)
	}
	err = client.Set(key, result.Token, time.Duration(expireSeconds)*time.Second).Err()
	if err != nil {
		return "", fmt.Errorf("failed to cache token: %w", err)
	}
	return result.Token, nil
}

func (p *LarkProvider) Send(level int, message string, attachment *types.Attachment, cfg types.Config) error {
	return p.SendToChannel(level, message, attachment, cfg, cfg.Channel)
}

func (p *LarkProvider) SendToChannel(level int, message string, attachment *types.Attachment, cfg types.Config, channel string) error {
	cfgCopy := cfg
	cfgCopy.Channel = channel
	switch cfgCopy.SendMethod {
	case types.MethodWebClient:
		return p.sendLarkWebClient(message, attachment, cfgCopy)
	default:
		return fmt.Errorf("unknown send method for Lark: %s", cfgCopy.SendMethod)
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

func (p *LarkProvider) sendLarkWebClient(message string, attachment *types.Attachment, cfg types.Config) error {
	formattedMessage := p.formatMessage(message, attachment, cfg)
	token := cfg.Token

	// Use LarkToken if available, otherwise fall back to Token parsing
	var appID, appSecret string
	if cfg.LarkToken.AppID != "" && cfg.LarkToken.AppSecret != "" {
		appID = cfg.LarkToken.AppID
		appSecret = cfg.LarkToken.AppSecret
		fetched, err := getTenantAccessToken(cfg, appID, appSecret)
		if err != nil {
			return err
		}
		token = fetched
	}

	// Get chat_id from channel name
	chatID, err := getChatIDFromChannelName(cfg, token, cfg.Channel)
	if err != nil {
		return fmt.Errorf("failed to get chat_id for channel '%s': %v", cfg.Channel, err)
	}

	url := "https://open.larksuite.com/open-apis/im/v1/messages"
	headers := map[string]string{"Authorization": "Bearer " + token, "Content-Type": "application/json"}
	content := fmt.Sprintf(`{"text":"%s"}`, formattedMessage)
	payload := map[string]interface{}{
		"receive_id": chatID,
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
