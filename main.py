#!/usr/bin/env python3
"""
Merchant Document Processing Pipeline
Premium GUI Version - Main Entry Point
"""

import sys
import logging
from pathlib import Path

# Base directory is wherever this script lives
BASE_DIR = Path(__file__).resolve().parent

# Add the src/ folder to sys.path so you can import gui.premium_gui
SRC_DIR = BASE_DIR / "src"
sys.path.insert(0, str(SRC_DIR))

def setup_application():
    """Create needed dirs and configure logging."""
    # ensure input/, output/ and logs/ exist next to this script
    for folder in ("input", "output", "logs"):
        (BASE_DIR / folder).mkdir(parents=True, exist_ok=True)

    # configure a rolling file + console logger
    log_path = BASE_DIR / "logs" / "application.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(log_path, encoding="utf-8"),
            logging.StreamHandler(sys.stdout)
        ]
    )

def main():
    """Main entry point: setup then launch GUI."""
    try:
        setup_application()

        # now import your GUI launcher from src/gui/premium_gui.py
        from src.gui.premium_gui import launch_application
        launch_application()

    except ImportError as e:
        logging.error("Import Error: %s", e)
        print("Import Error:", e)
        print("Did you pip install -r requirements.txt?")
        sys.exit(1)

    except Exception:
        logging.exception("Unhandled application error")
        sys.exit(1)

if __name__ == "__main__":
    main()
