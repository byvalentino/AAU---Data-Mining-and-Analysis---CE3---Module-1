"""Run land() with the filesystem watched, and report what it actually did.

Used only by check_04. A kill at a random moment tests luck; this tests
behaviour. We record every file opened for writing, every fsync, and every
rename, in order — then check_04 asserts the four steps happened in the four
right places.

This exists because the first version of check_04 passed a deliberately naive
land() that wrote straight to the destination. It survived because it never
flushed, so the kill destroyed the evidence along with the bug.
"""
from __future__ import annotations

import builtins
import importlib.util
import json
import os
import pathlib
import sys

REPOSITORY = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPOSITORY))

EVENTS: list[dict] = []
WATCHED = pathlib.Path(sys.argv[2]).resolve()   # the landing folder
DESTINATION = pathlib.Path(sys.argv[1]).resolve()
COUNT = int(sys.argv[3])
REPORT = pathlib.Path(sys.argv[4])


def inside(path) -> bool:
    try:
        return pathlib.Path(path).resolve().parent == WATCHED
    except (OSError, ValueError):
        return False


real_open, real_replace = builtins.open, os.replace
real_rename, real_fsync = os.rename, os.fsync


def traced_open(file, mode="r", *args, **kwargs):
    if inside(file) and any(letter in mode for letter in "wxa"):
        EVENTS.append({"event": "open_for_write", "path": str(file), "mode": mode})
    return real_open(file, mode, *args, **kwargs)


def traced_replace(source, target, *args, **kwargs):
    if inside(target):
        EVENTS.append({"event": "rename", "from": str(source), "to": str(target)})
    return real_replace(source, target, *args, **kwargs)


def traced_rename(source, target, *args, **kwargs):
    if inside(target):
        EVENTS.append({"event": "rename", "from": str(source), "to": str(target)})
    return real_rename(source, target, *args, **kwargs)


def traced_fsync(descriptor):
    EVENTS.append({"event": "fsync"})
    return real_fsync(descriptor)


builtins.open, os.replace, os.rename, os.fsync = (
    traced_open, traced_replace, traced_rename, traced_fsync)
# pathlib routes through io.open rather than builtins.open, so cover it too.
import io  # noqa: E402
real_io_open = io.open
io.open = traced_open

spec = importlib.util.spec_from_file_location(
    "lab04", REPOSITORY / "labs" / "04_survive_the_kill.py")
lab = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lab)

try:
    lab.land([{"n": n, "filler": "x" * 200} for n in range(COUNT)], DESTINATION)
    failure = None
except Exception as error:  # report it rather than dying silently
    failure = f"{type(error).__name__}: {error}"

builtins.open, os.replace, os.rename, os.fsync, io.open = (
    real_open, real_replace, real_rename, real_fsync, real_io_open)
REPORT.write_text(json.dumps({"events": EVENTS, "failure": failure}))
