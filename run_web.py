#!/usr/bin/env python3
"""Launch the Streamlit GUI from a frozen or source checkout."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def app_dir() -> Path:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent


def main() -> None:
    os.chdir(app_dir())
    sys.path.insert(0, str(app_dir()))
    from streamlit.web.cli import main as st_main

    sys.argv = ["streamlit", "run", str(app_dir() / "streamlit_app.py"), "--server.headless=true"]
    st_main()


if __name__ == "__main__":
    main()
