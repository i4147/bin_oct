"""Regression tests for independently reproducible failures in the scripts."""

from __future__ import annotations

import importlib.util
import io
import json
import runpy
import subprocess
import sys
import tempfile
import types
import unittest
import warnings
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]


def load_script(name: str, substitutes: dict[str, types.ModuleType]) -> types.ModuleType:
    """Exercise a script's own logic without requiring optional external tools."""
    spec = importlib.util.spec_from_file_location(f"_debug_regression_{name}", ROOT / f"{name}.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    with mock.patch.dict(sys.modules, {**substitutes, spec.name: module}):
        spec.loader.exec_module(module)
    return module


def fake_module(name: str, **attributes: object) -> types.ModuleType:
    module = types.ModuleType(name)
    for key, value in attributes.items():
        setattr(module, key, value)
    return module


pfzf = load_script("pfzf", {})


class CleanVersionTests(unittest.TestCase):
    def run_script(self, path: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-B", str(ROOT / "clean_version.py"), str(path)],
            capture_output=True,
            text=True,
            check=False,
        )

    def test_missing_input_reports_a_clean_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "missing.txt"
            result = self.run_script(path)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(f"Not a file: {path}", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_valid_input_still_cleans_and_deduplicates(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "requirements.txt"
            path.write_text(
                "# comment\nrequests==2.0\nexample @ https://example.invalid/pkg\n"
                "requests==3.0\nhttps://example.invalid/archive.zip\n",
                encoding="utf-8",
            )
            result = self.run_script(path)
            output = path.read_text(encoding="utf-8")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(output, "requests\nexample\n")


class FuzzyPickerTests(unittest.TestCase):
    def test_interactive_selection_and_scrolling(self) -> None:
        keys = ["DOWN", "DOWN", "DOWN", "DOWN", "ENTER"]
        with (
            mock.patch.object(pfzf, "get_terminal_size", return_value=(80, 4)),
            mock.patch.object(pfzf, "read_key", side_effect=keys),
            mock.patch("sys.stdout", new_callable=io.StringIO),
        ):
            selected = pfzf.fzf(["one", "two", "three", "four", "five", "six"])

        self.assertEqual(selected, "five")

    def test_filtering_with_no_matches_returns_none(self) -> None:
        with (
            mock.patch.object(pfzf, "get_terminal_size", return_value=(80, 6)),
            mock.patch.object(pfzf, "read_key", side_effect=["z", "ENTER"]),
            mock.patch("sys.stdout", new_callable=io.StringIO),
        ):
            selected = pfzf.fzf(["one", "two"])

        self.assertIsNone(selected)


class BracketCheckerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.module = load_script("ensurebracket", {"dh": fake_module("dh", get_files=mock.Mock())})

    def test_balanced_and_unbalanced_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "example.py"
            with mock.patch("sys.stdout", new_callable=io.StringIO) as output:
                path.write_text("([{ }])", encoding="utf-8")
                self.assertTrue(self.module.process_file(path))
                self.assertIn(path.name, output.getvalue())
                path.write_text("([)]", encoding="utf-8")
                self.assertFalse(self.module.process_file(path))
                path.write_text("([", encoding="utf-8")
                self.assertFalse(self.module.process_file(path))

    def test_string_path_is_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "example.py"
            path.write_text("()", encoding="utf-8")
            with mock.patch("sys.stdout", new_callable=io.StringIO):
                self.assertTrue(self.module.process_file(str(path)))


class Dos2UnixTests(unittest.TestCase):
    def setUp(self) -> None:
        dependencies = {
            "dh": fake_module("dh", is_binary=lambda path: b"\x00" in path.read_bytes()),
            "dos2unix": fake_module("dos2unix", dos2unix=lambda data: data.replace(b"\r\n", b"\n")),
            "loguru": fake_module("loguru", logger=mock.Mock()),
        }
        self.module = load_script("pydos2unix", dependencies)

    def test_converts_crlf_and_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "example.txt"
            path.write_bytes(b"first\r\nsecond\r\n")
            self.assertEqual(self.module.convert_file(path), (str(path), True, "Converted"))
            self.assertEqual(path.read_bytes(), b"first\nsecond\n")
            self.assertEqual(self.module.convert_file(path), (str(path), True, "Already Unix format"))

    def test_skips_binary_and_missing_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "binary.txt"
            path.write_bytes(b"\x00\r\n")
            self.assertEqual(self.module.convert_file(path), (str(path), False, "Binary file (skipped)"))
            self.assertEqual(path.read_bytes(), b"\x00\r\n")
            missing = Path(directory) / "missing.txt"
            self.assertEqual(self.module.convert_file(missing), (str(missing), False, "Not a file"))


class ManDocTests(unittest.TestCase):
    def setUp(self) -> None:
        self.run_command = mock.Mock()
        dh = fake_module("dh", cprint=mock.Mock(), mpf=mock.Mock(), runcmd=self.run_command)
        self.module = load_script("man_doc", {"dh": dh})

    def test_failed_conversion_reports_error_and_preserves_source(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "example.1"
            path.write_text("manual", encoding="utf-8")
            self.run_command.return_value = (1, "", "mandoc failed")
            with mock.patch("sys.stderr", new_callable=io.StringIO) as stderr:
                self.assertFalse(self.module.safe_run(path))
            self.assertIn("mandoc failed", stderr.getvalue())
            self.assertEqual(path.read_text(encoding="utf-8"), "manual")
            self.assertFalse(path.with_suffix(".html").exists())

    def test_successful_conversion_writes_output(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "example.1"
            path.write_text("manual", encoding="utf-8")
            self.run_command.return_value = (0, "<p>manual</p>", "")
            self.assertTrue(self.module.safe_run(path))
            self.assertEqual(path.with_suffix(".html").read_text(encoding="utf-8"), "<p>manual</p>")
            self.assertFalse(path.exists())


class CommentRemoverDiscoveryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.module = load_script("drmc", {"loguru": fake_module("loguru", logger=mock.Mock())})

    def test_directory_discovery_finds_candidates_and_skips_ignored_paths(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            nested = root / "nested"
            nested.mkdir()
            python_file = nested / "script.py"
            python_file.write_text("print('hello')\n", encoding="utf-8")
            executable = root / "script"
            executable.write_text("#!/usr/bin/env python3\nprint('hello')\n", encoding="utf-8")
            wheel = root / "package.whl"
            wheel.touch()
            (root / "notes.txt").write_text("not Python", encoding="utf-8")
            ignored = root / ".git"
            ignored.mkdir()
            (ignored / "ignore.py").write_text("pass\n", encoding="utf-8")
            (root / "link.py").symlink_to(python_file)

            discovered = set(self.module.iter_targets([root]))
            self.assertEqual(discovered, {python_file, executable, wheel})

    def test_explicit_python_file_is_a_target(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "example.py"
            path.write_text("pass\n", encoding="utf-8")
            self.assertEqual(list(self.module.iter_targets([path])), [path])


class QrCodeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.image = mock.Mock(mode="RGB")
        self.image_context = mock.MagicMock()
        self.image_context.__enter__.return_value = self.image
        self.open_image = mock.Mock(return_value=self.image_context)
        self.decode = mock.Mock()
        dependencies = {
            "PIL": fake_module("PIL", Image=types.SimpleNamespace(open=self.open_image)),
            "pyzbar": fake_module("pyzbar", pyzbar=types.SimpleNamespace(decode=self.decode)),
        }
        self.module = load_script("qrcoder", dependencies)

    def test_decodes_all_qr_results(self) -> None:
        rect = types.SimpleNamespace(left=1, top=2, width=3, height=4)
        self.decode.return_value = [
            types.SimpleNamespace(data=b"first", type="QRCODE", rect=rect),
            types.SimpleNamespace(data="second ✓".encode(), type="QRCODE", rect=rect),
        ]
        with mock.patch("sys.stdout", new_callable=io.StringIO) as output:
            results = self.module.process_qrcode("example.png")
        self.assertEqual(results, ["first", "second ✓"])
        self.assertIn("QR Code 2", output.getvalue())
        self.decode.assert_called_once_with(self.image)

    def test_converts_non_rgb_images_and_handles_no_results(self) -> None:
        self.image.mode = "L"
        converted = self.image.convert.return_value
        self.decode.return_value = []
        self.assertEqual(self.module.process_qrcode("example.png"), [])
        self.image.convert.assert_called_once_with("RGB")
        self.decode.assert_called_once_with(converted)


class DeepLTranslatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.module = load_script("dt1", {"loguru": fake_module("loguru", logger=mock.Mock())})

    def test_translator_can_be_called_repeatedly(self) -> None:
        client = mock.Mock()
        client.translate_text.side_effect = [types.SimpleNamespace(text="bonjour"), "au revoir"]
        deepl = fake_module("deepl", DeepLClient=mock.Mock(return_value=client))
        with mock.patch.dict(sys.modules, {"deepl": deepl}), mock.patch.dict(
            "os.environ", {"DEEPL_API_KEY": "test-key"}
        ):
            translate = self.module._make_deepl("en", "fr")
            self.assertEqual(translate("hello"), "bonjour")
            self.assertEqual(translate("goodbye"), "au revoir")
        self.assertEqual(
            client.translate_text.call_args_list,
            [
                mock.call("hello", source_lang="EN", target_lang="FR"),
                mock.call("goodbye", source_lang="EN", target_lang="FR"),
            ],
        )

    def test_source_language_auto_detection_and_aliases(self) -> None:
        for source, expected in (("auto", None), ("zh-CN", "ZH"), ("he", "HE")):
            with self.subTest(source=source):
                client = mock.Mock()
                client.translate_text.return_value = types.SimpleNamespace(text="bonjour")
                deepl = fake_module("deepl", DeepLClient=mock.Mock(return_value=client))
                with mock.patch.dict(sys.modules, {"deepl": deepl}), mock.patch.dict(
                    "os.environ", {"DEEPL_API_KEY": "test-key"}
                ):
                    translate = self.module._make_deepl(source, "fr")
                    self.assertEqual(translate("hello"), "bonjour")
                client.translate_text.assert_called_once_with("hello", source_lang=expected, target_lang="FR")


class FormatterFailureTests(unittest.TestCase):
    def setUp(self) -> None:
        self.size = mock.Mock()
        self.format = mock.Mock()
        self.report = mock.Mock()
        dh = fake_module(
            "dh", cprint=mock.Mock(), fsz=mock.Mock(), get_files=mock.Mock(),
            gsz=self.size, mpf=mock.Mock(), rrs=self.report, runcmd=self.format,
        )
        self.module = load_script("cppu", {"dh": dh})

    def test_formatter_failure_does_not_raise_an_unbound_local_error(self) -> None:
        self.size.return_value = 10
        self.format.side_effect = RuntimeError("formatter failed")
        self.assertIsNone(self.module.process_file(Path("example.c")))
        self.report.assert_not_called()

    def test_successful_formatting_reports_sizes(self) -> None:
        self.size.side_effect = [100, 80]
        self.module.process_file(Path("example.c"))
        self.report.assert_called_once_with(Path("example.c"), 100, 80)


class ImageAsciiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.art = mock.Mock()
        self.factory = mock.Mock(return_value=self.art)
        dependencies = {
            "ascii_magic": fake_module("ascii_magic", AsciiArt=types.SimpleNamespace(from_image=self.factory)),
            "dh": fake_module("dh", get_files=mock.Mock()),
        }
        self.module = load_script("img2asci", dependencies)

    def test_processes_an_image_path(self) -> None:
        with mock.patch.object(self.module.os, "get_terminal_size", return_value=types.SimpleNamespace(columns=80)):
            self.module.process_file(Path("example.png"))
        self.factory.assert_called_once_with(Path("example.png"))
        self.art.to_terminal.assert_called_once_with(columns=80, width_ratio=2, monochrome=False)


class FontNamingTests(unittest.TestCase):
    def setUp(self) -> None:
        ttfont = mock.Mock()
        font_tools = fake_module("fontTools")
        font_tools.__path__ = []
        ttlib = fake_module("fontTools.ttLib", TTFont=ttfont)
        ttlib.__path__ = []
        ttfont_module = fake_module("fontTools.ttLib.ttFont", TTFont=ttfont)
        dh = fake_module(
            "dh", cprint=mock.Mock(), get_files=mock.Mock(), mpf=mock.Mock(),
            unique_path=lambda path: path.with_stem(path.stem + "-unique"),
        )
        self.module = load_script(
            "tell_font_name",
            {"dh": dh, "fontTools": font_tools, "fontTools.ttLib": ttlib, "fontTools.ttLib.ttFont": ttfont_module},
        )

    def test_renames_a_font_using_its_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            original = Path(directory) / "input.ttf"
            original.write_bytes(b"font data")
            with mock.patch.object(self.module, "get_font_names", return_value=("Example", "Regular")):
                self.assertEqual(self.module.process_file(original), 0)
            renamed = Path(directory) / "Example-Regular.ttf"
            self.assertEqual(renamed.read_bytes(), b"font data")
            self.assertFalse(original.exists())

    def test_avoids_overwriting_an_existing_font(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            original = Path(directory) / "input.ttf"
            existing = Path(directory) / "Example-Regular.ttf"
            original.write_bytes(b"new")
            existing.write_bytes(b"existing")
            with mock.patch.object(self.module, "get_font_names", return_value=("Example", "Regular")):
                self.assertEqual(self.module.process_file(original), 0)
            self.assertEqual(existing.read_bytes(), b"existing")
            self.assertEqual((Path(directory) / "Example-Regular-unique.ttf").read_bytes(), b"new")

    def test_filename_cleanup_preserves_parent_directory(self) -> None:
        with tempfile.TemporaryDirectory(prefix="fonts_1_") as directory:
            original = Path(directory) / "input.ttf"
            original.write_bytes(b"font data")
            with mock.patch.object(self.module, "get_font_names", return_value=("Example_1", "Regular_2")):
                self.assertEqual(self.module.process_file(original), 0)
            self.assertEqual((Path(directory) / "Example-Regular.ttf").read_bytes(), b"font data")


class SqlToJsonCommandTests(unittest.TestCase):
    def setUp(self) -> None:
        dateutil = fake_module("dateutil")
        dateutil.__path__ = []
        sqlalchemy = fake_module("sqlalchemy", create_engine=mock.Mock())
        sqlalchemy.__path__ = []
        dependencies = {
            "fire": fake_module("fire", Fire=mock.Mock()),
            "dateutil": dateutil,
            "dateutil.relativedelta": fake_module("dateutil.relativedelta", relativedelta=mock.Mock()),
            "sqlalchemy": sqlalchemy,
            "sqlalchemy.sql": fake_module("sqlalchemy.sql", text=mock.Mock()),
        }
        self.module = load_script("sqltojson", dependencies)

    def test_list_options_use_the_existing_config_helpers(self) -> None:
        config = {
            "connections": {"main": "sqlite:///main.db", "other": "sqlite:///other.db"},
            "queries": {"all": "SELECT 1", "shared": "SELECT 2"},
            "connection_queries": {"main": {"private": "SELECT 3", "shared": "SELECT 4"}},
        }
        with tempfile.TemporaryDirectory() as directory:
            config_path = Path(directory) / "sql2json.json"
            config_path.write_text(json.dumps(config), encoding="utf-8")
            for option, expected in (
                ({"list_connections": True}, ["main", "other"]),
                ({"list_queries": "legacy"}, ["all", "shared"]),
                ({"list_queries": True}, {"global": ["all", "shared"], "connections": {"main": ["private", "shared"]}}),
            ):
                with self.subTest(option=option), mock.patch("sys.stdout", new_callable=io.StringIO) as output:
                    self.module.handle_run_query2json(config=str(config_path), **option)
                    self.assertEqual(json.loads(output.getvalue()), expected)

    def test_sql_file_argument_dispatches_to_the_default_connection(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            sql_file = Path(directory) / "query.sql"
            sql_file.write_text("SELECT 1", encoding="utf-8")
            with (
                mock.patch.object(self.module, "run_query2json", return_value=[{"value": 1}]) as run,
                mock.patch.object(self.module, "emit_result") as emit,
            ):
                self.module.handle_run_query2json(name=str(sql_file))
            run.assert_called_once_with(
                "default", "@" + str(sql_file), False, False, "", "", "", timezone=None, read_only=False
            )
            emit.assert_called_once_with([{"value": 1}], "json", str(sql_file.with_suffix(".json")), "", "", False, None)


class LiteralNewlineConverterTests(unittest.TestCase):
    def setUp(self) -> None:
        joblib = fake_module("joblib", Parallel=mock.Mock(), delayed=mock.Mock())
        self.module = load_script("bnn", {"joblib": joblib})

    def test_missing_input_returns_an_error_without_a_cleanup_crash(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "missing.txt"
            result = self.module.process_file_chunked(path)
        self.assertFalse(result.success)
        self.assertIn("FileNotFoundError", result.error_msg)

    def test_temporary_file_failure_preserves_the_source(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "example.txt"
            path.write_text(r"one\ntwo", encoding="utf-8")
            with mock.patch.object(self.module.tempfile, "NamedTemporaryFile", side_effect=OSError("no temp")):
                result = self.module.process_file_chunked(path)
            self.assertFalse(result.success)
            self.assertIn("no temp", result.error_msg)
            self.assertEqual(path.read_text(encoding="utf-8"), r"one\ntwo")

    def test_chunk_boundaries_and_external_path_reporting(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "example.txt"
            path.write_text(r"one\ntwo\nthree", encoding="utf-8")
            result = self.module.process_file_chunked(path, chunk_size=1)
            self.assertTrue(result.success)
            self.assertEqual(result.replacements, 2)
            self.assertEqual(path.read_text(encoding="utf-8"), "one\ntwo\nthree")
            self.assertIn(str(path), str(result))

    def test_preserves_existing_crlf_while_converting_literal_newlines(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "example.txt"
            path.write_bytes(b"one\r\ntwo\\nthree\r\n")
            result = self.module.process_file_chunked(path, chunk_size=2)
            self.assertTrue(result.success)
            self.assertEqual(path.read_bytes(), b"one\r\ntwo\nthree\r\n")

    def test_invalid_utf8_does_not_corrupt_the_source(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "example.txt"
            original = b"one\\ntwo\xffthree"
            path.write_bytes(original)
            result = self.module.process_file_chunked(path, chunk_size=2)
            self.assertFalse(result.success)
            self.assertIn("Encoding error", result.error_msg)
            self.assertEqual(path.read_bytes(), original)

    def test_invalid_chunk_sizes_cannot_empty_the_source(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "example.txt"
            original = b"one\\ntwo"
            for chunk_size in (0, -1):
                with self.subTest(chunk_size=chunk_size):
                    path.write_bytes(original)
                    result = self.module.process_file_chunked(path, chunk_size=chunk_size)
                    self.assertFalse(result.success)
                    self.assertEqual(path.read_bytes(), original)

    def test_cli_rejects_zero_chunk_size_before_processing(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "example.txt"
            path.write_bytes(b"one\\ntwo")
            with (
                mock.patch.object(sys, "argv", ["bnn.py", "--chunk-size", "0", str(path)]),
                self.assertLogs(self.module.logger, level="ERROR"),
            ):
                self.assertEqual(self.module.main(), 1)
            self.module.Parallel.assert_not_called()
            self.assertEqual(path.read_bytes(), b"one\\ntwo")


class DeleteLinesCliTests(unittest.TestCase):
    def run_script(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-B", str(ROOT / "dll.py"), *args],
            capture_output=True,
            text=True,
            check=False,
        )

    def test_missing_range_reports_usage_without_changing_the_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "lines.txt"
            path.write_text("one\ntwo\nthree\n", encoding="utf-8")
            for args in ((), (str(path),)):
                with self.subTest(args=args):
                    result = self.run_script(*args)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn("Usage:", result.stderr)
                    self.assertNotIn("Traceback", result.stderr)
                    self.assertEqual(path.read_text(encoding="utf-8"), "one\ntwo\nthree\n")

    def test_deletes_the_requested_inclusive_range(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "lines.txt"
            path.write_text("one\ntwo\nthree\nfour\n", encoding="utf-8")
            result = self.run_script(str(path), "2", "3")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(path.read_text(encoding="utf-8"), "one\nfour")

    def test_invalid_ranges_are_rejected_without_writing(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "lines.txt"
            original = "one\ntwo\nthree\n"
            for start, end in (("0", "1"), ("-1", "2"), ("3", "2"), ("abc", "2")):
                with self.subTest(start=start, end=end):
                    path.write_text(original, encoding="utf-8")
                    result = self.run_script(str(path), start, end)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertNotIn("Traceback", result.stderr)
                    self.assertEqual(path.read_text(encoding="utf-8"), original)


class AudioTranscriptionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.audio = mock.MagicMock()
        self.audio.__len__.return_value = 0
        speech = fake_module(
            "speech_recognition", Recognizer=mock.Mock(), AudioFile=mock.Mock(),
            UnknownValueError=type("UnknownValueError", (Exception,), {}),
            RequestError=type("RequestError", (Exception,), {}),
        )
        pydub = fake_module("pydub", AudioSegment=types.SimpleNamespace(from_file=mock.Mock(return_value=self.audio)))
        self.dependencies = {"speech_recognition": speech, "pydub": pydub}

    def test_cli_duration_is_interpreted_as_seconds(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            audio_path = Path(directory) / "empty.wav"
            output_path = Path(directory) / "output.txt"
            audio_path.touch()
            with (
                mock.patch.dict(sys.modules, self.dependencies),
                mock.patch.object(sys, "argv", ["audio2text.py", str(audio_path), str(output_path), "30"]),
                mock.patch("signal.signal"),
                mock.patch("sys.stdout", new_callable=io.StringIO) as output,
            ):
                runpy.run_path(str(ROOT / "audio2text.py"), run_name="__main__")
            self.assertIn("Chunk duration: 30.0 seconds", output.getvalue())

    def test_interruption_before_first_chunk_reports_zero_completed(self) -> None:
        module = load_script("audio2text", self.dependencies)
        module.interrupted = True
        with tempfile.TemporaryDirectory() as directory:
            audio_path = Path(directory) / "empty.wav"
            audio_path.touch()
            for duration in (0, 1000):
                with self.subTest(duration=duration):
                    self.audio.__len__.return_value = duration
                    output_path = Path(directory) / "output.txt"
                    with mock.patch("signal.signal"), mock.patch("sys.stdout", new_callable=io.StringIO) as output:
                        module.wav_to_text_chunked(str(audio_path), str(output_path))
                    self.assertIn(f"Completed: 0/{int(duration > 0)} chunks", output.getvalue())


class UnusedImportAnalyzerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.module = load_script("afkco", {"zstandard": fake_module("zstandard")})

    def test_report_models_accept_the_fields_used_by_the_analyzer(self) -> None:
        unused = self.module.UnusedImport(
            lineno=1, col_offset=0, statement="import os", unused_names=["os"], module_path="example.py"
        )
        first = self.module.FileReport("first.py")
        second = self.module.FileReport("second.py")
        first.unused_imports.append(unused)
        self.assertEqual(second.unused_imports, [])
        self.assertEqual(unused.lineno, 1)
        self.assertEqual(first.path, "first.py")

    def test_analyzes_and_reconstructs_an_import_statement(self) -> None:
        source = "import os, sys\nprint(os.name)\n"
        unused, error = self.module.analyze_imports(source, "example.py")
        self.assertIsNone(error)
        self.assertEqual(len(unused), 1)
        self.assertEqual(unused[0].unused_names, ["sys"])
        fixed, success = self.module.remove_unused_imports(source, unused)
        self.assertTrue(success)
        self.assertEqual(fixed, "import os\nprint(os.name)\n")

    def test_file_report_and_output(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "example.py"
            source = "import os\nprint('hello')\n"
            path.write_text(source, encoding="utf-8")
            report = self.module.process_py_file(path)
            self.assertEqual(report.path, str(path))
            self.assertEqual(report.file_size, len(source.encode("utf-8")))
            self.assertIsNone(report.error)
            with mock.patch("sys.stdout", new_callable=io.StringIO) as output:
                self.module.print_report([report], use_color=False)
            self.assertIn("import os", output.getvalue())
            missing = self.module.process_py_file(Path(directory) / "missing.py")
            self.assertIn("Read error", missing.error)

    def test_type_checking_block_imports_are_not_flagged(self) -> None:
        source = (
            "from typing import TYPE_CHECKING\n"
            "if TYPE_CHECKING:\n"
            "    import os\n"
            "    from pathlib import Path\n"
            "else:\n"
            "    import math\n"
        )
        unused, error = self.module.analyze_imports(source)
        self.assertIsNone(error)
        self.assertEqual([name for item in unused for name in item.unused_names], ["math"])

    def test_autofix_preserves_indentation_in_nested_blocks(self) -> None:
        source = "def f():\n    import os, sys\n    return os.name\n"
        unused, error = self.module.analyze_imports(source)
        self.assertIsNone(error)
        fixed, success = self.module.remove_unused_imports(source, unused)
        self.assertTrue(success)
        self.assertEqual(fixed, "def f():\n    import os\n    return os.name\n")

    def test_autofix_rejects_removing_the_only_statement_in_a_block(self) -> None:
        source = "def f():\n    import os\n"
        unused, _ = self.module.analyze_imports(source)
        fixed, success = self.module.remove_unused_imports(source, unused)
        self.assertFalse(success)
        self.assertEqual(fixed, source)

    def test_autofix_does_not_remove_inline_code_or_comments(self) -> None:
        for source in ("import os; print('keep')\n", "import os  # keep this comment\n"):
            with self.subTest(source=source):
                unused, _ = self.module.analyze_imports(source)
                fixed, success = self.module.remove_unused_imports(source, unused)
                self.assertFalse(success)
                self.assertEqual(fixed, source)

    def test_type_checking_name_does_not_hide_a_separate_runtime_import(self) -> None:
        source = "from typing import TYPE_CHECKING\nif TYPE_CHECKING:\n    import os\nimport os\n"
        unused, error = self.module.analyze_imports(source)
        self.assertIsNone(error)
        self.assertEqual([name for item in unused for name in item.unused_names], ["os"])

    def test_qualified_type_checking_guard_is_respected(self) -> None:
        source = "import typing\nif typing.TYPE_CHECKING:\n    from pathlib import Path\n"
        unused, error = self.module.analyze_imports(source)
        self.assertIsNone(error)
        self.assertEqual(unused, [])

    def test_autofix_rejects_stale_line_numbers(self) -> None:
        source = "import os\n"
        unused = [self.module.UnusedImport(100, 0, "import os", ["os"])]
        fixed, success = self.module.remove_unused_imports(source, unused)
        self.assertFalse(success)
        self.assertEqual(fixed, source)


class BytecodeCompilerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.module = load_script("mkpik", {})

    def test_legacy_compile_can_delete_source_after_success(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "example.py"
            source.write_text("print('compiled successfully')\n", encoding="utf-8")
            self.assertTrue(self.module.compile_single_file(source, legacy=True, delete_source=True))
            compiled = source.with_suffix(".pyc")
            self.assertFalse(source.exists())
            self.assertTrue(compiled.is_file())
            result = subprocess.run([sys.executable, "-B", str(compiled)], capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, "compiled successfully\n")

    def test_compile_failure_preserves_source_and_existing_bytecode(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "broken.py"
            source.write_text("def broken(:\n", encoding="utf-8")
            compiled = source.with_suffix(".pyc")
            compiled.write_bytes(b"previous bytecode")
            with self.assertRaises(self.module.py_compile.PyCompileError):
                self.module.compile_single_file(source, legacy=True, delete_source=True)
            self.assertEqual(source.read_text(encoding="utf-8"), "def broken(:\n")
            self.assertEqual(compiled.read_bytes(), b"previous bytecode")

    def test_compile_honors_the_configured_cache_prefix(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "example.py"
            source.write_text("value = 1\n", encoding="utf-8")
            prefix = root / "bytecode-cache"
            args = types.SimpleNamespace(
                targets=[str(source)], optimize=0, legacy=False, delete_source=False, pycache_prefix=str(prefix)
            )
            with mock.patch.object(sys, "pycache_prefix", None), mock.patch.dict("os.environ", {}):
                self.module.cmd_compile(args)
                cache = Path(importlib.util.cache_from_source(str(source)))
                self.assertTrue(cache.is_file())
                self.assertTrue(cache.is_relative_to(prefix))
                self.assertTrue(source.is_file())


class MainGuardDryRunTests(unittest.TestCase):
    def test_ast_dry_run_never_changes_files_in_either_execution_mode(self) -> None:
        for workers in (0, 2):
            with self.subTest(workers=workers), tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "example.py"
                original = "print('hello')\n"
                path.write_text(original, encoding="utf-8")
                command = [sys.executable, "-B", str(ROOT / "main_guard_checker.py"), "fix", directory, "--dry-run"]
                if workers:
                    command += ["--parallel", str(workers)]
                result = subprocess.run(command, capture_output=True, text=True, check=False)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(path.read_text(encoding="utf-8"), original)
                self.assertIn("Would add (dry-run): 1", result.stdout)


class PycSizeReportTests(unittest.TestCase):
    def test_equal_sizes_do_not_raise(self) -> None:
        dh = fake_module("dh", fsz=lambda size: f"{size} B", get_files=mock.Mock(return_value=[]), gsz=lambda path: 100)
        module = load_script("mkpyc", {"dh": dh})
        with (
            mock.patch.object(module, "get_context"),
            mock.patch.object(sys, "argv", ["mkpyc.py"]),
            mock.patch("sys.stdout", new_callable=io.StringIO) as output,
        ):
            module.main()
        self.assertIn("space changed", output.getvalue())
        self.assertIn("0 B", output.getvalue())


class InteractiveTypoFixerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.module = load_script("autofix_typo", {"dh": fake_module("dh", PY_KEYWORDS=set())})

    def test_accepting_suggestion_learns_the_correction(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with mock.patch.object(self.module.TypoFixerWithLearning, "_load_word_list"):
                fixer = self.module.TypoFixerWithLearning(learning_db=str(Path(directory) / "patterns.json"))
            with (
                mock.patch.object(fixer, "suggest_correction", return_value="hello"),
                mock.patch("builtins.input", return_value="y"),
                mock.patch("sys.stdout", new_callable=io.StringIO),
                mock.patch("sys.stderr", new_callable=io.StringIO),
            ):
                self.assertEqual(fixer.interactive_fix("helo", "helo world"), "hello")
            self.assertEqual(fixer.learner.learned_corrections["helo"], "hello")

    def test_manual_correction_is_learned(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with mock.patch.object(self.module.TypoFixerWithLearning, "_load_word_list"):
                fixer = self.module.TypoFixerWithLearning(learning_db=str(Path(directory) / "patterns.json"))
            with (
                mock.patch.object(fixer, "suggest_correction", return_value=None),
                mock.patch("builtins.input", side_effect=["e", "world"]),
                mock.patch("sys.stdout", new_callable=io.StringIO),
                mock.patch("sys.stderr", new_callable=io.StringIO),
            ):
                self.assertEqual(fixer.interactive_fix("wurld", "hello wurld"), "world")
            self.assertEqual(fixer.learner.learned_corrections["wurld"], "world")


class CodepenConverterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.module = load_script("codepener", {})

    def test_html_template_preserves_content_and_metadata(self) -> None:
        result = self.module.convert_codepen_html("<p>Hello</p>", title="Demo", charset="UTF-8")
        self.assertEqual(
            result,
            '<!DOCTYPE html>\n<html lang="en">\n<head>\n    <meta charset="UTF-8">\n'
            '    <meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
            '    <title>Demo</title>\n    <link rel="stylesheet" href="style.css">\n'
            '</head>\n<body>\n<p>Hello</p>\n    <script src="script.js"></script>\n'
            '</body>\n</html>\n',
        )

    def test_converts_a_file_with_a_derived_title(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "my-project.html"
            output = Path(directory) / "output.html"
            source.write_text("<p>Demo</p>", encoding="utf-8")
            with mock.patch("sys.stdout", new_callable=io.StringIO):
                self.assertTrue(self.module.process_file(source, output))
            self.assertIn("<title>My Project</title>", output.read_text(encoding="utf-8"))
            self.assertEqual(source.read_text(encoding="utf-8"), "<p>Demo</p>")


class CCommentRemoverTests(unittest.TestCase):
    def setUp(self) -> None:
        self.module = load_script(
            "rmh",
            {"loguru": fake_module("loguru", logger=mock.Mock()), "tqdm": fake_module("tqdm", tqdm=mock.Mock())},
        )

    def test_comments_are_removed_without_touching_quoted_text(self) -> None:
        source = (
            'const char *url = "https://example.com/a"; // remove this\n'
            'const char *quote = "He said \\"hi\\""; /* block // still block */\n'
            'int __STRING_PLACEHOLDER_0__ = 7;\n'
        )
        cleaned, count = self.module.CommentRemover().remove_comments(source)
        self.assertEqual(count, 2)
        self.assertIn('"https://example.com/a"', cleaned)
        self.assertIn('"He said \\"hi\\""', cleaned)
        self.assertIn("int __STRING_PLACEHOLDER_0__ = 7;", cleaned)
        self.assertNotIn("remove this", cleaned)
        self.assertNotIn("still block", cleaned)

    def test_quotes_inside_a_comment_do_not_hide_its_end(self) -> None:
        source = 'int x; /* " quoted text in a comment */\nconst char *s = "hello"; // trailing\n'
        cleaned, count = self.module.CommentRemover().remove_comments(source)
        self.assertEqual(count, 2)
        self.assertIn("int x;", cleaned)
        self.assertIn('const char *s = "hello";', cleaned)
        self.assertNotIn("quoted text", cleaned)

    def test_cpp_raw_strings_and_their_whitespace_are_preserved(self) -> None:
        raw_literal = 'R"tag(first " // not a comment\n\nlast  \n)tag"'
        source = f'const char *s = {raw_literal}; // real comment\n'
        cleaned, count = self.module.CommentRemover().remove_comments(source)
        self.assertEqual(count, 1)
        self.assertIn(raw_literal, cleaned)
        self.assertNotIn("real comment", cleaned)

    def test_block_comments_do_not_join_adjacent_tokens(self) -> None:
        cleaned, count = self.module.CommentRemover().remove_comments("int/**/value = 1;\n")
        self.assertEqual(count, 1)
        self.assertIn("int value = 1;", cleaned)

    def test_continued_line_comment_is_fully_removed(self) -> None:
        source = "// comment \\\nstill a comment\nint value = 1;\n"
        cleaned, count = self.module.CommentRemover().remove_comments(source)
        self.assertEqual(count, 1)
        self.assertNotIn("still a comment", cleaned)
        self.assertIn("int value = 1;", cleaned)

    def test_processing_creates_a_byte_exact_backup(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "example.c"
            original = b"int value = 1; // comment\r\n"
            path.write_bytes(original)
            result = self.module.CommentRemover().process_file(path)
            self.assertTrue(result.success, result.error)
            self.assertEqual(path.with_suffix(".c.bak").read_bytes(), original)
            self.assertEqual(result.backup_size, len(original))
            self.assertNotIn("comment", path.read_text(encoding="utf-8"))

    def test_existing_backup_is_not_overwritten(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "example.c"
            original = b"int value = 1; // comment\n"
            path.write_bytes(original)
            backup = path.with_suffix(".c.bak")
            backup.write_bytes(b"previous backup")
            result = self.module.CommentRemover().process_file(path)
            self.assertFalse(result.success)
            self.assertEqual(path.read_bytes(), original)
            self.assertEqual(backup.read_bytes(), b"previous backup")

    def test_dry_run_does_not_create_a_backup_or_modify_source(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "example.c"
            original = b"int value = 1; // comment\n"
            path.write_bytes(original)
            with mock.patch("sys.stdout", new_callable=io.StringIO):
                self.assertEqual(self.module.main([str(path)], dry_run=True), 0)
            self.assertEqual(path.read_bytes(), original)
            self.assertFalse(path.with_suffix(".c.bak").exists())

    def test_no_backup_mode_removes_only_the_backup_it_created(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "example.c"
            path.write_bytes(b"int value = 1; // comment\n")

            def process(paths, workers):
                return [self.module.CommentRemover().process_file(p) for p in paths]

            with (
                mock.patch.object(self.module, "process_files_parallel", side_effect=process),
                mock.patch("sys.stdout", new_callable=io.StringIO),
            ):
                self.assertEqual(self.module.main([str(path)], keep_backups=False), 0)
            self.assertFalse(path.with_suffix(".c.bak").exists())
            self.assertNotIn("comment", path.read_text(encoding="utf-8"))


class InvalidEscapeScannerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.module = load_script("fixescape", {})

    def test_clean_file_is_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "example.py"
            path.write_text('value = "hello"\n', encoding="utf-8")
            _, has_issues, output, new_content = self.module.check_and_fix_file((str(path), True))
            self.assertFalse(has_issues)
            self.assertEqual(output, [])
            self.assertIsNone(new_content)

    def test_missing_file_error_is_reported_to_the_caller(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "missing.py"
            _, has_issues, output, new_content = self.module.check_and_fix_file((str(path), True))
            self.assertTrue(has_issues)
            self.assertTrue(any("Error reading" in line for line in output))
            self.assertIsNone(new_content)

    def test_crlf_line_endings_are_preserved_when_applying_a_fix(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "example.py"
            path.write_bytes(b'value = "\\q"\r\nother = 1\r\n')
            result = subprocess.run(
                [sys.executable, "-B", str(ROOT / "fixescape.py"), "--apply", str(path)],
                capture_output=True,
                text=True,
                timeout=20,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(path.read_bytes(), b'value = r"\\q"\r\nother = 1\r\n')

    def test_unterminated_string_is_reported_without_a_secondary_crash(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "example.py"
            path.write_text('value = """unterminated\n', encoding="utf-8")
            _, has_issues, output, new_content = self.module.check_and_fix_file((str(path), True))
            self.assertTrue(has_issues)
            self.assertTrue(any("token" in line.lower() for line in output))
            self.assertIsNone(new_content)

    def test_invalid_escape_is_found_and_corrected_without_changing_its_value(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "example.py"
            path.write_text('value = "\\q"\n', encoding="utf-8")
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", DeprecationWarning)
                _, has_issues, _, new_content = self.module.check_and_fix_file((str(path), True))
            self.assertTrue(has_issues)
            self.assertEqual(new_content, 'value = r"\\q"\n')

    def test_mixed_valid_and_invalid_escapes_are_not_changed_unsafely(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "example.py"
            original = 'unsafe = "\\q\\n"\nsafe = "\\q"\n'
            path.write_text(original, encoding="utf-8")
            _, has_issues, output, new_content = self.module.check_and_fix_file((str(path), True))
            self.assertTrue(has_issues)
            self.assertTrue(any("manual" in line.lower() for line in output))
            self.assertEqual(new_content, 'unsafe = "\\q\\n"\nsafe = r"\\q"\n')


if __name__ == "__main__":
    unittest.main()
