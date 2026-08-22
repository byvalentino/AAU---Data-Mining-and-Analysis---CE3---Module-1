"""Lab 3 — Profile the day.

Why this lab exists: a dataset that "looks clean" has never been measured, and
the columns of this archive that lie about themselves — a timestamp that is
local time, a mileage that is a sentinel — are invisible until somebody
computes five numbers before touching anything. You prove you can measure the
five quality dimensions as ratios and counts, write them where a reader and a
program will both find them, turn them into rules the next day's data can be
tested against, and then say out loud whether the day is fit to use.
Where it sits: Block 3 — "The five dimensions of data quality", and the
definition slides "Definition — completeness", "— uniqueness", "— validity",
"— consistency", "— timeliness", "Definition — the data dictionary, and the
profile you write", "Definition — the profile a program can read" and
"Definition — the fitness verdict".
What the check grades: profile() returns the five sections with the exact
counts and ratios the check measures itself on the same slice (median interval
to a thousandth of a second, counts exactly, the offset set equal to [1.0]),
without changing the frame; write_profile() writes DATA_PROFILE.md with the
five "- name: value" lines the check parses; declare_profile() writes
out/data_profile.json in the schema HANDOFF.md fixes; check_against() is silent
on the day the profile was declared from and complains, naming the field, on a
seeded corruption of it; fitness_verdict() returns one of three calls with a
reason built out of the evidence, and the same boundary applied to five days.
Needs: json, pandas; lab_support.load_slice; for the demonstration _narrate,
    numpy and plotly.

Twenty-five minutes.

You describe. You do not repair. The single most common mistake in this lab is
dropping the odd values and then reporting perfect quality — which is how a
dataset comes to look clean and behave badly.

What you write, in order:

    profile(frame)                  measure the five dimensions
    write_profile(measurements)     DATA_PROFILE.md, for a person
    declare_profile(frame, ...)     out/data_profile.json, for a program
    check_against(frame, profile)   apply the declaration to a day
    fitness_verdict(evidence)       the call, and the reason for it

The first two describe what you have. The third turns the description into a
statement of what the data must satisfy — which is a commitment, not a
measurement, and it is the file Module 2 will read. The fourth applies that
statement. The fifth is the only one where the answer is yours.

The five dimensions, and exactly what each means here:

  completeness   share of rows carrying a value, per column, as a fraction
                 between 0 and 1. Every column, not only the bad ones.

  uniqueness     duplicate_rows        — rows identical in every column
                 duplicate_vehicle_time — the same vehicle_id at the same
                                          utc_time more than once

  validity       negative_speed_rows   — rows where speed is below zero
                 mileage_at_ceiling    — rows where mileage equals 65535, the
                                         maximum of an unsigned 16-bit field. It
                                         is a sentinel meaning *no reading*, not
                                         a distance. Count them; do not average
                                         them in. Note how many there are, and
                                         what that does to the column's mean.

  consistency    timestamp_minus_utc_hours — the distinct offsets, in hours,
                 between the column named `timestamp` and `utc_time`. Note what
                 you find and what it implies about the column's name.

  timeliness     median_interval_s     — median seconds between consecutive
                                         readings, sorted by utc_time
                 gaps_over_60s         — how many consecutive intervals exceed
                                         60 seconds, counted within a day

Why within a day: measured across days the largest gap is simply the night,
which says nothing about the instrument. Group by the date before differencing.
"""
from __future__ import annotations

import json
import pathlib
import sys

import numpy as np
import pandas as pd
import plotly.graph_objects as go

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from lab_support import NotSolved, load_slice  # noqa: E402
from _narrate import narrator, show_table, save_figure  # noqa: E402,F401

LAB = 3
REPOSITORY = pathlib.Path(__file__).resolve().parent.parent
PROFILE_PATH = REPOSITORY / "DATA_PROFILE.md"
PROFILE_JSON = REPOSITORY / "out" / "data_profile.json"
MILEAGE_CEILING = 65535  # two to the sixteenth minus one: the sentinel, not a distance

# The schema string that goes into out/data_profile.json. Module 2 reads it
# before it reads anything else, so that a profile written for a different
# course, or for a later version of this one, is refused rather than misread.
PROFILE_SCHEMA = "aau-ce3/data-profile/1"

