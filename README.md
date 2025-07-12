# Context7 to Markdown (`c2md`)

A blazing fast tool that converts Context7 to organized markdown documentation with automatic directory structure, multi-language parsing support, and table of contents generation. Supports both local files and direct URLs from Context7.com.

Install with pip
```bash
pip install c2md
```
Install with uv
```bash
uv pip install c2md
```
*or*
```bash
uvx c2md https://context7.com/org/project
```

## Why `c2md`? 🤔

MCP servers are fairly new and are quite rudimentary. They introduce latency, increase prompt size, consume tokens on every request, and, in the case of Context7, require network calls for each library lookup. Additionally, Context7's MCP server uses natural language search that can miss relevant sections or return results you don't even need.

With `c2md`, you convert a library <ins>once</ins> per project and reference it locally. Instead of making MCP calls that cost 4,000-20,000 tokens per search, you attach the generated 000-index.md (typically costs less than Context7's `resolve-library-id` alone) directly to your agent. The agent gets complete context without network delays or token waste on repeated or bad searches.

This tool excels when dealing with large libraries like Neon, which has around 240 sections (~520,000 tokens). The locally generated index provides instant, inexpensive library context to any section while consuming ~50% fewer tokens than equivalent MCP operations. You can even pass the table of contents or specific sections from the library via a rule in your favorite AI IDE.

If that didn't sell you, `c2md`:

- **⚓ Converts Context7 to local markdown**
- **🧠 Logically organizes the library into sections with sequential file naming**
- **🗨️ Consolidates multi-language sections into a single document**
- **📜 Generates Table of contents = easy context for your agent**
- **🗺️ Maps source URLs to appropriate file paths and names** 
- **🏎️ Fast as hell**

## Installation

#### Using pip

```bash
pip install c2md
```

#### Using uv

```bash
uv pip install c2md
```
*or*
```bash
uvx c2md https://context7.com/org/project
```

## 📋 Requirements

- Python 3.8 or higher
- No external dependencies required unless developing

## 🛠️ Usage

After installation, use the `c2md` command:

### Basic Usage

From local file - output defaults to ./output/
```bash
c2md /path/to/llms.txt
```
From Context7 standard URL
```bash
c2md https://context7.com/org/project
```
From Context7 raw URL with tokens query
```bash
c2md https://context7.com/org/project/llms.txt?tokens=173800
```

### Advanced Usage

```bash
# Specify output directory, 001-index.md (ToC) generated in output root
c2md /path/to/llms.txt -d /path/to/output

# From Context7 raw URL with output directory
c2md https://context7.com/org/project/llms.txt -d .docs/neon

# Disable ToC generation
c2md /path/to/llms.txt -nt

# Full example with all options, no table of contents
c2md https://context7.com/context7/supabase/llms.txt?tokens=1000000 -d /path/to/output -nt 
```

### Command Line Options

- `input_file|input_url`: Context7 formatted llms.txt or Context7 URL (required)
- `-d, --directory`: Output directory (default: current directory)
- `-nt, --no-toc`: Disable table of contents generation in documentation root
- `-np, --no-prefix`: Disable "000-" prefix file naming
- `-h, --help`: Show help message and exit

## Bug Reports

If you encounter any issues, please report them on the [GitHub Issues](https://github.com/crisp-sh/context7-to-markdown/issues) page.

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
