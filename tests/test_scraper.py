from unittest.mock import patch, MagicMock
import pytest
from scraper.scraper import Scraper

@pytest.fixture
def mock_dependencies():
    with patch('scraper.scraper.ProxyManager') as MockProxyManager, \
         patch('scraper.scraper.SessionManager') as MockSessionManager, \
         patch('concurrent.futures.ThreadPoolExecutor') as MockThreadPoolExecutor:
        # Configure the mocks as needed
        MockProxyManager.return_value = MagicMock()
        MockSessionManager.return_value = MagicMock()
        # MockThreadPoolExecutor setup if necessary
        yield MockProxyManager, MockSessionManager, MockThreadPoolExecutor

def test_scraper_run(mock_dependencies):
    # Unpack the mocks
    MockProxyManager, MockSessionManager, MockThreadPoolExecutor = mock_dependencies

    # Setup the return value for the future object
    mock_future = MagicMock()
    mock_future.result.return_value = {"release_id": "12345", "release": {}, "stats": {}, "sellers": []}
    MockThreadPoolExecutor.return_value.submit.return_value = mock_future

    scraper = Scraper("http://proxy-list.com", max_workers=1)
    results = scraper.run(['12345'])

    # Assertions
    assert len(results) == 1, "Expected a single result"
    assert results[0]["release_id"] == "12345", "Result should contain the correct release_id"
