# db_connector.py
import pandas as pd
import psycopg2
import mysql.connector

class DBConnector:
    def __init__(self, db_type, host, port, db_name, username, password):
        self.db_type = db_type.lower()
        self.host = host
        self.port = port
        self.db_name = db_name
        self.username = username
        self.password = password
        self.conn = None

    def connect(self):
        if self.db_type == "postgresql":
            self.conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                dbname=self.db_name,
                user=self.username,
                password=self.password
            )
        elif self.db_type == "mysql":
            self.conn = mysql.connector.connect(
                host=self.host,
                port=self.port,
                database=self.db_name,
                user=self.username,
                password=self.password
            )
        else:
            raise ValueError(f"Unsupported DB type: {self.db_type}")

    def get_schema(self):
        """
        Returns {table_name: [col1, col2, ...]} for all tables in the DB
        """
        schema = {}
        cursor = self.conn.cursor()

        if self.db_type == "postgresql":
            cursor.execute("""
                SELECT table_name, column_name
                FROM information_schema.columns
                WHERE table_schema = 'public'
                ORDER BY table_name, ordinal_position
            """)
        elif self.db_type == "mysql":
            cursor.execute("""
                SELECT table_name, column_name
                FROM information_schema.columns
                WHERE table_schema = %s
                ORDER BY table_name, ordinal_position
            """, (self.db_name,))
        else:
            raise ValueError("Unsupported DB type for schema fetch")

        for table, column in cursor.fetchall():
            schema.setdefault(table, []).append(column)

        cursor.close()
        return schema

    def execute_query(self, sql):
        """
        Executes a SQL SELECT query and returns results as a Pandas DataFrame
        """
        df = pd.read_sql(sql, self.conn)
        return df

    def close(self):
        if self.conn:
            self.conn.close()
            self.conn = None
