import os

from dotenv import load_dotenv

load_dotenv()

MYSQL = {
    "host": os.getenv("MYSQL_HOST"),
    "port": int(os.getenv("MYSQL_PORT", 3306)),
    "database": os.getenv("MYSQL_DATABASE"),
    "user": os.getenv("MYSQL_USER"),
    "password": os.getenv("MYSQL_PASSWORD"),
}

CLICKHOUSE = {
    "host": os.getenv("CH_HOST"),
    "port": int(os.getenv("CH_PORT", 8123)),
    "database": os.getenv("CH_DATABASE"),
    "username": os.getenv("CH_USER"),
    "password": os.getenv("CH_PASSWORD"),
}

TABLES = [
    x.strip()
    for x in os.getenv("TABLES", "").split(",")
    if x.strip()
]

ID_COLUMN = os.getenv("ID_COLUMN", "id")

DATE_COLUMN = os.getenv("DATE_COLUMN", "report_in_day")

SKIP_LAST_DAYS = int(os.getenv("SKIP_LAST_DAYS", 2))

BATCH_SIZE = int(os.getenv("BATCH_SIZE", 10000))

CRON_HOUR = int(os.getenv("CRON_HOUR", 2))

CRON_MINUTE = int(os.getenv("CRON_MINUTE", 0))

STATE_FILE = os.getenv("STATE_FILE", "state.json")

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

CH_ENGINE = os.getenv("CH_ENGINE", "ReplacingMergeTree")

WEBHOOK_TITLE = os.getenv("WEBHOOK_TITLE", "ETL")

WEBHOOK_ENABLED = os.getenv("WEBHOOK_ENABLED", "false").lower() == "true"

WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")

WEBHOOK_TIMEOUT = int(
    os.getenv("WEBHOOK_TIMEOUT", "30")
)

TZ = os.getenv("TZ", "UTC")