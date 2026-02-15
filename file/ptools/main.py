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
import re
from io import StringIO

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
        # 先写入原始HTML
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)

        # 询问是否格式化（此时文件已关闭，可安全读取）
        pretty_input: str = console.input(
            "Is it necessary to format the output HTML file?(Y/N): "
        )
        if pretty_input.lower() in ["y", "yes"]:
            with open(output_path, "r", encoding="utf-8") as f:
                raw_html = f.read()

            def pretty_print_html(html_str: str) -> str:
                """格式化HTML，保留DOCTYPE和注释，缩进4空格，pre/code开始标签同行，并处理自定义标记%%c:class%%"""
                # 内部函数：处理文本中的标记，并添加class到所属元素
                def process_text(text, owner):
                    # 跳过pre/code内的标记
                    if owner is not None and owner.tag in ('pre', 'code'):
                        return text
                    pattern = r'%%c:([^%]+)%%'
                    match = re.search(pattern, text)
                    if match:
                        class_name = match.group(1).strip()
                        # 移除标记（只移除第一个）
                        new_text = re.sub(pattern, '', text, count=1)
                        # 为owner添加class
                        if owner is not None:
                            existing = owner.get('class', '')
                            if existing:
                                owner.set('class', f"{existing} {class_name}")
                            else:
                                owner.set('class', class_name)
                        return new_text
                    return text

                # 递归遍历元素树，处理text和tail中的标记
                def process_markup(element, skip=False):
                    # 处理element的text（如果不跳过）
                    if not skip:
                        if element.text and '%%' in element.text:
                            element.text = process_text(element.text, element)
                    # 处理子元素：如果本元素是pre/code，则子元素应跳过
                    child_skip = skip or element.tag in ('pre', 'code')
                    for child in element:
                        process_markup(child, skip=child_skip)
                    # 处理element的tail（始终处理，但会检查owner是否为pre/code）
                    if element.tail and '%%' in element.tail:
                        parent = element.getparent()
                        if parent is not None:
                            element.tail = process_text(element.tail, parent)

                # 1. 提取DOCTYPE及其之前的内容（如注释）
                doctype_match = re.search(r'(<!DOCTYPE[^>]*>)', html_str, re.IGNORECASE)
                if doctype_match:
                    doctype = doctype_match.group(1)
                    before_doctype = html_str[:doctype_match.start()]  # DOCTYPE前的注释等
                    after_doctype = html_str[doctype_match.end():]     # DOCTYPE后的内容
                else:
                    doctype = ''
                    before_doctype = ''
                    after_doctype = html_str

                try:
                    # 2. 将剩余部分解析为完整HTML文档（自动补全缺失的html/body）
                    root = html2.document_fromstring(after_doctype)

                    # 3. 使用4个空格进行层级缩进
                    etree.indent(root, space="    ")

                    # 4. 调整 <pre><code> 格式：使其开始标签在同一行
                    for pre in root.xpath('.//pre'):
                        if len(pre) > 0 and pre[0].tag == 'code':
                            pre.text = None          # 清除pre本身的缩进文本
                            pre[0].tail = '\n'       # code后换行

                    # 5. 处理自定义标记 %%c:class%%
                    process_markup(root)

                    # 6. 序列化为字符串（无需pretty_print，缩进已手动添加）
                    formatted_root = etree.tostring(root, encoding='unicode', method='html')

                    # 7. 拼接：前置注释 + DOCTYPE + 换行 + 格式化后的文档
                    return before_doctype + doctype + '\n' + formatted_root

                except Exception as e:
                    logging.warning(f"完整文档解析失败，尝试片段模式: {e}")
                    # 降级方案：使用fragments_fromstring确保内容不丢失
                    try:
                        fragments = html2.fragments_fromstring(html_str)
                        pretty_parts = []
                        for frag in fragments:
                            if isinstance(frag, str):
                                pretty_parts.append(frag)
                            else:
                                # 对片段内的元素也尝试indent
                                try:
                                    etree.indent(frag, space="    ")
                                except:
                                    pass
                                # 调整pre/code格式
                                for pre in frag.xpath('.//pre'):
                                    if len(pre) > 0 and pre[0].tag == 'code':
                                        pre.text = None
                                        pre[0].tail = '\n'
                                # 处理标记
                                process_markup(frag)
                                pretty_parts.append(
                                    etree.tostring(frag, encoding='unicode', method='html')
                                )
                        return ''.join(pretty_parts)
                    except Exception as e2:
                        logging.error(f"格式化失败，保留原始内容: {e2}")
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
