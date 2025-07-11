"""
Unit tests for the CLI entry point module (__main__.py).

This module tests the command-line interface functionality including argument parsing,
file validation, directory management, workflow orchestration, and error handling.
"""

import os
import shutil
import sys
import tempfile
import unittest
from io import StringIO
from unittest.mock import Mock, patch

# Handle both relative and absolute imports
try:
    from c2md.__main__ import (
        ensure_output_directory,
        flatten_organized_structure,
        main,
        print_processing_summary,
        validate_input_file,
    )
    from c2md.file_organizer import FileOrganizerError, OrganizedFile
    from c2md.index_generator import IndexGeneratorError
    from c2md.markdown_writer import MarkdownWriterError
    from c2md.parser import Context7ParseError
    from c2md.url_mapper import URLMapperError
except ImportError:
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from c2md.__main__ import (
        ensure_output_directory,
        flatten_organized_structure,
        main,
        print_processing_summary,
        validate_input_file,
    )
    from c2md.file_organizer import FileOrganizerError, OrganizedFile
    from c2md.index_generator import IndexGeneratorError
    from c2md.markdown_writer import MarkdownWriterError
    from c2md.parser import Context7ParseError
    from c2md.url_mapper import URLMapperError


class TestValidateInputFile(unittest.TestCase):
    """Test cases for validate_input_file function."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.test_dir, "test.txt")

        # Create a valid test file
        with open(self.test_file, 'w') as f:
            f.write("test content")

    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_validate_valid_file(self):
        """Test validation of a valid file."""
        # Should not raise any exception
        validate_input_file(self.test_file)

    def test_validate_nonexistent_file(self):
        """Test validation of non-existent file."""
        nonexistent_file = os.path.join(self.test_dir, "nonexistent.txt")

        with self.assertRaises(FileNotFoundError) as context:
            validate_input_file(nonexistent_file)

        self.assertIn("Input file not found", str(context.exception))
        self.assertIn(nonexistent_file, str(context.exception))

    def test_validate_directory_instead_of_file(self):
        """Test validation when path points to directory."""
        with self.assertRaises(ValueError) as context:
            validate_input_file(self.test_dir)

        self.assertIn("Input path is not a file", str(context.exception))

    @patch('os.access')
    def test_validate_unreadable_file(self, mock_access):
        """Test validation of unreadable file."""
        mock_access.return_value = False

        with self.assertRaises(PermissionError) as context:
            validate_input_file(self.test_file)

        self.assertIn("Input file is not readable", str(context.exception))
        mock_access.assert_called_with(self.test_file, os.R_OK)


class TestEnsureOutputDirectory(unittest.TestCase):
    """Test cases for ensure_output_directory function."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_ensure_existing_directory(self):
        """Test ensuring an existing directory."""
        # Should not raise any exception
        ensure_output_directory(self.test_dir)
        self.assertTrue(os.path.exists(self.test_dir))

    def test_ensure_new_directory(self):
        """Test creating a new directory."""
        new_dir = os.path.join(self.test_dir, "new_directory")
        self.assertFalse(os.path.exists(new_dir))

        ensure_output_directory(new_dir)
        self.assertTrue(os.path.exists(new_dir))

    def test_ensure_nested_directory(self):
        """Test creating nested directories."""
        nested_dir = os.path.join(self.test_dir, "level1", "level2", "level3")
        self.assertFalse(os.path.exists(nested_dir))

        ensure_output_directory(nested_dir)
        self.assertTrue(os.path.exists(nested_dir))

    @patch('pathlib.Path.mkdir')
    def test_ensure_directory_permission_error(self, mock_mkdir):
        """Test handling of permission errors during directory creation."""
        mock_mkdir.side_effect = PermissionError("Permission denied")

        with self.assertRaises(PermissionError) as context:
            ensure_output_directory("/restricted/path")

        self.assertIn("Cannot create output directory", str(context.exception))

    @patch('pathlib.Path.mkdir')
    def test_ensure_directory_general_error(self, mock_mkdir):
        """Test handling of general errors during directory creation."""
        mock_mkdir.side_effect = OSError("Disk full")

        with self.assertRaises(RuntimeError) as context:
            ensure_output_directory("/some/path")

        self.assertIn("Failed to create output directory", str(context.exception))


