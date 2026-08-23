"""Lab 1, solved — with the reasoning, not only the code.

Run it: `python3 solutions/lab_01.py` from exercises/, or `python3
labs/01_is_it_independent.py` after `python3 apply.py`. It narrates what it
loads, measures the autocorrelation in both orders, and writes the figure
out/lab_01_autocorrelation_by_order.html (and .png).
"""
from __future__ import annotations

import math
import pathlib
import sys

import numpy as np
import pandas as pd
import plotly.graph_objects as go

LAB = 1

# Below this many surviving pairs a correlation is arithmetic rather than
# evidence: two pairs always give exactly +1 or -1, whatever the data does.
# A stated choice, printed on the definition slide beside the formula.
MINIMUM_PAIRS = 30


def autocorrelation(series, lag: int) -> float:
    """The lag-k sample autocorrelation, as defined on the slide.

        r_k = Σ_{t=k+1}^{n} (x_t − x̄)(x_{t−k} − x̄) / Σ_{t=1}^{n} (x_t − x̄)²

    Implements the sample autocorrelation of Box, Jenkins, Reinsel & Ljung
    (2015, §2.1), the form Hyndman & Athanasopoulos (2021, §2.8) print. The
    four things that make this correct rather than nearly correct:

    1. Deviations from the mean. Correlation is about how two things vary
       together around their centre. Multiply the raw values instead and you
       measure size, not co-movement — and on a series that is mostly positive
       you will get something close to 1 whatever the data does.
    2. One mean and one denominator, over the whole series. The pairwise
       alternative — each shifted copy with its own mean, which is what pandas'
       Series.autocorr computes — is a legitimate statistic and a different one;
       the two differ in the fourth decimal at lag 120 on this file, and the
       check grades this one because it is the one in the books.
    3. The overlap rule for missing values. A pair enters the numerator only if
       both of its members are present where they stand. Note what is NOT done:
       dropping the missing values before shifting. That closes the gap and
       pairs readings which were never neighbours.
    4. A floor on how many pairs may carry the answer. Two surviving pairs give
       exactly +1 or -1 for any data at all, because two points always lie on a
       line. Returning that number is worse than returning nothing, so this
       returns nothing: not-a-number, which no reader can mistake for evidence.

    Point 4 is the one pandas' own autocorr does not do, and it is why calling
    it here is not merely against the rules but wrong.
    """
    values = np.asarray(pd.Series(series).astype(float), dtype=float)
    if lag == 0:
        return 1.0

    present = ~np.isnan(values)
    both_present = present[lag:] & present[:-lag]
    if both_present.sum() < MINIMUM_PAIRS:
        return math.nan

    deviation = values - values[present].mean()
    deviation[~present] = 0.0            # a missing value takes part in no sum
    numerator = float(np.sum((deviation[lag:] * deviation[:-lag])[both_present]))
    denominator = float(np.sum(deviation[present] ** 2))
    if denominator == 0:                  # a constant series has no variation to correlate
        return math.nan
    return numerator / denominator


def in_time_order(frame):
    """Sort by the timestamp, and leave the caller's table alone.

    mergesort is stable, so rows sharing a timestamp keep the order they
    arrived in. That matters here: an unstable sort would give a different
    answer on a different machine, and a measurement that moves between
    machines is not a measurement.

    reset_index matters as much as the sort. Without it the rows are in time
    order but the index still carries the old positions, and anything that
    later aligns on the index quietly puts them back the way they were.
    """
    ordered = frame.assign(_utc=pd.to_datetime(frame["utc_time"]))
    ordered = ordered.sort_values("_utc", kind="mergesort").reset_index(drop=True)
    return ordered.drop(columns="_utc")


def lag_one_both_ways(frame) -> dict:
    """The same rows measured twice, because the pair is the finding.

    Shipped order gives about 0.9608. Time order gives about 0.9970. Neither
    number is an error: they are answers to two different questions, and only
    the timestamp says which question you asked.

    The direction matters more than the size. Disorder pushes the correlation
    down, towards what independent draws would look like. A distortion that
    makes data look messier gets investigated; a distortion that makes data look
    more independent than it is gets believed, because it licenses the
    convenient decision — a random split.
    """
    shipped = frame["speed"].astype(float)
    ordered = in_time_order(frame)["speed"].astype(float)
    return {
        "as_shipped": autocorrelation(shipped, 1),
        "in_time_order": autocorrelation(ordered, 1),
    }


