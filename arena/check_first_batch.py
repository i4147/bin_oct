#!/usr/bin/env python3
"""Check documented copies against originals without importing project dependencies."""
from pathlib import Path
from tempfile import TemporaryDirectory
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
FILES = ('23.py', '480mkv.py', '7ziper.py', 'a-b.py', 'abline.py')
for name in FILES:
    for source in (ROOT / name, ROOT / 'documented' / name):
        compile(source.read_bytes(), str(source), 'exec')
print('PASS: all 10 source files compile')


def run_case(script, inputs, args):
    outputs = []
    for source in (ROOT / script, ROOT / 'documented' / script):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            for name, text in inputs.items():
                (root / name).write_text(text, encoding='utf-8')
            proc = subprocess.run([sys.executable, str(source), *args], cwd=root,
                                  capture_output=True, text=True, check=False)
            contents = {name: (root / name).read_bytes() for name in inputs}
            outputs.append((proc.returncode, proc.stdout, proc.stderr, contents))
    if outputs[0] != outputs[1]:
        raise AssertionError(f'{script}: documented copy differed for {inputs!r} / {args!r}')


run_case('480mkv.py', {'in.txt': 'video-480.mkv\nvideo-720.mp4\nother\n'}, ['in.txt'])
run_case('480mkv.py', {'in.txt': 'video-720.mp4\nother\n'}, ['in.txt'])
run_case('480mkv.py', {'in.txt': 'no matches\n'}, ['in.txt'])
run_case('a-b.py', {'a.txt': 'alpha\nbeta\ngamma\n', 'b.txt': 'beta\n'}, ['a.txt', 'b.txt'])
run_case('abline.py', {'in.txt': 'one::two\nthree\n\n'}, ['-a', 'in.txt', '::'])
run_case('abline.py', {'in.txt': 'one::two\nthree\n\n'}, ['-b', 'in.txt', '::'])
print('PASS: six original-versus-copy CLI comparisons')
