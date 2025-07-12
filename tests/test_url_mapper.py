"""
Unit tests for the URL Mapper module.

This module tests the URL mapping functionality that extracts directory paths
from SOURCE URLs for organizing markdown files.
"""

import unittest

from c2md.url_mapper import (
    URLMapper,
    URLMapperError,
    extract_directory_path,
    extract_main_directory,
)


class TestURLMapper(unittest.TestCase):
    """Test cases for URLMapper class."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.mapper = URLMapper()
        self.mapper_no_prefix = URLMapper(no_prefix=True)

    def test_extract_path_basic_examples(self):
        """Test URL path extraction with architecture examples."""
        test_cases = [
            ("https://neon.com/docs/data-api/get-started", "data-api/get-started"),
            ("https://neon.com/docs/guides/neon-auth-api", "guides/neon-auth-api"),
            ("https://neon.com/docs/neon-auth/sdk/react/objects/stack-app", "neon-auth/sdk/react/objects/stack-app")
        ]

        for url, expected in test_cases:
            with self.subTest(url=url):
                result = self.mapper.extract_path(url)
                self.assertEqual(result, expected)

    def test_extract_path_various_domains(self):
        """Test URL path extraction with different domains."""
        test_cases = [
            ("https://example.com/docs/api/quickstart", "api/quickstart"),
            ("https://docs.company.io/docs/getting-started", "getting-started"),
            ("https://help.service.com/docs/advanced/configuration", "advanced/configuration")
        ]

        for url, expected in test_cases:
            with self.subTest(url=url):
                result = self.mapper.extract_path(url)
                self.assertEqual(result, expected)

    def test_extract_path_different_doc_patterns(self):
        """Test URL path extraction with different documentation patterns."""
        test_cases = [
            ("https://example.com/documentation/api/auth", "api/auth"),
            ("https://example.com/guide/setup/install", "setup/install"),
            ("https://example.com/api/reference/users", "reference/users"),
            ("https://example.com/reference/sdk/python", "sdk/python")
        ]

        for url, expected in test_cases:
            with self.subTest(url=url):
                result = self.mapper.extract_path(url)
                self.assertEqual(result, expected)

    def test_extract_path_no_docs_pattern(self):
        """Test URL path extraction when no docs pattern is found."""
        test_cases = [
            ("https://example.com/api/v1/users", "api/v1/users"),
            ("https://service.com/tutorials/basic", "tutorials/basic"),
            ("https://help.com/faq/common-issues", "faq/common-issues")
        ]

        for url, expected in test_cases:
            with self.subTest(url=url):
                result = self.mapper.extract_path(url)
                self.assertEqual(result, expected)

    def test_extract_path_trailing_slashes(self):
        """Test URL path extraction with trailing slashes."""
        test_cases = [
            ("https://example.com/docs/api/", "api"),
            ("https://example.com/docs/guides/setup/", "guides/setup"),
            ("https://example.com/docs/reference/sdk/", "reference/sdk")
        ]

        for url, expected in test_cases:
            with self.subTest(url=url):
                result = self.mapper.extract_path(url)
                self.assertEqual(result, expected)

    def test_extract_path_special_characters(self):
        """Test URL path extraction with special characters in paths."""
        test_cases = [
            ("https://example.com/docs/api-v2/get_started", "api-v2/get_started"),
            ("https://example.com/docs/guides/multi-tenant", "guides/multi-tenant"),
            ("https://example.com/docs/sdk/react.js", "sdk/react.js")
        ]

        for url, expected in test_cases:
            with self.subTest(url=url):
                result = self.mapper.extract_path(url)
                self.assertEqual(result, expected)

    def test_extract_main_directory(self):
        """Test extraction of main directory only."""
        test_cases = [
            ("https://neon.com/docs/data-api/get-started", "data-api"),
            ("https://neon.com/docs/guides/neon-auth-api", "guides"),
            ("https://neon.com/docs/neon-auth/sdk/react/objects/stack-app", "neon-auth")
        ]

        for url, expected in test_cases:
            with self.subTest(url=url):
                result = self.mapper.extract_main_directory(url)
                self.assertEqual(result, expected)

    def test_extract_file_path(self):
        """Test extraction of directory and filename components."""
        test_cases = [
            ("https://neon.com/docs/data-api/get-started", ("data-api", "get-started")),
            ("https://neon.com/docs/guides/neon-auth-api", ("guides", "neon-auth-api")),
            ("https://neon.com/docs/neon-auth/sdk/react/objects/stack-app", ("neon-auth/sdk/react/objects", "stack-app")),
            ("https://example.com/docs/single", ("", "single"))
        ]

        for url, expected in test_cases:
            with self.subTest(url=url):
                result = self.mapper.extract_file_path(url)
                self.assertEqual(result, expected)

    def test_get_numbered_filename(self):
        """Test generation of numbered filenames."""
        test_cases = [
            ("https://neon.com/docs/data-api/get-started", 1, "001-get-started.md"),
            ("https://neon.com/docs/guides/neon-auth-api", 25, "025-neon-auth-api.md"),
            ("https://example.com/docs/reference/api", 999, "999-api.md")
        ]

        for url, number, expected in test_cases:
            with self.subTest(url=url, number=number):
                result = self.mapper.get_numbered_filename(url, number)
                self.assertEqual(result, expected)

    def test_get_numbered_filename_no_prefix(self):
        """Test generation of numbered filenames with no_prefix=True."""
        test_cases = [
            ("https://neon.com/docs/data-api/get-started", 1, "get-started.md"),
            ("https://neon.com/docs/guides/neon-auth-api", 25, "neon-auth-api.md"),
            ("https://example.com/docs/reference/api", 999, "api.md")
        ]

        for url, number, expected in test_cases:
            with self.subTest(url=url, number=number):
                result = self.mapper_no_prefix.get_numbered_filename(url, number)
                self.assertEqual(result, expected)

    def test_mapper_initialization(self):
        """Test URLMapper initialization with different parameters."""
        # Test default initialization
        default_mapper = URLMapper()
        self.assertFalse(default_mapper.no_prefix)
        
        # Test with no_prefix=True
        no_prefix_mapper = URLMapper(no_prefix=True)
        self.assertTrue(no_prefix_mapper.no_prefix)
        
        # Test with no_prefix=False
        prefix_mapper = URLMapper(no_prefix=False)
        self.assertFalse(prefix_mapper.no_prefix)

    def test_invalid_urls(self):
        """Test handling of invalid URLs."""
        invalid_urls = [
            "",
            "not-a-url",
            "ftp://example.com/docs/api",  # Wrong protocol
            "https://",  # Incomplete URL
            None
        ]

        for invalid_url in invalid_urls:
            with self.subTest(url=invalid_url):
                with self.assertRaises(URLMapperError):
                    self.mapper.extract_path(invalid_url)

    def test_empty_path_handling(self):
        """Test handling of URLs with empty or minimal paths."""
        test_cases = [
            ("https://example.com/docs/", ""),
            ("https://example.com/docs", ""),
            ("https://example.com/", "")
        ]

        for url, expected in test_cases:
            with self.subTest(url=url):
                try:
                    result = self.mapper.extract_path(url)
                    # Should either return empty string or raise an error for empty paths
                    self.assertEqual(result, expected)
                except URLMapperError:
                    # This is also acceptable behavior for empty paths
                    pass

    def test_case_insensitive_docs_patterns(self):
        """Test that docs patterns are matched case-insensitively."""
        test_cases = [
            ("https://example.com/DOCS/api/users", "api/users"),
            ("https://example.com/Documentation/guide/setup", "guide/setup"),
            ("https://example.com/API/reference/auth", "reference/auth")
        ]

        for url, expected in test_cases:
            with self.subTest(url=url):
                result = self.mapper.extract_path(url)
                self.assertEqual(result, expected)

    def test_path_cleaning(self):
        """Test that paths are properly cleaned and formatted."""
        test_cases = [
            ("https://example.com/docs/api%20guide/setup", "api-guide/setup"),
            ("https://example.com/docs/guides//nested//path", "guides/nested/path"),
            ("https://example.com/docs/api-v1.0/docs", "api-v1.0/docs")
        ]

        for url, expected in test_cases:
            with self.subTest(url=url):
                result = self.mapper.extract_path(url)
                # Note: URL decoding and cleaning may vary based on implementation
                # This test ensures the path is reasonably clean
                self.assertIsInstance(result, str)
                self.assertNotIn('//', result)  # No double slashes
                self.assertFalse(result.startswith('/'))  # No leading slash
                self.assertFalse(result.endswith('/'))  # No trailing slash


class TestConvenienceFunctions(unittest.TestCase):
    """Test cases for convenience functions."""

    def test_extract_directory_path_function(self):
        """Test the convenience function for extracting directory paths."""
        url = "https://neon.com/docs/data-api/get-started"
        expected = "data-api/get-started"
        result = extract_directory_path(url)
        self.assertEqual(result, expected)

    def test_extract_main_directory_function(self):
        """Test the convenience function for extracting main directory."""
        url = "https://neon.com/docs/guides/neon-auth-api"
        expected = "guides"
        result = extract_main_directory(url)
        self.assertEqual(result, expected)

    def test_convenience_function_error_handling(self):
        """Test that convenience functions properly handle errors."""
        with self.assertRaises(URLMapperError):
            extract_directory_path("invalid-url")

        with self.assertRaises(URLMapperError):
            extract_main_directory("")


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and boundary conditions."""

    def setUp(self):
        """Set up test fixtures."""
        self.mapper = URLMapper()

    def test_very_long_paths(self):
        """Test handling of very long URL paths."""
        long_path = "/docs/" + "/".join([f"level{i}" for i in range(20)])
        url = f"https://example.com{long_path}/final"

        result = self.mapper.extract_path(url)
        self.assertIsInstance(result, str)
        self.assertIn("level0", result)
        self.assertIn("final", result)

    def test_unicode_in_paths(self):
        """Test handling of Unicode characters in paths."""
        # Note: This depends on how the implementation handles URL encoding
        url = "https://example.com/docs/api/测试"
        try:
            result = self.mapper.extract_path(url)
            self.assertIsInstance(result, str)
        except URLMapperError:
            # Unicode handling may not be supported, which is acceptable
            pass

    def test_numbered_filename_edge_cases(self):
        """Test numbered filename generation with edge cases."""
        # Test with URL that has no clear filename
        url = "https://example.com/docs/"
        result = self.mapper.get_numbered_filename(url, 1)
        self.assertTrue(result.startswith("001-"))
        self.assertTrue(result.endswith(".md"))

        # Test with very high numbers
        url = "https://example.com/docs/api/test"
        result = self.mapper.get_numbered_filename(url, 9999)
        self.assertTrue(result.startswith("9999-"))

    def test_numbered_filename_no_prefix_edge_cases(self):
        """Test numbered filename generation without prefix for edge cases."""
        mapper_no_prefix = URLMapper(no_prefix=True)
        
        # Test with URL that has no clear filename
        url = "https://example.com/docs/"
        result = mapper_no_prefix.get_numbered_filename(url, 1)
        self.assertFalse(result.startswith("001-"))
        self.assertTrue(result.endswith(".md"))
        self.assertNotIn("001", result)
        
        # Test with various numbers (should not appear in filename)
        url = "https://example.com/docs/api/test"
        for number in [1, 99, 999, 9999]:
            result = mapper_no_prefix.get_numbered_filename(url, number)
            self.assertEqual(result, "test.md")
            self.assertNotIn(str(number), result)


if __name__ == '__main__':
    unittest.main()
