import os
import pathlib
import fnmatch
import argparse
from typing import List, Set, Tuple, Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.tree import Tree
from rich import box

# Rich console for pretty output
console = Console()


# Binary file detection via magic bytes (first bytes of common binary formats)
BINARY_SIGNATURES: List[bytes] = [
    b"\x89PNG",  # PNG
    b"\xff\xd8\xff",  # JPEG
    b"GIF87a",  # GIF
    b"GIF89a",  # GIF
    b"PK\x03\x04",  # ZIP, DOCX, XLSX, JAR, APK
    b"PK\x05\x06",  # ZIP empty
    b"\x50\x4b\x07\x08",  # ZIP spanned
    b"%PDF",  # PDF
    b"\x7fELF",  # ELF executable
    b"MZ",  # Windows executable
    b"\xca\xfe\xba\xbe",  # Java class / Mach-O fat binary
    b"\xfe\xed\xfa\xce",  # Mach-O 32-bit
    b"\xfe\xed\xfa\xcf",  # Mach-O 64-bit
    b"\xcf\xfa\xed\xfe",  # Mach-O 64-bit reversed
    b"\x1f\x8b",  # GZIP
    b"BZ",  # BZIP2
    b"\xfd7zXZ",  # XZ
    b"Rar!\x1a\x07",  # RAR
    b"\x00\x00\x00\x1c\x66\x74\x79\x70",  # MP4/M4A
    b"\x00\x00\x00\x20\x66\x74\x79\x70",  # MP4
    b"ID3",  # MP3 with ID3
    b"\xff\xfb",  # MP3
    b"\xff\xfa",  # MP3
    b"OggS",  # OGG
    b"RIFF",  # WAV, AVI
    b"fLaC",  # FLAC
    b"\x00\x00\x01\x00",  # ICO
    b"OTTO",  # OpenType font
    b"\x00\x01\x00\x00",  # TrueType font
    b"wOFF",  # WOFF
    b"wOF2",  # WOFF2
    b"\x1a\x45\xdf\xa3",  # WebM/MKV
    b"SQLite format 3",  # SQLite
    b"\x00asm",  # WebAssembly
]

# Known binary file extensions (lowercase, without dot)
BINARY_EXTENSIONS: Set[str] = {
    # Images
    "png",
    "jpg",
    "jpeg",
    "gif",
    "bmp",
    "ico",
    "webp",
    "svg",
    "tiff",
    "tif",
    "psd",
    "raw",
    "heic",
    "heif",
    "avif",
    # Audio
    "mp3",
    "wav",
    "flac",
    "aac",
    "ogg",
    "wma",
    "m4a",
    "opus",
    # Video
    "mp4",
    "avi",
    "mkv",
    "mov",
    "wmv",
    "flv",
    "webm",
    "m4v",
    "mpeg",
    "mpg",
    # Archives
    "zip",
    "tar",
    "gz",
    "rar",
    "7z",
    "bz2",
    "xz",
    "iso",
    "dmg",
    # Executables & Libraries
    "exe",
    "dll",
    "so",
    "dylib",
    "bin",
    "out",
    "app",
    "msi",
    # Documents (binary)
    "pdf",
    "doc",
    "docx",
    "xls",
    "xlsx",
    "ppt",
    "pptx",
    "odt",
    "ods",
    "odp",
    # Fonts
    "ttf",
    "otf",
    "woff",
    "woff2",
    "eot",
    # Database
    "db",
    "sqlite",
    "sqlite3",
    "mdb",
    # Other
    "pyc",
    "pyo",
    "class",
    "jar",
    "war",
    "ear",
    "apk",
    "ipa",
    "o",
    "a",
    "lib",
    "obj",
    "wasm",
}

