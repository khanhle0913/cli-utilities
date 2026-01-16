"""Minimal interactive mode for codesynth."""

import os
import sys

from .rich_compat import Console

from .collector import detect_source_directories

console = Console()


def clear_lines(n: int = 1):
    """Clear n lines above cursor."""
    for _ in range(n):
        sys.stdout.write("\033[F")
        sys.stdout.write("\033[K")
    sys.stdout.flush()


def interactive_mode() -> list[str]:
    """Minimal interactive CLI - directory, tree, output only."""
    from InquirerPy import inquirer  # type: ignore

    args: list[str] = []
    cwd = os.getcwd()

    # Detect source directories
    detected = detect_source_directories(cwd)
    detected_names = [os.path.basename(d) for d in detected] if detected else []

    # 1. Directory selection
    dir_choices: list[dict[str, str]] = [{"name": ". (current)", "value": "."}]
    for name in detected_names:
        dir_choices.append({"name": f"{name}", "value": name})

    default_dir = detected_names[0] if detected_names else "."
    console.print("[dim]arrows: navigate | enter: confirm[/dim]")
    selected_dir = inquirer.select(  # type: ignore
        message="Directory",
        choices=dir_choices,
        default=default_dir,
        pointer=">",
    ).execute()

    clear_lines(2)
    args.append(selected_dir)

    # 2. Include tree?
    console.print("[dim]arrows: navigate | enter: confirm[/dim]")
    include_tree = inquirer.select(  # type: ignore
        message="Include tree",
        choices=[
            {"name": "yes", "value": True},
            {"name": "no", "value": False},
        ],
        default=True,
        pointer=">",
    ).execute()

    clear_lines(2)
    if include_tree:
        args.append("-t")

    # 3. Output
    console.print("[dim]arrows: navigate | enter: confirm[/dim]")
    output = inquirer.select(  # type: ignore
        message="Output",
        choices=[
            {"name": "codesynth.md", "value": "file"},
            {"name": "clipboard", "value": "clipboard"},
        ],
        default="file",
        pointer=">",
    ).execute()

    clear_lines(2)
    if output == "clipboard":
        args.append("--clipboard")

    # Show command
    cmd = "codesynth " + " ".join(args)
    console.print(f"  [dim]>[/dim] {cmd}")
    console.print()

    return args
