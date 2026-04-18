#!/usr/bin/env python3
"""WinPyAI -- AI Desktop Chat Application

Entry point for the application. Run with:

    python main.py

Requires Python 3.10+, PyQt6, and a running Ollama instance.
"""

if __name__ == "__main__":
    from winpyai.app import run_app

    run_app()