# Extension to language mapping for syntax highlighting
EXTENSION_LANGUAGE_MAP: dict[str, str] = {
    "py": "python",
    "js": "javascript",
    "ts": "typescript",
    "jsx": "jsx",
    "tsx": "tsx",
    "rb": "ruby",
    "rs": "rust",
    "go": "go",
    "java": "java",
    "kt": "kotlin",
    "swift": "swift",
    "c": "c",
    "cpp": "cpp",
    "cc": "cpp",
    "cxx": "cpp",
    "h": "c",
    "hpp": "cpp",
    "cs": "csharp",
    "php": "php",
    "sh": "bash",
    "bash": "bash",
    "zsh": "zsh",
    "fish": "fish",
    "ps1": "powershell",
    "sql": "sql",
    "html": "html",
    "htm": "html",
    "css": "css",
    "scss": "scss",
    "sass": "sass",
    "less": "less",
    "json": "json",
    "xml": "xml",
    "yaml": "yaml",
    "yml": "yaml",
    "toml": "toml",
    "ini": "ini",
    "cfg": "ini",
    "conf": "ini",
    "md": "markdown",
    "markdown": "markdown",
    "rst": "rst",
    "tex": "latex",
    "r": "r",
    "R": "r",
    "m": "matlab",
    "lua": "lua",
    "pl": "perl",
    "pm": "perl",
    "ex": "elixir",
    "exs": "elixir",
    "erl": "erlang",
    "hrl": "erlang",
    "clj": "clojure",
    "cljs": "clojure",
    "scala": "scala",
    "hs": "haskell",
    "ml": "ocaml",
    "fs": "fsharp",
    "vim": "vim",
    "dockerfile": "dockerfile",
    "makefile": "makefile",
    "cmake": "cmake",
    "groovy": "groovy",
    "gradle": "groovy",
    "tf": "hcl",
    "hcl": "hcl",
    "proto": "protobuf",
    "graphql": "graphql",
    "gql": "graphql",
    "vue": "vue",
    "svelte": "svelte",
}


