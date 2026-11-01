#!/data/data/com.termux/files/usr/bin/env python
"""Speech <-> text utilities: transcribe audio, speak text, play audio.

Analysis / deduplication
------------------------
- ``audio2text.py`` (WAV, chunked Google STT) and ``audio2txt.py`` (M4A,
  single-shot Google STT) are the same job with different chunking; they
  are one ``transcribe`` command with ``--engine google`` and
  ``--chunk-seconds`` (0 = whole file, the old M4A behaviour).
- ``whisper2txt.py`` is ``transcribe --engine whisper``.
- ``tts_from_file.py`` and ``txt2wav.py`` are functionally identical
  (chunk a text file and speak each chunk); the hardcoded
  ``/sdcard/Download/sample.txt`` became a required positional argument.
- ``mp3play.py`` (GStreamer via PyGObject) is the ``play`` command.

Third-party packages (only needed for the subcommand that uses them):
``SpeechRecognition`` + ``pydub`` (google), ``openai-whisper`` (whisper),
``PyGObject`` (play). The speaker command defaults to ``termux-tts-speak``
as in the originals; on desktop Linux try ``--speaker "espeak-ng"`` or
``--speaker "festival --tts"`` (see ``--speaker`` help).

Original script mapping
-----------------------
  audio2text.py   -> transcribe -e google in.wav [--chunk-seconds 30]
  audio2txt.py    -> transcribe -e google in.m4a --chunk-seconds 0
  whisper2txt.py  -> transcribe -e whisper in.m4a
  tts_from_file.py / txt2wav.py -> speak file.txt
  mp3play.py      -> play song.mp3

Examples
--------
  python3 speech_text_tool.py transcribe -e whisper -m base talk.m4a -o talk.txt
  python3 speech_text_tool.py speak notes.txt --max-chars 1500
"""

import argparse
import shlex
import subprocess
import sys
import tempfile
from collections.abc import Sequence
from pathlib import Path
from urllib.request import pathname2url

DEFAULT_OUTPUT: str = "out.txt"
DEFAULT_CHUNK_SECONDS: int = 30
DEFAULT_MAX_CHARS: int = 3000
DEFAULT_WHISPER_MODEL: str = "base"


def _missing(package: str, pip_name: str) -> SystemExit:
    """Exit with an install hint for an optional dependency."""
    return SystemExit(f"Missing optional dependency '{package}'. Install it with: pip install {pip_name}")


def chunk_text(text: str, max_chars: int = DEFAULT_MAX_CHARS) -> list[str]:
    """Split *text* into chunks of at most *max_chars* on line boundaries."""
    chunks: list[str] = []
    current: str = ""
    for raw_line in text.splitlines():
        line: str = raw_line.strip()
        while len(line) > max_chars:
            if current:
                chunks.append(current)
                current = ""
            chunks.append(line[:max_chars])
            line = line[max_chars:]
        candidate: str = f"{current}\n{line}".strip() if current else line
        if len(candidate) <= max_chars:
            current = candidate
        else:
            if current:
                chunks.append(current)
            current = line
    if current.strip():
        chunks.append(current)
    return [c for c in chunks if c.strip()]


