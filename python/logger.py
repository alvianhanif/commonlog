"""
Main logger for commonlog
"""
import logging
import sys
import os

# Add current directory to path for direct imports
_current_dir = os.path.dirname(os.path.abspath(__file__))
if _current_dir not in sys.path:
    sys.path.insert(0, _current_dir)

from providers import SlackProvider, LarkProvider
from log_types import AlertLevel, Attachment, debug_log

# ====================
# Configuration and Logger
# ====================

class commonlog:
    def send_to_channel(self, level, message, attachment=None, trace="", channel=None):
        debug_log(self.config, f"send_to_channel called with level: {level}, message length: {len(message)}, channel: {channel}, has attachment: {attachment is not None}, has trace: {bool(trace)}")
        
        if level == AlertLevel.INFO:
            logging.info(message)
            debug_log(self.config, "INFO level message logged locally, skipping provider send")
            return
        try:
            # Use provided channel or fallback to resolved channel
            target_channel = channel if channel else self._resolve_channel(level)
            if channel is None:
                debug_log(self.config, f"Resolved channel using resolver: {target_channel}")
            else:
                debug_log(self.config, f"Using provided channel: {target_channel}")
            
            original_channel = self.config.channel
            self.config.channel = target_channel
            if trace:
                debug_log(self.config, f"Processing trace attachment, trace length: {len(trace)}")
                if attachment is None:
                    attachment = Attachment(content=trace, file_name="trace.log")
                    debug_log(self.config, "Created new trace attachment")
                else:
                    if attachment.content:
                        attachment.content += "\n\n--- Trace Log ---\n" + trace
                        debug_log(self.config, "Appended trace to existing attachment content")
                    else:
                        attachment.content = trace
                        attachment.file_name = "trace.log"
                        debug_log(self.config, "Set trace as attachment content")
            
            debug_log(self.config, f"Calling provider.send_to_channel with resolved channel: {target_channel}")
            self.provider.send_to_channel(level, message, attachment, self.config, target_channel)
            self.config.channel = original_channel
            debug_log(self.config, "Provider send_to_channel completed successfully")
        except Exception as e:
            debug_log(self.config, f"Provider send_to_channel failed: {e}")
            logging.error(f"Failed to send alert: {e}")
            raise

    def custom_send(self, provider, level, message, attachment=None, trace="", channel=None):
        debug_log(self.config, f"custom_send called with custom provider: {provider}, level: {level}, message length: {len(message)}")
        
        if provider == "slack":
            custom_provider = SlackProvider()
        elif provider == "lark":
            custom_provider = LarkProvider()
        else:
            logging.warning(f"Unknown provider: {provider}, defaulting to Slack")
            custom_provider = SlackProvider()
            debug_log(self.config, f"Unknown provider '{provider}', defaulted to slack")
        
        debug_log(self.config, f"Created custom provider: {provider}")

        if level == AlertLevel.INFO:
            logging.info(message)
            debug_log(self.config, "INFO level message logged locally for custom provider, skipping send")
            return
        try:
            # Use provided channel or fallback to resolved channel
            target_channel = channel if channel else self._resolve_channel(level)
            debug_log(self.config, f"Resolved channel for custom send: {target_channel}")
            
            original_channel = self.config.channel
            self.config.channel = target_channel
            if trace:
                debug_log(self.config, f"Processing trace for custom send, trace length: {len(trace)}")
                if attachment is None:
                    attachment = Attachment(content=trace, file_name="trace.log")
                else:
                    if attachment.content:
                        attachment.content += "\n\n--- Trace Log ---\n" + trace
                    else:
                        attachment.content = trace
                        attachment.file_name = "trace.log"
            debug_log(self.config, f"Calling custom provider.send with provider: {provider}, channel: {target_channel}")
            custom_provider.send(level, message, attachment, self.config)
            self.config.channel = original_channel
            debug_log(self.config, "Custom provider send completed successfully")
        except Exception as e:
            debug_log(self.config, f"Custom provider send failed: {e}")
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
        
        debug_log(config, f"Created logger with provider: {config.provider}, send method: {config.send_method}, debug: {config.debug}")

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