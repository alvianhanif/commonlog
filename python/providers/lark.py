"""
Lark Provider for commonlog
"""
import requests
import json
from ..log_types import SendMethod, Provider
from .redis_client import get_redis_client, RedisConfigError

class LarkProvider(Provider):
    def send_to_channel(self, level, message, attachment, config, channel):
        original_channel = config.channel
        config.channel = channel
        self.send(level, message, attachment, config)
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

    def send(self, level, message, attachment, config):
        formatted_message = self._format_message(message, attachment, config)
        if config.send_method == SendMethod.WEBCLIENT:
            self._send_lark_webclient(formatted_message, config)
        else:
            raise ValueError(f"Unknown send method for Lark: {config.send_method}")

    def _format_message(self, message, attachment, config):
        formatted = ""
        # Add service and environment header
        if config.service_name and config.environment:
            formatted += f"**[{config.service_name} - {config.environment}]**\n"
        elif config.service_name:
            formatted += f"**[{config.service_name}]**\n"
        elif config.environment:
            formatted += f"**[{config.environment}]**\n"
        formatted += message
        if attachment and attachment.content:
            filename = attachment.file_name or "attachment.txt"
            formatted += f"\n\n**{filename}:**\n```\n{attachment.content}\n```"
        if attachment and attachment.url:
            formatted += f"\n\n**Attachment:** {attachment.url}"
        return formatted

    def _send_lark_webclient(self, formatted_message, config):
        token = config.token
        
        # Use lark_token if available, otherwise fall back to token parsing
        if config.lark_token and config.lark_token.app_id and config.lark_token.app_secret:
            token = self.get_tenant_access_token(config, config.lark_token.app_id, config.lark_token.app_secret)
        
        url = "https://open.larksuite.com/open-apis/im/v1/messages"
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        content = json.dumps({"text": formatted_message})
        payload = {"receive_id": config.channel, "msg_type": "text", "content": content}
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code != 200:
            raise Exception(f"Lark WebClient response: {response.status_code}")