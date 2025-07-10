"""
Unit tests for the MarkdownWriter module.

This module tests the markdown generation functionality including file writing,
content formatting, language handling, and error cases.
"""

import unittest
import tempfile
import os
import shutil
from unittest.mock import patch, mock_open

# Handle both relative and absolute imports
try:
    from src.markdown_writer import (
        MarkdownWriter, MarkdownWriterError,
        write_markdown_file, write_markdown_files, preview_markdown_content
    )
    from src.file_organizer import OrganizedFile
except ImportError:
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from src.markdown_writer import (
        MarkdownWriter, MarkdownWriterError,
        write_markdown_file, write_markdown_files, preview_markdown_content
    )
    from src.file_organizer import OrganizedFile


class TestMarkdownWriter(unittest.TestCase):
    """Test cases for the MarkdownWriter class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary directory for test outputs
        self.test_dir = tempfile.mkdtemp()
        self.writer = MarkdownWriter(self.test_dir)
        
        # Sample entries for testing
        self.sample_entry = {
            'title': 'Test Function',
            'description': 'A simple test function for demonstration.',
            'source': 'https://example.com/docs/test',
            'language': 'python',
            'code': 'def test():\n    return "Hello, World!"',
            'original_order': 1
        }
        
        self.sample_organized_file = OrganizedFile(
            entry=self.sample_entry,
            directory_path='examples',
            filename='001-test-function.md',
            number=1
        )
    
    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_markdown_writer_initialization(self):
        """Test MarkdownWriter initialization."""
        writer = MarkdownWriter()
        self.assertEqual(writer.output_directory, "output")
        
        # Use a relative path within the test directory to avoid permission issues
        custom_path = os.path.join(self.test_dir, "custom_output")
        writer = MarkdownWriter(custom_path)
        self.assertEqual(writer.output_directory, custom_path)
    
    def test_ensure_output_directory_creation(self):
        """Test that output directory is created during initialization."""
        test_path = os.path.join(self.test_dir, "new_output")
        self.assertFalse(os.path.exists(test_path))
        
        MarkdownWriter(test_path)
        self.assertTrue(os.path.exists(test_path))
    
    def test_write_single_file(self):
        """Test writing a single organized file."""
        output_path = self.writer.write_file(self.sample_organized_file)
        
        expected_path = os.path.join(self.test_dir, 'examples', '001-test-function.md')
        self.assertEqual(output_path, expected_path)
        self.assertTrue(os.path.exists(output_path))
        
        # Check file content
        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        self.assertIn('# Test Function', content)
        self.assertIn('## Test Function', content)
        self.assertIn('A simple test function for demonstration.', content)
        self.assertIn('### Python', content)
        self.assertIn('```python', content)
        self.assertIn('def test():', content)
        self.assertIn('*Source: https://example.com/docs/test*', content)
    
    def test_write_multiple_files_same_path(self):
        """Test writing multiple files that should be combined."""
        entry2 = {
            'title': 'Another Function',
            'description': 'Another test function.',
            'source': 'https://example.com/docs/test',  # Same source
            'language': 'python',
            'code': 'def another_test():\n    return "Goodbye!"',
            'original_order': 2
        }
        
        organized_file2 = OrganizedFile(
            entry=entry2,
            directory_path='examples',
            filename='001-test-function.md',  # Same filename
            number=2
        )
        
        files = [self.sample_organized_file, organized_file2]
        output_paths = self.writer.write_files(files)
        
        self.assertEqual(len(output_paths), 1)  # Should be combined into one file
        
        # Check combined content
        with open(output_paths[0], 'r', encoding='utf-8') as f:
            content = f.read()
        
        self.assertIn('# Test Function', content)
        self.assertIn('## Test Function', content)
        self.assertIn('## Another Function', content)
        self.assertIn('def test():', content)
        self.assertIn('def another_test():', content)
    
    def test_write_multiple_files_different_paths(self):
        """Test writing multiple files with different paths."""
        entry2 = {
            'title': 'Second Function',
            'description': 'A second test function.',
            'source': 'https://example.com/docs/other',  # Different source
            'language': 'javascript',
            'code': 'function test() {\n  return "Hello";\n}',
            'original_order': 1
        }
        
        organized_file2 = OrganizedFile(
            entry=entry2,
            directory_path='guides',
            filename='001-second-function.md',
            number=1
        )
        
        files = [self.sample_organized_file, organized_file2]
        output_paths = self.writer.write_files(files)
        
        self.assertEqual(len(output_paths), 2)  # Should be separate files
        
        # Check both files exist
        for path in output_paths:
            self.assertTrue(os.path.exists(path))
    
    def test_group_files_by_path(self):
        """Test grouping files by their full path."""
        entry2 = {
            'title': 'Another Function',
            'description': 'Another test function.',
            'source': 'https://example.com/docs/test',  # Same source
            'language': 'python',
            'code': 'def another():\n    pass',
            'original_order': 2
        }
        
        organized_file2 = OrganizedFile(
            entry=entry2,
            directory_path='examples',
            filename='001-test-function.md',  # Same path
            number=2
        )
        
        entry3 = {
            'title': 'Different Function',
            'description': 'A different function.',
            'source': 'https://example.com/docs/other',
            'language': 'python',
            'code': 'def different():\n    pass',
            'original_order': 1
        }
        
        organized_file3 = OrganizedFile(
            entry=entry3,
            directory_path='guides',
            filename='001-different.md',  # Different path
            number=1
        )
        
        files = [self.sample_organized_file, organized_file2, organized_file3]
        groups = self.writer._group_files_by_path(files)
        
        self.assertEqual(len(groups), 2)
        self.assertIn('examples/001-test-function.md', groups)
        self.assertIn('guides/001-different.md', groups)
        self.assertEqual(len(groups['examples/001-test-function.md']), 2)
        self.assertEqual(len(groups['guides/001-different.md']), 1)
    
    def test_generate_markdown_content_single_entry(self):
        """Test generating markdown content for a single entry."""
        content = self.writer._generate_markdown_content([self.sample_organized_file])
        
        expected_sections = [
            '# Test Function',
            '## Test Function',
            'A simple test function for demonstration.',
            '### Python',
            '```python',
            'def test():',
            '    return "Hello, World!"',
            '```',
            '---',
            '*Source: https://example.com/docs/test*'
        ]
        
        for section in expected_sections:
            self.assertIn(section, content)
    
    def test_generate_markdown_content_multiple_entries(self):
        """Test generating markdown content for multiple entries."""
        entry2 = {
            'title': 'Second Function',
            'description': 'Another function.',
            'source': 'https://example.com/docs/test',  # Same source
            'language': 'python',
            'code': 'def second():\n    return "Second"',
            'original_order': 2
        }
        
        organized_file2 = OrganizedFile(
            entry=entry2,
            directory_path='examples',
            filename='001-test-function.md',
            number=2
        )
        
        files = [self.sample_organized_file, organized_file2]
        content = self.writer._generate_markdown_content(files)
        
        # Should contain both sections
        self.assertIn('## Test Function', content)
        self.assertIn('## Second Function', content)
        self.assertIn('def test():', content)
        self.assertIn('def second():', content)
        
        # Should have single source attribution
        self.assertEqual(content.count('*Source:'), 1)
    
    def test_clean_language_identifier(self):
        """Test language identifier cleaning and mapping."""
        test_cases = [
            ('javascript', 'javascript'),
            ('js', 'javascript'),
            ('JavaScript', 'javascript'),
            ('TypeScript', 'typescript'),
            ('ts', 'typescript'),
            ('python', 'python'),
            ('py', 'python'),
            ('Python', 'python'),
            ('c++', 'cpp'),
            ('C++', 'cpp'),
            ('c#', 'csharp'),
            ('C#', 'csharp'),
            ('html', 'html'),
            ('css', 'css'),
            ('bash', 'bash'),
            ('shell', 'bash'),
            ('sh', 'bash'),
            ('json', 'json'),
            ('yaml', 'yaml'),
            ('yml', 'yaml'),
            ('unknown_lang', 'unknown_lang'),
            ('', ''),
        ]
        
        for input_lang, expected_output in test_cases:
            with self.subTest(input_lang=input_lang):
                result = self.writer._clean_language_identifier(input_lang)
                self.assertEqual(result, expected_output)
    
    def test_get_output_summary(self):
        """Test getting output summary without writing files."""
        entry2 = {
            'title': 'Another Function',
            'description': 'Another function.',
            'source': 'https://example.com/docs/other',
            'language': 'javascript',
            'code': 'function test() {}',
            'original_order': 1
        }
        
        organized_file2 = OrganizedFile(
            entry=entry2,
            directory_path='guides',
            filename='001-another.md',
            number=1
        )
        
        files = [self.sample_organized_file, organized_file2]
        summary = self.writer.get_output_summary(files)
        
        self.assertEqual(summary['total_files'], 2)
        self.assertEqual(summary['total_entries'], 2)
        self.assertEqual(len(summary['file_paths']), 2)
        self.assertIn('examples/001-test-function.md', summary['file_paths'])
        self.assertIn('guides/001-another.md', summary['file_paths'])
        self.assertIn('examples', summary['directories'])
        self.assertIn('guides', summary['directories'])
    
    def test_get_output_summary_empty(self):
        """Test getting output summary for empty file list."""
        summary = self.writer.get_output_summary([])
        
        self.assertEqual(summary['total_files'], 0)
        self.assertEqual(summary['total_entries'], 0)
        self.assertEqual(summary['file_paths'], [])
        self.assertEqual(summary['directories'], set())
    
    def test_write_file_error_handling(self):
        """Test error handling when writing files."""
        # Create an organized file with an invalid path
        invalid_entry = self.sample_entry.copy()
        invalid_organized_file = OrganizedFile(
            entry=invalid_entry,
            directory_path='',
            filename='',  # Invalid filename
            number=1
        )
        
        with patch('builtins.open', side_effect=OSError("Permission denied")):
            with self.assertRaises(MarkdownWriterError):
                self.writer.write_file(invalid_organized_file)
    
    def test_write_files_error_handling(self):
        """Test error handling when writing multiple files."""
        with patch('builtins.open', side_effect=OSError("Disk full")):
            with self.assertRaises(MarkdownWriterError):
                self.writer.write_files([self.sample_organized_file])
    
    def test_empty_content_handling(self):
        """Test handling of entries with missing fields."""
        minimal_entry = {
            'title': '',
            'description': '',
            'source': '',
            'language': '',
            'code': '',
            'original_order': 1
        }
        
        minimal_organized_file = OrganizedFile(
            entry=minimal_entry,
            directory_path='minimal',
            filename='001-minimal.md',
            number=1
        )
        
        content = self.writer._generate_markdown_content([minimal_organized_file])
        
        # Should still generate valid markdown structure
        self.assertIn('# Untitled', content)
        self.assertIn('## Untitled', content)
        # Code section should NOT be present when code is empty
        self.assertNotIn('### Code', content)
        self.assertNotIn('```', content)


class TestConvenienceFunctions(unittest.TestCase):
    """Test cases for convenience functions."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        
        self.sample_entry = {
            'title': 'Convenience Test',
            'description': 'Testing convenience functions.',
            'source': 'https://example.com/docs/convenience',
            'language': 'python',
            'code': 'print("Hello")',
            'original_order': 1
        }
        
        self.sample_organized_file = OrganizedFile(
            entry=self.sample_entry,
            directory_path='convenience',
            filename='001-convenience.md',
            number=1
        )
    
    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_write_markdown_file_convenience(self):
        """Test write_markdown_file convenience function."""
        output_path = write_markdown_file(self.sample_organized_file, self.test_dir)
        
        expected_path = os.path.join(self.test_dir, 'convenience', '001-convenience.md')
        self.assertEqual(output_path, expected_path)
        self.assertTrue(os.path.exists(output_path))
    
    def test_write_markdown_files_convenience(self):
        """Test write_markdown_files convenience function."""
        files = [self.sample_organized_file]
        output_paths = write_markdown_files(files, self.test_dir)
        
        self.assertEqual(len(output_paths), 1)
        self.assertTrue(os.path.exists(output_paths[0]))
    
    def test_preview_markdown_content(self):
        """Test preview_markdown_content convenience function."""
        content = preview_markdown_content([self.sample_organized_file])
        
        self.assertIn('# Convenience Test', content)
        self.assertIn('## Convenience Test', content)
        self.assertIn('Testing convenience functions.', content)
        self.assertIn('print("Hello")', content)


