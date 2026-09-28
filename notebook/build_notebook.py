#!/usr/bin/env python3
"""Build Module 1's demonstration notebook, and execute it.

    python "Module 1/notebook/build_notebook.py"            build and run
    python "Module 1/notebook/build_notebook.py" --no-run   build only

Rewritten 28 September 2026 to the specification Module 4's notebook was rebuilt
to. The notebook follows the deck, `slides/Module1.pptx`, block by block, then
its "References and Backup Material", and holds itself to three things:

  every image on a shown slide is drawn here by Python -- on the lab data where
      the slide shows data, by the deck's own figure code where the deck has
      some, and labelled "illustrative" where the slide's picture carries a
      concept and no data; the images it does not draw (photographs, logos,
      posters, vendor diagrams, the video) are listed with the reason in
      notebook/figure_map.json;
  every lab exercise is stated as its stub states it, and its solution runs step
      by step with every function's code visible -- copied verbatim from
      exercises/solutions/, lab_support.py, _narrate.py, mock/provider.py and
      the checks' fixtures, and held to those files by
      tools/check_notebook_sources.py;
  every number the slides print is recomputed on the lab data; agrees() stops
      the run if the deck and the code disagree, and beside() prints the archive
      value the slide quotes next to the slice's, with the reason they differ.

Data: only what the labs ship -- `exercises/data/bus_slice.csv.gz` (shuttle
VJRD1A10224000055, 22 and 23 January 2020, 48,290 readings as they arrived,
out of time order), Lab 2's synthetic provider and the checks' synthetic
fixtures. The archive values the deck quotes are read from
`slides/measured.json`, never recomputed from the archive, which is not in git.

The notebook is executed from `Module 1/exercises` and immediately works in a
temporary copy of that folder, because Labs 3 and 4 write files (DATA_PROFILE.md,
out/, landing/) and a demonstration must not touch a student's folder. Needs the
lab requirements plus notebook/requirements.txt.
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(HERE))

from notebook_kit import Notebook, execute  # noqa: E402

OUTPUT = HERE / "Module1_demonstration.ipynb"
EXERCISES = HERE.parent / "exercises"
SUPPORT = "Module 1/exercises/lab_support.py"
NARRATE = "Module 1/exercises/_narrate.py"
MAKE_FIGS = "Module 1/slides/make_figs.py"

nb = Notebook(1, HERE / "references.json")


# The shape of every explanation cell above a code cell.
def explain(goal: str, why: str, what: str, so_what: str, extra: str = "") -> None:
    text = (f"**Goal.** {goal}\n\n**Why.** {why}\n\n**What the code does.** {what}\n\n"
            f"**So what.** {so_what}")
    nb.md(text + (f"\n\n{extra}" if extra else ""))


# =============================================================================
# Front matter
# =============================================================================

def front_matter() -> None:
    nb.md("""
    # Module 1 — Collecting and storing data

    **Data Mining and Analysis (course code CE3) · Aalborg University, Copenhagen**

    *How does data from the world enter a system so that it can still be trusted
    years later?*

    This notebook is the deck's companion. It follows the same four blocks in the
    same order, then the deck's "References and Backup Material". It draws every
    picture on the slides that carries data or a concept, states every laboratory
    exercise as the lab file states it, and runs the reference solution with all
    of its code on the page.

    | Block | The question | Laboratory |
    |---|---|---|
    | 1 | What is a pipeline, and what kind of data do you have? | Lab 1 — Is it independent? |
    | 2 | Where does data come from, and what may you take? | Lab 2 — Collect the day |
    | 3 | What do you actually have, measured? | Lab 3 — Profile the day |
    | 4 | How do you keep it, and what does that cost? | Lab 4 — Survive the kill |

    **How to read it.** Every code cell has a short note above it: the *goal*, *why*
    it is done, *what the code does*, and *so what* — what the result lets you say.
    Cells that begin `# Source: … verbatim` are copied from the laboratory files and
    checked against them, so the code you read is the code the labs run. Cells that
    draw a figure name the slide they reproduce. Formulas are written in Python with
    `sympy` and displayed as LaTeX.

    **Scope of every number.** The deck quotes two kinds of number. Most are
    measured on the slice you clone — `exercises/data/bus_slice.csv.gz`, one shuttle,
    both days, 48,290 readings — and are recomputed here and checked: `agrees()`
    stops the notebook if the code and the slide disagree. `agrees()` also checks a
    few values the deck does not print — from a lab file, the lab's check or
    `measured.json` — and then names that source instead of *deck*. A few are measured on the
    full archive (`data/bus.csv`, two shuttles, 53,155 readings), which is not in
    this repository. For those the notebook computes the same quantity on the slice
    and prints the archive value the slide quotes beside it, labelled *archive*,
    with the reason the two differ (`beside()`).

    **How to run it.** From `Module 1/exercises`, after `bash setup.sh` and
    `pip install -r ../notebook/requirements.txt`. It runs in under two minutes and
    writes nothing into `exercises/`: it works in a temporary copy.
    """)


# =============================================================================
# Set-up
# =============================================================================

def setup() -> None:
    nb.md("## Set-up")
    explain(
        "Load the libraries, and define the small tools every later cell uses.",
        "A notebook that claims to reproduce a deck needs a way to show a figure, a "
        "formula and a number side by side with what the slide printed.",
        "`show()` renders a plotly figure to a static image embedded in the notebook, so "
        "it displays anywhere, including offline. `formula()` displays sympy expressions "
        "(or LaTeX strings) as LaTeX; `card` and `NamedSet` let a formula count the "
        "elements of a set built over the rows of a file. `agrees()` prints a number "
        "stated elsewhere beside the same number computed here, names where the stated "
        "value comes from — *deck* when a slide prints it, otherwise the lab file, "
        "`measured.json` or the check that states it — and stops the run when they "
        "differ; `beside()` prints two numbers that are expected to differ, with the "
        "reason, and records them for the closing table.",
        "If the deck and the code ever disagree, this notebook fails to run rather than "
        "quietly showing a different number.")
    nb.code(r'''
    import atexit
    import hashlib
    import json
    import math
    import os
    import shutil
    import subprocess
    import sys
    import tempfile
    import types
    import warnings
    from pathlib import Path

    import numpy as np
    import pandas as pd
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    import sympy as sp
    from IPython.display import Image, Math, display

    warnings.filterwarnings("ignore", category=FutureWarning)
    pd.set_option("display.width", 120)
    pd.set_option("display.max_colwidth", 100)

    # The course palette: reference blue, comparison orange, neutral grey, red only
    # for what fails; green and navy for the notebook's own annotations.
    BLUE, ORANGE, GREY, RED, GREEN, NAVY = ("#2A78D6", "#E07B39", "#52514E",
                                           "#C0392B", "#2E8B57", "#1F2A5A")


    def show(fig, name, width=1000, height=560):
        """Draw a plotly figure as a static image inside the notebook."""
        fig.update_layout(template="plotly_white", width=width, height=height)
        if fig.layout.margin.t is None:          # unless the figure asked for its own room
            fig.update_layout(margin=dict(l=70, r=30, t=70, b=60))
        display(Image(fig.to_image(format="png", width=width, height=height, scale=1)))


    def formula(*parts):
        """Display sympy expressions (or LaTeX strings) side by side."""
        pieces = [p if isinstance(p, str) else sp.latex(p, order="none") for p in parts]
        display(Math(r"\qquad ".join(pieces)))


    class card(sp.Function):
        """The number of elements of a set, |S|, as an unevaluated sympy object."""
        def _latex(self, printer, exp=None):
            return r"\left|" + printer._print(self.args[0]) + r"\right|"


    class NamedSet(sp.Set):
        """A set known only by its name (the rows of a file, what is on disk), so that
        sympy's set-builder objects can be written over it."""
        def __new__(cls, name):
            return sp.Set.__new__(cls, sp.Symbol(name))

        def _latex(self, printer):
            return self.args[0].name

        def _contains(self, other):
            return None


    def agrees(what, computed, stated, places=None, expected_from="deck"):
        """A number stated elsewhere, recomputed here. Stops the run on a mismatch.
        places=None compares exactly (counts, lists); otherwise to that many decimals.
        expected_from names where the stated value comes from: "deck" when a slide
        prints it, otherwise the file or the check that states it."""
        if places is None:
            if computed != stated:
                raise AssertionError(f"{what}: {expected_from} says {stated}, the code gives {computed}")
            shown = computed
        else:
            shown = round(float(computed), places)
            if abs(shown - float(stated)) > 0.5 * 10 ** -places + 1e-12:
                raise AssertionError(f"{what}: {expected_from} says {stated}, the code gives {shown}")
            shown = int(shown) if places == 0 else shown
        print(f"  {what:<66} {expected_from + ' ' + str(stated):<26} computed {shown}")


    DIFFERENCES = []   # every beside() call, gathered for the closing table


    def beside(what, computed, stated, why):
        """Two numbers that are expected to differ, printed with the reason."""
        DIFFERENCES.append((what, str(computed), str(stated), why))
        print(f"  {what}: computed here {computed}, stated {stated} — {why}")
    ''')

    explain(
        "Work in a temporary copy of `exercises/`, never in the folder itself.",
        "Labs 3 and 4 write files — `DATA_PROFILE.md`, `out/`, `landing/` — and the kill "
        "test starts subprocesses that write there too. A demonstration that ran in the "
        "student's own folder would overwrite their work and leave the instructor's "
        "outputs behind in it. Module 1's labs are delivered; nothing here may change them.",
        "Remembers where the notebook was started (`Module 1/exercises`) and where the "
        "deck's measurements live (`slides/measured.json`), copies `exercises/` into a new "
        "temporary folder without any earlier run's outputs, moves the working directory "
        "there, and arranges for the copy to be deleted when the kernel stops.",
        "Every relative path below — `data/bus_slice.csv.gz`, `solutions/`, `verify/` — "
        "resolves exactly as it does for a student, inside a folder nobody else uses.")
    nb.code(r'''
    EXERCISES = Path.cwd()
    assert (EXERCISES / "lab_support.py").exists(), "run this notebook from Module 1/exercises"
    SLIDES = EXERCISES.parent / "slides"

    WORK = Path(tempfile.mkdtemp(prefix="module1_notebook_")) / "exercises"
    shutil.copytree(EXERCISES, WORK, ignore=shutil.ignore_patterns(
        "out", "landing", "DATA_PROFILE.md", "__pycache__", ".your_attempt", ".attempts.json"))
    os.chdir(WORK)
    atexit.register(shutil.rmtree, WORK.parent, ignore_errors=True)
    print("working in a temporary copy of exercises/:",
          sorted(p.name for p in WORK.iterdir() if not p.name.startswith(".")))
    ''')

    explain(
        "Read the archive values the deck quotes, from the file the deck's own script wrote.",
        "A handful of slide numbers are measured on the full archive, which is not in the "
        "repository. They must not be retyped by hand, and they must not be presented as "
        "if the slice had produced them.",
        "Loads `slides/measured.json`, written by `slides/make_figs.py` in full mode, and "
        "defines `archive(key)`, which returns the stored value of one entry.",
        "Wherever a slide quotes the archive, the notebook prints this stored value beside "
        "the slice's own, labelled *archive*.")
    nb.code(r'''
    ARCHIVE = json.loads((SLIDES / "measured.json").read_text())


    def archive(key):
        """The value the deck's own script stored for one archive-wide measurement."""
        return ARCHIVE[key]["value"]


    print(f"{len(ARCHIVE) - 1} stored measurements; the archive's rows: {archive('rows'):,} "
          f"from {archive('vehicles')} vehicles — note: {ARCHIVE['rows']['note']}")
    ''')

    nb.md("""
    ### The laboratory machinery, in full

    The four labs share two small files: `lab_support.py` (the unsolved marker and the
    data loader) and `_narrate.py` (how the solutions tell their story). Nothing is
    imported from them: the next cells *are* them.
    """)
    explain(
        "Let `lab_support.py`'s path constants resolve inside a notebook.",
        "The file finds its data relative to its own location (`__file__`), which a "
        "notebook does not have.",
        "Points `__file__` at `lab_support.py` in the working copy.",
        "The next cell can then be copied from the file unchanged.")
    nb.code('''
    __file__ = str(Path.cwd() / "lab_support.py")
    ''')
    explain(
        "Define the data loader every lab uses, and the marker an unsolved lab raises.",
        "`load_slice()` returns the bytes as they ship and sorts nothing — the disorder "
        "of the rows is Lab 1's first finding, so the loader must not hide it.",
        "Copies `HERE`, `SLICE`, `NotSolved` and `load_slice` from `lab_support.py`, "
        "verbatim, with their docstrings.",
        "Every number below starts from `load_slice()`, exactly as the labs do.")
    nb.source(SUPPORT, "HERE", "SLICE", "NotSolved", "load_slice")
    explain(
        "Give the solutions the narration helpers they print with.",
        "Each solution's demonstration tells its story through `narrator`, `show_table` "
        "and `save_figure`; running the demonstration here needs the same three.",
        "Copies `narrator` and `show_table` verbatim from `_narrate.py`, with the clock and "
        "the formatter they use.",
        "The narrator prefixes every line with the seconds since the kernel started, so "
        "those prefixes differ from one run to the next; nothing else in its lines does, "
        "apart from the timings Lab 4 measures on purpose.")
    nb.source(NARRATE, "_START", "_Elapsed", "narrator", "show_table")
    explain(
        "Define the third narration helper, `save_figure`, for a notebook.",
        "In the terminal `_narrate.save_figure` writes `out/lab_0K_<name>.html` and a "
        "`.png` twin, which a notebook reader never opens.",
        "Applies the same layout as the file's version and shows the figure in place.",
        "Every figure a solution draws appears under the cell that drew it.")
    nb.code('''
    def save_figure(fig, name, lab, logger=None, width=1000, height=560):
        """The notebook's save_figure: the layout of _narrate.save_figure, shown in
        place instead of written to out/lab_0K_<name>.html."""
        fig.update_layout(template="plotly_white", width=width, height=height,
                          margin=dict(l=60, r=30, t=60, b=60))
        show(fig, f"lab_{lab:02d}_{name}", width=width, height=height)
        (logger.info if logger else print)(f"figure -> shown here (lab_{lab:02d}_{name})")
    ''')
    explain(
        "Make the labs' own `import` lines find the code defined in this notebook.",
        "The solutions' demonstrations begin with `from _narrate import …` and "
        "`from lab_support import …`, and Lab 2 imports its provider from `mock.provider`. "
        "Left alone, Python would import the files from the working copy — code nobody "
        "reading this notebook has seen.",
        "`module(name, **objects)` registers a stand-in module in `sys.modules` whose "
        "attributes are the objects defined in the cells above. An `import` of that name "
        "then returns them, and the verbatim lines run unchanged.",
        "Every function a demonstration calls is one printed in this notebook.")
    nb.code('''
    def module(name, **objects):
        """A stand-in module whose attributes are objects defined in this notebook."""
        stand_in = types.ModuleType(name)
        stand_in.__dict__.update(objects)
        sys.modules[name] = stand_in
        return stand_in


    module("lab_support", HERE=HERE, SLICE=SLICE, NotSolved=NotSolved, load_slice=load_slice)
    module("_narrate", narrator=narrator, show_table=show_table, save_figure=save_figure)
    print("stand-ins registered:", [n for n in ("lab_support", "_narrate") if n in sys.modules])
    ''')

    nb.md("""
    ### The deck's own measuring code

    Every number on the slides was measured by `slides/make_figs.py`. The next cells
    copy its measuring functions verbatim, so the deck's numbers can be measured again
    here with the deck's own code — on the slice, which is what the labs ship.
    """)
    explain(
        "Bring in `make_figs.py`'s constants and its two measuring functions.",
        "`measure()` is what produced the archive-wide numbers in `measured.json`; "
        "`measure_slice()` produced the slice numbers. Running them here on the slice is "
        "the most direct test of which slide numbers the lab data reproduce.",
        "Copies the vehicle, the first day, the palette, the lag grid, the estimator "
        "(`sample_autocorrelation`, the Box–Jenkins form Lab 1 grades), `measure()`, "
        "`measure_format_cost()`, `measure_parquet_share()` and `measure_slice()`. Two "
        "names are deliberately not copied: `HERE` and `SLICE`, which in `make_figs.py` "
        "point at `slides/`; here `SLICE` stays `lab_support`'s path to the same file, "
        "so `measure_slice()`'s default argument reads the working copy's slice.",
        "From here on a number labelled *the deck's own code* was computed by the "
        "function that computed the slide's.")
    nb.source(MAKE_FIGS, "BOTH_DAYS_VEHICLE", "FIRST_DAY", "BLUE", "ORANGE", "GREY", "RED",
              "MINIMUM_PAIRS", "LAGS", "entry", "sample_autocorrelation", "measure",
              "measure_format_cost", "measure_parquet_share", "measure_slice",
              cite="[@box2015; @hyndman2021; @bayley1946; @zeng2023]")
    explain(
        "Define where `make_figs.py`'s figure functions draw.",
        "Its four figure functions end by calling `write_figure(fig, name)`, which writes "
        "`slides/figures/<name>.png`. The deck must not be touched from here.",
        "`write_figure` applies `make_figs.py`'s layout (template, font size, margins) and "
        "shows the figure in place instead of writing it.",
        "A figure labelled *the slide's own code* below is the deck's figure, redrawn by "
        "the deck's function.")
    nb.code('''
    def write_figure(fig, name, width=1000, height=560):
        """make_figs.py's write_figure(), shown in place instead of written to figures/."""
        fig.update_layout(template="plotly_white", width=width, height=height,
                          font=dict(size=16), margin=dict(l=70, r=30, t=70, b=70))
        display(Image(fig.to_image(format="png", width=width, height=height, scale=1)))
    ''')

    nb.md("""
    ### The data, and what the lab data can and cannot reproduce

    *Slide: "The case — two shuttles, sixteen phones, five beacons".*
    """)
    explain(
        "Load the slice the labs load, and measure it with the deck's archive-wide code.",
        "The deck's footers say \"Numbers: the archive — data/bus.csv\". Some of those "
        "numbers are properties of the one shuttle the slice holds and come out identical; "
        "others depend on the second shuttle, which the slice does not hold. The reader "
        "deserves to know which is which before any of them is used.",
        "Loads the slice with `load_slice()`, runs `make_figs.measure()` on it, and "
        "tabulates every stored archive measurement against the same measurement on the "
        "slice. The format-cost entries are left out here: they are wall-clock seconds, "
        "and Block 4 measures them in the open.",
        "Most rows agree exactly. The rows that differ — the row count, the vehicles, the "
        "completeness of `emergency_stop`, the negative speeds, the constant columns — "
        "are the ones printed with `beside()` wherever a slide quotes them.")
    nb.code('''
    bus = load_slice()
    print(f"the slice: {len(bus):,} rows x {bus.shape[1]} columns, vehicle(s) "
          f"{sorted(bus['vehicle_id'].unique())}")
    agrees("rows in the slice", len(bus), archive("slice_rows"), expected_from="measured.json")

    on_the_slice = measure(bus)
    timed = ("format_cost", "parquet_share_of_csv")
    comparison = pd.DataFrame(
        [(key, json.dumps(archive(key)), json.dumps(on_the_slice[key]["value"]),
          archive(key) == on_the_slice[key]["value"])
         for key in on_the_slice if key not in timed],
        columns=["measurement", "archive (measured.json)", "the slice (same code)", "same"])
    comparison
    ''')


# =============================================================================

def main() -> int:
    front_matter()
    setup()
    from sections import block1, block2, block3, block4, backup
    block1.build(nb, explain)
    block2.build(nb, explain)
    block3.build(nb, explain)
    block4.build(nb, explain)
    backup.build(nb, explain)
    nb.md("""
    ---
    ## Where this notebook and the slides differ, and why

    The slides are the master and are not changed. Where a number computed here does
    not match the number a slide prints, the notebook printed both at that point, with
    the reason. The table gathers every one of them, as they were printed in this run.
    """)
    explain(
        "Gather every number this notebook printed beside a slide's number.",
        "A reader should find every difference between the notebook and the slides in one "
        "place, with its reason, without searching the notebook.",
        "Tabulates what each `beside()` call recorded during this run: the quantity, the value "
        "computed here, the value on the slide or in the archive, and why they differ.",
        "Every row is explained where it first appears; none of them is a change to the slides.")
    nb.code('''
    with pd.option_context("display.max_colwidth", None):     # the reasons, in full
        display(pd.DataFrame(DIFFERENCES, columns=["quantity", "computed here",
                                                   "the slide or the archive", "why they differ"]))
    ''')
    nb.write(OUTPUT)
    print(f"wrote {OUTPUT.relative_to(ROOT)}")
    if "--no-run" not in sys.argv:
        execute(OUTPUT, EXERCISES)
        print(f"executed {OUTPUT.relative_to(ROOT)} in {EXERCISES.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
