import unittest
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from logger import Unilog
from unilog_types import Config, SendMethod, AlertLevel, Attachment

class TestUnilog(unittest.TestCase):
    def test_init(self):
        config = Config(
            provider="slack",
            send_method=SendMethod.WEBHOOK,
            webhook_url="https://example.com",
            channel="#test"
        )
        logger = Unilog(config)
        self.assertEqual(logger.config.provider, "slack")

    def test_send_info(self):
        config = Config(provider="slack", send_method=SendMethod.WEBHOOK)
        logger = Unilog(config)
        # INFO should not send
        logger.send(AlertLevel.INFO, "Test info", trace="")

if __name__ == '__main__':
    unittest.main()