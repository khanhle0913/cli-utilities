"""Gitignore parser for codesynth."""

import os
import pathlib
import fnmatch
from typing import List

from .constants import DEFAULT_IGNORE_DIRS


class GitignoreParser:
    """Parser for .gitignore files."""

    def __init__(
        self, start_dir: str = ".", gitignore_name: str = ".gitignore"
    ):
        self.patterns: List[str] = []
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

        if self.gitignore_path:
            with open(self.gitignore_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue

                    if line.endswith("/"):
                        self.dir_patterns.append(line.rstrip("/"))
                    else:
                        self.patterns.append(line)

    def should_ignore(self, path: str, is_dir: bool = False) -> bool:
        """Check if a path should be ignored based on gitignore patterns."""
        path_parts = pathlib.Path(path).parts

        if is_dir:
            for pattern in self.dir_patterns:
                if fnmatch.fnmatch(os.path.basename(path), pattern):
                    return True
                for part in path_parts:
                    if fnmatch.fnmatch(part, pattern):
                        return True

        for pattern in self.patterns:
            if fnmatch.fnmatch(os.path.basename(path), pattern):
                return True
            if "/" in pattern and fnmatch.fnmatch(path, pattern):
                return True
            for part in path_parts:
                if fnmatch.fnmatch(part, pattern):
                    return True

        return False

    @classmethod
    def empty(cls) -> "GitignoreParser":
        """Create an empty parser with only default ignores."""
        parser = cls.__new__(cls)
        parser.patterns = []
        parser.dir_patterns = list(DEFAULT_IGNORE_DIRS)
        parser.gitignore_path = None
        return parser
