#!/usr/bin/env python3
"""Check 1 — the autocorrelation is right, the rows are in order, and both numbers are reported.

This check does not call pandas' Series.autocorr. The lab forbids it, and a
check that grades against the very call the lab forbids proves nothing: the
one-line cheat passes it by construction. So the expected value is written out
here from the definition on the slide "Definition — lag-k sample
autocorrelation" — the Box–Jenkins sample autocorrelation, one mean and one
denominator over the whole series (Box, Jenkins, Reinsel & Ljung, 2015, §2.1;
Hyndman & Athanasopoulos, 2021, §2.8) — and two of the cases below are cases
where pandas' estimator and this one disagree on purpose: the fourth decimal at
lag 120, and not-a-number below the pair floor.
"""
import math
import sys, pathlib
import numpy as np
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from _harness import run, close, explain                             # noqa: E402
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from lab_support import load_slice                                   # noqa: E402
import pandas as pd                                                  # noqa: E402

# The same floor the lab states. Written here rather than imported from the lab,
# so that lowering it in the lab lowers nothing here.
MINIMUM_PAIRS = 30


def expected_autocorrelation(values, lag: int) -> float:
    """The definition on the slide, spelled out, so this check owns its answer.

    r_k = Σ_{t=k+1}^{n} (x_t − x̄)(x_{t−k} − x̄) / Σ_{t=1}^{n} (x_t − x̄)²

    One mean x̄ and one denominator, both over every value that is present; a
    pair (x_t, x_{t−k}) enters the numerator only when both members are present
    where they stand — the gaps are not closed first. Below MINIMUM_PAIRS
    surviving pairs, refuse to answer: two points always lie on a line, so a
    correlation from a handful of pairs is +1 or -1 whatever the data does.
    """
    series = np.asarray(values, dtype=float)
    if lag == 0:
        return 1.0
    present = ~np.isnan(series)
    both_present = present[lag:] & present[:-lag]
    if both_present.sum() < MINIMUM_PAIRS:
        return float("nan")
    deviation = series - series[present].mean()
    deviation[~present] = 0.0            # a missing value takes part in no sum
    numerator = float((deviation[lag:] * deviation[:-lag])[both_present].sum())
    denominator = float((deviation[present] ** 2).sum())
    if denominator == 0:
        return float("nan")
    return numerator / denominator


def pairwise_pearson(values, lag: int) -> float:
    """The other estimator — each shifted copy with its own mean and spread.

    This is what pandas' Series.autocorr computes. It is a legitimate
    statistic and it is not the one on the slide; the check names it here so
    that it can assert the two are told apart at a lag where they differ.
    """
    series = pd.Series(np.asarray(values, dtype=float)).reset_index(drop=True)
    return float(series.autocorr(lag))


def sparse_series() -> pd.Series:
    """Two hundred positions, ten adjacent pairs, everything else missing.

    At lag 1 exactly ten pairs survive, which is below the floor, so the
    contract requires not-a-number. pandas answers this case with a confident
    number instead — that is the disagreement, and it is what stops the lab
    being solved by delegating to the library it forbids.
    """
    values = [0.4, 1.9, 2.2, 0.1, 3.3, 1.1, 0.7, 2.8, 1.4, 2.0,
              0.9, 1.7, 2.5, 0.3, 3.1, 1.6, 0.6, 2.3, 1.2, 2.7]
    series = pd.Series([float("nan")] * 200)
    for pair in range(10):
        series[20 * pair] = values[2 * pair]
        series[20 * pair + 1] = values[2 * pair + 1]
    return series


