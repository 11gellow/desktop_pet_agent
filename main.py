#!/usr/bin/env python3
"""
Desktop Pet Agent - Entry Point

Usage:
    python main.py

Create a .env file in the project root with your LLM_API_KEY to connect to
DeepSeek or any OpenAI-compatible API.  Without it, the app uses a mock LLM.

Example .env:
    LLM_API_KEY=sk-your-deepseek-key
    LLM_BASE_URL=https://api.deepseek.com/v1
    LLM_MODEL=deepseek-chat
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path


def _load_dotenv(path: Path) -> None:
    """Load key=value pairs from a .env file into os.environ."""
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key, value = key.strip(), value.strip()
        if key and key not in os.environ:  # don't override existing env vars
            os.environ[key] = value


# Load .env from project root BEFORE any other imports so config can read it
_load_dotenv(Path(__file__).resolve().parent / ".env")

import qasync
from PySide6.QtWidgets import QApplication

from src.app import Application


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("DesktopPetAgent")
    app.setOrganizationName("DesktopPet")

    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)

    application = Application()
    application.run()

    with loop:
        loop.run_forever()


if __name__ == "__main__":
    main()
