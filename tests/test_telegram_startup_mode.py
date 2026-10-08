import unittest
from unittest.mock import patch

from telegram.error import InvalidToken

import main


class TelegramStartupModeTests(unittest.TestCase):
    def test_invalid_token_is_degraded_not_fatal(self):
        self.assertEqual(main.telegram_startup_mode(InvalidToken("Unauthorized")), "disabled_invalid_token")

    def test_unrelated_error_remains_fatal(self):
        self.assertEqual(main.telegram_startup_mode(RuntimeError("network")), "fatal")


if __name__ == "__main__":
    unittest.main()
