"""Lab 3, solved — with the reasoning, not only the code.

Run it: `python3 solutions/lab_03.py` from exercises/, or `python3
labs/03_profile_the_day.py` after `python3 apply.py`. It narrates the five
dimensions as it measures them, writes DATA_PROFILE.md and out/data_profile.json,
applies the declaration to the day it came from and to a broken copy of it,
returns a fitness verdict, and draws two figures from its own profile:
out/lab_03_completeness.html and out/lab_03_interval_histogram.html (with .png
twins).
"""
from __future__ import annotations

import json
import pathlib
import sys

import numpy as np
import pandas as pd
import plotly.graph_objects as go

LAB = 3
REPOSITORY = pathlib.Path(__file__).resolve().parent.parent
PROFILE_PATH = REPOSITORY / "DATA_PROFILE.md"
PROFILE_JSON = REPOSITORY / "out" / "data_profile.json"
MILEAGE_CEILING = 65535  # two to the sixteenth minus one: the sentinel, not a distance
PROFILE_SCHEMA = "aau-ce3/data-profile/1"

EVIDENCE_KEYS = ("worst_column_completeness", "largest_gap_seconds",
                 "backward_step_share", "effective_sample_size",
                 "implausible_row_share")
HIGHER_IS_BETTER = ("worst_column_completeness", "effective_sample_size")
VERDICT_CALLS = ("use", "use with a caveat", "do not use")

# The boundary, and the argument for each number. Nothing in the check compares
# these with numbers of its own; what it grades is that the verdicts below obey
# them and each other. Another teacher would set them differently and would owe
# the room the same five sentences.
FITNESS_LIMITS = {
    # A column absent on more than one row in twenty is not a column with holes,
    # it is a column you would be imputing rather than using.
    "worst_column_completeness": 0.95,
    # Ten minutes. Any average taken across a gap that long describes a window
    # that did not exist: the arithmetic is real and the window is not.
    "largest_gap_seconds": 600.0,
    # Two per cent of pairs out of order is a file with a few late arrivals.
    # More than that is a file whose order carries no information.
    "backward_step_share": 0.02,
    # A hundred independent readings. Below that a day is closer to one
    # observation than to a sample, and every interval computed from it is a
    # work of fiction (Bayley & Hammersley, 1946).
    "effective_sample_size": 100.0,
    # Two per cent outside the ranges the profile itself declares. Beyond that
    # the data is not the thing the profile describes.
    "implausible_row_share": 0.02,
}

# How far a declared range sits outside what was actually seen, as a share of
# the observed span, and how much extra absence a column is allowed. Both are
# choices, both are printed beside the numbers they produce, and both are the
# whole difference between a profile that cries wolf and one that never barks.
# The two quantities no caveat can repair, and the condition each of the other
# three imposes. This split, not the five numbers above, is the argument.
NO_CAVEAT_REPAIRS_IT = ("worst_column_completeness", "implausible_row_share")
CAVEATS = {
    "largest_gap_seconds": "the window around the longest gap is excluded and no average "
                           "is quoted across it",
    "backward_step_share": "the rows are sorted by time before anything that depends on "
                           "order is computed",
    "effective_sample_size": "every interval is widened to the effective number of "
                             "independent readings and no claim rests on the row count",
}

RANGE_MARGIN = 0.05
MISSING_MARGIN = 0.01
STEP_TOLERANCE = 0.25

# Units, where this archive actually justifies one. Most of these columns
# arrived with no unit written down anywhere, and inventing one in the profile
# would be the same failure the module opens with, committed in a file that
# Module 2 will believe. `payload` and `mileage` are left null on purpose.
UNITS = {
    "lat": "degrees north", "lon": "degrees east",
    "speed": "metres per second",
    "outside_temperature": "degrees Celsius", "inside_temperature": "degrees Celsius",
    "battery_level": "per cent", "theta": "radians",
    "x_web": "metres, Web Mercator", "y_web": "metres, Web Mercator",
}


