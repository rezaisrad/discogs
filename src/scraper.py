from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import wraps
import logging
import requests
from data import DiscogsRelease, DiscogsStatsPage, DiscogsSellerPageRelease
from random import choice
import time
import threading

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(threadName)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("debug.log"),
        logging.StreamHandler()
    ]
)

def retry_with_new_proxy(max_retries=5):
    def decorator(func):
        @wraps(func)
        def wrapper(release_id, proxy_manager, *args, **kwargs):
            retries = 0
            proxy = None
            while retries < max_retries:
                try:
                    if proxy:  # Remove the previous proxy if retrying
                        proxy_manager.remove_proxy(proxy)
                    proxy = proxy_manager.get_proxy()
                    return func(release_id, proxy_manager, proxy, *args, **kwargs)  # Pass both proxy_manager and proxy
                except Exception as e:
                    logging.error(f"Attempt {retries + 1} for release {release_id} failed: {e}")
                    retries += 1
                    if retries >= max_retries:
                        logging.error(f"Max retries reached for release {release_id}. Giving up.")
                        return None
                    time.sleep(2 ** retries)  # Exponential backoff
            return None
        return wrapper
    return decorator


class ProxyManager:
    def __init__(self, proxy_list_url):
        self.proxy_list_url = proxy_list_url
        self.proxies = self._fetch_proxies()

    def _fetch_proxies(self):
        try:
            response = requests.get(self.proxy_list_url)
            response.raise_for_status()
            proxy_list = response.text.strip().split("\n")
            return [{"http": f"http://{proxy}"} for proxy in proxy_list]
        except requests.RequestException as e:
            logging.error(f"Failed to fetch proxies: {e}")
            return []

    def get_proxy(self):
        proxy = choice(self.proxies) if self.proxies else None
        logging.debug(f"Selected proxy {proxy} for thread: {threading.current_thread().name}")
        return proxy

    def remove_proxy(self, proxy):
        if proxy in self.proxies:
            self.proxies.remove(proxy)
            logging.debug(f"Removed proxy {proxy} from the list.")

@retry_with_new_proxy()
def get_release_info(release_id, proxy_manager, proxy): 
    session = requests.Session()
    session.proxies = proxy
    logging.debug(f"Fetching release info for ID: {release_id} using session: {session} in thread: {threading.current_thread().name}")

    results = {}
    try:
        results["release_id"] = release_id

        release_page = DiscogsRelease(release_id, session=session)
        release_page.fetch_and_parse()
        results["release"] = release_page.stats

        stats_page = DiscogsStatsPage(release_id, session=session)
        stats_page.fetch_and_parse()
        results["stats"] = {"have": stats_page.members_have, "want": stats_page.members_want}

        query_params = {"sort": "listed,desc", "limit": 250, "genre": "Electronic", "format": "Vinyl"}
        seller_page = DiscogsSellerPageRelease(release_id, session=session, query_params=query_params)
        seller_page.fetch_and_parse()
        results["sellers"] = seller_page.items_for_sale
    except Exception as e:
        logging.error(f"Error processing release {release_id} with session: {session}: {e}")
        proxy_manager.remove_proxy(proxy)
    return results


def run_scraper(url, release_ids, max_workers=3):
    proxy_manager = ProxyManager(url)
    results = []
    try:
        with ThreadPoolExecutor(max_workers=int(max_workers)) as executor:
            futures = [
                executor.submit(get_release_info, rid, proxy_manager)
                for rid in release_ids
            ]
            for future in as_completed(futures):
                try:
                    result = future.result()
                    if result:
                        results.append(result)
                        logging.info(f"Successfully fetched data: {result['release_id']}")
                except Exception as e:
                    logging.error(f"Error processing task: {e}")
    except KeyboardInterrupt:
        logging.info("Received KeyboardInterrupt, terminating workers.")
        for future in futures:
            future.cancel()
        logging.info("Workers terminated.")
        return results
    return results
