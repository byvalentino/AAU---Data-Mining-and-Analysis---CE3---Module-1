"""Lab 4, solved — with the reasoning, not only the code.

Run it: `python3 solutions/lab_04.py` from exercises/, or `python3
labs/04_survive_the_kill.py` after `python3 apply.py`. It lands the slice under
landing/demo/, verifies the manifest, replays from a byte offset, measures the
three formats and draws out/lab_04_format_cost.html (and .png).
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

LAB = 4


def land(records: list[dict], path: pathlib.Path) -> None:
    """Write, flush, fsync, rename, record — and why that order and no other.

    Implements the card "Definition — write, flush, fsync, rename, record":
    write(tmp) → flush → fsync → os.replace(tmp, path) → record, with the
    manifest line {"file", "records", "sha256"}. The rename's atomicity within
    one filesystem is the promise of the portable operating system interface
    (IEEE & The Open Group, 2018, rename()); the checksum is SHA-256 (NIST,
    2015, FIPS 180-4); atomicity and durability are two of the four promises of
    Haerder & Reuter (1983), had here without a database.

    Consider the alternatives and what a kill does to each:

      write straight to the destination      a reader during the write sees half
                                             a file. Worse, a kill leaves half a
                                             file permanently, and nothing marks
                                             it as incomplete.

      write, rename, no fsync                the rename is atomic but the bytes
                                             may still be in the operating
                                             system's buffer. A power cut leaves
                                             an intact name over empty content.

      manifest first, then write             after a kill the manifest claims a
                                             file that does not exist. Every
                                             downstream reader now trusts a lie,
                                             which is worse than missing data
                                             because nobody goes looking.

      write, flush, fsync, rename, record    at every instant the manifest is a
                                             subset of what is really on disk.
                                             That is the invariant, and it is
                                             the only one worth having.

    The temporary file must be in the destination's own folder. os.replace is
    atomic within a filesystem and merely a copy across two.

    The fifth step is not a step at all but a property: after a crash you cannot
    know whether the manifest line was appended, so the only safe thing to do is
    run the landing again — and that is only safe if running it again changes
    nothing. The identifier of a landing is the pair (file name, checksum). Two
    landings of the same payload are the same landing and leave one line; a
    second payload under the same name is a genuine second landing and leaves a
    second line, which is what makes the manifest a history rather than a state.
    Suppressing every repeated append would pass a test that only ever lands the
    same bytes, and would silently lose the corrected file.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = "".join(json.dumps(r, default=str) + "\n" for r in records).encode()
    digest = hashlib.sha256(payload).hexdigest()

    temporary = path.parent / f".{path.name}.partial"
    with open(temporary, "wb") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())      # the bytes are now on the disk itself

    os.replace(temporary, path)        # atomic: old file or new file, never half

    if _already_recorded(path.parent / "manifest.jsonl", path.name, digest):
        return                         # the same landing, run twice; nothing to add

    entry = {
        "file": path.name,
        "records": len(records),
        "sha256": digest,
        "bytes": len(payload),
    }
    with open(path.parent / "manifest.jsonl", "a") as manifest:
        manifest.write(json.dumps(entry) + "\n")
        manifest.flush()
        os.fsync(manifest.fileno())


def _already_recorded(manifest: pathlib.Path, name: str, digest: str) -> bool:
    """Does the manifest already claim this file with this checksum?

    A line that will not parse is skipped rather than raised on: land() may be
    running precisely because the last one was killed, and a reader that dies on
    damaged input cannot be the thing that repairs it.
    """
    if not manifest.exists():
        return False
    for line in manifest.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        if entry.get("file") == name and entry.get("sha256") == digest:
            return True
    return False


def replay(log_path: pathlib.Path, offset: int) -> list[dict]:
    """Read the log forward from a byte offset.

    Implements the card "Definition — the log, and replay from a byte offset":
    replay(log, o) = every record whose first byte lies at position ≥ o, in
    file order. This is the whole of what a log gives you (Kreps, 2013; 2014):
    a position that never moves, so a reader that crashed can store where it
    got to and resume there. Note that the offset is a byte position, not a
    record number — which is exactly why records are one per line and never
    reformatted.
    """
    records = []
    with open(log_path, "rb") as handle:
        handle.seek(offset)
        for line in handle:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def format_cost(frame, folder: pathlib.Path) -> dict:
    """Measure three formats on this data rather than trusting a benchmark.

    Implements the card "Definition — what a format costs": cost(f) = (bytes on
    disk, seconds to read back, best of three) for csv, csv.gz and parquet, the
    same frame written once each. Zeng, Hui, Shen, Pavlo, McKinney & Zhang
    (2023) do the same at scale for the columnar formats.

    The result is usually not what people expect: the smallest file is not the
    fastest to read. Compressed comma-separated values wins on bytes and loses
    on time, because every read must decompress the whole file. Parquet stores
    column by column, so reading it touches less and parses less.
    """
    folder.mkdir(parents=True, exist_ok=True)

    writers = {
        "csv": (lambda p: frame.to_csv(p, index=False), pd.read_csv),
        "csv_gz": (lambda p: frame.to_csv(p, index=False, compression="gzip"), pd.read_csv),
        "parquet": (lambda p: frame.to_parquet(p, index=False), pd.read_parquet),
    }

    results = {}
    for name, (write, read) in writers.items():
        path = folder / f"cost.{name.replace('_', '.')}"
        write(path)
        best = min(_time_once(read, path) for _ in range(3))  # the cost, not the noise
        results[name] = {"bytes": path.stat().st_size, "read_s": round(best, 4)}
    return results


