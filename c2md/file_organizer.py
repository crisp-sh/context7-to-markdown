"""
File organization module for Context7-to-Markdown CLI tool.

This module organizes parsed Context7 entries into a logical directory structure
with numbered files, ready for markdown generation. It uses the URLMapper to
determine directory paths and implements a numbering scheme for files within
the same directory.
"""

import os
from collections import defaultdict
from typing import Any, Dict, List, Optional, Union

try:
    from .url_mapper import URLMapper
except ImportError:
    from url_mapper import URLMapper


class FileOrganizerError(Exception):
    """Custom exception for file organization errors."""
    pass


class ConsolidatedEntry:
    """Represents a consolidated entry with multiple content variants."""

    def __init__(self, source_url: str, entries: List[Dict[str, Any]]):
        """
        Initialize a consolidated entry.

        Args:
            source_url: Common source URL for all entries
            entries: List of entries sharing the same source URL
        """
        self.source_url = source_url
        self.entries = entries
        self.main_title = self._extract_main_title()
        self.language_variants = self._extract_language_variants()

    def _extract_main_title(self) -> str:
        """Extract the main title from the consolidated entries."""
        if not self.entries:
            return 'Untitled'

        # Use the first entry's title as the main title
        # TODO: Could be enhanced to find the most descriptive title
        return self.entries[0].get('title', 'Untitled').strip()

    def _extract_language_variants(self) -> List[Dict[str, Any]]:
        """Extract language variants from the entries."""
        variants = []
        for entry in self.entries:
            variant = {
                'title': entry.get('title', '').strip(),
                'description': entry.get('description', '').strip(),
                'code': entry.get('code', '').strip(),
                'language': self._detect_language(entry),
                'original_entry': entry
            }
            variants.append(variant)
        return variants

    def _detect_language(self, entry: Dict[str, Any]) -> str:
        """Detect the programming language from an entry."""
        # First check if language is explicitly specified
        if 'language' in entry and entry['language']:
            return entry['language'].lower().strip()

        # Try to infer from code content or title
        code = entry.get('code', '').strip()
        title = entry.get('title', '').lower()

        # Language detection heuristics
        if 'curl' in title or 'bash' in title or code.startswith('curl'):
            return 'bash'
        elif 'sql' in title or 'CREATE TABLE' in code.upper() or 'SELECT' in code.upper():
            return 'sql'
        elif 'javascript' in title or 'js' in title or 'import' in code:
            return 'javascript'
        elif 'json' in title or code.strip().startswith('{') or code.strip().startswith('['):
            return 'json'
        elif 'python' in title or 'py' in title:
            return 'python'
        elif 'http' in code.upper() and 'content-type' in code.lower():
            return 'http'

        return 'text'


class OrganizedFile:
    """Represents a single organized file with its metadata."""

    def __init__(self, entry: Union[Dict[str, Any], ConsolidatedEntry], directory_path: str,
                 filename: str, number: int):
        """
        Initialize an organized file.

        Args:
            entry: Original parsed entry from Context7Parser or ConsolidatedEntry
            directory_path: Target directory path for the file
            filename: Generated filename for the file
            number: Sequential number within the directory
        """
        self.entry = entry
        self.directory_path = directory_path
        self.filename = filename
        self.number = number
        self.full_path = os.path.join(directory_path, filename) if directory_path else filename
        self.is_consolidated = isinstance(entry, ConsolidatedEntry)

    def __repr__(self):
        if isinstance(self.entry, ConsolidatedEntry):
            return f"OrganizedFile(path='{self.full_path}', consolidated_title='{self.entry.main_title}', variants={len(self.entry.language_variants)})"
        else:
            return f"OrganizedFile(path='{self.full_path}', title='{self.entry.get('title', 'Untitled')}')"


