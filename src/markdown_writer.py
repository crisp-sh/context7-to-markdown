"""
Markdown generation module for Context7-to-Markdown CLI tool.

This module generates markdown files from organized Context7 entries. It creates
properly formatted markdown documents with titles, descriptions, code blocks,
and source attribution. Multiple entries sharing the same source URL are combined
into a single markdown file.
"""

import os
from typing import List, Dict, Any, Optional, Union
from pathlib import Path

try:
    from .file_organizer import OrganizedFile
except ImportError:
    from file_organizer import OrganizedFile


class MarkdownWriterError(Exception):
    """Custom exception for markdown writing errors."""
    pass


class MarkdownWriter:
    """Generates markdown files from organized Context7 entries."""
    
    def __init__(self, output_directory: str = "output"):
        """
        Initialize the markdown writer.
        
        Args:
            output_directory: Base directory where markdown files will be written
        """
        self.output_directory = output_directory
        self._ensure_output_directory()
    
    def _ensure_output_directory(self):
        """Create the output directory if it doesn't exist."""
        Path(self.output_directory).mkdir(parents=True, exist_ok=True)
    
    def write_file(self, organized_file: OrganizedFile) -> str:
        """
        Write a single organized file to markdown.
        
        Args:
            organized_file: OrganizedFile instance containing entry and metadata
            
        Returns:
            Full path to the written markdown file
            
        Raises:
            MarkdownWriterError: If writing fails
        """
        try:
            # Generate markdown content
            content = self._generate_markdown_content([organized_file])
            
            # Determine output path
            output_path = os.path.join(self.output_directory, organized_file.full_path)
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Write file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return output_path
            
        except Exception as e:
            raise MarkdownWriterError(f"Failed to write markdown file '{organized_file.full_path}': {str(e)}")
    
    def write_files(self, organized_files: List[OrganizedFile]) -> List[str]:
        """
        Write multiple organized files to markdown.
        
        Args:
            organized_files: List of OrganizedFile instances
            
        Returns:
            List of full paths to written markdown files
            
        Raises:
            MarkdownWriterError: If writing fails
        """
        if not organized_files:
            return []
        
        written_files = []
        
        # Group files by their full path (files with same source URL)
        file_groups = self._group_files_by_path(organized_files)
        
        for file_path, files in file_groups.items():
            try:
                # Generate combined content for files sharing the same path
                content = self._generate_markdown_content(files)
                
                # Determine output path
                output_path = os.path.join(self.output_directory, file_path)
                
                # Ensure directory exists
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                
                # Write file
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                written_files.append(output_path)
                
            except Exception as e:
                raise MarkdownWriterError(f"Failed to write markdown file '{file_path}': {str(e)}")
        
        return written_files
    
    def _group_files_by_path(self, organized_files: List[OrganizedFile]) -> Dict[str, List[OrganizedFile]]:
        """
        Group organized files by their full path.
        
        Files with the same source URL should be combined into a single markdown file.
        
        Args:
            organized_files: List of OrganizedFile instances
            
        Returns:
            Dictionary mapping file paths to lists of OrganizedFile instances
        """
        file_groups = {}
        
        for organized_file in organized_files:
            path = organized_file.full_path
            if path not in file_groups:
                file_groups[path] = []
            file_groups[path].append(organized_file)
        
        return file_groups
    
    def _generate_markdown_content(self, organized_files: List[OrganizedFile]) -> str:
        """
        Generate markdown content for one or more organized files.
        
        Args:
            organized_files: List of OrganizedFile instances (should share same source URL)
            
        Returns:
            Complete markdown content as string
        """
        if not organized_files:
            return ""
        
        # Sort files by their number to maintain order
        sorted_files = sorted(organized_files, key=lambda f: f.number)
        
        # Generate main title
        if len(sorted_files) == 1:
            main_title = sorted_files[0].entry.get('title', '').strip() or 'Untitled'
        else:
            # For multiple entries, use a combined title or the first entry's title
            main_title = sorted_files[0].entry.get('title', '').strip() or 'Untitled'
        
        # Start building content
        content_parts = [f"# {main_title}\n"]
        
        # Add each entry as a section
        for organized_file in sorted_files:
            entry = organized_file.entry
            
            # Add entry title as h2
            title = entry.get('title', '').strip() or 'Untitled'
            content_parts.append(f"## {title}\n")
            
            # Add description if present
            description = entry.get('description', '').strip()
            if description:
                content_parts.append(f"{description}\n")
            
            # Add code block if present
            code = entry.get('code', '').strip()
            if code:
                language = entry.get('language', '').lower()
                # Clean up language identifier
                language = self._clean_language_identifier(language)
                content_parts.append(f"### {language.title() if language else 'Code'}\n")
                content_parts.append(f"```{language}\n{code}\n```\n")
        
        # Add source attribution
        source_url = sorted_files[0].entry.get('source', '')
        if source_url:
            content_parts.append("---\n")
            content_parts.append(f"*Source: {source_url}*\n")
        
        return "\n".join(content_parts)
    
    def _clean_language_identifier(self, language: str) -> str:
        """
        Clean and normalize language identifier for code blocks.
        
        Args:
            language: Raw language string from entry
            
        Returns:
            Cleaned language identifier
        """
        if not language:
            return ""
        
        # Convert to lowercase and strip whitespace
        cleaned = language.lower().strip()
        
        # Map common variations to standard identifiers
        language_map = {
            'javascript': 'javascript',
            'js': 'javascript',
            'typescript': 'typescript',
            'ts': 'typescript',
            'python': 'python',
            'py': 'python',
            'java': 'java',
            'c++': 'cpp',
            'cpp': 'cpp',
            'c#': 'csharp',
            'csharp': 'csharp',
            'html': 'html',
            'css': 'css',
            'sql': 'sql',
            'bash': 'bash',
            'shell': 'bash',
            'sh': 'bash',
            'json': 'json',
            'xml': 'xml',
            'yaml': 'yaml',
            'yml': 'yaml',
            'markdown': 'markdown',
            'md': 'markdown',
        }
        
        return language_map.get(cleaned, cleaned)
    
    def get_output_summary(self, organized_files: List[OrganizedFile]) -> Dict[str, Any]:
        """
        Get a summary of what would be written without actually writing files.
        
        Args:
            organized_files: List of OrganizedFile instances
            
        Returns:
            Dictionary containing summary information
        """
        if not organized_files:
            return {
                'total_files': 0,
                'total_entries': 0,
                'file_paths': [],
                'directories': set()
            }
        
        file_groups = self._group_files_by_path(organized_files)
        file_paths = list(file_groups.keys())
        directories = {os.path.dirname(path) for path in file_paths if os.path.dirname(path)}
        
        return {
            'total_files': len(file_groups),
            'total_entries': len(organized_files),
            'file_paths': file_paths,
            'directories': directories
        }


# Convenience functions
def write_markdown_file(organized_file: OrganizedFile, output_directory: str = "output") -> str:
    """
    Convenience function to write a single organized file to markdown.
    
    Args:
        organized_file: OrganizedFile instance
        output_directory: Directory where the file will be written
        
    Returns:
        Full path to the written file
    """
    writer = MarkdownWriter(output_directory)
    return writer.write_file(organized_file)


def write_markdown_files(organized_files: List[OrganizedFile], output_directory: str = "output") -> List[str]:
    """
    Convenience function to write multiple organized files to markdown.
    
    Args:
        organized_files: List of OrganizedFile instances
        output_directory: Directory where files will be written
        
    Returns:
        List of full paths to written files
    """
    writer = MarkdownWriter(output_directory)
    return writer.write_files(organized_files)


def preview_markdown_content(organized_files: List[OrganizedFile]) -> str:
    """
    Preview the markdown content that would be generated without writing to file.
    
    Args:
        organized_files: List of OrganizedFile instances (should share same source)
        
    Returns:
        Generated markdown content
    """
    writer = MarkdownWriter()
    return writer._generate_markdown_content(organized_files)