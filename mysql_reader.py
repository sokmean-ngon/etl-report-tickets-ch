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
        self.cursor = self.conn.cursor(dictionary=True)

    def get_tables(self):
        self.cursor.execute("SHOW TABLES")
        return [list(row.values())[0] for row in self.cursor.fetchall()]

    def get_columns(self, table):
        self.cursor.execute(f"SHOW COLUMNS FROM `{table}`")
        return self.cursor.fetchall()

    def fetch_batch(self, table, last_id):

        sql = f"""
        SELECT *
        FROM `{table}`
        WHERE `{ID_COLUMN}` > %s
        AND `{DATE_COLUMN}` < CAST(
                DATE_FORMAT(
                    DATE_SUB(CURDATE(), INTERVAL %s DAY),
                    '%Y%m%d'
                ) AS UNSIGNED
            )
        ORDER BY `{ID_COLUMN}`
        LIMIT %s
        """

        self.cursor.execute(
            sql,
            (
                last_id,
                SKIP_LAST_DAYS,
                BATCH_SIZE,
            ),
        )

        rows = self.cursor.fetchall()

        if rows:
            last_id = rows[-1][ID_COLUMN]

        return rows, last_id

    def count_remaining(self, table, last_id):
        sql = f"""
        SELECT COUNT(*)
        FROM `{table}`
        WHERE `{ID_COLUMN}` > %s
          AND `{DATE_COLUMN}` < DATE_SUB(NOW(), INTERVAL %s DAY)
        """

        self.cursor.execute(sql, (last_id, SKIP_LAST_DAYS))

        return self.cursor.fetchone()["COUNT(*)"]

    def close(self):
        self.cursor.close()
        self.conn.close()