def body(lab):
    bus = load_slice()
    speed = bus["speed"].astype(float).reset_index(drop=True)

    # --- the arithmetic, against this check's own formula
    zero = lab.autocorrelation(speed, 0)
    close(zero, 1.0, 1e-9, "autocorrelation at lag 0 must be exactly 1")

    # --- the estimator is the one on the slide, not the other legitimate one.
    # At lag 120 on this file the Box–Jenkins value and the pairwise Pearson
    # value differ by about 4.5e-4, well past the tolerance, so a student who
    # gave each shifted copy its own mean — or delegated to Series.autocorr —
    # is told which estimator they computed instead of "wrong by 0.0004". This
    # runs before the tolerance test so that the message is the useful one.
    measured_120 = lab.autocorrelation(speed, 120)
    other_120 = pairwise_pearson(speed, 120)
    assert not (abs(measured_120 - other_120) <= 1e-6), explain(
        "lab1:estimator",
        f"at lag 120 you gave {measured_120:.6f}, which is not the estimator the "
        "slide defines — it is the other legitimate one",
        "You computed the pairwise Pearson correlation of the two shifted copies, "
        "each with its own mean and its own spread, which is what pandas' "
        "Series.autocorr returns. The card \"Definition — lag-k sample "
        "autocorrelation\" grades the Box–Jenkins estimator instead: one mean x̄ and "
        "one denominator, both over the whole series. The two agree to three "
        "decimals at lag 1 and part company by the fourth at lag 120, which is why "
        f"this check asks at 120: the value it wants there is "
        f"{expected_autocorrelation(speed, 120):.6f}.")

    for shift in (1, 2, 20, 120):
        close(lab.autocorrelation(speed, shift),
              expected_autocorrelation(speed, shift), 1e-4,
              f"autocorrelation at lag {shift}, on the rows as they ship")

    # --- the overlap rule, on a series with holes punched in it
    # A student who drops the missing values first and closes the gap passes
    # everything above and fails here, because closing the gap pairs readings
    # that were never neighbours.
    generator = np.random.default_rng(0)
    holed = speed.copy()
    holed[generator.choice(len(holed), size=len(holed) // 5, replace=False)] = np.nan
    for shift in (1, 20):
        measured = lab.autocorrelation(holed, shift)
        closed_up = float(holed.dropna().reset_index(drop=True).autocorr(shift))
        close(measured, expected_autocorrelation(holed, shift), 1e-4,
              f"autocorrelation at lag {shift} with one fifth of the values missing")
        assert abs(measured - closed_up) > 1e-4, (
            f"at lag {shift} you gave {measured:.6f}, which is what you get by dropping "
            "the missing values first and closing the gap. That pairs readings which "
            "were never neighbours. Keep every value where it stands and drop the pair, "
            "not the value.")

    # --- the case pandas answers differently, which is the point of rule 5
    sparse = sparse_series()
    measured = lab.autocorrelation(sparse, 1)
    assert isinstance(measured, float) and math.isnan(measured), (
        f"with only ten surviving pairs your function returned {measured!r}. The "
        f"contract says not-a-number below {MINIMUM_PAIRS} pairs, because two points "
        "always lie on a line and a handful of pairs always look strongly correlated. "
        "pandas' own autocorr answers this case with a number — which is exactly why "
        "the lab tells you not to call it.")

    # The control: shuffled values must show no correlation at all. A student who
    # forgot the mean passes the tests above and fails this one.
    shuffled = speed.sample(frac=1, random_state=0).reset_index(drop=True)
    measured = lab.autocorrelation(shuffled, 1)
    assert abs(measured) < 0.02, explain(
        "lab1:control",
        f"on shuffled values the correlation should be near zero; you gave {measured:.4f}",
        "Shuffling destroys every relation between neighbouring readings, so anything "
        "far from nought is a property of your arithmetic rather than of the data. The "
        "usual cause is a sum of products of raw values instead of products of "
        "deviations: subtract x̄ from every value before you multiply, or you are "
        "measuring how far the series sits from zero.")

    # --- the rows have to be put in time order, and the original left alone
    before = pd.to_datetime(bus["utc_time"])
    ordered = lab.in_time_order(bus)
    after = pd.to_datetime(ordered["utc_time"])

    assert after.is_monotonic_increasing, explain(
        "lab1:monotone",
        "in_time_order() returned rows whose utc_time still goes backwards",
        "Sort by the parsed timestamp, not by the column as it arrived. Sorting it as "
        "text happens to give the right answer on this file, because every value here "
        "is written to the same three decimals — but that is luck rather than a rule, "
        "and one timestamp written to a different precision breaks it in silence.")
    assert len(ordered) == len(bus), (
        f"in_time_order() returned {len(ordered):,} rows from {len(bus):,}. Ordering is "
        "not filtering — every row must survive, including the ones that look wrong.")
    assert list(ordered.index) == list(range(len(ordered))), (
        "in_time_order() left the old index in place. The rows are in time order but "
        "position and index still disagree, so anything that aligns on the index puts "
        "them back the way they were. Reset it.")
    assert np.allclose(np.sort(ordered["speed"].astype(float).to_numpy()),
                       np.sort(bus["speed"].astype(float).to_numpy())), (
        "in_time_order() changed the values, not only their order.")
    assert pd.to_datetime(bus["utc_time"]).equals(before), (
        "in_time_order() sorted the caller's frame in place. The next function needs "
        "the shipped order as well — copy before you sort.")

    # --- both numbers reported, and the sorted one is the one that means anything
    both = lab.lag_one_both_ways(bus)
    assert isinstance(both, dict) and set(both) == {"as_shipped", "in_time_order"}, (
        'lag_one_both_ways() must return exactly the keys "as_shipped" and '
        f'"in_time_order"; you returned {sorted(both) if hasattr(both, "__iter__") else both!r}')

    shipped_value = expected_autocorrelation(speed, 1)
    ordered_value = expected_autocorrelation(
        ordered["speed"].astype(float).to_numpy(), 1)

    close(float(both["as_shipped"]), shipped_value, 1e-4,
          "lag_one_both_ways()['as_shipped'], measured on the rows as they ship")

    assert abs(float(both["in_time_order"]) - shipped_value) > 1e-4, explain(
        "lab1:both-ways",
        f"you reported {float(both['in_time_order']):.4f} for the time-ordered rows, "
        "which is the number the shipped order already gives",
        "The two keys are meant to hold two different measurements of the same rows, "
        "and yours hold one measurement twice. A lag is only a lag when the rows are "
        "in order: shifting by one position shifts by one row, and in this file the "
        "next row is anywhere from an hour earlier to an hour later. Order the frame "
        "first and then measure the ordered frame — not the one you started with.")
    close(float(both["in_time_order"]), ordered_value, 1e-4,
          "lag_one_both_ways()['in_time_order'], measured after ordering by utc_time")

    answer = lab.split_strategy().strip().lower()
    assert answer in {"at random", "by time"}, (
        f'split_strategy() must return "at random" or "by time"; you returned "{answer}"')
    assert answer == "by time", explain(
        "lab1:split",
        f'you answered "{answer}", and the two numbers you have just measured do not '
        "support it",
        f"In time order consecutive readings correlate at {ordered_value:.3f}. A random "
        "split therefore puts a reading and its own near-copy on opposite sides of the "
        "boundary, so the test set contains the training set in all but name and the "
        "score you report is a measurement of the leak. Cut the series at one instant "
        "instead: everything before it trains, everything after it tests (Bergmeir & "
        "Benítez, 2012).")


run(1, "01_is_it_independent", "autocorrelation", body)
