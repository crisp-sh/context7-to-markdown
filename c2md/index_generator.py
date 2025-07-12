"""
Index generation module for Context7-to-Markdown CLI tool.

This module generates a table of contents (index) file from a list of generated
markdown files. It organizes files by directory structure and creates a
hierarchical navigation document with properly formatted markdown links.
"""

import os
import re
from collections import defaultdict
from typing import Any, Dict, List, Optional

try:
    from .markdown_writer import OrganizedFile
except ImportError:
    from markdown_writer import OrganizedFile


class IndexGeneratorError(Exception):
    """Custom exception for index generation errors."""
    pass


class IndexGenerator:
    """Generates table of contents index from markdown files."""

    def __init__(self, output_directory: str = "output", no_prefix: bool = False):
        """
        Initialize the index generator.

        Args:
            output_directory: Base directory where files are located and index will be written
            no_prefix: If True, omit numeric prefix in index filename
        """
        self.output_directory = output_directory
        if no_prefix:
            self.index_filename = "index.md"
        else:
            self.index_filename = "000-index.md"

    def generate_index(self, file_paths: List[str], output_path: Optional[str] = None) -> str:
        """
        Generate index file from a list of markdown file paths.

        Args:
            file_paths: List of relative file paths to include in index
            output_path: Optional custom output path for index file

        Returns:
            Full path to the generated index file

        Raises:
            IndexGeneratorError: If generation fails
        """
        try:
            # Organize files by directory
            directory_structure = self._organize_files_by_directory(file_paths)

            # Generate index content
            content = self._generate_index_content(directory_structure)

            # Determine output path
            if output_path is None:
                output_path = os.path.join(self.output_directory, self.index_filename)

            # Ensure directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            # Write index file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)

            return output_path

        except Exception as e:
            raise IndexGeneratorError(f"Failed to generate index: {str(e)}")

    def generate_index_from_organized_files(self, organized_files: List[OrganizedFile],
                                          output_path: Optional[str] = None) -> str:
        """
        Generate index file from organized file objects.

        Args:
            organized_files: List of OrganizedFile instances
            output_path: Optional custom output path for index file

        Returns:
            Full path to the generated index file
        """
        # Extract file paths from organized files
        file_paths = [organized_file.full_path for organized_file in organized_files]

        # Create enhanced structure with title information
        directory_structure = self._organize_files_by_directory(file_paths)

        # Enhance with titles from organized files
        for organized_file in organized_files:
            file_path = organized_file.full_path
            if isinstance(organized_file.entry, dict):
                title = organized_file.entry.get('title', '').strip()
            else:
                title = organized_file.entry.main_title

            # Find the file in our structure and add title
            directory = os.path.dirname(file_path) or '.'
            filename = os.path.basename(file_path)

            if directory in directory_structure:
                for file_info in directory_structure[directory]:
                    if file_info['filename'] == filename:
                        if title:
                            file_info['title'] = title
                        break

        # Generate content and write file
        content = self._generate_index_content(directory_structure)

        if output_path is None:
            output_path = os.path.join(self.output_directory, self.index_filename)

        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return output_path

    def _organize_files_by_directory(self, file_paths: List[str]) -> Dict[str, List[Dict[str, str]]]:
        """
        Organize file paths by their directory structure.

        Args:
            file_paths: List of file paths to organize

        Returns:
            Dictionary mapping directory paths to lists of file information
        """
        directory_structure = defaultdict(list)

        for file_path in file_paths:
            # Normalize path separators
            file_path = file_path.replace('\\', '/')

            # Extract directory and filename
            directory = os.path.dirname(file_path) or '.'
            filename = os.path.basename(file_path)

            # Skip if not a markdown file
            if not filename.lower().endswith('.md'):
                continue

            # Extract title from filename (remove numbering and extension)
            title = self._extract_title_from_filename(filename)

            # Add to structure
            directory_structure[directory].append({
                'filename': filename,
                'path': file_path,
                'title': title
            })

        # Sort files within each directory
        for directory in directory_structure:
            directory_structure[directory].sort(key=lambda x: x['filename'])

        return dict(directory_structure)

    def _extract_title_from_filename(self, filename: str) -> str:
        """
        Extract a human-readable title from a filename.

        Args:
            filename: The filename to extract title from

        Returns:
            Extracted title string
        """
        # Remove extension
        name = os.path.splitext(filename)[0]

        # Remove numbering prefix (e.g., "001-", "002-")
        name = re.sub(r'^\d+[-_]*', '', name)

        # Replace hyphens and underscores with spaces
        name = name.replace('-', ' ').replace('_', ' ')

        # Title case
        title = ' '.join(word.capitalize() for word in name.split())

        return title if title else 'Untitled'

    def _extract_title_from_markdown(self, file_path: str) -> Optional[str]:
        """
        Extract title from markdown file's first heading.

        Args:
            file_path: Path to the markdown file

        Returns:
            Extracted title or None if not found
        """
        try:
            full_path = os.path.join(self.output_directory, file_path)

            if not os.path.exists(full_path):
                return None

            with open(full_path, encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    # Look for first heading
                    if line.startswith('#'):
                        # Extract title from heading
                        title = re.sub(r'^#+\s*', '', line).strip()
                        return title if title else None
                    # Stop at first non-empty, non-heading line
                    elif line:
                        break

        except Exception:
            # If we can't read the file, that's okay
            pass

        return None

    def _generate_index_content(self, directory_structure: Dict[str, List[Dict[str, str]]]) -> str:
        """
        Generate the complete index markdown content.

        Args:
            directory_structure: Organized directory structure

        Returns:
            Complete markdown content for the index
        """
        content_parts = [
            "# Documentation Index\n",
            "## Table of Contents\n"
        ]

        # Sort directories (root directory first, then alphabetically)
        sorted_directories = sorted(directory_structure.keys(),
                                  key=lambda d: (d != '.', d))

        for directory in sorted_directories:
            files = directory_structure[directory]

            if not files:
                continue

            # Add directory heading
            if directory == '.':
                # Root directory - don't show a heading
                pass
            else:
                content_parts.append(f"### {directory}/\n")

            # Add file links
            for file_info in files:
                file_info['filename']
                file_path = file_info['path']
                title = file_info['title']

                # Try to get a better title from the markdown file
                markdown_title = self._extract_title_from_markdown(file_path)
                if markdown_title:
                    title = markdown_title

                # Create markdown link
                content_parts.append(f"- [{title}]({file_path})\n")

            content_parts.append("\n")

        # Add footer
        content_parts.extend([
            "---\n",
            "*Generated by Context7-to-Markdown CLI Tool*\n"
        ])

        return "".join(content_parts)

    def get_index_summary(self, file_paths: List[str]) -> Dict[str, Any]:
        """
        Get a summary of what the index would contain without generating it.

        Args:
            file_paths: List of file paths to analyze

        Returns:
            Dictionary containing summary information
        """
        directory_structure = self._organize_files_by_directory(file_paths)

        total_files = sum(len(files) for files in directory_structure.values())
        directory_count = len(directory_structure)

        # Get directory breakdown
        directory_breakdown = {}
        for directory, files in directory_structure.items():
            directory_breakdown[directory] = len(files)

        return {
            'total_files': total_files,
            'total_directories': directory_count,
            'directory_breakdown': directory_breakdown,
            'index_filename': self.index_filename,
            'output_path': os.path.join(self.output_directory, self.index_filename)
        }


# Convenience functions
def generate_index(file_paths: List[str], output_directory: str = "output",
                  output_path: Optional[str] = None) -> str:
    """
    Convenience function to generate index from file paths.

    Args:
        file_paths: List of markdown file paths
        output_directory: Directory where files are located
        output_path: Optional custom output path for index

    Returns:
        Full path to generated index file
    """
    generator = IndexGenerator(output_directory)
    return generator.generate_index(file_paths, output_path)


def generate_index_from_organized_files(organized_files: List[OrganizedFile],
                                       output_directory: str = "output",
                                       output_path: Optional[str] = None) -> str:
    """
    Convenience function to generate index from organized files.

    Args:
        organized_files: List of OrganizedFile instances
        output_directory: Directory where files are located
        output_path: Optional custom output path for index

    Returns:
        Full path to generated index file
    """
    generator = IndexGenerator(output_directory)
    return generator.generate_index_from_organized_files(organized_files, output_path)


def preview_index_content(file_paths: List[str], output_directory: str = "output") -> str:
    """
    Preview the index content that would be generated without writing to file.

    Args:
        file_paths: List of markdown file paths
        output_directory: Directory where files are located

    Returns:
        Generated index content
    """
    generator = IndexGenerator(output_directory)
    directory_structure = generator._organize_files_by_directory(file_paths)
    return generator._generate_index_content(directory_structure)
