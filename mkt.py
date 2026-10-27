#!/data/data/com.termux/files/usr/bin/python
import argparse
import base64
import mimetypes
import re
from pathlib import Path
from typing import List, Set, Tuple

import requests
from bs4 import BeautifulSoup


def skeletonize_soup(soup: BeautifulSoup) -> str:
    if not soup.body:
        return ""
    for list_elem in soup.body.find_all(["ul", "ol"]):
        lis = list_elem.find_all("li", recursive=False)
        list_elem.clear()
        if lis:
            first = lis[0]
            first.clear()
            first.string = "Placeholder item"
            list_elem.append(first)
        else:
            sample_li = soup.new_tag("li")
            sample_li.string = "Placeholder item"
            list_elem.append(sample_li)
    for table in soup.body.find_all("table"):
        rows = table.find_all("tr")
        table.clear()
        if rows:
            first_row = rows[0]
            table.append(first_row)
            for cell in first_row.find_all(["th", "td"]):
                cell.clear()
                cell.string = "Placeholder"
        else:
            new_row = soup.new_tag("tr")
            new_cell = soup.new_tag("td")
            new_cell.string = "Placeholder"
            new_row.append(new_cell)
            table.append(new_row)
    for elem in soup.body.find_all(["h1", "h2", "h3", "h4", "h5", "h6", "p", "div", "span", "section", "article"]):
        if elem.parent is None:
            continue
        if elem.find_parent(["table", "ul", "ol"]):
            continue
        if elem.get_text(strip=True):
            elem.clear()
            elem.string = "Placeholder content"
    return str(soup.body)


def _fetch_asset(url_or_path: str, base_dir: Path) -> Tuple[bytes, str]:
    if url_or_path.startswith("data:"):
        return b"", ""
    if url_or_path.startswith(("http://", "https://")):
        try:
            response = requests.get(url_or_path, timeout=10)
            if response.status_code == 200:
                content_type = response.headers.get("Content-Type", "")
                mime = (
                    content_type.split(";")[0]
                    if content_type
                    else mimetypes.guess_type(url_or_path)[0] or "application/octet-stream"
                )
                return response.content, mime
        except Exception as e:
            print(f"Error downloading remote asset {url_or_path}: {e}")
        return b"", "application/octet-stream"
    local_path = (base_dir / url_or_path).resolve()
    if local_path.is_file():
        try:
            mime, _ = mimetypes.guess_type(str(local_path))
            return local_path.read_bytes(), mime or "application/octet-stream"
        except Exception as e:
            print(f"Error reading local asset {local_path}: {e}")
    return b"", "application/octet-stream"


def inline_css_assets_recursive(css_text: str, base_dir: Path, seen_assets: Set[str]) -> str:
    url_pattern = r'url\((?:\'|")?([^\'")]+)(?:\'|")?\)'
    while True:
        matches = re.findall(url_pattern, css_text)
        updated = False
        for asset_path in matches:
            if asset_path.startswith("data:") or asset_path in seen_assets:
                continue
            seen_assets.add(asset_path)
            content, mime = _fetch_asset(asset_path, base_dir)
            if content:
                if mime == "text/css":
                    nested_css = content.decode("utf-8", errors="ignore")
                    resolved_css = inline_css_assets_recursive(nested_css, base_dir, seen_assets)
                    b64_content = base64.b64encode(resolved_css.encode("utf-8")).decode("utf-8")
                else:
                    b64_content = base64.b64encode(content).decode("utf-8")
                data_uri = f"data:{mime};base64,{b64_content}"
                css_text = css_text.replace(asset_path, data_uri)
                updated = True
        if not updated:
            break
    return css_text