# The five quantities a fitness verdict is allowed to weigh, and the direction
# in which each one gets worse. Nothing else reaches fitness_verdict().
#
#   worst_column_completeness   0 to 1, higher is better. The smallest
#                               completeness over the columns where an absent
#                               value is a defect. Columns where absence is
#                               itself the measurement are excluded by name --
#                               emergency_stop is empty because no stop
#                               occurred, and counting that as incompleteness is
#                               the misconception this module opens with.
#   largest_gap_seconds         seconds, higher is worse. The longest interval
#                               between consecutive readings within a day.
#   backward_step_share         0 to 1, higher is worse. The share of
#                               consecutive row pairs that step backwards in
#                               time in the file as it arrived.
#   effective_sample_size       a count of rows, higher is better. The number of
#                               independent readings the day is worth,
#                               n(1 - rho)/(1 + rho) with rho the lag-1
#                               autocorrelation (Bayley & Hammersley, 1946).
#   implausible_row_share       0 to 1, higher is worse. The share of rows
#                               holding a value outside a range the profile
#                               itself declares.
EVIDENCE_KEYS = ("worst_column_completeness", "largest_gap_seconds",
                 "backward_step_share", "effective_sample_size",
                 "implausible_row_share")

# Your boundary. Five numbers, one for each evidence key: the point at which
# that quantity stops being a wobble and starts being a reason. Nothing here is
# measured, so no number here is right or wrong on its own -- the check never
# compares your limits against limits of its own, because it has none. What it
# does compare is your verdicts against these limits: a day where nothing is
# outside them has to be one you use, a day where anything is outside them is not
# a day you use as it stands, a day where everything is outside them has to be
# one you refuse, and a day at least as good as another on all five may not get
# the harsher call. Set them before you write fitness_verdict(), and say them out
# loud in the reasons you return.
FITNESS_LIMITS = {
    "worst_column_completeness": None,   # below this share of rows, a column is a gap
    "largest_gap_seconds": None,         # a gap longer than this is not a sampling wobble
    "backward_step_share": None,         # above this share of pairs out of order, the file is unordered
    "effective_sample_size": None,       # below this many independent readings, the day is one observation
    "implausible_row_share": None,       # above this share outside the declared range, the day is not what it says
}

# The three calls, and nothing else. They are ordered: each commits you to more
# than the one before it.
VERDICT_CALLS = ("use", "use with a caveat", "do not use")


def profile(frame) -> dict:
    """Measure the five quality dimensions. Change nothing.

    Returns:
        {
          "completeness": {column: fraction, ...},
          "uniqueness":   {"duplicate_rows": int, "duplicate_vehicle_time": int},
          "validity":     {"negative_speed_rows": int, "mileage_at_ceiling": int},
          "consistency":  {"timestamp_minus_utc_hours": [float, ...]},
          "timeliness":   {"median_interval_s": float, "gaps_over_60s": int},
        }

    Definition graded by the check (DAMA UK, 2013; Pipino, Lee & Wang, 2002),
    one line per card:
        completeness_j = |{i : x_{ij} is present}| / n, for every column j
        duplicate_rows = n − |distinct rows|; duplicate_vehicle_time = n − |distinct (vehicle_id, utc_time)|
        negative_speed_rows = |{i : speed_i < 0}|; mileage_at_ceiling = |{i : mileage_i = 2^{16} − 1}|
        timestamp_minus_utc_hours = sorted set of (timestamp_i − utc_time_i), in hours, over every row i
        Δt_i = t_{(i+1)} − t_{(i)}, rows sorted by utc_time, within one day; report median Δt and |{i : Δt_i > 60 s}|
    Choices: present means not null; the uniqueness key is (vehicle_id,
    utc_time); the sentinel is MILEAGE_CEILING = 65535, counted, never averaged
    in; offsets are rounded to two decimals before the set is formed; intervals
    are taken within a day and the threshold is 60 s. Slides: "Definition —
    completeness", "— uniqueness", "— validity", "— consistency", "— timeliness".

    Needs: pandas
    """
    # TODO: measure, do not clean.
    raise NotSolved("profile(frame) still raises instead of returning the five dimensions")


def write_profile(measurements: dict) -> str:
    """Write DATA_PROFILE.md and return what was written.

    The check reads this file, so the format matters. One fact per line, in the
    form `- name: value`, with these five names present at minimum:

        - median_interval_s: <seconds>
        - gaps_over_60s: <count>
        - duplicate_rows: <count>
        - negative_speed_rows: <count>
        - mileage_at_ceiling: <count>

    Definition graded by the check:
        for every field: unit, source, valid range, owner · DATA_PROFILE.md: one
        line per measurement, "- name: value", five names at least
        (Riley, 2017; Gebru et al., 2021). Choice: the five names above are the
        ones the check parses; the values are yours to measure. Slide:
        "Definition — the data dictionary, and the profile you write".

    The values are yours to measure. None is written here, because a number you
    copied is not a number you measured, and the point of the lab is the second
    one.

    Put whatever else you find useful around them — a heading, the completeness
    table, a sentence on what the `timestamp` column actually holds. This is the
    document whose absence caused the three lying columns in the lecture.

    Needs: str.join, pathlib.Path.write_text
    """
    # TODO: format the measurements and write the file.
    raise NotSolved("write_profile(measurements) still raises instead of writing the file")


