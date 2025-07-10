"""
File organization module for Context7-to-Markdown CLI tool.

This module organizes parsed Context7 entries into a logical directory structure
with numbered files, ready for markdown generation. It uses the URLMapper to
determine directory paths and implements a numbering scheme for files within
the same directory.
"""

from typing import List, Dict, Any, Optional
from collections import defaultdict
import os
try:
    from .url_mapper import URLMapper
except ImportError:
    from url_mapper import URLMapper


class FileOrganizerError(Exception):
    """Custom exception for file organization errors."""
    pass


class OrganizedFile:
    """Represents a single organized file with its metadata."""
    
    def __init__(self, entry: Dict[str, Any], directory_path: str, 
                 filename: str, number: int):
        """
        Initialize an organized file.
        
        Args:
            entry: Original parsed entry from Context7Parser
            directory_path: Target directory path for the file
            filename: Generated filename for the file
            number: Sequential number within the directory
        """
        self.entry = entry
        self.directory_path = directory_path
        self.filename = filename
        self.number = number
        self.full_path = os.path.join(directory_path, filename) if directory_path else filename
    
    def __repr__(self):
        return f"OrganizedFile(path='{self.full_path}', title='{self.entry.get('title', 'Untitled')}')"


class FileOrganizer:
    """Organizes Context7 entries into a structured directory layout."""
    
    def __init__(self, url_mapper: Optional[URLMapper] = None):
        """
        Initialize the file organizer.
        
        Args:
            url_mapper: URLMapper instance for path extraction. If None, creates a new instance.
        """
        self.url_mapper = url_mapper or URLMapper()
        self._directory_counters = defaultdict(int)
    
    def organize_entries(self, entries: List[Dict[str, Any]]) -> Dict[str, List[OrganizedFile]]:
        """
        Organize parsed entries into a structured directory layout.
        
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
            # Group entries by directory path
            grouped_entries = self._group_by_directory(entries)
            
            # Number files within each directory and create organized structure
            organized_structure = self._create_organized_structure(grouped_entries)
            
            return organized_structure
            
        except Exception as e:
            raise FileOrganizerError(f"Error organizing entries: {str(e)}")
    
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
        Generate a filename for an entry with number prefix.
        
        Args:
            entry: Parsed entry dictionary
            number: Sequential number for the file
            
        Returns:
            Generated filename with number prefix
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