#!/data/data/com.termux/files/usr/bin/python
from pathlib import Path
from typing import Annotated
import sys
from rich.console import Console
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.panel import Panel
from loguru import logger


def render_markdown(content: str) -> None:
    """Render markdown with syntax highlighting for code blocks."""
    console = Console()
    md = Markdown(content)
    lines = content.splitlines()
    in_code_block = False
    code_language = ""
    code_content = []
    for line in lines:
        if line.startswith("```"):
            if in_code_block:
                syntax = Syntax("\n".join(code_content), code_language, theme="monokai", line_numbers=True)
                console.print(syntax)
                code_content = []
                in_code_block = False
            else:
                in_code_block = True
                code_language = line[3:].strip() or "python"
        elif in_code_block:
            code_content.append(line)
        else:
            console.print(line)
    if in_code_block:
        syntax = Syntax("\n".join(code_content), code_language, theme="monokai", line_numbers=True)
        console.print(syntax)


def main(
    file: Annotated[Path | None, "Markdown file path"] = None,
    pager: Annotated[bool, "Use pager for long documents"] = False,
) -> None:
    """Render markdown file or stdin with glow-like formatting."""
    try:
        if file:
            content = Path(file).read_text(encoding="utf-8")
        else:
            content = sys.stdin.read()
        if pager:
            from rich.pager import SystemPager

            console = Console(pager=SystemPager())
        else:
            console = Console()
        render_markdown(content)
    except Exception as e:
        logger.opt(exception=True).error("Rendering failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
