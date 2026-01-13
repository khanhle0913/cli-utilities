# codesynth

Synthesize a codebase into a single, LLM-friendly markdown document.

## Basic Usage

```bash
# Auto-detect source directories (src/, lib/, app/, etc.)
codesynth

# Scan specific directory
codesynth ./my-project

# Custom output file
codesynth -o project_docs.md
```

## Auto-Detection

When run without arguments, `codesynth` automatically searches for common source directories:

```
src, lib, app, source, code, pkg, packages, modules, core, internal,
cmd, backend, frontend, server, client, api, services, components
```

If none found, it falls back to the current directory.

## Output Format

By default, output is **minimal** (no directory tree, no file sizes). Add flags to include more details:

```bash
# Include directory tree structure
codesynth --with-tree

# Show file sizes
codesynth --with-size

# Full output with both
codesynth --with-tree --with-size
```

## Filtering Files

### By Extension

```bash
# Only Python files
codesynth -e py

# Multiple extensions
codesynth -e py js ts tsx
```

### By Pattern

```bash
# Exclude test files
codesynth --exclude "*.test.py" "*.spec.ts"

# Exclude directories
codesynth --exclude "__pycache__/*" "tests/*"
```

### By Size

```bash
# Skip files larger than 100KB
codesynth --max-size 100KB

# Skip files larger than 1MB
codesynth --max-size 1MB
```

### By Depth

```bash
# Only top 2 levels
codesynth --max-depth 2
```

### Ignore .gitignore

```bash
# Include files normally ignored by .gitignore
codesynth --no-gitignore
```

Note: Default system directories (`.git`, `.venv`, `node_modules`, `__pycache__`) are always ignored.

## Output Options

### To File (default)

```bash
codesynth -o docs.md
```

### To Stdout

```bash
# Copy to clipboard (macOS)
codesynth --stdout | pbcopy

# Copy to clipboard (Linux)
codesynth --stdout | xclip -selection clipboard
```

### Quiet Mode

```bash
# Suppress progress output
codesynth -q -o output.md
```

## Analysis Mode

### List Files Only

```bash
codesynth --list-files
```

Output:

```
Files to include (3)
├── src/main.py (2.5 KB)
├── src/utils.py (1.2 KB)
└── src/config.py (800 B)
```

### Statistics Only

```bash
codesynth --stats-only
```

Output:

```
   Codebase Statistics
╭──────────────┬─────────╮
│ Total files  │ 15      │
│ Binary files │ 2       │
│ Text files   │ 13      │
│ Total size   │ 45.2 KB │
╰──────────────┴─────────╯
```

## Binary Files

```bash
# Include binary files in output
codesynth --include-binary
```

By default, binary files are detected and skipped.

## Default Ignores

The following directories are always ignored:

- `.git`, `.svn`, `.hg`, `.bzr` (version control)
- `node_modules` (Node.js)
- `.venv`, `venv` (Python virtual environments)
- `__pycache__` (Python cache)

Additionally, patterns from `.gitignore` are respected (unless `--no-gitignore`).

## Custom Ignore File

```bash
# Use custom ignore file
codesynth -i .customignore
```

## Command Reference

### Output Options

| Option          | Short | Description                           |
| --------------- | ----- | ------------------------------------- |
| `--output FILE` | `-o`  | Output file (default: source_code.md) |
| `--stdout`      |       | Output to stdout                      |
| `--quiet`       | `-q`  | Suppress progress messages            |
| `--with-tree`   |       | Include directory tree in output      |
| `--with-size`   |       | Show file sizes in output             |

### Filtering Options

| Option                 | Short | Description                |
| ---------------------- | ----- | -------------------------- |
| `--extensions EXT...`  | `-e`  | Filter by file extensions  |
| `--exclude PATTERN...` |       | Glob patterns to exclude   |
| `--max-depth N`        |       | Maximum directory depth    |
| `--no-gitignore`       |       | Ignore .gitignore patterns |
| `--ignore-file FILE`   | `-i`  | Custom ignore file         |

### Content Options

| Option             | Description                          |
| ------------------ | ------------------------------------ |
| `--max-size SIZE`  | Maximum file size (e.g., 100KB, 1MB) |
| `--include-binary` | Include binary files                 |

### Information Options

| Option         | Description                     |
| -------------- | ------------------------------- |
| `--list-files` | List files only, don't generate |
| `--stats-only` | Show statistics only            |

## Examples

```bash
# Typical Python project
codesynth -e py --exclude "tests/*" -o code.md

# Frontend project
codesynth -e js ts tsx css --max-size 50KB

# Include everything (ignore .gitignore)
codesynth --no-gitignore -o full_code.md

# Full output with tree and sizes
codesynth --with-tree --with-size -o detailed.md

# Quick analysis
codesynth --stats-only
```
