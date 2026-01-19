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
	@if [ -x .venv/bin/python ]; then .venv/bin/python install.py; \
	elif [ -x venv/bin/python ]; then venv/bin/python install.py; \
	else uv run install.py; fi

uninstall:
	@if [ -x .venv/bin/python ]; then .venv/bin/python install.py --uninstall; \
	elif [ -x venv/bin/python ]; then venv/bin/python install.py --uninstall; \
	else uv run install.py --uninstall; fi

list:
	@if [ -x .venv/bin/python ]; then .venv/bin/python install.py --list; \
	elif [ -x venv/bin/python ]; then venv/bin/python install.py --list; \
	else uv run install.py --list; fi

lint:
	@uv run pyright src/ install.py
