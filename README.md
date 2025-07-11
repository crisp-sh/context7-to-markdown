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
pip install context7-to-markdown
```

### Using uv (recommended for faster installation)

```bash
uv install context7-to-markdown
```

### Development Installation

```bash
# Clone the repository
git clone https://github.com/context7/context7-to-markdown.git
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

Run the test suite:

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run tests with coverage
pytest --cov=context7_to_markdown
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### Development Setup

```bash
# Clone the repository
git clone https://github.com/context7/context7-to-markdown.git
cd context7-to-markdown

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e .

# Install development dependencies
pip install pytest pytest-cov
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=context7_to_markdown

# Run specific test file
pytest tests/test_parser.py
```

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🐛 Bug Reports

If you encounter any issues, please report them on the [GitHub Issues](https://github.com/context7/context7-to-markdown/issues) page.

## 📚 Documentation

For more detailed documentation, visit our [documentation site](https://github.com/context7/context7-to-markdown/docs).

## 🔄 Changelog

### v0.1.0
- Initial release
- Basic Context7 to Markdown conversion
- Directory organization based on source URLs
- Table of contents generation
- CLI interface with `c2md` command

---

Made with ❤️ by the Context7 team