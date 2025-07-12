import argparse
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

try:
    import requests
except ImportError:
    requests = None

# Import all the processing modules
try:
    from .file_organizer import FileOrganizer, FileOrganizerError, OrganizedFile
    from .index_generator import IndexGenerator, IndexGeneratorError
    from .markdown_writer import MarkdownWriter, MarkdownWriterError
    from .parser import Context7ParseError, Context7Parser
    from .url_mapper import URLMapper, URLMapperError
except ImportError:
    # Fallback for direct execution
    from parser import Context7ParseError, Context7Parser

    from file_organizer import FileOrganizer, FileOrganizerError, OrganizedFile
    from index_generator import IndexGenerator, IndexGeneratorError
    from markdown_writer import MarkdownWriter, MarkdownWriterError
    from url_mapper import URLMapper, URLMapperError


def validate_input_file(file_path: str) -> None:
    """
    Validate that the input file exists and is readable.

    Args:
        file_path: Path to the Context7 formatted llms.txt 
        or Context7 URL (required)

    Raises:
        FileNotFoundError: If file doesn't exist
        PermissionError: If file is not readable
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Input file not found: {file_path}")

    if not os.path.isfile(file_path):
        raise ValueError(f"Input path is not a file: {file_path}")

    if not os.access(file_path, os.R_OK):
        raise PermissionError(f"Input file is not readable: {file_path}")


def is_url(input_string: str) -> bool:
    """
    Check if the input string is a URL.
    
    Args:
        input_string: The input string to check
        
    Returns:
        True if the input is a URL, False otherwise
    """
    try:
        result = urlparse(input_string)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def validate_and_transform_context7_url(url: str) -> Tuple[bool, str]:
    """
    Validate and transform context7.com URLs to the correct format.
    
    Valid patterns:
    - https://context7.com/{org}/{project}/llms.txt
    - https://context7.com/{org}/{project} (will be transformed)
    
    Invalid patterns:
    - https://context7.com/{project}/llms.txt (missing org)
    
    Args:
        url: URL to validate and transform
        
    Returns:
        Tuple of (is_valid, transformed_url)
    """
    try:
        parsed = urlparse(url)
        
        # Check domain
        if parsed.netloc != 'context7.com':
            return False, ""
        
        # Clean path and split into segments
        path = parsed.path.strip('/')
        segments = [s for s in path.split('/') if s]
        
        # Need at least 2 segments: org/user and project
        if len(segments) < 2:
            return False, ""
        
        # Check if the last segment is llms.txt
        if segments[-1] == 'llms.txt':
            # If it ends with llms.txt, we need exactly 3 segments (org/project/llms.txt)
            if len(segments) != 3:
                return False, ""  # Wrong number of segments
            org, project = segments[0], segments[1]
        elif len(segments) == 2:
            # This is the short format (org/project), needs transformation
            org, project = segments[0], segments[1]
        else:
            # Invalid format - too many segments without llms.txt
            return False, ""
        
        # Build the correct URL
        correct_path = f"/{org}/{project}/llms.txt"
        
        # Build URL with updated path
        transformed = urlunparse((
            parsed.scheme,
            parsed.netloc,
            correct_path,
            parsed.params,
            parsed.query,
            parsed.fragment
        ))
        
        # Ensure tokens parameter
        transformed = ensure_tokens_parameter(transformed)
        
        return True, transformed
    except Exception:
        return False, ""


def ensure_tokens_parameter(url: str) -> str:
    """
    Ensure the URL has a tokens parameter, adding default if missing.
    
    Args:
        url: The input URL
        
    Returns:
        URL with tokens parameter
    """
    parsed = urlparse(url)
    query_params = parse_qs(parsed.query)
    
    # If tokens parameter doesn't exist, add default
    if 'tokens' not in query_params:
        query_params['tokens'] = ['999999999']
    
    # Rebuild the URL with updated query
    new_query = urlencode(query_params, doseq=True)
    new_parsed = parsed._replace(query=new_query)
    return urlunparse(new_parsed)


def download_context7_content(url: str) -> str:
    """
    Download content from a context7.com URL.
    
    Args:
        url: The context7.com URL to download from
        
    Returns:
        The downloaded content
        
    Raises:
        RuntimeError: If download fails
    """
    if requests is None:
        raise RuntimeError("Optional dependency 'requests' is not installed.")
    try:
        # Add tokens parameter if missing
        url_with_tokens = ensure_tokens_parameter(url)
        
        print(f"🌐 Downloading from: {url_with_tokens}")
        
        # Set a reasonable timeout and headers
        headers = {
            'User-Agent': 'c2md-cli/1.0'
        }
        
        response = requests.get(url_with_tokens, headers=headers, timeout=30)
        response.raise_for_status()
        
        print(f"✅ Successfully downloaded {len(response.content)} bytes")
        return response.text
        
    except requests.exceptions.HTTPError as e:
        raise RuntimeError(f"HTTP error downloading content: {e}")
    except requests.exceptions.ConnectionError as e:
        raise RuntimeError(f"Connection error: {e}")
    except requests.exceptions.Timeout as e:
        raise RuntimeError(f"Request timed out: {e}")
    except Exception as e:
        raise RuntimeError(f"Failed to download content: {e}")


def ensure_output_directory(output_dir: str) -> None:
    """
    Create output directory if it doesn't exist.

    Args:
        output_dir: Path to the output directory

    Raises:
        PermissionError: If directory cannot be created
    """
    try:
        Path(output_dir).mkdir(parents=True, exist_ok=True)
    except PermissionError:
        raise PermissionError(f"Cannot create output directory: {output_dir}")
    except Exception as e:
        raise RuntimeError(f"Failed to create output directory '{output_dir}': {str(e)}")


def flatten_organized_structure(organized_structure: Dict[str, List[OrganizedFile]]) -> List[OrganizedFile]:
    """
    Flatten the organized structure into a single list of OrganizedFile objects.

    Args:
        organized_structure: Dictionary mapping directory paths to lists of OrganizedFile objects

    Returns:
        Flattened list of all OrganizedFile objects
    """
    flattened = []
    for directory_files in organized_structure.values():
        flattened.extend(directory_files)
    return flattened


def print_processing_summary(entries_count: int, files_written: List[str],
                           index_path: Optional[str] = None) -> None:
    """
    Print a summary of the processing results.

    Args:
        entries_count: Number of entries processed
        files_written: List of written file paths
        index_path: Path to generated index file (if any)
    """
    print("\n✅ Processing complete!")
    print(f"📋 Processed {entries_count} Context7 entries")
    print(f"📄 Generated {len(files_written)} markdown files")

    if files_written:
        print("📁 Files written to:")
        for file_path in sorted(files_written):
            print(f"   • {file_path}")

    if index_path:
        print(f"📑 Index generated: {index_path}")


def main():
    """Main entry point for the Context7-to-Markdown CLI tool."""
    parser = argparse.ArgumentParser(
        description="Convert Context7 format to organized markdown documentation"
    )
    parser.add_argument("input", help="Context7 formatted llms.txt or Context7 URL (required)")
    parser.add_argument(
        "-d", "--directory", default=None, help="Output directory (default: ./output)"
    )
    parser.add_argument(
        "-nt", "--no-toc", action="store_false", dest="tree", default=True,
        help="Disable table of contents generation"
    )
    parser.add_argument(
        "-np", "--no-prefix", action="store_true", default=False,
        help="Generate filenames without number prefixes"
    )
    args = parser.parse_args()

    # Determine output directory
    if args.directory is not None:
        # If --no-prefix or --no-toc flags are specified, treat provided directory as base and create 'output' subdirectory.
        if args.no_prefix or not args.tree:
            output_directory = os.path.join(args.directory, "output")
        else:
            output_directory = args.directory
    else:
        output_directory = os.path.join(os.getcwd(), "output")

    try:
        # Step 1: Check if input is a URL or file
        if is_url(args.input):
            # Handle URL input
            print(f"🔍 Validating URL: {args.input}")
            
            # Validate and transform the URL
            is_valid, transformed_url = validate_and_transform_context7_url(args.input)
            if not is_valid:
                raise ValueError(
                    "Invalid URL. Only context7.com URLs in the format:\n"
                    "  - https://context7.com/{org}/{project}/llms.txt\n"
                    "  - https://context7.com/{org}/{project}\n"
                    "are supported.\n"
                    f"Example: https://context7.com/vercel/next.js"
                )
            
            # Download content with transformed URL
            content = download_context7_content(transformed_url)
            
            # Step 2: Ensure output directory exists
            print(f"📁 Preparing output directory: {output_directory}")
            ensure_output_directory(output_directory)
            
            # Step 3: Parse Context7 content
            print("📖 Parsing Context7 content...")
            parser_instance = Context7Parser()
            entries = parser_instance.parse_content(content)
        else:
            # Handle file input (existing logic)
            print(f"🔍 Validating input file: {args.input}")
            validate_input_file(args.input)
            
            # Step 2: Ensure output directory exists
            print(f"📁 Preparing output directory: {output_directory}")
            ensure_output_directory(output_directory)
            
            # Step 3: Parse Context7 file
            print("📖 Parsing Context7 file...")
            parser_instance = Context7Parser()
            entries = parser_instance.parse_file(args.input)

        if not entries:
            print("⚠️  No entries found in the input file.")
            return

        print(f"✅ Found {len(entries)} entries")

        # Step 4: Organize entries into directory structure
        print("🗂️  Organizing entries into directory structure...")
        url_mapper = URLMapper(no_prefix=args.no_prefix)
        file_organizer = FileOrganizer(url_mapper, no_prefix=args.no_prefix)
        organized_structure = file_organizer.organize_entries(entries)

        # Flatten the organized structure
        organized_files = flatten_organized_structure(organized_structure)
        print(f"✅ Organized {len(organized_files)} files across {len(organized_structure)} directories")

        # Step 5: Write markdown files
        print("✍️  Writing markdown files...")
        markdown_writer = MarkdownWriter(output_directory)
        written_files = markdown_writer.write_files(organized_files)

        # Step 6: Generate index if requested
        index_path = None
        if args.tree:
            print("📑 Generating table of contents index...")
            index_generator = IndexGenerator(output_directory, no_prefix=args.no_prefix)

            # Convert written files to relative paths for index
            relative_paths = []
            for file_path in written_files:
                rel_path = os.path.relpath(file_path, output_directory)
                relative_paths.append(rel_path)

            index_path = index_generator.generate_index(relative_paths)

        # Step 7: Print summary
        print_processing_summary(len(entries), written_files, index_path)

    except Context7ParseError as e:
        print(f"❌ Parsing error: {e}", file=sys.stderr)
        print("💡 Please check that your input file is in valid Context7 format.", file=sys.stderr)
        sys.exit(1)

    except FileOrganizerError as e:
        print(f"❌ File organization error: {e}", file=sys.stderr)
        print("💡 Please check that your Context7 entries have valid SOURCE URLs.", file=sys.stderr)
        sys.exit(1)

    except MarkdownWriterError as e:
        print(f"❌ Markdown writing error: {e}", file=sys.stderr)
        print("💡 Please check output directory permissions.", file=sys.stderr)
        sys.exit(1)

    except IndexGeneratorError as e:
        print(f"❌ Index generation error: {e}", file=sys.stderr)
        print("💡 Index generation failed, but markdown files were created successfully.", file=sys.stderr)
        # Don't exit here, as the main processing succeeded

    except URLMapperError as e:
        print(f"❌ URL mapping error: {e}", file=sys.stderr)
        print("💡 Please check that your Context7 entries have valid SOURCE URLs.", file=sys.stderr)
        sys.exit(1)

    except FileNotFoundError as e:
        print(f"❌ File not found: {e}", file=sys.stderr)
        print("💡 Please check that the input file path is correct.", file=sys.stderr)
        sys.exit(1)

    except PermissionError as e:
        print(f"❌ Permission error: {e}", file=sys.stderr)
        print("💡 Please check file and directory permissions.", file=sys.stderr)
        sys.exit(1)

    except ValueError as e:
        print(f"❌ Invalid input: {e}", file=sys.stderr)
        sys.exit(1)

    except Exception as e:
        print(f"❌ Unexpected error: {e}", file=sys.stderr)
        print("💡 Please check your input file and try again.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
