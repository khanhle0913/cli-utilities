"""CLI argument parsing for codesynth."""

import argparse

from .utils import parse_size


def create_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        description="Synthesize codebase into LLM-friendly markdown",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        add_help=True,
    )

    parser.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="Directory to scan",
    )

    # Output options
    output_group = parser.add_argument_group("Output")
    output_group.add_argument(
        "-o",
        "--output",
        default="codesynth.md",
        help="Output file name",
    )
    output_group.add_argument(
        "--stdout",
        action="store_true",
        help="Output to stdout",
    )
    output_group.add_argument(
        "--clipboard",
        action="store_true",
        help="Copy output to clipboard",
    )
    output_group.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Suppress progress messages",
    )
    output_group.add_argument(
        "-t",
        "--tree",
        action="store_true",
        dest="with_tree",
        help="Include directory tree",
    )
    output_group.add_argument(
        "-s",
        "--size",
        action="store_true",
        dest="with_size",
        help="Show file sizes",
    )

    # File selection
    file_group = parser.add_argument_group("Selection")
    file_group.add_argument(
        "-f",
        "--files",
        nargs="+",
        metavar="FILE",
        help="Include only specific files",
    )
    file_group.add_argument(
        "--extensions",
        nargs="+",
        metavar="EXT",
        help="Filter by extensions",
    )
    file_group.add_argument(
        "-e",
        "--exclude",
        nargs="+",
        metavar="PATTERN",
        help="Exclude patterns",
    )
    file_group.add_argument(
        "--max-depth",
        type=int,
        metavar="N",
        help="Maximum directory depth",
    )
    file_group.add_argument(
        "-i",
        "--ignore-file",
        default=".gitignore",
        help="Custom ignore file",
    )
    file_group.add_argument(
        "--no-gitignore",
        action="store_true",
        help="Ignore .gitignore patterns",
    )

    # Content options
    content_group = parser.add_argument_group("Content")
    content_group.add_argument(
        "--max-size",
        type=parse_size,
        metavar="SIZE",
        help="Maximum file size",
    )
    content_group.add_argument(
        "--include-binary",
        action="store_true",
        help="Include binary files",
    )

    # Info options
    info_group = parser.add_argument_group("Analysis")
    info_group.add_argument(
        "--stats-only",
        action="store_true",
        help="Show statistics only",
    )
    info_group.add_argument(
        "--list-files",
        action="store_true",
        help="List files only",
    )

    # Reverse options
    reverse_group = parser.add_argument_group("Reverse")
    reverse_group.add_argument(
        "--reverse",
        metavar="FILE",
        help="Reverse codesynth markdown into source files",
    )
    reverse_group.add_argument(
        "--output-dir",
        metavar="DIR",
        help="Output directory for --reverse",
    )

    return parser
