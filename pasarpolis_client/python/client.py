"""
Pasarpolis Alert Client

A simplified client for pasarpolis services to send alerts to Lark and Slack
with sensible defaults.
"""

from typing import Optional, Callable
from enum import Enum
import logging

from unilog.python import Unilog, Config, SendMethod, AlertLevel, DefaultChannelResolver, Attachment


class Environment(str, Enum):
    DEV = "dev"
    STAGING = "staging"
    PRODUCTION = "production"
    UNITTEST = "unittest"


class Provider(str, Enum):
    LARK = "lark"
    SLACK = "slack"


class Client:
    """
    Main client for sending alerts with pasarpolis defaults.
    """

    def __init__(self, logger: Unilog, config: Config):
        self.logger = logger
        self.config = config

    @classmethod
    def create(cls, service_name: str, env: Environment, provider: Provider) -> 'Client':
        """
        Create a new pasarpolis alert client with sensible defaults.

        Args:
            service_name: Name of the service
            env: Environment (dev, staging, production)
            provider: Alert provider (lark or slack)

        Returns:
            Configured Client instance

        Raises:
            ValueError: If required environment variables are not set
        """
        config = Config(
            provider=provider.value,
            send_method=SendMethod.WEBHOOK,  # Default to webhook for simplicity
            service_name=service_name,
            environment=env.value,
        )

        # Set up default channel resolver based on environment
        resolver = cls._get_default_channel_resolver(env)
        config.channel_resolver = resolver

        # Set default send method and credentials based on provider
        if provider == Provider.LARK:
            config.send_method = SendMethod.WEBHOOK
            # Default Lark webhook URL - should be configured via environment variables
            if env == Environment.UNITTEST:
                config.webhook_url = "unittest://dummy-lark"
            else:
                webhook_url = cls._get_env_var("PASARPOLIS_LARK_WEBHOOK_URL")
                if webhook_url:
                    config.webhook_url = webhook_url
                else:
                    raise ValueError("PASARPOLIS_LARK_WEBHOOK_URL environment variable not set")
        elif provider == Provider.SLACK:
            config.send_method = SendMethod.WEBHOOK
            # Default Slack webhook URL - should be configured via environment variables
            if env == Environment.UNITTEST:
                config.webhook_url = "unittest://dummy-slack"
            else:
                webhook_url = cls._get_env_var("PASARPOLIS_SLACK_WEBHOOK_URL")
                if webhook_url:
                    config.webhook_url = webhook_url
                else:
                    raise ValueError("PASARPOLIS_SLACK_WEBHOOK_URL environment variable not set")
        else:
            raise ValueError(f"Unsupported provider: {provider}")

        logger = Unilog(config)
        return cls(logger, config)

    @classmethod
    def create_with_config(
        cls,
        service_name: str,
        env: Environment,
        provider: Provider,
        config_modifier: Optional[Callable[[Config], None]] = None
    ) -> 'Client':
        """
        Create a client with custom configuration.

        Args:
            service_name: Name of the service
            env: Environment
            provider: Alert provider
            config_modifier: Optional function to modify the config

        Returns:
            Configured Client instance
        """
        client = cls.create(service_name, env, provider)

        if config_modifier:
            config_modifier(client.config)
            # Recreate logger with modified config
            client.logger = Unilog(client.config)

        return client

    def _send_or_log(self, level: AlertLevel, level_name: str, message: str, attachment: Optional[Attachment] = None, trace: str = "") -> None:
        """Helper method to send alert or log for unittest environment."""
        if self.config.environment == Environment.UNITTEST.value:
            log_method = getattr(logging, level_name.lower())
            if attachment and trace:
                log_method(f"[{level_name}] {message} (attachment: {attachment.file_name})\nTrace: {trace}")
            elif attachment:
                log_method(f"[{level_name}] {message} (attachment: {attachment.file_name})")
            elif trace:
                log_method(f"[{level_name}] {message}\nTrace: {trace}")
            else:
                log_method(f"[{level_name}] {message}")
            return
        self.logger.send(level, message, attachment, trace)

    def send_info(self, message: str) -> None:
        """Send an info-level alert (logs only)."""
        self._send_or_log(AlertLevel.INFO, "INFO", message)

    def send_warn(self, message: str) -> None:
        """Send a warning-level alert."""
        self._send_or_log(AlertLevel.WARN, "WARNING", message)

    def send_warn_with_attachment(self, message: str, attachment: Attachment) -> None:
        """Send a warning-level alert with attachment."""
        self._send_or_log(AlertLevel.WARN, "WARNING", message, attachment)

    def send_warn_with_trace(self, message: str, trace: str) -> None:
        """Send a warning-level alert with trace."""
        self._send_or_log(AlertLevel.WARN, "WARNING", message, None, trace)

    def send_error(self, message: str) -> None:
        """Send an error-level alert."""
        self._send_or_log(AlertLevel.ERROR, "ERROR", message)

    def send_error_with_attachment(self, message: str, attachment: Attachment) -> None:
        """Send an error-level alert with attachment."""
        self._send_or_log(AlertLevel.ERROR, "ERROR", message, attachment)

    def send_error_with_trace(self, message: str, trace: str) -> None:
        """Send an error-level alert with trace."""
        self._send_or_log(AlertLevel.ERROR, "ERROR", message, None, trace)

    def send_error_with_attachment_and_trace(self, message: str, attachment: Attachment, trace: str) -> None:
        """Send an error-level alert with both attachment and trace."""
        self._send_or_log(AlertLevel.ERROR, "ERROR", message, attachment, trace)

    @staticmethod
    def _get_default_channel_resolver(env: Environment) -> DefaultChannelResolver:
        """Get appropriate channel mappings for each environment."""
        if env == Environment.PRODUCTION:
            return DefaultChannelResolver(
                channel_map={
                    AlertLevel.INFO: "#pasarpolis-general",
                    AlertLevel.WARN: "#pasarpolis-warnings",
                    AlertLevel.ERROR: "#pasarpolis-alerts",
                },
                default_channel="#pasarpolis-general"
            )
        elif env == Environment.STAGING:
            return DefaultChannelResolver(
                channel_map={
                    AlertLevel.INFO: "#pasarpolis-staging-general",
                    AlertLevel.WARN: "#pasarpolis-staging-warnings",
                    AlertLevel.ERROR: "#pasarpolis-staging-alerts",
                },
                default_channel="#pasarpolis-staging-general"
            )
        elif env == Environment.DEV:
            return DefaultChannelResolver(
                channel_map={
                    AlertLevel.INFO: "#pasarpolis-dev-general",
                    AlertLevel.WARN: "#pasarpolis-dev-warnings",
                    AlertLevel.ERROR: "#pasarpolis-dev-alerts",
                },
                default_channel="#pasarpolis-dev-general"
            )
        elif env == Environment.UNITTEST:
            return DefaultChannelResolver(
                channel_map={
                    AlertLevel.INFO: "#pasarpolis-unittest-general",
                    AlertLevel.WARN: "#pasarpolis-unittest-warnings",
                    AlertLevel.ERROR: "#pasarpolis-unittest-alerts",
                },
                default_channel="#pasarpolis-unittest-general"
            )
        else:
            return DefaultChannelResolver(default_channel="#pasarpolis-general")

    @staticmethod
    def _get_env_var(key: str) -> Optional[str]:
        """Get environment variable."""
        import os
        return os.getenv(key)