"""Block four — keeping it, and what that costs; Laboratory 4."""

S = "Module 1/exercises/solutions"
LABS = "Module 1/exercises/labs"
MAKE_FIGS = "Module 1/slides/make_figs.py"
CHECK_4 = "Module 1/exercises/verify/check_04.py"


def build(nb, explain) -> None:
    nb.md("""
    ---
    # Block four — Keeping it, and what that costs

    *Slides 62–73.*

    ### Immutability, checksums and the manifest

    *Slides: "Immutability — keep the original exactly as it arrived" and "Checksums and
    the manifest — how you know it is the same file".* Write the incoming bytes once and
    never modify them; every later stage produces new files [@helland2015]. A parser bug
    found in week three is repaired by re-reading week one — if week one still exists. A
    checksum is a short fingerprint of a file's bytes: SHA-256, standardised as FIPS
    180-4 [@nist2015]. A manifest lists every file received with its fingerprint, under
    three fixed key names — `file`, `records`, `sha256` — so a program written by
    somebody else can read it.
    """)
    explain(
        "Fingerprint the slice, and show that one changed byte changes the fingerprint.",
        "The manifest's promise — that the file analysed is the file received — rests on "
        "this property.",
        "Computes the SHA-256 of `data/bus_slice.csv.gz` as it ships, then of the same bytes "
        "with one byte in the middle altered, in memory.",
        "Two unrelated 64-character digests. A colleague who \"fixed\" a file in place cannot "
        "do it unnoticed.")
    nb.code('''
    raw = Path("data/bus_slice.csv.gz").read_bytes()
    altered = bytearray(raw)
    altered[len(raw) // 2] ^= 0x01
    print(f"{len(raw):,} bytes")
    print("SHA-256 as shipped:       ", hashlib.sha256(raw).hexdigest())
    print("SHA-256, one bit changed: ", hashlib.sha256(bytes(altered)).hexdigest())
    ''')

    # --- slide 65: landing -------------------------------------------------------------------------
    nb.md("### Definition — write, flush, fsync, rename, record\n\n*Slide: \"Definition — write, "
          "flush, sync, rename, record\".*")
    explain(
        "Write the landing as the slide defines it, and the invariant it keeps.",
        "A landing is atomic and durable when the bytes go to a temporary file beside the "
        "destination, are flushed and fsynced, renamed onto the final name in one step, and "
        "only then recorded. The rename is atomic within one filesystem "
        "[@ieee2018]; atomicity and durability are two of the four promises of "
        "{@haerder1983}.",
        "Writes, as sympy objects: the sequence as the order of the five steps' instants "
        "(write(tmp), flush, fsync, os.replace(tmp, path), record); the manifest line as a "
        "dictionary; the rule of one line per distinct (file, sha256) as a set size; and the "
        "invariant as an implication that holds at every instant t.",
        "At every instant the manifest is a subset of what is really on disk; record first, "
        "and a kill leaves a claim with nothing behind it.")
    nb.equation("landing", r'''
    steps = [sp.Symbol(rf"t_{{{k}}}^{{\mathrm{{{name}}}}}")
             for k, name in enumerate(("write", "flush", "fsync", "replace", "record"), start=1)]
    formula(sp.And(*[earlier < later for earlier, later in zip(steps, steps[1:])]))
    sha_256 = sp.Function(r"\mathrm{SHA\text{-}256}")
    formula(sp.Eq(sp.Symbol(r"\text{manifest line}"),
                  sp.Dict({sp.Symbol(r"\texttt{file}"): sp.Symbol(r"\text{name}"),
                           sp.Symbol(r"\texttt{records}"): sp.Symbol(r"\text{count}"),
                           sp.Symbol(r"\texttt{sha256}"): sha_256(sp.Symbol(r"\text{bytes written}"))}),
                  evaluate=False))
    j = sp.Symbol("j", integer=True, positive=True)
    lines = NamedSet(r"\{1, \ldots, m\}")
    file_j, sha_j = sp.IndexedBase(r"\mathrm{file}"), sp.IndexedBase(r"\mathrm{sha256}")
    formula(sp.Eq(sp.Symbol("m"), card(sp.ImageSet(sp.Lambda(j, sp.Tuple(file_j[j], sha_j[j])), lines)),
                  evaluate=False),
            r"\text{one line per distinct (file, sha256)}")
    f, h = sp.symbols("f h")
    formula(sp.Implies(sp.Contains(sp.Tuple(f, h), NamedSet(r"\mathrm{manifest}(t)")),
                       sp.And(sp.Contains(f, NamedSet(r"\mathrm{disk}(t)")), sp.Eq(sha_256(f), h))),
            r"\text{at every instant } t")
    ''', slides=["65"])
    nb.md("## Laboratory 4 — the solution, function by function")
    explain(
        "Make the Lab 4 solution's paths resolve in the working copy.",
        "Its demonstration lands files under the folder above its own file.",
        "Points `__file__` at `solutions/lab_04.py` in the working copy.",
        "Every landing below happens inside the working copy.")
    nb.code('''
    __file__ = str(Path.cwd() / "solutions" / "lab_04.py")
    ''')
    explain(
        "Define `land()` as the Lab 4 solution writes it.",
        "Its docstring walks through the three wrong orders and what a kill does to each, "
        "and the fifth property: after a crash you cannot know whether the manifest line "
        "was appended, so landing again must change nothing. The landing's identifier is "
        "(file name, checksum).",
        "Copies `LAB`, `land` and `_already_recorded` from `solutions/lab_04.py`, verbatim.",
        "The function the check traces and kills ten times.")
    nb.source(f"{S}/lab_04.py", "LAB", "land", "_already_recorded",
              cite="[@ieee2018; @nist2015; @haerder1983; @kleppmann2017]")
    explain(
        "Watch what `land()` actually does to the filesystem, the way the check does.",
        "A kill at a random moment tests luck; a trace tests behaviour. The check's "
        "`trace_subject.py` replaces `open`, `os.replace`, `os.rename` and `os.fsync` with "
        "recording versions, runs one landing in its own process, and reports the events "
        "in order.",
        "Puts the solution in place of the stub in the working copy — what `python3 "
        "apply.py` does for this lab — prints `verify/trace_subject.py` in full, runs it on "
        "2,000 records, and prints the events with file names only.",
        "Open the temporary file, fsync, rename, then open the manifest and fsync it: the "
        "slide's order, observed rather than asserted.")
    nb.code('''
    shutil.copyfile("solutions/lab_04.py", "labs/04_survive_the_kill.py")   # as apply.py does
    print(Path("verify/trace_subject.py").read_text())
    trace_folder = Path("landing") / "_trace"
    trace_folder.mkdir(parents=True, exist_ok=True)
    report = trace_folder / "_trace.json"
    subprocess.run([sys.executable, "verify/trace_subject.py", str(trace_folder / "day.jsonl"),
                    str(trace_folder), "2000", str(report)], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    traced = json.loads(report.read_text())
    print("failure:", traced["failure"])
    for event in traced["events"]:
        detail = {key: Path(value).name for key, value in event.items() if key in ("path", "from", "to")}
        print(f"  {event['event']:<15} {detail}")
    ''')
    explain(
        "Point `__file__` at the check, so its paths resolve in the working copy.",
        "`check_04.py` finds its arena and its kill subject relative to its own file.",
        "Points `__file__` at `verify/check_04.py` in the working copy.",
        "The next cell copies the check's kill machinery unchanged.")
    nb.code('''
    __file__ = str(Path.cwd() / "verify" / "check_04.py")
    ''')
    explain(
        "Define the check's kill machinery, verbatim.",
        "The kill test is the lab's claim made physical: start a landing in its own process, "
        "kill it part-way, and inspect what survives. The check aims its kills at fractions "
        "of how long a landing takes on this machine, because fixed delays landed inside the "
        "interpreter's start-up and tested nothing.",
        "Copies the arena, the subject, the record count, the kill fractions, "
        "`manifest_is_honest`, `manifest_lines`, `run_subject` and `time_one_landing` from "
        "`verify/check_04.py`, verbatim.",
        "The same code `make check4` runs.")
    nb.source(CHECK_4, "REPOSITORY", "ARENA", "SUBJECT", "RECORDS", "KILL_FRACTIONS",
              "manifest_is_honest", "manifest_lines", "run_subject", "time_one_landing",
              cite="[@haerder1983; @nist2015]")
    explain(
        "Kill a landing ten times and check that the manifest never lies.",
        "The subject process prints `ready` just before calling `land()`, so each kill is "
        "timed from the start of the write rather than from the start of the interpreter.",
        "Prints `verify/kill_subject.py` in full, measures how long one landing of 60,000 "
        "records takes here, then for each of the ten fractions starts a landing, kills it "
        "at that fraction of the time, and inspects the arena: every manifest line must parse, "
        "name a file that exists, and match that file's checksum; and the destination, if "
        "present, must hold only whole records.",
        "No complaint after any kill. How many kills land mid-write depends on this "
        "machine's speed, so only the two facts the check requires are printed: at least one "
        "kill interrupted a landing, and at least one manifest entry was verified to its "
        "checksum.")
    nb.code('''
    print(SUBJECT.read_text())
    if ARENA.exists():
        shutil.rmtree(ARENA)
    ARENA.mkdir(parents=True)
    calibration = ARENA / "_calibrate"
    landing_seconds = time_one_landing(calibration)
    shutil.rmtree(calibration)
    killed, inspected, complaints = 0, 0, []
    for fraction in KILL_FRACTIONS:
        target = ARENA / "day.jsonl"
        killed += run_subject(target, fraction * landing_seconds)
        complaint, verified = manifest_is_honest(ARENA)
        if complaint:
            complaints.append(complaint)
        inspected += verified
        if target.exists():
            content = target.read_bytes()
            assert content.endswith(b"\\n")
            for line in content.splitlines():
                json.loads(line)
    print(f"{len(KILL_FRACTIONS)} landings of {RECORDS:,} records, each killed at a fraction of a landing's time")
    print("complaints about the manifest after any kill:", complaints)
    agrees("at least one kill landed while land() was running", killed >= 1, True, expected_from="check_04")
    agrees("at least one manifest entry verified to its checksum", inspected >= 1, True, expected_from="check_04")
    shutil.rmtree(ARENA)
    ''')

    # --- slides 66-67: the log ------------------------------------------------------------------------
    nb.md("""
    ### The log, and replay from a byte offset

    *Slides: "The log — four properties that solve most of this" and "Definition — the
    log, and replay from a byte offset".* Records are appended in arrival order and never
    changed; each has a position — its offset — that never moves; any reader can start
    from any offset; many readers can do this independently. That is the whole
    abstraction [@kreps2013; @kreps2014]. In the file built today the offset is a byte
    position, which is why records are one JSON object per line and never reformatted.
    """)
    explain(
        "Write replay as the slide defines it.",
        "A reader that crashed stores where it got to and resumes there; a record number "
        "would need the file re-read, a byte position needs one seek.",
        "Writes, as a sympy set, the records r of the log whose first byte lies at or after "
        "the offset o.",
        "The next cells check the solution against exactly this.")
    nb.equation("replay", r'''
    o = sp.Symbol("o", integer=True, nonnegative=True)
    r_ = sp.Symbol("r")
    first_byte = sp.Function(r"\mathrm{first\_byte}")
    formula(sp.Eq(sp.Function(r"\mathrm{replay}")(sp.Symbol(r"\mathrm{log}"), o),
                  sp.ConditionSet(r_, first_byte(r_) >= o, NamedSet(r"\mathrm{log}")), evaluate=False),
            r"\text{in file order; } o \text{ is a byte offset, not a record number}")
    ''', slides=["67"])
    explain(
        "Define `replay()` as the Lab 4 solution writes it.",
        "It is the second deliverable of Lab 4.",
        "Copies `replay` from `solutions/lab_04.py`, verbatim.",
        "One seek, then read forward.")
    nb.source(f"{S}/lab_04.py", "replay", cite="[@kreps2013]")
    explain(
        "Land a small log and replay it from byte 0 and from the first byte of record 120.",
        "The check does exactly this with 500 records, and requires 500 and then 380, "
        "starting at record 120.",
        "Lands 500 records with `land()`, computes the byte offset where record 120 begins "
        "by summing the lengths of the first 120 lines, and replays from both offsets.",
        "500 and 380, starting at n = 120: the offset is a byte position.")
    nb.code('''
    log_folder = Path("landing") / "_replay"
    log = log_folder / "day.jsonl"
    land([{"n": number, "speed": number / 100} for number in range(500)], log)
    lines = log.read_bytes().splitlines(keepends=True)
    offset = sum(len(line) for line in lines[:120])
    tail = replay(log, offset)
    agrees("records replayed from byte 0", len(replay(log, 0)), 500, expected_from="check_04")
    agrees(f"records replayed from byte {offset:,}", len(tail), 380, expected_from="check_04")
    agrees("first record replayed from that byte", tail[0]["n"], 120, expected_from="check_04")
    ''')

    # --- slides 68-69: idempotence ----------------------------------------------------------------------
    nb.md("""
    ### Idempotence, and the four steps that survive a crash

    *Slides: "Idempotence, and the database promises with the marketing removed" and
    "Write, flush, rename, record — four steps that survive a crash".* An operation is
    idempotent when running it twice gives the same result as running it once
    [@rfc9110]. After a crash you rarely know whether the last step completed; if it is
    idempotent you run it again. Delivering at least once and removing duplicates by
    identifier is achievable; "exactly once" as a network guarantee is not, and systems
    that claim it do precisely this underneath [@kleppmann2017, ch. 11]. Lab 2's
    collector and Lab 4's landing are the two halves.
    """)
    explain(
        "Land the day Lab 2 collects, twice, and then a corrected version of it.",
        "The slide ties the two labs together: Lab 2 removes a repeated page by record "
        "identifier; Lab 4 keys a landing on (file name, checksum), so the same payload "
        "landed twice leaves one manifest entry, and a corrected payload under the same name "
        "leaves a second.",
        "Collects 23 January from a fresh provider with `collect()`, lands it, lands it "
        "again, then lands it with one record's speed corrected, counting manifest lines "
        "after each.",
        "1, 1, 2: a repeat records nothing twice, and a correction is recorded, so the "
        "manifest is a history rather than a state.")
    nb.code('''
    day = collect(Provider(), "2020-01-23")
    destination = Path("landing") / "_idempotence" / "day.jsonl"
    counts = []
    for payload in (day, day, [dict(day[0], speed=0.0)] + day[1:]):
        land(payload, destination)
        counts.append(len(manifest_lines(destination.parent)))
    agrees("manifest lines after land, land again, land a correction", counts, [1, 1, 2], expected_from="check_04")
    ''')
    nb.md("""
    ### Where it lands — bronze, silver, and the data product

    *Slide: "Where it lands — bronze, silver, and the data product".* Bronze is exactly as
    received and immutable; silver is parsed, typed and de-duplicated (Module 2); gold is
    shaped for a question (Modules 2 and 3). A cold path stores everything for later, a
    warm path answers within seconds and keeps less — the batch and speed layers of
    {@marz2015}; the lakehouse is the claim that one open storage layer can serve both
    [@armbrust2021]. The layer diagram shown in block one is not redrawn: it is labels.
    """)

    # --- slides 71-72: format cost -------------------------------------------------------------------
    nb.md("### Definition — what a format costs\n\n*Slides: \"Definition — what a format costs\" "
          "and \"What a format costs, measured\".*")
    explain(
        "Write the cost of a format as the slide defines it.",
        "A format's cost is measured, not asserted: the bytes it writes from the same table "
        "and the seconds to read them back, best of three [@zeng2023].",
        "Writes cost(f) as a pair, with the minimum over three reads.",
        "Sizes travel between machines; seconds are this machine's, today — report both.")
    nb.equation("format_cost", r'''
    f, r = sp.symbols("f r")
    read_time = sp.Function(r"t_{\mathrm{read}}")
    formula(sp.Eq(sp.Function("cost")(f), sp.Tuple(sp.Function("bytes")(f),
                  sp.Min(read_time(f, 1), read_time(f, 2), read_time(f, 3))), evaluate=False),
            sp.Contains(f, sp.FiniteSet(*(sp.Symbol(rf"\texttt{{{name}}}") for name in ("csv", "csv.gz", "parquet"))),
                        evaluate=False))
    ''', slides=["71"])
    explain(
        "Define `format_cost()` as the Lab 4 solution writes it.",
        "It is the third deliverable of Lab 4.",
        "Copies `format_cost` and `_time_once` from `solutions/lab_04.py`, verbatim.",
        "The same frame written once in each format, read back three times.")
    nb.source(f"{S}/lab_04.py", "format_cost", "_time_once", cite="[@zeng2023; @huyen2022]")
    explain(
        "Measure the three formats on the slice, and set the archive's numbers beside them.",
        "The slides quote the archive: 53,155 rows, 14.49, 2.48 and 3.34 megabytes, read in "
        "0.17, 0.213 and 0.014 seconds on the instructor's machine. The slice is 48,290 rows "
        "of one vehicle, and this is a different machine on a different day.",
        "Runs `format_cost()` on the slice in the working copy, checks the two properties the "
        "check grades (Parquet and gzip smaller than plain CSV), and prints each measurement "
        "beside the archive value `measured.json` stores.",
        "The sizes are this data's and repeat exactly on every run; the seconds are "
        "wall-clock, differ on every run, and are printed, never asserted. The ordering of "
        "sizes is the slide's; whether the smallest is also the slowest here, the printed "
        "seconds say.")
    nb.code('''
    measured = format_cost(bus, Path("landing") / "_format")
    assert measured["parquet"]["bytes"] < measured["csv"]["bytes"]
    assert measured["csv_gz"]["bytes"] < measured["csv"]["bytes"]
    stored = archive("format_cost")
    for name in ("csv", "csv_gz", "parquet"):
        beside(f"{name:<8} megabytes", f"{measured[name]['bytes'] / 1e6:.2f} (slice)",
               f"{stored[name]['megabytes']} (archive)", "the archive has 4,865 more rows")
        print(f"  {name:<8} seconds to read back, best of three (slice, this machine, timing): "
              f"{measured[name]['read_s']:.3f}; the slide's archive value {stored[name]['read_s']}")
    beside("Parquet as a share of plain CSV, size",
           f"{measured['parquet']['bytes'] / measured['csv']['bytes']:.2f} (slice)",
           f"{archive('parquet_share_of_csv')['size']} (archive)", "the same trade-off on different rows")
    beside("Parquet as a share of plain CSV, read time",
           f"{measured['parquet']['read_s'] / measured['csv']['read_s']:.2f} (slice, this machine, this run)",
           f"{archive('parquet_share_of_csv')['read_time']} (archive; slide 72's \\"0.08 of its read time\\")",
           "a ratio of two wall-clock times: it depends on the machine, the day and the run, and "
           "the rows differ (the archive has 4,865 more). The slide's 0.08 was measured once on "
           "the instructor's machine; the value here changes every time the notebook runs")
    smallest = min(measured, key=lambda name: measured[name]["bytes"])
    agrees("smallest file (slice; the slide says csv.gz on the archive)", smallest, "csv_gz")
    ''')
    explain(
        "Bring in the slide's format-cost figure function.",
        "The slide's figure is drawn by `make_figs.py` from the archive numbers stored in "
        "`measured.json`, not re-measured, so that the figure does not change on every "
        "rebuild.",
        "Copies `figure_format_cost()` from `make_figs.py`, verbatim.",
        "The next figure is the slide's, from the stored archive numbers.")
    nb.source(MAKE_FIGS, "figure_format_cost")
    explain(
        "Redraw the slide's figure from the archive numbers it was drawn from.",
        "The slide's numbers are the archive's; they cannot be reproduced on the slice, so "
        "the faithful copy is the stored one, labelled as such — its title says \"the whole "
        "archive\".",
        "Runs `figure_format_cost()` on `measured.json`'s `format_cost` entry and checks the "
        "stored values against the numbers the slides print.",
        "The slide's figure exactly; the next figure shows the slice's measurement.")
    nb.figure("format_cost", '''
    figure_format_cost(archive("format_cost"))
    for name, megabytes, seconds in (("csv", 14.49, 0.17), ("csv_gz", 2.48, 0.213), ("parquet", 3.34, 0.014)):
        agrees(f"{name} megabytes (archive, measured.json)", stored[name]["megabytes"], megabytes, 2)
        agrees(f"{name} seconds to read back (archive, measured.json)", stored[name]["read_s"], seconds, 3)
    agrees("Parquet share of CSV, size (archive)", archive("parquet_share_of_csv")["size"], 0.23, 2)
    agrees("Parquet share of CSV, read time (archive)", archive("parquet_share_of_csv")["read_time"], 0.08, 2)
    ''', slides=["72"], treatment="archive: the slide's own code on the numbers measured.json stores")
    explain(
        "Draw the same two panels from the slice, measured a moment ago.",
        "The slide's lesson is to measure on your own data rather than accept a benchmark — "
        "including the slide's.",
        "Draws the sizes and read times `format_cost()` just measured, in the slide's layout.",
        "The sizes repeat on every run; the seconds are this run's.")
    nb.figure("format_cost_on_the_slice", '''
    names = list(measured)
    fig = make_subplots(rows=1, cols=2, subplot_titles=("What it costs to keep", "What it costs to read"))
    megabytes = [measured[name]["bytes"] / 1e6 for name in names]
    seconds = [measured[name]["read_s"] for name in names]
    fig.add_bar(x=names, y=megabytes, marker_color=BLUE, showlegend=False,
                text=[f"{v:.2f}" for v in megabytes], textposition="outside", row=1, col=1)
    fig.add_bar(x=names, y=seconds, marker_color=ORANGE, showlegend=False,
                text=[f"{v:.3f}" for v in seconds], textposition="outside", row=1, col=2)
    fig.update_yaxes(title_text="megabytes on disk", range=[0, max(megabytes) * 1.25], row=1, col=1)
    fig.update_yaxes(title_text="seconds to read back (this run)", range=[0, max(seconds) * 1.25], row=1, col=2)
    fig.update_layout(title="What a format costs — the slice, this machine, best of three (seconds vary by run)")
    show(fig, "format_cost_on_the_slice", width=1100, height=520)
    ''', slides=["72"], treatment="lab data: the slide's measurement repeated on the slice")

    # --- the laboratory ----------------------------------------------------------------------------------
    nb.md("""
    ## Laboratory 4 — Survive the kill

    *Slide: "Lab 4 — Survive the kill".* Three functions, one per definition card.
    Write, flush, fsync, rename, record; then the check kills the process mid-write,
    repeatedly, and lands the same payload twice, which must leave one manifest entry.
    Then replay from an arbitrary offset, and measure the three formats yourself.
    Twenty-five minutes.
    """)
    nb.statement(f"{LABS}/04_survive_the_kill.py")
    explain(
        "Point `__file__` at the stub, so its landing folder resolves in the working copy.",
        "The stub's demonstration writes into `LANDING`, a constant the solution does not "
        "have.",
        "Points `__file__` at `labs/04_survive_the_kill.py` in the working copy.",
        "The next cell copies `LANDING` from the stub unchanged.")
    nb.code('''
    __file__ = str(Path.cwd() / "labs" / "04_survive_the_kill.py")
    ''')
    explain(
        "Define the stub's landing folder.",
        "The stub's `__main__` lands into it.",
        "Copies `LANDING` from the stub, verbatim.",
        "`landing/` in the working copy.")
    nb.source(f"{LABS}/04_survive_the_kill.py", "LANDING")
    explain(
        "Run the stub's `__main__` block against the solved functions.",
        "It is what a student sees when the file is complete.",
        "The lines below are the stub's demonstration, verbatim.",
        "The same hundred records landed twice leave one manifest line; then the three "
        "formats, whose seconds are this run's.")
    nb.step(f"{LABS}/04_survive_the_kill.py", 0)
    explain(
        "Make the solution's demonstration believe it is running from its own file.",
        "It lands under `landing/demo/` beside the folder above its own file.",
        "Points `__file__` back at `solutions/lab_04.py` in the working copy.",
        "The demonstration below runs unchanged.")
    nb.code('''
    __file__ = str(Path.cwd() / "solutions" / "lab_04.py")
    ''')
    explain(
        "Run the solution's demonstration, verbatim.",
        "It lands the whole slice, verifies the manifest against the file's checksum, "
        "demonstrates idempotence, replays from a byte offset, measures the formats and "
        "draws the figure.",
        "The lines below are the solution's `__main__` block, unchanged. Its narration "
        "prints two measured durations — the landing and the format reads — which differ on "
        "every run.",
        "Every step of the block, on the full day.")
    nb.step(f"{S}/lab_04.py", 0)
