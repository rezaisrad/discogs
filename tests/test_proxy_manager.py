import pytest
import requests_mock
from managers.proxy_manager import ProxyManager

@pytest.fixture
def proxy_list_url():
    return "http://proxylist.com/proxies"

@pytest.fixture
def proxy_manager(proxy_list_url):
    return ProxyManager(proxy_list_url)

def test_fetch_proxies_success(proxy_list_url):
    with requests_mock.Mocker() as m:
        m.get(proxy_list_url, text="proxy1\nproxy2")
        manager = ProxyManager(proxy_list_url)
        assert len(manager.proxies) == 2, "Should fetch and store two proxies"

def test_fetch_proxies_failure(proxy_list_url):
    with requests_mock.Mocker() as m:
        m.get(proxy_list_url, status_code=500)
        manager = ProxyManager(proxy_list_url)
        assert len(manager.proxies) == 0, "Should handle fetch failure gracefully"

def test_get_proxy(proxy_manager):
    proxy_manager.proxies = [{"http": "http://proxy1"}, {"http": "http://proxy2"}]
    selected_proxy = proxy_manager.get_proxy()
    assert selected_proxy in proxy_manager.proxies, "get_proxy should return a valid proxy"

def test_remove_proxy(proxy_manager):
    initial_proxy = {"http": "http://proxy1"}
    proxy_manager.proxies = [initial_proxy, {"http": "http://proxy2"}]
    proxy_manager.remove_proxy(initial_proxy)
    assert initial_proxy not in proxy_manager.proxies, "remove_proxy should remove the specified proxy"

def test_replace_proxy(proxy_manager):
    initial_proxies = [{"http": "http://proxy1"}, {"http": "http://proxy2"}]
    proxy_manager.proxies = list(initial_proxies)
    old_proxy = initial_proxies[0]
    proxy_manager.replace_proxy(old_proxy)
    assert old_proxy not in proxy_manager.proxies, "replace_proxy should remove the old proxy"
    assert len(proxy_manager.proxies) == 2, "replace_proxy should replace one proxy with another"