class FileOrganizer:
    """Organizes Context7 entries into a structured directory layout."""

    def __init__(self, url_mapper: Optional[URLMapper] = None, no_prefix: bool = False):
        """
        Initialize the file organizer.

        Args:
            url_mapper: URLMapper instance for path extraction. If None, creates a new instance.
            no_prefix: If True, filenames will be generated without number prefixes
        """
        self.url_mapper = url_mapper or URLMapper(no_prefix=no_prefix)
        self.no_prefix = no_prefix
        self._directory_counters = defaultdict(int)

    def organize_entries(self, entries: List[Dict[str, Any]]) -> Dict[str, List[OrganizedFile]]:
        """
        Organize parsed entries into a structured directory layout.
        Groups entries by source_url first, then by directory.

        Args:
            entries: List of parsed entries from Context7Parser

        Returns:
            Dictionary where keys are directory paths and values are lists of OrganizedFile objects

        Raises:
            FileOrganizerError: If organization fails
        """
        if not entries:
            return {}

        if not isinstance(entries, list):
            raise FileOrganizerError("Entries must be a list")

        try:
            # First, group entries by source_url for consolidation
            source_url_groups = self._group_by_source_url(entries)

            # Create consolidated entries or keep single entries
            consolidated_entries = self._create_consolidated_entries(source_url_groups)

            # Group by directory
            directory_groups = self._group_by_directory_consolidated(consolidated_entries)

            # Create organized structure
            organized_structure = self._create_organized_structure_consolidated(directory_groups)

            return organized_structure

        except FileOrganizerError:
            # Re-raise specific errors
            raise
        except Exception as e:
            # Wrap generic exceptions
            raise FileOrganizerError(f"An unexpected error occurred during file organization: {e}") from e

    def _group_by_directory(self, entries: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Group entries by their target directory path.

        Args:
            entries: List of parsed entries

        Returns:
            Dictionary mapping directory paths to lists of entries
        """
        grouped = defaultdict(list)

        for entry in entries:
            source_url = entry.get('source', '')
            if not source_url:
                # Handle entries without source URLs
                grouped[''].append(entry)
                continue

            try:
                directory_path = self.url_mapper.extract_path(source_url)
                # Extract directory part (everything except last segment)
                if '/' in directory_path:
                    directory_path = '/'.join(directory_path.split('/')[:-1])
                else:
                    # Single segment - treat as filename, place in root directory
                    directory_path = ''

                grouped[directory_path].append(entry)

            except Exception as e:
                # Handle URL mapping errors by placing in root
                print(f"Warning: Could not extract path from URL '{source_url}': {e}")
                grouped[''].append(entry)

        return dict(grouped)

    def _create_organized_structure(self, grouped_entries: Dict[str, List[Dict[str, Any]]]) -> Dict[str, List[OrganizedFile]]:
        """
        Create the final organized structure with numbered files.

        Args:
            grouped_entries: Dictionary mapping directory paths to entries

        Returns:
            Dictionary mapping directory paths to lists of OrganizedFile objects
        """
        organized_structure = {}

        for directory_path, entries in grouped_entries.items():
            organized_files = []

            # Sort entries by original order to maintain consistency
            sorted_entries = sorted(entries, key=lambda x: x.get('original_order', 0))

            for entry in sorted_entries:
                # Get next number for this directory
                self._directory_counters[directory_path] += 1
                file_number = self._directory_counters[directory_path]

                # Generate filename
                filename = self._generate_filename(entry, file_number)

                # Create organized file object
                organized_file = OrganizedFile(
                    entry=entry,
                    directory_path=directory_path,
                    filename=filename,
                    number=file_number
                )

                organized_files.append(organized_file)

            organized_structure[directory_path] = organized_files

        return organized_structure

    def _generate_filename(self, entry: Dict[str, Any], number: int) -> str:
        """
        Generate a filename for an entry with or without number prefix.

        Args:
            entry: Parsed entry dictionary
            number: Sequential number for the file

        Returns:
            Generated filename with or without number prefix based on no_prefix flag
        """
        source_url = entry.get('source', '')

        if source_url:
            try:
                # Use URL mapper to generate numbered filename
                return self.url_mapper.get_numbered_filename(source_url, number)
            except Exception:
                # Fallback to title-based filename
                pass

        # Fallback: use title or default name
        title = entry.get('title', 'untitled')
        # Clean title for filename
        clean_title = self._clean_filename(title)
        
        if self.no_prefix:
            # Return filename without number prefix
            return f"{clean_title}.md"
        else:
            # Format number with zero padding (3 digits)
            padded_number = f"{number:03d}"
            return f"{padded_number}-{clean_title}.md"

    def _clean_filename(self, filename: str) -> str:
        """
        Clean a string to be suitable for use as a filename.

        Args:
            filename: Raw filename string

        Returns:
            Cleaned filename string
        """
        import re

        # Convert to lowercase and replace spaces with hyphens
        clean = filename.lower().replace(' ', '-')

        # Remove or replace invalid characters
        clean = re.sub(r'[^\w\-.]', '', clean)

        # Remove multiple consecutive hyphens
        clean = re.sub(r'-+', '-', clean)

        # Remove leading/trailing hyphens
        clean = clean.strip('-')

        # Ensure it's not empty
        if not clean:
            clean = 'untitled'

        return clean
    def _group_by_source_url(self, entries: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Group entries by their source_url for consolidation.

        Args:
            entries: List of parsed entries

        Returns:
            Dictionary mapping source URLs to lists of entries
        """
        grouped = defaultdict(list)

        for entry in entries:
            source_url = entry.get('source', '')
            if source_url:
                grouped[source_url].append(entry)
            else:
                # Handle entries without source URLs - each gets its own group
                grouped[f"no_source_{id(entry)}"].append(entry)

        return grouped

    def _create_consolidated_entries(self, source_url_groups: Dict[str, List[Dict[str, Any]]]) -> List[Union[Dict[str, Any], ConsolidatedEntry]]:
        """
        Create consolidated entries or keep single entries.

        Args:
            source_url_groups: Dictionary mapping source URLs to lists of entries

        Returns:
            List of either single entries or ConsolidatedEntry objects
        """
        consolidated_entries = []

        for source_url, entries in source_url_groups.items():
            if len(entries) > 1:
                # Multiple entries for the same source URL - consolidate them
                consolidated_entry = ConsolidatedEntry(source_url, entries)
                consolidated_entries.append(consolidated_entry)
            else:
                # Single entry - keep as is
                consolidated_entries.append(entries[0])

        return consolidated_entries

    def _group_by_directory_consolidated(self, consolidated_entries: List[Union[Dict[str, Any], ConsolidatedEntry]]) -> Dict[str, List[Union[Dict[str, Any], ConsolidatedEntry]]]:
        """
        Group consolidated entries by their target directory path.

        Args:
            consolidated_entries: List of entries or ConsolidatedEntry objects

        Returns:
            Dictionary mapping directory paths to lists of entries
        """
        grouped = defaultdict(list)

        for entry in consolidated_entries:
            if isinstance(entry, ConsolidatedEntry):
                # Use the source URL from the consolidated entry
                source_url = entry.source_url
            else:
                # Use the source URL from the regular entry
                source_url = entry.get('source', '')

            if not source_url:
                # Handle entries without source URLs
                grouped[''].append(entry)
                continue

            try:
                directory_path = self.url_mapper.extract_path(source_url)
                # Extract directory part (everything except last segment)
                if '/' in directory_path:
                    directory_path = '/'.join(directory_path.split('/')[:-1])
                else:
                    # Single segment - treat as filename, place in root directory
                    directory_path = ''

                grouped[directory_path].append(entry)

            except Exception:
                # Fallback to root directory if URL mapping fails
                grouped[''].append(entry)

        return grouped

    def _create_organized_structure_consolidated(self, grouped_entries: Dict[str, List[Union[Dict[str, Any], ConsolidatedEntry]]]) -> Dict[str, List[OrganizedFile]]:
        """
        Create organized structure from grouped consolidated entries.

        Args:
            grouped_entries: Dictionary mapping directory paths to consolidated entries

        Returns:
            Dictionary mapping directory paths to lists of OrganizedFile objects
        """
        organized_structure = {}

        for directory_path, entries in grouped_entries.items():
            organized_files = []

            # Sort entries by original order to maintain consistency
            # For ConsolidatedEntry, use the first entry's order
            def get_sort_key(entry):
                if isinstance(entry, ConsolidatedEntry):
                    return entry.entries[0].get('original_order', 0)
                else:
                    return entry.get('original_order', 0)

            sorted_entries = sorted(entries, key=get_sort_key)

            for entry in sorted_entries:
                # Get next number for this directory
                self._directory_counters[directory_path] += 1
                file_number = self._directory_counters[directory_path]

                # Generate filename
                filename = self._generate_filename_consolidated(entry, file_number)

                # Create organized file object
                organized_file = OrganizedFile(
                    entry=entry,
                    directory_path=directory_path,
                    filename=filename,
                    number=file_number
                )

                organized_files.append(organized_file)

            organized_structure[directory_path] = organized_files

        return organized_structure

    def _generate_filename_consolidated(self, entry: Union[Dict[str, Any], ConsolidatedEntry], number: int) -> str:
        """
        Generate a filename for a consolidated entry with number prefix.

        Args:
            entry: Entry or ConsolidatedEntry object
            number: Sequential number for the file

        Returns:
            Generated filename with number prefix
        """
        if isinstance(entry, ConsolidatedEntry):
            # Use the source URL from the consolidated entry
            source_url = entry.source_url
            # Use the main title as the base filename
            title = entry.main_title
        else:
            # Use the source URL from the regular entry
            source_url = entry.get('source', '')
            title = entry.get('title', 'untitled')

        if source_url:
            try:
                # Use URL mapper to generate numbered filename
                return self.url_mapper.get_numbered_filename(source_url, number)
            except Exception:
                # Fallback to title-based filename
                pass

        # Fallback: use title or default name
        # Clean title for filename
        clean_title = self._clean_filename(title)
        padded_number = f"{number:03d}"
        return f"{padded_number}-{clean_title}.md"

    def get_directory_summary(self, organized_structure: Dict[str, List[OrganizedFile]]) -> Dict[str, Any]:
        """
        Generate a summary of the organized directory structure.

        Args:
            organized_structure: Organized file structure

        Returns:
            Summary dictionary with statistics and structure info
        """
        summary = {
            'total_files': 0,
            'total_directories': len(organized_structure),
            'directories': {},
            'structure_preview': []
        }

        for directory_path, files in organized_structure.items():
            dir_name = directory_path if directory_path else 'root'
            summary['directories'][dir_name] = {
                'file_count': len(files),
                'files': [f.filename for f in files]
            }
            summary['total_files'] += len(files)

            # Add to structure preview
            summary['structure_preview'].append({
                'directory': dir_name,
                'files': len(files)
            })

        return summary

    def reset_counters(self):
        """Reset directory counters for a fresh organization."""
        self._directory_counters.clear()


def organize_context7_entries(entries: List[Dict[str, Any]],
                            url_mapper: Optional[URLMapper] = None) -> Dict[str, List[OrganizedFile]]:
    """
    Convenience function to organize Context7 entries.

    Args:
        entries: List of parsed Context7 entries
        url_mapper: Optional URLMapper instance

    Returns:
        Organized file structure dictionary

    Raises:
        FileOrganizerError: If organization fails
    """
    organizer = FileOrganizer(url_mapper)
    return organizer.organize_entries(entries)


# TODO: Add support for custom numbering schemes (e.g., hexadecimal, alphabetical)
# TODO: Add configuration for custom filename patterns
# FUTURE: Consider adding support for duplicate detection and handling
# FUTURE: Add support for organizing by language or other metadata fields
