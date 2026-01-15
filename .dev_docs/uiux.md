# CLI UX Design Guidelines

Design principles for CLI utilities in this project, inspired by Claude Code's minimal aesthetic.

## Philosophy

**Less is more.** Users don't need to be told everything - they need to see what matters.

### Core Principles

1. **Quiet by default** - Only show essential information
2. **Progressive disclosure** - More details available on request (`--verbose`)
3. **Scannable output** - Important info at a glance
4. **No visual noise** - Avoid boxes, borders, heavy decorations

## Visual Language

### Prefixes

Use single-character prefixes for status indication:

| Prefix | Meaning         | Usage                      |
| ------ | --------------- | -------------------------- |
| `+`    | Success/Added   | File written, item added   |
| `-`    | Removed         | File deleted, item removed |
| `>`    | Action/Progress | Currently doing something  |
| `!`    | Warning         | Non-fatal issue            |
| `x`    | Error           | Fatal issue                |
| `?`    | Prompt          | Waiting for input          |

Example:

```
  + Wrote output.md
  ! 2 files skipped (binary)
  x Not a directory: /invalid/path
```

### Indentation

- **2-space indent** for all output lines
- Aligns with prefix + space (e.g., ` +`)
- Creates clean left edge for scanning

```
  Found src, lib
  Scanning /path/to/project
  Using .gitignore (5 patterns)
  + Wrote codesynth.md

  10 file(s) processed
  65.2 KB total
```

### Text Styling

Use Rich markup sparingly:

| Style                  | Usage                    |
| ---------------------- | ------------------------ |
| `[dim]...[/dim]`       | Secondary info, metadata |
| `[bold]...[/bold]`     | Key values, filenames    |
| `[green]...[/green]`   | Success states           |
| `[yellow]...[/yellow]` | Warnings                 |
| `[red]...[/red]`       | Errors                   |
| `[cyan]...[/cyan]`     | Highlighted values       |

**Rules:**

- Never color entire lines
- Color only the significant part
- Dim is better than hiding

Example:

```python
console.print(f"  [dim]Scanning[/dim] {directory}")
console.print(f"  + Wrote {filename}")
console.print(f"  [dim]{count} file(s) total[/dim]")
```

## Output Patterns

### Status Messages

Short, action-oriented:

```
  Found src, lib                    # What was detected
  Scanning /path/to/project         # What's happening
  Using .gitignore (5 patterns)     # Configuration info
```

### Completion Messages

Clear success indicator + result:

```
  + Wrote output.md                 # Primary result
                                    # Empty line for separation
  10 file(s) processed              # Key metric
  65.2 KB total                     # Secondary metric
```

### Warnings

Non-intrusive but visible:

```
  ! Files not found:
      missing.py
      another.py
```

### Errors

Clear and actionable:

```
  x Not a directory: /invalid/path
  x No valid files specified
```

## Statistics

### Simple Format

Avoid tables. Use aligned text:

```
  15 file(s) total
  13 text, 2 binary
  45.2 KB total
```

### With Context

Group related info:

```
  10 file(s) processed
  2 skipped (binary)
  65.2 KB total
```

## Progress Indication

### For Fast Operations

Use transient spinner that disappears:

```python
with Progress(
    SpinnerColumn(),
    TextColumn("[dim]{task.description}[/dim]"),
    transient=True,
    console=console,
) as progress:
    progress.add_task("Collecting", total=None)
```

### For Longer Operations

Add minimal progress bar:

```python
with Progress(
    SpinnerColumn(),
    TextColumn("[dim]{task.description}[/dim]"),
    BarColumn(bar_width=20),
    TextColumn("[dim]{task.percentage:>3.0f}%[/dim]"),
    transient=True,
    console=console,
) as progress:
    task = progress.add_task("Writing", total=len(files))
```

## Help Display

### Quick Help (no args)

Show immediately usable examples:

```
  codesynth - synthesize codebase to markdown

  Usage
    codesynth [options] [directory]
    codesynth -f <files...> [options]

  Examples
    codesynth ./my-project
    codesynth -f src/main.py src/utils.py
    codesynth -e py js --with-tree

  Output
    -o, --output <file>    output file (codesynth.md)
    --stdout               output to stdout
    ...
```

### Structure

1. **One-liner description**
2. **Usage patterns**
3. **Common examples**
4. **Grouped options** (most used first)
5. **Pointer to full docs**

## Anti-Patterns

### Avoid

```
# Too much decoration
╭─────────────────────────────────╮
│  Processing complete!           │
╰─────────────────────────────────╯

# Too verbose
[INFO] Starting file collection process...
[INFO] Found 10 files in directory
[INFO] Applying gitignore patterns...
[SUCCESS] File collection complete!

# Unnecessary colors
[green]>[/green] [cyan]Scanning[/cyan] [bold]/path/to/dir[/bold]

# Emoji clutter
✨ Starting process...
📁 Found 10 files
✅ Complete!
```

### Prefer

```
  Found 10 files
  Scanning /path/to/dir
  + Done

  10 file(s) processed
```

## Implementation

### Output Module Structure

```python
# output.py

from rich.console import Console

console = Console()

def print_status(message: str, style: str = "info"):
    """Print a status message."""
    prefixes = {
        "info": "[dim]>[/dim]",
        "success": "[green]+[/green]",
        "warning": "[yellow]![/yellow]",
        "error": "[red]x[/red]",
    }
    prefix = prefixes.get(style, prefixes["info"])
    console.print(f"  {prefix} {message}")

def print_scanning(directory: str):
    """Print scanning message."""
    console.print(f"  [dim]Scanning[/dim] {directory}")

def print_generated(filename: str):
    """Print generation complete."""
    console.print(f"  [green]+[/green] Wrote {filename}")

def print_stats(processed: int, size: str):
    """Print final statistics."""
    console.print()
    console.print(f"  {processed} file(s) processed")
    console.print(f"  [dim]{size} total[/dim]")
```

### Consistency Checklist

- [ ] All output lines indented with 2 spaces
- [ ] Single-char prefixes for status
- [ ] Dim for secondary information
- [ ] No boxes or borders
- [ ] No emoji
- [ ] Transient progress bars
- [ ] Statistics in plain text format
- [ ] Error messages are actionable

## Examples

### Good Output Flow

```
  codesynth - synthesize codebase to markdown

  Usage
    codesynth [options] [directory]
  ...
```

```
  Found src
  Scanning /home/user/project/src
  Using .gitignore (5 patterns)
  + Wrote codesynth.md

  10 file(s) processed
  65.2 KB total
```

```
  ! Files not found:
      missing.py

  Selected 3 file(s)
  + Wrote output.md

  3 file(s) processed
  12.5 KB total
```

```
  x Not a directory: /invalid
```

This style ensures output is:

- **Scannable** - Key info stands out
- **Quiet** - No noise
- **Professional** - Clean aesthetic
- **Consistent** - Same patterns everywhere
