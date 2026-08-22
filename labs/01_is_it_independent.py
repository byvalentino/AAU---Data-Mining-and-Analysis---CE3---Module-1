"""Lab 1 — Is it independent?

Why this lab exists: sensor readings arrive twice a second and look like tens of
thousands of observations, but consecutive readings are near-copies of each
other, and the file that holds them is not even in time order. You prove both
by measuring the lag-k autocorrelation yourself, in the shipped order and in
time order, and you draw the one consequence that matters for every model
after this: split by time, never at random.
Where it sits: Block 1 — "What disorder costs, and the rule that prevents it",
and the definition slides "Definition — lag-k sample autocorrelation",
"Definition — the monotone-timestamp rule" and "Definition — a split by time,
never at random".
What the check grades: autocorrelation() equals the Box–Jenkins estimator on
the slide to four decimal places at several lags, on the shipped rows, with a
fifth of the values removed, and on a series too sparse to answer;
in_time_order() returns the same rows monotone in utc_time with the index reset
and the caller's frame untouched; lag_one_both_ways() returns both numbers, and
split_strategy() returns "by time".
Needs: numpy, pandas, math; lab_support.load_slice; for the demonstration _narrate and
    plotly.

Twenty-five minutes.

Misconception this lab corrects: "the rows are in the order they were recorded."
They are not. The slice this lab loads arrived out of order and is shipped that
way deliberately. 11,143 of its 48,289 consecutive row pairs step backwards in
utc_time. Nothing in the file says so, every function still returns a number,
and the number is wrong in the direction that flatters you.

Almost every statistical result you will meet assumes that observations are
independent and identically distributed: each one drawn afresh, unaffected by
the last. Sensor data is not like that, and this lab makes you measure the
difference rather than take my word for it.

What you write: autocorrelation(series, lag), in_time_order(frame),
lag_one_both_ways(frame), and split_strategy().

Three ways to get the autocorrelation wrong, and all three are the point:

  * forgetting to subtract the mean, which measures size rather than co-movement
  * shifting by k+1 or k-1, which you will notice because lag 0 must give 1.0
  * measuring before ordering, which answers a different question entirely

Finish early? Run it on payload instead of speed and see which decays slower.
"""
from __future__ import annotations

import math
import pathlib
import sys

import numpy as np
import pandas as pd
import plotly.graph_objects as go

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from lab_support import NotSolved, load_slice  # noqa: E402
from _narrate import narrator, show_table, save_figure  # noqa: E402,F401

LAB = 1

# Below this many surviving pairs a correlation is arithmetic rather than
# evidence: two pairs always give exactly +1 or -1, whatever the data does.
# A stated choice, printed on the definition slide beside the formula.
MINIMUM_PAIRS = 30


def autocorrelation(series, lag: int) -> float:
    """The lag-k sample autocorrelation of `series`, in the order it was given.

    Args:
        series: a sequence of numbers, in whatever order it was handed to you.
                It may contain missing values.
        lag:    how many places to shift, zero or more.

    Returns:
        A float between -1 and 1, or not-a-number where the rules below say so.

    Definition graded by the check:
        r_k = Σ_{t=k+1}^{n} (x_t − x̄)(x_{t−k} − x̄) / Σ_{t=1}^{n} (x_t − x̄)²
        (Box, Jenkins, Reinsel & Ljung, 2015, §2.1; Hyndman & Athanasopoulos,
        2021, §2.8). Choices: one mean x̄ and one denominator, both over every
        value that is present; a pair (x_t, x_{t−k}) enters the numerator only
        when both members are present where they stand — do not drop the
        missing values first and close the gap, that pairs readings which were
        never neighbours; fewer than MINIMUM_PAIRS surviving pairs → nan.
        Slide: "Definition — lag-k sample autocorrelation".

    The contract in full, because one correlation is only comparable with
    another when both were computed under the same rule:

      1. lag 0 returns exactly 1.0.

      2. Pair the value at position t with the value at position t − lag. The
         first `lag` positions have no partner, so they take no part in the
         numerator. Every present value takes part in the mean and in the
         denominator.

      3. The overlap rule for missing values: a pair counts only when BOTH of
         its members are present, at their original positions.

      4. If fewer than MINIMUM_PAIRS pairs survive, return float("nan"). A
         correlation from a handful of pairs is not a measurement, and
         reporting it as one is how a confident wrong answer reaches a report.

    Do not call pandas' own autocorr. It computes a different estimator (the
    Pearson correlation of the two shifted copies, each with its own mean) and
    it does not implement rule 4, so it hands you a confident 1.0 exactly where
    this contract requires not-a-number. The check tests both differences on
    purpose: pandas' number differs from this one in the fourth decimal at lag
    120 on this very file.

    Needs: numpy, math
    """
    # TODO: replace this with your own calculation.
    raise NotSolved(
        "autocorrelation(series, lag) still raises instead of returning a number")


