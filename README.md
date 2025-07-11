# Context7 to Markdown (`c2md`)

A blazing fast CLI tool that converts Context7 URLs & llms.txt files to organized markdown documentation with automatic directory structure, multi-language parsing support, and table of contents generation. Supports both local files and direct URLs from Context7.com.

Install with pip
```bash
pip install c2md
```
Install with uv
```bash
uv pip install c2md
```
```bash
uvx c2md
```
## Features

#### **⚓ Convert Context7 to Markdown**

Transform Context7 links or llms.txt files into clean, organized markdown documentation.

#### **🧠 Smart Organization**

Automatically organizes markdown files into logical directory structures based on source URLs.

#### **🗨️ Multi-Language Support**

Consolidates multi-language sections into a single document.

#### **📜 Table of Contents** 

Generates comprehensive index files to provide context to your agent.

#### **🗺️ URL Mapping** 

Intelligently maps source URLs to appropriate file paths and names

#### **❌ Error Handling**
Robust error handling with detailed feedback for troubleshooting

## Why `c2md`? 🤔

MCP is clunky, slow, adds additional prompt context, and time consuming. 

With `c2md`, you can pass a specific section of a technology's documentation to an agent. Instead of fairly unreliable natural language search with the Context7 MCP server, you can just attach the `@/path/to/000-index.md` to your agent. 

Depending on the number of locally available documentation sections/files, this can save tokens/context. For example, the Neon docs have around 240 sections (520,000 tokens), with the total 000-index.md costing around 4,000 tokens; alternatively, calls to the Context7 MCP can cost anywhere from 8,000 to 20,000 tokens.  

## Installation

#### Using pip

```bash
pip install c2md
```

#### Using uv

```bash
uv pip install c2md
```
or
```bash
uvx c2md
```

## 📋 Requirements

- Python 3.8 or higher
- No external dependencies required unless developing

## 🛠️ Usage

After installation, use the `c2md` command:

### Basic Usage

```bash
# From local file - output defaults to ./output/
c2md /path/to/llms.txt

# From Context7 URL (must include tokens parameter)
c2md https://context7.com/context7/neon/llms.txt?tokens=519821
```

### Advanced Usage

```bash
# Specify output directory, 001-index.md (ToC) generated in output root
c2md /path/to/llms.txt -d /path/to/output

# From Context7 URL with output directory
c2md https://context7.com/context7/neon/llms.txt?tokens=519821 -d .docs/neon

# Disable ToC generation
c2md /path/to/llms.txt --no-tree

# Full example with all options, no ToC/tree
c2md https://context7.com/context7/supabase/llms.txt?tokens=1000000 -d /path/to/output --no-tree
```

### Command Line Options

- `input_file`: Path to the Context7 format input file or Context7 URL (required)
- `-d, --directory`: Output directory (default: current directory)
- `-T, --tree`: Generate table of contents index (default: enabled)
- `--no-tree`: Disable table of contents generation
- `-h, --help`: Show help message and exit

<details>
    <summary>
    <strong>Developing locally & contributing</strong>
    </summary>

### Contributing 🤝

Contributions are welcome! Please feel free to submit a PR if you would like to contribute or have an issue.

### Development Installation

```bash
# Clone the repository
git clone https://github.com/crisp-sh/context7-to-markdown.git
cd context7-to-markdown

# Install in development mode
pip install -e .
```

### Output Structure

The tool creates an organized directory structure:

```
output/
├── 001-index.md                    # Table of contents (if enabled)
├── domain1.com/
│   ├── section1/
│   │   ├── 001-page1.md
│   │   └── 002-page2.md
│   └── section2/
│       └── 001-page3.md
└── domain2.com/
    └── docs/
        └── 001-guide.md
```

### Context7 Format

The tool processes Context7 format files, which should contain entries with:
- **SOURCE**: URL or source identifier
- **CONTENT**: The actual content to be converted
- **TITLE**: Optional title for the content
- **LANGUAGE**: Denotes a multi-language document

### Architecture

The tool consists of several modular components:

- **Parser**: Processes Context7 format files
- **URL Mapper**: Maps source URLs to file paths
- **File Organizer**: Organizes content into directory structures
- **Markdown Writer**: Generates clean markdown files
- **Index Generator**: Creates table of contents

### Testing

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

### Releasing

This project uses automated versioned releases with [Hatch](https://hatch.pypa.io/) for version management.

#### Quick Release

```bash
# Create a patch release (0.1.0 → 0.1.1)
hatch run release patch

# Create a minor release (0.1.0 → 0.2.0)
hatch run release minor

# Create a major release (0.1.0 → 1.0.0)
hatch run release major
```

#### Development Setup

```bash
# Clone the repository
git clone https://github.com/crisp-sh/context7-to-markdown.git
cd context7-to-markdown

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install
pip install -e .
```

#### Running Tests

```bash
# Run all tests with Hatch
hatch run test

# Run specific test file
hatch run test tests/test_specific.py

# Run tests with coverage
hatch run test-cov
```
</details>

## Bug Reports

If you encounter any issues, please report them on the [GitHub Issues](https://github.com/crisp-sh/context7-to-markdown/issues) page.