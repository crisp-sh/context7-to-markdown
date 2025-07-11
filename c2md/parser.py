"""
Context7 format parser module.

This module implements parsing of Context7 format text files into structured data.
The Context7 format uses '----------------------------------------' as entry delimiters and contains
metadata fields (TITLE, DESCRIPTION, SOURCE, LANGUAGE) followed by code content.
"""

import re
from typing import Any, Dict, List, Optional


class Context7ParseError(Exception):
    """Custom exception for Context7 parsing errors."""
    pass


class Context7Parser:
    """Parser for Context7 format text files."""

    # Delimiter that separates entries
    ENTRY_DELIMITER = "----------------------------------------"

    # Metadata field patterns
    METADATA_FIELDS = {
        'title': r'^TITLE:\s*(.*)$',
        'description': r'^DESCRIPTION:\s*(.*)$',
        'source': r'^SOURCE:\s*(.*)$',
        'language': r'^LANGUAGE:\s*(.*)$'
    }

    def __init__(self):
        """Initialize the parser."""
        self.entries = []
        self.original_order = 0

    def parse_file(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Parse a Context7 format file and return list of entry dictionaries.

        Args:
            file_path: Path to the Context7 format text file

        Returns:
            List of entry dictionaries with structure:
            {
                "title": str,
                "description": str,
                "source": str,
                "language": str,
                "code": str,
                "original_order": int
            }

        Raises:
            Context7ParseError: If file cannot be read or parsed
            FileNotFoundError: If file does not exist
        """
        try:
            with open(file_path, encoding='utf-8') as file:
                content = file.read()
            return self.parse_content(content)
        except FileNotFoundError:
            raise Context7ParseError(f"File not found: {file_path}")
        except Exception as e:
            raise Context7ParseError(f"Error reading file {file_path}: {str(e)}")

    def parse_content(self, content: str) -> List[Dict[str, Any]]:
        """
        Parse Context7 format content string.

        Args:
            content: Raw text content in Context7 format

        Returns:
            List of parsed entry dictionaries
        """
        self.entries = []
        self.original_order = 0

        # Split content by delimiter
        raw_entries = content.split(self.ENTRY_DELIMITER)

        for raw_entry in raw_entries:
            raw_entry = raw_entry.strip()
            if not raw_entry:  # Skip empty entries
                continue

            try:
                parsed_entry = self._parse_single_entry(raw_entry)
                if parsed_entry:  # Only add if parsing was successful
                    self.entries.append(parsed_entry)
            except Exception as e:
                # Log malformed entry but continue processing
                print(f"Warning: Skipping malformed entry at position {self.original_order}: {str(e)}")
                continue

        return self.entries

    def _parse_single_entry(self, entry_text: str) -> Optional[Dict[str, Any]]:
        """
        Parse a single Context7 entry.

        Args:
            entry_text: Raw text of a single entry

        Returns:
            Parsed entry dictionary or None if parsing fails
        """
        lines = entry_text.split('\n')
        entry_data = {
            'title': '',
            'description': '',
            'source': '',
            'language': '',
            'code': '',
            'original_order': self.original_order
        }

        self.original_order += 1

        # Parse metadata fields
        code_start_index = None
        current_field = None

        for i, line in enumerate(lines):
            line = line.strip()

            # Check for metadata fields
            field_found = False
            for field_name, pattern in self.METADATA_FIELDS.items():
                match = re.match(pattern, line, re.IGNORECASE)
                if match:
                    entry_data[field_name] = match.group(1).strip()
                    current_field = field_name
                    field_found = True
                    break

            # Check for CODE: marker
            if re.match(r'^CODE:\s*$', line, re.IGNORECASE):
                code_start_index = i + 1
                current_field = 'code'
                field_found = True
                continue

            # Handle multi-line descriptions and continuation of fields
            if not field_found and current_field and line:
                if current_field == 'description':
                    # Append to description if it's continuing
                    if entry_data['description']:
                        entry_data['description'] += ' ' + line
                    else:
                        entry_data['description'] = line

        # Extract code content
        if code_start_index is not None:
            code_lines = lines[code_start_index:]
            # Remove empty lines at start and end
            while code_lines and not code_lines[0].strip():
                code_lines.pop(0)
            while code_lines and not code_lines[-1].strip():
                code_lines.pop()

            entry_data['code'] = '\n'.join(code_lines)

        # Validate required fields
        if not self._validate_entry(entry_data):
            return None

        return entry_data

    def _validate_entry(self, entry_data: Dict[str, Any]) -> bool:
        """
        Validate that entry has minimum required fields.

        Args:
            entry_data: Parsed entry dictionary

        Returns:
            True if entry is valid, False otherwise
        """
        # At minimum, we need a title and source
        if not entry_data.get('title') or not entry_data.get('source'):
            return False

        # Title should not be empty or just whitespace
        if not entry_data['title'].strip():
            return False

        # Source should look like a URL (basic validation)
        source = entry_data['source'].strip()
        if not (source.startswith('http://') or source.startswith('https://')):
            return False

        return True

    @staticmethod
    def create_sample_entry() -> Dict[str, Any]:
        """
        Create a sample entry for testing purposes.

        Returns:
            Sample entry dictionary
        """
        return {
            'title': 'Sample Entry',
            'description': 'This is a sample Context7 entry for testing.',
            'source': 'https://example.com/docs/sample',
            'language': 'python',
            'code': 'print("Hello, World!")',
            'original_order': 0
        }


def parse_context7_file(file_path: str) -> List[Dict[str, Any]]:
    """
    Convenience function to parse a Context7 file.

    Args:
        file_path: Path to Context7 format file

    Returns:
        List of parsed entry dictionaries

    Raises:
        Context7ParseError: If parsing fails
    """
    parser = Context7Parser()
    return parser.parse_file(file_path)


def parse_context7_content(content: str) -> List[Dict[str, Any]]:
    """
    Convenience function to parse Context7 content string.

    Args:
        content: Context7 format content

    Returns:
        List of parsed entry dictionaries
    """
    parser = Context7Parser()
    return parser.parse_content(content)


# TODO: Add support for nested LANGUAGE/CODE blocks within single entries
# TODO: Add more sophisticated URL validation
# FUTURE: Consider adding support for custom delimiters
# FUTURE: Add support for additional metadata fields beyond the standard four
