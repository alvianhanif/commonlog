"""
Slack Provider for commonlog
"""
import requests
import sys
import os

# Add parent directory to path for imports
_parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _parent_dir not in sys.path:
    sys.path.insert(0, _parent_dir)

from log_types import SendMethod, Provider, debug_log

class SlackProvider(Provider):
    def send_to_channel(self, level, message, attachment, config, channel):
        original_channel = config.channel
        config.channel = channel
        self.send(level, message, attachment, config)
        config.channel = original_channel

    def send(self, level, message, attachment, config):
        debug_log(config, f"SlackProvider.send called with level: {level}, send method: {config.send_method}")
        formatted_message = self._format_message(message, attachment, config)
        if config.send_method == SendMethod.WEBCLIENT:
            debug_log(config, "Using Slack webclient method")
            self._send_slack_webclient(formatted_message, config)
        elif config.send_method == SendMethod.WEBHOOK:
            debug_log(config, "Using Slack webhook method")
            self._send_slack_webhook(formatted_message, config)
        else:
            error_msg = f"Unknown send method for Slack: {config.send_method}"
            debug_log(config, f"Error: {error_msg}")
            raise ValueError(error_msg)

    def _format_message(self, message, attachment, config):
        formatted = ""

        # Add service and environment header
        if config.service_name and config.environment:
            formatted += f"*[{config.service_name} - {config.environment}]*\n"
        elif config.service_name:
            formatted += f"*[{config.service_name}]*\n"
        elif config.environment:
            formatted += f"*[{config.environment}]*\n"

        formatted += message

        if attachment and attachment.content:
            filename = attachment.file_name or "Trace Logs"
            formatted += f"\n\n*{filename}:*\n```\n{attachment.content}\n```"
        if attachment and attachment.url:
            formatted += f"\n\n*Attachment:* {attachment.url}"

        return formatted

    def _send_slack_webclient(self, formatted_message, config):
        debug_log(config, "send_slack_webclient: preparing API request")
        # Use slack_token if available, otherwise fall back to token
        token = config.token
        if config.slack_token:
            token = config.slack_token
            debug_log(config, "send_slack_webclient: using slack_token")
        else:
            debug_log(config, "send_slack_webclient: using token")
        
        url = "https://slack.com/api/chat.postMessage"
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json; charset=utf-8"}
        payload = {"channel": config.channel, "text": formatted_message}
        debug_log(config, f"send_slack_webclient: sending to channel: {config.channel}, payload size: {len(str(payload))}")
        
        response = requests.post(url, headers=headers, json=payload)
        debug_log(config, f"send_slack_webclient: response status: {response.status_code}, response data: {response.text}")
        if response.status_code != 200:
            error_msg = f"Slack WebClient response: {response.status_code}"
            debug_log(config, f"send_slack_webclient: error: {error_msg}")
            raise Exception(error_msg)
        debug_log(config, "send_slack_webclient: message sent successfully")

    def _send_slack_webhook(self, formatted_message, config):
        debug_log(config, "send_slack_webhook: preparing webhook request")
        # For webhook, the token field contains the webhook URL
        webhook_url = config.token
        if not webhook_url:
            error_msg = "Webhook URL is required for Slack webhook method"
            debug_log(config, f"Error: {error_msg}")
            raise Exception(error_msg)
        
        debug_log(config, f"send_slack_webhook: using webhook URL, channel: {config.channel}")
        payload = {"text": formatted_message}
        # If channel is specified, include it in the payload
        if config.channel:
            payload["channel"] = config.channel
        
        debug_log(config, f"send_slack_webhook: payload prepared, size: {len(str(payload))}")
        response = requests.post(webhook_url, json=payload)
        debug_log(config, f"send_slack_webhook: response status: {response.status_code}, response data: {response.text}")
        if response.status_code != 200:
            error_msg = f"Slack webhook response: {response.status_code}"
            debug_log(config, f"send_slack_webhook: error: {error_msg}")
            raise Exception(error_msg)
        debug_log(config, "send_slack_webhook: webhook sent successfully")