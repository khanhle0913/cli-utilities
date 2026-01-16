"""Output formatting for codesynth (Claude Code style)."""

import os

from rich.console import Console

from .utils import format_size


console = Console()


def print_status(message: str, style: str = "info"):
    """Print a status message with consistent formatting."""
    styles = {
        "info": "[cyan]>[/cyan]",
        "success": "[green]>[/green]",
        "warning": "[yellow]![/yellow]",
        "error": "[red]x[/red]",
    }
    prefix = styles.get(style, styles["info"])
    console.print(f"  {prefix} {message}")


def print_scanning(directory: str):
    """Print scanning message."""
    console.print(f"  [dim]Scanning[/dim] {directory}")


def print_detected(dirs: list[str]):
    """Print auto-detected directories."""
    dirs_str = ", ".join(os.path.basename(d) for d in dirs)
    console.print(f"  [dim]Found[/dim] {dirs_str}")


def print_gitignore(path: str, file_patterns: int, dir_patterns: int):
    """Print gitignore info."""
    console.print(
        f"  [dim]Using[/dim] {os.path.basename(path)} [dim]({file_patterns} patterns)[/dim]"
    )


def print_extensions(extensions: list[str]):
    """Print extension filter info."""
    ext_str = ", ".join(f".{e}" for e in extensions)
    console.print(f"  [dim]Filter[/dim] {ext_str}")


def print_files_selected(count: int):
    """Print selected files count."""
    console.print(f"  [dim]Selected[/dim] {count} file(s)")


def print_missing_files(files: list[str]):
    """Print missing files warning."""
    console.print(f"  [yellow]![/yellow] Files not found:")
    for f in files:
        console.print(f"      [dim]{f}[/dim]")


def print_generated(output_file: str):
    """Print generation complete message."""
    console.print(f"  [green]+[/green] Wrote {output_file}")


def print_stats(stats: dict):
    """Print generation statistics in Claude Code style."""
    console.print()
    console.print(f"  {stats['processed_files']} file(s) processed")

    if stats["skipped_files"] > 0:
        skip_parts = []
        if stats["binary_files"] > 0:
            skip_parts.append(f"{stats['binary_files']} binary")
        if stats["oversized_files"] > 0:
            skip_parts.append(f"{stats['oversized_files']} oversized")
        skip_info = ", ".join(skip_parts) if skip_parts else "filtered"
        console.print(
            f"  [dim]{stats['skipped_files']} skipped ({skip_info})[/dim]"
        )

    console.print(f"  [dim]{format_size(stats['processed_size'])} total[/dim]")


def print_file_list(files: list[str], root_dir: str):
    """Print file list with sizes."""
    console.print()
    for f in files:
        rel_path = os.path.relpath(f, root_dir)
        from .utils import get_file_size

        size = get_file_size(f)
        console.print(f"  {rel_path} [dim]({format_size(size)})[/dim]")
    console.print()
    console.print(f"  [dim]{len(files)} file(s)[/dim]")


def print_codebase_stats(total: int, binary: int, text: int, size: int):
    """Print codebase statistics."""
    console.print()
    console.print(f"  {total} file(s) total")
    console.print(f"  [dim]{text} text, {binary} binary[/dim]")
    console.print(f"  [dim]{format_size(size)} total[/dim]")


def show_help():
    """Display beautiful help page with rich formatting."""
    console.print()
    console.print(
        "  [bold]codesynth[/bold] [dim]- synthesize codebase to LLM-friendly markdown[/dim]"
    )
    console.print()

    # Quick start
    console.print("  [dim]Quick Start[/dim]")
    console.print(
        "    codesynth .                    [dim]scan current directory[/dim]"
    )
    console.print(
        "    codesynth . -t                 [dim]include directory tree[/dim]"
    )
    console.print(
        "    codesynth . --clipboard        [dim]copy to clipboard[/dim]"
    )
    console.print()

    # Common use cases
    console.print("  [dim]Use Cases[/dim]")
    console.print("    [bold]Python project[/bold]")
    console.print("    codesynth --extensions py -e tests/* -t")
    console.print()
    console.print("    [bold]Frontend project[/bold]")
    console.print("    codesynth --extensions js ts tsx --max-size 50KB")
    console.print()
    console.print("    [bold]Specific files[/bold]")
    console.print("    codesynth -f src/main.py src/utils.py -t")
    console.print()

    # Options grouped
    console.print("  [dim]Options[/dim]")
    console.print("    [bold]Output[/bold]")
    console.print(
        "    -o FILE              output file [dim](codesynth.md)[/dim]"
    )
    console.print("    --clipboard          copy to clipboard")
    console.print("    --stdout             print to terminal")
    console.print("    -t, --tree           include directory tree")
    console.print("    -s, --size           show file sizes")
    console.print()
    console.print("    [bold]Selection[/bold]")
    console.print("    -f FILES             specific files only")
    console.print("    --extensions EXTS    filter by extension")
    console.print("    -e, --exclude PATS   exclude patterns")
    console.print("    --max-depth N        max directory depth")
    console.print("    -i FILE              custom ignore file [dim](.gitignore)[/dim]")
    console.print("    --no-detect          disable auto-detect for '.'")
    console.print()
    console.print("    [bold]Content[/bold]")
    console.print(
        "    --max-size SIZE      max file size [dim](e.g., 100KB)[/dim]"
    )
    console.print("    --include-binary     include binary files")
    console.print()
    console.print("    [bold]Analysis[/bold]")
    console.print("    --list-files         list files only")
    console.print("    --stats-only         statistics only")
    console.print()
    console.print("    [bold]Other[/bold]")
    console.print("    --no-gitignore       ignore .gitignore")
    console.print("    -q                   quiet mode")
    console.print()
    console.print("    [bold]Reverse[/bold]")
    console.print("    --reverse FILE       reverse codesynth markdown")
    console.print("    --output-dir DIR     output directory for reverse")
    console.print()

    # Tips
    console.print("  [dim]Tips[/dim]")
    console.print(
        "    Run [bold]codesynth[/bold] without args for interactive mode"
    )
    console.print()


def print_help_hint():
    """Print hint about help command."""
    console.print("  [dim]Use -h or --help for more options[/dim]")
    console.print()
