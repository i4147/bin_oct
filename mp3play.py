#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that plays an audio file from either a local file path or a web URL and waits until playback has fully finished before returning. The script should expose a reusable function that accepts a sound source (a local path or an http/https link) and a blocking flag, and should raise a clear, custom error if the audio backend fails to start playback. Requesting non-blocking playback should be rejected with a clear error stating it is not yet supported on this platform. When run directly from the command line, the script should take the sound file path or URL as its first argument and play it, exiting cleanly once playback completes. Focus on reliable completion detection, resource cleanup after playback, and informative error messages for invalid input or playback failures.
---"""

from __future__ import annotations


class PlaysoundException(Exception):
    pass


def playsound(sound, block=True):
    if not block:
        msg = "block=False cannot be used on this platform yet"
        raise NotImplementedError(msg)
    import os
    from urllib.request import pathname2url
    import gi

    gi.require_version("Gst", "1.0")
    from gi.repository import Gst

    Gst.init(None)
    playbin = Gst.ElementFactory.make("playbin", "playbin")
    if sound.startswith(("http://", "https://")):
        playbin.props.uri = sound
    else:
        playbin.props.uri = "file://" + pathname2url(os.path.abspath(sound))
    set_result = playbin.set_state(Gst.State.PLAYING)
    if set_result != Gst.StateChangeReturn.ASYNC:
        raise PlaysoundException("playbin.set_state returned " + repr(set_result))
    bus = playbin.get_bus()
    bus.poll(Gst.MessageType.EOS, Gst.CLOCK_TIME_NONE)
    playbin.set_state(Gst.State.NULL)


if __name__ == "__main__":
    import sys

    fn = sys.argv[1]
    playsound(fn)