def declare_profile(frame, measurements: dict) -> dict:
    """Turn the measurements into rules, write out/data_profile.json, return it.

    DATA_PROFILE.md is for a person. This is the same profile for a program: the
    machine-readable statement of what every column of this dataset must
    satisfy, which Module 2 loads before it touches a row. HANDOFF.md holds the
    schema, the exact key names and an example; read it, because it is a
    contract and the next module is written against it.

    The shape, in one glance:

        {"schema": PROFILE_SCHEMA, "module": 1, "dataset": <name>,
         "rows": <int>, "time_column": "utc_time",
         "expected_step_seconds": <number>, "step_tolerance_share": <number>,
         "columns": {"<name>": {"type": "number" | "text",
                                "unit": <string or null>,
                                "minimum": <number or null>,
                                "maximum": <number or null>,
                                "max_missing_share": <number between 0 and 1>},
                     ...}}

    Every column of the frame gets an entry. A declaration is a commitment, so
    both ends of it are real work:

      too tight   and tomorrow's ordinary day is reported as broken, you stop
                  believing your own alarm, and the profile becomes decoration.
      too loose   and nothing can ever violate it. A range that admits a shuttle
                  travelling at 999 metres per second is not a range, and the
                  check will land exactly that on you.

    Definition graded by the check:
        declaration = {schema, rows, time_column, expected_step_seconds,
        step_tolerance_share, columns}, written as out/data_profile.json, one
        entry per column of the frame, each carrying type, unit, minimum,
        maximum, max_missing_share
        (Gebru et al., 2021; Riley, 2017). Choices: the ranges and the allowed
        missing share are yours, derived from what you measured and widened by
        as much as you are willing to defend; "number" means a numeric column
        and "text" anything else; expected_step_seconds is the median interval
        within a day and step_tolerance_share the fraction of it you allow.
        Slide: "Definition — the profile a program can read".

    Needs: json.dumps, pathlib.Path.write_text, pathlib.Path.mkdir
    """
    # TODO: build the declaration, write PROFILE_JSON, and return the dictionary.
    raise NotSolved("declare_profile(frame, measurements) still raises instead of "
                    "writing out/data_profile.json")


def check_against(frame, profile: dict) -> list[str]:
    """Test one day's data against a declaration. Return one line per breach.

    An empty list means the frame satisfies everything the profile declares.
    Otherwise, one short line of English per breach, each **beginning with the
    name it is about** — the column, or the profile's time column for the step
    rule — because whoever reads this at seven in the morning needs the field
    name before the sentence.

    The rules, in this order, so that one failure does not manufacture another:

        1. presence      a declared column that is not in the frame
        2. type          "number" wants a numeric column, "text" wants any other
        3. range         values below minimum or above maximum. Skipped when the
                         type rule has already failed for that column, because
                         comparing text with a number raises rather than
                         reports, and skipped when either bound is null
        4. missing       the share of absent values above max_missing_share
        5. step          the median interval within a day, in the profile's time
                         column, further from expected_step_seconds than
                         step_tolerance_share of it

    Definition graded by the check:
        check_against(frame, profile) = [] when every declared rule holds, else one line per breach, in the order presence → type → range → missing share → step, each line beginning with the field it concerns
        (Gebru et al., 2021; Riley, 2017). Choices: the median step is taken
        within a day, as on the timeliness card; the range rule is skipped for a
        column whose type rule has already failed; a column in the frame that
        the profile does not declare is not a breach, because a profile
        describes what it declares. Slide: "Definition — the profile a program
        can read".

    Needs: pandas, and the profile dictionary you declared
    """
    # TODO: apply the declaration to the frame and report what it does not satisfy.
    raise NotSolved("check_against(frame, profile) still raises instead of returning breaches")


