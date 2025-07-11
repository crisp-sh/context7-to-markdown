"""Test URL support functionality."""

import unittest
from unittest.mock import patch, Mock
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from c2md.__main__ import (
    is_url,
    validate_and_transform_context7_url,
    ensure_tokens_parameter,
    download_context7_content
)


class TestURLSupport(unittest.TestCase):
    """Test URL support functions."""

    def test_is_url(self):
        """Test URL detection."""
        # Valid URLs
        assert is_url("https://context7.com/project/llms.txt") is True
        assert is_url("http://example.com") is True
        assert is_url("https://example.com/path/to/file") is True
        
        # Invalid URLs
        assert is_url("not-a-url") is False
        assert is_url("/path/to/file") is False
        assert is_url("file.txt") is False
        assert is_url("") is False

    def test_validate_and_transform_context7_url(self):
        """Test context7.com URL validation and transformation."""
        # Valid context7 URLs with full path
        is_valid, url = validate_and_transform_context7_url("https://context7.com/org/project/llms.txt")
        assert is_valid is True
        assert url == "https://context7.com/org/project/llms.txt?tokens=999999999"
        
        # Valid context7 URLs with short path (should be transformed)
        is_valid, url = validate_and_transform_context7_url("https://context7.com/org/project")
        assert is_valid is True
        assert url == "https://context7.com/org/project/llms.txt?tokens=999999999"
        
        # Invalid URLs - wrong domain
        is_valid, url = validate_and_transform_context7_url("https://example.com/org/project/llms.txt")
        assert is_valid is False
        assert url == ""
        
        # Invalid URLs - only one path segment
        is_valid, url = validate_and_transform_context7_url("https://context7.com/project/llms.txt")
        assert is_valid is False
        assert url == ""
        
        # Invalid URLs - only one path segment without llms.txt
        is_valid, url = validate_and_transform_context7_url("https://context7.com/project")
        assert is_valid is False
        assert url == ""
        
        # Valid URL with existing tokens parameter
        is_valid, url = validate_and_transform_context7_url("https://context7.com/org/project/llms.txt?tokens=12345")
        assert is_valid is True
        assert url == "https://context7.com/org/project/llms.txt?tokens=12345"
        
        # HTTP is allowed
        is_valid, url = validate_and_transform_context7_url("http://context7.com/org/project/llms.txt")
        assert is_valid is True
        assert url == "http://context7.com/org/project/llms.txt?tokens=999999999"

    def test_ensure_tokens_parameter(self):
        """Test tokens parameter addition."""
        # URL without tokens parameter
        url = "https://context7.com/project/llms.txt"
        result = ensure_tokens_parameter(url)
        assert "tokens=999999999" in result
        
        # URL with existing tokens parameter
        url = "https://context7.com/project/llms.txt?tokens=12345"
        result = ensure_tokens_parameter(url)
        assert "tokens=12345" in result
        assert "tokens=999999999" not in result
        
        # URL with other parameters
        url = "https://context7.com/project/llms.txt?other=value"
        result = ensure_tokens_parameter(url)
        assert "tokens=999999999" in result
        assert "other=value" in result

    @patch('c2md.__main__.requests')
    def test_download_context7_content_success(self, mock_requests):
        """Test successful content download."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "TITLE: Test\nDESCRIPTION: Test content"
        mock_response.content = b"Test content"
        mock_requests.get.return_value = mock_response
        
        url = "https://context7.com/project/llms.txt"
        content = download_context7_content(url)
        
        assert content == "TITLE: Test\nDESCRIPTION: Test content"
        # Verify tokens parameter was added
        mock_requests.get.assert_called_once()
        call_args = mock_requests.get.call_args
        assert "tokens=999999999" in call_args[0][0]

    def test_download_context7_content_error(self):
        """Test download error handling."""
        with patch('c2md.__main__.requests') as mock_requests:
            # Import real requests to get exception classes
            import requests as real_requests
            
            # Set up the exceptions on the mock
            mock_requests.exceptions = real_requests.exceptions
            
            # Create a connection error
            mock_requests.get.side_effect = real_requests.exceptions.ConnectionError("Network error")
            
            url = "https://context7.com/project/llms.txt"
            with self.assertRaises(RuntimeError) as context:
                download_context7_content(url)
            
            self.assertIn("Connection error", str(context.exception))
    
    @patch('c2md.__main__.requests')
    def test_various_context7_url_patterns(self, mock_requests):
        """Test various context7.com URL patterns (simulating test_context7_api.py)."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "TITLE: Test\nDESCRIPTION: Test content"
        mock_response.content = b"Test content"
        mock_response.headers = {'content-type': 'text/plain'}
        mock_requests.get.return_value = mock_response
        
        # Test patterns that should work after transformation
        test_urls = [
            "https://context7.com/vercel/next.js",
            "https://context7.com/org/project",
        ]
        
        for url in test_urls:
            is_valid, transformed_url = validate_and_transform_context7_url(url)
            self.assertTrue(is_valid, f"URL {url} should be valid")
            content = download_context7_content(transformed_url)
            self.assertIsNotNone(content)
            self.assertIn("TITLE:", content)
    
    @patch('c2md.__main__.requests')
    def test_content_inspection(self, mock_requests):
        """Test content inspection functionality (simulating test_downloaded_content.py)."""
        # Mock response with realistic llms.txt content
        test_content = """TITLE: Test Library
DESCRIPTION: A test library for unit testing
TAGS: test, unittest, python

# Test Library Documentation

This is a sample content for testing purposes.
It contains multiple lines and sections.

## Installation
```bash
pip install test-library
```

## Usage
```python
import test_library
test_library.run()
```
"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = test_content
        mock_response.content = test_content.encode('utf-8')
        mock_requests.get.return_value = mock_response
        
        url = "https://context7.com/test/library/llms.txt"
        content = download_context7_content(url)
        
        # Test content characteristics
        self.assertGreater(len(content), 100, "Content should have substantial length")
        self.assertGreater(len(content.splitlines()), 5, "Content should have multiple lines")
        self.assertIn("TITLE:", content, "Content should have TITLE field")
        self.assertIn("DESCRIPTION:", content, "Content should have DESCRIPTION field")
        self.assertIn("TAGS:", content, "Content should have TAGS field")
        
        # Test that we can get first 1000 characters (like the manual test does)
        first_1000 = content[:1000]
        self.assertLessEqual(len(first_1000), 1000)
        self.assertIn("TITLE:", first_1000)
    
    def test_http_error_handling(self):
        """Test HTTP error responses."""
        with patch('c2md.__main__.requests') as mock_requests:
            import requests as real_requests
            mock_requests.exceptions = real_requests.exceptions
            
            # Mock 404 response
            mock_response = Mock()
            mock_response.status_code = 404
            mock_response.raise_for_status.side_effect = real_requests.exceptions.HTTPError("404 Not Found")
            mock_requests.get.return_value = mock_response
            
            url = "https://context7.com/nonexistent/project/llms.txt"
            with self.assertRaises(RuntimeError) as context:
                download_context7_content(url)
            
            self.assertIn("HTTP error", str(context.exception))


if __name__ == '__main__':
    unittest.main()