#!/data/data/com.termux/files/usr/bin/python3.12
"""Write a Python script that generates a basic HTML5 boilerplate file.
It should define a function accepting an optional filename parameter (defaulting to "index.html") and write a standard HTML template—including doctype, charset meta tag, viewport meta tag, title, and a simple "Hello, World!" heading in the body—to that file using UTF-8 encoding via pathlib.
The function should print a success message showing the created filename and current working directory, or print an error message if the file write fails due to an exception.
The script should run the function automatically when executed directly."""

from pathlib import Path


def create_html_template(filename: str = "index.html") -> None:
    html_template = '<!DOCTYPE html>\n<html lang="en">\n<head>\n    <meta charset="UTF-8">\n    <meta name="viewport" content="width=device-width, initial-scale=1.0">\n    <title>Document</title>\n</head>\n<body>\n    <h1>Hello, World!</h1>\n    <!-- Your content here -->\n</body>\n</html>\n'
    try:
        Path(filename).write_text(html_template, encoding="utf-8")
        print(f"Successfully created {filename} in {Path.cwd()}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    create_html_template()