def _time_once(read, path) -> float:
    start = time.perf_counter()
    read(path)
    return time.perf_counter() - start


if __name__ == "__main__":
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
    from _narrate import narrator, show_table, save_figure
    from lab_support import load_slice

    say = narrator(LAB)
    say.info("Lab 4 — land the day so that a kill cannot corrupt it, replay it, and price the formats")
    bus = load_slice()
    say.info("loaded the archive slice, %s rows x %d columns, exactly as it ships",
             f"{len(bus):,}", bus.shape[1])

    folder = pathlib.Path(__file__).resolve().parent.parent / "landing" / "demo"
    if folder.exists():
        for stale in folder.iterdir():
            stale.unlink()
    folder.mkdir(parents=True, exist_ok=True)

    # One landing: the whole slice as one record per line.
    records = bus.to_dict("records")
    log = folder / "day.jsonl"
    started = time.perf_counter()
    land(records, log)
    say.info("landed %s records to %s in %.2f s: write tmp → flush → fsync → os.replace → "
             "record", f"{len(records):,}", log.name, time.perf_counter() - started)

    # The invariant, verified the way the check verifies it.
    entry = json.loads((folder / "manifest.jsonl").read_text().splitlines()[-1])
    digest = hashlib.sha256(log.read_bytes()).hexdigest()
    say.info("manifest line: file=%s records=%s sha256=%s… bytes=%s", entry["file"],
             f"{entry['records']:,}", entry["sha256"][:16], f"{entry['bytes']:,}")
    say.info("the file on disk hashes to the manifest's SHA-256: %s — the manifest is a "
             "subset of what is really on disk", digest == entry["sha256"])

    # Idempotence, demonstrated rather than asserted: land the same payload a
    # second time, as a restarted job would, and count the manifest lines.
    before = len((folder / "manifest.jsonl").read_text().strip().splitlines())
    land(records, log)
    after = len((folder / "manifest.jsonl").read_text().strip().splitlines())
    say.info("landed the identical payload again: manifest lines %d -> %d, because the "
             "landing is idempotent on (file name, checksum)", before, after)
    land(records[:10], log)
    say.info("landed different bytes under the same name: manifest lines -> %d, because "
             "that is a second landing and not a repeat of the first",
             len((folder / "manifest.jsonl").read_text().strip().splitlines()))
    # Put the full day back, so replay below reads what the narration says it does.
    land(records, log)

    # Replay from the start and from a byte offset.
    everything = replay(log, 0)
    lines = log.read_bytes().splitlines(keepends=True)
    skip = 40_000
    offset = sum(len(line) for line in lines[:skip])
    tail = replay(log, offset)
    say.info("replay from byte 0: %s records; from byte %s (where record %s starts): %s "
             "records, the first of them utc_time %s", f"{len(everything):,}",
             f"{offset:,}", f"{skip:,}", f"{len(tail):,}", tail[0]["utc_time"])
    say.info("the offset is a byte position, not a record number — one seek, no re-read")

    # What a format costs, measured here and now.
    cost = format_cost(bus, folder)
    ledger = pd.DataFrame(
        [(name, c["bytes"] / 1e6, c["read_s"]) for name, c in cost.items()],
        columns=["format", "megabytes on disk", "seconds to read (best of 3)"])
    show_table(ledger, "format cost on the slice, this machine, today", logger=say)
    smallest = ledger.loc[ledger["megabytes on disk"].idxmin(), "format"]
    fastest = ledger.loc[ledger["seconds to read (best of 3)"].idxmin(), "format"]
    say.info("smallest: %s; fastest to read: %s — %s", smallest, fastest,
             "the smallest is not the fastest" if smallest != fastest
             else "here the smallest happens to be the fastest too; the numbers say so, not a benchmark")

    fig = make_subplots(rows=1, cols=2, subplot_titles=("What it costs to keep",
                                                        "What it costs to read"))
    fig.add_trace(go.Bar(x=ledger["format"], y=ledger["megabytes on disk"],
                         marker_color="#2A78D6", text=[f"{v:.2f}" for v in ledger["megabytes on disk"]],
                         textposition="outside", showlegend=False), row=1, col=1)
    fig.add_trace(go.Bar(x=ledger["format"], y=ledger["seconds to read (best of 3)"],
                         marker_color="#E07B39",
                         text=[f"{v:.3f}" for v in ledger["seconds to read (best of 3)"]],
                         textposition="outside", showlegend=False), row=1, col=2)
    fig.update_yaxes(title_text="megabytes on disk", row=1, col=1)
    fig.update_yaxes(title_text="seconds to read back", row=1, col=2)
    fig.update_xaxes(title_text="format", row=1, col=1)
    fig.update_xaxes(title_text="format", row=1, col=2)
    fig.update_layout(title="What a format costs on the slice — measured, best of three reads")
    save_figure(fig, "format_cost", LAB, logger=say)

    say.info("what the check grades: land() traced (tmp beside path, fsync before rename, "
             "manifest after) and killed at ten moments with every manifest entry verifying to "
             "its checksum; replay from 0 and from a byte offset; three formats with non-zero "
             "sizes and times, parquet and csv.gz smaller than csv")
