"""
Unit tests for the FileOrganizer module.

Tests cover file organization logic, numbering schemes, directory structure creation,
and integration with URLMapper.
"""

import os
import sys
import unittest
from unittest.mock import Mock, patch

# Add src to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from c2md.file_organizer import (
    FileOrganizer,
    FileOrganizerError,
    OrganizedFile,
    organize_context7_entries,
)
from c2md.url_mapper import URLMapper


class TestOrganizedFile(unittest.TestCase):
    """Test cases for OrganizedFile class."""

    def setUp(self):
        """Set up test fixtures."""
        self.sample_entry = {
            'title': 'Test Entry',
            'description': 'Test description',
            'source': 'https://example.com/docs/api/test',
            'language': 'python',
            'code': 'print("test")',
            'original_order': 0
        }

    def test_organized_file_creation(self):
        """Test OrganizedFile creation with valid data."""
        organized_file = OrganizedFile(
            entry=self.sample_entry,
            directory_path='api',
            filename='001-test.md',
            number=1
        )

        self.assertEqual(organized_file.entry, self.sample_entry)
        self.assertEqual(organized_file.directory_path, 'api')
        self.assertEqual(organized_file.filename, '001-test.md')
        self.assertEqual(organized_file.number, 1)
        self.assertEqual(organized_file.full_path, 'api/001-test.md')

    def test_organized_file_root_directory(self):
        """Test OrganizedFile with empty directory path (root)."""
        organized_file = OrganizedFile(
            entry=self.sample_entry,
            directory_path='',
            filename='001-test.md',
            number=1
        )

        self.assertEqual(organized_file.full_path, '001-test.md')

    def test_organized_file_repr(self):
        """Test string representation of OrganizedFile."""
        organized_file = OrganizedFile(
            entry=self.sample_entry,
            directory_path='api',
            filename='001-test.md',
            number=1
        )

        repr_str = repr(organized_file)
        self.assertIn('001-test.md', repr_str)
        self.assertIn('Test Entry', repr_str)