class TestFlattenOrganizedStructure(unittest.TestCase):
    """Test cases for flatten_organized_structure function."""

    def setUp(self):
        """Set up test fixtures."""
        self.sample_entry1 = {
            'title': 'Test Entry 1',
            'description': 'First test entry',
            'source': 'https://example.com/docs/test1',
            'language': 'python',
            'code': 'print("test1")',
            'original_order': 0
        }

        self.sample_entry2 = {
            'title': 'Test Entry 2',
            'description': 'Second test entry',
            'source': 'https://example.com/docs/test2',
            'language': 'python',
            'code': 'print("test2")',
            'original_order': 1
        }

        self.organized_file1 = OrganizedFile(
            entry=self.sample_entry1,
            directory_path='api',
            filename='001-test1.md',
            number=1
        )

        self.organized_file2 = OrganizedFile(
            entry=self.sample_entry2,
            directory_path='guides',
            filename='001-test2.md',
            number=1
        )

    def test_flatten_single_directory(self):
        """Test flattening structure with single directory."""
        organized_structure = {
            'api': [self.organized_file1]
        }

        result = flatten_organized_structure(organized_structure)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], self.organized_file1)

    def test_flatten_multiple_directories(self):
        """Test flattening structure with multiple directories."""
        organized_structure = {
            'api': [self.organized_file1],
            'guides': [self.organized_file2]
        }

        result = flatten_organized_structure(organized_structure)

        self.assertEqual(len(result), 2)
        self.assertIn(self.organized_file1, result)
        self.assertIn(self.organized_file2, result)

    def test_flatten_multiple_files_per_directory(self):
        """Test flattening structure with multiple files per directory."""
        organized_structure = {
            'api': [self.organized_file1, self.organized_file2]
        }

        result = flatten_organized_structure(organized_structure)

        self.assertEqual(len(result), 2)
        self.assertIn(self.organized_file1, result)
        self.assertIn(self.organized_file2, result)

    def test_flatten_empty_structure(self):
        """Test flattening empty structure."""
        result = flatten_organized_structure({})
        self.assertEqual(result, [])

    def test_flatten_structure_with_empty_directories(self):
        """Test flattening structure with empty directories."""
        organized_structure = {
            'api': [],
            'guides': [self.organized_file1]
        }

        result = flatten_organized_structure(organized_structure)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], self.organized_file1)


class TestPrintProcessingSummary(unittest.TestCase):
    """Test cases for print_processing_summary function."""

    def test_print_summary_basic(self):
        """Test printing basic summary."""
        files_written = [
            "/path/to/output/api/001-example.md",
            "/path/to/output/guides/001-guide.md"
        ]

        with patch('sys.stdout', new=StringIO()) as fake_out:
            print_processing_summary(2, files_written)
            output = fake_out.getvalue()

        self.assertIn("✅ Processing complete!", output)
        self.assertIn("📋 Processed 2 Context7 entries", output)
        self.assertIn("📄 Generated 2 markdown files", output)
        self.assertIn("📁 Files written to:", output)
        self.assertIn("001-example.md", output)
        self.assertIn("001-guide.md", output)

    def test_print_summary_with_index(self):
        """Test printing summary with index file."""
        files_written = ["/path/to/output/api/001-example.md"]
        index_path = "/path/to/output/000-index.md"

        with patch('sys.stdout', new=StringIO()) as fake_out:
            print_processing_summary(1, files_written, index_path)
            output = fake_out.getvalue()

        self.assertIn("📑 Index generated: /path/to/output/000-index.md", output)

    def test_print_summary_no_files(self):
        """Test printing summary with no files written."""
        with patch('sys.stdout', new=StringIO()) as fake_out:
            print_processing_summary(0, [])
            output = fake_out.getvalue()

        self.assertIn("📋 Processed 0 Context7 entries", output)
        self.assertIn("📄 Generated 0 markdown files", output)
        self.assertNotIn("📁 Files written to:", output)

    def test_print_summary_sorted_files(self):
        """Test that files are displayed in sorted order."""
        files_written = [
            "/path/to/zebra.md",
            "/path/to/alpha.md",
            "/path/to/beta.md"
        ]

        with patch('sys.stdout', new=StringIO()) as fake_out:
            print_processing_summary(3, files_written)
            output = fake_out.getvalue()

        # Check that files appear in sorted order
        alpha_pos = output.find("alpha.md")
        beta_pos = output.find("beta.md")
        zebra_pos = output.find("zebra.md")

        self.assertTrue(alpha_pos < beta_pos < zebra_pos)


