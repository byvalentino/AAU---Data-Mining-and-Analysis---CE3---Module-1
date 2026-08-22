#!/usr/bin/env python3
"""Check 4 — kill it mid-write, repeatedly, and see what survives."""
import json, os, hashlib, shutil, signal, subprocess, sys, pathlib, time
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from _harness import run, explain                                    # noqa: E402
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from lab_support import load_slice                                   # noqa: E402

REPOSITORY = pathlib.Path(__file__).resolve().parent.parent
ARENA = REPOSITORY / "landing" / "_check"
SUBJECT = REPOSITORY / "verify" / "kill_subject.py"
RECORDS = 60_000          # large enough that writing takes measurable time

# Fractions of how long land() actually takes on this machine, measured below.
# Fixed millisecond delays were the earlier bug: they were all spent on the
# interpreter importing pandas, so every kill landed before land() had opened a
# file and the loop asserted nothing at all. Everything past 1.0 lets the write
# finish, which is what puts a real manifest in front of the inspection.
KILL_FRACTIONS = (0.05, 0.15, 0.25, 0.35, 0.5, 0.65, 0.8, 0.95, 1.15, 1.4)


def manifest_is_honest(folder: pathlib.Path) -> tuple[str | None, int]:
    """The invariant: everything the manifest claims is really there, and whole.

    Returns the complaint, if any, and how many entries were checked all the way
    through to their checksum. The count is what proves the inspection happened:
    a loop that never saw a manifest reports no complaint either, and silence
    from a test that never ran looks exactly like success.
    """
    manifest = folder / "manifest.jsonl"
    if not manifest.exists():
        return None, 0
    verified = 0
    for number, line in enumerate(manifest.read_text().splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            return f"manifest line {number} is half-written: {line[:60]!r}", verified
        if "file" not in entry:
            return (f"manifest line {number} has no \"file\" key: {sorted(entry)}. "
                    "The three key names are fixed — \"file\", \"records\", \"sha256\" "
                    "— because a manifest is read by somebody who did not write it.",
                    verified)
        claimed = folder / entry["file"]
        if not claimed.exists():
            return (f"the manifest claims {entry['file']} but it is not on disk. "
                    "You recorded before you renamed.", verified)
        if "sha256" not in entry:
            return (f"manifest line {number} records {entry['file']} with no \"sha256\" "
                    f"key: {sorted(entry)}. Without a checksum the manifest proves the "
                    "file exists and nothing about whether it is the file you wrote, "
                    "which is the whole reason for keeping one.", verified)
        digest = hashlib.sha256(claimed.read_bytes()).hexdigest()
        if digest != entry["sha256"]:
            return (f"{entry['file']} does not match the checksum the manifest "
                    "recorded for it — the file was recorded before it was complete",
                    verified)
        verified += 1
    return None, verified


def manifest_lines(folder: pathlib.Path) -> list[dict]:
    """The manifest as a list of entries. Used where the count is the point."""
    manifest = folder / "manifest.jsonl"
    if not manifest.exists():
        return []
    return [json.loads(line) for line in manifest.read_text().splitlines() if line.strip()]


def run_subject(target: pathlib.Path, kill_after_s: float | None) -> bool:
    """Start one land() in its own process and optionally kill it mid-write.

    The subject prints a line when the expensive imports are done and land() is
    about to be called. The delay is timed from that line, so the kill lands
    inside the write rather than inside the import.

    Returns True if the signal was actually delivered to a running process.
    """
    process = subprocess.Popen(
        [sys.executable, str(SUBJECT), str(target), str(RECORDS)],
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
    process.stdout.readline()            # blocks until land() is about to start
    if kill_after_s is not None:
        time.sleep(kill_after_s)
        if process.poll() is None:
            process.send_signal(signal.SIGKILL)
            process.wait()
            process.stdout.close()
            return True
    process.wait()
    process.stdout.close()
    return False


def time_one_landing(folder: pathlib.Path) -> float:
    """How long land() takes here, so the kills can be aimed at it.

    Machines differ by an order of magnitude. A delay that lands mid-write on a
    laptop lands after the rename on a fast server, and a test whose meaning
    depends on the hardware is not a test.
    """
    folder.mkdir(parents=True, exist_ok=True)
    start = time.perf_counter()
    run_subject(folder / "day.jsonl", None)
    return time.perf_counter() - start


def body(lab):
    if ARENA.exists():
        shutil.rmtree(ARENA)
    ARENA.mkdir(parents=True)

    # Touch all three functions first, in this process, so that an unwritten lab
    # raises NotSolved here and exits 2. Discovered inside a killed subprocess it
    # would look like a failure instead of a blank page.
    lab.land([{"n": 0}], ARENA / "probe.jsonl")
    lab.replay(ARENA / "probe.jsonl", 0)
    lab.format_cost(load_slice().head(50), ARENA)
    shutil.rmtree(ARENA); ARENA.mkdir(parents=True)

    # --- what land() actually does, watched rather than guessed
    report = ARENA / "_trace.json"
    subject = REPOSITORY / "verify" / "trace_subject.py"
    subprocess.run([sys.executable, str(subject), str(ARENA / "day.jsonl"),
                    str(ARENA), "2000", str(report)], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    traced = json.loads(report.read_text())
    assert traced["failure"] is None, f"land() raised: {traced['failure']}"
    events = traced["events"]

    destination = str((ARENA / "day.jsonl").resolve())
    manifest = str((ARENA / "manifest.jsonl").resolve())

    opened = [e["path"] for e in events if e["event"] == "open_for_write"]
    assert not any(pathlib.Path(p).resolve() == pathlib.Path(destination) for p in opened), (
        "land() opened the destination file for writing directly. A kill during that "
        "write leaves half a file, permanently, with nothing marking it incomplete. "
        "Write to a temporary file in the same folder and os.replace it into position.")

    renames = [e for e in events if e["event"] == "rename"]
    assert renames, (
        "land() never renamed anything into place. The atomic step is os.replace: "
        "before it a reader sees the old file, after it the new one, and never a "
        "state in between.")
    assert pathlib.Path(renames[0]["from"]).resolve().parent == ARENA.resolve(), (
        "the temporary file was outside the destination's folder. os.replace is only "
        "atomic within one filesystem; across two it is a copy, and a kill during a "
        "copy leaves exactly the partial file you were avoiding.")

    order = [e["event"] for e in events]
    assert "fsync" in order[:order.index("rename")], (
        "land() renamed without calling os.fsync first. The rename is atomic but the "
        "bytes may still be in the operating system's buffer, so a power cut leaves an "
        "intact name over empty content.")

    manifest_opens = [i for i, e in enumerate(events)
                      if e["event"] == "open_for_write"
                      and pathlib.Path(e["path"]).resolve() == pathlib.Path(manifest)]
    assert manifest_opens, "land() never wrote a manifest entry"
    rename_at = order.index("rename")
    assert manifest_opens[0] > rename_at, (
        "land() wrote the manifest before the data was in place. After a kill the "
        "manifest then claims a file that does not exist — worse than missing data, "
        "because nothing goes looking for it. Record last.")

    shutil.rmtree(ARENA); ARENA.mkdir(parents=True)

    # --- how long land() takes here, so that the kills can be aimed at it
    calibration = ARENA / "_calibrate"
    landing_seconds = time_one_landing(calibration)
    shutil.rmtree(calibration)

    # --- and then the real thing: kill it, repeatedly, and check the invariant
    killed = 0
    manifest_entries_inspected = 0
    for fraction in KILL_FRACTIONS:
        target = ARENA / "day.jsonl"
        when = fraction * landing_seconds
        killed += run_subject(target, when)

        complaint, verified = manifest_is_honest(ARENA)
        assert complaint is None, (
            f"after a kill {when * 1000:.0f} ms into land(): {complaint}")
        manifest_entries_inspected += verified

        if target.exists():
            content = target.read_bytes()
            assert content.endswith(b"\n"), (
                f"after a kill {when * 1000:.0f} ms into land(), {target.name} ends "
                "mid-line")
            for line in content.splitlines():
                try:
                    json.loads(line)
                except json.JSONDecodeError:
                    raise AssertionError(
                        f"after a kill {when * 1000:.0f} ms into land(), "
                        f"{target.name} holds a truncated record")

    # The loop is only evidence if it actually did both things. Without these
    # two lines a kill that always arrived too early, or always too late, reads
    # as ten passes — which is how this check spent ten subprocesses asserting
    # nothing at all in an earlier version.
    assert killed >= 1, (
        f"none of the {len(KILL_FRACTIONS)} kills landed while land() was running "
        f"(it takes about {landing_seconds * 1000:.0f} ms here). The invariant was "
        "never put under pressure, so this check proved nothing. Raise RECORDS.")
    assert manifest_entries_inspected >= 1, (
        f"{len(KILL_FRACTIONS)} kills and not one manifest entry was ever inspected. "
        "Either land() never finished a landing or it never recorded one, so the "
        "checksum test never ran. A test that never runs is not a test that passed.")

    shutil.rmtree(ARENA); ARENA.mkdir(parents=True)

    # --- a clean landing, then replay from an offset
    shutil.rmtree(ARENA); ARENA.mkdir(parents=True)
    records = [{"n": n, "speed": n / 100} for n in range(500)]
    log = ARENA / "day.jsonl"
    lab.land(records, log)

    complaint, verified = manifest_is_honest(ARENA)
    assert complaint is None, complaint
    assert verified == 1, (
        f"one landing should leave exactly one verifiable manifest entry; {verified} "
        "were checked through to a checksum")

    # --- the same landing, run again. At-least-once writing is only usable
    # because the receiving step is idempotent -- the same argument Lab 2 made
    # about at-least-once delivery. This module used to teach that and then land
    # the identical file ten times, appending ten manifest lines, and pass.
    #
    # In its own folder, because a manifest is a history: once a name has been
    # landed twice with different bytes, the earlier entry describes bytes that
    # are no longer on disk. That is honest, and it is not what
    # manifest_is_honest() is looking for.
    repeat_arena = ARENA / "_idempotence"
    repeat_arena.mkdir(parents=True, exist_ok=True)
    target = repeat_arena / "day.jsonl"

    lab.land(records, target)
    first = manifest_lines(repeat_arena)
    assert len(first) == 1, (
        f"one landing left {len(first)} manifest line(s), expected 1")

    lab.land(records, target)                      # the restarted job
    again = manifest_lines(repeat_arena)
    assert len(again) == 1, explain(
        "lab4:idempotent",
        f"the same payload landed twice left {len(again)} manifest lines, not 1",
        "After a crash you cannot know whether the manifest line was appended, so "
        "the only safe thing to do is land it again -- and that is only safe if "
        "landing it again changes nothing. Read the manifest before you append and "
        "skip the line that is already there. The identifier is the pair (file "
        "name, checksum): the same bytes under the same name are the same landing.")
    assert again == first, (
        "the repeat left one manifest line, but a different one. Re-landing the same "
        "payload must leave the record that is already there untouched; rewriting it "
        "loses the moment the data actually arrived.")

    lab.land(records[:120], target)                # different bytes, same name
    third = manifest_lines(repeat_arena)
    assert len(third) == 2, explain(
        "lab4:not-a-repeat",
        f"a different payload under the same name left {len(third)} manifest line(s), "
        "expected 2",
        "Idempotence is not 'append at most once'. A corrected file is a second "
        "landing and has to be recorded, or the manifest silently describes bytes "
        "that were replaced. Key the check on (file name, checksum), not on the "
        "file name alone and not on whether the manifest is empty.")
    assert hashlib.sha256(target.read_bytes()).hexdigest() == third[-1]["sha256"], (
        "the second landing recorded a checksum that is not the checksum of the file "
        "now on disk")

    shutil.rmtree(repeat_arena)

    everything = lab.replay(log, 0)
    assert len(everything) == 500, (
        f"replay from offset 0 gave {len(everything)} records, expected 500")

    lines = log.read_bytes().splitlines(keepends=True)
    offset = sum(len(line) for line in lines[:120])
    tail = lab.replay(log, offset)
    assert len(tail) == 380, (
        f"replay from byte {offset} gave {len(tail)} records, expected 380. "
        "An offset is a byte position, not a record number.")
    assert tail[0]["n"] == 120, (
        f"replay from byte {offset} started at record {tail[0]['n']}, expected 120")

    # --- the format measurement
    cost = lab.format_cost(load_slice(), ARENA)
    for name in ("csv", "csv_gz", "parquet"):
        assert name in cost, f"format_cost() did not report '{name}'"
        assert cost[name]["bytes"] > 0 and cost[name]["read_s"] > 0, \
            f"format_cost()['{name}'] has a zero size or time — did you measure it?"
    assert cost["parquet"]["bytes"] < cost["csv"]["bytes"], (
        "your measurement says Parquet is larger than comma-separated values on this "
        "data. Check that you wrote the whole frame to each.")
    assert cost["csv_gz"]["bytes"] < cost["csv"]["bytes"], \
        "compressed comma-separated values should be smaller than uncompressed"

    shutil.rmtree(ARENA, ignore_errors=True)


run(4, "04_survive_the_kill", "land", body)
