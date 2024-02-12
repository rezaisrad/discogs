from contextlib import contextmanager
import psycopg2
from psycopg2.extras import Json
from sinks import BaseDataStore

class PostgresDataStore(BaseDataStore):
    def __init__(self, database_url):
        self.database_url = database_url
        self.conn = None

    @contextmanager
    def get_db_connection(self):
        self.conn = psycopg2.connect(self.database_url)
        try:
            yield self.conn
        finally:
            self.conn.close()

    @contextmanager
    def get_db_cursor(self, commit=False):
        with self.get_db_connection() as conn:
            cursor = conn.cursor()
            try:
                yield cursor
                if commit:
                    conn.commit()
            finally:
                cursor.close()

    def insert(self, table_name, data_batch):
        with self.get_db_cursor(commit=True) as cursor:
            args_str = ",".join(cursor.mogrify("(%s)", (Json(data),)).decode("utf-8") for data in data_batch)
            cursor.execute(f"INSERT INTO {table_name} (data) VALUES " + args_str)

    def query(self, query_params):
        # Implementation depends on specific query needs
        pass