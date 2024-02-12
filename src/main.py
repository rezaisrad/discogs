import os
import logging
from dotenv import load_dotenv
from xml_handler import XMLDataHandler
from sinks.postgres import PostgresDataStore

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
POSTGRES_TABLE_NAME = os.getenv("POSTGRES_TABLE_NAME", "releases_db")
DATA_URL = os.getenv("DATA_URL")
DESTINATION_DIR = os.getenv("DESTINATION_DIR", "./")


def setup_logging():
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )


def setup_data_store():
    # Create and return a DataStore instance
    data_store = PostgresDataStore(DATABASE_URL, POSTGRES_TABLE_NAME)
    data_store.connect()
    return data_store


def main():
    setup_logging()

    # Initialize the data store
    data_store = setup_data_store()

    # Initialize XMLDataHandler with the URL, destination directory, and data store
    handler = XMLDataHandler(DATA_URL, DESTINATION_DIR, data_store=data_store)
    try:
        handler.download_file()
        handler.parse_xml()
        handler.delete_file()
    except Exception as e:
        logging.error(f"An error occurred: {e}")


if __name__ == "__main__":
    main()
