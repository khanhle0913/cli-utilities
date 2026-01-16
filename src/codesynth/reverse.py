"""Reverse codesynth markdown back into source files."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import List, Tuple

from .output import console, print_status


FILE_HEADER_RE = re.compile(r"^## File: (.+?)(?: \([^)]*\))?$")
STATUS_SKIPPED_RE = re.compile(r"^\*\*Status:\*\* Skipped")


@dataclass
class ParsedFile:
    """Parsed file entry from codesynth markdown."""

    path: str
    content: str
    skipped: bool


def _parse_fence_marker(line: str) -> str | None:
    stripped = line.strip()
    if not stripped.startswith("`"):
        return None
    count = 0
    for char in stripped:
        if char == "`":
            count += 1
        else:
            break
    if count < 3:
        return None
    return "`" * count


def parse_codesynth_markdown(content: str) -> Tuple[List[ParsedFile], List[str]]:
    """Parse codesynth markdown content into file entries.

    Returns a tuple of parsed files and warning messages.
    """
    lines = content.splitlines(keepends=True)
    files: List[ParsedFile] = []
    warnings: List[str] = []
    index = 0

    while index < len(lines):
        line = lines[index].rstrip("\n")
        match = FILE_HEADER_RE.match(line.strip())
        if not match:
            index += 1
            continue

        rel_path = match.group(1)
        index += 1

        while index < len(lines) and lines[index].strip() == "":
            index += 1

        skipped = False
        if index < len(lines) and STATUS_SKIPPED_RE.match(lines[index].strip()):
            skipped = True
            index += 1
            while index < len(lines) and lines[index].strip() == "":
                index += 1

        if index >= len(lines):
            warnings.append(f"Missing code fence for {rel_path}")
            break

        fence_marker = _parse_fence_marker(lines[index])
        if not fence_marker:
            warnings.append(f"Invalid code fence for {rel_path}")
            index += 1
            continue

        index += 1
        content_lines: List[str] = []
        while index < len(lines):
            if lines[index].strip() == fence_marker:
                index += 1
                break
            content_lines.append(lines[index])
            index += 1
        else:
            warnings.append(f"Unterminated code fence for {rel_path}")

        files.append(
            ParsedFile(path=rel_path, content="".join(content_lines), skipped=skipped)
        )

    return files, warnings


def _safe_join(base_dir: str, rel_path: str) -> str | None:
    base_abs = os.path.abspath(base_dir)
    target = os.path.abspath(os.path.join(base_abs, rel_path))
    if target == base_abs:
        return None
    if not target.startswith(base_abs + os.sep):
        return None
    return target


def reverse_codesynth(
    input_path: str, output_dir: str, quiet: bool = False
) -> dict:
    """Reverse a codesynth markdown file into source files."""
    with open(input_path, "r", encoding="utf-8") as handle:
        content = handle.read()

    files, warnings = parse_codesynth_markdown(content)
    stats = {
        "total_files": len(files),
        "written_files": 0,
        "skipped_files": 0,
        "warnings": warnings,
    }

    os.makedirs(output_dir, exist_ok=True)

    for entry in files:
        if entry.skipped:
            stats["skipped_files"] += 1
            continue

        target_path = _safe_join(output_dir, entry.path)
        if not target_path:
            stats["skipped_files"] += 1
            warnings.append(f"Unsafe path skipped: {entry.path}")
            continue

        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        with open(target_path, "w", encoding="utf-8") as handle:
            handle.write(entry.content)
        stats["written_files"] += 1

    if not quiet:
        print_status(f"Wrote {stats['written_files']} file(s)", style="success")
        if stats["skipped_files"]:
            print_status(
                f"Skipped {stats['skipped_files']} file(s)", style="warning"
            )
        for message in warnings:
            console.print(f"  [yellow]![/yellow] {message}")

    return stats
