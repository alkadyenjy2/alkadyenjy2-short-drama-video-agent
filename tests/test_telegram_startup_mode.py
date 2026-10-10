import unittest

from telegram.error import InvalidToken

import main


class TelegramStartupModeTests(unittest.TestCase):
    def test_missing_token_is_degraded_not_fatal(self):
        error = RuntimeError("BOT_TOKEN is missing. Set BOT_TOKEN in environment.")
        self.assertEqual(main.telegram_startup_mode(error), "disabled_missing_token")

    def test_invalid_token_is_degraded_not_fatal(self):
        self.assertEqual(main.telegram_startup_mode(InvalidToken("Unauthorized")), "disabled_invalid_token")

    def test_unrelated_error_remains_fatal(self):
        self.assertEqual(main.telegram_startup_mode(RuntimeError("network")), "fatal")


if __name__ == "__main__":
    unittest.main()
