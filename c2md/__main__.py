import argparse
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional

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
        file_path: Path to the input file

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
    parser.add_argument("input_file", help="Context7 generated llms.txt file")
    parser.add_argument(
        "-d", "--directory", default=None, help="Output directory (default: ./output)"
    )
    parser.add_argument(
        "-T", "--tree", action="store_true", default=True, help="Generate table of contents index (default: true)"
    )
    parser.add_argument(
        "--no-tree", action="store_false", dest="tree", help="Disable table of contents generation"
    )
    args = parser.parse_args()

    # Determine output directory
    # Always create an "output" subdirectory in the specified or current directory
    if args.directory is not None:
        output_directory = args.directory
    else:
        output_directory = os.path.join(os.getcwd(), "output")

    try:
        # Step 1: Validate input file
        print(f"🔍 Validating input file: {args.input_file}")
        validate_input_file(args.input_file)

        # Step 2: Ensure output directory exists
        print(f"📁 Preparing output directory: {output_directory}")
        ensure_output_directory(output_directory)

        # Step 3: Parse Context7 file
        print("📖 Parsing Context7 file...")
        parser_instance = Context7Parser()
        entries = parser_instance.parse_file(args.input_file)

        if not entries:
            print("⚠️  No entries found in the input file.")
            return

        print(f"✅ Found {len(entries)} entries")

        # Step 4: Organize entries into directory structure
        print("🗂️  Organizing entries into directory structure...")
        url_mapper = URLMapper()
        file_organizer = FileOrganizer(url_mapper)
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
            index_generator = IndexGenerator(output_directory)

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
