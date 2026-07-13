import clickhouse_connect

from config import CLICKHOUSE

from schema import SchemaConverter


class ClickHouseWriter:

    def __init__(self):

        self.client = clickhouse_connect.get_client(
            host=CLICKHOUSE["host"],
            port=CLICKHOUSE["port"],
            username=CLICKHOUSE["username"],
            password=CLICKHOUSE["password"],
            database=CLICKHOUSE["database"],
        )

        self.schema = SchemaConverter()

    def table_exists(self, table):

        sql = f"EXISTS TABLE {table}"

        return self.client.command(sql) == 1

    def create_table(self, table):

        self.schema.create_table(
            self.client,
            table,
        )

    def insert_rows(self, table, rows):

        if not rows:
            return

        if not self.table_exists(table):
            self.create_table(table)
        # else:
        #     self.schema.review_table_schema(
        #         self.client,
        #         table,
        #     )

        columns = list(rows[0].keys())

        data = []

        for row in rows:
            data.append([row[col] for col in columns])

        self.client.insert(
            table=table,
            data=data,
            column_names=columns,
        )

    def optimize(self, table):

        self.client.command(f"OPTIMIZE TABLE {table} FINAL")

    def close(self):

        self.schema.close()

        self.client.close()