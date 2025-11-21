"""
Slack Provider for unilog
"""
import requests
from ..unilog_types import SendMethod, Provider

class SlackProvider(Provider):
    def send(self, level, message, attachment, config):
        formatted_message = self._format_message(message, attachment, config)
        if config.send_method == SendMethod.WEBHOOK:
            self._send_slack_webhook(formatted_message, config)
        elif config.send_method == SendMethod.HTTP:
            self._send_slack_http(formatted_message, config)
        elif config.send_method == SendMethod.WEBCLIENT:
            self._send_slack_webclient(formatted_message, config)
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
            filename = attachment.file_name or "attachment.txt"
            formatted += f"\n\n*{filename}:*\n```\n{attachment.content}\n```"
        if attachment and attachment.url:
            formatted += f"\n\n*Attachment:* {attachment.url}"

        return formatted

    def _send_slack_webhook(self, formatted_message, config):
        payload = {"text": formatted_message, "channel": config.channel}
        response = requests.post(config.webhook_url, json=payload)
        if response.status_code != 200:
            raise Exception(f"Slack webhook response: {response.status_code}")

    def _send_slack_http(self, formatted_message, config):
        payload = {"text": formatted_message}
        response = requests.post(config.http_url, json=payload)
        if response.status_code != 200:
            raise Exception(f"Slack HTTP response: {response.status_code}")

    def _send_slack_webclient(self, formatted_message, config):
        url = "https://slack.com/api/chat.postMessage"
        headers = {"Authorization": f"Bearer {config.token}", "Content-Type": "application/json"}
        payload = {"channel": config.channel, "text": formatted_message}
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code != 200:
            raise Exception(f"Slack WebClient response: {response.status_code}")