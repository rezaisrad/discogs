import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import Json
from contextlib import contextmanager

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")


@contextmanager
def get_db_connection():
    conn = psycopg2.connect(DATABASE_URL)
    try:
        yield conn
    finally:
        conn.close()


@contextmanager
def get_db_cursor(commit=False):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            yield cursor
            if commit:
                conn.commit()
        finally:
            cursor.close()


def insert_batch(cursor, table_name, data_batch):
    """Inserts a batch of data into the specified table."""
    args_str = ",".join(
        cursor.mogrify("(%s)", (Json(data),)).decode("utf-8") for data in data_batch
    )
    cursor.execute(f"INSERT INTO {table_name} (data) VALUES " + args_str)
