import socket
from datetime import datetime

import requests

from config import (
    WEBHOOK_ENABLED,
    WEBHOOK_TIMEOUT,
    WEBHOOK_URL,
    WEBHOOK_TITLE,
)
from logger import get_logger

logger = get_logger()


class WebhookNotifier:

    @staticmethod
    def send(status, message, **kwargs):

        if not WEBHOOK_ENABLED:
            return

        if not WEBHOOK_URL:
            return

        payload = {
            "status": status,
            "title": WEBHOOK_TITLE,
            "message": message
        }

        payload.update(kwargs)

        try:

            requests.post(
                WEBHOOK_URL,
                json=payload,
                timeout=WEBHOOK_TIMEOUT,
            )

            logger.info(
                "Webhook notification sent."
            )

        except Exception as e:

            logger.error(
                f"Webhook notification failed: {e}"
            )