from contextlib import contextmanager
import psycopg2
from psycopg2.extras import Json
from psycopg2 import OperationalError
from sinks import BaseDataStore

class PostgresDataStore(BaseDataStore):
    def __init__(self, database_url, table_name):
        self.database_url = database_url
        self.table_name = table_name
        self.conn = None

    def connect(self):
        """Establishes a database connection if not already connected."""
        if self.conn is None:
            try:
                self.conn = psycopg2.connect(self.database_url)
            except OperationalError as e:
                print(f"An error occurred while trying to connect to the database: {e}")
                self.conn = None
        else:
            try:
                # Check if connection is closed (conn.closed == 0 means open)
                if self.conn.closed == 0:
                    return
                else:
                    self.conn = psycopg2.connect(self.database_url)
            except OperationalError as e:
                print(f"An error occurred while trying to reconnect to the database: {e}")
                self.conn = None

    @contextmanager
    def get_db_connection(self):
        """Context manager for database connection."""
        if self.conn is None or self.conn.closed != 0:
            self.connect()
        try:
            yield self.conn
        finally:
            self.conn.close()

    @contextmanager
    def get_db_cursor(self, commit=False):
        """Context manager for database cursor."""
        with self.get_db_connection() as conn:
            cursor = conn.cursor()
            try:
                yield cursor
                if commit:
                    conn.commit()
            finally:
                cursor.close()

    def insert(self, records):
        """Inserts a batch of data into the specified table."""
        with self.get_db_cursor(commit=True) as cursor:
            args_str = ",".join(cursor.mogrify("(%s)", (Json(data),)).decode("utf-8") for data in records)
            cursor.execute(f"INSERT INTO {self.table_name} (data) VALUES " + args_str)

    def query(self, query_params):
        # Implementation depends on specific query needs
        pass