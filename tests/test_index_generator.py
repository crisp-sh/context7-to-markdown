"""
Unit tests for the IndexGenerator module.

This module tests the index generation functionality including file organization,
content generation, title extraction, and error handling.
"""

import os
import shutil
import tempfile
import unittest
from unittest.mock import patch

from c2md.file_organizer import OrganizedFile
from c2md.index_generator import (
    IndexGenerator,
    IndexGeneratorError,
    generate_index,
    generate_index_from_organized_files,
    preview_index_content,
)


class TestIndexGenerator(unittest.TestCase):
    """Test cases for the IndexGenerator class."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary directory for test outputs
        self.test_dir = tempfile.mkdtemp()
        self.generator = IndexGenerator(self.test_dir)

        # Sample file paths for testing
        self.sample_file_paths = [
            "examples/001-get-started.md",
            "examples/002-advanced-features.md",
            "guides/001-installation.md",
            "guides/002-configuration.md",
            "api/001-authentication.md",
            "reference.md"  # Root level file
        ]

        # Sample organized file for testing
        self.sample_entry = {
            'title': 'Test Documentation',
            'description': 'A test document',
            'source': 'https://example.com/docs/test',
            'language': 'markdown',
            'code': '# Test Content',
            'original_order': 1
        }

        self.sample_organized_file = OrganizedFile(
            entry=self.sample_entry,
            directory_path='examples',
            filename='001-test-doc.md',
            number=1
        )

    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_index_generator_initialization(self):
        """Test IndexGenerator initialization."""
        generator = IndexGenerator()
        self.assertEqual(generator.output_directory, "output")
        self.assertEqual(generator.index_filename, "000-index.md")

        generator = IndexGenerator("/custom/path")
        self.assertEqual(generator.output_directory, "/custom/path")

    def test_organize_files_by_directory(self):
        """Test organizing files by directory structure."""
        directory_structure = self.generator._organize_files_by_directory(self.sample_file_paths)

        # Check directory keys
        expected_directories = {'examples', 'guides', 'api', '.'}
        self.assertEqual(set(directory_structure.keys()), expected_directories)

        # Check file counts
        self.assertEqual(len(directory_structure['examples']), 2)
        self.assertEqual(len(directory_structure['guides']), 2)
        self.assertEqual(len(directory_structure['api']), 1)
        self.assertEqual(len(directory_structure['.']), 1)

        # Check file structure
        examples_files = directory_structure['examples']
        self.assertEqual(examples_files[0]['filename'], '001-get-started.md')
        self.assertEqual(examples_files[0]['path'], 'examples/001-get-started.md')
        self.assertEqual(examples_files[0]['title'], 'Get Started')

    def test_extract_title_from_filename(self):
        """Test title extraction from filenames."""
        test_cases = [
            ('001-get-started.md', 'Get Started'),
            ('002-advanced-features.md', 'Advanced Features'),
            ('installation-guide.md', 'Installation Guide'),
            ('api_reference.md', 'Api Reference'),
            ('simple.md', 'Simple'),
            ('123-complex-file-name.md', 'Complex File Name'),
            ('no-extension', 'No Extension'),
            ('', 'Untitled'),
        ]

        for filename, expected_title in test_cases:
            with self.subTest(filename=filename):
                result = self.generator._extract_title_from_filename(filename)
                self.assertEqual(result, expected_title)

    def test_extract_title_from_markdown(self):
        """Test title extraction from markdown file content."""
        # Create a test markdown file
        test_content = """# Main Title

Some content here.

## Subtitle
More content.
"""
        test_file = os.path.join(self.test_dir, "test.md")
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(test_content)

        # Test extraction
        title = self.generator._extract_title_from_markdown("test.md")
        self.assertEqual(title, "Main Title")

    def test_extract_title_from_markdown_no_heading(self):
        """Test title extraction when file has no heading."""
        # Create a test markdown file without headings
        test_content = """This is just regular content.

