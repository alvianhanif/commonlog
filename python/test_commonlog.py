import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import unittest
from unittest.mock import Mock, patch
from log_types import Config, SendMethod, AlertLevel, Attachment
from logger import commonlog

class Testcommonlog(unittest.TestCase):
    def test_init(self):
        config = Config(
            provider="slack",
            send_method=SendMethod.WEBCLIENT,
            token="dummy-token",
            channel="#test"
        )
        logger = commonlog(config)
        self.assertEqual(logger.config.provider, "slack")

    def test_init_with_lark(self):
        config = Config(
            provider="lark",
            send_method=SendMethod.WEBHOOK,
            lark_token=Mock(app_id="test", app_secret="secret"),
            channel="test-channel"
        )
        logger = commonlog(config)
        self.assertEqual(logger.config.provider, "lark")

    def test_init_with_unknown_provider(self):
        config = Config(
            provider="unknown",
            send_method=SendMethod.WEBCLIENT,
            token="dummy-token",
            channel="#test"
        )
        logger = commonlog(config)
        self.assertEqual(logger.config.provider, "unknown")
        # Should default to slack provider
        self.assertIsNotNone(logger.provider)

    def test_send_info(self):
        config = Config(provider="slack", send_method=SendMethod.WEBCLIENT)
        logger = commonlog(config)
        # INFO should not send
        logger.send(AlertLevel.INFO, "Test info", trace="")

    def test_send_warn(self):
        config = Config(
            provider="slack",
            send_method=SendMethod.WEBCLIENT,
            token="dummy-token",
            channel="#test"
        )
        logger = commonlog(config)
        # Mock the provider to avoid actual API calls
        with patch.object(logger.provider, 'send') as mock_send:
            logger.send(AlertLevel.WARN, "Test warn message")
            mock_send.assert_called_once()

    def test_send_error(self):
        config = Config(
            provider="slack",
            send_method=SendMethod.WEBCLIENT,
            token="dummy-token",
            channel="#test"
        )
        logger = commonlog(config)
        # Mock the provider to avoid actual API calls
        with patch.object(logger.provider, 'send') as mock_send:
            logger.send(AlertLevel.ERROR, "Test error message")
            mock_send.assert_called_once()

    def test_send_to_channel(self):
        config = Config(
            provider="slack",
            send_method=SendMethod.WEBCLIENT,
            token="dummy-token",
            channel="#default"
        )
        logger = commonlog(config)
        # Mock the provider to avoid actual API calls
        with patch.object(logger.provider, 'send_to_channel') as mock_send:
            logger.send_to_channel(AlertLevel.WARN, "Test message", channel="#custom")
            mock_send.assert_called_once()

    def test_send_with_attachment(self):
        config = Config(
            provider="slack",
            send_method=SendMethod.WEBCLIENT,
            token="dummy-token",
            channel="#test"
        )
        logger = commonlog(config)
        attachment = Attachment(file_name="test.txt", content="test content")
        # Mock the provider to avoid actual API calls
        with patch.object(logger.provider, 'send') as mock_send:
            logger.send(AlertLevel.ERROR, "Test with attachment", attachment=attachment)
            mock_send.assert_called_once()

    def test_send_with_trace(self):
        config = Config(
            provider="slack",
            send_method=SendMethod.WEBCLIENT,
            token="dummy-token",
            channel="#test"
        )
        logger = commonlog(config)
        trace = "stack trace here"
        # Mock the provider to avoid actual API calls
        with patch.object(logger.provider, 'send') as mock_send:
            logger.send(AlertLevel.ERROR, "Test with trace", trace=trace)
            mock_send.assert_called_once()

    def test_send_with_attachment_and_trace(self):
        config = Config(
            provider="slack",
            send_method=SendMethod.WEBCLIENT,
            token="dummy-token",
            channel="#test"
        )
        logger = commonlog(config)
        attachment = Attachment(file_name="test.txt", content="test content")
        trace = "stack trace here"
        # Mock the provider to avoid actual API calls
        with patch.object(logger.provider, 'send') as mock_send:
            logger.send(AlertLevel.ERROR, "Test with attachment and trace", attachment=attachment, trace=trace)
            mock_send.assert_called_once()

    def test_send_to_channel_with_trace(self):
        config = Config(
            provider="slack",
            send_method=SendMethod.WEBCLIENT,
            token="dummy-token",
            channel="#test"
        )
        logger = commonlog(config)
        trace = "stack trace here"
        # Mock the provider to avoid actual API calls
        with patch.object(logger.provider, 'send_to_channel') as mock_send:
            logger.send_to_channel(AlertLevel.ERROR, "Test with trace", trace=trace, channel="#custom")
            mock_send.assert_called_once()

    def test_custom_send(self):
        config = Config(
            provider="slack",
            send_method=SendMethod.WEBCLIENT,
            token="dummy-token",
            channel="#test"
        )
        logger = commonlog(config)
        # Mock the LarkProvider.send method to avoid Redis connection
        with patch('providers.LarkProvider.send') as mock_send:
            logger.custom_send("lark", AlertLevel.ERROR, "Custom provider test")
            mock_send.assert_called_once()

    def test_custom_send_unknown_provider(self):
        config = Config(
            provider="slack",
            send_method=SendMethod.WEBCLIENT,
            token="dummy-token",
            channel="#test"
        )
        logger = commonlog(config)
        # Should default to Slack for unknown provider without raising exception
        with patch('providers.SlackProvider.send') as mock_send:
            logger.custom_send("unknown", AlertLevel.ERROR, "Unknown provider test")
            mock_send.assert_called_once()

    def test_resolve_channel_with_resolver(self):
        from log_types import DefaultChannelResolver
        resolver = DefaultChannelResolver(
            channel_map={AlertLevel.ERROR: "#errors", AlertLevel.WARN: "#warnings"},
            default_channel="#general"
        )
        config = Config(
            provider="slack",
            send_method=SendMethod.WEBCLIENT,
            token="dummy-token",
            channel="#default",
            channel_resolver=resolver
        )
        logger = commonlog(config)

        # Test ERROR level resolution
        error_channel = logger._resolve_channel(AlertLevel.ERROR)
        self.assertEqual(error_channel, "#errors")

        # Test WARN level resolution
        warn_channel = logger._resolve_channel(AlertLevel.WARN)
        self.assertEqual(warn_channel, "#warnings")

        # Test INFO level resolution (should use default)
        info_channel = logger._resolve_channel(AlertLevel.INFO)
        self.assertEqual(info_channel, "#general")

    def test_resolve_channel_without_resolver(self):
        config = Config(
            provider="slack",
            send_method=SendMethod.WEBCLIENT,
            token="dummy-token",
            channel="#default"
        )
        logger = commonlog(config)

        channel = logger._resolve_channel(AlertLevel.ERROR)
        self.assertEqual(channel, "#default")

    def test_send_error_handling(self):
        config = Config(
            provider="slack",
            send_method=SendMethod.WEBCLIENT,
            token="dummy-token",
            channel="#test"
        )
        logger = commonlog(config)
        # Mock the provider to raise an exception
        with patch.object(logger.provider, 'send', side_effect=Exception("Test error")):
            with self.assertRaises(Exception):
                logger.send(AlertLevel.ERROR, "Test message")

    def test_send_to_channel_error_handling(self):
        config = Config(
            provider="slack",
            send_method=SendMethod.WEBCLIENT,
            token="dummy-token",
            channel="#test"
        )
        logger = commonlog(config)
        # Mock the provider to raise an exception
        with patch.object(logger.provider, 'send_to_channel', side_effect=Exception("Test error")):
            with self.assertRaises(Exception):
                logger.send_to_channel(AlertLevel.ERROR, "Test message", channel="#custom")

    def test_custom_send_error_handling(self):
        config = Config(
            provider="slack",
            send_method=SendMethod.WEBCLIENT,
            token="dummy-token",
            channel="#test"
        )
        logger = commonlog(config)
        # Mock the provider to raise an exception
        with patch('providers.LarkProvider.send', side_effect=Exception("Test error")):
            with self.assertRaises(Exception):
                logger.custom_send("lark", AlertLevel.ERROR, "Test message")

if __name__ == '__main__':
    unittest.main()