# main.py - Video Agent v1.2 Deployment Foundation - Production entrypoint
# Combines: persistence init + health server + telegram bot
# No hardcoded secrets, fail-fast on BOT_TOKEN missing

import os
import asyncio
import signal
import logging
import re
from telegram.error import InvalidToken
from dotenv import load_dotenv

# Load .env if exists (dev), but env vars take precedence (prod)
load_dotenv()

from persistence.repository import get_repository
from health import start_health_server

# Import bot components from bot.py v1.1 (we reuse behavior)
import bot as bot_module


_TELEGRAM_TOKEN_PATTERN = re.compile(r"\b\d{6,12}:[A-Za-z0-9_-]{20,}\b")
_REDACTED_TOKEN = "[REDACTED_TELEGRAM_BOT_TOKEN]"


def _redact_telegram_tokens(value):
    """Redact Telegram bot tokens from any log message or rendered traceback."""
    if not isinstance(value, str):
        return value
    return _TELEGRAM_TOKEN_PATTERN.sub(_REDACTED_TOKEN, value)


class TelegramTokenRedactionFilter(logging.Filter):
    """Prevent library exceptions from writing bot tokens into platform logs."""

    def filter(self, record):
        try:
            message = record.getMessage()
        except Exception:
            message = str(record.msg)
        record.msg = _redact_telegram_tokens(message)
        record.args = ()

        if record.exc_info:
            try:
                rendered_exception = logging.Formatter().formatException(record.exc_info)
            except Exception:
                rendered_exception = "[exception details suppressed]"
            record.exc_text = _redact_telegram_tokens(rendered_exception)
            record.exc_info = None
        elif record.exc_text:
            record.exc_text = _redact_telegram_tokens(record.exc_text)
        return True


def configure_secret_redaction():
    """Attach token redaction to existing handlers before third-party bot startup."""
    redactor = TelegramTokenRedactionFilter()
    root = logging.getLogger()
    if not root.handlers:
        logging.basicConfig(level=logging.INFO)
    for handler in root.handlers:
        handler.addFilter(redactor)

    # Some libraries install their own handlers instead of propagating to root.
    for logger in logging.root.manager.loggerDict.values():
        if isinstance(logger, logging.Logger):
            for handler in logger.handlers:
                handler.addFilter(redactor)


def get_bot_token():
    return bot_module.get_bot_token()


def telegram_startup_mode(error):
    """Classify Telegram startup failures without hiding unrelated failures."""
    if isinstance(error, InvalidToken):
        return "disabled_invalid_token"
    return "fatal"


async def main():
    configure_secret_redaction()
    print("=== Video Agent v1.2 Deployment Foundation Starting ===")

    # 1. Persistence init
    db_path = os.getenv("DATABASE_PATH", "./data/video_agent.db")
    print(f"Initializing persistence: {db_path}")
    repo = get_repository(db_path=db_path)
    try:
        repo.init_schema()
        print("Persistence schema initialized")
        if not repo.health_check():
            raise RuntimeError("Persistence health check failed after init")
        print("Persistence health: ok")
    except Exception as e:
        print(f"FATAL: Persistence init failed: {e}")
        # Health endpoint will report 503
        raise

    # 2. Health server - non-blocking
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    print(f"Starting health server on {host}:{port}")
    health_server, health_thread = start_health_server(lambda: repo, host=host, port=port)
    print(f"Health endpoint: http://{host}:{port}/health")

    # 3. Telegram bot - fail-fast on BOT_TOKEN missing (already in get_bot_token)
    print("Initializing Telegram bot...")
    application = None
    telegram_enabled = True
    try:
        application = bot_module.build_application()
        print("Telegram bot initialized - BOT_TOKEN present")
    except RuntimeError as e:
        print(f"FATAL: {e}")
        raise
    except Exception as e:
        if telegram_startup_mode(e) == "disabled_invalid_token":
            telegram_enabled = False
            print("WARNING: Telegram BOT_TOKEN rejected by Telegram; continuing in degraded web/health mode.")
        else:
            print(f"FATAL: Bot init failed: {e}")
            raise

    # 4. Start Telegram polling and keep the service alive.
    stop_event = asyncio.Event()

    def handle_shutdown(signum, frame):
        print(f"Received signal {signum}, shutting down gracefully...")
        stop_event.set()

    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)

    if telegram_enabled and application is not None:
        print("Initializing Telegram polling...")
        try:
            await application.initialize()
            await application.start()
            if application.updater is None:
                raise RuntimeError("Telegram updater is unavailable; cannot start polling")
            await application.updater.start_polling()
            print("Telegram polling active")
        except InvalidToken:
            telegram_enabled = False
            print("WARNING: Telegram BOT_TOKEN rejected during startup; continuing in degraded web/health mode.")
        except Exception as e:
            print(f"FATAL: Telegram startup failed: {e}")
            raise
    print("=== Video Agent v1.2 Ready ===")
    print("Health: GET /health")
    print(f"Bot: {'Telegram polling active' if telegram_enabled else 'disabled (invalid token)'}")
    print("Persistence: SQLite local - migration path to Postgres in DEPLOYMENT.md")
    print("Publisher: Evidence Gate enforced")

    try:
        await stop_event.wait()
    finally:
        if application and application.updater and application.updater.running:
            await application.updater.stop()
        if application and application.running:
            await application.stop()
        if application and application.initialized:
            await application.shutdown()
        health_server.shutdown()
        if hasattr(repo, "close"):
            repo.close()

    return {"status": "STOPPED"}


if __name__ == "__main__":
    asyncio.run(main())