class GitignoreParser:
    # Default directories to always ignore (not typically in .gitignore)
    DEFAULT_IGNORE_DIRS: Set[str] = {
        ".git",
        ".svn",
        ".hg",
        ".bzr",
        "__pycache__",
        "node_modules",
        ".venv",
        "venv",
        ".env",
    }

    def __init__(
        self, start_dir: str = ".", gitignore_name: str = ".gitignore"
    ):
        self.patterns: List[str] = []
        self.dir_patterns: List[str] = list(self.DEFAULT_IGNORE_DIRS)
        self.gitignore_path = None

        # Search for gitignore in current and parent directories
        current = os.path.abspath(start_dir)
        while True:
            potential_gitignore = os.path.join(current, gitignore_name)
            if os.path.exists(potential_gitignore):
                self.gitignore_path = potential_gitignore
                break

            parent = os.path.dirname(current)
            if parent == current:  # Reached root
                break
            current = parent

        if self.gitignore_path:
            with open(self.gitignore_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    # Skip empty lines and comments
                    if not line or line.startswith("#"):
                        continue

                    # Directory patterns
                    if line.endswith("/"):
                        self.dir_patterns.append(line.rstrip("/"))
                    else:
                        self.patterns.append(line)

    def should_ignore(self, path: str, is_dir: bool = False) -> bool:
        """Check if a path should be ignored based on gitignore patterns."""
        path_parts = pathlib.Path(path).parts

        # Check directory patterns
        if is_dir:
            for pattern in self.dir_patterns:
                if fnmatch.fnmatch(os.path.basename(path), pattern):
                    return True
                # Check if any parent directory matches
                for part in path_parts:
                    if fnmatch.fnmatch(part, pattern):
                        return True

        # Check file patterns
        for pattern in self.patterns:
            # Check basename
            if fnmatch.fnmatch(os.path.basename(path), pattern):
                return True
            # Check full path for patterns with /
            if "/" in pattern and fnmatch.fnmatch(path, pattern):
                return True
            # Check if any part of the path matches
            for part in path_parts:
                if fnmatch.fnmatch(part, pattern):
                    return True

        return False


def is_binary_file(filepath: str) -> Tuple[bool, str]:
    """
    Detect if a file is binary using multiple methods.

    Returns:
        Tuple[bool, str]: (is_binary, reason)
        - is_binary: True if file is detected as binary
        - reason: Description of why it was detected as binary
    """
    # Method 1: Check file extension
    ext = os.path.splitext(filepath)[1].lstrip(".").lower()
    if ext in BINARY_EXTENSIONS:
        return True, f"binary extension (.{ext})"

    # Method 2: Check magic bytes
    try:
        with open(filepath, "rb") as f:
            header = f.read(32)  # Read first 32 bytes

            if not header:
                return False, ""

            # Check against known binary signatures
            for signature in BINARY_SIGNATURES:
                if header.startswith(signature):
                    return True, "binary signature detected"

            # Method 3: Check for null bytes (common in binary files)
            # Read more content to check for null bytes
            f.seek(0)
            chunk = f.read(8192)  # Read first 8KB
            if b"\x00" in chunk:
                return True, "null bytes detected"

            # Method 4: Check ratio of non-printable characters
            non_printable = sum(
                1
                for byte in chunk
                if byte < 32
                and byte not in (9, 10, 13)  # tab, newline, carriage return
            )
            if len(chunk) > 0 and (non_printable / len(chunk)) > 0.1:
                return True, "high non-printable character ratio"

    except (OSError, IOError) as e:
        return False, f"error checking: {e}"

    return False, ""


def get_file_language(filepath: str) -> str:
    """Get the language identifier for syntax highlighting based on file extension."""
    ext = os.path.splitext(filepath)[1].lstrip(".").lower()

    # Check special filenames
    basename = os.path.basename(filepath).lower()
    if basename in ("dockerfile", "containerfile"):
        return "dockerfile"
    if basename in ("makefile", "gnumakefile"):
        return "makefile"
    if basename in ("cmakelists.txt",):
        return "cmake"
    if basename in (".env", ".env.local", ".env.example"):
        return "bash"
    if basename in ("gemfile", "rakefile"):
        return "ruby"

    return EXTENSION_LANGUAGE_MAP.get(ext, ext if ext else "text")


def get_file_size(filepath: str) -> int:
    """Get file size in bytes."""
    try:
        return os.path.getsize(filepath)
    except OSError:
        return 0


def format_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    size: float = float(size_bytes)
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024:
            return (
                f"{size:.1f} {unit}" if unit != "B" else f"{int(size)} {unit}"
            )
        size /= 1024
    return f"{size:.1f} TB"


def read_file_content(
    filepath: str, max_size: Optional[int] = None, skip_binary: bool = True
) -> Tuple[str, Optional[str]]:
    """
    Read file content, handling different encodings and binary detection.

    Args:
        filepath: Path to the file
        max_size: Maximum file size in bytes (None = no limit)
        skip_binary: Whether to skip binary files

    Returns:
        Tuple[str, Optional[str]]: (content, warning_message)
        - content: File content or placeholder message
        - warning_message: Warning if file was skipped (None if read successfully)
    """
    # Check file size
    file_size = get_file_size(filepath)
    if max_size is not None and file_size > max_size:
        return (
            f"[File skipped: size {format_size(file_size)} exceeds limit {format_size(max_size)}]",
            f"size exceeds {format_size(max_size)}",
        )

    # Check if binary
    if skip_binary:
        is_binary, reason = is_binary_file(filepath)
        if is_binary:
            return f"[Binary file: {reason}]", f"binary ({reason})"

    # Try reading with different encodings
    encodings = ["utf-8", "latin-1", "cp1252"]

    for encoding in encodings:
        try:
            with open(filepath, "r", encoding=encoding) as f:
                return f.read(), None
        except UnicodeDecodeError:
            continue
        except Exception as e:
            return f"[Error reading file: {str(e)}]", f"read error: {e}"

    return "[Binary file or unsupported encoding]", "unsupported encoding"


def collect_files(root_dir: str, ignore_parser: GitignoreParser) -> List[str]:
    """Recursively collect all files that should not be ignored."""
    files = []

    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Get relative path
        rel_dir = os.path.relpath(dirpath, root_dir)
        if rel_dir == ".":
            rel_dir = ""

        # Filter out ignored directories (modify in place to prevent os.walk from entering them)
        dirnames[:] = [
            d
            for d in dirnames
            if not ignore_parser.should_ignore(
                os.path.join(rel_dir, d) if rel_dir else d, is_dir=True
            )
        ]

        # Collect non-ignored files
        for filename in filenames:
            rel_path = os.path.join(rel_dir, filename) if rel_dir else filename

            if not ignore_parser.should_ignore(rel_path, is_dir=False):
                files.append(os.path.join(dirpath, filename))

    return sorted(files)


def generate_tree(files: List[str], root_dir: str) -> str:
    """Generate a tree structure of the files."""
    tree_lines = []

    # Build directory structure
    dir_structure = {}
    for filepath in files:
        rel_path = os.path.relpath(filepath, root_dir)
        parts = pathlib.Path(rel_path).parts

        current = dir_structure
        for i, part in enumerate(parts):
            if i == len(parts) - 1:  # File
                if "_files" not in current:
                    current["_files"] = []
                current["_files"].append(part)
            else:  # Directory
                if part not in current:
                    current[part] = {}
                current = current[part]

    # Render tree
    def render_tree(structure, prefix="", is_last=True):
        items = []

        # Get directories and files
        dirs = {k: v for k, v in structure.items() if k != "_files"}
        files = structure.get("_files", [])

        # Sort directories and files
        sorted_dirs = sorted(dirs.items())
        sorted_files = sorted(files)

        all_items = [(d, True) for d in sorted_dirs] + [
            (f, False) for f in sorted_files
        ]

        for idx, (item, is_dir) in enumerate(all_items):
            is_last_item = idx == len(all_items) - 1

            # Tree characters
            connector = "└── " if is_last_item else "├── "
            extension = "    " if is_last_item else "│   "

            if is_dir:
                dir_name, substructure = item
                items.append(f"{prefix}{connector}{dir_name}/")
                items.extend(
                    render_tree(substructure, prefix + extension, is_last_item)
                )
            else:
                items.append(f"{prefix}{connector}{item}")

        return items

    tree_lines.append(".")
    tree_lines.extend(render_tree(dir_structure))

    return "\n".join(tree_lines)


def generate_markdown(
    files: List[str],
    root_dir: str,
    output_file: str,
    max_file_size: Optional[int] = None,
    include_binary: bool = False,
    show_tree: bool = False,
    show_size: bool = False,
    stdout: bool = False,
) -> dict:
    """
    Generate LLM-friendly markdown file with all file contents.

    Args:
        files: List of file paths to include
        root_dir: Root directory for relative paths
        output_file: Output file path
        max_file_size: Maximum file size in bytes (None = no limit)
        include_binary: Whether to include binary files
        show_tree: Whether to show directory tree
        show_size: Whether to show file size in output
        stdout: Whether to output to stdout instead of file

    Returns:
        dict: Statistics about the generation
    """
    stats = {
        "total_files": len(files),
        "processed_files": 0,
        "skipped_files": 0,
        "binary_files": 0,
        "oversized_files": 0,
        "total_size": 0,
        "processed_size": 0,
        "skipped_reasons": [],
    }

    output_lines = []

    def write(text: str):
        output_lines.append(text)

    write("# Source Code Documentation\n\n")
    write(f"**Root Directory:** `{os.path.abspath(root_dir)}`\n\n")
    write(f"**Total Files:** {len(files)}\n\n")

    # Add directory tree (only if requested)
    if show_tree:
        write("## Directory Structure\n\n")
        write("```\n")
        write(generate_tree(files, root_dir))
        write("\n```\n\n")

    write("---\n\n")

    for filepath in files:
        rel_path = os.path.relpath(filepath, root_dir)
        file_size = get_file_size(filepath)
        stats["total_size"] += file_size

        write(f"## File: `{rel_path}`\n\n")

        # Add file metadata
        write(f"**Path:** `{rel_path}`  \n")
        if show_size:
            write(f"**Size:** {format_size(file_size)}  \n")

        # Read content with binary detection
        content, warning = read_file_content(
            filepath, max_size=max_file_size, skip_binary=not include_binary
        )

        # Update stats
        if warning:
            stats["skipped_files"] += 1
            stats["skipped_reasons"].append((rel_path, warning))
            if "binary" in warning:
                stats["binary_files"] += 1
            if "size exceeds" in warning:
                stats["oversized_files"] += 1
            write(f"**Status:** Skipped ({warning})  \n\n")
        else:
            stats["processed_files"] += 1
            stats["processed_size"] += file_size

        # Determine language for syntax highlighting
        lang = get_file_language(filepath)

        write(f"```{lang}\n")
        write(content)
        if not content.endswith("\n"):
            write("\n")
        write("```\n\n")
        write("---\n\n")

    # Write output
    output_content = "".join(output_lines)

    if stdout:
        print(output_content)
    else:
        with open(output_file, "w", encoding="utf-8") as out:
            out.write(output_content)

    return stats


def print_stats(stats: dict):
    """Print generation statistics using rich table."""
    table = Table(
        title="Generation Statistics",
        box=box.ROUNDED,
        show_header=False,
        title_style="bold cyan",
    )
    table.add_column("Metric", style="dim")
    table.add_column("Value", style="bold")

    table.add_row("Total files found", str(stats["total_files"]))
    table.add_row(
        "Files processed",
        f"[green]{stats['processed_files']}[/green]",
    )

    if stats["skipped_files"] > 0:
        table.add_row(
            "Files skipped",
            f"[yellow]{stats['skipped_files']}[/yellow]",
        )
        if stats["binary_files"] > 0:
            table.add_row(
                "  Binary files",
                f"[dim]{stats['binary_files']}[/dim]",
            )
        if stats["oversized_files"] > 0:
            table.add_row(
                "  Oversized files",
                f"[dim]{stats['oversized_files']}[/dim]",
            )

    table.add_row("Total size scanned", format_size(stats["total_size"]))
    table.add_row(
        "Content size",
        f"[cyan]{format_size(stats['processed_size'])}[/cyan]",
    )

    console.print()
    console.print(table)


def parse_size(size_str: str) -> int:
    """Parse human-readable size string to bytes."""
    size_str = size_str.strip().upper()
    units = {"B": 1, "KB": 1024, "MB": 1024**2, "GB": 1024**3}

    for unit, multiplier in units.items():
        if size_str.endswith(unit):
            try:
                return int(float(size_str[: -len(unit)].strip()) * multiplier)
            except ValueError:
                raise argparse.ArgumentTypeError(f"Invalid size: {size_str}")

    # Assume bytes if no unit
    try:
        return int(size_str)
    except ValueError:
        raise argparse.ArgumentTypeError(f"Invalid size: {size_str}")


def collect_files_filtered(
    root_dir: str,
    ignore_parser: GitignoreParser,
    extensions: Optional[List[str]] = None,
    exclude_patterns: Optional[List[str]] = None,
    max_depth: Optional[int] = None,
) -> List[str]:
    """
    Recursively collect files with additional filtering options.

    Args:
        root_dir: Root directory to scan
        ignore_parser: GitignoreParser instance
        extensions: List of extensions to include (e.g., ['py', 'js'])
        exclude_patterns: Additional glob patterns to exclude
        max_depth: Maximum directory depth to scan
    """
    files = []
    root_depth = root_dir.rstrip(os.sep).count(os.sep)

    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Check depth
        current_depth = dirpath.rstrip(os.sep).count(os.sep) - root_depth
        if max_depth is not None and current_depth >= max_depth:
            dirnames.clear()  # Don't descend further
            continue

        # Get relative path
        rel_dir = os.path.relpath(dirpath, root_dir)
        if rel_dir == ".":
            rel_dir = ""

        # Filter out ignored directories
        dirnames[:] = [
            d
            for d in dirnames
            if not ignore_parser.should_ignore(
                os.path.join(rel_dir, d) if rel_dir else d, is_dir=True
            )
        ]

        # Collect non-ignored files
        for filename in filenames:
            rel_path = os.path.join(rel_dir, filename) if rel_dir else filename

            # Check gitignore
            if ignore_parser.should_ignore(rel_path, is_dir=False):
                continue

            # Check extension filter
            if extensions:
                ext = os.path.splitext(filename)[1].lstrip(".").lower()
                if ext not in extensions:
                    continue

            # Check exclude patterns
            if exclude_patterns:
                excluded = False
                for pattern in exclude_patterns:
                    if fnmatch.fnmatch(rel_path, pattern) or fnmatch.fnmatch(
                        filename, pattern
                    ):
                        excluded = True
                        break
                if excluded:
                    continue

            files.append(os.path.join(dirpath, filename))

    return sorted(files)


# Common source code directories to auto-detect (in priority order)
COMMON_SOURCE_DIRS: List[str] = [
    "src",
    "lib",
    "app",
    "source",
    "code",
    "pkg",
    "packages",
    "modules",
    "core",
    "internal",
    "cmd",  # Go projects
    "backend",
    "frontend",
    "server",
    "client",
    "api",
    "services",
    "components",
]


def detect_source_directories(base_dir: str) -> List[str]:
    """
    Auto-detect common source code directories in the given base directory.

    Returns:
        List of detected source directories (absolute paths).
        Empty list if none found.
    """
    detected = []
    for dir_name in COMMON_SOURCE_DIRS:
        dir_path = os.path.join(base_dir, dir_name)
        if os.path.isdir(dir_path):
            detected.append(dir_path)
    return detected


def main():

    parser = argparse.ArgumentParser(
        description="Synthesize codebase into LLM-friendly markdown with gitignore support",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                          # Auto-detect src/, lib/, app/, etc.
  %(prog)s ./my-project             # Scan specific directory
  %(prog)s -e py js ts              # Only include Python, JS, TypeScript files
  %(prog)s --max-size 100KB         # Skip files larger than 100KB
  %(prog)s --exclude "*.test.py"    # Exclude test files
  %(prog)s --stdout | pbcopy        # Copy output to clipboard (macOS)

Auto-detected directories (in order):
  src, lib, app, source, code, pkg, packages, modules, core, internal,
  cmd, backend, frontend, server, client, api, services, components
        """,
    )
    parser.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="Directory to scan (default: auto-detect common source dirs, fallback to current)",
    )

    # Output options
    output_group = parser.add_argument_group("Output Options")
    output_group.add_argument(
        "-o",
        "--output",
        default="codesynth.md",
        help="Output file name (default: codesynth.md)",
    )
    output_group.add_argument(
        "--stdout",
        action="store_true",
        help="Output to stdout instead of file",
    )
    output_group.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Suppress progress messages (only show output)",
    )
    output_group.add_argument(
        "--with-tree",
        action="store_true",
        help="Include directory tree in output",
    )
    output_group.add_argument(
        "--with-size",
        action="store_true",
        help="Show file sizes in output",
    )

    # Filtering options
    filter_group = parser.add_argument_group("Filtering Options")
    filter_group.add_argument(
        "-i",
        "--ignore-file",
        default=".gitignore",
        help="Gitignore file to use (default: .gitignore)",
    )
    filter_group.add_argument(
        "-e",
        "--extensions",
        nargs="+",
        metavar="EXT",
        help="Only include files with these extensions (e.g., py js ts)",
    )
    filter_group.add_argument(
        "--exclude",
        nargs="+",
        metavar="PATTERN",
        help="Additional glob patterns to exclude (e.g., '*.test.py' 'docs/*')",
    )
    filter_group.add_argument(
        "--max-depth",
        type=int,
        metavar="N",
        help="Maximum directory depth to scan",
    )
    filter_group.add_argument(
        "--no-gitignore",
        action="store_true",
        help="Ignore .gitignore patterns (include all files)",
    )

    # Content options
    content_group = parser.add_argument_group("Content Options")
    content_group.add_argument(
        "--max-size",
        type=parse_size,
        metavar="SIZE",
        help="Maximum file size to include (e.g., 100KB, 1MB)",
    )
    content_group.add_argument(
        "--include-binary",
        action="store_true",
        help="Include binary files (by default they are skipped)",
    )

    # Info options
    info_group = parser.add_argument_group("Information Options")
    info_group.add_argument(
        "--stats-only",
        action="store_true",
        help="Only show statistics, don't generate output",
    )
    info_group.add_argument(
        "--list-files",
        action="store_true",
        help="Only list files that would be included",
    )

    args = parser.parse_args()

    # Validate directory
    if not os.path.isdir(args.directory):
        console.print(
            f"[red]Error:[/red] '{args.directory}' is not a valid directory"
        )
        return 1

    quiet = args.quiet or args.stdout

    # Determine directories to scan
    scan_directories: List[str] = []
    user_specified_dir = args.directory != "."

    if user_specified_dir:
        # User explicitly specified a directory
        scan_directories = [args.directory]
    else:
        # Auto-detect common source directories
        detected = detect_source_directories(args.directory)
        if detected:
            scan_directories = detected
            if not quiet:
                dirs_str = ", ".join(
                    f"[cyan]{os.path.basename(d)}[/cyan]" for d in detected
                )
                console.print(f"[green]>[/green] Auto-detected: {dirs_str}")
        else:
            # Fallback to current directory
            scan_directories = [args.directory]
            if not quiet:
                console.print(
                    "[yellow]>[/yellow] No common source dirs found, scanning current directory"
                )

    if not quiet:
        if len(scan_directories) == 1:
            console.print(
                f"[green]>[/green] Scanning: [bold]{os.path.abspath(scan_directories[0])}[/bold]"
            )
        else:
            console.print(
                f"[green]>[/green] Scanning [bold]{len(scan_directories)}[/bold] directories"
            )

    # Parse gitignore (from base directory) unless --no-gitignore
    if args.no_gitignore:
        # Create empty parser with only default ignores
        ignore_parser = GitignoreParser.__new__(GitignoreParser)
        ignore_parser.patterns = []
        ignore_parser.dir_patterns = list(GitignoreParser.DEFAULT_IGNORE_DIRS)
        ignore_parser.gitignore_path = None
        if not quiet:
            console.print("[yellow]>[/yellow] Ignoring .gitignore patterns")
    else:
        ignore_parser = GitignoreParser(args.directory, args.ignore_file)
        if not quiet:
            if ignore_parser.gitignore_path:
                console.print(
                    f"[green]>[/green] Using [dim]{os.path.basename(ignore_parser.gitignore_path)}[/dim] "
                    f"([dim]{len(ignore_parser.patterns)} file, {len(ignore_parser.dir_patterns)} dir patterns[/dim])"
                )

    # Normalize extensions
    extensions = None
    if args.extensions:
        extensions = [ext.lstrip(".").lower() for ext in args.extensions]
        if not quiet:
            ext_str = ", ".join(f"[magenta].{e}[/magenta]" for e in extensions)
            console.print(f"[green]>[/green] Filtering: {ext_str}")

    # Collect files from all directories
    files: List[str] = []

    if not quiet:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            progress.add_task("Collecting files...", total=None)
            for scan_dir in scan_directories:
                dir_files = collect_files_filtered(
                    scan_dir,
                    ignore_parser,
                    extensions=extensions,
                    exclude_patterns=args.exclude,
                    max_depth=args.max_depth,
                )
                files.extend(dir_files)
    else:
        for scan_dir in scan_directories:
            dir_files = collect_files_filtered(
                scan_dir,
                ignore_parser,
                extensions=extensions,
                exclude_patterns=args.exclude,
                max_depth=args.max_depth,
            )
            files.extend(dir_files)

    # Remove duplicates and sort
    files = sorted(set(files))

    if not files:
        console.print("[yellow]No files found to process[/yellow]")
        return 0

    # List files only mode
    if args.list_files:
        tree = Tree(
            f"[bold cyan]Files to include[/bold cyan] ({len(files)})",
            guide_style="dim",
        )
        for f in files:
            rel_path = os.path.relpath(f, args.directory)
            size = get_file_size(f)
            tree.add(
                f"[white]{rel_path}[/white] [dim]({format_size(size)})[/dim]"
            )
        console.print()
        console.print(tree)
        return 0

    # Stats only mode
    if args.stats_only:
        total_size = sum(get_file_size(f) for f in files)
        binary_count = sum(1 for f in files if is_binary_file(f)[0])

        table = Table(
            title="Codebase Statistics",
            box=box.ROUNDED,
            title_style="bold cyan",
        )
        table.add_column("Metric", style="dim")
        table.add_column("Value", style="bold")
        table.add_row("Total files", str(len(files)))
        table.add_row("Binary files", f"[yellow]{binary_count}[/yellow]")
        table.add_row(
            "Text files", f"[green]{len(files) - binary_count}[/green]"
        )
        table.add_row("Total size", f"[cyan]{format_size(total_size)}[/cyan]")
        console.print()
        console.print(table)
        return 0

    # Generate output
    if not quiet:
        output_name = "stdout" if args.stdout else args.output
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            transient=True,  # Clear progress bar after completion
        ) as progress:
            task = progress.add_task(
                f"Generating {output_name}...", total=len(files)
            )

            # Generate with progress updates
            stats = generate_markdown(
                files,
                args.directory,
                args.output,
                max_file_size=args.max_size,
                include_binary=args.include_binary,
                show_tree=args.with_tree,
                show_size=args.with_size,
                stdout=args.stdout,
            )
            progress.update(task, completed=len(files))

        # Print success message after progress bar is cleared
        if not args.stdout:
            console.print(
                f"[green]>[/green] Generated [bold]{args.output}[/bold]"
            )
    else:
        stats = generate_markdown(
            files,
            args.directory,
            args.output,
            max_file_size=args.max_size,
            include_binary=args.include_binary,
            show_tree=args.with_tree,
            show_size=args.with_size,
            stdout=args.stdout,
        )

    if not quiet:
        print_stats(stats)

    return 0


if __name__ == "__main__":
    exit(main())
