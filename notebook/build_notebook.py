#!/usr/bin/env python3
"""Build Module 1's demonstration notebook; the instructor executes it against the archive.

    python "Module 1/notebook/build_notebook.py"            writes Module1_demonstration.ipynb
    python3 tools/check_notebook.py "Module 1" --run       executes it (needs data/bus.csv)

The notebook demonstrates the four presentation blocks on the real trial data,
with the definition card of every concept it demonstrates — formula and citation
in the markdown cell above the code — and plotly figures inline (fig.show(),
plus a portable network graphic under notebook/figures/). It is instructor-side:
it reads data/bus.csv, which is not in this repository and reaches students
through Moodle, so this builder only writes the cells; execution happens on the
instructor's machine with the working directory Module 1/exercises.

Structure is fixed by CLAUDE.md section 7 — Hook, Core Concept, Worked Example,
Practice, Appendix — and it closes on a References cell.

Only vehicle telemetry is opened here. The phone traces identify sixteen people
and no cell in this course prints one of their rows.
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

import nbformat
from nbformat.v4 import new_code_cell, new_markdown_cell, new_notebook

HERE = Path(__file__).resolve().parent
OUTPUT = HERE / "Module1_demonstration.ipynb"

MARKDOWN = "markdown"
CODE = "code"

CELLS = [
(MARKDOWN, """# Module 1 — Collecting and storing data

**Data Mining and Analysis (course code CE3) · Aalborg University, Copenhagen**

This notebook demonstrates the four blocks of the lecture on the real archive:
two automated shuttles on a fixed loop in Copenhagen, 22–23 January 2020.

Run it top to bottom. Every number the lecture claims is recomputed here in
front of you — that is the point of it. Every concept the labs grade appears
first as its definition card — the formula and the source the slide carries —
and then as code that computes exactly that. Seeds are fixed (the one shuffle
uses seed 0, as the slide says); the figures are plotly and are also saved as
portable network graphics under `notebook/figures/`.

**Data:** `data/bus.csv`, vehicle telemetry, which identifies nobody. The phone
traces from the same trial identify sixteen volunteers and are not opened
anywhere in this course except as aggregates."""),

(MARKDOWN, """## Hook

A shuttle reports its position, speed and payload about twice a second for two
days. You have 53,155 rows. How many observations do you actually have?

Not 53,155. Possibly closer to a hundred. By the end of this notebook you will
have measured the difference — and seen why it decides how you are allowed to
split the data, which decides whether your model works in service."""),

(CODE, '''import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

warnings.filterwarnings("ignore", category=FutureWarning)
pd.set_option("display.width", 110)

# The course palette: reference blue, comparison orange, neutral grey, red only for what fails.
BLUE, ORANGE, GREY, RED = "#2A78D6", "#E07B39", "#52514E", "#C0392B"
FIGURES = Path("../notebook/figures")   # the working directory is Module 1/exercises
FIGURES.mkdir(parents=True, exist_ok=True)

def show(fig, name, width=900, height=500):
    """Render inline and keep a portable network graphic beside the notebook."""
    fig.update_layout(template="plotly_white", width=width, height=height)
    fig.write_image(str(FIGURES / f"{name}.png"), scale=2)
    fig.show()

# The archive. Not in the repository students clone — see the note above.
BUS = Path("data/bus.csv")
bus = pd.read_csv(BUS, low_memory=False)
bus["utc"] = pd.to_datetime(bus["utc_time"])

print(f"{len(bus):,} rows, {bus.shape[1] - 1} columns (plus the parsed utc column)")
print("vehicles:", bus["vehicle_id"].unique().tolist())
print("days:    ", sorted({str(d) for d in bus["utc"].dt.date}))'''),

(MARKDOWN, """## Core Concept

### A pipeline is elements in series

Collect → store → clean → model → serve. Because they are in series, an error at
any stage reaches every stage after it, and nothing downstream can repair a fact
recorded wrongly upstream (Huyen, 2022). That is why this module is about
collection rather than algorithms.

### Independent draws, or a series?

Almost every standard statistical result assumes observations are *independent
and identically distributed*: each drawn afresh, unaffected by the last
(Casella & Berger, 2002).

