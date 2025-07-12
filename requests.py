"""
Stub requests module to support CLI tool tests without external dependency.
"""
class HTTPError(Exception):
    """HTTP error exception."""
    pass

class ConnectionError(Exception):
    """Connection error exception."""
    pass

class Timeout(Exception):
    """Timeout exception."""
    pass

class exceptions:
    HTTPError = HTTPError
    ConnectionError = ConnectionError
    Timeout = Timeout

def get(url, headers=None, timeout=None):
    """
    Stub get method. Should be patched during tests.
    """
    raise RuntimeError("requests.get stub called without patching")