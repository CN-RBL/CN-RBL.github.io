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
import gc
from io import StringIO
from concurrent.futures import ThreadPoolExecutor, as_completed

__version__: str = "Beta 0.1"

gc.enable()

# 将格式化函数提升到模块级别，以便多线程调用
def pretty_print_html(html_str: str) -> str:
    """格式化HTML，保留DOCTYPE和注释，缩进4空格，pre/code开始标签同行，
    并处理自定义标记%%c:class1,class2%%"""

    # 内部函数：处理文本中的标记，并添加class到所属元素
    def process_text(text, owner):
        # 跳过pre/code内的标记
        if owner is not None and owner.tag in ("pre", "code"):
            return text
        pattern = r"%%c:([^%]+)%%"
        match = re.search(pattern, text)
        if match:
            class_str = match.group(1).strip()
            # 解析逗号分隔的class列表，去除空格
            classes = [c.strip() for c in class_str.split(",") if c.strip()]
            # 移除标记（只移除第一个）
            new_text = re.sub(pattern, "", text, count=1)
            # 为owner添加class
            if owner is not None and classes:
                existing = owner.get("class", "")
                new_classes = " ".join(classes)
                if existing:
                    owner.set("class", f"{existing} {new_classes}")
                else:
                    owner.set("class", new_classes)
            return new_text
        return text

    # 递归遍历元素树，处理text和tail中的标记
    def process_markup(element, skip=False):
        # 处理element的text（如果不跳过）
        if not skip:
            if element.text and "%%" in element.text:
                element.text = process_text(element.text, element)
        # 处理子元素：如果本元素是pre/code，则子元素应跳过
        child_skip = skip or element.tag in ("pre", "code")
        for child in element:
            process_markup(child, skip=child_skip)
        # 处理element的tail（始终处理，但会检查owner是否为pre/code）
        if element.tail and "%%" in element.tail:
            parent = element.getparent()
            if parent is not None:
                element.tail = process_text(element.tail, parent)

    # 1. 提取DOCTYPE及其之前的内容（如注释）
    doctype_match = re.search(r"(<!DOCTYPE[^>]*>)", html_str, re.IGNORECASE)
    if doctype_match:
        doctype = doctype_match.group(1)
        before_doctype = html_str[: doctype_match.start()]  # DOCTYPE前的注释等
        after_doctype = html_str[doctype_match.end() :]  # DOCTYPE后的内容
    else:
        doctype = ""
        before_doctype = ""
        after_doctype = html_str

    try:
        # 2. 将剩余部分解析为完整HTML文档（自动补全缺失的html/body）
        root = html2.document_fromstring(after_doctype)

        # 3. 使用4个空格进行层级缩进
        etree.indent(root, space="    ")

        # 4. 调整 <pre><code> 格式：使其开始标签在同一行
        for pre in root.xpath(".//pre"):
            if len(pre) > 0 and pre[0].tag == "code":
                pre.text = None  # 清除pre本身的缩进文本
                pre[0].tail = "\n"  # code后换行

        # 5. 处理自定义标记 %%c:class%%
        process_markup(root)

        # 6. 序列化为字符串（无需pretty_print，缩进已手动添加）
        formatted_root = etree.tostring(root, encoding="unicode", method="html")

        # 7. 拼接：前置注释 + DOCTYPE + 换行 + 格式化后的文档
        return before_doctype + doctype + "\n" + formatted_root

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
                    for pre in frag.xpath(".//pre"):
                        if len(pre) > 0 and pre[0].tag == "code":
                            pre.text = None
                            pre[0].tail = "\n"
                    # 处理标记
                    process_markup(frag)
                    pretty_parts.append(
                        etree.tostring(frag, encoding="unicode", method="html")
                    )
            return "".join(pretty_parts)
        except Exception as e2:
            logging.error(f"格式化失败，保留原始内容: {e2}")
            return html_str


