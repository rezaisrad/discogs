import cloudscraper
from threading import Lock, current_thread
import time
import logging

class SessionManager:
    def __init__(self, proxy_manager, rate_limit_per_minute=30):
        logging.info("Initializing SessionManager with rate limit per minute: %d", rate_limit_per_minute)
        self.proxy_manager = proxy_manager
        self.rate_limit_per_minute = rate_limit_per_minute
        self.sessions_lock = Lock()
        self.thread_sessions = {}
        self.proxy_failures = {} 
        
    def get_session(self, use_proxy=True):
        thread_id = current_thread().ident
        with self.sessions_lock:
            if thread_id not in self.thread_sessions or not self._can_make_request(thread_id):
                self._create_or_recycle_session(thread_id, use_proxy)
            session_info = self.thread_sessions.get(thread_id, {})
            return session_info['session'], session_info.get('proxy')
        
    def _create_or_recycle_session(self, thread_id, use_proxy):
        # Check if a session exists and can be reused.
        if thread_id in self.thread_sessions:
            session_info = self.thread_sessions[thread_id]
            # Check if proxy requirements have changed or session needs a new proxy.
            if use_proxy:
                new_proxy = self.proxy_manager.get_proxy()
                # Update the session's proxy if a new one is obtained.
                if new_proxy and (not session_info['proxy'] or session_info['proxy'] != new_proxy):
                    session_info['session'].proxies = new_proxy
                    session_info['proxy'] = new_proxy
                    logging.info(f"Updated proxy for thread {thread_id} to {new_proxy['http']}.")
            else:
                # Clear the proxy if not using one anymore.
                session_info['session'].proxies = {}
                session_info['proxy'] = None
            
            # Reset the request count and update the last used timestamp.
            session_info['last_used'] = time.time()
            session_info['request_count'] = 0
        else:
            # Create a new session if one does not exist.
            logging.debug(f"Creating new session for thread {thread_id}.")
            session = cloudscraper.create_scraper()
            proxy = self.proxy_manager.get_proxy() if use_proxy else None
            if proxy:
                session.proxies = proxy
            self.thread_sessions[thread_id] = {
                'session': session, 
                'last_used': time.time(), 
                'request_count': 0, 
                'proxy': proxy
            }
            logging.debug(f"New session created at {proxy['http']}.")

        
    def _can_make_request(self, identifier):
        """Check if the session can make a request based on the rate limit."""
        logging.debug("Checking if can make request for identifier: %s", identifier)
        min_interval = self._get_min_interval()
        session_info = self.thread_sessions.get(identifier, {})
        elapsed_time = time.time() - session_info.get('last_used', 0)
        return elapsed_time >= min_interval and session_info.get('request_count', 0) < self.rate_limit_per_minute

    def _update_request_time(self, identifier):
        if identifier in self.thread_sessions:
            self.thread_sessions[identifier]['last_used'] = time.time()
            self.thread_sessions[identifier]['request_count'] += 1
        else:
            logging.error(f"Session identifier {identifier} not found in thread_sessions.")
                
    def _get_min_interval(self):
        return 60.0 / self.rate_limit_per_minute

    def _get_valid_proxy(self):
        logging.debug("Attempting to get a valid proxy")
        for _ in range(len(self.proxy_manager.proxies)):
            proxy = self.proxy_manager.get_proxy()
            if proxy and self.proxy_manager.validate_proxy(proxy):
                logging.debug("Valid proxy found: %s", proxy)
                return proxy['http']
            self.proxy_manager.remove_proxy(proxy)
            logging.debug("Removing invalid proxy: %s", proxy)
        logging.warning("No valid proxy found.")
        return None

    def replace_proxy(self, identifier):
        with self.sessions_lock:
            if identifier in self.thread_sessions:
                old_proxy = self.thread_sessions[identifier]['proxy']
                new_proxy = self._get_valid_proxy()
                if new_proxy:
                    self.thread_sessions[identifier]['proxy'] = {"http": new_proxy, "https": new_proxy}
                    self.thread_sessions[identifier]['session'].proxies = {"http": new_proxy, "https": new_proxy}
                    logging.info(f"Replaced proxy for {identifier} from {old_proxy} to {new_proxy}")
                else:
                    logging.warning(f"Could not find a valid proxy to replace for {identifier}.")
            else:
                logging.error(f"Tried to replace proxy for non-existent session identifier {identifier}.")