class TestFileOrganizer(unittest.TestCase):
    """Test cases for FileOrganizer class."""

    def setUp(self):
        """Set up test fixtures."""
        self.file_organizer = FileOrganizer()
        self.sample_entries = [
            {
                'title': 'API Getting Started',
                'description': 'Introduction to the API',
                'source': 'https://example.com/docs/api/getting-started',
                'language': 'python',
                'code': 'import requests',
                'original_order': 0
            },
            {
                'title': 'API Reference',
                'description': 'Complete API reference',
                'source': 'https://example.com/docs/api/reference',
                'language': 'python',
                'code': 'def api_call(): pass',
                'original_order': 1
            },
            {
                'title': 'Guide Overview',
                'description': 'Guide to using the service',
                'source': 'https://example.com/docs/guides/overview',
                'language': 'markdown',
                'code': '# Overview',
                'original_order': 2
            }
        ]

    def test_file_organizer_initialization(self):
        """Test FileOrganizer initialization."""
        # Test with default URLMapper
        organizer = FileOrganizer()
        self.assertIsInstance(organizer.url_mapper, URLMapper)
        self.assertFalse(organizer.no_prefix)  # Default should be False

        # Test with custom URLMapper
        custom_mapper = URLMapper()
        organizer = FileOrganizer(custom_mapper)
        self.assertEqual(organizer.url_mapper, custom_mapper)
        
        # Test with no_prefix=True
        organizer_no_prefix = FileOrganizer(no_prefix=True)
        self.assertTrue(organizer_no_prefix.no_prefix)
        self.assertTrue(organizer_no_prefix.url_mapper.no_prefix)

    def test_organize_entries_basic(self):
        """Test basic entry organization."""
        result = self.file_organizer.organize_entries(self.sample_entries)

        # Should have two directories: 'api' and 'guides'
        self.assertEqual(len(result), 2)
        self.assertIn('api', result)
        self.assertIn('guides', result)

        # Check API directory
        api_files = result['api']
        self.assertEqual(len(api_files), 2)
        self.assertIsInstance(api_files[0], OrganizedFile)
        self.assertIsInstance(api_files[1], OrganizedFile)

        # Check numbering
        self.assertEqual(api_files[0].number, 1)
        self.assertEqual(api_files[1].number, 2)

        # Check guides directory
        guides_files = result['guides']
        self.assertEqual(len(guides_files), 1)
        self.assertEqual(guides_files[0].number, 1)

    def test_organize_entries_empty_list(self):
        """Test organizing empty list of entries."""
        result = self.file_organizer.organize_entries([])
        self.assertEqual(result, {})

    def test_organize_entries_invalid_input(self):
        """Test organizing with invalid input."""
        with self.assertRaises(FileOrganizerError):
            self.file_organizer.organize_entries("not a list")  # type: ignore

    def test_organize_entries_missing_source(self):
        """Test organizing entries with missing source URLs."""
        entries_without_source = [
            {
                'title': 'No Source Entry',
                'description': 'Entry without source',
                'source': '',
                'language': 'python',
                'code': 'print("no source")',
                'original_order': 0
            }
        ]

        result = self.file_organizer.organize_entries(entries_without_source)

        # Should be placed in root directory (empty string key)
        self.assertIn('', result)
        self.assertEqual(len(result['']), 1)

    def test_organize_entries_url_mapping_error(self):
        """Test organizing entries when URL mapping fails."""
        # Mock URLMapper to raise exception
        mock_mapper = Mock(spec=URLMapper)
        mock_mapper.extract_path.side_effect = Exception("URL mapping failed")

        organizer = FileOrganizer(mock_mapper)

        # Should handle the error gracefully and place in root
        with patch('builtins.print'):  # Suppress warning print
            result = organizer.organize_entries(self.sample_entries)

        # All entries should be in root directory
        self.assertIn('', result)
        self.assertEqual(len(result['']), 3)

    def test_group_by_directory(self):
        """Test grouping entries by directory."""
        grouped = self.file_organizer._group_by_directory(self.sample_entries)

        self.assertEqual(len(grouped), 2)
        self.assertIn('api', grouped)
        self.assertIn('guides', grouped)
        self.assertEqual(len(grouped['api']), 2)
        self.assertEqual(len(grouped['guides']), 1)

    def test_generate_filename_with_url(self):
        """Test filename generation with valid URL."""
        entry = {
            'title': 'Test Entry',
            'source': 'https://example.com/docs/api/test-endpoint',
            'original_order': 0
        }

        filename = self.file_organizer._generate_filename(entry, 1)
        self.assertEqual(filename, '001-test-endpoint.md')

    def test_generate_filename_without_url(self):
        """Test filename generation without URL."""
        entry = {
            'title': 'Test Entry Title',
            'source': '',
            'original_order': 0
        }

        filename = self.file_organizer._generate_filename(entry, 1)
        self.assertEqual(filename, '001-test-entry-title.md')

    def test_generate_filename_url_error(self):
        """Test filename generation when URL processing fails."""
        entry = {
            'title': 'Test Entry',
            'source': 'invalid-url',
            'original_order': 0
        }

        filename = self.file_organizer._generate_filename(entry, 1)
        self.assertEqual(filename, '001-test-entry.md')

    def test_clean_filename(self):
        """Test filename cleaning function."""
        # Test various cleaning scenarios
        test_cases = [
            ('Normal Title', 'normal-title'),
            ('Title with $pecial Ch@rs!', 'title-with-pecial-chrs'),
            ('Multiple   Spaces', 'multiple-spaces'),
            ('Title---with---dashes', 'title-with-dashes'),
            ('', 'untitled'),
            ('   ', 'untitled'),
            ('Title With CAPS', 'title-with-caps')
        ]

        for input_title, expected in test_cases:
            with self.subTest(input_title=input_title):
                result = self.file_organizer._clean_filename(input_title)
                self.assertEqual(result, expected)

    def test_get_directory_summary(self):
        """Test directory summary generation."""
        organized_structure = self.file_organizer.organize_entries(self.sample_entries)
        summary = self.file_organizer.get_directory_summary(organized_structure)

        self.assertIn('total_files', summary)
        self.assertIn('total_directories', summary)
        self.assertIn('directories', summary)
        self.assertIn('structure_preview', summary)

        self.assertEqual(summary['total_files'], 3)
        self.assertEqual(summary['total_directories'], 2)
        self.assertIn('api', summary['directories'])
        self.assertIn('guides', summary['directories'])

    def test_reset_counters(self):
        """Test resetting directory counters."""
        # Organize entries to populate counters
        self.file_organizer.organize_entries(self.sample_entries)

        # Check that counters have values
        self.assertGreater(len(self.file_organizer._directory_counters), 0)

        # Reset counters
        self.file_organizer.reset_counters()

        # Check that counters are cleared
        self.assertEqual(len(self.file_organizer._directory_counters), 0)

    def test_consistent_numbering(self):
        """Test that numbering is consistent across multiple runs."""
        # First run
        result1 = self.file_organizer.organize_entries(self.sample_entries)

        # Reset and run again
        self.file_organizer.reset_counters()
        result2 = self.file_organizer.organize_entries(self.sample_entries)

        # Results should be identical
        self.assertEqual(len(result1), len(result2))
        for directory in result1:
            self.assertIn(directory, result2)
            self.assertEqual(len(result1[directory]), len(result2[directory]))

            # Check that filenames are identical
            filenames1 = [f.filename for f in result1[directory]]
            filenames2 = [f.filename for f in result2[directory]]
            self.assertEqual(filenames1, filenames2)

    def test_original_order_preservation(self):
        """Test that original order is preserved within directories."""
        # Create entries with mixed original orders
        mixed_entries = [
            {
                'title': 'Second Entry',
                'source': 'https://example.com/docs/api/second',
                'original_order': 1
            },
            {
                'title': 'First Entry',
                'source': 'https://example.com/docs/api/first',
                'original_order': 0
            },
            {
                'title': 'Third Entry',
                'source': 'https://example.com/docs/api/third',
                'original_order': 2
            }
        ]

        result = self.file_organizer.organize_entries(mixed_entries)
        api_files = result['api']

        # Should be ordered by original_order
        self.assertEqual(api_files[0].entry.main_title if not isinstance(api_files[0].entry, dict) else api_files[0].entry.get('title'), 'First Entry')
        self.assertEqual(api_files[1].entry.main_title if not isinstance(api_files[1].entry, dict) else api_files[1].entry.get('title'), 'Second Entry')
        self.assertEqual(api_files[2].entry.main_title if not isinstance(api_files[2].entry, dict) else api_files[2].entry.get('title'), 'Third Entry')

        # Numbers should be sequential
        self.assertEqual(api_files[0].number, 1)
        self.assertEqual(api_files[1].number, 2)
        self.assertEqual(api_files[2].number, 3)

    def test_generate_filename_with_no_prefix(self):
        """Test filename generation with no_prefix=True."""
        # Create FileOrganizer with no_prefix=True
        file_organizer_no_prefix = FileOrganizer(no_prefix=True)
        
        entry = {
            'title': 'Test Entry Title',
            'source': 'https://example.com/docs/api/test-endpoint',
            'original_order': 0
        }
        
        # Test with URL
        filename = file_organizer_no_prefix._generate_filename(entry, 1)
        self.assertEqual(filename, 'test-endpoint.md')
        self.assertNotIn('001', filename)
        
        # Test without URL (fallback to title)
        entry_no_url = {
            'title': 'Another Test Entry',
            'source': '',
            'original_order': 0
        }
        
        filename = file_organizer_no_prefix._generate_filename(entry_no_url, 5)
        self.assertEqual(filename, 'another-test-entry.md')
        self.assertNotIn('005', filename)

    def test_organize_entries_with_no_prefix(self):
        """Test organizing entries with no_prefix=True."""
        file_organizer_no_prefix = FileOrganizer(no_prefix=True)
        
        entries = [
            {
                'title': 'API Getting Started',
                'source': 'https://example.com/docs/api/getting-started',
                'original_order': 0
            },
            {
                'title': 'API Reference',
                'source': 'https://example.com/docs/api/reference',
                'original_order': 1
            }
        ]
        
        result = file_organizer_no_prefix.organize_entries(entries)
        
        # Check that filenames don't have number prefixes
        api_files = result['api']
        self.assertEqual(api_files[0].filename, 'getting-started.md')
        self.assertEqual(api_files[1].filename, 'reference.md')
        
        # Numbers should still be tracked internally
        self.assertEqual(api_files[0].number, 1)
        self.assertEqual(api_files[1].number, 2)

    def test_filename_generation_comparison(self):
        """Test filename generation with and without prefix."""
        # Create two organizers with different settings
        organizer_with_prefix = FileOrganizer(no_prefix=False)
        organizer_no_prefix = FileOrganizer(no_prefix=True)
        
        entry = {
            'title': 'Test Entry',
            'source': 'https://example.com/docs/test',
            'original_order': 0
        }
        
        # Generate filenames with both organizers
        filename_with_prefix = organizer_with_prefix._generate_filename(entry, 1)
        filename_no_prefix = organizer_no_prefix._generate_filename(entry, 1)
        
        # With prefix should have number
        self.assertEqual(filename_with_prefix, '001-test.md')
        
        # Without prefix should not have number
        self.assertEqual(filename_no_prefix, 'test.md')


