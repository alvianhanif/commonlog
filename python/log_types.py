"""
commonlog: Unified logging and alerting for Slack/Lark (Python)
"""
from abc import ABC, abstractmethod

class SendMethod:
    WEBCLIENT = "webclient"
    WEBHOOK = "webhook"

class AlertLevel:
    INFO = 0
    WARN = 1
    ERROR = 2

class Attachment:
    def __init__(self, url=None, file_name=None, content=None):
        self.url = url
        self.file_name = file_name
        self.content = content

class ChannelResolver(ABC):
    @abstractmethod
    def resolve_channel(self, level):
        pass

class DefaultChannelResolver(ChannelResolver):
    def __init__(self, channel_map=None, default_channel=None):
        self.channel_map = channel_map or {}
        self.default_channel = default_channel

    def resolve_channel(self, level):
        return self.channel_map.get(level, self.default_channel)

class LarkToken:
    def __init__(self, app_id=None, app_secret=None):
        self.app_id = app_id
        self.app_secret = app_secret

class Config:
    def __init__(self, provider, send_method, token=None, slack_token=None, lark_token=None, channel=None, channel_resolver=None, service_name=None, environment=None, redis_host=None, redis_port=None, debug=False):
        self.provider = provider
        self.send_method = send_method
        self.token = token
        self.slack_token = slack_token
        self.lark_token = lark_token
        self.channel = channel
        self.channel_resolver = channel_resolver
        self.service_name = service_name
        self.environment = environment
        self.redis_host = redis_host
        self.redis_port = redis_port
        self.debug = debug

class Provider(ABC):
    @abstractmethod
    def send_to_channel(self, level, message, attachment, config, channel):
        pass

# Debug logging
import logging

debug_logger = logging.getLogger('commonlog.debug')
debug_logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('[COMMONLOG DEBUG] %(filename)s:%(lineno)d - %(message)s'))
debug_logger.addHandler(handler)

def debug_log(config, message, *args):
    if hasattr(config, 'debug') and config.debug:
        debug_logger.debug(message, *args)