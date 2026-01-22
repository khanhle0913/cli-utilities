# codesynth

Synthesize codebase into LLM-friendly markdown.

## Quick Start

```bash
# Interactive mode (arrow key navigation)
codesynth

# Scan directory
codesynth .
codesynth ./my-project

# Specific files
codesynth -f src/main.py src/utils.py src/

# With directory tree
codesynth . -t

# Reverse markdown into source files
codesynth --reverse codesynth.md --output-dir ./restored
```

## Usage Patterns

### Scan Directory

```bash
codesynth <directory> [options]
```

Auto-detects common source directories (`src`, `lib`, `app`, etc.) when scanning `.`

### Select Files

```bash
codesynth -f <files...> [options]
```

Use `-t` to include full directory structure for context.

### Interactive Mode

```bash
codesynth
```

Arrow key navigation to configure:

- Action (scan/files)
- Directory selection
- Options (tree, sizes, etc.)
- Extension filters
- Output destination

## Options Reference

### Output

| Option     | Short | Description                         |
| ---------- | ----- | ----------------------------------- |
| `--output` | `-o`  | Output file (default: codesynth.md) |
| `--stdout` |       | Output to stdout                    |
| `--clipboard` |    | Copy output to clipboard            |
| `--quiet`  | `-q`  | Suppress progress messages          |
| `--clear`  | `-c`  | Delete output file and exit         |
| `--tree`   | `-t`  | Include directory tree              |
| `--size`   | `-s`  | Show file sizes in output           |

### Selection

| Option           | Short | Description                          |
| ---------------- | ----- | ------------------------------------ |
| `--files`        | `-f`  | Include specific files or directories |
| `--extensions`   |       | Filter by file extensions            |
| `--exclude`      | `-e`  | Glob patterns to exclude             |
| `--max-depth`    |       | Maximum directory depth              |
| `--ignore-file`  | `-i`  | Custom ignore file                   |
| `--no-gitignore` |       | Ignore .gitignore patterns           |
| `--no-detect`    |       | Disable auto-detect for `.`          |

### Content

| Option             | Description                           |
| ------------------ | ------------------------------------- |
| `--max-size`       | Maximum file size (e.g., 100KB, 1MB)  |
| `--include-binary` | Include binary files in output        |

### Analysis

| Option         | Description                     |
| -------------- | ------------------------------- |
| `--list-files` | List files only, don't generate |
| `--stats-only` | Show statistics only            |

### Reverse

| Option          | Description                                |
| --------------- | ------------------------------------------ |
| `--reverse`     | Reverse codesynth markdown into source     |
| `--output-dir`  | Output directory for `--reverse`           |

## Best Practices

### 1. Start with Analysis

```bash
codesynth --stats-only     # Check file count and sizes
codesynth --list-files     # Review file list
```

### 2. Filter by Extension

```bash
codesynth --extensions py            # Python only
codesynth --extensions js ts tsx     # JavaScript/TypeScript
```

### 3. Exclude Tests and Generated Files

```bash
codesynth -e "tests/*" "*_test.py" "__pycache__/*"
```

### 4. Limit File Size

```bash
codesynth --max-size 100KB  # Skip large files
```

### 5. Include Context

```bash
codesynth -t                # Add directory structure
```

### 6. Copy to Clipboard

```bash
# macOS
codesynth --stdout | pbcopy

# Linux
codesynth --stdout | xclip -selection clipboard
```

## Examples

### Python Backend

```bash
codesynth --extensions py -e "tests/*" "migrations/*" -o backend.md
```

### React Frontend

```bash
codesynth --extensions tsx ts css -e "node_modules/*" --max-size 50KB
```

### Full Project with Tree

```bash
codesynth . -ts -o project.md
```

### Specific Core Files

```bash
codesynth -f src/main.py src/config.py src/core/*.py src/ -t
```

### Quick Export for LLM

```bash
codesynth --extensions py -t --stdout | pbcopy
```

### Restore from Markdown

```bash
codesynth --reverse codesynth.md --output-dir ./restored-project
```

## Output Format

Generated markdown includes:

1. **Header** - Root directory, total files
2. **Directory Tree** (optional) - Visual structure
3. **File Contents** - Each file with:
   - Path
   - Size (optional)
   - Syntax-highlighted code block

### Dynamic Backtick Escaping

Files containing triple backticks are automatically wrapped with additional backticks to prevent markdown conflicts.

## Default Ignores

Always ignored:

- `.git`, `.svn`, `.hg`, `.bzr`
- `node_modules`
- `.venv`, `venv`, `__pycache__`

Additionally respects `.gitignore` patterns (unless `--no-gitignore`).

## Architecture

```
src/codesynth/
├── __init__.py      # Main entry, orchestration
├── cli.py           # Argument parsing
├── collector.py     # File collection logic
├── constants.py     # Binary signatures, extensions
├── generator.py     # Markdown generation
├── interactive.py   # Interactive mode (InquirerPy)
├── output.py        # Console output formatting
├── parser.py        # Gitignore parsing
├── reverse.py       # Reverse markdown into source files
└── utils.py         # Utility functions
```