def split_strategy() -> str:
    """By time, and the measurement is the argument.

    Once the rows are in time order, consecutive speed readings correlate at
    about 0.997. A random split therefore puts a reading in the training set and
    its own neighbour — very nearly the same number — in the test set. The model
    is then tested on something it has effectively already seen, scores
    beautifully, and fails the moment it meets a genuinely new stretch of time.

    Splitting by time is the only split that asks the question you actually
    care about: given the past, can it handle the future? (Bergmeir & Benítez,
    2012; Roberts et al., 2017.)
    """
    return "by time"


if __name__ == "__main__":
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
    from _narrate import narrator, show_table, save_figure
    from lab_support import load_slice

    say = narrator(LAB)
    say.info("Lab 1 — the same speed column, three orders: is a reading an independent draw?")
    bus = load_slice()
    say.info("loaded the archive slice, %s rows x %d columns, exactly as it ships",
             f"{len(bus):,}", bus.shape[1])

    # The one-line rule, asked first because everything below depends on it.
    monotone = pd.to_datetime(bus["utc_time"]).is_monotonic_increasing
    say.info("utc_time only ever increases: %s — so a lag of one row is not a lag "
             "of half a second until the rows are sorted", monotone)

    ordered = in_time_order(bus)
    say.info("sorted by utc_time with a stable sort and the index reset; %s rows in, "
             "%s rows out, none altered", f"{len(bus):,}", f"{len(ordered):,}")
    shipped_speed = bus["speed"].astype(float)
    ordered_speed = ordered["speed"].astype(float)
    shuffled_speed = ordered_speed.sample(frac=1, random_state=0).reset_index(drop=True)
    say.info("control: the same values shuffled with seed 0 — what independence looks like")

    lags = [1, 2, 5, 10, 20, 40, 60, 120, 240, 600, 1200]
    table = pd.DataFrame({
        "lag (rows)": lags,
        "as shipped": [autocorrelation(shipped_speed, k) for k in lags],
        "in time order": [autocorrelation(ordered_speed, k) for k in lags],
        "shuffled": [autocorrelation(shuffled_speed, k) for k in lags],
    })
    show_table(table, "speed, lag-k sample autocorrelation (dimensionless), three orders",
               logger=say)

    both = lag_one_both_ways(bus)
    say.info("lag-1 autocorrelation of speed, rows as shipped: %.4f", both["as_shipped"])
    say.info("lag-1 autocorrelation of speed, rows sorted by utc_time: %.4f",
             both["in_time_order"])
    say.info("the disorder pushes the number down, towards independence — the direction "
             "that licenses a random split, which is why both numbers are reported")
    rho = both["in_time_order"]
    say.info("effective sample size n(1 − ρ)/(1 + ρ) at ρ = %.4f: about %.0f independent "
             "observations in %s rows (Bayley & Hammersley, 1946)",
             rho, len(bus) * (1 - rho) / (1 + rho), f"{len(bus):,}")
    say.info("split strategy: %s", split_strategy())

    fig = go.Figure()
    fig.add_hline(y=0, line_color="#52514E", line_width=1)
    fig.add_trace(go.Scatter(x=lags, y=table["in time order"], mode="lines+markers",
                             name="rows sorted by utc_time", line_color="#2A78D6"))
    fig.add_trace(go.Scatter(x=lags, y=table["as shipped"], mode="lines+markers",
                             name="rows as the file ships", line_color="#E07B39"))
    fig.add_trace(go.Scatter(x=lags, y=table["shuffled"], mode="lines+markers",
                             name="the same values, shuffled (control)",
                             line=dict(color="#52514E", dash="dot")))
    fig.update_layout(
        title="Lag-k sample autocorrelation of speed — sorted, as shipped, shuffled",
        xaxis=dict(title="lag k (rows; one row is 0.5 s only in time order)", type="log"),
        yaxis=dict(title="sample autocorrelation r_k (dimensionless)"),
        legend=dict(x=0.62, y=0.98))
    save_figure(fig, "autocorrelation_by_order", LAB, logger=say)

    say.info("what the check grades: autocorrelation() equals the Box–Jenkins estimator to "
             "1e-4 at lags 1, 2, 20 and 120 (and is not the pairwise one), returns nan below "
             "%d pairs, keeps holes where they stand; in_time_order() is monotone, same rows, "
             "index reset, caller untouched; both lag-1 numbers reported; split \"by time\"",
             MINIMUM_PAIRS)
