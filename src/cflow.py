#!/usr/bin/env python3
"""
cflow - Code Flow Visualizer

Visualize function call graphs from entry point through the entire call chain.
Supports Python codebases using AST-based analysis.

Usage:
    cflow ./src                        # Analyze and output call tree to cflow.md
    cflow ./src --entry main           # Start from specific function
    cflow ./src --with-mermaid         # Include Mermaid diagram in output
    cflow ./src/main.py                # Analyze specific file
"""

import ast
import sys
import argparse
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict

from codesynth.rich_compat import (
    Console,
    Table,
    Tree,
    Progress,
    SpinnerColumn,
    TextColumn,
    box,
)

# Rich console for pretty output
console = Console()


# ================================================================
# Data Structures
# ================================================================


@dataclass
class FunctionInfo:
    """Information about a function or method."""

    name: str
    qualified_name: str  # Class.method or function
    filepath: Path
    lineno: int
    language: str
    calls: List[str] = field(default_factory=list)
    is_method: bool = False
    class_name: Optional[str] = None


@dataclass
class CallGraph:
    """Represents the function call graph."""

    functions: Dict[str, FunctionInfo] = field(default_factory=dict)
    edges: List[Tuple[str, str]] = field(default_factory=list)
    entry_points: List[str] = field(default_factory=list)
    external_calls: Set[str] = field(default_factory=set)


# ================================================================
# File Extension
# ================================================================

SUPPORTED_EXTENSION: str = ".py"


def is_python_file(filepath: Path) -> bool:
    """Check if file is a Python file."""
    return filepath.suffix.lower() == SUPPORTED_EXTENSION


# ================================================================
# Python Parser (AST-based)
# ================================================================


class PythonCallVisitor(ast.NodeVisitor):
    """Extract function calls from Python AST."""

    def __init__(self, class_names: Optional[Set[str]] = None):
        self.calls: List[str] = []
        self.constructor_calls: List[str] = []  # Track ClassName() calls
        self.class_names = class_names or set()

    def visit_Call(self, node: ast.Call):
        call_name = self._get_call_name(node)
        if call_name:
            # Check if this is a constructor call (ClassName())
            if call_name in self.class_names:
                # Add as constructor call -> ClassName.__init__
                self.constructor_calls.append(f"{call_name}.__init__")
            self.calls.append(call_name)
        self.generic_visit(node)

    def _get_call_name(self, node: ast.Call) -> Optional[str]:
        if isinstance(node.func, ast.Name):
            return node.func.id
        elif isinstance(node.func, ast.Attribute):
            parts = []
            current = node.func
            while isinstance(current, ast.Attribute):
                parts.append(current.attr)
                current = current.value
            if isinstance(current, ast.Name):
                parts.append(current.id)
            parts.reverse()
            return ".".join(parts)
        return None


class PythonModuleVisitor(ast.NodeVisitor):
    """Visit Python module and extract function definitions."""

    def __init__(self, filepath: Path):
        self.filepath = filepath
        self.functions: Dict[str, FunctionInfo] = {}
        self.current_class: Optional[str] = None
        self._function_nodes: Dict[
            str, ast.FunctionDef | ast.AsyncFunctionDef
        ] = {}
        self.class_names: Set[str] = (
            set()
        )  # Track all class names for constructor detection
        self.class_methods: Dict[str, Set[str]] = (
            {}
        )  # class_name -> set of method names

    def visit_ClassDef(self, node: ast.ClassDef):
        old_class = self.current_class
        self.current_class = node.name
        self.class_names.add(node.name)  # Track class name
        self.class_methods[node.name] = set()  # Initialize method set
        self.generic_visit(node)
        self.current_class = old_class

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self._process_function(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self._process_function(node)

    def _process_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef):
        if self.current_class:
            qualified_name = f"{self.current_class}.{node.name}"
            is_method = True
            class_name = self.current_class
            # Track method in class
            self.class_methods[self.current_class].add(node.name)
        else:
            qualified_name = node.name
            is_method = False
            class_name = None

        func_info = FunctionInfo(
            name=node.name,
            qualified_name=qualified_name,
            filepath=self.filepath,
            lineno=node.lineno,
            language="python",
            is_method=is_method,
            class_name=class_name,
        )

        self.functions[qualified_name] = func_info
        self._function_nodes[qualified_name] = node

    def extract_calls(self):
        for qualified_name, node in self._function_nodes.items():
            visitor = PythonCallVisitor(class_names=self.class_names)
            for child in ast.walk(node):
                if isinstance(child, ast.Call):
                    visitor.visit_Call(child)
            # Combine regular calls with constructor calls
            all_calls = visitor.calls + visitor.constructor_calls
            self.functions[qualified_name].calls = all_calls


