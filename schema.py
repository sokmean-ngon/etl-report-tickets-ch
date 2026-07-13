import re

import mysql.connector

from config import CH_ENGINE, ID_COLUMN, MYSQL, CLICKHOUSE

from logger import get_logger

logger = get_logger()

DECIMAL_PATTERN = re.compile(
    r"decimal\((\d+)\s*,\s*(\d+)\)",
    re.IGNORECASE,
)

class SchemaConverter:
    
    @staticmethod
    def normalize_type(dtype: str) -> str:
        return dtype.lower().replace(" ", "")

    @staticmethod
    def mysql_to_clickhouse(mysql_type: str) -> str:
        """
        Convert a MySQL column type to a ClickHouse type.
        """

        t = mysql_type.lower().strip()

        unsigned = "unsigned" in t

        # Normalize
        t = t.replace(" unsigned", "")
        t = t.replace(" zerofill", "")

        INTEGER_TYPES = {
            "tinyint": ("Int8", "UInt8"),
            "smallint": ("Int16", "UInt16"),
            "mediumint": ("Int32", "UInt32"),
            "int": ("Int32", "UInt32"),
            "integer": ("Int32", "UInt32"),
            "bigint": ("Int64", "UInt64"),
        }

        STRING_TYPES = (
            "char",
            "varchar",
            "tinytext",
            "text",
            "mediumtext",
            "longtext",
            "json",
            "enum",
            "set",
            "binary",
            "varbinary",
            "tinyblob",
            "blob",
            "mediumblob",
            "longblob",
        )

        # ---------- Integer ----------
        for prefix, (signed_type, unsigned_type) in INTEGER_TYPES.items():

            if t.startswith(prefix):

                # tinyint(1) -> boolean
                if prefix == "tinyint":
                    m = re.search(r"tinyint\((\d+)\)", t)
                    if m and int(m.group(1)) == 1:
                        return "UInt8"

                return unsigned_type if unsigned else signed_type

        # ---------- Decimal ----------
        if t.startswith("decimal"):

            m = DECIMAL_PATTERN.search(t)

            if m:
                precision = int(m.group(1))
                scale = int(m.group(2))

                # ClickHouse maximum precision is 76
                if precision > 76:
                    raise ValueError(
                        f"Unsupported Decimal precision: {precision}"
                    )

                return f"Decimal({precision},{scale})"

            logger.warning(
                f"Unknown decimal definition '{mysql_type}', "
                "using Decimal(18,4)"
            )

            return "Decimal(18,4)"

        # ---------- Float ----------
        if t.startswith("float"):
            return "Float32"

        if t.startswith(("double", "real")):
            return "Float64"

        # ---------- Boolean ----------
        if t.startswith(("bool", "boolean")):
            return "UInt8"

        # ---------- Bit ----------
        if t.startswith("bit"):

            m = re.search(r"bit\((\d+)\)", t)

            if m:

                bits = int(m.group(1))

                if bits == 1:
                    return "UInt8"

                if bits <= 8:
                    return "UInt8"

                if bits <= 16:
                    return "UInt16"

                if bits <= 32:
                    return "UInt32"

                if bits <= 64:
                    return "UInt64"

            return "String"

        # ---------- Date / Time ----------
        if t.startswith(("datetime", "timestamp")):

            m = re.search(r"\((\d+)\)", t)

            if m:
                return f"DateTime64({m.group(1)})"

            return "DateTime"

        if t.startswith("date"):
            return "Date"

        if t.startswith("time"):
            return "String"

        if t.startswith("year"):
            return "UInt16"

        # ---------- UUID ----------
        if t.startswith("uuid"):
            return "UUID"

        # ---------- String ----------
        if t.startswith(STRING_TYPES):
            return "String"

        logger.warning(
            f"Unknown MySQL type '{mysql_type}', mapped to String."
        )

        return "String"
    

    def __init__(self):
        self.conn = mysql.connector.connect(**MYSQL)
        self.cursor = self.conn.cursor(dictionary=True)

    def get_mysql_schema(self, table):

        self.cursor.execute(f"SHOW FULL COLUMNS FROM `{table}`")

        schema = {}

        for c in self.cursor.fetchall():

            ch_type = self.mysql_to_clickhouse(c["Type"])

            nullable = c["Null"] == "YES"

            if nullable:
                ch_type = f"Nullable({ch_type})"

            schema[c["Field"]] = ch_type

        logger.debug(f"MySQL schema ({table}): {schema}")

        return schema

    def get_clickhouse_schema(self, ch_client, table):

        sql = f"""
        SELECT
            name,
            type
        FROM system.columns
        WHERE database = '{CLICKHOUSE["database"]}'
        AND table = '{table}'
        ORDER BY position
        """

        rows = ch_client.query(sql).result_rows

        schema = dict(rows)

        logger.debug(
            f"ClickHouse schema ({table}): {schema}"
        )

        return schema

    def review_table_schema(self, ch_client, table):

        mysql_schema = self.get_mysql_schema(table)

        clickhouse_schema = self.get_clickhouse_schema(
            ch_client,
            table,
        )

        added = False

        logger.info(f"Checking schema: {table}")

        mysql_columns = set(mysql_schema.keys())
        ch_columns = set(clickhouse_schema.keys())
        new_columns = mysql_columns - ch_columns

        #
        # Add new columns
        #
        for column in sorted(new_columns):

            ch_type = mysql_schema[column]

            logger.info(
                f"Adding new column: {column} ({ch_type})"
            )

            sql = (
                f"ALTER TABLE `{table}` "
                f"ADD COLUMN IF NOT EXISTS `{column}` {ch_type}"
            )

            logger.debug(sql)

            try:

                ch_client.command(sql)

                logger.info(
                    f"Added column '{column}' successfully."
                )

                added = True

            except Exception as e:

                logger.error(
                    f"Failed to add column '{column}': {e}"
                )

        if added:

            clickhouse_schema = self.get_clickhouse_schema(
                ch_client,
                table,
            )

        mysql_columns = set(mysql_schema.keys())
        ch_columns = set(clickhouse_schema.keys())
            
        #
        # Compare existing columns
        #
        for column in sorted(mysql_columns & ch_columns):

            mysql_type = mysql_schema[column]
            ch_type = clickhouse_schema[column]

            if self.normalize_type(mysql_type) != self.normalize_type(ch_type):

                logger.warning(
                    f"Type mismatch:\n"
                    f"  Column : {column}\n"
                    f"  MySQL  : {mysql_type}\n"
                    f"  CH     : {ch_type}\n"
                    f"  Action : Manual review required"
                )

        #
        # Columns only in ClickHouse
        #
        for column in sorted(ch_columns - mysql_columns):

            logger.warning(
                f"Column '{column}' exists only in ClickHouse."
            )

        logger.info(
            f"Schema review completed: {table}"
        )

    def get_create_sql(self, table, engine=None):

        if engine is None:
            engine = CH_ENGINE

        schema = self.get_mysql_schema(table)

        fields = [
            f"`{column}` {dtype}"
            for column, dtype in schema.items()
        ]

        create_sql = f"""
        CREATE TABLE IF NOT EXISTS `{table}`
        (
            {", ".join(fields)}
        )
        ENGINE = {engine}
        ORDER BY `{ID_COLUMN}`
        """

        return create_sql

    def create_table(self, ch_client, table, engine=None):
        ch_client.command(
            self.get_create_sql(
                table,
                engine,
            )
        )

    def close(self):
        self.cursor.close()
        self.conn.close()