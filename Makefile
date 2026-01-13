# ================================================================
# CLI Utilities - Makefile
# ================================================================
# Cross-platform installation via install.py
# This Makefile provides convenient shortcuts for Linux/macOS users.
# ================================================================

.PHONY: install uninstall list lint help

help:
	@echo "================================================================"
	@echo "  CLI Utilities"
	@echo "================================================================"
	@echo ""
	@echo "Usage:"
	@echo "  make install      Install all utilities"
	@echo "  make uninstall    Remove all utilities"
	@echo "  make list         List available utilities"
	@echo "  make lint         Run type checking"
	@echo ""

install:
	@uv run install.py

uninstall:
	@uv run install.py --uninstall

list:
	@uv run install.py --list

lint:
	@uv run pyright src/ install.py
