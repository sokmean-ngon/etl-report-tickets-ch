import logging

from config import LOG_LEVEL


def get_logger():

    logging.basicConfig(
        level=LOG_LEVEL,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("logs/sync.log")
        ],
    )

    return logging.getLogger("mysql-sync")