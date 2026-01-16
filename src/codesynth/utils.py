"""Utility functions for codesynth."""

import os
import re
import argparse
from typing import Tuple, Optional

from .constants import (
    BINARY_SIGNATURES,
    BINARY_EXTENSIONS,
    EXTENSION_LANGUAGE_MAP,
)


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


def parse_size(size_str: str) -> int:
    """Parse human-readable size string to bytes."""
    size_str = size_str.strip().upper()
    units = {"GB": 1024**3, "MB": 1024**2, "KB": 1024, "B": 1}

    for unit, multiplier in units.items():
        if size_str.endswith(unit):
            try:
                return int(float(size_str[: -len(unit)].strip()) * multiplier)
            except ValueError:
                raise argparse.ArgumentTypeError(f"Invalid size: {size_str}")

    try:
        return int(size_str)
    except ValueError:
        raise argparse.ArgumentTypeError(f"Invalid size: {size_str}")


def count_max_backticks(content: str) -> int:
    """Count the maximum consecutive backticks in content."""
    matches = re.findall(r"`+", content)
    if not matches:
        return 0
    return max(len(m) for m in matches)


def get_fence(content: str, min_ticks: int = 3) -> str:
    """Get a fence string that won't conflict with content."""
    max_ticks = count_max_backticks(content)
    needed = max(min_ticks, max_ticks + 1)
    return "`" * needed


def is_binary_file(filepath: str) -> Tuple[bool, str]:
    """
    Detect if a file is binary using multiple methods.

    Returns:
        Tuple[bool, str]: (is_binary, reason)
    """
    try:
        with open(filepath, "rb") as f:
            header = f.read(32)

            if not header:
                ext = os.path.splitext(filepath)[1].lstrip(".").lower()
                if ext in BINARY_EXTENSIONS:
                    return True, f"binary extension (.{ext})"
                return False, ""

            for signature in BINARY_SIGNATURES:
                if header.startswith(signature):
                    return True, "binary signature detected"

            f.seek(0)
            chunk = f.read(8192)
            if b"\x00" in chunk:
                return True, "null bytes detected"

            non_printable = sum(
                1 for byte in chunk if byte < 32 and byte not in (9, 10, 13)
            )
            if len(chunk) > 0 and (non_printable / len(chunk)) > 0.1:
                return True, "high non-printable character ratio"

        ext = os.path.splitext(filepath)[1].lstrip(".").lower()
        if ext in BINARY_EXTENSIONS:
            return True, f"binary extension (.{ext})"

    except (OSError, IOError) as e:
        return False, f"error checking: {e}"

    return False, ""


def get_file_language(filepath: str) -> str:
    """Get the language identifier for syntax highlighting."""
    ext = os.path.splitext(filepath)[1].lstrip(".").lower()

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


def read_file_content(
    filepath: str, max_size: Optional[int] = None, skip_binary: bool = True
) -> Tuple[str, Optional[str]]:
    """
    Read file content, handling different encodings and binary detection.

    Returns:
        Tuple[str, Optional[str]]: (content, warning_message)
    """
    file_size = get_file_size(filepath)
    if max_size is not None and file_size > max_size:
        return (
            f"[File skipped: size {format_size(file_size)} exceeds limit {format_size(max_size)}]",
            f"size exceeds {format_size(max_size)}",
        )

    if skip_binary:
        is_binary, reason = is_binary_file(filepath)
        if is_binary:
            return f"[Binary file: {reason}]", f"binary ({reason})"

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