> **Definition — lag-k sample autocorrelation.** The lag-k sample
> autocorrelation of x_1 … x_n is the summed product of each value's and its
> k-places-earlier value's deviation from the one series mean, divided by the
> summed squared deviation of all n values.
>
> `r_k = Σ_{t=k+1}^{n} (x_t − x̄)(x_{t−k} − x̄) / Σ_{t=1}^{n} (x_t − x̄)²`
>
> Box, Jenkins, Reinsel & Ljung (2015), §2.1; Hyndman & Athanasopoulos (2021), §2.8.
> Choices: one mean and one denominator over every present value; a pair
> enters the numerator only when both members are present where they stand;
> below thirty surviving pairs the answer is not-a-number. This is the
> estimator Lab 1 grades — not the pairwise Pearson correlation of the two
> shifted copies that `pandas.Series.autocorr` computes, which differs in the
> fourth decimal at lag 120 on this data.

If readings are independent draws, r_k is near zero for every k except 0.

> **Definition — the monotone-timestamp rule.** A lag is a shift by position,
> and a shift in time only when the positions are in time order. So the rows
> are sorted by their timestamp before any lag, difference, window or split by
> date, and the lag-one autocorrelation is reported before and after.
>
> `sort by utc_time so that t_{i} ≤ t_{i+1} for every i < n; only then is a lag of k rows a lag of k·Δt in time · report r_1 as shipped and r_1 in time order, on the same rows`
>
> Box, Jenkins, Reinsel & Ljung (2015), §2.1 — a time series is a sequence
> ordered in time, and the estimator above assumes it.

So before measuring anything, ask the timestamp one question."""),

(CODE, '''MINIMUM_PAIRS = 30   # the stated floor: below it two points always lie on a line

def sample_autocorrelation(values, lag):
    """r_k = Σ_{t=k+1}^{n} (x_t − x̄)(x_{t−k} − x̄) / Σ_{t=1}^{n} (x_t − x̄)²  — the definition on the slide.

    Implements the Box–Jenkins sample autocorrelation (Box, Jenkins, Reinsel &
    Ljung, 2015, §2.1) with the two stated choices: pairs with a missing member
    are skipped where they stand, and fewer than MINIMUM_PAIRS pairs give nan.
    """
    x = np.asarray(values, dtype=float)
    if lag == 0:
        return 1.0
    present = ~np.isnan(x)
    both = present[lag:] & present[:-lag]
    if both.sum() < MINIMUM_PAIRS:
        return float("nan")
    d = x - x[present].mean()
    d[~present] = 0.0
    return float((d[lag:] * d[:-lag])[both].sum() / (d[present] ** 2).sum())

# The first mess, and it is not a rehearsal: ask whether the timestamp only ever
# increases. The slice shipped in the exercise repository answers False, and the
# archive is worth asking the same question of before anything else is computed.
step = bus["utc"].diff().dt.total_seconds().iloc[1:]
backwards = step < 0

print("utc_time only ever increases:", bus["utc"].is_monotonic_increasing)
print(f"consecutive row pairs stepping backwards: {backwards.sum():,} of {len(step):,} "
      f"({backwards.mean() * 100:.1f} %)")
if backwards.any():
    print(f"largest single step backwards:              {step.min():.1f} s")'''),

(MARKDOWN, """If that printed `False`, every lag below is a shift by row rather than a shift
by time, and the two are different questions. So measure both, and let the pair
be the finding rather than picking one and hoping."""),

(CODE, '''# One shuttle, one day. State the choice beside the number: the vehicle that ran
# on both days, and the first of them. Both orders are kept, deliberately: the
# rows as they sit in the file, and the same rows sorted by utc_time.
VEHICLE = "VJRD1A10224000055"
chosen = bus[(bus["vehicle_id"] == VEHICLE)
             & (bus["utc"].dt.date == pd.Timestamp("2020-01-22").date())]
one = chosen.sort_values("utc", kind="mergesort")

as_shipped = chosen["speed"].astype(float).reset_index(drop=True)
speed = one["speed"].astype(float).reset_index(drop=True)
shuffled = speed.sample(frac=1, random_state=0).reset_index(drop=True)   # seed 0, the control

LAGS = [1, 2, 5, 10, 20, 40, 60, 120, 240, 600, 1200]
curves = {"as shipped": [sample_autocorrelation(as_shipped, k) for k in LAGS],
          "in time order": [sample_autocorrelation(speed, k) for k in LAGS],
          "shuffled": [sample_autocorrelation(shuffled, k) for k in LAGS]}

print(f"{VEHICLE}, 22 January, {len(speed):,} readings\\n")
print(f"{'lag':>6} {'seconds':>9} {'as shipped':>12} {'in time order':>15} {'shuffled':>10}")
for k, a, s, r in zip(LAGS, curves["as shipped"], curves["in time order"], curves["shuffled"]):
    print(f"{k:>6} {k * 0.5:>9.1f} {a:>12.4f} {s:>15.4f} {r:>10.4f}")

fig = go.Figure()
fig.add_hline(y=0, line_color=GREY, line_width=1)
fig.add_trace(go.Scatter(x=LAGS, y=curves["in time order"], mode="lines+markers",
                         name="rows sorted by utc_time", line_color=BLUE))
fig.add_trace(go.Scatter(x=LAGS, y=curves["as shipped"], mode="lines+markers",
                         name="rows as the file ships", line_color=ORANGE))
fig.add_trace(go.Scatter(x=LAGS, y=curves["shuffled"], mode="lines+markers",
                         name="the same values, shuffled (control)", line=dict(color=GREY, dash="dot")))
fig.update_layout(title="Lag-k sample autocorrelation of speed — one vehicle, one day, three orders",
                  xaxis=dict(title="lag k (rows; one row is 0.5 s only in time order)", type="log"),
                  yaxis_title="sample autocorrelation r_k (dimensionless)")
show(fig, "autocorrelation_by_order")'''),

(MARKDOWN, """Read the lag-1 row across. In time order, consecutive readings correlate at
about **0.997**. In the order the rows happen to sit in the file the same
readings give a visibly smaller number, and shuffling the values outright
collapses it to about **−0.001** — that last one is the control, and it shows
the measurement works.

