"""
URL mapping module for Context7-to-Markdown CLI tool.

This module extracts directory paths from SOURCE URLs to organize markdown files
into a proper directory structure. It follows the strategy of extracting path
segments after '/docs/' and preserving subdirectory hierarchies.
"""

import re
from typing import Optional, Tuple
from urllib.parse import urlparse


class URLMapperError(Exception):
    """Custom exception for URL mapping errors."""
    pass


class URLMapper:
    """Maps SOURCE URLs to directory paths for file organization."""

    # Common documentation URL patterns
    DOCS_PATTERNS = [
        r'/documentation(?:/|$)',
        r'/docs(?:/|$)',
        r'/doc(?:/|$)',
        r'/guide(?:/|$)',
        r'/api/(?=(?:docs?|reference))',  # Only match /api/ when followed by docs or reference
        r'/reference(?:/|$)'
    ]

    def __init__(self, no_prefix: bool = False):
        """Initialize the URL mapper.
        
        Args:
            no_prefix: If True, filenames will be generated without number prefixes
        """
        self.no_prefix = no_prefix

    def extract_path(self, source_url: str) -> str:
        """
        Extract directory path from a SOURCE URL.

        Args:
            source_url: The SOURCE URL from a Context7 entry

        Returns:
            Directory path structure for file organization

        Examples:
            https://neon.com/docs/data-api/get-started → data-api/get-started
            https://neon.com/docs/guides/neon-auth-api → guides/neon-auth-api
            https://neon.com/docs/neon-auth/sdk/react/objects/stack-app → neon-auth/sdk/react/objects/stack-app

        Raises:
            URLMapperError: If URL cannot be parsed or no valid path found
        """
        if not source_url or not isinstance(source_url, str):
            raise URLMapperError("Source URL must be a non-empty string")

        # Clean and validate URL
        url = source_url.strip()
        if not self._is_valid_url(url):
            raise URLMapperError(f"Invalid URL format: {url}")

        try:
            parsed_url = urlparse(url)
            path = parsed_url.path

            # Extract path after documentation directory
            docs_path = self._extract_docs_path(path)
            if docs_path is None:
                # Fallback: use the entire path if no docs pattern found
                docs_path = path.lstrip('/')
                if not docs_path:
                    return ''
            elif docs_path == '':
                # Empty path after docs pattern - return empty string
                return ''

            # Clean and format the path
            formatted_path = self._format_path(docs_path)

            if not formatted_path and docs_path:
                raise URLMapperError(f"No valid path extracted from URL: {url}")

            return formatted_path

        except Exception as e:
            if isinstance(e, URLMapperError):
                raise
            raise URLMapperError(f"Error parsing URL {url}: {str(e)}")

    def extract_main_directory(self, source_url: str) -> str:
        """
        Extract just the main directory (first level) from SOURCE URL.

        Args:
            source_url: The SOURCE URL from a Context7 entry

        Returns:
            Main directory name for top-level organization

        Examples:
            https://neon.com/docs/data-api/get-started → data-api
            https://neon.com/docs/guides/neon-auth-api → guides
        """
        full_path = self.extract_path(source_url)
        return full_path.split('/')[0] if full_path else ''

    def extract_file_path(self, source_url: str) -> Tuple[str, str]:
        """
        Extract both directory and filename components from SOURCE URL.

        Args:
            source_url: The SOURCE URL from a Context7 entry

        Returns:
            Tuple of (directory_path, filename) for file organization

        Examples:
            https://neon.com/docs/data-api/get-started → ('data-api', 'get-started')
            https://neon.com/docs/guides/neon-auth-api → ('guides', 'neon-auth-api')
        """
        full_path = self.extract_path(source_url)
        if '/' in full_path:
            # Split into directory and filename
            parts = full_path.split('/')
            directory = '/'.join(parts[:-1])
            filename = parts[-1]
            return (directory, filename)
        else:
            # Single level - treat as both directory and filename
            return ('', full_path)

    def _is_valid_url(self, url: str) -> bool:
        """
        Validate if the URL is properly formatted.

        Args:
            url: URL string to validate

        Returns:
            True if URL is valid, False otherwise
        """
        try:
            result = urlparse(url)
            # Only allow http and https schemes for documentation URLs
            return result.scheme in ('http', 'https') and bool(result.netloc)
        except Exception:
            return False

    def _extract_docs_path(self, url_path: str) -> Optional[str]:
        """
        Extract the path after documentation directory patterns.

        Args:
            url_path: Path component of the URL

        Returns:
            Path after docs directory or None if not found
        """
        for pattern in self.DOCS_PATTERNS:
            match = re.search(pattern, url_path, re.IGNORECASE)
            if match:
                # Get everything after the docs pattern
                start_index = match.end()
                remaining_path = url_path[start_index:].lstrip('/')
                return remaining_path  # Return empty string if nothing after pattern

        return None

    def _format_path(self, path: str) -> str:
        """
        Format and clean the extracted path.

        Args:
            path: Raw extracted path

        Returns:
            Cleaned and formatted path
        """
        if not path:
            return ''

        # Remove leading/trailing slashes and normalize
        path = path.strip('/')

        # Split, clean, and rejoin path segments
        segments = []
        for segment in path.split('/'):
            segment = segment.strip()
            if segment:
                # Clean segment: remove special chars, replace spaces with hyphens
                cleaned = re.sub(r'[^\w\-.]', '-', segment)
                cleaned = re.sub(r'-+', '-', cleaned)  # Multiple hyphens to single
                cleaned = cleaned.strip('-')  # Remove leading/trailing hyphens
                if cleaned:
                    segments.append(cleaned)

        return '/'.join(segments)

    def get_numbered_filename(self, source_url: str, number: int) -> str:
        """
        Generate a numbered filename from SOURCE URL.

        Args:
            source_url: The SOURCE URL from a Context7 entry
            number: Sequential number for the file

        Returns:
            Formatted filename with or without number prefix based on no_prefix flag

        Examples:
            URL with number 1 (no_prefix=False) → '001-get-started.md'
            URL with number 1 (no_prefix=True) → 'get-started.md'
        """
        _, filename = self.extract_file_path(source_url)
        if not filename:
            filename = 'untitled'

        if self.no_prefix:
            # Return filename without number prefix
            return f"{filename}.md"
        else:
            # Format number with zero padding (3 digits)
            padded_number = f"{number:03d}"
            return f"{padded_number}-{filename}.md"


def extract_directory_path(source_url: str) -> str:
    """
    Convenience function to extract directory path from SOURCE URL.

    Args:
        source_url: SOURCE URL from Context7 entry

    Returns:
        Directory path for file organization

    Raises:
        URLMapperError: If URL mapping fails
    """
    mapper = URLMapper()
    return mapper.extract_path(source_url)


def extract_main_directory(source_url: str) -> str:
    """
    Convenience function to extract main directory from SOURCE URL.

    Args:
        source_url: SOURCE URL from Context7 entry

    Returns:
        Main directory name
    """
    mapper = URLMapper()
    return mapper.extract_main_directory(source_url)


# TODO: Add support for custom URL patterns beyond standard docs directories
# TODO: Add configuration for custom path transformation rules
# FUTURE: Consider adding support for subdomain-based organization
# FUTURE: Add caching for frequently processed URLs