def profile(frame: pd.DataFrame) -> dict:
    """Measure the five dimensions. Repair nothing.

    Implements the five cards of block 3 — completeness as a ratio per column,
    uniqueness and validity as counts, consistency as a set of offsets,
    timeliness as a median and a count — the DAMA UK (2013) list with the
    metrics written as ratios and counts after Pipino, Lee & Wang (2002).

    The discipline that matters here is the one thing the code cannot show you:
    every temptation to fix something is postponed. The negative speeds stay.
    The ceiling values stay. You are writing the document that tells the next
    person what they are dealing with, and a profile that has quietly cleaned
    its subject describes a dataset that does not exist.

    Two choices worth stating, because standing rule 2 says a number carries
    the choice that produced it:

      * gaps are taken within a day. Across days the largest gap is the night,
        which says nothing about the instrument. Group before differencing.
      * validity needs the data dictionary. `speed` below zero is only invalid
        if the field is a speed; if it is a signed velocity, the vehicle is
        reversing and the rows are fine. We count them and say so rather than
        pronouncing them wrong.
    """
    utc = pd.to_datetime(frame["utc_time"])
    stamp = pd.to_datetime(frame["timestamp"])

    # The monotone-timestamp rule from Lab 1: intervals mean nothing until the
    # rows are in time order, and the night is not a fault of the instrument.
    ordered = frame.assign(_utc=utc).sort_values("_utc")
    intervals = ordered.groupby(ordered["_utc"].dt.date)["_utc"].diff().dt.total_seconds().dropna()

    offsets = sorted({round(v, 2) for v in (stamp - utc).dt.total_seconds() / 3600})

    # Not rounded: battery_level is present on all but one row in fifty
    # thousand, and rounding it to four decimals would call it complete.
    return {
        "completeness": {c: float(frame[c].notna().mean()) for c in frame.columns},
        "uniqueness": {
            "duplicate_rows": int(frame.duplicated().sum()),
            "duplicate_vehicle_time": int(
                frame.duplicated(subset=["vehicle_id", "utc_time"]).sum()),
        },
        "validity": {
            "negative_speed_rows": int((frame["speed"] < 0).sum()),
            "mileage_at_ceiling": int((frame["mileage"] == MILEAGE_CEILING).sum()),
        },
        "consistency": {"timestamp_minus_utc_hours": offsets},
        "timeliness": {
            "median_interval_s": round(float(intervals.median()), 3),
            "gaps_over_60s": int((intervals > 60).sum()),
        },
    }


def write_profile(measurements: dict) -> str:
    """Write DATA_PROFILE.md — the document whose absence caused the lying columns.

    The five "- name: value" lines are the contract of the card "Definition —
    the data dictionary, and the profile you write": a program reads them, so
    the names are fixed and the values are measured, never copied.
    """
    timeliness = measurements["timeliness"]
    uniqueness = measurements["uniqueness"]
    validity = measurements["validity"]
    offsets = measurements["consistency"]["timestamp_minus_utc_hours"]
    incomplete = {c: v for c, v in measurements["completeness"].items() if v < 1}

    lines = [
        "# Data profile — bus_slice.csv.gz",
        "",
        "Shuttle VJRD1A10224000055, 22 and 23 January 2020. Measured before any",
        "cleaning. Nothing in this file has been repaired.",
        "",
        "## The five dimensions",
        "",
        f"- median_interval_s: {timeliness['median_interval_s']}",
        f"- gaps_over_60s: {timeliness['gaps_over_60s']}",
        f"- duplicate_rows: {uniqueness['duplicate_rows']}",
        f"- duplicate_vehicle_time: {uniqueness['duplicate_vehicle_time']}",
        f"- negative_speed_rows: {validity['negative_speed_rows']}",
        f"- mileage_at_ceiling: {validity['mileage_at_ceiling']}",
        "",
        "Gaps are counted within a day. Across days the largest gap is the night.",
        "",
        "## Completeness",
        "",
    ]
    if incomplete:
        lines += [f"- {column}: {share:.6f}" for column, share in sorted(incomplete.items())]
    else:
        lines.append("- every column carries a value in every row")
    lines += [
        "",
        "## What the names do not tell you",
        "",
        f"- `timestamp` differs from `utc_time` by {offsets} hour(s). It is local",
        "  time, not coordinated universal time, despite sitting beside the column",
        "  that holds the real one.",
        f"- `mileage` reaches {MILEAGE_CEILING}, an unsigned 16-bit counter at its",
        "  ceiling. It is not a distance.",
        "- `emergency_stop` is empty on most rows, and the emptiness means no stop",
        "  occurred. Do not impute it.",
        "",
    ]
    text = "\n".join(lines)
    PROFILE_PATH.write_text(text)
    return text