Note which way the disorder pushes: *down*, towards what independent draws would
look like. A distortion that makes data look messier gets investigated. One that
makes data look more independent than it is gets believed, because it licenses
the convenient decision.

> **Effective sample size.** For a lag-one autocorrelation ρ, a series of n
> readings carries about `n_eff = n(1 − ρ)/(1 + ρ)` independent observations'
> worth of evidence about its mean (Bayley & Hammersley, 1946).

> **Definition — a split by time, never at random.** A split by time keeps
> every training observation earlier than every test observation, so the test
> set asks what the model will face in service — given the past, what comes
> next.
>
> `train = {x_t : t < t_c}, test = {x_t : t ≥ t_c} for one cut instant t_c — never a random permutation of the rows`
>
> Bergmeir & Benítez (2012); Roberts et al. (2017).

**So the practical consequence:** never split this data at random. A random split
puts a reading and its own neighbour on opposite sides of the boundary, so the
test set is a paraphrase of the training set. The model scores beautifully and
fails in service. Split by time — and sort by time before you measure anything
that depends on order."""),

(CODE, '''rho = curves["in time order"][0]
n = len(speed)
print(f"lag-1 autocorrelation in time order: {rho:.4f}")
print(f"effective sample size n(1 - rho)/(1 + rho): {n * (1 - rho) / (1 + rho):.0f} of {n:,} readings")'''),

(MARKDOWN, """## Worked Example

### The five quality dimensions, measured before anything is cleaned

Completeness, uniqueness, validity, consistency, timeliness. The list is the DAMA
UK Working Group's six primary dimensions minus accuracy (DAMA UK, 2013), which
this archive cannot measure without a second instrument; that quality is fitness
for use and multi-dimensional is Wang & Strong (1996); that each dimension is a
computable ratio is Pipino, Lee & Wang (2002); the survey is Batini et al.
(2009). Each is a number you can compute in one line. A quality claim you cannot
put a number on is an opinion.

