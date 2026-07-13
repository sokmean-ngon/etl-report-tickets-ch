from logger import get_logger
from scheduler import Scheduler

logger = get_logger()


def main():

    logger.info("=" * 80)
    logger.info("MySQL -> ClickHouse Sync Service")
    logger.info("=" * 80)

    Scheduler().start()


if __name__ == "__main__":
    main()