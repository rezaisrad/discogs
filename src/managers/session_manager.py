import cloudscraper
from threading import Lock
import time
import requests
import logging

class SessionManager:
    def __init__(self, proxy_manager, rate_limit_per_minute=30):
        logging.info("Initializing SessionManager with rate limit per minute: %d", rate_limit_per_minute)
        self.proxy_manager = proxy_manager
        self.rate_limit_per_minute = rate_limit_per_minute
        self.sessions = {}
        self.sessions_lock = Lock()

    def get_session(self, use_proxy=True):
        logging.debug("Requesting session with proxy usage set to: %s", use_proxy)
        if not use_proxy:
            identifier = 'no_proxy'
        else:
            proxy = self._get_valid_proxy()
            identifier = proxy['http'] if proxy else 'no_proxy'

        with self.sessions_lock:
            if identifier not in self.sessions or not self._can_make_request(identifier):
                logging.debug("Creating or recycling session for identifier: %s", identifier)
                self._create_or_recycle_session(identifier)
            else:
                logging.debug("Reusing session for identifier: %s", identifier)
            
            self._update_request_time(identifier)
            return self.sessions[identifier]['session']

    def _create_or_recycle_session(self, identifier):
        logging.info("Creating new session for identifier: %s", identifier)
        session = cloudscraper.create_scraper()
        if identifier != 'no_proxy':
            proxy = {'http': identifier}
            session.proxies = proxy
            logging.info("Session for %s set with proxy: %s", identifier, proxy)
        self.sessions[identifier] = {
            'session': session,
            'last_used': time.time(),
            'request_count': 1
        }

    def _can_make_request(self, identifier):
        min_interval = self._get_min_interval()
        elapsed_time = time.time() - self.sessions.get(identifier, {}).get('last_used', 0)
        can_request = elapsed_time >= min_interval
        logging.debug("Can make request for %s: %s", identifier, can_request)
        return can_request

    def _update_request_time(self, identifier):
        logging.debug("Updating request time for identifier: %s", identifier)
        self.sessions[identifier]['last_used'] = time.time()
        self.sessions[identifier]['request_count'] += 1

    def _get_min_interval(self):
        return 60.0 / self.rate_limit_per_minute

    def _get_valid_proxy(self):
        logging.debug("Attempting to get a valid proxy")
        for _ in range(len(self.proxy_manager.proxies)):
            proxy = self.proxy_manager.get_proxy()
            if self._validate_proxy(proxy):
                logging.info("Valid proxy found: %s", proxy)
                return proxy
            logging.info("Removing invalid proxy: %s", proxy)
            self.proxy_manager.remove_proxy(proxy)
        logging.warning("No valid proxy found.")
        return None

    def _validate_proxy(self, proxy):
        logging.debug("Validating proxy: %s", proxy)
        try:
            response = requests.get("https://httpbin.org/ip", proxies=proxy, timeout=5)
            valid = response.status_code == 200
            logging.debug("Proxy validation result for %s: %s", proxy, valid)
            return valid
        except requests.RequestException:
            logging.warning("Proxy validation failed for: %s", proxy)
            return False