> **Definition — completeness.** The share of the n rows that carry a value in
> a column — a ratio between nought and one, reported for every column.
>
> `completeness_j = |{i : x_{ij} is present}| / n, for every column j`
>
> DAMA UK (2013); Pipino, Lee & Wang (2002). Choice: present means not null;
> the ratio is not rounded before it is compared."""),

(CODE, '''# 1. Completeness -- the share of rows carrying a value, per column.
completeness = bus.drop(columns=["utc"]).notna().mean()
incomplete = completeness[completeness < 1].sort_values()
print("columns that are not complete:")
for column, share in incomplete.items():
    print(f"  {column:20} {share * 100:7.3f} %")
print(f"\\n{(completeness == 1).sum()} of {len(completeness)} columns are complete")

shown = pd.concat([incomplete, completeness[completeness == 1].head(3)])
fig = go.Figure(go.Bar(x=shown.values * 100, y=shown.index, orientation="h", marker_color=BLUE,
                       text=[f"{v * 100:.3f}" for v in shown.values], textposition="outside"))
fig.update_layout(title="Completeness, measured before anything is cleaned — the whole archive",
                  xaxis=dict(title="rows carrying a value (per cent)", range=[0, 112]),
                  yaxis_title="column")
show(fig, "completeness")'''),

(MARKDOWN, """`emergency_stop` is empty on nearly half the rows. That is **not** a defect: it
means no emergency stop happened, which is the normal state of a shuttle.

This is the misconception the module exists to correct. Impute it with a default
and you destroy the signal. Absence is sometimes the measurement.

> **Definition — uniqueness.** Uniqueness fails when one thing is recorded
> twice; measured as the number of rows identical in every column, and as the
> number of rows repeating the key that should identify one reading.
>
> `duplicate_rows = n − |distinct rows|; duplicate_vehicle_time = n − |distinct (vehicle_id, utc_time)|`
>
> DAMA UK (2013); Pipino, Lee & Wang (2002). Choice: the key is
> (vehicle_id, utc_time).

