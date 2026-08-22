"""Lab 4 — Survive the kill.

Why this lab exists: a crash is normal, and a pipeline that a crash can leave
half-written is one you must rebuild rather than restart. You prove that your
landing survives being killed at any moment — old state or new state, never a
half file, never a manifest that claims what is not there — that a reader can
resume from a byte offset, and that you measure what a format costs instead of
believing a benchmark.
Where it sits: Block 4 — "Write, flush, rename, record — four steps that
survive a crash", and the definition slides "Definition — write, flush, fsync,
rename, record", "Definition — the log, and replay from a byte offset" and
"Definition — what a format costs".
What the check grades: land() is traced — temporary file in the destination's
folder, fsync before rename, manifest written after — and killed at ten moments,
after each of which every manifest entry must verify to its SHA-256 checksum
and no partial file may remain; landing the same payload twice leaves one
manifest entry and landing a different one under the same name leaves two;
replay() from 0 returns every record and from a later byte offset exactly the
rest; format_cost() reports three formats with non-zero sizes and read times,
Parquet and gzip both smaller than plain comma-separated values.
Needs: hashlib, json, os, pathlib, time, pandas; lab_support.load_slice; for the
    demonstration _narrate and plotly.

Twenty-five minutes.

The check will kill your process, repeatedly, at moments you do not choose. What
survives must always be consistent: either the complete old state or the complete
new state, never half a file. This is four lines of discipline, and it is the
difference between a pipeline you can restart and one you must rebuild.

What you write: land(records, path), replay(log_path, offset),
format_cost(frame, folder).

land — write, flush, fsync, rename, record

    1. Write the records to a temporary file *in the same folder* as the
       destination. Same folder matters: rename is only atomic within one
       filesystem.
    2. Flush, and call os.fsync, so the bytes are on the disk and not in a
       buffer that a kill would discard.
    3. os.replace the temporary file onto the destination. A reader now sees
       either the old file or the new one. There is no moment in between.
    4. Only then append a line to the manifest. The manifest is the truth: a
       file it does not mention does not exist, and it must never mention a
       file that is missing or incomplete.

    Do it in the other order — manifest first — and after a kill you will claim
    data you do not have. The check tests exactly that.

    5. And because you cannot tell, after a crash, whether step 4 completed,
       land() must be safe to run again: the same payload landed twice leaves
       ONE manifest entry, not two. That is idempotence, and the identifier is
       the pair (file name, checksum) — read the manifest before you append and
       skip a line that is already there. A different payload under the same
       name is a different landing and does get its own line, so "never append
       twice" is not the answer either.

    The lab that hands you at-least-once delivery (Lab 2) and the lab that hands
    you at-least-once writing are the same lesson twice: the far end promises to
    deliver at least once, your own retry loop promises to write at least once,
    and both are only usable because the receiving step is idempotent.

replay — a log is only useful if you can resume

    Return the records in the log from byte `offset` onwards. One JavaScript
    Object Notation record per line, so an offset is just a place to seek to.

format_cost — measure, do not assume

    Write the frame as comma-separated values, as gzip-compressed
    comma-separated values, and as Parquet. Return the size of each in bytes and
    the seconds taken to read each back. Report what you measured, even if it
    contradicts what you expected. Especially then.
"""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import sys
import time

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from lab_support import NotSolved, load_slice  # noqa: E402
from _narrate import narrator, show_table, save_figure  # noqa: E402,F401

LAB = 4
LANDING = pathlib.Path(__file__).resolve().parent.parent / "landing"


def land(records: list[dict], path: pathlib.Path) -> None:
    """Write `records` to `path` so that a kill can never leave a partial file.

    Then append one line to path.parent / "manifest.jsonl" — one JavaScript
    Object Notation object per line, with exactly these three key names:

        "file"     the file's name only, not its folder, as a string
        "records"  how many records the file holds, as a whole number
        "sha256"   the checksum of the bytes you wrote, as a hexadecimal string

    Definition graded by the check:
        write(tmp) → flush → fsync → os.replace(tmp, path) → record
        · manifest line = {"file": name, "records": count, "sha256": SHA-256(bytes written)}, one line per distinct (file, sha256)
        (IEEE & The Open Group, 2018, rename(); NIST, 2015, FIPS 180-4;
        Haerder & Reuter, 1983; Kleppmann, 2017). Choices: tmp lives in path's
        own folder, because rename is atomic only within one filesystem; the
        checksum is SHA-256 of exactly the bytes written; the manifest is
        appended last and fsynced too; the identifier that makes the landing
        idempotent is the pair (file name, checksum), so re-landing the same
        payload appends nothing and landing different bytes under the same name
        appends a second line. Slide: "Definition — write, flush, fsync,
        rename, record".

    The names are fixed rather than left to taste because a manifest is read by
    somebody who did not write it — months later, possibly by a program. A
    checksum under a key nobody thinks to look for is a checksum nobody checks,
    and the check treats a missing "sha256" as a failed integrity test, not as
    a test to skip.

    You may add further keys of your own; these three must be present.

    Needs: json.dumps, open(..., "wb"), file.flush, os.fsync, os.replace,
        hashlib.sha256(...).hexdigest, open(..., "a"), and a read of the
        manifest before the append
    """
    # TODO: write, flush, fsync, rename, record — in that order.
    raise NotSolved("land(records, path) still raises instead of writing atomically")


def replay(log_path: pathlib.Path, offset: int) -> list[dict]:
    """Every record in the log from byte `offset` onwards, in order.

    Definition graded by the check:
        replay(log, o) = every record whose first byte lies at position ≥ o, in
        file order; o is a byte offset, not a record number
        (Kreps, 2013; Kreps, 2014). Choice: one record per line, so seeking to
        a line's first byte and reading forward is the whole implementation.
        Slide: "Definition — the log, and replay from a byte offset".

    Needs: open(..., "rb"), file.seek, iteration over lines, json.loads
    """
    # TODO: open the file, seek to offset, read forward.
    raise NotSolved("replay(log_path, offset) still raises instead of returning records")


def format_cost(frame, folder: pathlib.Path) -> dict:
    """Measure what three storage formats cost on this data.

    Returns:
        {"csv":     {"bytes": int, "read_s": float},
         "csv_gz":  {"bytes": int, "read_s": float},
         "parquet": {"bytes": int, "read_s": float}}

    Definition graded by the check:
        cost(f) = (bytes on disk, seconds to read back, best of three) for
        f ∈ {csv, csv.gz, parquet}, one frame written once each
        (Zeng, Hui, Shen, Pavlo, McKinney & Zhang, 2023). Choices: best of
        three reads, so that the cost is measured and not the noise; the whole
        frame, every column, to each format. Slide: "Definition — what a format
        costs".

    Needs: pandas, time.perf_counter, pathlib.Path.stat().st_size, min
    """
    # TODO: write each format, read each back, time the reads.
    raise NotSolved("format_cost(frame, folder) still raises instead of returning sizes")


if __name__ == "__main__":
    say = narrator(LAB)
    LANDING.mkdir(exist_ok=True)
    bus = load_slice()
    say.info("archive slice, %s rows, as shipped", f"{len(bus):,}")
    land(bus.head(100).to_dict("records"), LANDING / "day.jsonl")
    land(bus.head(100).to_dict("records"), LANDING / "day.jsonl")   # the same payload, again
    say.info("landed twice, manifest lines: %d",
             len((LANDING / "manifest.jsonl").read_text().strip().splitlines()))
    for name, cost in format_cost(bus, LANDING).items():
        say.info("%-9s %7.2f MB  %.3f s", name, cost["bytes"] / 1e6, cost["read_s"])