def declare_profile(frame: pd.DataFrame, measurements: dict) -> dict:
    """Turn the measurements into rules and write out/data_profile.json.

    Implements the card "Definition — the profile a program can read". This is
    the moment the module stops describing and starts committing: every number
    below is a statement that the next day's data can be tested against, and
    somebody will be woken up by it.

    The two margins are the whole design. Declared exactly at the observed
    minimum and maximum, the profile fires on the first ordinary day that is a
    tenth of a degree colder, everyone learns to ignore it, and it is worse than
    nothing. Declared wide enough to be safe, it admits a shuttle at 999 metres
    per second. Five per cent of the observed span, and one percentage point of
    extra absence, are defensible here because the archive is two days of one
    vehicle on a fixed loop; a fleet over a year would want wider, and would owe
    the reader the same sentence.

    Note what is deliberately not declared: a unit for `payload` or `mileage`.
    Nobody wrote one down, and a profile that invents one is the original sin of
    this module committed in a file that the next module will believe.
    """
    columns = {}
    for name in frame.columns:
        series = frame[name]
        numeric = pd.api.types.is_numeric_dtype(series)
        absent = 1.0 - float(measurements["completeness"][name])
        rule = {
            "type": "number" if numeric else "text",
            "unit": UNITS.get(name),
            "minimum": None,
            "maximum": None,
            "max_missing_share": round(min(1.0, absent + MISSING_MARGIN), 6),
        }
        if numeric:
            low, high = float(series.min()), float(series.max())
            span = high - low
            margin = RANGE_MARGIN * (span if span > 0 else max(abs(high), 1.0))
            rule["minimum"] = round(low - margin, 6)
            rule["maximum"] = round(high + margin, 6)
        columns[name] = rule

    declaration = {
        "schema": PROFILE_SCHEMA,
        "module": 1,
        "dataset": "exercises/data/bus_slice.csv.gz",
        "rows": int(len(frame)),
        "time_column": "utc_time",
        "expected_step_seconds": float(measurements["timeliness"]["median_interval_s"]),
        "step_tolerance_share": STEP_TOLERANCE,
        "columns": columns,
    }
    PROFILE_JSON.parent.mkdir(parents=True, exist_ok=True)
    PROFILE_JSON.write_text(json.dumps(declaration, indent=1, sort_keys=True) + "\n")
    return declaration


def check_against(frame: pd.DataFrame, profile: dict) -> list[str]:
    """Apply a declaration to a day. Empty list means the day satisfies it.

    Implements the second half of the card "Definition — the profile a program
    can read": presence, then type, then range, then missing share, then the
    sampling step, each complaint beginning with the field it concerns.

    The order is not cosmetic. A numeric column that has arrived as text will
    raise rather than report if you compare it with a number, so the range rule
    is skipped exactly where the type rule has already spoken. That is the
    general shape of every validation layer worth having: later rules assume
    what earlier rules established, and say nothing when the assumption failed.
    """
    breaches: list[str] = []
    columns = profile.get("columns", {})
    typed = {}

    for name, rule in columns.items():
        if name not in frame.columns:
            breaches.append(f"{name}: declared in the profile and not in this frame.")
            continue
        numeric = pd.api.types.is_numeric_dtype(frame[name])
        typed[name] = (rule.get("type") == "number") == numeric
        if not typed[name]:
            arrived = "number" if numeric else "text"
            breaches.append(f"{name}: declared as {rule.get('type')}, arrived as "
                            f"{arrived} (stored as {frame[name].dtype}).")

    for name, rule in columns.items():
        if not typed.get(name) or rule.get("type") != "number":
            continue
        values = frame[name]
        if rule.get("minimum") is not None:
            below = int((values < rule["minimum"]).sum())
            if below:
                breaches.append(f"{name}: {below} row(s) below the declared minimum "
                                f"{rule['minimum']}.")
        if rule.get("maximum") is not None:
            above = int((values > rule["maximum"]).sum())
            if above:
                breaches.append(f"{name}: {above} row(s) above the declared maximum "
                                f"{rule['maximum']}.")

    for name, rule in columns.items():
        if name not in frame.columns or rule.get("max_missing_share") is None:
            continue
        absent = 1.0 - float(frame[name].notna().mean())
        if absent > float(rule["max_missing_share"]):
            breaches.append(f"{name}: absent on {absent:.4f} of rows, above the declared "
                            f"{rule['max_missing_share']}.")

    time_column = profile.get("time_column")
    expected = profile.get("expected_step_seconds")
    if time_column in frame.columns and expected is not None:
        stamps = pd.to_datetime(frame[time_column], errors="coerce").sort_values()
        steps = stamps.groupby(stamps.dt.date).diff().dt.total_seconds().dropna()
        if len(steps):
            median = float(steps.median())
            tolerance = float(profile.get("step_tolerance_share", 0.0)) * float(expected)
            if abs(median - float(expected)) > tolerance:
                breaches.append(
                    f"{time_column}: median step {median:.3f} s within a day, declared "
                    f"{expected} s with {tolerance:.3f} s of tolerance.")
    return breaches