def process_file(
    path: str, output_dir: str, template_content: str | None, format_all: bool
) -> tuple:
    """处理单个Markdown文件的函数，在线程池中执行"""
    try:
        # 每个线程独立创建markdown解析器，避免共享状态
        md = markdown_it.MarkdownIt("gfm-like", {"typographer": True})
        md.enable(["replacements", "smartquotes"])

        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        html: str = md.render(content)
        output_path: str = os.path.join(
            output_dir, os.path.basename(path).replace(".md", ".html")
        )

        if template_content:
            # 使用原始模板内容进行替换，不修改共享变量
            title_els = html2.fromstring(html).xpath(".//h1")
            title = title_els[0].text_content() if title_els else "Untitled"
            filled_template = template_content.replace("%%title%%", title)
            html = filled_template.replace("%%content%%", html)

        # 先写入原始HTML
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)

        if format_all:
            with open(output_path, "r", encoding="utf-8") as f:
                raw_html = f.read()
            pretty_html = pretty_print_html(raw_html)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(pretty_html)
            logging.info(f"Formatted: {output_path}")
        else:
            logging.info(f"Converted without formatting: {output_path}")

        return True, path, output_path, None
    except Exception as e:
        return False, path, None, str(e)


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
    # 验证输入文件
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

    output_dir: str = console.input("Input your output directory [bold]path[/bold]: ")
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
    template_content = None
    if template:
        if not os.path.exists(template):
            logging.error(f'Template file not found: "{template}"')
        elif not os.path.isfile(template):
            logging.error(f'Template path is not a file: "{template}"')
        elif not (template.endswith(".html") or template.endswith(".htm")):
            logging.error(f'Template path is not a HTML file: "{template}"')
        else:
            logging.debug(f'Template file: "{template}"')
            with open(template, "r", encoding="utf-8") as f:
                template_content = f.read()

    # 全局询问是否格式化所有文件
    format_all = False
    if vinput_paths:
        pretty_global = console.input("Format all output HTML files? (Y/N): ")
        format_all = pretty_global.lower() in ["y", "yes"]

    logging.info("Starting markdown to HTML conversion with thread pool.")

    # 使用线程池并发处理文件
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = []
        for path in vinput_paths:
            future = executor.submit(
                process_file, path, output_dir, template_content, format_all
            )
            futures.append(future)

        success_count = 0
        fail_count = 0
        for future in as_completed(futures):
            success, path, out_path, error = future.result()
            if success:
                success_count += 1
                logging.info(f"Successfully converted: {path} -> {out_path}")
            else:
                fail_count += 1
                logging.error(f"Failed to convert {path}: {error}")

    logging.info(
        f"Finished convert process. Success: {success_count}, Failed: {fail_count}"
    )
    update_article_list = console.input(
        "Do you require an update to the article list? (Y/N): "
    )
    if not update_article_list.lower() in ["y", "yes"]:
        return 0
    logging.info("Starting article list update process.")
    gc.collect()  # 强制垃圾回收，释放内存
    success_count = 0
    fail_count = 0

    article_dir = console.input(
        "Please enter the path to the article directory (.html): "
    )
    if not os.path.exists(article_dir):
        logging.error(f'Article directory not found: "{article_dir}"')
        return 1
    elif not os.path.isdir(article_dir):
        logging.error(f'Article path is not a directory: "{article_dir}"')
        return 1

    article_list_path = console.input(
        "Please enter the path to the article list HTML file: "
    )
    if not os.path.exists(article_list_path):
        logging.error(f'Article list file not found: "{article_list_path}"')
        return 1
    elif not os.path.isfile(article_list_path):
        logging.error(f'Article list path is not a file: "{article_list_path}"')
        return 1
    elif not (
        article_list_path.endswith(".html") or article_list_path.endswith(".htm")
    ):
        logging.error(f'Article list path is not a HTML file: "{article_list_path}"')
        return 1
    title_list = []
    path_list = []
    for path in os.listdir(article_dir):
        try:
            if path.endswith(".html") or path.endswith(".htm"):
                article_path = os.path.join(article_dir, path)
                path_list.append(article_path)
                logging.info(f"Processing article: {article_path}")
                with open(article_path, "r", encoding="utf-8") as f:
                    article_content = f.read()
                title_els = html2.fromstring(article_content).xpath(".//h1")
                title_list.append(title_els[0].text_content() if title_els else "Untitled")
        except Exception as e:
            logging.error(f"Failed to process article {path}: {e}")
            fail_count += 1
    if not title_list:
        logging.error("No valid articles found to update the list.")
        return 1
    for title in title_list:
        try:
            title_list.append(f"<div class=\"card\">\n<a href={os.path.relpath(path_list[title_list.index(title)], os.path.dirname(article_list_path))}>{title}</a></div>")
            title_list.remove(title)
        except Exception as e:
            logging.error(f"Failed to create card for title {title}: {e}")
            fail_count += 1
        else:
            success_count += 1
    title_list.sort()
    with open(article_list_path, "r", encoding="utf-8") as f:
        list_content = f.read()
    with open(article_list_path, "w", encoding="utf-8") as f:
        f.write(pretty_print_html(list_content.replace("%%cards%%", "\n".join(title_list))))
    logging.info(
        f"Finished update process. Success: {success_count}, Failed: {fail_count}"
    )
    logging.info("All processes completed.")
    os.system("start msedge 127.0.0.1:5500")
    return 1 if fail_count else 0


if __name__ == "__main__":
    exit(main())
