"""
Unit tests for the Context7 parser module.

This module contains comprehensive tests for parsing Context7 format files,
including edge cases, error handling, and malformed entries.
"""

import unittest
import tempfile
import os
from unittest.mock import patch, mock_open
from typing import List, Dict, Any

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from parser import (
    Context7Parser,
    Context7ParseError,
    parse_context7_file,
    parse_context7_content
)


class TestContext7Parser(unittest.TestCase):
    """Test cases for Context7Parser class."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.parser = Context7Parser()

    def test_parser_initialization(self):
        """Test that parser initializes correctly."""
        self.assertEqual(self.parser.entries, [])
        self.assertEqual(self.parser.original_order, 0)
        self.assertEqual(self.parser.ENTRY_DELIMITER, "----------------------------------------")

    def test_parse_valid_single_entry(self):
        """Test parsing a single valid Context7 entry."""
        content = """TITLE: Sample Entry
DESCRIPTION: This is a test entry
SOURCE: https://example.com/docs/sample
LANGUAGE: python
CODE:
print("Hello, World!")
"""
        entries = self.parser.parse_content(content)
        
        self.assertEqual(len(entries), 1)
        entry = entries[0]
        
        self.assertEqual(entry['title'], 'Sample Entry')
        self.assertEqual(entry['description'], 'This is a test entry')
        self.assertEqual(entry['source'], 'https://example.com/docs/sample')
        self.assertEqual(entry['language'], 'python')
        self.assertEqual(entry['code'], 'print("Hello, World!")')
        self.assertEqual(entry['original_order'], 0)

    def test_parse_multiple_entries_with_delimiter(self):
        """Test parsing multiple entries separated by delimiter."""
        content = """TITLE: First Entry
DESCRIPTION: First test entry
SOURCE: https://example.com/docs/first
LANGUAGE: python
CODE:
print("First")

----------------------------------------

TITLE: Second Entry
DESCRIPTION: Second test entry
SOURCE: https://example.com/docs/second
LANGUAGE: javascript
CODE:
console.log("Second");
"""
        entries = self.parser.parse_content(content)
        
        self.assertEqual(len(entries), 2)
        
        # Check first entry
        self.assertEqual(entries[0]['title'], 'First Entry')
        self.assertEqual(entries[0]['original_order'], 0)
        
        # Check second entry
        self.assertEqual(entries[1]['title'], 'Second Entry')
        self.assertEqual(entries[1]['language'], 'javascript')
        self.assertEqual(entries[1]['original_order'], 1)

    def test_parse_entry_with_multiline_description(self):
        """Test parsing entry with multi-line description."""
        content = """TITLE: Complex Entry
DESCRIPTION: This is a multi-line description
that spans several lines and contains
detailed information about the entry
SOURCE: https://example.com/docs/complex
LANGUAGE: python
CODE:
def complex_function():
    return "complex"
"""
        entries = self.parser.parse_content(content)
        
        self.assertEqual(len(entries), 1)
        expected_desc = "This is a multi-line description that spans several lines and contains detailed information about the entry"
        self.assertEqual(entries[0]['description'], expected_desc)

    def test_parse_entry_with_empty_code_block(self):
        """Test parsing entry with empty code block."""
        content = """TITLE: Empty Code Entry
DESCRIPTION: This entry has empty code
SOURCE: https://example.com/docs/empty
LANGUAGE: text
CODE:
"""
        entries = self.parser.parse_content(content)
        
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]['code'], '')

    def test_parse_entry_with_code_containing_blank_lines(self):
        """Test parsing entry with code that contains blank lines."""
        content = """TITLE: Code with Blanks
DESCRIPTION: Code containing blank lines
SOURCE: https://example.com/docs/blanks
LANGUAGE: python
CODE:
def function():
    print("start")
    
    print("middle")
    
    print("end")
"""
        entries = self.parser.parse_content(content)
        
        self.assertEqual(len(entries), 1)
        expected_code = '''def function():
    print("start")
    
    print("middle")
    
    print("end")'''
        self.assertEqual(entries[0]['code'], expected_code)

    def test_skip_malformed_entry_missing_title(self):
        """Test that entries without titles are skipped."""
        content = """DESCRIPTION: Missing title