No headings here.
"""
        test_file = os.path.join(self.test_dir, "no-heading.md")
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(test_content)

        # Test extraction
        title = self.generator._extract_title_from_markdown("no-heading.md")
        self.assertIsNone(title)

    def test_extract_title_from_markdown_nonexistent_file(self):
        """Test title extraction from non-existent file."""
        title = self.generator._extract_title_from_markdown("nonexistent.md")
        self.assertIsNone(title)

    def test_generate_index_content(self):
        """Test generation of index markdown content."""
        directory_structure = self.generator._organize_files_by_directory(self.sample_file_paths)
        content = self.generator._generate_index_content(directory_structure)

        # Check essential components
        self.assertIn("# Documentation Index", content)
        self.assertIn("## Table of Contents", content)
        self.assertIn("### examples/", content)
        self.assertIn("### guides/", content)
        self.assertIn("### api/", content)
        self.assertIn("- [Get Started](examples/001-get-started.md)", content)
        self.assertIn("- [Reference](reference.md)", content)  # Root file
        self.assertIn("*Generated by Context7-to-Markdown CLI Tool*", content)

    def test_generate_index_from_file_paths(self):
        """Test generating index file from file paths."""
        output_path = self.generator.generate_index(self.sample_file_paths)

        expected_path = os.path.join(self.test_dir, "000-index.md")
        self.assertEqual(output_path, expected_path)
        self.assertTrue(os.path.exists(output_path))

        # Check file content
        with open(output_path, encoding='utf-8') as f:
            content = f.read()

        self.assertIn("# Documentation Index", content)
        self.assertIn("### examples/", content)
        self.assertIn("- [Get Started](examples/001-get-started.md)", content)

    def test_generate_index_custom_output_path(self):
        """Test generating index with custom output path."""
        custom_path = os.path.join(self.test_dir, "custom-index.md")
        output_path = self.generator.generate_index(self.sample_file_paths, custom_path)

        self.assertEqual(output_path, custom_path)
        self.assertTrue(os.path.exists(custom_path))

    def test_generate_index_from_organized_files(self):
        """Test generating index from organized file objects."""
        organized_files = [self.sample_organized_file]
        output_path = self.generator.generate_index_from_organized_files(organized_files)

        expected_path = os.path.join(self.test_dir, "000-index.md")
        self.assertEqual(output_path, expected_path)
        self.assertTrue(os.path.exists(output_path))

        # Check that the title from the organized file is used
        with open(output_path, encoding='utf-8') as f:
            content = f.read()

        self.assertIn("- [Test Documentation](examples/001-test-doc.md)", content)

    def test_generate_index_empty_file_list(self):
        """Test generating index with empty file list."""
        output_path = self.generator.generate_index([])

        self.assertTrue(os.path.exists(output_path))

        with open(output_path, encoding='utf-8') as f:
            content = f.read()

        self.assertIn("# Documentation Index", content)
        self.assertIn("## Table of Contents", content)
        self.assertIn("*Generated by Context7-to-Markdown CLI Tool*", content)

    def test_generate_index_non_markdown_files_filtered(self):
        """Test that non-markdown files are filtered out."""
        mixed_files = [
            "docs/001-guide.md",
            "docs/image.png",
            "docs/script.js",
            "docs/002-reference.md",
            "README.txt"
        ]

        directory_structure = self.generator._organize_files_by_directory(mixed_files)

        # Only markdown files should be included
        self.assertEqual(len(directory_structure['docs']), 2)
        filenames = [f['filename'] for f in directory_structure['docs']]
        self.assertIn('001-guide.md', filenames)
        self.assertIn('002-reference.md', filenames)
        self.assertNotIn('image.png', filenames)
        self.assertNotIn('script.js', filenames)

    def test_get_index_summary(self):
        """Test getting index summary without generating file."""
        summary = self.generator.get_index_summary(self.sample_file_paths)

        self.assertEqual(summary['total_files'], 6)
        self.assertEqual(summary['total_directories'], 4)  # examples, guides, api, .
        self.assertEqual(summary['index_filename'], "000-index.md")
        self.assertIn('examples', summary['directory_breakdown'])
        self.assertEqual(summary['directory_breakdown']['examples'], 2)

    def test_get_index_summary_empty_list(self):
        """Test getting summary for empty file list."""
        summary = self.generator.get_index_summary([])

        self.assertEqual(summary['total_files'], 0)
        self.assertEqual(summary['total_directories'], 0)
        self.assertEqual(summary['directory_breakdown'], {})

    def test_generate_index_error_handling(self):
        """Test error handling during index generation."""
        # Test with invalid output path that can't be created
        with patch('builtins.open', side_effect=OSError("Permission denied")):
            with self.assertRaises(IndexGeneratorError):
                self.generator.generate_index(self.sample_file_paths)

    def test_directory_sorting(self):
        """Test that directories are sorted correctly (root first, then alphabetical)."""
        file_paths = [
            "zebra/001-file.md",
            "alpha/001-file.md",
            "root-file.md",
            "beta/001-file.md"
        ]

        directory_structure = self.generator._organize_files_by_directory(file_paths)
        content = self.generator._generate_index_content(directory_structure)

        # Root files should appear first (no directory heading)
        # Then directories should be alphabetical
        lines = content.split('\n')

        # Find the order of directory headings
        directory_headings = [line for line in lines if line.startswith('### ')]
        expected_order = ['### alpha/', '### beta/', '### zebra/']
        self.assertEqual(directory_headings, expected_order)

    def test_file_sorting_within_directory(self):
        """Test that files are sorted correctly within directories."""
        file_paths = [
            "docs/003-third.md",
            "docs/001-first.md",
            "docs/002-second.md"
        ]

        directory_structure = self.generator._organize_files_by_directory(file_paths)
        files = directory_structure['docs']

        # Files should be sorted by filename
        expected_order = ['001-first.md', '002-second.md', '003-third.md']
        actual_order = [f['filename'] for f in files]
        self.assertEqual(actual_order, expected_order)

    def test_unicode_handling(self):
        """Test handling of Unicode characters in filenames and paths."""
        unicode_files = [
            "docs/001-café-guide.md",
            "docs/002-naïve-approach.md",
            "中文/001-chinese-doc.md"
        ]

        directory_structure = self.generator._organize_files_by_directory(unicode_files)
        content = self.generator._generate_index_content(directory_structure)

        self.assertIn("### 中文/", content)
        self.assertIn("- [Café Guide](docs/001-café-guide.md)", content)
        self.assertIn("- [Naïve Approach](docs/002-naïve-approach.md)", content)

    def test_path_normalization(self):
        """Test that paths with different separators are normalized."""
        mixed_paths = [
            "docs\\windows\\001-guide.md",  # Windows-style path
            "docs/unix/001-guide.md",       # Unix-style path
        ]

        directory_structure = self.generator._organize_files_by_directory(mixed_paths)

        # Both should be treated correctly
        self.assertIn('docs/windows', directory_structure)
        self.assertIn('docs/unix', directory_structure)


class TestConvenienceFunctions(unittest.TestCase):
    """Test cases for convenience functions."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()

        self.sample_file_paths = [
            "examples/001-example.md",
            "guides/001-guide.md"
        ]

        self.sample_entry = {
            'title': 'Convenience Test',
            'description': 'Testing convenience functions.',
            'source': 'https://example.com/docs/convenience',
            'language': 'markdown',
            'code': '# Test',
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

    def test_generate_index_convenience(self):
        """Test generate_index convenience function."""
        output_path = generate_index(self.sample_file_paths, self.test_dir)

        expected_path = os.path.join(self.test_dir, "000-index.md")
        self.assertEqual(output_path, expected_path)
        self.assertTrue(os.path.exists(output_path))

    def test_generate_index_from_organized_files_convenience(self):
        """Test generate_index_from_organized_files convenience function."""
        files = [self.sample_organized_file]
        output_path = generate_index_from_organized_files(files, self.test_dir)

        expected_path = os.path.join(self.test_dir, "000-index.md")
        self.assertEqual(output_path, expected_path)
        self.assertTrue(os.path.exists(output_path))

    def test_preview_index_content_convenience(self):
        """Test preview_index_content convenience function."""
        content = preview_index_content(self.sample_file_paths, self.test_dir)

        self.assertIn("# Documentation Index", content)
        self.assertIn("### examples/", content)
        self.assertIn("- [Example](examples/001-example.md)", content)


class TestEdgeCases(unittest.TestCase):
    """Test cases for edge cases and special scenarios."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.generator = IndexGenerator(self.test_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_very_deep_directory_structure(self):
        """Test handling of very deep directory structures."""
        deep_paths = [
            "level1/level2/level3/level4/level5/001-deep-file.md"
        ]

        directory_structure = self.generator._organize_files_by_directory(deep_paths)
        content = self.generator._generate_index_content(directory_structure)

        self.assertIn("### level1/level2/level3/level4/level5/", content)
        self.assertIn("- [Deep File](level1/level2/level3/level4/level5/001-deep-file.md)", content)

    def test_special_characters_in_paths(self):
        """Test handling of special characters in file paths."""
        special_paths = [
            "docs & guides/001-file with spaces.md",
            "docs/001-file-with-dashes.md",
            "docs/001_file_with_underscores.md"
        ]

        directory_structure = self.generator._organize_files_by_directory(special_paths)
        content = self.generator._generate_index_content(directory_structure)

        self.assertIn("### docs & guides/", content)
        self.assertIn("- [File With Spaces](docs & guides/001-file with spaces.md)", content)
        self.assertIn("- [File With Dashes](docs/001-file-with-dashes.md)", content)
        self.assertIn("- [File With Underscores](docs/001_file_with_underscores.md)", content)

    def test_empty_directory_handling(self):
        """Test handling when directories would be empty after filtering."""
        # All non-markdown files
        non_markdown_paths = [
            "images/photo.jpg",
            "scripts/build.sh",
            "data/config.json"
        ]

        directory_structure = self.generator._organize_files_by_directory(non_markdown_paths)
        content = self.generator._generate_index_content(directory_structure)

        # Should still have basic structure but no directory sections
        self.assertIn("# Documentation Index", content)
        self.assertIn("## Table of Contents", content)
        self.assertNotIn("### images/", content)
        self.assertNotIn("### scripts/", content)

    def test_malformed_markdown_file_title_extraction(self):
        """Test title extraction from malformed markdown files."""
        # Create files with various malformed heading scenarios
        test_cases = [
            ("# ", ""),  # Empty heading
            ("##", ""),  # Heading with no content
            ("#NoSpace", "NoSpace"),  # No space after #
            ("# Multiple # Hash # Marks", "Multiple # Hash # Marks"),  # Multiple hashes
        ]

        for content, expected in test_cases:
            with self.subTest(content=content):
                filename = f"test_{hash(content)}.md"
                test_file = os.path.join(self.test_dir, filename)

                with open(test_file, 'w', encoding='utf-8') as f:
                    f.write(content)

                title = self.generator._extract_title_from_markdown(filename)
                if expected:
                    self.assertEqual(title, expected)
                else:
                    self.assertIsNone(title)


if __name__ == '__main__':
    unittest.main()
