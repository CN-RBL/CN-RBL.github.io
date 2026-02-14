# -*- coding: utf-8 -*-

import markdown
import platform
import importlib.metadata
from rich.logging import RichHandler
import logging

def main() -> int:
    logging.basicConfig(level=logging.DEBUG, format="%(message)s", handlers=[RichHandler()])
    logging.info("Starting main process.")
    logging.debug(f"Python version: {platform.python_version()}")
    logging.debug(f"markdown module version: {markdown.__version__}")
    logging.debug(f"rich module version: {importlib.metadata.version('rich')}")
    return 0

if __name__ == '__main__':
    exit(main())
