# CLI Utilities

A collection of CLI utilities for daily development workflows.

## Quick Start

### Prerequisites

Install `uv` package manager:

**Linux/macOS:**

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows (PowerShell):**

```powershell
irm https://astral.sh/uv/install.ps1 | iex
```

### Installation

**Linux/macOS:**

```bash
make install
```

**Windows (PowerShell):**

```powershell
uv run install.py
```

### Setup PATH

After installation, add `~/.local/bin` to your PATH:

**Bash/Zsh** (add to `~/.bashrc` or `~/.zshrc`):

```bash
export PATH="$HOME/.local/bin:$PATH"
```

**Fish** (run once):

```fish
fish_add_path ~/.local/bin
```

**Windows PowerShell:**

```powershell
# Current session
$env:Path += ";$env:USERPROFILE\.local\bin"

# Permanent (run once)
[Environment]::SetEnvironmentVariable('Path', $env:Path + ";$env:USERPROFILE\.local\bin", 'User')
```

### Verify Installation

```bash
codesynth --help
```

### Uninstall

**Linux/macOS:**

```bash
make uninstall
```

**Windows (PowerShell):**

```powershell
uv run install.py --uninstall
```

## Available Utilities

| Utility     | Description                                    | Usage Guide                            |
| ----------- | ---------------------------------------------- | -------------------------------------- |
| `codesynth` | Synthesize codebase into LLM-friendly markdown | [docs/codesynth.md](docs/codesynth.md) |
