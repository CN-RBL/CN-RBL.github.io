# -*- coding: utf-8 -*-

import markdown_it
import platform
import importlib.metadata
from rich.logging import RichHandler
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
import logging
import os
from lxml import html as html2
from lxml import etree

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
    logging.debug(f"markdown-it module version: {markdown_it.__version__}")
    logging.debug(f"rich module version: {importlib.metadata.version('rich')}")
    logging.debug(f"PTools module version: {__version__}")

    input_paths: set[str] = set(
        console.input(
            "Input your markdown file [bold]path[/bold] " '("|" to split): '
        ).split("|")
    )
    logging.debug(f"Input paths: {input_paths}")
    # Does the file exist? Is it a file?
    vinput_paths: list[str] = []
    for path in input_paths:
        if not os.path.exists(path):
            logging.warning(f'File not found: "{path}"')
        elif not os.path.isfile(path):
            logging.warning(f"Path is not a file: {path}")
        elif not (path.endswith(".md") or path.endswith(".markdown")):
            logging.warning(f'Path is not a markdown file: "{path}"')
        else:
            vinput_paths.append(path)
    logging.debug(f"Valid paths: {vinput_paths}")
    if not vinput_paths:
        logging.error("No valid input files.")
        return 1
    del input_paths

    output_dir: str = console.input(
        "Input your output directory [bold]path[/bold]: "  # ignore
    )
    if not os.path.exists(output_dir):
        logging.error(f'Output directory not found: "{output_dir}"')
        return 1
    elif not os.path.isdir(output_dir):
        logging.error(f'Output path is not a directory: "{output_dir}"')
        return 1
    logging.debug(f'Output directory: "{output_dir}"')

    template: str = console.input(
        "Input your HTML template file [bold]path[/bold] "
        "(optional, press Enter to skip): "
    )
    if not os.path.exists(template):
        logging.error(f'Template file not found: "{template}"')
        template = ""
    elif not os.path.isfile(template):
        logging.error(f'Template path is not a file: "{template}"')
        template = ""
    elif not (template.endswith(".html") or template.endswith(".htm")):
        logging.error(f'Template path is not a HTML file: "{template}"')
        template = ""
    if template:
        logging.debug(f'Template file: "{template}"')
        with open(template, "r", encoding="utf-8") as f:
            template_content: str = f.read()

    logging.info("Strarting markdown to HTML conversion.")
    md = markdown_it.MarkdownIt("gfm-like", {"typographer": True})
    md.enable(["replacements", "smartquotes"])
    for path in vinput_paths:
        with open(path, "r", encoding="utf-8") as f:
            content: str = f.read()
        html: str = md.render(content)
        output_path: str = os.path.join(
            output_dir, os.path.basename(path).replace(".md", ".html")
        )
        if template:
            title = html2.fromstring(html).xpath(".//h1")
            title = title[0].text_content() if title else "Untitled"
            template_content = template_content.replace("%%title%%", title)
            html = template_content.replace("%%content%%", html)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)
                # pretty print
        pretty_input: str = console.input(
            "Is it necessary to format the output HTML file?(Y/N): "
        )
        if pretty_input.lower() in ["y", "yes"]:
            with open(output_path, "r", encoding="utf-8") as f:
                raw_html = f.read()

            def pretty_print_html(html_str: str) -> str:
                """智能格式化HTML，保留完整结构和DOCTYPE。"""
                from io import StringIO
                try:
                    # 使用 etree.HTMLParser 解析，它能保留 DOCTYPE
                    parser = etree.HTMLParser(remove_blank_text=False)  # 保留空白以便格式化
                    tree = etree.parse(StringIO(html_str), parser)
                    doctype = tree.docinfo.doctype if tree.docinfo.doctype else ''
                    root = tree.getroot()
                    # 格式化根元素
                    formatted_root = etree.tostring(
                        root,
                        encoding='unicode',
                        pretty_print=True,
                        method='html'
                    )
                    # 如果存在 DOCTYPE，则拼接到前面
                    if doctype:
                        return doctype + '\n' + formatted_root
                    else:
                        return formatted_root
                except Exception as e:
                    # 如果解析为完整文档失败（例如纯片段），回退到片段处理
                    logging.warning(f"完整文档解析失败，尝试片段模式: {e}")
                    try:
                        fragments = html2.fragments_fromstring(html_str)
                        pretty_parts = []
                        for frag in fragments:
                            if isinstance(frag, str):
                                pretty_parts.append(frag)
                            else:
                                pretty_parts.append(
                                    etree.tostring(
                                        frag,
                                        encoding='unicode',
                                        pretty_print=True,
                                        method='html'
                                    )
                                )
                        return ''.join(pretty_parts)
                    except Exception as e2:
                        logging.error(f"片段解析也失败，返回原始内容: {e2}")
                        return html_str

            pretty_html = pretty_print_html(raw_html)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(pretty_html)
            console.print(pretty_html)
        logging.info(f'Converted "{path}" to "{output_path}". OK!')
    logging.info("Finished main process.")
    return 0


if __name__ == "__main__":
    exit(main())
