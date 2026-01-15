"""Markdown generation for codesynth."""

import os
import pathlib
from typing import List, Optional

from .utils import (
    get_file_size,
    format_size,
    read_file_content,
    get_file_language,
    get_fence,
)


def generate_tree(files: List[str], root_dir: str) -> str:
    """Generate a tree structure of the files."""
    dir_structure: dict = {}

    for filepath in files:
        rel_path = os.path.relpath(filepath, root_dir)
        parts = pathlib.Path(rel_path).parts

        current = dir_structure
        for i, part in enumerate(parts):
            if i == len(parts) - 1:
                if "_files" not in current:
                    current["_files"] = []
                current["_files"].append(part)
            else:
                if part not in current:
                    current[part] = {}
                current = current[part]

    def render_tree(structure: dict, prefix: str = "") -> List[str]:
        items = []
        dirs = {k: v for k, v in structure.items() if k != "_files"}
        file_list = structure.get("_files", [])

        sorted_dirs = sorted(dirs.items())
        sorted_files = sorted(file_list)

        all_items = [(d, True) for d in sorted_dirs] + [
            (f, False) for f in sorted_files
        ]

        for idx, (item, is_dir) in enumerate(all_items):
            is_last_item = idx == len(all_items) - 1
            connector = "└── " if is_last_item else "├── "
            extension = "    " if is_last_item else "│   "

            if is_dir:
                dir_name, substructure = item
                items.append(f"{prefix}{connector}{dir_name}/")
                items.extend(render_tree(substructure, prefix + extension))
            else:
                items.append(f"{prefix}{connector}{item}")

        return items

    # Use directory name instead of '.'
    root_name = os.path.basename(os.path.abspath(root_dir))
    if not root_name:
        root_name = "."
    tree_lines = [f"{root_name}/"]
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
    tree_files: Optional[List[str]] = None,
    tree_root: Optional[str] = None,
    return_content: bool = False,
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
        tree_files: Files to use for tree generation (for --files mode)

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

    output_lines: List[str] = []

    def write(text: str):
        output_lines.append(text)

    write("# Source Code Documentation\n\n")
    write(f"**Root Directory:** `{os.path.abspath(root_dir)}`\n\n")
    write(f"**Total Files:** {len(files)}\n\n")

    if show_tree:
        files_for_tree = tree_files if tree_files else files
        # Use tree_root if provided, otherwise root_dir
        tree_base = tree_root if tree_root else root_dir
        write("## Directory Structure\n\n")
        write("```\n")
        write(generate_tree(files_for_tree, tree_base))
        write("\n```\n\n")

    write("---\n\n")

    for filepath in files:
        rel_path = os.path.relpath(filepath, root_dir)
        file_size = get_file_size(filepath)
        stats["total_size"] += file_size

        # File header with optional size
        if show_size:
            write(f"## File: {rel_path} ({format_size(file_size)})\n\n")
        else:
            write(f"## File: {rel_path}\n\n")

        content, warning = read_file_content(
            filepath, max_size=max_file_size, skip_binary=not include_binary
        )

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

        lang = get_file_language(filepath)
        fence = get_fence(content)

        write(f"{fence}{lang}\n")
        write(content)
        if not content.endswith("\n"):
            write("\n")
        write(f"{fence}\n\n")
        write("---\n\n")

    output_content = "".join(output_lines)

    if return_content:
        stats["content"] = output_content
    elif stdout:
        print(output_content)
    else:
        with open(output_file, "w", encoding="utf-8") as out:
            out.write(output_content)

    return stats
