from config import TABLES
from mysql_reader import MySQLReader
from clickhouse_writer import ClickHouseWriter

mysql = MySQLReader()
writer = ClickHouseWriter()

# Use tables from .env, otherwise get all tables from MySQL
tables = TABLES if TABLES else mysql.get_tables()

for table in tables:

    if table.startswith("_"):
        continue

    print(f"Updating schema: {table}")

    writer.schema.review_table_schema(
        writer.client,
        table,
    )

mysql.close()
writer.close()