class TestConvenienceFunction(unittest.TestCase):
    """Test cases for convenience functions."""

    def test_organize_context7_entries(self):
        """Test the convenience function."""
        sample_entries = [
            {
                'title': 'Test Entry',
                'source': 'https://example.com/docs/test',
                'original_order': 0
            }
        ]

        result = organize_context7_entries(sample_entries)

        self.assertIsInstance(result, dict)
        self.assertIn('', result)  # Root directory for single-level path
        self.assertEqual(len(result['']), 1)

    def test_organize_context7_entries_with_custom_mapper(self):
        """Test convenience function with custom URLMapper."""
        custom_mapper = URLMapper()
        sample_entries = [
            {
                'title': 'Test Entry',
                'source': 'https://example.com/docs/test',
                'original_order': 0
            }
        ]

        result = organize_context7_entries(sample_entries, custom_mapper)

        self.assertIsInstance(result, dict)
        self.assertIn('', result)

    def test_organize_context7_entries_with_no_prefix(self):
        """Test convenience function with no_prefix parameter."""
        # Create a custom mapper with no_prefix=True
        custom_mapper = URLMapper(no_prefix=True)
        sample_entries = [
            {
                'title': 'Test Entry',
                'source': 'https://example.com/docs/test',
                'original_order': 0
            }
        ]

        # The organize_context7_entries function should respect the mapper's no_prefix setting
        result = organize_context7_entries(sample_entries, custom_mapper)
        
        self.assertIsInstance(result, dict)
        self.assertIn('', result)
        
        # Check that the filename doesn't have a prefix
        organized_file = result[''][0]
        self.assertEqual(organized_file.filename, 'test.md')
        self.assertNotIn('001', organized_file.filename)