def fitness_verdict(evidence: dict) -> tuple[str, str]:
    """The call, and the argument for it. Implements "Definition — the fitness verdict".

    The rule below is mine, not the course's, and the check does not know it. It
    reads FITNESS_LIMITS, applies those five numbers to five days, and asks only
    that my verdicts obey my own boundary and do not contradict one another.
    Another teacher would draw the line elsewhere and would have to defend it
    the same way — out loud, with the numbers in the sentence.

    Mine has two tiers, and the tiers matter more than the numbers.

      Three of the five breaches can be written down and worked around:

        largest_gap_seconds     a gap is a window. Exclude it, say so, and
                                everything outside the window is still true.
        backward_step_share     rows out of order are repairable. Sort by time
                                before computing anything ordered — Lab 1 — and
                                it is the same file.
        effective_sample_size   this is a statement about precision, not about
                                correctness. Widen every interval to the
                                effective count and make no claim that rests on
                                the number of rows.

      Two cannot:

        worst_column_completeness   there is no subset of the day where the
                                    column is present, so there is no window to
                                    exclude and nothing left to caveat.
        implausible_row_share       when a large share of rows sits outside the
                                    ranges the profile itself declares, the data
                                    is not the thing the profile describes, and
                                    you cannot drop "the wrong rows" without
                                    knowing which ones they are.

    So: nothing breached, use it; a fatal quantity breached, refuse it; anything
    else, use it with the breach written down as a condition. The archive slice
    the students hold comes out "use with a caveat", and that caveat — sort it,
    exclude the long gap, do not treat forty-eight thousand rows as forty-eight
    thousand observations — is precisely what Module 2 needs to be told.
    """
    outside = [key for key in EVIDENCE_KEYS if _breaches(key, evidence[key])]
    fatal = [key for key in outside if key in NO_CAVEAT_REPAIRS_IT]

    if not outside:
        call = "use"
    elif fatal:
        call = "do not use"
    else:
        call = "use with a caveat"

    spoken = list(outside) if len(outside) >= 2 else list(outside) + _tightest(
        evidence, outside, 2 - len(outside))
    weighed = "; ".join(
        f"{key.replace('_', ' ')} {_g(evidence[key])} against my limit "
        f"{_g(FITNESS_LIMITS[key])}" for key in spoken)

    if call == "use":
        tail = "nothing is outside the boundary I set, so the day goes forward as it stands."
    elif call == "use with a caveat":
        # No count here, and no other number: every figure in the reason has to
        # be one of the numbers the verdict was handed, and "three conditions"
        # is not one of them. The check catches exactly that, which is the point.
        conditions = "; ".join(CAVEATS[key] for key in outside)
        tail = f"the day goes forward with this written down as a condition — {conditions}."
    else:
        tail = (f"no caveat repairs {' and '.join(fatal).replace('_', ' ')} — there is no "
                "subset of this day where that quantity is sound, so anything computed "
                "from it would describe the instrument rather than the world.")
    return call, f"{weighed}; {tail}"


def _breaches(key: str, value) -> bool:
    """Outside the boundary — below the limit where higher is better, above it where not."""
    limit = float(FITNESS_LIMITS[key])
    return float(value) < limit if key in HIGHER_IS_BETTER else float(value) > limit


def _tightest(evidence: dict, exclude, how_many: int) -> list[str]:
    """The quantities closest to their limit, so a one-breach reason still compares."""
    room = {}
    for key in EVIDENCE_KEYS:
        if key in exclude:
            continue
        limit, value = float(FITNESS_LIMITS[key]), float(evidence[key])
        scale = max(abs(limit), 1e-9)
        room[key] = (value - limit) / scale if key in HIGHER_IS_BETTER else (limit - value) / scale
    return sorted(room, key=room.get)[:max(0, how_many)]


