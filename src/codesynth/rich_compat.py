"""Compatibility layer for Rich optional dependency."""

from __future__ import annotations

import importlib.util
from typing import Any


if importlib.util.find_spec("rich") is None:

    class Console:
        """Fallback console that proxies to built-in print."""

        def print(self, *args: Any, **kwargs: Any) -> None:
            print(*args)

    class Progress:
        """Fallback progress context manager."""

        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass

        def __enter__(self) -> "Progress":
            return self

        def __exit__(self, exc_type, exc, traceback) -> bool:
            return False

        def add_task(self, *args: Any, **kwargs: Any) -> int:
            return 0

        def update(self, *args: Any, **kwargs: Any) -> None:
            return None

    class SpinnerColumn:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass

    class TextColumn:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass

    class BarColumn:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass

    class Table:
        def __init__(self, title: str | None = None, **kwargs: Any) -> None:
            self.title = title
            self.columns: list[str] = []
            self.rows: list[tuple[str, ...]] = []

        def add_column(self, name: str, **kwargs: Any) -> None:
            self.columns.append(name)

        def add_row(self, *values: str) -> None:
            self.rows.append(values)

        def __str__(self) -> str:
            lines: list[str] = []
            if self.title:
                lines.append(str(self.title))
            if self.columns:
                lines.append(" | ".join(self.columns))
            for row in self.rows:
                lines.append(" | ".join(str(value) for value in row))
            return "\n".join(lines)

    class Tree:
        def __init__(self, label: str, **kwargs: Any) -> None:
            self.label = label
            self.children: list["Tree"] = []

        def add(self, label: str, **kwargs: Any) -> "Tree":
            child = Tree(label)
            self.children.append(child)
            return child

        def __str__(self) -> str:
            lines = [str(self.label)]

            def render(node: "Tree", prefix: str) -> None:
                for child in node.children:
                    lines.append(f"{prefix}- {child.label}")
                    render(child, f"{prefix}  ")

            render(self, "")
            return "\n".join(lines)

    class _Box:
        ROUNDED = None

    box = _Box()

else:
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
    from rich.table import Table
    from rich.tree import Tree
    from rich import box