class TestMainFunction(unittest.TestCase):
    """Test cases for the main CLI function."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.test_dir, "test.context7")

        # Create a sample Context7 file
        context7_content = """TITLE: Sample Entry
DESCRIPTION: This is a test entry
SOURCE: https://example.com/docs/api/sample
LANGUAGE: python
CODE:
print("Hello, World!")
"""
        with open(self.test_file, 'w') as f:
            f.write(context7_content)

    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    @patch('c2md.__main__.Context7Parser')
    @patch('c2md.__main__.URLMapper')
    @patch('c2md.__main__.FileOrganizer')
    @patch('c2md.__main__.MarkdownWriter')
    @patch('c2md.__main__.IndexGenerator')
    @patch('argparse.ArgumentParser.parse_args')
    @patch('sys.stdout', new_callable=StringIO)
    def test_main_successful_execution(self, mock_stdout, mock_parse_args, mock_index_gen, mock_writer,
                                     mock_organizer, mock_mapper, mock_parser):
        """Test successful execution of main function."""
        # Mock parsed arguments
        mock_args = Mock()
        mock_args.input_file = self.test_file
        mock_args.directory = self.test_dir
        mock_args.tree = True  # Default tree option
        mock_parse_args.return_value = mock_args

        # Mock parser
        mock_parser_instance = Mock()
        mock_parser_instance.parse_file.return_value = [
            {
                'title': 'Sample Entry',
                'description': 'Test entry',
                'source': 'https://example.com/docs/api/sample',
                'language': 'python',
                'code': 'print("test")',
                'original_order': 0
            }
        ]
        mock_parser.return_value = mock_parser_instance

        # Mock organizer
        mock_organizer_instance = Mock()
        organized_file = OrganizedFile(
            entry=mock_parser_instance.parse_file.return_value[0],
            directory_path='api',
            filename='001-sample.md',
            number=1
        )
        mock_organizer_instance.organize_entries.return_value = {'api': [organized_file]}
        mock_organizer.return_value = mock_organizer_instance

        # Mock writer
        mock_writer_instance = Mock()
        mock_writer_instance.write_files.return_value = ['/output/api/001-sample.md']
        mock_writer.return_value = mock_writer_instance

        # Mock index generator
        mock_index_instance = Mock()
        mock_index_instance.generate_index.return_value = '/output/000-index.md'
        mock_index_gen.return_value = mock_index_instance

        # Execute main function
        main()

        # Verify workflow execution
        mock_parser_instance.parse_file.assert_called_once_with(self.test_file)
        mock_organizer_instance.organize_entries.assert_called_once()
        mock_writer_instance.write_files.assert_called_once()
        mock_index_instance.generate_index.assert_called_once()

        # Check output
        output = mock_stdout.getvalue()
        self.assertIn("🔍 Validating input file", output)
        self.assertIn("📁 Preparing output directory", output)
        self.assertIn("📖 Parsing Context7 file", output)
        self.assertIn("✅ Found 1 entries", output)
        self.assertIn("🗂️  Organizing entries", output)
        self.assertIn("✍️  Writing markdown files", output)
        self.assertIn("📑 Generating table of contents", output)
        self.assertIn("✅ Processing complete!", output)

    @patch('sys.stdout', new_callable=StringIO)
    def test_main_no_tree_option(self, mock_stdout):
        """Test main function with --no-tree option."""

        with patch('c2md.__main__.Context7Parser') as mock_parser, \
             patch('c2md.__main__.FileOrganizer') as mock_organizer, \
             patch('c2md.__main__.MarkdownWriter') as mock_writer, \
             patch('c2md.__main__.IndexGenerator') as mock_index_gen, \
             patch('argparse.ArgumentParser.parse_args') as mock_parse_args:

            # Mock parsed arguments
            mock_args = Mock()
            mock_args.input_file = self.test_file
            mock_args.directory = self.test_dir
            mock_args.tree = False  # --no-tree sets tree to False
            mock_parse_args.return_value = mock_args

            # Setup mocks
            mock_parser_instance = Mock()
            mock_parser_instance.parse_file.return_value = [
                {'title': 'Test', 'source': 'https://example.com', 'original_order': 0}
            ]
            mock_parser.return_value = mock_parser_instance

            mock_organizer_instance = Mock()
            mock_organizer_instance.organize_entries.return_value = {}
            mock_organizer.return_value = mock_organizer_instance

            mock_writer_instance = Mock()
            mock_writer_instance.write_files.return_value = []
            mock_writer.return_value = mock_writer_instance

            main()

            # Index generator should not be called
            mock_index_gen.assert_not_called()

            output = mock_stdout.getvalue()
            self.assertNotIn("📑 Generating table of contents", output)

    @patch('argparse.ArgumentParser.parse_args')
    @patch('sys.stderr', new_callable=StringIO)
    def test_main_file_not_found_error(self, mock_stderr, mock_parse_args):
        """Test main function with file not found error."""
        nonexistent_file = os.path.join(self.test_dir, "nonexistent.context7")

        # Mock parsed arguments with nonexistent file
        mock_args = Mock()
        mock_args.input_file = nonexistent_file
        mock_args.directory = self.test_dir
        mock_args.tree = True
        mock_parse_args.return_value = mock_args

        with self.assertRaises(SystemExit) as cm:
            main()

        self.assertEqual(cm.exception.code, 1)
        error_output = mock_stderr.getvalue()
        self.assertIn("❌ File not found", error_output)
        self.assertIn("💡 Please check that the input file path is correct", error_output)

    @patch('argparse.ArgumentParser.parse_args')
    @patch('sys.stderr', new_callable=StringIO)
    def test_main_permission_error(self, mock_stderr, mock_parse_args):
        """Test main function with permission error."""
        # Mock parsed arguments
        mock_args = Mock()
        mock_args.input_file = self.test_file
        mock_args.directory = self.test_dir
        mock_args.tree = True
        mock_parse_args.return_value = mock_args

        with patch('c2md.__main__.validate_input_file', side_effect=PermissionError("Permission denied")):
            with self.assertRaises(SystemExit) as cm:
                main()

            self.assertEqual(cm.exception.code, 1)
            error_output = mock_stderr.getvalue()
            self.assertIn("❌ Permission error", error_output)
            self.assertIn("💡 Please check file and directory permissions", error_output)

    @patch('argparse.ArgumentParser.parse_args')
    @patch('sys.stderr', new_callable=StringIO)
    def test_main_context7_parse_error(self, mock_stderr, mock_parse_args):
        """Test main function with Context7 parsing error."""
        # Mock parsed arguments
        mock_args = Mock()
        mock_args.input_file = self.test_file
        mock_args.directory = self.test_dir
        mock_args.tree = True
        mock_parse_args.return_value = mock_args

        with patch('c2md.__main__.Context7Parser') as mock_parser:
            mock_parser_instance = Mock()
            mock_parser_instance.parse_file.side_effect = Context7ParseError("Invalid format")
            mock_parser.return_value = mock_parser_instance

            with self.assertRaises(SystemExit) as cm:
                main()

            self.assertEqual(cm.exception.code, 1)
            error_output = mock_stderr.getvalue()
            self.assertIn("❌ Parsing error", error_output)
            self.assertIn("💡 Please check that your input file is in valid Context7 format", error_output)

    @patch('argparse.ArgumentParser.parse_args')
    @patch('sys.stderr', new_callable=StringIO)
    def test_main_url_mapper_error(self, mock_stderr, mock_parse_args):
        """Test main function with URL mapper error."""
        # Mock parsed arguments
        mock_args = Mock()
        mock_args.input_file = self.test_file
        mock_args.directory = self.test_dir
        mock_args.tree = True
        mock_parse_args.return_value = mock_args

        with patch('c2md.__main__.Context7Parser') as mock_parser, \
             patch('c2md.__main__.URLMapper') as mock_mapper:

            mock_parser_instance = Mock()
            mock_parser_instance.parse_file.return_value = [{'title': 'Test'}]
            mock_parser.return_value = mock_parser_instance

            mock_mapper.side_effect = URLMapperError("Invalid URL")

            with self.assertRaises(SystemExit) as cm:
                main()

            self.assertEqual(cm.exception.code, 1)
            error_output = mock_stderr.getvalue()
            self.assertIn("❌ URL mapping error", error_output)
            self.assertIn("💡 Please check that your Context7 entries have valid SOURCE URLs", error_output)

    @patch('argparse.ArgumentParser.parse_args')
    @patch('sys.stderr', new_callable=StringIO)
    def test_main_file_organizer_error(self, mock_stderr, mock_parse_args):
        """Test main function with file organizer error."""
        # Mock parsed arguments
        mock_args = Mock()
        mock_args.input_file = self.test_file
        mock_args.directory = self.test_dir
        mock_args.tree = True
        mock_parse_args.return_value = mock_args

        with patch('c2md.__main__.Context7Parser') as mock_parser, \
             patch('c2md.__main__.FileOrganizer') as mock_organizer:

            mock_parser_instance = Mock()
            mock_parser_instance.parse_file.return_value = [{'title': 'Test'}]
            mock_parser.return_value = mock_parser_instance

            mock_organizer_instance = Mock()
            mock_organizer_instance.organize_entries.side_effect = FileOrganizerError("Organization failed")
            mock_organizer.return_value = mock_organizer_instance

            with self.assertRaises(SystemExit) as cm:
                main()

            self.assertEqual(cm.exception.code, 1)
            error_output = mock_stderr.getvalue()
            self.assertIn("❌ File organization error", error_output)

    @patch('argparse.ArgumentParser.parse_args')
    @patch('sys.stderr', new_callable=StringIO)
    def test_main_markdown_writer_error(self, mock_stderr, mock_parse_args):
        """Test main function with markdown writer error."""
        # Mock parsed arguments
        mock_args = Mock()
        mock_args.input_file = self.test_file
        mock_args.directory = self.test_dir
        mock_args.tree = True
        mock_parse_args.return_value = mock_args

        with patch('c2md.__main__.Context7Parser') as mock_parser, \
             patch('c2md.__main__.FileOrganizer') as mock_organizer, \
             patch('c2md.__main__.MarkdownWriter') as mock_writer:

            # Setup successful parsing and organizing
            mock_parser_instance = Mock()
            mock_parser_instance.parse_file.return_value = [{'title': 'Test'}]
            mock_parser.return_value = mock_parser_instance

            mock_organizer_instance = Mock()
            mock_organizer_instance.organize_entries.return_value = {'test': []}
            mock_organizer.return_value = mock_organizer_instance

            # Make writer fail
            mock_writer_instance = Mock()
            mock_writer_instance.write_files.side_effect = MarkdownWriterError("Write failed")
            mock_writer.return_value = mock_writer_instance

            with self.assertRaises(SystemExit) as cm:
                main()

            self.assertEqual(cm.exception.code, 1)
            error_output = mock_stderr.getvalue()
            self.assertIn("❌ Markdown writing error", error_output)

    @patch('c2md.__main__.IndexGenerator')
    @patch('c2md.__main__.MarkdownWriter')
    @patch('c2md.__main__.FileOrganizer')
    @patch('c2md.__main__.Context7Parser')
    @patch('argparse.ArgumentParser.parse_args')
    @patch('sys.stderr', new_callable=StringIO)
    def test_main_index_generator_error_no_exit(self, mock_stderr, mock_parse_args, mock_parser, mock_organizer, mock_writer, mock_index_gen):
        """Test main function with index generator error (should not exit)."""
        # Mock parsed arguments
        mock_args = Mock()
        mock_args.input_file = self.test_file
        mock_args.directory = self.test_dir
        mock_args.tree = True
        mock_parse_args.return_value = mock_args

        # Setup successful workflow until index generation
        mock_parser_instance = Mock()
        mock_parser_instance.parse_file.return_value = [{'title': 'Test'}]
        mock_parser.return_value = mock_parser_instance

        mock_organizer_instance = Mock()
        mock_organizer_instance.organize_entries.return_value = {'test': []}
        mock_organizer.return_value = mock_organizer_instance

        mock_writer_instance = Mock()
        mock_writer_instance.write_files.return_value = ['/test.md']
        mock_writer.return_value = mock_writer_instance

        # Make index generator fail
        mock_index_instance = Mock()
        mock_index_instance.generate_index.side_effect = IndexGeneratorError("Index failed")
        mock_index_gen.return_value = mock_index_instance

        # Should not raise SystemExit for index generator errors
        main()

        error_output = mock_stderr.getvalue()
        self.assertIn("❌ Index generation error", error_output)
        self.assertIn("💡 Index generation failed, but markdown files were created successfully", error_output)

    @patch('argparse.ArgumentParser.parse_args')
    @patch('sys.stderr', new_callable=StringIO)
    def test_main_value_error(self, mock_stderr, mock_parse_args):
        """Test main function with value error."""
        # Mock the return value of parse_args()
        mock_args = Mock()
        mock_args.input_file = "invalid_file"
        mock_args.directory = self.test_dir
        mock_args.tree = True
        mock_parse_args.return_value = mock_args

        with self.assertRaises(SystemExit) as cm:
            main()

        self.assertEqual(cm.exception.code, 1)
        error_output = mock_stderr.getvalue()
        self.assertIn("❌ File not found", error_output)

    @patch('c2md.__main__.validate_input_file')
    @patch('argparse.ArgumentParser.parse_args')
    @patch('sys.stderr', new_callable=StringIO)
    def test_main_unexpected_error(self, mock_stderr, mock_parse_args, mock_validate):
        """Test main function with unexpected error."""
        # Mock parsed arguments
        mock_args = Mock()
        mock_args.input_file = self.test_file
        mock_args.directory = self.test_dir
        mock_args.tree = True
        mock_parse_args.return_value = mock_args

        # Make validation fail with unexpected error
        mock_validate.side_effect = RuntimeError("Unexpected error")

        with self.assertRaises(SystemExit) as cm:
            main()

        self.assertEqual(cm.exception.code, 1)
        error_output = mock_stderr.getvalue()
        self.assertIn("❌ Unexpected error", error_output)
        self.assertIn("💡 Please check your input file and try again", error_output)

    @patch('c2md.__main__.Context7Parser')
    @patch('argparse.ArgumentParser.parse_args')
    @patch('sys.stdout', new_callable=StringIO)
    def test_main_no_entries_found(self, mock_stdout, mock_parse_args, mock_parser):
        """Test main function when no entries are found."""
        # Mock parsed arguments
        mock_args = Mock()
        mock_args.input_file = self.test_file
        mock_args.directory = self.test_dir
        mock_args.tree = True
        mock_parse_args.return_value = mock_args

        mock_parser_instance = Mock()
        mock_parser_instance.parse_file.return_value = []  # No entries
        mock_parser.return_value = mock_parser_instance

        main()

        output = mock_stdout.getvalue()
        self.assertIn("⚠️  No entries found in the input file", output)

    @patch('c2md.__main__.validate_input_file')
    @patch('c2md.__main__.ensure_output_directory')
    @patch('c2md.__main__.Context7Parser')
    @patch('c2md.__main__.FileOrganizer')
    @patch('c2md.__main__.MarkdownWriter')
    @patch('argparse.ArgumentParser.parse_args')
    @patch('sys.stdout', new_callable=StringIO)
    def test_main_argument_parsing(self, mock_stdout, mock_parse_args, mock_writer, mock_organizer, mock_parser, mock_ensure_dir, mock_validate):
        """Test that command line arguments are parsed correctly."""
        # Mock parsed arguments
        mock_args = Mock()
        mock_args.input_file = 'input.txt'
        mock_args.directory = '/custom/dir'
        mock_args.tree = False  # --no-tree flag
        mock_parse_args.return_value = mock_args

        # Mock empty parsing to avoid workflow execution
        mock_parser_instance = Mock()
        mock_parser_instance.parse_file.return_value = []
        mock_parser.return_value = mock_parser_instance

        main()

        # Verify that validate_input_file was called with correct path
        mock_validate.assert_called_once_with('input.txt')
        # Verify that ensure_output_directory was called with correct output dir
        mock_ensure_dir.assert_called_once_with('/custom/dir/output')
            # These would have been called during execution


class TestIntegrationScenarios(unittest.TestCase):
    """Integration test scenarios for main function."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_end_to_end_workflow_minimal(self):
        """Test minimal end-to-end workflow with real components."""
        # Create a test Context7 file
        test_file = os.path.join(self.test_dir, "test.context7")
        context7_content = """TITLE: Sample Entry
DESCRIPTION: This is a test entry
SOURCE: https://example.com/docs/api/sample
LANGUAGE: python
CODE:
print("Hello, World!")
"""
        with open(test_file, 'w') as f:
            f.write(context7_content)

        mock_argv = ['__main__.py', test_file, '-d', self.test_dir, '--no-tree']

        with patch.object(sys, 'argv', mock_argv):
            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                main()

                output = mock_stdout.getvalue()
                self.assertIn("✅ Processing complete!", output)
                self.assertIn("📋 Processed 1 Context7 entries", output)

                # Check that output was created
                output_dir = os.path.join(self.test_dir, "output")
                self.assertTrue(os.path.exists(output_dir))


if __name__ == '__main__':
    unittest.main()
