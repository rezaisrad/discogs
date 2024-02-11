import os
import logging
from dotenv import load_dotenv
from xml_handler import XMLDataHandler


def setup_logging():
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )


def main():
    load_dotenv()
    setup_logging()

    # Retrieve URL and destination directory from environment variables
    data_url = os.getenv("DATA_URL")
    destination_dir = os.getenv("DESTINATION_DIR", "./")

    # Initialize XMLDataHandler with the URL and destination directory
    handler = XMLDataHandler(data_url, destination_dir)
    try:
        handler.download_file()
        handler.parse_xml()
    except Exception as e:
        logging.error(f"An error occurred: {e}")


if __name__ == "__main__":
    main()
