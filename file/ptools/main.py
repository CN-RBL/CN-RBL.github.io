# -*- coding: utf-8 -*-

import markdown
import platform
import importlib.metadata
from rich.logging import RichHandler
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
import logging
import os

__version__ = "Beta 0.1"


def main() -> int:
    console = Console()
    panel = Panel(Text("Welcome to the Python Tools application!",
                       justify="center"),
                  title="PTools", subtitle="Enjoy your using!",
                  style="bold green")
    console.print(panel)
    logging.basicConfig(level=logging.DEBUG, format="%(message)s",
                        handlers=[RichHandler()])
    logging.info("Starting main process.")
    logging.debug(f"Platform: {platform.platform()}")
    logging.debug(f"Python version: {platform.python_version()}")
    logging.debug(f"markdown module version: {markdown.__version__}")
    logging.debug(f"rich module version: {importlib.metadata.version('rich')}")
    logging.debug(f"PTools module version: {__version__}")
    paths = console.input("Input your markdown file [bold]path[/bold] "
                          '("|" to split): ')
    paths = paths.split("|")
    logging.debug(f"Input paths: {paths}")
    # Does the file exist? Is it a file?
    vpaths = []
    for path in paths:
        if not os.path.exists(path):
            logging.warning(f"File not found: {path}")
        elif not os.path.isfile(path):
            logging.warning(f"Path is not a file: {path}")
        else:
            vpaths.append(path)
    logging.debug(f"Valid paths: {vpaths}")
    logging.info("Finished main process.")
    return 0


if __name__ == '__main__':
    exit(main())
