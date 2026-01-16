"""Gitignore parser for codesynth."""

from __future__ import annotations

import os
import pathlib
import fnmatch
from dataclasses import dataclass
from typing import List

from .constants import DEFAULT_IGNORE_DIRS


@dataclass(frozen=True)
class GitignorePattern:
    pattern: str
    is_dir: bool
    negate: bool
    anchored: bool


class GitignoreParser:
    """Parser for .gitignore files."""

    def __init__(
        self, start_dir: str = ".", gitignore_name: str = ".gitignore"
    ):
        self.patterns: List[GitignorePattern] = []
        self.dir_patterns: List[str] = list(DEFAULT_IGNORE_DIRS)
        self.gitignore_path: str | None = None

        # Search for gitignore in current and parent directories
        current = os.path.abspath(start_dir)
        while True:
            potential_gitignore = os.path.join(current, gitignore_name)
            if os.path.exists(potential_gitignore):
                self.gitignore_path = potential_gitignore
                break

            parent = os.path.dirname(current)
            if parent == current:
                break
            current = parent

        for dir_pattern in self.dir_patterns:
            self.patterns.append(
                GitignorePattern(
                    pattern=dir_pattern,
                    is_dir=True,
                    negate=False,
                    anchored=False,
                )
            )

        if self.gitignore_path:
            with open(self.gitignore_path, "r", encoding="utf-8") as f:
                for line in f:
                    entry = line.strip()
                    if not entry or entry.startswith("#"):
                        continue

                    negate = False
                    if entry.startswith("\\!"):
                        entry = entry[1:]
                    elif entry.startswith("!"):
                        negate = True
                        entry = entry[1:]

                    anchored = entry.startswith("/")
                    if anchored:
                        entry = entry.lstrip("/")

                    is_dir = entry.endswith("/")
                    if is_dir:
                        entry = entry.rstrip("/")

                    if entry:
                        self.patterns.append(
                            GitignorePattern(
                                pattern=entry,
                                is_dir=is_dir,
                                negate=negate,
                                anchored=anchored,
                            )
                        )

    def _matches_pattern(
        self, pattern: GitignorePattern, path: str, is_dir: bool
    ) -> bool:
        path_normalized = path.replace(os.sep, "/").lstrip("./")
        path_parts = pathlib.Path(path_normalized).parts

        if pattern.anchored:
            if pattern.is_dir:
                if is_dir:
                    return fnmatch.fnmatch(
                        path_normalized, pattern.pattern
                    )
                return path_normalized.startswith(
                    pattern.pattern.rstrip("/") + "/"
                )
            return fnmatch.fnmatch(path_normalized, pattern.pattern)

        if pattern.is_dir:
            if is_dir and fnmatch.fnmatch(
                os.path.basename(path_normalized), pattern.pattern
            ):
                return True
            for part in path_parts:
                if fnmatch.fnmatch(part, pattern.pattern):
                    return True
            if not is_dir and "/" not in pattern.pattern:
                return any(
                    fnmatch.fnmatch(part, pattern.pattern) for part in path_parts
                )
            return False

        if fnmatch.fnmatch(os.path.basename(path_normalized), pattern.pattern):
            return True
        if "/" in pattern.pattern and fnmatch.fnmatch(
            path_normalized, pattern.pattern
        ):
            return True
        return any(
            fnmatch.fnmatch(part, pattern.pattern) for part in path_parts
        )

    def should_ignore(self, path: str, is_dir: bool = False) -> bool:
        """Check if a path should be ignored based on gitignore patterns."""
        ignored = False

        for pattern in self.patterns:
            if self._matches_pattern(pattern, path, is_dir=is_dir):
                ignored = not pattern.negate

        return ignored

    @classmethod
    def empty(cls) -> "GitignoreParser":
        """Create an empty parser with only default ignores."""
        parser = cls.__new__(cls)
        parser.patterns = [
            GitignorePattern(
                pattern=dir_pattern,
                is_dir=True,
                negate=False,
                anchored=False,
            )
            for dir_pattern in DEFAULT_IGNORE_DIRS
        ]
        parser.dir_patterns = list(DEFAULT_IGNORE_DIRS)
        parser.gitignore_path = None
        return parser
