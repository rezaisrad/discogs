import logging
import scraper
from sinks.postgres import PostgresDataStore
import os
from dotenv import load_dotenv

load_dotenv()

URL = os.getenv("PROXIES_URL")
MAX_WORKERS = int(os.getenv("MAX_WORKERS", 3))
MAX_RETRIES = int(os.getenv("MAX_RETRIES", 5))
DATABASE_URL = os.getenv("DATABASE_URL")
TABLE_NAME = os.getenv("TABLE_NAME")
QUERY_PATH = "../db/releases.sql"
BATCH_SIZE = 100

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(threadName)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("debug.log"),
        logging.StreamHandler()
    ]
)



def write_to_postgres(p, releases):
    if not releases:
        logging.warning("No releases to write to Postgres.")
        return

    insert_release_sellers(p, releases)
    insert_release_details(p, releases)
    insert_release_wants_haves(p, releases, "want")
    insert_release_wants_haves(p, releases, "have")
    

def insert_release_sellers(p, releases):
    """Insert release sellers data into the release_sellers table."""
    logging.info("Inserting release sellers data.")
    try:
        sellers_data = [
        (
            release["release_id"],
            seller.get("image_url"),
            seller.get("rating"),
            seller.get("have"),
            seller.get("want"),
            seller.get("title"),
            seller.get("label"),
            seller.get("catno"),
            seller.get("media_condition"),
            seller.get("media_condition_description"),
            seller.get("seller"),
            seller.get("seller_rating"),
            seller.get("ships_from"),
            seller.get("currency"),
            seller.get("price"),
        )
        for release in releases
        for seller in release.get("sellers", [])
        ]
        query = """
        INSERT INTO release_sellers (
            release_id, image_url, rating, have, want, title, label, catno, media_condition, 
            media_condition_description, seller, seller_rating, ships_from, currency, price
        ) VALUES %s
        """
        p.bulk_insert(query, sellers_data)
        logging.info("Successfully inserted release sellers data.")
    except Exception as e:
        logging.error(f"Failed to insert release sellers data: {e}")



def insert_release_details(p, releases):
    """Insert release details data into the release_details table."""
    logging.info("Inserting release details data.")
    try:
        details_data = [
            (
                release["release_id"],
                release.get("release", {}).get("Have"),
                release.get("release", {}).get("Want"),
                release.get("release", {}).get("Avg Rating"),
                release.get("release", {}).get("Ratings"),
                release.get("release", {}).get("Last Sold"),
                release.get("release", {}).get("Low"),
                release.get("release", {}).get("Median"),
                release.get("release", {}).get("High"),
            )
            for release in releases
        ]

        query = """
        INSERT INTO release_details (
            release_id, have, want, avg_rating, ratings, last_sold, low, median, high
        ) VALUES %s
        """
        p.bulk_insert(query, details_data)
        logging.info("Successfully inserted release details data.")
    except Exception as e:
        logging.error(f"Failed to insert release details data: {e}")


def insert_release_wants_haves(p, releases, type_):
    """Insert release wants/haves data into the release_wants or release_haves table."""
    logging.info("Inserting release want/haves data.")
    try:
        table_name = f"release_{type_}s"
        data = [
            (release["release_id"], user)
            for release in releases
            for user in release.get("stats", {}).get(type_, [])
        ]
        query = f"INSERT INTO {table_name} (release_id, username) VALUES %s"
        p.bulk_insert(query, data)
        logging.info("Successfully inserted release want/haves data.")
    except Exception as e:
        logging.error(f"Failed to insert release want/haves data: {e}")


def main():
    p = PostgresDataStore(DATABASE_URL, TABLE_NAME)
    release_ids = p.fetch_ids_from_file(QUERY_PATH)
    
    logging.info(f"Processing {len(release_ids)} release IDs in batches of {BATCH_SIZE}.")
    for i in range(0, len(release_ids), BATCH_SIZE):
        batch_ids = release_ids[i : i + BATCH_SIZE]
        logging.info(f"Processing batch {i//BATCH_SIZE + 1}/{len(release_ids)//BATCH_SIZE + 1}.")
        try:
            releases = scraper.run_scraper(URL, batch_ids, MAX_WORKERS)
            write_to_postgres(p, releases)
        except Exception as e:
            logging.error(f"Error processing batch {i//BATCH_SIZE}: {e}")


if __name__ == "__main__":
    main()