> **Definition — validity.** Conformance to a stated rule of type and range,
> measured as the count of rows failing each rule — here speed below zero, and
> mileage at the ceiling of an unsigned sixteen-bit counter, a sentinel that
> means no reading.
>
> `negative_speed_rows = |{i : speed_i < 0}|; mileage_at_ceiling = |{i : mileage_i = 2^{16} − 1}|`
>
> DAMA UK (2013); Pipino, Lee & Wang (2002). Choice: the sentinel 65535 is
> counted, never averaged in; the speed rule is "below zero" because no range
> has been declared."""),

(CODE, '''# 2. Uniqueness  3. Validity -- and the column that is not a distance.
MILEAGE_CEILING = 65535   # two to the sixteenth minus one
print("identical rows:              ", bus.duplicated().sum())
print("same vehicle, same instant:  ", bus.duplicated(subset=["vehicle_id", "utc_time"]).sum())
print()
print(f"speed range: {bus['speed'].min():.3f} to {bus['speed'].max():.3f} m/s")
print(f"rows with negative speed: {(bus['speed'] < 0).sum():,}"
      "   <- reversing, or invalid? You cannot say without the data dictionary.")
print(f"rows with mileage at the sentinel {MILEAGE_CEILING}: {(bus['mileage'] == MILEAGE_CEILING).sum():,}")
print()
print("mileage distinct values:", bus["mileage"].nunique(),
      " maximum:", bus["mileage"].max(), " = 2**16 - 1, a counter at its ceiling")'''),

(MARKDOWN, """> **Definition — consistency.** Whether fields that must agree do agree; here,
> the set of distinct differences between the column named `timestamp` and
> `utc_time`, in hours — one value if the two columns are one clock, and that
> value says what the name hides.
>
> `timestamp_minus_utc_hours = sorted set of (timestamp_i − utc_time_i), in hours, over every row i`
>
> DAMA UK (2013); Pipino, Lee & Wang (2002). Choice: rounded to two decimals
> before the set is formed."""),

(CODE, '''# 4. Consistency -- three time columns, and two of them are not what they say.
offsets_stamp = sorted({round(v, 2) for v in
                        (pd.to_datetime(bus["timestamp"]) - bus["utc"]).dt.total_seconds() / 3600})
offsets_local = sorted({round(v, 2) for v in
                        (pd.to_datetime(bus["local_time"]) - bus["utc"]).dt.total_seconds() / 3600})
print("timestamp  - utc_time, hours:", offsets_stamp)
print("local_time - utc_time, hours:", offsets_local)
print("\\nA column named `timestamp` holding local time, beside the column that")
print("holds the real one. Nothing in the name tells you. Ten minutes of")
print("measurement does.")
print("\\ncolumns holding one value in every row:",
      [c for c in bus.columns if c != "utc" and bus[c].nunique(dropna=True) == 1])'''),

(MARKDOWN, """> **Definition — timeliness.** Whether readings arrive when they should: the
> interval between consecutive readings once the rows are in time order, taken
> within a day, summarised as its median and as the count of intervals longer
> than one minute.
>
> `Δt_i = t_{(i+1)} − t_{(i)}, rows sorted by utc_time, within one day; report median Δt and |{i : Δt_i > 60 s}|`
>
> DAMA UK (2013); Pipino, Lee & Wang (2002). Choices: within a day, because
> across days the largest gap is the night; one minute as the threshold; the
> rows sorted first, by the monotone-timestamp rule."""),

(CODE, '''# 5. Timeliness -- and the choice that has to be printed beside the number.
ordered = bus[bus["vehicle_id"] == VEHICLE].sort_values("utc", kind="mergesort")
within_day = ordered.groupby(ordered["utc"].dt.date)["utc"].diff().dt.total_seconds().dropna()
across_days = ordered["utc"].diff().dt.total_seconds().dropna()

print(f"median interval:              {within_day.median():.3f} s")
print(f"gaps over 60 s, within a day: {(within_day > 60).sum()}")
print(f"longest gap, within a day:    {within_day.max():.1f} s "
      f"({within_day.max() / 60:.0f} minutes)")
print(f"longest gap, across days:     {across_days.max():.1f} s "
      f"({across_days.max() / 3600:.1f} hours)  <- that is the night, not a fault")

# Drawn in log10(seconds) on a linear axis, so every bar has the same width in
# log space and the one-minute line sits where it belongs.
positive = within_day[within_day > 0]
log_edges = np.linspace(np.log10(positive.min()), np.log10(positive.max()), 40)
counts, _ = np.histogram(np.log10(positive), bins=log_edges)
width = float(log_edges[1] - log_edges[0])
fig = go.Figure(go.Bar(x=log_edges[:-1] + width / 2, y=counts, width=width * 0.95, marker_color=BLUE))
fig.add_shape(type="line", x0=np.log10(60), x1=np.log10(60), y0=0, y1=1, yref="paper",
              line=dict(color=RED, dash="dash"))
ticks = [0.01, 0.1, 0.5, 1, 10, 60, 100, 1000]
fig.update_layout(title=f"Twice a second, except {int((within_day > 60).sum())} times — one vehicle, within a day",
                  xaxis=dict(title="gap between consecutive readings (seconds, logarithmic axis)",
                             tickvals=[np.log10(t) for t in ticks], ticktext=[f"{t:g}" for t in ticks]),
                  yaxis=dict(title="number of gaps (count)", type="log"), bargap=0.05)
show(fig, "sampling_gaps")'''),

(MARKDOWN, """That last pair is standing rule 2 in action. Measured across days, the largest
gap is 20 hours — which says nothing about the instrument and everything about
the clock. The number is only meaningful with the choice printed beside it.

The first draft of this course's own slides carried the 20-hour figure. The note
attached to the measurement is what caught it."""),

(MARKDOWN, """### What a format costs

> **Definition — what a format costs.** The cost of a storage format is
> measured, not asserted: for each format, the size in bytes of the file it
> writes from the same table, and the seconds it takes to read that file back,
> best of three so that the cost is measured and not the noise.
>
> `cost(f) = (bytes on disk, seconds to read back, best of three) for f ∈ {csv, csv.gz, parquet}, one frame written once each`
>
> Zeng, Hui, Shen, Pavlo, McKinney & Zhang (2023) measure the same trade-offs
> between columnar formats at scale.