class TestEdgeCases(unittest.TestCase):
    """Test cases for edge cases and special scenarios."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.writer = MarkdownWriter(self.test_dir)
    
    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_unicode_content(self):
        """Test handling of Unicode content."""
        unicode_entry = {
            'title': 'Unicode Test 🔥',
            'description': 'Testing Unicode: café, naïve, 中文',
            'source': 'https://example.com/unicode',
            'language': 'python',
            'code': '# Unicode comment: 中文\nprint("café")',
            'original_order': 1
        }
        
        organized_file = OrganizedFile(
            entry=unicode_entry,
            directory_path='unicode',
            filename='001-unicode.md',
            number=1
        )
        
        output_path = self.writer.write_file(organized_file)
        
        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        self.assertIn('Unicode Test 🔥', content)
        self.assertIn('café, naïve, 中文', content)
        self.assertIn('# Unicode comment: 中文', content)
    
    def test_very_long_content(self):
        """Test handling of very long content."""
        long_code = '\n'.join([f'# Line {i}' for i in range(1000)])
        long_entry = {
            'title': 'Long Content Test',
            'description': 'A' * 1000,  # Very long description
            'source': 'https://example.com/long',
            'language': 'python',
            'code': long_code,
            'original_order': 1
        }
        
        organized_file = OrganizedFile(
            entry=long_entry,
            directory_path='long',
            filename='001-long.md',
            number=1
        )
        
        # Should handle long content without errors
        output_path = self.writer.write_file(organized_file)
        self.assertTrue(os.path.exists(output_path))
        
        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        self.assertIn('# Line 999', content)  # Check end of long code
    
    def test_special_characters_in_filename(self):
        """Test handling of special characters in file paths."""
        special_entry = {
            'title': 'Special & "Chars" Test',
            'description': 'Testing special characters.',
            'source': 'https://example.com/special',
            'language': 'bash',
            'code': 'echo "Special chars: & < > \'"',
            'original_order': 1
        }
        
        organized_file = OrganizedFile(
            entry=special_entry,
            directory_path='special-dir',
            filename='001-special-chars.md',
            number=1
        )
        
        output_path = self.writer.write_file(organized_file)
        self.assertTrue(os.path.exists(output_path))
        
        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        self.assertIn('Special & "Chars" Test', content)
        self.assertIn('echo "Special chars: & < > \'"', content)


if __name__ == '__main__':
    unittest.main()