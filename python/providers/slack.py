"""
Slack Provider for commonlog
"""
import requests
from ..log_types import SendMethod, Provider

class SlackProvider(Provider):
    def send_to_channel(self, level, message, attachment, config, channel):
        original_channel = config.channel
        config.channel = channel
        self.send(level, message, attachment, config)
        config.channel = original_channel

    def send(self, level, message, attachment, config):
        formatted_message = self._format_message(message, attachment, config)
        if config.send_method == SendMethod.WEBCLIENT:
            self._send_slack_webclient(formatted_message, config)
        elif config.send_method == SendMethod.WEBHOOK:
            self._send_slack_webhook(formatted_message, config)
        else:
            raise ValueError(f"Unknown send method for Slack: {config.send_method}")

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
        # Use slack_token if available, otherwise fall back to token
        token = config.token
        if config.slack_token:
            token = config.slack_token
        
        url = "https://slack.com/api/chat.postMessage"
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json; charset=utf-8"}
        payload = {"channel": config.channel, "text": formatted_message}
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code != 200:
            raise Exception(f"Slack WebClient response: {response.status_code}")

    def _send_slack_webhook(self, formatted_message, config):
        # For webhook, the token field contains the webhook URL
        webhook_url = config.token
        if not webhook_url:
            raise Exception("Webhook URL is required for Slack webhook method")
        
        payload = {"text": formatted_message}
        # If channel is specified, include it in the payload
        if config.channel:
            payload["channel"] = config.channel
        
        response = requests.post(webhook_url, json=payload)
        if response.status_code != 200:
            raise Exception(f"Slack webhook response: {response.status_code}")