def parse_python_file(filepath: Path) -> Dict[str, FunctionInfo]:
    """Parse Python file using AST."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            source = f.read()
        tree = ast.parse(source, filename=str(filepath))
    except (IOError, UnicodeDecodeError, SyntaxError):
        return {}

    visitor = PythonModuleVisitor(filepath)
    visitor.visit(tree)
    visitor.extract_calls()
    return visitor.functions


# ================================================================
# File Collection
# ================================================================


def collect_source_files(
    root_path: Path, exclude_dirs: Optional[Set[str]] = None
) -> List[Path]:
    """Collect all Python source files."""
    if exclude_dirs is None:
        exclude_dirs = {
            ".git",
            ".svn",
            ".hg",
            "__pycache__",
            ".venv",
            "venv",
            ".env",
            "env",
            ".tox",
            ".nox",
            ".mypy_cache",
            ".pytest_cache",
            ".ruff_cache",
            "dist",
            "build",
        }

    files: List[Path] = []

    if root_path.is_file():
        if is_python_file(root_path):
            return [root_path]
        return []

    for entry in root_path.iterdir():
        if entry.name.startswith("."):
            continue
        if entry.name in exclude_dirs:
            continue

        if entry.is_dir():
            files.extend(collect_source_files(entry, exclude_dirs))
        elif entry.is_file() and is_python_file(entry):
            files.append(entry)

    return files


# ================================================================
# Call Graph Builder
# ================================================================


def find_entry_points(functions: Dict[str, FunctionInfo]) -> List[str]:
    """Find likely entry points - only obvious ones like main."""
    entry_points: List[str] = []

    # Patterns that are NOT entry points
    excluded_patterns = {
        # Magic methods
        "__init__",
        "__str__",
        "__repr__",
        "__call__",
        "__enter__",
        "__exit__",
        "__iter__",
        "__next__",
        "__len__",
        "__getitem__",
        "__setitem__",
        # Visitor pattern methods (AST, etc.)
        "visit",
        "generic_visit",
        # Common non-entry patterns
        "constructor",
        "setup",
        "teardown",
        "configure",
    }

    # Prefixes that indicate non-entry points
    excluded_prefixes = (
        "_",  # Private methods
        "visit_",  # Visitor pattern
        "test_",  # Test functions
        "on_",  # Event handlers
        "handle_",  # Handlers (usually called internally)
    )

    # Priority 1: main function (the only guaranteed entry point)
    if "main" in functions:
        entry_points.append("main")
        return entry_points  # If main exists, it's likely THE entry point

    # Priority 2: Only top-level functions not called by others
    # But be much more strict
    all_calls: Set[str] = set()
    for func_info in functions.values():
        for call in func_info.calls:
            all_calls.add(call)
            if "." in call:
                all_calls.add(call.split(".")[-1])

    for name in functions:
        simple_name = name.split(".")[-1] if "." in name else name

        # Skip if called by others
        if simple_name in all_calls or name in all_calls:
            continue

        # Skip excluded patterns
        if simple_name in excluded_patterns:
            continue

        # Skip excluded prefixes
        if any(simple_name.startswith(p) for p in excluded_prefixes):
            continue

        # Skip class methods (they're usually not entry points)
        if "." in name:
            continue

        # Only add if not already in list
        if name not in entry_points:
            entry_points.append(name)

    # If no entry points found, return empty (user should use --entry)
    return entry_points


def build_call_graph(
    root_path: Path,
    entry_function: Optional[str] = None,
    max_depth: int = 10,
) -> CallGraph:
    """Build a call graph from source files."""
    graph = CallGraph()

    # Collect and parse files
    source_files = collect_source_files(root_path)
    all_functions: Dict[str, FunctionInfo] = {}

    for filepath in source_files:
        file_functions = parse_python_file(filepath)
        all_functions.update(file_functions)

    graph.functions = all_functions

    # Determine entry points
    if entry_function:
        if entry_function in all_functions:
            graph.entry_points = [entry_function]
        else:
            matches = [n for n in all_functions if entry_function in n]
            graph.entry_points = matches[:1] if matches else []
    else:
        graph.entry_points = find_entry_points(all_functions)

    # Build edges (internal only)
    visited: Set[str] = set()
    known_names = set(all_functions.keys())
    known_simple = {n.split(".")[-1]: n for n in all_functions.keys()}

    # Build a map of method names to their qualified names (for cross-class resolution)
    # method_name -> [ClassName.method_name, ...]
    method_to_qualified: Dict[str, List[str]] = defaultdict(list)
    for name in all_functions.keys():
        if "." in name:
            method_name = name.split(".")[-1]
            method_to_qualified[method_name].append(name)

    def resolve_call(
        call_name: str,
        current_class: Optional[str],
        caller_func: Optional[str] = None,
    ) -> Optional[str]:
        # Direct match (qualified name exactly matches)
        if call_name in known_names:
            return call_name

        # self.method() -> CurrentClass.method
        if call_name.startswith("self.") and current_class:
            method = call_name.replace("self.", "")
            qualified = f"{current_class}.{method}"
            if qualified in known_names:
                return qualified
            # self.method() could also call a nested method, ignore if not found
            return None

        # instance.method() pattern -> try to find ClassName.method
        # But be careful not to match same-name methods incorrectly
        if "." in call_name:
            parts = call_name.split(".")
            method = parts[-1]  # Last part is the method name

            # Skip external calls like logging.info, self.client.foo, etc.
            # These are calls to external libraries/objects
            # Only resolve if the pattern looks like a known class method

            if method in method_to_qualified:
                candidates = method_to_qualified[method]
                # Filter out deeply nested names (more than 2 parts = nested funcs)
                candidates = [c for c in candidates if c.count(".") == 1]

                # Don't match if caller would be calling itself
                if caller_func:
                    candidates = [c for c in candidates if c != caller_func]

                # Filter out methods from the same class (avoid false cross-reference)
                if current_class:
                    # Prefer methods from DIFFERENT classes
                    other_class_candidates = [
                        c
                        for c in candidates
                        if not c.startswith(f"{current_class}.")
                    ]
                    if other_class_candidates:
                        candidates = other_class_candidates

                # Only resolve if there's exactly ONE candidate
                # If multiple candidates exist (e.g., PersonRepository.create vs 
                # ZoneRepository.create), we cannot determine which one without 
                # type analysis, so we return None to avoid false positives
                if len(candidates) == 1:
                    return candidates[0]
                # Multiple candidates = ambiguous, don't resolve

            # Don't resolve arbitrary instance.method() calls
            return None

        # Simple name match (for top-level functions only)
        simple = call_name.split(".")[-1]
        if simple in known_simple:
            qualified = known_simple[simple]
            # Only match if it's a top-level function (no dots)
            # to avoid matching Class.method as just 'method'
            if "." not in qualified:
                return qualified

        return None

    def traverse(func_name: str, depth: int = 0):
        if depth > max_depth or func_name in visited:
            return
        visited.add(func_name)

        func_info = all_functions.get(func_name)
        if not func_info:
            return

        for call in func_info.calls:
            resolved = resolve_call(call, func_info.class_name, func_name)
            if resolved:
                graph.edges.append((func_name, resolved))
                traverse(resolved, depth + 1)
            else:
                graph.external_calls.add(call)

    for entry in graph.entry_points:
        traverse(entry)

    return graph


# ================================================================
# Output Formatters
# ================================================================


def format_tree_text(graph: CallGraph, max_depth: int = 10) -> str:
    """Generate ASCII tree representation."""
    lines: List[str] = []

    # Build adjacency list
    adj: Dict[str, List[str]] = defaultdict(list)
    for src, dst in graph.edges:
        if dst not in adj[src]:
            adj[src].append(dst)

    def render_node(
        node: str,
        prefix: str = "",
        is_last: bool = True,
        visited: Set[str] | None = None,
        depth: int = 0,
    ):
        if visited is None:
            visited = set()

        connector = "└── " if is_last else "├── "
        func_info = graph.functions.get(node)
        suffix = ""
        if func_info:
            suffix = f" ({func_info.filepath.name}:{func_info.lineno})"

        if node in visited:
            lines.append(f"{prefix}{connector}{node} (recursive){suffix}")
            return

        lines.append(f"{prefix}{connector}{node}{suffix}")

        if depth >= max_depth:
            children = adj.get(node, [])
            if children:
                child_prefix = prefix + ("    " if is_last else "│   ")
                lines.append(f"{child_prefix}└── ...")
            return

        visited = visited | {node}
        children = sorted(adj.get(node, []))
        child_prefix = prefix + ("    " if is_last else "│   ")

        for i, child in enumerate(children):
            is_child_last = i == len(children) - 1
            render_node(child, child_prefix, is_child_last, visited, depth + 1)

    # Filter entry points: only those with edges (have children)
    entry_points_with_edges = [
        entry for entry in graph.entry_points if adj.get(entry)
    ]

    # If no entry points have edges, show all entry points
    if not entry_points_with_edges:
        entry_points_with_edges = graph.entry_points[:5]

    # Render each entry point
    for i, entry in enumerate(sorted(entry_points_with_edges)):
        func_info = graph.functions.get(entry)
        suffix = ""
        if func_info:
            suffix = f" ({func_info.filepath.name}:{func_info.lineno})"

        children = sorted(adj.get(entry, []))

        # Skip entry points with no children (unless it's the only one)
        if not children and len(entry_points_with_edges) > 1:
            continue

        lines.append(f"{entry}{suffix}")
        for j, child in enumerate(children):
            is_last = j == len(children) - 1
            render_node(child, "", is_last, {entry}, 1)

        if i < len(entry_points_with_edges) - 1:
            lines.append("")

    return "\n".join(lines)


def format_mermaid(graph: CallGraph, max_nodes: int = 50) -> str:
    """Generate Mermaid flowchart with ELK layout."""
    lines = [
        "```mermaid",
        "---",
        "config:",
        "  layout: elk",
        "---",
        "flowchart TD",
    ]

    # Collect nodes in graph
    nodes_in_graph: Set[str] = set()
    for src, dst in graph.edges:
        nodes_in_graph.add(src)
        nodes_in_graph.add(dst)

    # Limit if too many
    if len(nodes_in_graph) > max_nodes:
        limited: Set[str] = set(graph.entry_points)
        for src, dst in graph.edges:
            if src in graph.entry_points:
                limited.add(dst)
        nodes_in_graph = limited

    def safe_id(name: str) -> str:
        return name.replace(".", "_").replace("-", "_")

    def label(name: str) -> str:
        if len(name) > 30:
            parts = name.split(".")
            if len(parts) > 1:
                return f"{parts[0]}...{parts[-1]}"
        return name

    # Only show entry points that participate in the graph
    entry_points_in_graph = [
        e for e in graph.entry_points if e in nodes_in_graph
    ]

    # Entry points
    lines.append("")
    lines.append("    %% Entry points")
    for entry in entry_points_in_graph:
        lines.append(f'    {safe_id(entry)}["{label(entry)}"]:::entry')

    # Other functions (no special styling - just plain nodes)
    lines.append("")
    lines.append("    %% Functions")
    for name in sorted(nodes_in_graph):
        if name not in entry_points_in_graph:
            sid = safe_id(name)
            lines.append(f'    {sid}["{label(name)}"]')

    # Edges
    lines.append("")
    lines.append("    %% Call relationships")
    seen: Set[Tuple[str, str]] = set()
    for src, dst in graph.edges:
        if src in nodes_in_graph and dst in nodes_in_graph:
            if (src, dst) not in seen:
                lines.append(f"    {safe_id(src)} --> {safe_id(dst)}")
                seen.add((src, dst))

    # Styling
    lines.append("")
    lines.append("    %% Styling")
    lines.append("    classDef entry fill:#4CAF50,stroke:#2E7D32,color:#fff")
    lines.append("```")

    return "\n".join(lines)


def generate_output(
    graph: CallGraph,
    root_path: Path,
    with_mermaid: bool = False,
    max_depth: int = 10,
) -> str:
    """Generate complete output content."""
    lines: List[str] = []

    # Header
    lines.append("# Call Graph")
    lines.append("")
    lines.append(f"**Source:** `{root_path}`  ")
    lines.append(f"**Functions:** {len(graph.functions)}  ")
    lines.append(f"**Entry Points:** {len(graph.entry_points)}  ")
    lines.append(f"**Call Edges:** {len(graph.edges)}")
    lines.append("")

    # Tree section
    lines.append("## Call Tree")
    lines.append("")
    lines.append("```")
    lines.append(format_tree_text(graph, max_depth))
    lines.append("```")
    lines.append("")

    # Optional Mermaid diagram
    if with_mermaid:
        lines.append("## Call Graph Diagram")
        lines.append("")
        lines.append(format_mermaid(graph))
        lines.append("")

    return "\n".join(lines)


# ================================================================
# Rich Output
# ================================================================


def print_stats(graph: CallGraph):
    """Print statistics."""
    table = Table(
        title="Call Graph Analysis",
        box=box.ROUNDED,
        show_header=False,
        title_style="bold cyan",
    )
    table.add_column("Metric", style="dim")
    table.add_column("Value", style="bold")

    table.add_row("Total functions", str(len(graph.functions)))
    table.add_row("Entry points", str(len(graph.entry_points)))
    table.add_row("Call edges", str(len(graph.edges)))

    # Language breakdown
    lang_count: Dict[str, int] = defaultdict(int)
    for func in graph.functions.values():
        lang_count[func.language] += 1

    if len(lang_count) > 1:
        for lang, count in sorted(lang_count.items()):
            table.add_row(f"  {lang}", f"[dim]{count}[/dim]")

    console.print(table)


def print_tree_rich(graph: CallGraph, max_depth: int = 5):
    """Print call tree using Rich."""
    if not graph.entry_points:
        return

    # Build adjacency
    adj: Dict[str, List[str]] = defaultdict(list)
    for src, dst in graph.edges:
        if dst not in adj[src]:
            adj[src].append(dst)

    tree = Tree("[bold]Call Tree[/bold]")

    def add_children(
        parent: Tree, node: str, visited: Set[str], depth: int = 0
    ):
        if depth > max_depth:
            parent.add("[dim]...[/dim]")
            return

        for child in sorted(adj.get(node, [])):
            if child in visited:
                parent.add(f"[dim]{child} (recursive)[/dim]")
            else:
                func = graph.functions.get(child)
                style = "[blue]" if func and func.is_method else "[green]"
                child_tree = parent.add(f"{style}{child}[/]")
                add_children(child_tree, child, visited | {child}, depth + 1)

    for entry in graph.entry_points[:5]:
        func = graph.functions.get(entry)
        loc = (
            f" [dim]({func.filepath.name}:{func.lineno})[/dim]" if func else ""
        )
        entry_tree = tree.add(f"[bold cyan]{entry}[/bold cyan]{loc}")
        add_children(entry_tree, entry, {entry})

    console.print(tree)


# ================================================================
# CLI
# ================================================================

DEFAULT_OUTPUT = "cflow.md"


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cflow",
        description="Code Flow Visualizer - Generate function call graphs for Python",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Examples:
  cflow ./src                          Analyze and output to cflow.md
  cflow ./src/main.py                  Analyze specific file
  cflow ./src --entry main             Start from 'main' function
  cflow ./src --with-mermaid           Include Mermaid diagram in output
  cflow ./src --stdout                 Output to stdout

Supported: Python (.py) - uses AST-based analysis
        """,
    )

    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Directory or file to analyze (default: current directory)",
    )

    parser.add_argument(
        "-e",
        "--entry",
        metavar="FUNC",
        help="Entry point function name (default: auto-detect)",
    )

    parser.add_argument(
        "-o",
        "--output",
        metavar="FILE",
        default=DEFAULT_OUTPUT,
        help=f"Output file (default: {DEFAULT_OUTPUT})",
    )

    parser.add_argument(
        "--stdout",
        action="store_true",
        help="Output to stdout instead of file",
    )

    parser.add_argument(
        "--with-mermaid",
        action="store_true",
        help="Include Mermaid diagram in output",
    )

    parser.add_argument(
        "--max-depth",
        type=int,
        default=10,
        metavar="N",
        help="Maximum call depth to traverse (default: 10)",
    )

    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Suppress progress messages",
    )

    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 0.1.0",
    )

    return parser


