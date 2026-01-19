#!/usr/bin/env python3
"""
Cross-platform installation script for My Utilities.
Works on Linux, macOS, and Windows.

Usage:
    uv run install.py          # Install
    uv run install.py --uninstall   # Uninstall
    uv run install.py --list        # List utilities
"""

import os
import sys
import stat
import shutil
import argparse
from pathlib import Path

# ================================================================
# Configuration
# ================================================================

# Utility definitions: source_file -> alias_name
UTILITIES = {
    "codesynth.py": "codesynth",
    "cflow.py": "cflow",
}

# ================================================================
# Platform Detection
# ================================================================

IS_WINDOWS = sys.platform == "win32"
HOME = Path.home()
INSTALL_DIR = HOME / ".local" / "bin"
SRC_DIR = Path(__file__).parent / "src"


# Colors for terminal output
class Colors:
    GREEN = "\033[92m" if not IS_WINDOWS else ""
    YELLOW = "\033[93m" if not IS_WINDOWS else ""
    RED = "\033[91m" if not IS_WINDOWS else ""
    CYAN = "\033[96m" if not IS_WINDOWS else ""
    RESET = "\033[0m" if not IS_WINDOWS else ""

    @classmethod
    def enable_windows_colors(cls):
        """Enable ANSI colors on Windows 10+"""
        if IS_WINDOWS:
            try:
                import ctypes

                kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined]
                kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
                cls.GREEN = "\033[92m"
                cls.YELLOW = "\033[93m"
                cls.RED = "\033[91m"
                cls.CYAN = "\033[96m"
                cls.RESET = "\033[0m"
            except Exception:
                pass


def print_status(msg: str, color: str = Colors.GREEN):
    print(f"{color}>{Colors.RESET} {msg}")


def print_error(msg: str):
    print(f"{Colors.RED}Error:{Colors.RESET} {msg}")


# ================================================================
# Installation Functions
# ================================================================


def check_uv() -> bool:
    """Check if uv is installed."""
    return shutil.which("uv") is not None


def create_wrapper_unix(
    src_path: Path, target_path: Path, project_dir: Path, venv_python: Path | None
):
    """Create shell wrapper for Unix systems."""
    if venv_python:
        content = f"""#!/bin/bash
exec "{venv_python}" "{src_path}" "$@"
"""
    else:
        content = f"""#!/bin/bash
exec uv run --project "{project_dir}" "{src_path}" "$@"
"""
    target_path.write_text(content)
    # Make executable
    target_path.chmod(
        target_path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
    )


def create_wrapper_windows(
    src_path: Path, target_path: Path, project_dir: Path, venv_python: Path | None
):
    """Create batch wrapper for Windows."""
    if venv_python:
        content = f"""@echo off
"{venv_python}" "{src_path}" %*
"""
    else:
        content = f"""@echo off
uv run --project "{project_dir}" "{src_path}" %*
"""
    target_path.with_suffix(".cmd").write_text(content)


def get_venv_python(project_dir: Path) -> Path | None:
    """Find a Python interpreter in a local venv."""
    venv_dirs = [project_dir / ".venv", project_dir / "venv"]
    for venv_dir in venv_dirs:
        python_path = (
            venv_dir / "Scripts" / "python.exe"
            if IS_WINDOWS
            else venv_dir / "bin" / "python"
        )
        if python_path.exists():
            return python_path
    return None


def install():
    """Install all utilities."""
    if not check_uv():
        print_error("'uv' is not installed.")
        if IS_WINDOWS:
            print("Install with: irm https://astral.sh/uv/install.ps1 | iex")
        else:
            print(
                "Install with: curl -LsSf https://astral.sh/uv/install.sh | sh"
            )
        return 1

    # Sync dependencies first
    print_status("Syncing dependencies...")
    import subprocess

    result = subprocess.run(
        ["uv", "sync"],
        cwd=Path(__file__).parent,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print_error("Failed to sync dependencies")
        print(result.stderr)
        return 1

    # Create install directory
    INSTALL_DIR.mkdir(parents=True, exist_ok=True)

    platform_name = (
        "Windows"
        if IS_WINDOWS
        else ("macOS" if sys.platform == "darwin" else "Linux")
    )
    print_status(f"Installing utilities to {INSTALL_DIR} ({platform_name})")

    for src_file, alias_name in UTILITIES.items():
        src_path = SRC_DIR / src_file
        if not src_path.exists():
            print(
                f"  {Colors.YELLOW}[!]{Colors.RESET} Skipping {alias_name} (source not found)"
            )
            continue

        project_dir = Path(__file__).parent.resolve()
        venv_python = get_venv_python(project_dir)
        if IS_WINDOWS:
            target_path = INSTALL_DIR / alias_name
            create_wrapper_windows(
                src_path.resolve(), target_path, project_dir, venv_python
            )
        else:
            target_path = INSTALL_DIR / alias_name
            create_wrapper_unix(
                src_path.resolve(), target_path, project_dir, venv_python
            )

        print(f"  {Colors.CYAN}[+]{Colors.RESET} Installed {alias_name}")

    print()
    print_status("Installation complete!")
    print()

    # Check PATH
    path_dirs = os.environ.get("PATH", "").split(os.pathsep)
    if str(INSTALL_DIR) not in path_dirs:
        print(
            f"{Colors.YELLOW}WARNING:{Colors.RESET} {INSTALL_DIR} is not in your PATH."
        )
        print()
        if IS_WINDOWS:
            print("Add to PATH (PowerShell):")
            print(f'  $env:Path += ";{INSTALL_DIR}"')
            print(
                f"  [Environment]::SetEnvironmentVariable('Path', $env:Path, 'User')"
            )
        else:
            shell = os.environ.get("SHELL", "")
            if "fish" in shell:
                print("Add to PATH (Fish):")
                print(f"  fish_add_path {INSTALL_DIR}")
            else:
                print("Add to PATH (Bash/Zsh):")
                print(f'  export PATH="{INSTALL_DIR}:$PATH"')
        print()

    return 0


def uninstall():
    """Uninstall all utilities."""
    print_status("Uninstalling utilities...", Colors.YELLOW)

    for src_file, alias_name in UTILITIES.items():
        if IS_WINDOWS:
            target_path = INSTALL_DIR / f"{alias_name}.cmd"
        else:
            target_path = INSTALL_DIR / alias_name

        if target_path.exists():
            target_path.unlink()
            print(f"  {Colors.YELLOW}[-]{Colors.RESET} Removed {alias_name}")

    print()
    print_status("Uninstallation complete!")
    return 0


def list_utilities():
    """List available utilities."""
    print("Available utilities:")
    print()
    for src_file, alias_name in UTILITIES.items():
        src_path = SRC_DIR / src_file
        status = (
            f"{Colors.GREEN}OK{Colors.RESET}"
            if src_path.exists()
            else f"{Colors.RED}MISSING{Colors.RESET}"
        )
        print(f"  {alias_name} ({src_file}) [{status}]")
    print()
    return 0


# ================================================================
# Main
# ================================================================


def main():
    Colors.enable_windows_colors()

    parser = argparse.ArgumentParser(
        description="Cross-platform installer for My Utilities"
    )
    parser.add_argument(
        "--uninstall", action="store_true", help="Uninstall utilities"
    )
    parser.add_argument(
        "--list", action="store_true", help="List available utilities"
    )
    args = parser.parse_args()

    if args.list:
        return list_utilities()
    elif args.uninstall:
        return uninstall()
    else:
        return install()


if __name__ == "__main__":
    sys.exit(main())