SOURCE: https://example.com/docs/missing
LANGUAGE: python
CODE:
print("no title")
"""
        entries = self.parser.parse_content(content)
        
        self.assertEqual(len(entries), 0)

    def test_skip_malformed_entry_missing_source(self):
        """Test that entries without source URLs are skipped."""
        content = """TITLE: Missing Source
DESCRIPTION: This entry has no source
LANGUAGE: python
CODE:
print("no source")
"""
        entries = self.parser.parse_content(content)
        
        self.assertEqual(len(entries), 0)

    def test_skip_malformed_entry_invalid_source_url(self):
        """Test that entries with invalid source URLs are skipped."""
        content = """TITLE: Invalid Source
DESCRIPTION: This entry has invalid source
SOURCE: not-a-valid-url
LANGUAGE: python
CODE:
print("invalid source")
"""
        entries = self.parser.parse_content(content)
        
        self.assertEqual(len(entries), 0)

    def test_parse_mixed_valid_and_invalid_entries(self):
        """Test parsing content with mix of valid and invalid entries."""
        content = """TITLE: Valid Entry
DESCRIPTION: This is valid
SOURCE: https://example.com/docs/valid
LANGUAGE: python
CODE:
print("valid")

----------------------------------------

DESCRIPTION: Missing title
SOURCE: https://example.com/docs/invalid
LANGUAGE: python
CODE:
print("invalid")

----------------------------------------

TITLE: Another Valid Entry
DESCRIPTION: This is also valid
SOURCE: https://example.com/docs/valid2
LANGUAGE: javascript
CODE:
console.log("valid");
"""
        entries = self.parser.parse_content(content)
        
        # Should only parse the 2 valid entries
        self.assertEqual(len(entries), 2)
        self.assertEqual(entries[0]['title'], 'Valid Entry')
        self.assertEqual(entries[1]['title'], 'Another Valid Entry')

    def test_parse_empty_content(self):
        """Test parsing empty content."""
        entries = self.parser.parse_content("")
        self.assertEqual(len(entries), 0)

    def test_parse_content_with_only_delimiters(self):
        """Test parsing content with only delimiters."""
        content = "----------------------------------------\n----------------------------------------"
        entries = self.parser.parse_content(content)
        self.assertEqual(len(entries), 0)

    def test_case_insensitive_field_parsing(self):
        """Test that field names are parsed case-insensitively."""
        content = """title: Case Test
description: Testing case insensitivity
source: https://example.com/docs/case
language: Python
code:
print("case test")
"""
        entries = self.parser.parse_content(content)
        
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]['title'], 'Case Test')
        self.assertEqual(entries[0]['language'], 'Python')

    def test_https_and_http_urls_valid(self):
        """Test that both HTTPS and HTTP URLs are accepted."""
        content_https = """TITLE: HTTPS Test
DESCRIPTION: Testing HTTPS URL
SOURCE: https://example.com/docs/https
LANGUAGE: python
CODE:
print("https")
"""
        
        content_http = """TITLE: HTTP Test
DESCRIPTION: Testing HTTP URL
SOURCE: http://example.com/docs/http
LANGUAGE: python
CODE:
print("http")
"""
        
        entries_https = self.parser.parse_content(content_https)
        entries_http = self.parser.parse_content(content_http)
        
        self.assertEqual(len(entries_https), 1)
        self.assertEqual(len(entries_http), 1)

    def test_create_sample_entry(self):
        """Test the static method for creating sample entries."""
        sample = Context7Parser.create_sample_entry()
        
        self.assertIn('title', sample)
        self.assertIn('description', sample)
        self.assertIn('source', sample)
        self.assertIn('language', sample)
        self.assertIn('code', sample)
        self.assertIn('original_order', sample)
        
        # Validate sample entry
        self.assertTrue(sample['title'])
        self.assertTrue(sample['source'].startswith('http'))

    def test_parse_file_success(self):
        """Test successful file parsing."""
        content = """TITLE: File Test