def _g(value) -> str:
    """A number written the way the evidence holds it, so it matches to the digit."""
    return f"{float(value):g}"


def evidence_from(frame, measurements: dict, profile: dict,
                  absence_is_the_measurement: tuple = ("emergency_stop",)) -> dict:
    """The five quantities of EVIDENCE_KEYS, from the profile and the frame.

    Given to the student rather than asked of them: the verdict is the exercise.
    The two decisions inside it are stated because they change the answer.
    emergency_stop is excluded from the worst completeness because its emptiness
    is the measurement, and the implausible share is counted against the ranges
    this profile itself declared — which is why it is nearly nought here and
    becomes informative the moment yesterday's profile meets today's data.
    """
    completeness = {column: share for column, share in measurements["completeness"].items()
                    if column not in absence_is_the_measurement}
    worst = min(completeness.values()) if completeness else 1.0

    utc = pd.to_datetime(frame[profile["time_column"]])
    ordered = utc.sort_values()
    within_day = ordered.groupby(ordered.dt.date).diff().dt.total_seconds().dropna()
    largest_gap = float(within_day.max()) if len(within_day) else 0.0

    steps = utc.diff().dt.total_seconds().dropna()
    backward_share = float((steps < 0).mean()) if len(steps) else 0.0

    rho = _lag_one_autocorrelation(frame.assign(_u=utc).sort_values("_u")["speed"].to_numpy())
    effective = (float(len(frame) * (1 - rho) / (1 + rho))
                 if rho == rho and rho > -1 else float(len(frame)))

    outside = pd.Series(False, index=frame.index)
    for column, rule in profile.get("columns", {}).items():
        if column not in frame.columns or rule.get("type") != "number":
            continue
        values = pd.to_numeric(frame[column], errors="coerce")
        if rule.get("minimum") is not None:
            outside |= values < rule["minimum"]
        if rule.get("maximum") is not None:
            outside |= values > rule["maximum"]

    return {
        "worst_column_completeness": round(worst, 6),
        "largest_gap_seconds": round(largest_gap, 3),
        "backward_step_share": round(backward_share, 6),
        "effective_sample_size": round(effective, 1),
        "implausible_row_share": round(float(outside.mean()), 6),
    }


def _lag_one_autocorrelation(values) -> float:
    """Lab 1's estimator, repeated so that this file stands on its own.

    r_1 = Σ_{t=2}^{n} (x_t − x̄)(x_{t−1} − x̄) / Σ_{t=1}^{n} (x_t − x̄)²
    (Box, Jenkins, Reinsel & Ljung, 2015, §2.1).
    """
    series = np.asarray(values, dtype=float)
    present = ~np.isnan(series)
    if present.sum() < 30:
        return float("nan")
    deviation = series - series[present].mean()
    deviation[~present] = 0.0
    both = present[1:] & present[:-1]
    denominator = float((deviation[present] ** 2).sum())
    if not denominator:
        return float("nan")
    return float((deviation[1:] * deviation[:-1])[both].sum()) / denominator


