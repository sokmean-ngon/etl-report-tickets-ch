import mysql.connector

from config import (
    MYSQL,
    ID_COLUMN,
    DATE_COLUMN,
    BATCH_SIZE,
    SKIP_LAST_DAYS,
)


class MySQLReader:

    def __init__(self):
        self.conn = mysql.connector.connect(**MYSQL)
        self.cursor = self.conn.cursor(
            dictionary=True,
            buffered=True,
        )

    def get_tables(self):
        self.cursor.execute("SHOW TABLES")
        rows = self.cursor.fetchall()
        return [next(iter(row.values())) for row in rows]

    def get_columns(self, table):
        self.cursor.execute(f"SHOW COLUMNS FROM `{table}`")
        return self.cursor.fetchall()

    def fetch_batch(self, table, last_date, last_id):
        self.conn.ping(
            reconnect=True,
            attempts=3,
            delay=2,
        )

        sql = f"""
        SELECT *
        FROM `{table}`
        WHERE (
                `{DATE_COLUMN}` > %s
            OR (
                `{DATE_COLUMN}` = %s
                AND `{ID_COLUMN}` > %s
            )
        )
        AND `{DATE_COLUMN}` < CAST(
                DATE_FORMAT(
                    DATE_SUB(CURDATE(), INTERVAL %s DAY),
                    '%Y%m%d'
                ) AS UNSIGNED
            )
        ORDER BY
            `{DATE_COLUMN}`,
            `{ID_COLUMN}`
        LIMIT %s
        """

        self.cursor.execute(
            sql,
            (
                last_date,
                last_date,
                last_id,
                SKIP_LAST_DAYS,
                BATCH_SIZE,
            ),
        )

        rows = self.cursor.fetchall()

        new_last_date = last_date
        new_last_id = last_id

        if rows:
            checkpoint = rows[-1]

            new_last_date = checkpoint[DATE_COLUMN]
            new_last_id = checkpoint[ID_COLUMN]

        return rows, new_last_date, new_last_id

    def close(self):
        self.cursor.close()
        self.conn.close()