class TestIntegrationWithURLMapper(unittest.TestCase):
    """Integration tests with URLMapper."""

    def setUp(self):
        """Set up test fixtures."""
        self.file_organizer = FileOrganizer()
        self.complex_entries = [
            {
                'title': 'Neon API Getting Started',
                'source': 'https://neon.com/docs/data-api/get-started',
                'original_order': 0
            },
            {
                'title': 'Neon Auth API',
                'source': 'https://neon.com/docs/guides/neon-auth-api',
                'original_order': 1
            },
            {
                'title': 'Stack App Objects',
                'source': 'https://neon.com/docs/neon-auth/sdk/react/objects/stack-app',
                'original_order': 2
            }
        ]

    def test_complex_directory_structure(self):
        """Test organizing entries with complex directory structures."""
        result = self.file_organizer.organize_entries(self.complex_entries)

        # Should have three directories based on URL structure
        expected_dirs = ['data-api', 'guides', 'neon-auth/sdk/react/objects']
        self.assertEqual(len(result), 3)

        for directory in expected_dirs:
            self.assertIn(directory, result)
            self.assertEqual(len(result[directory]), 1)

    def test_filename_generation_integration(self):
        """Test that filenames are generated correctly through URLMapper."""
        result = self.file_organizer.organize_entries(self.complex_entries)

        # Check specific filenames
        data_api_files = result['data-api']
        self.assertEqual(data_api_files[0].filename, '001-get-started.md')

        guides_files = result['guides']
        self.assertEqual(guides_files[0].filename, '001-neon-auth-api.md')

        stack_app_files = result['neon-auth/sdk/react/objects']
        self.assertEqual(stack_app_files[0].filename, '001-stack-app.md')


class TestErrorHandling(unittest.TestCase):
    """Test error handling scenarios."""

    def test_file_organizer_error_on_exception(self):
        """Test that FileOrganizerError is raised on unexpected exceptions."""
        file_organizer = FileOrganizer()

        # Mock a method to raise an exception
        with patch.object(file_organizer, '_group_by_source_url', side_effect=Exception("Unexpected error")):
            with self.assertRaises(FileOrganizerError) as context:
                file_organizer.organize_entries([{'source': 'http://example.com/page'}])
            self.assertIn("An unexpected error occurred", str(context.exception))

    def test_malformed_entries_handling(self):
        """Test handling of malformed entries."""
        malformed_entries = [
            None,  # None entry
            {},    # Empty entry
            {'title': 'Valid Entry', 'source': 'https://example.com/docs/test', 'original_order': 0}
        ]

        file_organizer = FileOrganizer()

        # Should handle malformed entries gracefully
        try:
            result = file_organizer.organize_entries(malformed_entries)
            # Should process the valid entry
            self.assertIsInstance(result, dict)
        except Exception as e:
            # If it raises an exception, it should be FileOrganizerError
            self.assertIsInstance(e, FileOrganizerError)


if __name__ == '__main__':
    unittest.main()
