"""
Main logger for commonlog
"""
import logging
from .providers import SlackProvider, LarkProvider
from .log_types import AlertLevel, Attachment

# ====================
# Configuration and Logger
# ====================

class commonlog:
    def send_to_channel(self, level, message, attachment=None, trace="", channel=None):
        if level == AlertLevel.INFO:
            logging.info(message)
            return
        try:
            # Use provided channel or fallback to resolved channel
            target_channel = channel if channel else self._resolve_channel(level)
            original_channel = self.config.channel
            self.config.channel = target_channel
            if trace:
                if attachment is None:
                    attachment = Attachment(content=trace, file_name="trace.log")
                else:
                    if attachment.content:
                        attachment.content += "\n\n--- Trace Log ---\n" + trace
                    else:
                        attachment.content = trace
                        attachment.file_name = "trace.log"
            self.provider.send(level, message, attachment, self.config)
            self.config.channel = original_channel
        except Exception as e:
            logging.error(f"Failed to send alert: {e}")
            raise

    def custom_send(self, provider, level, message, attachment=None, trace="", channel=None):
        if provider == "slack":
            custom_provider = SlackProvider()
        elif provider == "lark":
            custom_provider = LarkProvider()
        else:
            logging.warning(f"Unknown provider: {provider}, defaulting to Slack")
            custom_provider = SlackProvider()

        if level == AlertLevel.INFO:
            logging.info(message)
            return
        try:
            # Use provided channel or fallback to resolved channel
            target_channel = channel if channel else self._resolve_channel(level)
            original_channel = self.config.channel
            self.config.channel = target_channel
            if trace:
                if attachment is None:
                    attachment = Attachment(content=trace, file_name="trace.log")
                else:
                    if attachment.content:
                        attachment.content += "\n\n--- Trace Log ---\n" + trace
                    else:
                        attachment.content = trace
                        attachment.file_name = "trace.log"
            custom_provider.send(level, message, attachment, self.config)
            self.config.channel = original_channel
        except Exception as e:
            logging.error(f"Failed to send alert: {e}")
            raise

    def __init__(self, config):
        self.config = config
        if config.provider == "slack":
            self.provider = SlackProvider()
        elif config.provider == "lark":
            self.provider = LarkProvider()
        else:
            logging.warning(f"Unknown provider: {config.provider}, defaulting to Slack")
            self.provider = SlackProvider()

    def _resolve_channel(self, level):
        if self.config.channel_resolver:
            return self.config.channel_resolver.resolve_channel(level)
        return self.config.channel

    def send(self, level, message, attachment=None, trace=""):
        if level == AlertLevel.INFO:
            logging.info(message)
            return
        try:
            # Resolve the channel for this alert level
            resolved_channel = self._resolve_channel(level)
            
            # Temporarily modify config with resolved channel
            original_channel = self.config.channel
            self.config.channel = resolved_channel
            
            # If trace is provided, create an attachment
            if trace:
                if attachment is None:
                    attachment = Attachment(content=trace, file_name="trace.log")
                else:
                    # If there's already an attachment, combine the trace content
                    if attachment.content:
                        attachment.content += "\n\n--- Trace Log ---\n" + trace
                    else:
                        attachment.content = trace
                        attachment.file_name = "trace.log"
            self.provider.send(level, message, attachment, self.config)
            
            # Restore original channel
            self.config.channel = original_channel
        except Exception as e:
            logging.error(f"Failed to send alert: {e}")
            raise