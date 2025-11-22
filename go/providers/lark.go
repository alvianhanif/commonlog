package providers

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"time"

	"github.com/alvianhanif/commonlog/go/types"

	redis "github.com/go-redis/redis/v8"
)

// getRedisClient returns a Redis client using host/port from cfg, env, or default
func getRedisClient(cfg types.Config) (*redis.Client, error) {
	host := cfg.RedisHost
	port := cfg.RedisPort
	fmt.Printf("[Lark] Initializing Redis client with host: '%s', port: '%s'\n", host, port)
	if host == "" || port == "" {
		fmt.Printf("[Lark] RedisHost and RedisPort must be set in commonlog config\n")
		return nil, fmt.Errorf("RedisHost and RedisPort must be set in commonlog config")
	}
	addr := host + ":" + port
	fmt.Printf("[Lark] Connecting to Redis at address: %s\n", addr)
	client := redis.NewClient(&redis.Options{
		Addr: addr,
		DB:   0,
	})
	ctx := context.Background()
	if err := client.Ping(ctx).Err(); err != nil {
		fmt.Printf("[Lark] Failed to ping Redis at %s: %v\n", addr, err)
		return nil, fmt.Errorf("failed to ping Redis: %w", err)
	}
	fmt.Printf("[Lark] Successfully connected to Redis at %s\n", addr)
	return client, nil
}

func cacheLarkToken(cfg types.Config, appID, appSecret, token string) error {
	key := "commonlog_lark_token:" + appID + ":" + appSecret
	client, err := getRedisClient(cfg)
	if err != nil {
		return err
	}
	return client.Set(context.Background(), key, token, 90*time.Minute).Err()
}

func cacheChatID(cfg types.Config, channelName, chatID string) error {
	key := "commonlog_lark_chat_id:" + cfg.Environment + ":" + channelName
	client, err := getRedisClient(cfg)
	if err != nil {
		return err
	}
	return client.Set(context.Background(), key, chatID, 0).Err() // No expiry
}

func getCachedLarkToken(cfg types.Config, appID, appSecret string) (string, error) {
	key := "commonlog_lark_token:" + appID + ":" + appSecret
	client, err := getRedisClient(cfg)
	if err != nil {
		return "", err
	}
	result, err := client.Get(context.Background(), key).Result()
	if err == redis.Nil {
		fmt.Printf("[Lark] No cached token found for key: %s\n", key)
		return "", nil // No cached token
	} else if err != nil {
		fmt.Printf("[Lark] Error retrieving cached token for key %s: %v\n", key, err)
		return "", err
	}
	fmt.Printf("[Lark] Retrieved cached token for key: %s\n", key)
	return result, nil
}

func getCachedChatID(cfg types.Config, channelName string) (string, error) {
	key := "commonlog_lark_chat_id:" + cfg.Environment + ":" + channelName
	client, err := getRedisClient(cfg)
	if err != nil {
		return "", err
	}
	result, err := client.Get(context.Background(), key).Result()
	if err == redis.Nil {
		fmt.Printf("[Lark] No cached chat_id found for channel: %s in environment: %s\n", channelName, cfg.Environment)
		return "", nil // No cached chat_id
	} else if err != nil {
		fmt.Printf("[Lark] Error retrieving cached chat_id for channel %s in environment %s: %v\n", channelName, cfg.Environment, err)
		return "", err
	}
	fmt.Printf("[Lark] Retrieved cached chat_id for channel: %s in environment: %s\n", channelName, cfg.Environment)
	return result, nil
}

// getChatIDFromChannelName fetches the chat_id for a given channel name using pagination
func getChatIDFromChannelName(cfg types.Config, token, channelName string) (string, error) {
	// Try Redis cache first
	cached, err := getCachedChatID(cfg, channelName)
	if err != nil {
		return "", fmt.Errorf("failed to get Redis client: %w", err)
	}
	if cached != "" {
		return cached, nil
	}

	baseURL := "https://open.larksuite.com/open-apis/im/v1/chats"
	headers := map[string]string{"Authorization": "Bearer " + token}

	pageToken := ""
	hasMore := true

	for hasMore {
		url := baseURL + "?page_size=10"
		if pageToken != "" {
			url += "&page_token=" + pageToken
		}

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
			Code int    `json:"code"`
			Msg  string `json:"msg"`
			Data struct {
				Items []struct {
					ChatID string `json:"chat_id"`
					Name   string `json:"name"`
				} `json:"items"`
				PageToken string `json:"page_token"`
				HasMore   bool   `json:"has_more"`
			} `json:"data"`
		}

		if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
			return "", err
		}

		if result.Code != 0 {
			return "", fmt.Errorf("lark API error: %s", result.Msg)
		}

		// Search for the channel name in the current page
		for _, item := range result.Data.Items {
			if item.Name == channelName {
				// Cache the chat_id without expiry
				if err := cacheChatID(cfg, channelName, item.ChatID); err != nil {
					fmt.Printf("[Lark] Warning: failed to cache chat_id for channel %s: %v\n", channelName, err)
				}
				return item.ChatID, nil
			}
		}

		// Update pagination info
		pageToken = result.Data.PageToken
		hasMore = result.Data.HasMore
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
	err = client.Set(context.Background(), key, result.Token, time.Duration(expireSeconds)*time.Second).Err()
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
				filename = "Trace Logs"
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

	fmt.Printf("[Lark] Sending message to channel '%s' with method WebClient\n", cfg.Channel)

	// Use LarkToken if available, otherwise fall back to Token parsing
	var appID, appSecret string
	if cfg.LarkToken.AppID != "" && cfg.LarkToken.AppSecret != "" {
		appID = cfg.LarkToken.AppID
		appSecret = cfg.LarkToken.AppSecret
		fmt.Printf("[Lark] Fetching tenant access token for appID '%s'\n", appID)
		fetched, err := getTenantAccessToken(cfg, appID, appSecret)
		if err != nil {
			fmt.Printf("[Lark] Error fetching tenant access token: %v\n", err)
			return err
		}
		token = fetched
	}

	// Get chat_id from channel name
	fmt.Printf("[Lark] Resolving chat_id for channel '%s'\nToken: %s\n", cfg.Channel, token)
	chatID, err := getChatIDFromChannelName(cfg, token, cfg.Channel)
	if err != nil {
		fmt.Printf("[Lark] Failed to get chat_id for channel '%s': %v\n", cfg.Channel, err)
		return fmt.Errorf("failed to get chat_id for channel '%s': %v", cfg.Channel, err)
	}

	url := "https://open.larksuite.com/open-apis/im/v1/messages?receive_id_type=chat_id"
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
	fmt.Printf("[Lark] Sending POST request to %s\n", url)
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		fmt.Printf("[Lark] Error sending POST request: %v\n", err)
		return err
	}
	defer resp.Body.Close()

	// Log response data
	respBody := new(bytes.Buffer)
	_, copyErr := respBody.ReadFrom(resp.Body)
	if copyErr != nil {
		fmt.Printf("[Lark] Error reading response body: %v\n", copyErr)
	} else {
		fmt.Printf("[Lark] Response data: %s\n", respBody.String())
	}

	if resp.StatusCode != 200 {
		fmt.Printf("[Lark] WebClient response status: %d\n", resp.StatusCode)
		fmt.Printf("[Lark] Response data: %s\n", respBody.String())
		return fmt.Errorf("lark WebClient response: %d", resp.StatusCode)
	}
	fmt.Printf("[Lark] Message sent successfully to channel '%s'. Response: %s\n", cfg.Channel, respBody.String())
	return nil
}