Not asserted, measured — on this data, on this machine, today."""),

(CODE, '''import tempfile, time

def cost(frame):
    """Write and read the same table three ways. Best of three, so we measure
    the cost rather than the noise."""
    results = {}
    with tempfile.TemporaryDirectory() as folder:
        folder = Path(folder)
        writers = {
            "csv":     (lambda p: frame.to_csv(p, index=False), pd.read_csv),
            "csv.gz":  (lambda p: frame.to_csv(p, index=False, compression="gzip"), pd.read_csv),
            "parquet": (lambda p: frame.to_parquet(p, index=False), pd.read_parquet),
        }
        for name, (write, read) in writers.items():
            path = folder / f"bus.{name}"
            write(path)
            best = min(_read_once(read, path) for _ in range(3))
            results[name] = (path.stat().st_size / 1e6, best)
    return results

def _read_once(read, path):
    start = time.perf_counter(); read(path); return time.perf_counter() - start

measured = cost(bus.drop(columns=["utc"]))
print(f"{'format':10} {'megabytes':>10} {'read, s':>9}")
for name, (megabytes, seconds) in measured.items():
    print(f"{name:10} {megabytes:>10.2f} {seconds:>9.3f}")

names = list(measured)
fig = make_subplots(rows=1, cols=2, subplot_titles=("What it costs to keep", "What it costs to read"))
fig.add_trace(go.Bar(x=names, y=[measured[n][0] for n in names], marker_color=BLUE, showlegend=False,
                     text=[f"{measured[n][0]:.2f}" for n in names], textposition="outside"), row=1, col=1)
fig.add_trace(go.Bar(x=names, y=[measured[n][1] for n in names], marker_color=ORANGE, showlegend=False,
                     text=[f"{measured[n][1]:.3f}" for n in names], textposition="outside"), row=1, col=2)
fig.update_yaxes(title_text="megabytes on disk", row=1, col=1)
fig.update_yaxes(title_text="seconds to read back", row=1, col=2)
fig.update_xaxes(title_text="format", row=1, col=1)
fig.update_xaxes(title_text="format", row=1, col=2)
fig.update_layout(title="What a format costs — this archive, this machine, best of three")
show(fig, "format_cost", width=1000, height=460)'''),

(MARKDOWN, """The smallest file is usually **not** the fastest to read. Compressed
comma-separated values wins on bytes and loses on time, because every read
decompresses the whole file. Parquet stores column by column, so reading touches
less and parses less.

Report what you measured, especially when it contradicts what you expected."""),

(MARKDOWN, """## Practice

Three questions. Each is a few lines of code, and each has a definite answer.

1. **Which decays more slowly, `speed` or `payload`?** Compute the sample
   autocorrelation of both at lags 1, 20 and 120 (with `sample_autocorrelation`
   above, on the sorted day) and say what the difference tells you about how
   quickly each quantity can change.
2. **Where are the ten long gaps?** Find the intervals over 60 seconds for
   vehicle `...055` and print the times they begin. Do they cluster?
3. **How many rows would a naive cleaning destroy?** Count the rows a careless
   pipeline would drop by treating negative speed, the mileage ceiling and the
   empty `emergency_stop` as defects. Express it as a share of the file.

Answers are in the Appendix. Try them first."""),

(CODE, '''# Your workings here.
'''),

(MARKDOWN, """## Appendix

### Answers to the practice questions"""),

(CODE, '''# 1. payload decays more slowly than speed: a vehicle's load changes only when
#    someone boards, while its speed changes continuously.
for column in ("speed", "payload"):
    series = one[column].astype(float).reset_index(drop=True)
    print(f"{column:8}", " ".join(f"lag {k}: {sample_autocorrelation(series, k): .4f}" for k in (1, 20, 120)))

# 2. where the long gaps begin
long_gaps = within_day[within_day > 60]
print("\\nlong gaps begin at:")
for position, seconds in long_gaps.items():
    print(f"  {ordered.loc[position, 'utc']}  {seconds / 60:5.1f} minutes")

# 3. what a careless cleaning would destroy
careless = ((bus["speed"] < 0) | (bus["mileage"] == MILEAGE_CEILING) | bus["emergency_stop"].isna())
print(f"\\nrows a naive 'drop the odd ones' pass would remove: {careless.sum():,} "
      f"({careless.mean() * 100:.1f} % of the file)")
print("None of them is a defect. All of them are information.")'''),

