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

__version__: str = "Beta 0.1"


def main() -> int:
    console: Console = Console()
    panel: Panel = Panel(
        Text("Welcome to the Python Tools application!", justify="center"),
        title="PTools",
        subtitle="Enjoy your using!",
        style="bold green",
    )
    console.print(panel)
    logging.basicConfig(
        level=logging.DEBUG, format="%(message)s", handlers=[RichHandler()]
    )
    logging.info("Starting main process.")
    logging.debug(f"Platform: {platform.platform()}")
    logging.debug(f"Python version: {platform.python_version()}")
    logging.debug(f"markdown module version: {markdown.__version__}")
    logging.debug(f"rich module version: {importlib.metadata.version('rich')}")
    logging.debug(f"PTools module version: {__version__}")
    input_paths: set[str] = set(console.input(
        "Input your markdown file [bold]path[/bold] " '("|" to split): '
    ).split("|"))
    logging.debug(f"Input paths: {input_paths}")
    # Does the file exist? Is it a file?
    vinput_paths: list[str] = []
    for path in input_paths:
        if not os.path.exists(path):
            logging.warning(f"File not found: {path}")
        elif not os.path.isfile(path):
            logging.warning(f"Path is not a file: {path}")
        elif not (path.endswith(".md") or path.endswith(".markdown")):
            logging.warning(f"Path is not a markdown file: {path}")
        else:
            vinput_paths.append(path)
    logging.debug(f"Valid paths: {vinput_paths}")
    if not vinput_paths:
        logging.error("No valid input files.")
        return 1
    del input_paths
    output_dir: str = console.input(
        "Input your output directory [bold]path[/bold]: "
    )
    if not os.path.exists(output_dir):
        logging.error(f"Output directory not found: {output_dir}")
        return 1
    elif not os.path.isdir(output_dir):
        logging.error(f"Output path is not a directory: {output_dir}")
        return 1
    logging.info("Finished main process.")
    return 0


if __name__ == "__main__":
    exit(main())
