import pytest
from unittest.mock import patch, MagicMock
from managers.session_manager import SessionManager
from managers.proxy_manager import ProxyManager
import time

@pytest.fixture
def mock_proxy_manager(mocker):
    proxy_manager = MagicMock(spec=ProxyManager)
    # Return a string identifier for the proxy instead of a dict
    mocker.patch.object(proxy_manager, 'get_proxy', return_value='http://mockproxy:8080')
    return proxy_manager

def test_session_creation_and_recycling(mock_proxy_manager):
    session_manager = SessionManager(mock_proxy_manager, rate_limit_per_minute=60)
    first_session = session_manager.get_session(use_proxy=True)
    assert first_session is not None, "Session should be created."

    # Sleep to simulate passage of time (if needed)
    second_session = session_manager.get_session(use_proxy=True)
    assert first_session == second_session, "Should recycle the session when within rate limits."

def test_rate_limiting(mock_proxy_manager):
    session_manager = SessionManager(mock_proxy_manager, rate_limit_per_minute=1)
    session_manager.get_session(use_proxy=True)

    with patch('time.sleep', autospec=True) as mock_sleep:
        session_manager.get_session(use_proxy=True)
        mock_sleep.assert_called()

def test_session_request_time_update(mock_proxy_manager):
    session_manager = SessionManager(mock_proxy_manager, rate_limit_per_minute=30)
    session_manager.get_session(use_proxy=True)
    # Using the string identifier directly as returned by get_proxy mock
    identifier = 'http://mockproxy:8080'
    
    initial_last_used = session_manager.sessions[identifier]['last_used']
    # Sleep to ensure time difference is measurable
    time.sleep(1)
    session_manager.get_session(use_proxy=True)
    
    assert session_manager.sessions[identifier]['last_used'] > initial_last_used, "Session last used time should be updated."

@pytest.mark.parametrize("use_proxy", [True, False])
def test_unique_session_per_proxy_key(mock_proxy_manager, use_proxy):
    session_manager = SessionManager(mock_proxy_manager, rate_limit_per_minute=30)
    session1 = session_manager.get_session(use_proxy=use_proxy)
    session2 = session_manager.get_session(use_proxy=not use_proxy)
    
    assert session1 != session2, "Sessions should differ based on proxy use."
