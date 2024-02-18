from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
from models.discogs_objects import DiscogsRelease, DiscogsStatsPage, DiscogsSellerPageRelease
from managers.session_manager import SessionManager
from managers.proxy_manager import ProxyManager
import time 
import threading

class Scraper:
    def __init__(self, proxy_list_url, max_workers=3):
        self.proxy_manager = ProxyManager(proxy_list_url)
        self.session_manager = SessionManager(self.proxy_manager)
        self.max_workers = max_workers

    def get_release_info(self, release_id):
        logging.info(f"Fetching release info for ID: {release_id} using {self.session_manager} on thread: {threading.current_thread().name}")
        results = {}
        try:
            release_page = DiscogsRelease(release_id, self.session_manager)
            try:
                release_page.fetch_and_parse()
                results.update({"release_id": release_id, "release": release_page.stats})
            except Exception as e:
                logging.error(f"Error fetching DiscogsRelease for {release_id}: {e}", exc_info=True)
            
            time.sleep(1)
            
            stats_page = DiscogsStatsPage(release_id, self.session_manager)
            try:
                stats_page.fetch_and_parse()
                results["stats"] = {"have": stats_page.members_have, "want": stats_page.members_want}
            except Exception as e:
                logging.error(f"Error fetching DiscogsStatsPage for {release_id}: {e}", exc_info=True)
            
            time.sleep(1)
            
            query_params = {"sort": "listed,desc", "limit": 250, "genre": "Electronic", "format": "Vinyl"}
            seller_page = DiscogsSellerPageRelease(release_id, self.session_manager, query_params)
            try:
                seller_page.fetch_and_parse()
                results["sellers"] = seller_page.items_for_sale
            except Exception as e:
                logging.error(f"Error fetching DiscogsSellerPageRelease for {release_id}: {e}", exc_info=True)
            
            time.sleep(1)
        except Exception as e:
            logging.error(f"General error processing release {release_id} on thread: {threading.current_thread().name} with session manager: {self.session_manager}: {e}", exc_info=True)
        finally:
            return results

    def run(self, release_ids):
        logging.info("Starting scraper with %s workers", self.max_workers)
        results = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [executor.submit(self.get_release_info, rid) for rid in release_ids]
            for future in as_completed(futures):
                result = future.result()
                if result:
                    results.append(result)
                    logging.info(f"Successfully fetched data for release ID: {result['release_id']} on thread: {threading.current_thread().name}")
        return results