DESCRIPTION: Testing file parsing
SOURCE: https://example.com/docs/file
LANGUAGE: python
CODE:
print("file test")
"""
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as temp_file:
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            entries = self.parser.parse_file(temp_file_path)
            self.assertEqual(len(entries), 1)
            self.assertEqual(entries[0]['title'], 'File Test')
        finally:
            os.unlink(temp_file_path)

    def test_parse_file_not_found(self):
        """Test parsing non-existent file raises error."""
        with self.assertRaises(Context7ParseError) as context:
            self.parser.parse_file('/non/existent/file.txt')
        
        self.assertIn('File not found', str(context.exception))

    def test_parse_file_permission_error(self):
        """Test parsing file with permission error."""
        with patch('builtins.open', mock_open()) as mock_file:
            mock_file.side_effect = PermissionError("Permission denied")
            
            with self.assertRaises(Context7ParseError) as context:
                self.parser.parse_file('/restricted/file.txt')
            
            self.assertIn('Error reading file', str(context.exception))

    def test_convenience_function_parse_context7_file(self):
        """Test the convenience function for parsing files."""
        content = """TITLE: Convenience Test
DESCRIPTION: Testing convenience function
SOURCE: https://example.com/docs/convenience
LANGUAGE: python
CODE:
print("convenience")
"""
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as temp_file:
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            entries = parse_context7_file(temp_file_path)
            self.assertEqual(len(entries), 1)
            self.assertEqual(entries[0]['title'], 'Convenience Test')
        finally:
            os.unlink(temp_file_path)

    def test_convenience_function_parse_context7_content(self):
        """Test the convenience function for parsing content."""
        content = """TITLE: Content Test
DESCRIPTION: Testing content parsing
SOURCE: https://example.com/docs/content
LANGUAGE: python
CODE:
print("content")
"""
        
        entries = parse_context7_content(content)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]['title'], 'Content Test')

    def test_original_order_increments_correctly(self):
        """Test that original_order increments correctly even with skipped entries."""
        content = """TITLE: First
DESCRIPTION: First entry
SOURCE: https://example.com/docs/1
LANGUAGE: python
CODE:
print("1")

----------------------------------------

DESCRIPTION: Invalid - no title
SOURCE: https://example.com/docs/invalid
LANGUAGE: python
CODE:
print("invalid")

----------------------------------------

TITLE: Third
DESCRIPTION: Third entry  
SOURCE: https://example.com/docs/3
LANGUAGE: python
CODE:
print("3")
"""
        entries = self.parser.parse_content(content)
        
        # Should have 2 valid entries
        self.assertEqual(len(entries), 2)
        
        # But original_order should still reflect all processed entries
        self.assertEqual(entries[0]['original_order'], 0)
        self.assertEqual(entries[1]['original_order'], 2)

    def test_code_block_with_markdown_style_fences(self):
        """Test parsing code blocks that contain markdown-style code fences."""
        content = """TITLE: Markdown Test
DESCRIPTION: Code with markdown fences
SOURCE: https://example.com/docs/markdown
LANGUAGE: markdown
CODE:
```python
def example():
    return "nested code"
```
"""
        entries = self.parser.parse_content(content)
        
        self.assertEqual(len(entries), 1)
        expected_code = '''```python
def example():
    return "nested code"
```'''
        self.assertEqual(entries[0]['code'], expected_code)

    def test_whitespace_handling(self):
        """Test proper handling of whitespace in fields and code."""
        content = """TITLE:   Whitespace Test   
DESCRIPTION:   Testing whitespace handling   
SOURCE:   https://example.com/docs/whitespace   
LANGUAGE:   python   
CODE:
   # Code with leading/trailing whitespace   
   print("test")   
"""
        entries = self.parser.parse_content(content)
        
        self.assertEqual(len(entries), 1)
        entry = entries[0]
        
        # Fields should be stripped
        self.assertEqual(entry['title'], 'Whitespace Test')
        self.assertEqual(entry['description'], 'Testing whitespace handling')
        self.assertEqual(entry['source'], 'https://example.com/docs/whitespace')
        self.assertEqual(entry['language'], 'python')
        
        # Code should preserve internal whitespace but trim empty lines
        expected_code = '   # Code with leading/trailing whitespace   \n   print("test")'
        self.assertEqual(entry['code'], expected_code)


class TestContext7ParseError(unittest.TestCase):
    """Test cases for Context7ParseError exception."""

    def test_parse_error_creation(self):
        """Test that Context7ParseError can be created and raised."""
        with self.assertRaises(Context7ParseError) as context:
            raise Context7ParseError("Test error message")
        
        self.assertEqual(str(context.exception), "Test error message")

    def test_parse_error_inheritance(self):
        """Test that Context7ParseError inherits from Exception."""
        error = Context7ParseError("Test")
        self.assertIsInstance(error, Exception)


if __name__ == '__main__':
    # Create a test suite
    suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])
    
    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)