def inline_assets(soup: BeautifulSoup, base_dir: Path) -> None:
    seen_assets: Set[str] = set()
    for link in soup.find_all("link", rel="stylesheet"):
        href = link.get("href")
        if href:
            content, _ = _fetch_asset(href, base_dir)
            if content:
                style_tag = soup.new_tag("style")
                css_text = content.decode("utf-8", errors="ignore")
                style_tag.string = inline_css_assets_recursive(css_text, base_dir, seen_assets)
                link.replace_with(style_tag)
    for style in soup.find_all("style"):
        if style.string:
            style.string = inline_css_assets_recursive(style.string, base_dir, seen_assets)
    for script in soup.find_all("script"):
        src = script.get("src")
        if src:
            content, _ = _fetch_asset(src, base_dir)
            if content:
                script.string = content.decode("utf-8", errors="ignore")
                del script["src"]
    for img in soup.find_all("img"):
        src = img.get("src")
        if src and not src.startswith("data:"):
            content, mime = _fetch_asset(src, base_dir)
            if content:
                b64_content = base64.b64encode(content).decode("utf-8")
                img["src"] = f"data:{mime};base64,{b64_content}"


def process_single_file(path: Path) -> Tuple[List[str], List[str], List[str], List[str], List[str], str]:
    meta_tags: List[str] = []
    link_tags: List[str] = []
    script_tags: List[str] = []
    style_tags: List[str] = []
    body_classes: List[str] = []
    base_dir = path.parent
    try:
        content = path.read_text(encoding="utf-8")
        soup = BeautifulSoup(content, "lxml")
        inline_assets(soup, base_dir)
        if soup.head:
            for tag in soup.head.find_all("meta"):
                meta_tags.append(str(tag))
            for tag in soup.head.find_all("link"):
                if tag.get("rel") != ["stylesheet"]:
                    link_tags.append(str(tag))
            for tag in soup.head.find_all("style"):
                style_tags.append(str(tag))
                tag.decompose()
        for script in soup.find_all("script"):
            script_tags.append(str(script))
            script.decompose()
        if soup.body:
            classes = soup.body.get("class")
            if classes:
                body_classes = list(classes)
        body_skeleton = skeletonize_soup(soup)
        return meta_tags, link_tags, script_tags, style_tags, body_classes, body_skeleton
    except Exception as e:
        print(f"Error processing {path}: {e}")
        return [], [], [], [], [], ""


def get_output_path(output_file: str) -> Path:
    path = Path(output_file)
    if not path.exists():
        return path
    stem, suffix = path.stem, path.suffix
    counter = 1
    while True:
        new_path = path.with_name(f"{stem}_{counter}{suffix}")
        if not new_path.exists():
            return new_path
        counter += 1


def create_template_html(file_path: Path, output_file: str = "template.html", title: str = "HTML Template") -> bool:
    if not file_path.is_file():
        print(f"File not found: {file_path}")
        return False
    meta_tags, link_tags, script_tags, style_tags, body_classes, skeleton = process_single_file(file_path)
    meta_str = "\n".join("    " + tag for tag in sorted(meta_tags))
    link_str = "\n".join("    " + tag for tag in sorted(link_tags))
    style_str = "\n".join("    " + tag for tag in style_tags)
    script_str = "\n".join("    " + tag for tag in script_tags)
    classes_joined = " ".join(sorted(body_classes))
    body_class_str = f' class="{classes_joined}"' if classes_joined else ""
    combined_body = skeleton if skeleton else "    <!-- Template body content goes here -->"
    template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
{meta_str}
{link_str}
{style_str}
</head>
<body{body_class_str}>
{combined_body}
{script_str}
</body>
</html>"""
    final_output_path = get_output_path(output_file)
    try:
        final_output_path.write_text(template, encoding="utf-8")
        print(f"Template created successfully: {final_output_path}")
        return True
    except OSError as e:
        print(f"Failed to write template: {e}")
        return False


def main() -> None:
    parser = argparse.ArgumentParser(description="Create an completely recursive standalone HTML template.")
    parser.add_argument("path", type=str, help="HTML file to process")
    parser.add_argument("-o", "--output", default="template.html", help="Output template file")
    parser.add_argument("-t", "--title", default="HTML Template", help="Template title")
    args = parser.parse_args()
    if not create_template_html(Path(args.path), args.output, args.title):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
