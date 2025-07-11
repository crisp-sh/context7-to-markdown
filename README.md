# Context7 to Markdown Converter

A powerful CLI tool that converts Context7 format files to organized markdown documentation with automatic directory structure and table of contents generation.

## ✨ Features

- **Convert Context7 to Markdown**: Transform Context7 format files into clean, organized markdown documentation
- **Smart Organization**: Automatically organizes files into logical directory structures based on source URLs
- **Table of Contents**: Generates comprehensive index files for easy navigation
- **URL Mapping**: Intelligently maps source URLs to appropriate file paths and names
- **Error Handling**: Robust error handling with detailed feedback for troubleshooting
- **Cross-Platform**: Works on Windows, macOS, and Linux

## 🚀 Installation

### Using pip

```bash
pip install c2md
```

### Using uv (recommended for faster installation)

```bash
uv install c2md
```

### Development Installation

```bash
# Clone the repository
git clone https://github.com/crisp-sh/context7-to-markdown.git
cd context7-to-markdown

# Install in development mode
pip install -e .
```

## 📋 Requirements

- Python 3.8 or higher
- No external dependencies required

## 🛠️ Usage

After installation, use the `c2md` command to convert your Context7 files:

### Basic Usage

```bash
c2md input.context7
```

### Advanced Usage

```bash
# Specify output directory
c2md input.context7 -d /path/to/output

# Disable table of contents generation
c2md input.context7 --no-tree

# Full example with all options
c2md my-documentation.context7 -d ./docs --tree
```

### Command Line Options

- `input_file`: Path to the Context7 format input file (required)
- `-d, --directory`: Output directory (default: current directory)
- `-T, --tree`: Generate table of contents index (default: enabled)
- `--no-tree`: Disable table of contents generation
- `-h, --help`: Show help message and exit

## 📁 Output Structure

The tool creates an organized directory structure:

```
output/
├── index.md                    # Table of contents (if enabled)
├── domain1.com/
│   ├── section1/
│   │   ├── page1.md
│   │   └── page2.md
│   └── section2/
│       └── page3.md
└── domain2.com/
    └── docs/
        └── guide.md
```

## 🎯 Context7 Format

The tool processes Context7 format files, which should contain entries with:
- **SOURCE**: URL or source identifier
- **CONTENT**: The actual content to be converted
- **TITLE**: Optional title for the content

Example Context7 format:
```
SOURCE: https://example.com/docs/getting-started
TITLE: Getting Started Guide
CONTENT: # Getting Started
This is the main content...

---

SOURCE: https://example.com/api/reference
TITLE: API Reference
CONTENT: # API Reference
API documentation content...
```

## 🔧 Examples

### Convert a simple Context7 file

```bash
c2md documentation.context7
```

This will:
1. Parse the Context7 file
2. Create an `output/` directory
3. Generate organized markdown files
4. Create an `index.md` table of contents

### Convert with custom output directory

```bash
c2md docs.context7 -d ./website/content
```

### Convert without table of contents

```bash
c2md docs.context7 --no-tree
```

## 🏗️ Architecture

The tool consists of several modular components:

- **Parser**: Processes Context7 format files
- **URL Mapper**: Maps source URLs to file paths
- **File Organizer**: Organizes content into directory structures
- **Markdown Writer**: Generates clean markdown files
- **Index Generator**: Creates table of contents

## 🧪 Testing

Run the test suite using Hatch:

```bash
# Run tests
hatch run test

# Run tests with coverage
hatch run test-cov

# Run specific test file
hatch run test tests/test_specific.py
```

### Legacy Testing

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
python -m unittest discover tests

# Run tests with coverage
python -m unittest discover tests
```

## 🔄 Releasing

This project uses automated versioned releases with [Hatch](https://hatch.pypa.io/) for version management.

### Quick Release

```bash
# Create a patch release (0.1.0 → 0.1.1)
hatch run release patch

# Create a minor release (0.1.0 → 0.2.0)
hatch run release minor

# Create a major release (0.1.0 → 1.0.0)
hatch run release major
```

### Release Process

The release script automatically:
1. Checks that your working directory is clean
2. Runs the test suite
3. Updates the version in [`c2md/__init__.py`](c2md/__init__.py:5)
4. Creates a signed Git commit
5. Creates a signed Git tag
6. Pushes to GitHub, triggering the automated release workflow

### Custom Release Message

```bash
hatch run release patch -m "Fix critical bug in URL parsing"
```

### Dry Run

```bash
hatch run release patch --dry-run
```

### Requirements

- Git signing must be configured (see [docs/RELEASE_SETUP.md](docs/RELEASE_SETUP.md))
- Tests must pass
- Working directory must be clean

For detailed setup instructions, see [docs/RELEASE_SETUP.md](docs/RELEASE_SETUP.md).

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### Development Setup

```bash
# Clone the repository
git clone https://github.com/crisp-sh/context7-to-markdown.git
cd context7-to-markdown

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e .

# Install development dependencies
pip install -e .
```

### Running Tests

```bash
# Run all tests with Hatch
hatch run test

# Run specific test file
hatch run test tests/test_specific.py

# Run tests with coverage
hatch run test-cov
```

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🐛 Bug Reports

If you encounter any issues, please report them on the [GitHub Issues](https://github.com/crisp-sh/context7-to-markdown/issues) page.

## 📚 Documentation

For more detailed documentation, visit our [documentation site](https://github.com/crisp-sh/context7-to-markdown/docs).

## 🔄 Changelog

### v0.1.0
- Initial release
- Basic Context7 to Markdown conversion
- Directory organization based on source URLs
- Table of contents generation
- CLI interface with `c2md` command

---

Made with ❤️ by [crisp.sh](https://crisp.sh)