def main() -> int:
    parser = create_parser()
    args = parser.parse_args()

    # Validate path
    root_path = Path(args.path).resolve()
    if not root_path.exists():
        console.print(f"[red]Error:[/red] '{args.path}' is not a valid path")
        return 1

    quiet = args.quiet or args.stdout

    # Print scanning message
    if not quiet:
        console.print(f"[green]>[/green] Scanning: [bold]{root_path}[/bold]")

    # Print options being used
    if not quiet:
        if args.entry:
            console.print(
                f"[green]>[/green] Entry point: [cyan]{args.entry}[/cyan]"
            )
        if args.max_depth != 10:
            console.print(
                f"[green]>[/green] Max depth: [cyan]{args.max_depth}[/cyan]"
            )
        if args.with_mermaid:
            console.print(
                "[green]>[/green] Including [magenta]Mermaid diagram[/magenta]"
            )

    # Build call graph
    if not quiet:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            progress.add_task("Building call graph...", total=None)
            graph = build_call_graph(
                root_path,
                entry_function=args.entry,
                max_depth=args.max_depth,
            )
    else:
        graph = build_call_graph(
            root_path,
            entry_function=args.entry,
            max_depth=args.max_depth,
        )

    if not graph.functions:
        console.print("[yellow]No functions found[/yellow]")
        return 0

    if not graph.entry_points:
        console.print("[yellow]Warning:[/yellow] No entry points found")
        if args.entry:
            console.print(f"[dim]Function '{args.entry}' not found[/dim]")
        return 0

    # Print stats only (no tree in terminal)
    if not quiet:
        print_stats(graph)

    # Generate output
    output_content = generate_output(
        graph,
        root_path,
        with_mermaid=args.with_mermaid,
        max_depth=args.max_depth,
    )

    # Write output
    if args.stdout:
        print(output_content)
    else:
        output_path = Path(args.output)
        output_path.write_text(output_content)
        if not quiet:
            console.print(
                f"[green]>[/green] Generated [bold]{args.output}[/bold]"
            )

    return 0


if __name__ == "__main__":
    sys.exit(main())
