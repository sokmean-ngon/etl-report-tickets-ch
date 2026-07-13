from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from zoneinfo import ZoneInfo

from config import CRON_HOUR, CRON_MINUTE, TZ
from logger import get_logger
from sync import main as sync_job

logger = get_logger()

TIMEZONE = ZoneInfo(TZ)


class Scheduler:

    def __init__(self):
        self.scheduler = BlockingScheduler(timezone=TIMEZONE)

    def start(self):

        logger.info("=" * 80)
        logger.info("MySQL -> ClickHouse Synchronization Scheduler")
        logger.info("=" * 80)

        logger.info(
            f"Schedule : Every day at {CRON_HOUR:02d}:{CRON_MINUTE:02d}"
        )

        self.scheduler.add_job(
            sync_job,
            CronTrigger(
                hour=CRON_HOUR,
                minute=CRON_MINUTE,
            ),
            id="mysql_clickhouse_sync",
            replace_existing=True,
            max_instances=1,
            coalesce=True,
            misfire_grace_time=3600,
        )

        logger.info("Running first synchronization...")

        # Run immediately when the application starts
        sync_job()

        logger.info("Scheduler started.")

        try:
            self.scheduler.start()

        except (KeyboardInterrupt, SystemExit):
            logger.info("Scheduler stopped.")


def main():
    Scheduler().start()


if __name__ == "__main__":
    main()