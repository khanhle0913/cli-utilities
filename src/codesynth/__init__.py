"""
codesynth - Synthesize codebase into LLM-friendly markdown.
"""

import os
import sys
from typing import List

from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

from .cli import create_parser
from .parser import GitignoreParser
from .collector import detect_source_directories, collect_files_filtered
from .generator import generate_markdown
from .utils import get_file_size, is_binary_file, format_size
from .output import (
    console,
    print_scanning,
    print_detected,
    print_gitignore,
    print_extensions,
    print_files_selected,
    print_missing_files,
    print_generated,
    print_stats,
    print_file_list,
    print_codebase_stats,
    show_help,
    print_help_hint,
)
from .interactive import interactive_mode


def copy_to_clipboard(text: str) -> bool:
    """Copy text to clipboard using pyperclip. Returns True on success."""
    try:
        import pyperclip

        pyperclip.copy(text)
        return True
    except Exception:
        return False


def main() -> int:
    """Main entry point."""
    # Custom help handling
    if len(sys.argv) == 2 and sys.argv[1] in ["-h", "--help", "-help"]:
        show_help()
        return 0

    # Interactive mode if no arguments
    if len(sys.argv) == 1:
        try:
            args_list = interactive_mode()
            if not args_list:
                return 0
            # Re-parse with interactive args
            sys.argv = ["codesynth"] + args_list
        except KeyboardInterrupt:
            console.print("\n  [dim]Cancelled[/dim]")
            return 0

    parser = create_parser()
    args = parser.parse_args()

    # Validate directory
    if not os.path.isdir(args.directory):
        console.print(f"  [red]x[/red] Not a directory: {args.directory}")
        return 1

    # Handle clipboard - treat as stdout but capture and copy
    clipboard_mode = args.clipboard
    if clipboard_mode:
        args.stdout = True

    quiet = args.quiet or args.stdout

    # Handle --files mode
    if args.files:
        return handle_files_mode(args, quiet, clipboard_mode)

    # Regular directory scan mode
    return handle_scan_mode(args, quiet, clipboard_mode)


def handle_files_mode(args, quiet: bool, clipboard: bool = False) -> int:
    """Handle --files mode: specific files only."""
    files: List[str] = []
    missing_files: List[str] = []

    for file_path in args.files:
        if os.path.isabs(file_path):
            full_path = file_path
        else:
            full_path = os.path.join(args.directory, file_path)

        if os.path.isfile(full_path):
            files.append(os.path.abspath(full_path))
        else:
            missing_files.append(file_path)

    if missing_files and not quiet:
        print_missing_files(missing_files)

    if not files:
        console.print("  [red]x[/red] No valid files specified")
        return 1

    if not quiet:
        print_files_selected(len(files))

    # Collect all files for tree if needed
    tree_files = None
    if args.with_tree:
        if args.no_gitignore:
            ignore_parser = GitignoreParser.empty()
        else:
            ignore_parser = GitignoreParser(args.directory, args.ignore_file)

        tree_files = collect_files_filtered(
            args.directory,
            ignore_parser,
            extensions=None,
            exclude_patterns=None,
            max_depth=None,
        )

    # List files mode
    if args.list_files:
        print_file_list(files, args.directory)
        return 0

    # Stats only mode
    if args.stats_only:
        total_size = sum(get_file_size(f) for f in files)
        binary_count = sum(1 for f in files if is_binary_file(f)[0])
        print_codebase_stats(
            len(files), binary_count, len(files) - binary_count, total_size
        )
        return 0

    # Generate output
    if not quiet:
        with Progress(
            SpinnerColumn(),
            TextColumn("[dim]{task.description}[/dim]"),
            BarColumn(bar_width=20),
            TextColumn("[dim]{task.percentage:>3.0f}%[/dim]"),
            transient=True,
            console=console,
        ) as progress:
            task = progress.add_task("Writing", total=len(files))
            stats = generate_markdown(
                files,
                args.directory,
                args.output,
                max_file_size=args.max_size,
                include_binary=args.include_binary,
                show_tree=args.with_tree,
                show_size=args.with_size,
                stdout=args.stdout and not clipboard,
                tree_files=tree_files,
                return_content=clipboard,
            )
            progress.update(task, completed=len(files))

        if clipboard and "content" in stats:
            if copy_to_clipboard(stats["content"]):
                console.print("  [green]+[/green] Copied to clipboard")
            else:
                console.print(
                    "  [yellow]![/yellow] Clipboard not available, printing to stdout"
                )
                print(stats["content"])
        elif not args.stdout:
            print_generated(args.output)
    else:
        stats = generate_markdown(
            files,
            args.directory,
            args.output,
            max_file_size=args.max_size,
            include_binary=args.include_binary,
            show_tree=args.with_tree,
            show_size=args.with_size,
            stdout=args.stdout and not clipboard,
            tree_files=tree_files if args.with_tree else None,
            return_content=clipboard,
        )

        if clipboard and "content" in stats:
            if copy_to_clipboard(stats["content"]):
                console.print("  [green]+[/green] Copied to clipboard")
            else:
                console.print("  [yellow]![/yellow] Clipboard not available")
                print(stats["content"])

    if not quiet and not clipboard:
        print_stats(stats)
        print_help_hint()

    return 0


