import os
import logging
from dotenv import load_dotenv
from xml_handler import XMLDataHandler
from sinks.redis import RedisDataStore

def setup_logging():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def setup_data_store():
    # Create and return a RedisDataStore instance
    data_store = RedisDataStore(host='localhost', port=6379, db=0)
    data_store.connect()
    return data_store

def main():
    load_dotenv()
    setup_logging()

    # Initialize the data store
    data_store = setup_data_store()

    # Retrieve URL and destination directory from environment variables
    data_url = os.getenv("DATA_URL")
    destination_dir = os.getenv("DESTINATION_DIR", "./")

    # Initialize XMLDataHandler with the URL, destination directory, and data store
    handler = XMLDataHandler(data_url, destination_dir, data_store=data_store)
    try:
        handler.download_file()
        handler.parse_xml()
    except Exception as e:
        logging.error(f"An error occurred: {e}")

if __name__ == "__main__":
    main()