import time
import signal

from config import (TABLES, MAX_RETRIES)
from logger import get_logger
from state import State
from mysql_reader import MySQLReader
from clickhouse_writer import ClickHouseWriter
from notifier import WebhookNotifier

logger = get_logger()

running = True


def stop(signum, frame):
    global running
    logger.warning("Stopping sync...")
    running = False


signal.signal(signal.SIGINT, stop)
signal.signal(signal.SIGTERM, stop)


class SyncEngine:

    def __init__(self):

        self.mysql = MySQLReader()
        self.clickhouse = ClickHouseWriter()
        self.state = State()

    def get_tables(self):

        if TABLES:
            return TABLES

        return self.mysql.get_tables()

    def sync_table(self, table):

        logger.info("=" * 80)
        logger.info(f"Start syncing [{table}]")

        last_date, last_id = self.state.get_checkpoint(table)

        logger.info(
            f"Resume from Date={last_date} "
            f"ID={last_id}"
        )

        total_rows = 0
        batch = 0
        start = time.time()

        while running:

            rows, new_last_date, new_last_id = self.mysql.fetch_batch(
                table,
                last_date,
                last_id,
            )

            if not rows:
                break

            retry = 0

            while retry < MAX_RETRIES:

                try:

                    self.clickhouse.insert_rows(
                        table,
                        rows
                    )

                    # save checkpoint ONLY after insert success
                    self.state.save_checkpoint(
                        table,
                        new_last_date,
                        new_last_id,
                    )

                    break

                except Exception as e:

                    retry += 1

                    logger.error(
                        f"{table} batch failed "
                        f"(retry {retry}/{MAX_RETRIES}): {e}"
                    )

                    time.sleep(2 ** retry)

            else:

                message = f"{table}: maximum retries reached."

                logger.error(message)

                raise RuntimeError(message)

            batch += 1
            total_rows += len(rows)

            last_date = new_last_date
            last_id = new_last_id

            logger.info(
                f"[{table}] "
                f"Batch={batch:,} "
                f"Rows={len(rows):,} "
                f"LastDate={last_date} "
                f"LastID={last_id:,}"
            )

        elapsed = max(time.time() - start, 1)

        logger.info("-" * 80)
        logger.info(
            f"Completed [{table}]"
        )
        logger.info(
            f"Rows      : {total_rows:,}"
        )
        logger.info(
            f"Batches   : {batch:,}"
        )
        logger.info(
            f"Duration  : {elapsed:.2f}s"
        )
        logger.info(
            f"Speed     : {int(total_rows/elapsed):,} rows/sec"
        )

    def sync_all(self):

        success = True

        tables = self.get_tables()

        logger.info(
            f"Total tables : {len(tables)}"
        )

        for table in tables:

            if not running:
                break

            try:

                self.sync_table(table)

            except Exception as e:

                success = False

                logger.exception(
                    f"Failed syncing table {table}: {e}"
                )

        logger.info("All synchronization completed.")

        return success

    def close(self):

        self.mysql.close()
        self.clickhouse.close()


def main():

    start = time.time()

    engine = SyncEngine()

    try:

        success = engine.sync_all()

        elapsed = round(time.time() - start, 2)

        WebhookNotifier.send(
            status="SUCCESS" if success else "FAILED",
            message=(
                "Synchronization completed successfully."
                if success
                else "Synchronization completed with errors."
            ),
            duration_seconds=elapsed,
        )

    except Exception as e:

        elapsed = round(time.time() - start, 2)

        WebhookNotifier.send(
            status="FAILED",
            message=str(e),
            duration_seconds=elapsed,
        )

        raise

    finally:

        engine.close()


if __name__ == "__main__":

    main()