def handle_scan_mode(args, quiet: bool, clipboard: bool = False) -> int:
    """Handle regular directory scan mode."""
    # Determine directories to scan
    scan_directories: List[str] = []
    user_specified_dir = args.directory != "."

    if user_specified_dir:
        scan_directories = [args.directory]
        root_dir = args.directory
        tree_root = args.directory
    else:
        detected = detect_source_directories(args.directory)
        if detected:
            scan_directories = detected
            # root_dir = cwd for file paths, tree_root = detected dir for tree
            root_dir = args.directory
            tree_root = detected[0] if len(detected) == 1 else args.directory
            if not quiet:
                print_detected(detected)
        else:
            scan_directories = [args.directory]
            root_dir = args.directory
            tree_root = args.directory

    if not quiet:
        for d in scan_directories:
            print_scanning(os.path.abspath(d))

    # Parse gitignore
    if args.no_gitignore:
        ignore_parser = GitignoreParser.empty()
    else:
        ignore_parser = GitignoreParser(args.directory, args.ignore_file)
        if not quiet and ignore_parser.gitignore_path:
            print_gitignore(
                ignore_parser.gitignore_path,
                len(ignore_parser.patterns),
                len(ignore_parser.dir_patterns),
            )

    # Normalize extensions
    extensions = None
    if args.extensions:
        extensions = [ext.lstrip(".").lower() for ext in args.extensions]
        if not quiet:
            print_extensions(extensions)

    # Collect files
    files: List[str] = []

    if not quiet:
        with Progress(
            SpinnerColumn(),
            TextColumn("[dim]{task.description}[/dim]"),
            transient=True,
            console=console,
        ) as progress:
            progress.add_task("Collecting", total=None)
            for scan_dir in scan_directories:
                dir_files = collect_files_filtered(
                    scan_dir,
                    ignore_parser,
                    extensions=extensions,
                    exclude_patterns=args.exclude,
                    max_depth=args.max_depth,
                )
                files.extend(dir_files)
    else:
        for scan_dir in scan_directories:
            dir_files = collect_files_filtered(
                scan_dir,
                ignore_parser,
                extensions=extensions,
                exclude_patterns=args.exclude,
                max_depth=args.max_depth,
            )
            files.extend(dir_files)

    files = sorted(set(files))

    if not files:
        console.print("  [yellow]![/yellow] No files found")
        return 0

    # List files mode
    if args.list_files:
        print_file_list(files, root_dir)
        return 0

    # Stats only mode
    if args.stats_only:
        total_size = sum(get_file_size(f) for f in files)
        binary_count = sum(1 for f in files if is_binary_file(f)[0])
        print_codebase_stats(
            len(files), binary_count, len(files) - binary_count, total_size
        )
        return 0

    # Generate output
    if not quiet:
        with Progress(
            SpinnerColumn(),
            TextColumn("[dim]{task.description}[/dim]"),
            BarColumn(bar_width=20),
            TextColumn("[dim]{task.percentage:>3.0f}%[/dim]"),
            transient=True,
            console=console,
        ) as progress:
            task = progress.add_task("Writing", total=len(files))
            stats = generate_markdown(
                files,
                root_dir,
                args.output,
                max_file_size=args.max_size,
                include_binary=args.include_binary,
                show_tree=args.with_tree,
                show_size=args.with_size,
                stdout=args.stdout and not clipboard,
                tree_root=tree_root,
                return_content=clipboard,
            )
            progress.update(task, completed=len(files))

        if clipboard and "content" in stats:
            if copy_to_clipboard(stats["content"]):
                console.print("  [green]+[/green] Copied to clipboard")
            else:
                console.print("  [yellow]![/yellow] Clipboard not available")
                print(stats["content"])
        elif not args.stdout:
            print_generated(args.output)
    else:
        stats = generate_markdown(
            files,
            root_dir,
            args.output,
            max_file_size=args.max_size,
            include_binary=args.include_binary,
            show_tree=args.with_tree,
            show_size=args.with_size,
            stdout=args.stdout and not clipboard,
            tree_root=tree_root,
            return_content=clipboard,
        )

        if clipboard and "content" in stats:
            if copy_to_clipboard(stats["content"]):
                console.print("  [green]+[/green] Copied to clipboard")
            else:
                console.print("  [yellow]![/yellow] Clipboard not available")
                print(stats["content"])

    if not quiet and not clipboard:
        print_stats(stats)
        print_help_hint()

    return 0


if __name__ == "__main__":
    exit(main())