if __name__ == "__main__":
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
    from _narrate import narrator, show_table, save_figure
    from lab_support import load_slice

    say = narrator(LAB)
    say.info("Lab 3 — five quality dimensions measured before anything is cleaned")
    bus = load_slice()
    say.info("loaded the archive slice, %s rows x %d columns, exactly as it ships",
             f"{len(bus):,}", bus.shape[1])
    shape_before = bus.shape

    measurements = profile(bus)
    say.info("profile() left the frame as it found it: %s -> %s", shape_before, bus.shape)

    completeness = pd.Series(measurements["completeness"]).sort_values()
    incomplete = completeness[completeness < 1]
    say.info("completeness — %d of %d columns carry a value in every row; the rest, as a "
             "share of rows (not rounded, because all-but-one-row is not complete): %s",
             int((completeness == 1).sum()), len(completeness),
             {c: round(v, 6) for c, v in incomplete.items()})
    say.info("emergency_stop is empty on most rows because no stop occurred: the emptiness is "
             "the measurement, not a defect")
    say.info("uniqueness — %d identical rows, %d repeated (vehicle_id, utc_time) keys",
             measurements["uniqueness"]["duplicate_rows"],
             measurements["uniqueness"]["duplicate_vehicle_time"])
    say.info("validity — %d rows with speed below zero (reversing, or invalid? the data "
             "dictionary decides, so they are counted, not dropped); %d rows with mileage at the "
             "sentinel %d = 2^16 − 1",
             measurements["validity"]["negative_speed_rows"],
             measurements["validity"]["mileage_at_ceiling"], MILEAGE_CEILING)
    say.info("consistency — distinct (timestamp − utc_time) offsets, hours: %s; the column "
             "named timestamp holds local time",
             measurements["consistency"]["timestamp_minus_utc_hours"])
    say.info("timeliness — median interval %.3f s, %d gaps over 60 s within a day",
             measurements["timeliness"]["median_interval_s"],
             measurements["timeliness"]["gaps_over_60s"])

    ledger = pd.DataFrame(
        [("completeness", "share of rows with a value, per column", "min over columns",
          float(completeness.min())),
         ("uniqueness", "duplicate_rows", "count", measurements["uniqueness"]["duplicate_rows"]),
         ("uniqueness", "duplicate_vehicle_time", "count",
          measurements["uniqueness"]["duplicate_vehicle_time"]),
         ("validity", "negative_speed_rows", "count", measurements["validity"]["negative_speed_rows"]),
         ("validity", "mileage_at_ceiling", "count", measurements["validity"]["mileage_at_ceiling"]),
         ("consistency", "timestamp_minus_utc_hours", "set, hours",
          str(measurements["consistency"]["timestamp_minus_utc_hours"])),
         ("timeliness", "median_interval_s", "seconds", measurements["timeliness"]["median_interval_s"]),
         ("timeliness", "gaps_over_60s", "count within a day", measurements["timeliness"]["gaps_over_60s"])],
        columns=["dimension", "measure", "unit", "value"])
    show_table(ledger, "the profile", logger=say)

    text = write_profile(measurements)
    say.info("wrote %s (%d lines); the check parses its five '- name: value' lines",
             PROFILE_PATH.name, len(text.splitlines()))

    # --- the same profile, for a program this time
    declaration = declare_profile(bus, measurements)
    say.info("declared %d columns into %s: type, unit, minimum, maximum and the allowed "
             "missing share, with the ranges widened by %.0f per cent of the observed span "
             "and the absence allowance by %.0f percentage point(s) — both are choices, and "
             "both decide whether this file ever fires",
             len(declaration["columns"]), PROFILE_JSON.name, RANGE_MARGIN * 100,
             MISSING_MARGIN * 100)
    say.info("speed is declared %s to %s %s; payload and mileage are declared with no unit "
             "at all, because nobody ever wrote one down and inventing one here is the "
             "failure this module opens with",
             declaration["columns"]["speed"]["minimum"],
             declaration["columns"]["speed"]["maximum"],
             declaration["columns"]["speed"]["unit"])
    say.info("expected step %s s with %.0f per cent of tolerance; this is the file Module 2 "
             "loads before it touches a row, and HANDOFF.md is its schema",
             declaration["expected_step_seconds"], STEP_TOLERANCE * 100)

    say.info("the day it was declared from breaks nothing: check_against() returned %s",
             check_against(bus, declaration))

    # A broken copy, so that "returns nothing" is shown to be a result and not a
    # function that cannot speak. Same seed as the check's corruption.
    broken = bus.sample(frac=1.0, random_state=20200122).head(4000).copy()
    broken.loc[broken.index[:200], "speed"] = 999.0
    broken.loc[broken.index[:2400], "battery_level"] = np.nan
    broken = broken.drop(columns=["ramp_state"])
    for complaint in check_against(broken, declaration):
        say.info("broken copy — %s", complaint)

    # --- the evidence, and the verdict
    evidence = evidence_from(bus, measurements, declaration)
    say.info("evidence for the verdict, every number measured above: %s", evidence)
    say.info("emergency_stop is left out of the worst column completeness on purpose: it is "
             "empty because no stop occurred, and folding that in would call the best "
             "behaved day in the archive unusable")
    call, reason = fitness_verdict(evidence)
    say.info("verdict on this day: %s", call.upper())
    say.info("because: %s", reason)
    say.info("the boundary that produced it is mine and is written in FITNESS_LIMITS: %s. "
             "The check holds no thresholds; it grades that these verdicts obey these "
             "limits and do not contradict one another", FITNESS_LIMITS)

    # Figure 3: how far each quantity sits from the boundary, in units of the
    # boundary, so five quantities with five different units share one axis.
    headroom, colours, labels = [], [], []
    for key in EVIDENCE_KEYS:
        limit, value = float(FITNESS_LIMITS[key]), float(evidence[key])
        margin = ((value - limit) if key in HIGHER_IS_BETTER else (limit - value)) / abs(limit)
        headroom.append(margin)
        colours.append("#C0392B" if margin < 0 else "#2A78D6")
        labels.append(key.replace("_", " "))
    fig3 = go.Figure(go.Bar(x=headroom, y=labels, orientation="h", marker_color=colours,
                            text=[f"{v:+.2f}" for v in headroom], textposition="outside"))
    fig3.add_shape(type="line", x0=0, x1=0, y0=-0.5, y1=len(labels) - 0.5,
                   line=dict(color="#52514E", dash="dash"))
    fig3.update_layout(
        title=f"How far this day sits from the boundary I declared — verdict: {call}",
        xaxis_title="distance from my limit, as a multiple of the limit "
                    "(negative is outside it)",
        yaxis_title="evidence quantity")
    save_figure(fig3, "fitness_headroom", LAB, logger=say)

    # Figure 1: completeness bars from this very profile — every incomplete
    # column and three complete ones, so the contrast is visible.
    shown = pd.concat([incomplete, completeness[completeness == 1].head(3)])
    fig = go.Figure(go.Bar(
        x=shown.values * 100, y=shown.index, orientation="h", marker_color="#2A78D6",
        # Three decimals, because battery_level is 99.998 and two would print it as 100.
        text=[f"{v * 100:.3f}" for v in shown.values], textposition="outside"))
    fig.update_layout(title="Completeness of the slice, per column — measured before anything is cleaned",
                      xaxis=dict(title="rows carrying a value (per cent)", range=[0, 112]),
                      yaxis_title="column")
    save_figure(fig, "completeness", LAB, logger=say)

    # Figure 2: the interval distribution behind the timeliness numbers, drawn
    # in log10(seconds) on a linear axis so that every bar has the same width
    # in log space and the one-minute line sits where it belongs.
    utc = pd.to_datetime(bus["utc_time"])
    ordered = bus.assign(_utc=utc).sort_values("_utc")
    intervals = ordered.groupby(ordered["_utc"].dt.date)["_utc"].diff().dt.total_seconds().dropna()
    positive = intervals[intervals > 0]
    log_edges = np.linspace(np.log10(positive.min()), np.log10(positive.max()), 40)
    counts, _ = np.histogram(np.log10(positive), bins=log_edges)
    width = float(log_edges[1] - log_edges[0])
    fig2 = go.Figure(go.Bar(x=log_edges[:-1] + width / 2, y=counts, width=width * 0.95,
                            marker_color="#2A78D6", name="intervals within a day"))
    fig2.add_shape(type="line", x0=np.log10(60), x1=np.log10(60), y0=0, y1=1, yref="paper",
                   line=dict(color="#C0392B", dash="dash"))
    fig2.add_annotation(x=np.log10(60), y=1, yref="paper", text="one minute", showarrow=False,
                        xanchor="right", yanchor="top", xshift=-6, font=dict(color="#C0392B"))
    ticks = [0.01, 0.1, 0.5, 1, 10, 60, 100, 1000]
    fig2.update_layout(title=f"Interval between consecutive readings, within a day — twice a second, "
                             f"except {measurements['timeliness']['gaps_over_60s']} times",
                       xaxis=dict(title="gap between consecutive readings (seconds, logarithmic axis)",
                                  tickvals=[np.log10(t) for t in ticks],
                                  ticktext=[f"{t:g}" for t in ticks]),
                       yaxis=dict(title="number of gaps (count)", type="log"), bargap=0.05)
    save_figure(fig2, "interval_histogram", LAB, logger=say)

    say.info("what the check grades: the five sections present; median interval to 1e-3 s, "
             "counts exact, the offset set equal to [1.0], every column in completeness; the "
             "frame unchanged; DATA_PROFILE.md with the five parsable lines matching the "
             "check's own measurement; out/data_profile.json in the schema of HANDOFF.md, "
             "silent on this day and loud on a seeded corruption of it; and five verdicts "
             "consistent with FITNESS_LIMITS and with each other")
