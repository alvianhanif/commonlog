"""
Lark Provider for commonlog
"""
import requests
import json
import sys
import os

# Add directories to path for imports
_current_dir = os.path.dirname(os.path.abspath(__file__))
_parent_dir = os.path.dirname(_current_dir)
if _parent_dir not in sys.path:
    sys.path.insert(0, _parent_dir)
if _current_dir not in sys.path:
    sys.path.insert(0, _current_dir)

from log_types import SendMethod, Provider, debug_log
from redis_client import get_redis_client, RedisConfigError

class LarkProvider(Provider):
    def send_to_channel(self, level, message, attachment, config, channel):
        original_channel = config.channel
        config.channel = channel
        title, formatted_message = self._format_message(message, attachment, config)
        if config.send_method == SendMethod.WEBCLIENT:
            self._send_lark_webclient(title, formatted_message, config)
        elif config.send_method == SendMethod.WEBHOOK:
            self._send_lark_webhook(title, formatted_message, config)
        config.channel = original_channel

    def cache_lark_token(self, config, app_id, app_secret, token, expire):
        key = f"commonlog_lark_token:{app_id}:{app_secret}"
        try:
            client = get_redis_client(config)
        except RedisConfigError as e:
            raise Exception(f"Redis config error: {e}")
        expire_seconds = expire - 600
        if expire_seconds <= 0:
            expire_seconds = 60
        client.setex(key, expire_seconds, token)

    def get_cached_lark_token(self, config, app_id, app_secret):
        key = f"commonlog_lark_token:{app_id}:{app_secret}"
        try:
            client = get_redis_client(config)
        except RedisConfigError as e:
            raise Exception(f"Redis config error: {e}")
        return client.get(key)

    def cache_chat_id(self, config, channel_name, chat_id):
        key = f"commonlog_lark_chat_id:{config.environment}:{channel_name}"
        try:
            client = get_redis_client(config)
        except RedisConfigError as e:
            raise Exception(f"Redis config error: {e}")
        client.set(key, chat_id)  # No expiry

    def get_cached_chat_id(self, config, channel_name):
        key = f"commonlog_lark_chat_id:{config.environment}:{channel_name}"
        try:
            client = get_redis_client(config)
        except RedisConfigError as e:
            raise Exception(f"Redis config error: {e}")
        return client.get(key)

    def get_tenant_access_token(self, config, app_id, app_secret):
        cached = self.get_cached_lark_token(config, app_id, app_secret)
        if cached:
            return cached
        url = "https://open.larksuite.com/open-apis/auth/v3/tenant_access_token/internal"
        payload = {"app_id": app_id, "app_secret": app_secret}
        response = requests.post(url, json=payload)
        result = response.json()
        if result.get("code", 1) != 0:
            raise Exception(f"lark token error: {result.get('msg')}")
        token = result.get("tenant_access_token")
        expire = result.get("expire", 0)
        self.cache_lark_token(config, app_id, app_secret, token, expire)
        return token

    def get_chat_id_from_channel_name(self, config, token, channel_name):
        """Get chat_id from channel name using Lark API with pagination"""
        # Try Redis cache first
        cached = self.get_cached_chat_id(config, channel_name)
        if cached:
            return cached
        
        base_url = "https://open.larksuite.com/open-apis/im/v1/chats"
        headers = {"Authorization": f"Bearer {token}"}
        
        all_chats = []
        page_token = ""
        has_more = True
        
        while has_more:
            url = f"{base_url}?page_size=10"
            if page_token:
                url += f"&page_token={page_token}"
            
            response = requests.get(url, headers=headers)
            if response.status_code != 200:
                raise Exception(f"Lark chats API response: {response.status_code}")
            
            result = response.json()
            
            # Check for API error
            if result.get("code", 1) != 0:
                raise Exception(f"Lark API error: {result.get('msg', 'Unknown error')}")
            
            data = result.get("data", {})
            items = data.get("items", [])
            
            # Add current page items to all chats
            all_chats.extend(items)
            
            # Update pagination info
            page_token = data.get("page_token", "")
            has_more = data.get("has_more", False)
        
        # Find the chat with matching name
        for item in all_chats:
            if item.get("name") == channel_name:
                chat_id = item.get("chat_id")
                # Cache the chat_id without expiry
                self.cache_chat_id(config, channel_name, chat_id)
                return chat_id
        
        raise Exception(f"Channel '{channel_name}' not found")

    def send(self, level, message, attachment, config):
        debug_log(config, f"LarkProvider.send called with level: {level}, send method: {config.send_method}")
        title, formatted_message = self._format_message(message, attachment, config)
        if config.send_method == SendMethod.WEBCLIENT:
            debug_log(config, "Using Lark webclient method")
            self._send_lark_webclient(title, formatted_message, config)
        elif config.send_method == SendMethod.WEBHOOK:
            debug_log(config, "Using Lark webhook method")
            self._send_lark_webhook(title, formatted_message, config)
        else:
            error_msg = f"Unknown send method for Lark: {config.send_method}"
            debug_log(config, f"Error: {error_msg}")
            raise ValueError(error_msg)

    def _format_message(self, message, attachment, config):
        # Extract title from service and environment
        title = "Alert"
        if config.service_name and config.environment:
            title = f"{config.service_name} - {config.environment}"
        elif config.service_name:
            title = config.service_name
        elif config.environment:
            title = config.environment
        
        # Format message content without the header
        formatted = message
        if attachment and attachment.content:
            filename = attachment.file_name or "Trace Logs"
            formatted += f"\n\n**{filename}:**\n```\n{attachment.content}\n```"
        if attachment and attachment.url:
            formatted += f"\n\n**Attachment:** {attachment.url}"
        return title, json.dumps(formatted)

    def _send_lark_webclient(self, title, formatted_message, config):
        debug_log(config, "send_lark_webclient: preparing API request")
        token = config.token
        
        # Use lark_token if available, otherwise fall back to token parsing
        if config.lark_token and config.lark_token.app_id and config.lark_token.app_secret:
            debug_log(config, "send_lark_webclient: fetching tenant access token using lark_token")
            token = self.get_tenant_access_token(config, config.lark_token.app_id, config.lark_token.app_secret)
            debug_log(config, "send_lark_webclient: tenant access token fetched")
        elif token and len(token) < 100 and "++" in token:
            # If token is in "app_id++app_secret" format, fetch the tenant_access_token
            debug_log(config, "send_lark_webclient: parsing token in app_id++app_secret format")
            parts = token.split("++")
            if len(parts) == 2:
                token = self.get_tenant_access_token(config, parts[0], parts[1])
                debug_log(config, "send_lark_webclient: tenant access token fetched from parsed token")
        
        # Get chat_id from channel name
        debug_log(config, f"send_lark_webclient: resolving chat_id for channel '{config.channel}'")
        chat_id = self.get_chat_id_from_channel_name(config, token, config.channel)
        debug_log(config, f"send_lark_webclient: resolved chat_id")
        
        url = "https://open.larksuite.com/open-apis/im/v1/messages?receive_id_type=chat_id"
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        payload = {
            "receive_id": chat_id,
            "msg_type": "post",
            "content": {
                "post": {
                    "zh_cn": {
                        "title": title,
                        "content": [
                            [
                                {
                                    "tag": "text",
                                    "text": formatted_message
                                }
                            ]
                        ]
                    }
                }
            }
        }
        debug_log(config, f"send_lark_webclient: sending HTTP request, payload size: {len(str(payload))}, payload: {json.dumps(payload)}")
        
        response = requests.post(url, headers=headers, json=payload)
        debug_log(config, f"send_lark_webclient: response status: {response.status_code}")
        if response.status_code != 200:
            error_msg = f"Lark WebClient response: {response.status_code}"
            debug_log(config, f"send_lark_webclient: error: {error_msg}")
            raise Exception(error_msg)
        debug_log(config, "send_lark_webclient: message sent successfully")

    def _send_lark_webhook(self, title, formatted_message, config):
        debug_log(config, "send_lark_webhook: preparing webhook request")
        # For webhook, the token field contains the webhook URL
        webhook_url = config.token
        if not webhook_url:
            error_msg = "Webhook URL is required for Lark webhook method"
            debug_log(config, f"Error: {error_msg}")
            raise Exception(error_msg)
        
        debug_log(config, "send_lark_webhook: using webhook URL")
        payload = {
            "msg_type": "post",
            "content": {
                "post": {
                    "zh_cn": {
                        "title": title,
                        "content": [
                            [
                                {
                                    "tag": "text",
                                    "text": formatted_message
                                }
                            ]
                        ]
                    }
                }
            }
        }
        debug_log(config, f"send_lark_webhook: payload prepared, size: {len(str(payload))}, payload: {json.dumps(payload)}")
        response = requests.post(webhook_url, json=payload)
        debug_log(config, f"send_lark_webhook: response status: {response.status_code}, response data: {response.text}")
        if response.status_code != 200:
            error_msg = f"Lark webhook response: {response.status_code}"
            debug_log(config, f"send_lark_webhook: error: {error_msg}")
            raise Exception(error_msg)
        debug_log(config, "send_lark_webhook: webhook sent successfully")