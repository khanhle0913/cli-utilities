"""File collection logic for codesynth."""

import os
import fnmatch
from typing import List, Optional

from .parser import GitignoreParser
from .constants import COMMON_SOURCE_DIRS


def detect_source_directories(base_dir: str) -> List[str]:
    """
    Auto-detect common source code directories.

    Returns:
        List of detected source directories (absolute paths).
    """
    detected = []
    for dir_name in COMMON_SOURCE_DIRS:
        dir_path = os.path.join(base_dir, dir_name)
        if os.path.isdir(dir_path):
            detected.append(dir_path)
    return detected


def collect_files(root_dir: str, ignore_parser: GitignoreParser) -> List[str]:
    """Recursively collect all files that should not be ignored."""
    files = []

    for dirpath, dirnames, filenames in os.walk(root_dir):
        rel_dir = os.path.relpath(dirpath, root_dir)
        if rel_dir == ".":
            rel_dir = ""

        dirnames[:] = [
            d
            for d in dirnames
            if not ignore_parser.should_ignore(
                os.path.join(rel_dir, d) if rel_dir else d, is_dir=True
            )
        ]

        for filename in filenames:
            rel_path = os.path.join(rel_dir, filename) if rel_dir else filename
            if not ignore_parser.should_ignore(rel_path, is_dir=False):
                files.append(os.path.join(dirpath, filename))

    return sorted(files)


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
        current_depth = dirpath.rstrip(os.sep).count(os.sep) - root_depth
        if max_depth is not None and current_depth >= max_depth:
            dirnames.clear()
            continue

        rel_dir = os.path.relpath(dirpath, root_dir)
        if rel_dir == ".":
            rel_dir = ""

        dirnames[:] = [
            d
            for d in dirnames
            if not ignore_parser.should_ignore(
                os.path.join(rel_dir, d) if rel_dir else d, is_dir=True
            )
        ]

        for filename in filenames:
            rel_path = os.path.join(rel_dir, filename) if rel_dir else filename

            if ignore_parser.should_ignore(rel_path, is_dir=False):
                continue

            if extensions:
                ext = os.path.splitext(filename)[1].lstrip(".").lower()
                if ext not in extensions:
                    continue

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