def transcribe_google(audio_path: Path, output: Path, chunk_seconds: int) -> int:
    """Transcribe with Google Web Speech (via SpeechRecognition + pydub)."""
    try:
        import speech_recognition as sr
        from pydub import AudioSegment
    except ImportError:
        raise _missing("speech_recognition/pydub", "SpeechRecognition pydub") from None

    audio = AudioSegment.from_file(str(audio_path))
    total_ms: int = len(audio)
    chunk_ms: int = chunk_seconds * 1000 if chunk_seconds > 0 else total_ms
    num_chunks: int = max(1, (total_ms + chunk_ms - 1) // chunk_ms)
    recognizer = sr.Recognizer()
    output.write_text("", encoding="utf-8")
    parts: list[str] = []
    print(f"Processing {audio_path} ({total_ms / 1000:.1f}s) in {num_chunks} chunk(s)")
    for index in range(num_chunks):
        chunk = audio[index * chunk_ms : min((index + 1) * chunk_ms, total_ms)]
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as handle:
            tmp: str = handle.name
        try:
            chunk.export(tmp, format="wav")
            with sr.AudioFile(tmp) as source:
                data = recognizer.record(source)
            text: str = recognizer.recognize_google(data)
        except (sr.UnknownValueError, sr.RequestError, OSError) as exc:
            print(f"  - chunk {index + 1}/{num_chunks}: {exc}")
            continue
        finally:
            Path(tmp).unlink(missing_ok=True)
        if text.strip():
            parts.append(text)
            with output.open("a", encoding="utf-8") as sink:
                sink.write(text + " ")
            print(f"  + chunk {index + 1}/{num_chunks}: {text[:100]}")
    print(f"Saved transcription to {output} ({len(parts)} chunk(s) with speech)")
    return 0 if parts else 1


def transcribe_whisper(audio_path: Path, output: Path, model_name: str) -> int:
    """Transcribe locally with OpenAI Whisper."""
    try:
        import whisper
    except ImportError:
        raise _missing("whisper", "openai-whisper") from None
    print(f"Loading Whisper model '{model_name}'...")
    model = whisper.load_model(model_name)
    result: dict[str, object] = model.transcribe(str(audio_path))
    text: str = str(result["text"])
    output.write_text(text, encoding="utf-8")
    print(f"Saved transcription to {output}")
    print(text[:200])
    return 0


def cmd_transcribe(args: argparse.Namespace) -> int:
    """Run the ``transcribe`` subcommand."""
    if not args.input.is_file():
        print(f"Error: input not found: {args.input}", file=sys.stderr)
        return 1
    if args.engine == "whisper":
        return transcribe_whisper(args.input, args.output, args.model)
    return transcribe_google(args.input, args.output, args.chunk_seconds)


def cmd_speak(args: argparse.Namespace) -> int:
    """Read a text file aloud, chunk by chunk."""
    if not args.file.is_file():
        print(f"Error: file not found: {args.file}", file=sys.stderr)
        return 1
    text: str = args.file.read_text(encoding="utf-8", errors="ignore")
    chunks: list[str] = chunk_text(text, args.max_chars)
    command: list[str] = shlex.split(args.speaker)
    print(f"Loaded {args.file}: {len(chunks)} chunk(s), speaker={args.speaker!r}")
    for index, chunk in enumerate(chunks, start=1):
        print(f"Speaking chunk {index}/{len(chunks)} ({len(chunk)} chars)...")
        if args.dry_run:
            continue
        try:
            subprocess.run([*command, chunk], check=True)
        except FileNotFoundError:
            print(f"Error: speaker command not found: {command[0]}", file=sys.stderr)
            return 1
    return 0


def cmd_play(args: argparse.Namespace) -> int:
    """Play an audio file or URL with GStreamer (blocking)."""
    try:
        import gi

        gi.require_version("Gst", "1.0")
        from gi.repository import Gst
    except (ImportError, ValueError):
        raise _missing("gi (PyGObject)", "PyGObject  # plus distro GStreamer") from None
    sound: str = args.sound
    uri: str = (
        sound if sound.startswith(("http://", "https://")) else "file://" + pathname2url(str(Path(sound).absolute()))
    )
    Gst.init(None)
    playbin = Gst.ElementFactory.make("playbin", "playbin")
    playbin.props.uri = uri
    if playbin.set_state(Gst.State.PLAYING) != Gst.StateChangeReturn.ASYNC:
        print("Error: could not start playback.", file=sys.stderr)
        return 1
    playbin.get_bus().poll(Gst.MessageType.EOS, Gst.CLOCK_TIME_NONE)
    playbin.set_state(Gst.State.NULL)
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Create the command-line parser."""
    parser = argparse.ArgumentParser(description="Speech <-> text utilities.")
    sub = parser.add_subparsers(dest="command", required=True)

    tr = sub.add_parser("transcribe", help="Audio -> text (Google Web Speech or Whisper)")
    tr.add_argument("input", type=Path, help="Input audio file (wav/m4a/mp3/...)")
    tr.add_argument(
        "-o", "--output", type=Path, default=Path(DEFAULT_OUTPUT), help=f"Output text file (default: {DEFAULT_OUTPUT})"
    )
    tr.add_argument("-e", "--engine", choices=("google", "whisper"), default="google")
    tr.add_argument(
        "--chunk-seconds",
        type=int,
        default=DEFAULT_CHUNK_SECONDS,
        help="Google engine: seconds per request, 0 = whole file (default: 30)",
    )
    tr.add_argument("-m", "--model", default=DEFAULT_WHISPER_MODEL, help="Whisper engine: model name (default: base)")
    tr.set_defaults(handler=cmd_transcribe)

    sp = sub.add_parser("speak", help="Read a text file aloud in chunks")
    sp.add_argument("file", type=Path, help="Text file to speak")
    sp.add_argument(
        "--max-chars", type=int, default=DEFAULT_MAX_CHARS, help="Max characters per utterance (default: 3000)"
    )
    sp.add_argument(
        "--speaker",
        default="termux-tts-speak",
        help="Command that speaks its last argument (default: termux-tts-speak)",
    )
    sp.add_argument("-n", "--dry-run", action="store_true", help="Only list the chunks")
    sp.set_defaults(handler=cmd_speak)

    pl = sub.add_parser("play", help="Play an audio file/URL with GStreamer")
    pl.add_argument("sound", help="Audio file path or http(s) URL")
    pl.set_defaults(handler=cmd_play)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point."""
    args: argparse.Namespace = build_parser().parse_args(argv)
    handler = args.handler
    return int(handler(args))


if __name__ == "__main__":
    sys.exit(main())
