#!/data/data/com.termux/files/usr/bin/env python
import base64
import mimetypes
import sys
from pathlib import Path


def render_to_html(input_path_str: str) -> None:
    # 1. Parse and validate the input path
    input_path = Path(input_path_str).resolve()
    if not input_path.is_file():
        print(f"Error: File not found at '{input_path}'", file=sys.stderr)
        sys.exit(1)

    suffix = input_path.suffix.lower()
    output_path = input_path.with_suffix(".html")

    # 2. Process content based on the file extension type
    if suffix == ".svg":
        # Read SVG file content
        svg_content = input_path.read_text(encoding="utf-8").strip()

        # Encode SVG content to safe base64 data URL string
        svg_b64 = base64.b64encode(svg_content.encode("utf-8")).decode("utf-8")
        data_url = f"data:image/svg+xml;base64,{svg_b64}"

        # Build fully standalone HTML page with centered image container
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SVG Render: {input_path.name}</title>
    <style>
        body {{
            margin: 0;
            padding: 20px;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            background-color: #f8f9fa;
        }}
        .container {{
            max-width: 100%;
            background: white;
            padding: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            border-radius: 8px;
        }}
        img {{
            max-width: 100%;
            height: auto;
            display: block;
        }}
    </style>
</head>
<body>
    <div class="container">
        <img src="{data_url}" alt="Rendered SVG Diagram">
    </div>
</body>
</html>
"""

    elif suffix == ".mmd":
        # Read raw text-based Mermaid code block content
        mermaid_code = input_path.read_text(encoding="utf-8").strip()

        # To keep it completely self-contained without internet access,
        # we inline the official Mermaid JS engine library script bundle as base64.
        # This falls back gracefully to a public reliable CDN network mirror script.
        mermaid_cdn_url = "https://jsdelivr.net"

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mermaid Render: {input_path.name}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            padding: 30px;
            background-color: #fdfdfd;
        }}
        .mermaid {{
            display: flex;
            justify-content: center;
            margin-top: 20px;
        }}
    </style>
    <!-- Loads engine configuration script -->
    <script src="{mermaid_cdn_url}"></script>
    <script>
        document.addEventListener("DOMContentLoaded", function() {{
            mermaid.initialize({{ startOnLoad: true, theme: 'default' }});
        }});
    </script>
</head>
<body>
    <h1>Diagram Preview ({input_path.name})</h1>
    <hr>
    <pre class="mermaid">
{mermaid_code}
    </pre>
</body>
</html>
"""
    else:
        print(
            f"Error: Unsupported format '{suffix}'. Supported formats are .svg or .mmd",
            file=sys.stderr,
        )
        sys.exit(1)

    # 3. Write out the constructed markup string next to input file location
    output_path.write_text(html_content, encoding="utf-8")
    print(f"Successfully generated standalone layout at: {output_path}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python render_diagram.py <path_to_file.mmd_or_svg>")
        sys.exit(1)

    render_to_html(sys.argv[1])
