"""
Lark Provider for unilog
"""
import requests
import json
from ..unilog_types import SendMethod, Provider

class LarkProvider(Provider):
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
        url = "https://open.larksuite.com/open-apis/im/v1/messages"
        headers = {"Authorization": f"Bearer {config.token}", "Content-Type": "application/json"}
        content = json.dumps({"text": formatted_message})
        payload = {"receive_id": config.channel, "msg_type": "text", "content": content}
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code != 200:
            raise Exception(f"Lark WebClient response: {response.status_code}")