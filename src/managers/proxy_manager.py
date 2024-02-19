import logging
import requests
from random import choice
import threading

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
        logging.debug(f"Selected proxy {proxy['http']} for thread: {threading.current_thread().name}")
        return proxy

    def replace_proxy(self, old_proxy):
        self.remove_proxy(old_proxy)
        return self.get_proxy()

    def remove_proxy(self, proxy):
        if proxy in self.proxies:
            self.proxies.remove(proxy)
            logging.debug(f"Removed proxy {proxy['http']} from the list.")

    def validate_proxy(self, proxy):
        try:
            response = requests.get("https://httpbin.org/ip", proxies={"http": proxy}, timeout=5)
            return response.status_code == 200
        except requests.RequestException:
            return False