(MARKDOWN, """### A note on the two estimators

`pandas.Series.autocorr(k)` computes the Pearson correlation of the series with
its k-shifted copy — each copy with its own mean and spread over the overlap.
The slide, the stub and the check use the Box–Jenkins estimator above: one mean
and one denominator over the whole series. On this data the two agree to four
decimals at lag 1 and differ by about 4.5e-4 at lag 120, which is why the check
names the estimator it grades rather than accepting either. Both are legitimate
statistics; the point of a definition card is that everybody computes the same
one."""),

(MARKDOWN, """### A note on what is not here

The phone traces from the same trial — `passengers.csv` — are the position
records of sixteen identifiable people. Under Article 4 of the General Data
Protection Regulation that is personal data, whatever the columns are called.

In this course they are opened only where a block genuinely needs them, only
inside a notebook that stays out of the repository students clone, and only ever
in aggregate: counts, distributions, per-window summaries. A map shows the route,
never a person. Module 2 is where that begins."""),

(MARKDOWN, """## References

- Batini, C., Cappiello, C., Francalanci, C. & Maurino, A. (2009). *Methodologies for Data Quality Assessment and Improvement.* ACM Computing Surveys 41(3), Art. 16. https://doi.org/10.1145/1541880.1541883
- Bayley, G. V. & Hammersley, J. M. (1946). *The "Effective" Number of Independent Observations in an Autocorrelated Time Series.* Supplement to the Journal of the Royal Statistical Society 8(2), 184–197. https://doi.org/10.2307/2983560
- Bergmeir, C. & Benítez, J. M. (2012). *On the use of cross-validation for time series predictor evaluation.* Information Sciences 191, 192–213. https://doi.org/10.1016/j.ins.2011.12.028
- Box, G. E. P., Jenkins, G. M., Reinsel, G. C. & Ljung, G. M. (2015). *Time Series Analysis: Forecasting and Control*, 5th ed., §2.1. Wiley. ISBN 978-1-118-67502-1
- Casella, G. & Berger, R. L. (2002). *Statistical Inference*, 2nd ed. Duxbury.
- DAMA UK Working Group (2013). *The Six Primary Dimensions for Data Quality Assessment.* DAMA UK, October 2013.
- European Union (2016). *Regulation 2016/679, General Data Protection Regulation*, Articles 4–6. https://eur-lex.europa.eu/eli/reg/2016/679/oj
- Huyen, C. (2022). *Designing Machine Learning Systems*, ch. 3. O'Reilly.
- Hyndman, R. J. & Athanasopoulos, G. (2021). *Forecasting: Principles and Practice*, 3rd ed., §2.8. OTexts. https://otexts.com/fpp3/
- Pipino, L. L., Lee, Y. W. & Wang, R. Y. (2002). *Data Quality Assessment.* Communications of the ACM 45(4), 211–218. https://doi.org/10.1145/505248.506010
- Roberts, D. R. et al. (2017). *Cross-validation strategies for data with temporal, spatial, hierarchical, or phylogenetic structure.* Ecography 40(8), 913–929. https://doi.org/10.1111/ecog.02881
- Wang, R. Y. & Strong, D. M. (1996). *Beyond Accuracy: What Data Quality Means to Data Consumers.* Journal of Management Information Systems 12(4), 5–33. https://doi.org/10.1080/07421222.1996.11518099
- Zeng, X., Hui, Y., Shen, J., Pavlo, A., McKinney, W. & Zhang, H. (2023). *An Empirical Evaluation of Columnar Storage Formats.* Proceedings of the VLDB Endowment 17(2), 148–161. https://doi.org/10.14778/3626292.3626298

*All output and every figure above was computed from `data/bus.csv` by this notebook. Author's own.*"""),
]


def main(bus_path="data/bus.csv"):
    notebook = new_notebook(cells=[
        new_markdown_cell(text) if kind == MARKDOWN else new_code_cell(text)
        for kind, text in CELLS
    ])
    notebook.metadata.update({
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python"},
    })
    # Every code cell must at least parse; execution needs the archive.
    for kind, text in CELLS:
        if kind == CODE:
            ast.parse(text)
    OUTPUT.write_text(nbformat.writes(notebook))
    print(f"wrote {OUTPUT.name} — {len(CELLS)} cells; execute on the instructor's machine "
          f"with tools/check_notebook.py 'Module 1' --run")
    return OUTPUT


if __name__ == "__main__":
    main(*(sys.argv[1:] or []))
