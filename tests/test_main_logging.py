import io
import logging
import unittest

from main import TelegramTokenRedactionFilter, _redact_telegram_tokens


class TelegramTokenRedactionTests(unittest.TestCase):
    def setUp(self):
        self.token = "123456789:" + ("AbCdEfGhIjKlMnOpQrStUvWxYz0123456789" * 2)
        self.redacted = "[REDACTED_TELEGRAM_BOT_TOKEN]"

    def test_redacts_token_from_plain_text(self):
        result = _redact_telegram_tokens(f"Telegram rejected {self.token}")
        self.assertNotIn(self.token, result)
        self.assertIn(self.redacted, result)

    def test_filter_redacts_message_and_exception_traceback(self):
        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        handler.addFilter(TelegramTokenRedactionFilter())
        logger = logging.getLogger(f"token-redaction-test-{id(self)}")
        logger.handlers = []
        logger.propagate = False
        logger.setLevel(logging.ERROR)
        logger.addHandler(handler)
        self.addCleanup(logger.removeHandler, handler)

        logger.error("Rejected token %s", self.token)
        try:
            raise ValueError(f"Invalid credential: {self.token}")
        except ValueError:
            logger.exception("Bot initialization failed")

        output = stream.getvalue()
        self.assertNotIn(self.token, output)
        self.assertGreaterEqual(output.count(self.redacted), 2)


if __name__ == "__main__":
    unittest.main()
