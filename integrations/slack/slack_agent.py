#!/usr/bin/env python3
"""
Slack Agent entrypoint for St4bl / ARP.

Slack is a channel adapter. ARP remains the enforcement layer.
Never execute transfers directly from free-text Slack messages.
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

# Allow imports from repository root when run as a script.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("arp.slack_agent")

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

try:
    from slack_bolt import App
    from slack_bolt.adapter.socket_mode import SocketModeHandler
except ImportError:
    print(
        "Slack Bolt is not installed.\n"
        "Install Slack integration dependencies:\n"
        "  pip install -e \".[slack]\"\n"
        "Then configure SLACK_BOT_TOKEN and SLACK_APP_TOKEN in .env"
    )
    sys.exit(1)

from integrations.slack.handlers import dispatch_command

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN", "")
SLACK_SIGNING_SECRET = os.getenv("SLACK_SIGNING_SECRET", "")
SLACK_APP_TOKEN = os.getenv("SLACK_APP_TOKEN", "")
SLACK_ENABLE_SOCKET_MODE = os.getenv("SLACK_ENABLE_SOCKET_MODE", "true").lower() in (
    "1",
    "true",
    "yes",
)

app = App(token=SLACK_BOT_TOKEN, signing_secret=SLACK_SIGNING_SECRET or None)


@app.command("/st4bl")
def handle_st4bl_command(ack, command, respond):
    """Route /st4bl slash commands through ARP handlers."""
    ack()
    user_id = command.get("user_id", "slack-user")
    text = command.get("text", "")
    logger.info("Received /st4bl from user=%s text=%r", user_id, text)
    response = dispatch_command(text, user_id=user_id)
    respond(response)


def main() -> None:
    if not SLACK_BOT_TOKEN:
        logger.error("SLACK_BOT_TOKEN is not set. Copy .env.example to .env and configure Slack credentials.")
        sys.exit(1)

    logger.info("Starting St4bl / ARP Slack Agent")
    logger.info("Socket mode enabled: %s", SLACK_ENABLE_SOCKET_MODE)

    if SLACK_ENABLE_SOCKET_MODE:
        if not SLACK_APP_TOKEN:
            logger.error("SLACK_APP_TOKEN is required when SLACK_ENABLE_SOCKET_MODE=true")
            sys.exit(1)
        SocketModeHandler(app, SLACK_APP_TOKEN).start()
    else:
        logger.info("HTTP mode requires a public request URL configured in the Slack app settings.")
        logger.error("HTTP mode server bootstrap is not included in this scaffold. Use socket mode for local dev.")
        sys.exit(1)


if __name__ == "__main__":
    main()
