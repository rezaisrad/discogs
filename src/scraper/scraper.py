from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
from models.discogs_objects import DiscogsRelease, DiscogsStatsPage, DiscogsSellerPageRelease
from managers.session_manager import SessionManager
from managers.proxy_manager import ProxyManager
import threading

class Scraper:
    def __init__(self, proxy_list_url, max_workers=3):
        self.proxy_manager = ProxyManager(proxy_list_url)
        self.session_manager = SessionManager(self.proxy_manager)
        self.max_workers = max_workers

    def get_release_info(self, release_id):
        try:
            logging.info(f"Fetching release info for ID: {release_id} on thread: {threading.current_thread().name}")
            release_page = DiscogsRelease(release_id, self.session_manager)
            logging.debug(f"Fetching release seller pagr info for ID: {release_id} on thread: {threading.current_thread().name} on proxy: {release_page.proxy}")
            release_page.fetch_and_parse()

            stats_page = DiscogsStatsPage(release_id, self.session_manager)
            logging.debug(f"Fetching release stats page for ID: {release_id} on thread: {threading.current_thread().name} on proxy: {stats_page.proxy}")
            stats_page.fetch_and_parse()

            query_params = {"sort": "listed,desc", "limit": 250, "genre": "Electronic", "format": "Vinyl"}
            seller_page = DiscogsSellerPageRelease(release_id, self.session_manager, query_params)
            logging.debug(f"Fetching release seller pagr info for ID: {release_id} on thread: {threading.current_thread().name} on proxy: {seller_page.proxy}")
            seller_page.fetch_and_parse()

            return {
                "release_id": release_id,
                "release": release_page.stats,
                "stats": {"have": stats_page.members_have, "want": stats_page.members_want},
                "sellers": seller_page.items_for_sale
            }
        except Exception as e:
            logging.error(f"Error processing release {release_id} on thread: {threading.current_thread().name}: {e}", exc_info=True)
            return None


    def run(self, release_ids):
        logging.info("Starting scraper with %d workers", self.max_workers)
        results = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [executor.submit(self.get_release_info, rid) for rid in release_ids]
            for future in as_completed(futures):
                result = future.result()
                if result:
                    results.append(result)
                    logging.info(f"Successfully fetched data for release ID: {result['release_id']}")
        return results