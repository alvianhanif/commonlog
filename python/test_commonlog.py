import unittest
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from logger import commonlog
from commonlog_types import Config, SendMethod, AlertLevel, Attachment

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

    def test_send_info(self):
        config = Config(provider="slack", send_method=SendMethod.WEBCLIENT)
        logger = commonlog(config)
        # INFO should not send
        logger.send(AlertLevel.INFO, "Test info", trace="")

if __name__ == '__main__':
    unittest.main()