def in_time_order(frame):
    """The same rows, sorted so that utc_time never goes backwards.

    Args:
        frame: a table with a utc_time column, in the order it was loaded.

    Returns:
        A new table holding exactly the same rows — none added, none dropped,
        none altered — ordered by utc_time ascending, with the index reset to
        0, 1, 2, ... so that position and time finally agree.

    Definition graded by the check:
        sort by utc_time so that t_{i} ≤ t_{i+1} for every i < n; only then is
        a lag of k rows a lag of k·Δt in time
        (Box, Jenkins, Reinsel & Ljung, 2015, §2.1 — a time series is a
        sequence ordered in time, and the estimator above assumes it). Choices:
        sort by the parsed timestamp, not the text; a stable sort (mergesort),
        so rows sharing an instant keep their arrival order; the caller's frame
        is left untouched. Slide: "Definition — the monotone-timestamp rule".

    Do not modify the frame you were given. The next function needs the shipped
    order as well, and a lab that quietly sorts its own input in place produces
    two identical numbers and a student certain the lesson is fake.

    Needs: pandas
    """
    # TODO: parse utc_time, sort by it, reset the index, return the new frame.
    raise NotSolved("in_time_order(frame) still raises instead of returning a table")


def lag_one_both_ways(frame) -> dict:
    """The lag-one autocorrelation of speed, measured twice on the same rows.

    Args:
        frame: the table as load_slice() returned it, still in shipped order.

    Returns:
        {"as_shipped":    autocorrelation of speed at lag 1 in the given order,
         "in_time_order": autocorrelation of speed at lag 1 after ordering}

    Definition graded by the check:
        report r_1 as shipped and r_1 in time order, on the same rows
        (Box, Jenkins, Reinsel & Ljung, 2015, §2.1). Choices: r_1 is the
        estimator of autocorrelation() above; "in time order" means the frame
        in_time_order() returns, not the one you were given. Slide:
        "Definition — the monotone-timestamp rule".

    Both values are floats. Use the two functions you wrote above; this one is
    the wiring, not new arithmetic.

    Report both, always. The pair is the finding: one of these numbers describes
    the vehicle and the other describes the order somebody happened to write the
    rows in, and only the timestamp tells you which is which.

    Needs: autocorrelation, in_time_order, pandas
    """
    # TODO: measure the shipped order, then the time order, and return both.
    raise NotSolved(
        "lag_one_both_ways(frame) still raises instead of returning two numbers")


def split_strategy() -> str:
    """How should this data be split into training and test sets?

    Return exactly one of the two strings:

        "at random"   — shuffle the rows and cut
        "by time"     — everything before an instant trains, everything after tests

    Definition graded by the check:
        train = {x_t : t < t_c}, test = {x_t : t ≥ t_c} for one cut instant t_c
        — never a random permutation of the rows
        (Bergmeir & Benítez, 2012; Roberts et al., 2017). Choice: one cut
        instant, chosen before the model sees anything; Module 2 chooses it on
        this archive. Slide: "Definition — a split by time, never at random".

    Answer from what you measured above, not from habit. If consecutive readings
    are nearly identical, what does a random split put on both sides of the line?

    Needs: nothing but the measurement above
    """
    # TODO: return one of the two strings.
    raise NotSolved("split_strategy() still raises instead of returning a string")


if __name__ == "__main__":
    say = narrator(LAB)
    bus = load_slice()
    say.info("archive slice, %s rows, as shipped", f"{len(bus):,}")

    # The one-line question this whole lab exists to teach. It prints False.
    say.info("utc_time only ever increases: %s",
             pd.to_datetime(bus["utc_time"]).is_monotonic_increasing)

    ordered = in_time_order(bus)
    shipped_speed = bus["speed"].astype(float)
    ordered_speed = ordered["speed"].astype(float)
    table = pd.DataFrame({
        "lag": [0, 1, 20, 120],
        "as shipped": [autocorrelation(shipped_speed, k) for k in (0, 1, 20, 120)],
        "in time order": [autocorrelation(ordered_speed, k) for k in (0, 1, 20, 120)],
    })
    show_table(table, "speed autocorrelation, both orders", logger=say)
    say.info("lag one both ways: %s", lag_one_both_ways(bus))
    say.info("split: %s", split_strategy())
