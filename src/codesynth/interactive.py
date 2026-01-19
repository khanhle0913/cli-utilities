"""Minimal interactive mode for codesynth."""

import os
import sys

from rich.console import Console

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

    # 4. Extensions
    console.print("[dim]comma/space separated | leave blank for all[/dim]")
    extensions = inquirer.text(  # type: ignore
        message="Extensions",
        default="",
    ).execute()
    clear_lines(2)
    if extensions:
        ext_list = [
            ext.strip().lstrip(".")
            for ext in extensions.replace(",", " ").split()
            if ext.strip()
        ]
        if ext_list:
            args.append("--extensions")
            args.extend(ext_list)

    # 5. Exclude patterns
    console.print("[dim]comma/space separated | leave blank for none[/dim]")
    exclude_patterns = inquirer.text(  # type: ignore
        message="Exclude patterns",
        default="",
    ).execute()
    clear_lines(2)
    if exclude_patterns:
        exclude_list = [
            pattern.strip()
            for pattern in exclude_patterns.replace(",", " ").split()
            if pattern.strip()
        ]
        if exclude_list:
            args.append("-e")
            args.extend(exclude_list)

    # 6. Max file size
    console.print("[dim]e.g., 100KB, 1MB | leave blank for none[/dim]")
    max_size = inquirer.text(  # type: ignore
        message="Max file size",
        default="",
    ).execute()
    clear_lines(2)
    if max_size:
        args.append("--max-size")
        args.append(max_size.strip())

    # 7. Max depth
    console.print("[dim]integer | leave blank for none[/dim]")
    max_depth = inquirer.text(  # type: ignore
        message="Max depth",
        default="",
    ).execute()
    clear_lines(2)
    if max_depth:
        args.append("--max-depth")
        args.append(max_depth.strip())

    # Show command
    cmd = "codesynth " + " ".join(args)
    console.print(f"  [dim]>[/dim] {cmd}")
    console.print()

    return args