def fitness_verdict(evidence: dict) -> tuple[str, str]:
    """Say whether this day is fit to use, and why. Return (call, reason).

    `evidence` holds the five quantities of EVIDENCE_KEYS, measured by you, on
    your own data — evidence_from() below assembles it out of profile() and the
    declaration. `call` is one of VERDICT_CALLS:

        "use"                the day goes into the next stage as it stands.
                             Nothing about it changes what a reader of your
                             result would conclude.
        "use with a caveat"  the day goes on, but with a written condition
                             attached — a window excluded, a column not used, an
                             interval widened, a claim not made. The caveat is
                             the part that survives into Module 2, so it has to
                             be specific enough to act on.
        "do not use"         no caveat rescues it. Whatever you computed would be
                             a statement about the instrument rather than about
                             the world.

    `reason` is the argument, in one or two sentences, and the check grades it
    as hard as it grades the call:

      * every number in it must be one of the numbers you were handed, to the
        digit. A figure remembered from a slide is exactly the habit this course
        exists to break;
      * it must name at least two of the five quantities, in the words of
        EVIDENCE_KEYS — "the worst column completeness", "the largest gap in
        seconds". A verdict rests on a comparison, and a comparison has two
        sides;
      * it must say where your boundary lies. Your limits are in FITNESS_LIMITS
        and the check reads them too, so quoting one of those is quoting a
        number you declared rather than one you invented.

    No threshold is written down here for you to copy. Set FITNESS_LIMITS
    yourself, then apply that same boundary to every day you are given. What the
    check grades is not whether your boundary equals one of ours — there is no
    number of ours for it to equal — but whether the verdicts you return are
    consistent with the boundary you declared and with one another. A quantity
    outside your own limit is, in your own words, a reason: the day may still go
    forward, but not as it stands and not without the crossing written down. And
    a day at least as good as another on all five quantities may not receive the
    harsher call.

    Definition graded by the check:
        verdict(evidence) = (call, reason), call ∈ {use, use with a caveat, do not use}; the reason names ≥ 2 of the five evidence quantities and every number in it is one of them or one of FITNESS_LIMITS; no breach of FITNESS_LIMITS → use; any breach → not use; all five breached → do not use; evidence at least as good on all five → never the harsher call
        (Wang & Strong, 1996; Batini et al., 2009). Choices: the five quantities
        are EVIDENCE_KEYS and no others; the boundary is FITNESS_LIMITS and it
        is yours; a breach is a value below the limit where higher is better and
        above the limit where higher is worse. Slide: "Definition — the fitness
        verdict".

    Needs: the evidence dictionary, FITNESS_LIMITS, and a sentence you would be
    willing to defend to somebody who was not in the room
    """
    # TODO: weigh the evidence against your own limits, and say what you decided.
    raise NotSolved("fitness_verdict(evidence) still raises instead of returning "
                    "(call, reason)")


# --------------------------------------------------------------------------
# Given to you: the evidence, assembled out of your own measurements
# --------------------------------------------------------------------------
def evidence_from(frame, measurements: dict, profile: dict,
                  absence_is_the_measurement: tuple = ("emergency_stop",)) -> dict:
    """The five quantities of EVIDENCE_KEYS, from your profile and your data.

    Written for you, because the verdict is the exercise and the plumbing is
    not. Read it anyway: each of the five is a measurement you have already made
    or could make in one line, and the two decisions inside it are exactly the
    kind that belong in a profile rather than in a comment.

    The first is `absence_is_the_measurement`. emergency_stop is empty on nearly
    half the rows because no emergency stop occurred; folding that into the
    worst column completeness would call the archive's best-behaved day
    unusable. The choice is stated here, printed beside the number by the
    demonstration, and open to argument — which is the point.

    The second is that the implausible share is counted against the ranges *you*
    declared. On the day you declared them from it is nearly nought by
    construction. It becomes informative the moment yesterday's profile meets
    today's data, which is what Module 2 does with the file you are writing.
    """
    completeness = {column: share for column, share in measurements["completeness"].items()
                    if column not in absence_is_the_measurement}
    worst = min(completeness.values()) if completeness else 1.0

    utc = pd.to_datetime(frame[profile["time_column"]])
    ordered = utc.sort_values()
    within_day = ordered.groupby(ordered.dt.date).diff().dt.total_seconds().dropna()
    largest_gap = float(within_day.max()) if len(within_day) else 0.0

    # The file as it arrived, not sorted: how much of it steps backwards in time.
    steps = utc.diff().dt.total_seconds().dropna()
    backward_share = float((steps < 0).mean()) if len(steps) else 0.0

    # Bayley & Hammersley (1946): a series of nearly identical readings is worth
    # far fewer independent observations than it has rows.
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
    """Lab 1's estimator, repeated here so that this file stands on its own.

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
    say = narrator(LAB)
    bus = load_slice()
    say.info("archive slice, %s rows x %d columns, as shipped", f"{len(bus):,}", bus.shape[1])
    measurements = profile(bus)
    say.info("timeliness: %s", measurements["timeliness"])
    say.info("uniqueness: %s", measurements["uniqueness"])
    say.info("validity: %s", measurements["validity"])
    say.info("consistency: %s", measurements["consistency"])
    print(write_profile(measurements))

    declaration = declare_profile(bus, measurements)
    say.info("declared %d columns into %s", len(declaration["columns"]), PROFILE_JSON.name)
    say.info("the day it was declared from breaks nothing: %s", check_against(bus, declaration))

    evidence = evidence_from(bus, measurements, declaration)
    say.info("evidence, with emergency_stop left out of the completeness because its "
             "emptiness is the measurement: %s", evidence)
    call, reason = fitness_verdict(evidence)
    say.info("verdict: %s — %s", call, reason)
