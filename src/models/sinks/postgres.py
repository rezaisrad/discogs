from contextlib import contextmanager
import psycopg2
from psycopg2.extras import Json, execute_values
from psycopg2 import OperationalError
from .db import BaseDataStore
import logging 

class PostgresDataStore(BaseDataStore):
    def __init__(self, database_url, table_name):
        self.database_url = database_url
        self.table_name = table_name
        self.conn = None
        logging.info(f"Initializing PostgresDataStore for table: {table_name}")

    def connect(self):
        """Establishes a database connection if not already connected."""
        try:
            if self.conn is None or self.conn.closed != 0:
                self.conn = psycopg2.connect(self.database_url)
                logging.info("Database connection established.")
        except OperationalError as e:
            logging.error(f"Failed to connect to database: {e}")
            self.conn = None

    @contextmanager
    def get_db_connection(self):
        """Context manager for database connection."""
        try:
            if self.conn is None or self.conn.closed != 0:
                self.connect()
            yield self.conn
        except Exception as e:
            logging.error(f"Error during database operation: {e}")
        finally:
            self.conn.close()
            logging.info("Database connection closed.")

    @contextmanager
    def get_db_cursor(self, commit=False):
        """Context manager for database cursor."""
        with self.get_db_connection() as conn:
            cursor = conn.cursor()
            try:
                yield cursor
                if commit:
                    conn.commit()
                    logging.info("Database changes committed.")
            finally:
                cursor.close()

    def insert(self, records):
        """Inserts a batch of data into the specified table."""
        try:
            with self.get_db_cursor(commit=True) as cursor:
                args_str = ",".join(cursor.mogrify("(%s)", (Json(data),)).decode("utf-8") for data in records)
                cursor.execute(f"INSERT INTO {self.table_name} (data) VALUES " + args_str)
                logging.info(f"Inserted {len(records)} records into {self.table_name}.")
        except Exception as e:
            logging.error(f"Failed to insert records: {e}")

    def fetch_ids(self, query):
        """Fetches a list of IDs based on the provided query."""
        try:
            ids = []
            with self.get_db_cursor() as cursor:
                cursor.execute(query)
                ids = [row[0] for row in cursor.fetchall()]  # Assuming the ID is in the first column
            logging.info(f"Fetched {len(ids)} IDs.")
            return ids
        except Exception as e:
            logging.error(f"Failed to fetch IDs: {e}")
            return []

    def fetch_ids_from_file(self, file_path):
        """Runs a SQL query from a provided file path."""
        try:
            with open(file_path, 'r') as file:
                query = file.read()
            return self.fetch_ids(query)
        except Exception as e:
            logging.error(f"Failed to fetch IDs from file {file_path}: {e}")
            return []

    def bulk_insert(self, query, data):
        """Executes a bulk insert operation."""
        try:
            with self.get_db_cursor(commit=True) as cursor:
                execute_values(cursor, query, data, template=None, page_size=100)
                logging.info(f"Bulk inserted data using query: {query}")
        except Exception as e:
            logging.error(f"Failed to perform bulk insert: {e}")
