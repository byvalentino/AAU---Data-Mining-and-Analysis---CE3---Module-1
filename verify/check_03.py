#!/usr/bin/env python3
"""Check 3 — the day measured, declared, tested against its own declaration, and judged.

Four things are graded here and only the first two are arithmetic:

    profile()          the five dimensions, against the check's own measurement
    write_profile()    the document a person reads
    declare_profile()  the document a program reads — the contract Module 2 loads
    check_against()    that contract applied: silent on the day it came from,
                       and loud, naming the field, on a seeded corruption of it
    fitness_verdict()  the call and the argument for it, on five days built here
                       as dictionaries, so that nothing about the judgement
                       depends on the data being present

The verdict is the only place in the module where the check does not know the
answer. It holds no thresholds of its own. It reads the student's own
FITNESS_LIMITS and grades whether the five verdicts are consistent with that
boundary and with each other: the day that is at least as good as every other
must not be refused, the day that breaks every limit must not be used, a day at
least as good as another on all five quantities may not get the harsher call,
and the reason must be built out of the numbers the student was handed.
"""
import json, re, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from _harness import run, close, explain, grade_reason                # noqa: E402
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from lab_support import load_slice                                   # noqa: E402
import numpy as np                                                   # noqa: E402
import pandas as pd                                                  # noqa: E402

REPOSITORY = pathlib.Path(__file__).resolve().parent.parent
MILEAGE_CEILING = 65535
SEED = 20200122

# The direction in which each evidence quantity gets worse. The check holds its
# own copy rather than reading the lab's, because a check that imports its
# expectations from the thing it is grading is not a check.
HIGHER_IS_BETTER = ("worst_column_completeness", "effective_sample_size")
EVIDENCE_KEYS = ("worst_column_completeness", "largest_gap_seconds",
                 "backward_step_share", "effective_sample_size",
                 "implausible_row_share")
CALLS = ("use", "use with a caveat", "do not use")
SEVERITY = {call: rank for rank, call in enumerate(CALLS)}

# Five days, as dictionaries. Not one of them is loaded from a file: a verdict
# is a judgement about evidence, and the evidence is the five numbers.
#
# The shape of the set is what makes it gradeable without a threshold of ours.
# "a clean day" is at least as good as every other day on all five quantities;
# "a ruined day" is at least as bad as every other on all five; and the three
# days between them are pairwise incomparable — each is better than the others
# on something and worse on something else — so each of those three is a
# judgement that a defensible student could make either way.
FIXTURES = {
    "a clean day": {
        "worst_column_completeness": 0.9997, "largest_gap_seconds": 3.5,
        "backward_step_share": 0.0, "effective_sample_size": 1842.0,
        "implausible_row_share": 0.006},
    "one long gap": {
        "worst_column_completeness": 0.9981, "largest_gap_seconds": 5417.0,
        "backward_step_share": 0.0, "effective_sample_size": 1755.0,
        "implausible_row_share": 0.008},
    "the archive's own day": {
        "worst_column_completeness": 0.9962, "largest_gap_seconds": 876.3,
        "backward_step_share": 0.231, "effective_sample_size": 73.0,
        "implausible_row_share": 0.011},
    "a holed column": {
        "worst_column_completeness": 0.4118, "largest_gap_seconds": 4.2,
        "backward_step_share": 0.0, "effective_sample_size": 1690.0,
        "implausible_row_share": 0.014},
    "a ruined day": {
        "worst_column_completeness": 0.3106, "largest_gap_seconds": 7203.0,
        "backward_step_share": 0.4182, "effective_sample_size": 6.0,
        "implausible_row_share": 0.442},
}
BEST, WORST = "a clean day", "a ruined day"

# The day whose verdict turns on one quantity while the other four are as good
# as the best day's: whatever is decided about it, the reason has to name the
# thing that is out of line.
DECIDING = {"one long gap": "largest_gap_seconds",
            "a holed column": "worst_column_completeness"}


def truth(frame):
    """The check measures independently. It never imports the solution."""
    utc = pd.to_datetime(frame["utc_time"])
    ordered = frame.assign(_u=utc).sort_values("_u")
    steps = ordered.groupby(ordered["_u"].dt.date)["_u"].diff().dt.total_seconds().dropna()
    return {
        "median_interval_s": float(steps.median()),
        "gaps_over_60s": int((steps > 60).sum()),
        "duplicate_rows": int(frame.duplicated().sum()),
        "duplicate_vehicle_time": int(frame.duplicated(subset=["vehicle_id", "utc_time"]).sum()),
        "negative_speed_rows": int((frame["speed"] < 0).sum()),
        "mileage_at_ceiling": int((frame["mileage"] == MILEAGE_CEILING).sum()),
    }


def corrupt(frame):
    """One day that breaks five different declared rules, the same way everywhere.

    Seeded with the course seed, so the corruption is identical on every machine
    and a student can reproduce exactly the frame their check failed on.

      utc_time        every third reading survives, so the sampling step triples
      speed           500 rows at 999 metres per second, which no shuttle reaches
      battery_level   absent on three rows in five
      mileage         twenty rows carrying the text "unknown", so the column is
                      no longer numeric at all
      ramp_state      gone
    """
    generator = np.random.default_rng(SEED)
    utc = pd.to_datetime(frame["utc_time"])
    broken = (frame.assign(_u=utc).sort_values("_u").iloc[::3]
              .drop(columns="_u").reset_index(drop=True))

    broken.loc[generator.choice(len(broken), 500, replace=False), "speed"] = 999.0
    blanked = generator.choice(len(broken), int(0.6 * len(broken)), replace=False)
    broken.loc[blanked, "battery_level"] = np.nan
    broken["mileage"] = broken["mileage"].astype(object)
    broken.loc[generator.choice(len(broken), 20, replace=False), "mileage"] = "unknown"
    return broken.drop(columns=["ramp_state"])


def breaches(evidence, limits):
    """Which of the five quantities lie outside the student's own boundary."""
    outside = []
    for key in EVIDENCE_KEYS:
        limit, value = float(limits[key]), float(evidence[key])
        if (value < limit) if key in HIGHER_IS_BETTER else (value > limit):
            outside.append(key)
    return outside


def at_least_as_good(better, worse):
    """True when `better` is no worse than `worse` on every one of the five."""
    for key in EVIDENCE_KEYS:
        if key in HIGHER_IS_BETTER:
            if better[key] < worse[key]:
                return False
        elif better[key] > worse[key]:
            return False
    return True


def grade_the_profile(lab, frame, expected, measured):
    """The five dimensions, and the document a person reads."""
    for section in ("completeness", "uniqueness", "validity", "consistency", "timeliness"):
        assert section in measured, f"profile() did not return a '{section}' section"

    close(measured["timeliness"]["median_interval_s"], expected["median_interval_s"],
          1e-3, "timeliness → median_interval_s")
    close(measured["timeliness"]["gaps_over_60s"], expected["gaps_over_60s"], 0,
          "timeliness → gaps_over_60s (count them within a day; across days the "
          "largest gap is the night)")
    close(measured["uniqueness"]["duplicate_rows"], expected["duplicate_rows"], 0,
          "uniqueness → duplicate_rows")
    close(measured["uniqueness"]["duplicate_vehicle_time"],
          expected["duplicate_vehicle_time"], 0, "uniqueness → duplicate_vehicle_time")
    close(measured["validity"]["negative_speed_rows"], expected["negative_speed_rows"], 0,
          "validity → negative_speed_rows (count them, do not drop them)")
    close(measured["validity"]["mileage_at_ceiling"], expected["mileage_at_ceiling"], 0,
          f"validity → mileage_at_ceiling (rows where mileage == {MILEAGE_CEILING})")

    completeness = measured["completeness"]
    assert len(completeness) == frame.shape[1], (
        f"completeness covers {len(completeness)} columns; the frame has {frame.shape[1]}. "
        "Measure every column, not only the bad ones.")
    close(completeness["emergency_stop"], float(frame["emergency_stop"].notna().mean()),
          1e-4, "completeness → emergency_stop")

    offsets = measured["consistency"]["timestamp_minus_utc_hours"]
    assert [round(float(v), 2) for v in offsets] == [1.0], (
        f"consistency → timestamp_minus_utc_hours should be [1.0]; you gave {offsets}. "
        "The column named `timestamp` is local time.")

    # The written document. A profile nobody can read is not a profile.
    lab.write_profile(measured)
    profile_file = REPOSITORY / "DATA_PROFILE.md"
    assert profile_file.exists(), "write_profile() did not create DATA_PROFILE.md"
    text = profile_file.read_text()

    for name in ("median_interval_s", "gaps_over_60s", "duplicate_rows",
                 "negative_speed_rows", "mileage_at_ceiling"):
        found = re.search(rf"-\s*{name}\s*:\s*([-\d.]+)", text)
        assert found, (
            f"DATA_PROFILE.md has no line `- {name}: <value>`. The check reads this "
            "file, so the format matters.")
        close(float(found.group(1)), float(expected[name]), 1e-3,
              f"DATA_PROFILE.md → {name}")


def grade_the_declaration(lab, frame, expected, measured):
    """The document a program reads, and what happens when it meets a broken day."""
    declaration = lab.declare_profile(frame, measured)
    assert isinstance(declaration, dict), (
        f"declare_profile() returned {type(declaration).__name__}, not a dictionary")

    written = REPOSITORY / "out" / "data_profile.json"
    assert written.exists(), (
        "declare_profile() did not write out/data_profile.json. Module 2 loads that "
        "file by name; a declaration that stays in memory is not a hand-off.")
    on_disk = json.loads(written.read_text())
    assert on_disk == json.loads(json.dumps(declaration)), (
        "the dictionary declare_profile() returned and the one it wrote to "
        "out/data_profile.json are not the same. One of them is describing a dataset "
        "that nobody has.")

    assert on_disk.get("schema") == "aau-ce3/data-profile/1", (
        f"out/data_profile.json declares schema {on_disk.get('schema')!r}; the contract "
        "in HANDOFF.md fixes it at 'aau-ce3/data-profile/1', because the first thing "
        "Module 2 does is refuse a file it does not recognise.")
    for key in ("module", "dataset", "rows", "time_column", "expected_step_seconds",
                "step_tolerance_share", "columns"):
        assert key in on_disk, (
            f"out/data_profile.json has no {key!r} key. HANDOFF.md lists the seven "
            "top-level keys and Module 2 reads every one of them.")
    close(on_disk["rows"], len(frame), 0, "out/data_profile.json → rows")
    assert on_disk["time_column"] in frame.columns, (
        f"time_column is {on_disk['time_column']!r}, which is not a column of the frame")
    close(on_disk["expected_step_seconds"], expected["median_interval_s"], 1e-2,
          "out/data_profile.json → expected_step_seconds (the median interval within a day)")
    assert 0 < float(on_disk["step_tolerance_share"]) < 1, (
        f"step_tolerance_share is {on_disk['step_tolerance_share']}; it is a fraction of "
        "the expected step, so nought admits nothing and one admits everything")

    assert set(on_disk["columns"]) == set(frame.columns), (
        "out/data_profile.json declares "
        f"{len(on_disk['columns'])} columns and the frame has {frame.shape[1]}. Declare "
        "every column: a column nobody declared is a column nobody can test.")
    for name, rule in on_disk["columns"].items():
        missing_keys = {"type", "unit", "minimum", "maximum", "max_missing_share"} - set(rule)
        assert not missing_keys, (
            f"out/data_profile.json → {name} has no {sorted(missing_keys)}. The five key "
            "names are the contract in HANDOFF.md.")
        assert rule["type"] in ("number", "text"), (
            f"out/data_profile.json → {name} declares type {rule['type']!r}; the two "
            "values are 'number' and 'text'")
        assert 0.0 <= float(rule["max_missing_share"]) <= 1.0, (
            f"out/data_profile.json → {name}: max_missing_share is "
            f"{rule['max_missing_share']}, which is not a share")

    # The declaration must be true of the day it was declared from.
    quiet = lab.check_against(frame, declaration)
    assert isinstance(quiet, list), (
        f"check_against() returned {type(quiet).__name__}, not a list of strings")
    assert quiet == [], explain(
        "lab3:clean-day",
        f"check_against() reported {len(quiet)} breach(es) on the very day the profile "
        f"was declared from: {quiet[:3]}",
        "A declaration that its own data violates is not a declaration, it is a wish. "
        "Widen whichever rule fired until the day you measured satisfies it — and no "
        "further, because the next assertion lands a genuinely broken day on you.")

    # And it must catch a day that breaks it.
    broken = corrupt(frame)
    found = lab.check_against(broken, declaration)
    assert isinstance(found, list) and all(isinstance(line, str) for line in found), (
        "check_against() must return a list of strings, one line per breach")
    assert len(found) >= 5, explain(
        "lab3:corruption",
        f"the seeded corruption breaks five declared rules and check_against() found "
        f"{len(found)}",
        "The corrupted day drops a declared column, turns a numeric column into text, "
        "puts 500 rows far above a declared maximum, blanks three rows in five of "
        "another column, and triples the sampling step. Five rules, five lines. If your "
        "declaration is so wide that some of them are not breaches, it is a range "
        "nothing can violate, which is the same as having declared nothing.")

    reported = " ".join(found).lower()
    for field, what in (
            ("ramp_state", "a column you declared and the frame does not have"),
            ("mileage", "a column declared as a number that arrived as text"),
            ("speed", "500 rows at 999, far above any defensible maximum"),
            ("battery_level", "a column absent on three rows in five"),
            (str(on_disk["time_column"]), "a sampling step three times the declared one")):
        assert field.lower() in reported, explain(
            f"lab3:names:{field}",
            f"no line of check_against() names {field!r}",
            f"The corrupted day has {what}. Every complaint has to begin with the field "
            "it is about, because the person reading it at seven in the morning needs "
            "the name before the sentence — and because this check finds the rule you "
            "missed by looking for that name.")
    return declaration


def grade_the_verdict(lab, frame, measured, declaration):
    """The judgement. The check has no threshold of its own and grades consistency."""
    limits = getattr(lab, "FITNESS_LIMITS", None)
    assert isinstance(limits, dict), "FITNESS_LIMITS is not a dictionary"
    missing = [key for key in EVIDENCE_KEYS
               if not isinstance(limits.get(key), (int, float))
               or isinstance(limits.get(key), bool)]
    assert not missing, (
        f"FITNESS_LIMITS still has no number for {missing}. The boundary is yours to "
        "set and nobody else's to guess; the check applies exactly the numbers you put "
        "there, and until they are numbers there is nothing to apply.")

    # The pipeline end to end on the real slice: the student's own measurements
    # become the evidence a verdict is made of.
    real = lab.evidence_from(frame, measured, declaration)
    for key in EVIDENCE_KEYS:
        assert key in real and float(real[key]) == float(real[key]), (
            f"evidence_from() gave no usable {key} on the archive slice")

    calls, reasons = {}, {}
    for name, evidence in FIXTURES.items():
        handed = dict(evidence)
        answer = lab.fitness_verdict(handed)
        assert isinstance(answer, tuple) and len(answer) == 2, (
            f"fitness_verdict() on {name!r} returned {answer!r}; it returns the pair "
            "(call, reason)")
        call, reason = answer
        assert call in CALLS, (
            f"fitness_verdict() called {name!r} {call!r}. The three calls are "
            f"{', '.join(repr(c) for c in CALLS)} and there is no fourth.")
        assert handed == evidence, (
            f"fitness_verdict() changed the evidence dictionary it was given, on {name!r}. "
            "A verdict reads its evidence; it does not edit it.")
        again, _ = lab.fitness_verdict(dict(evidence))
        assert again == call, (
            f"fitness_verdict() called {name!r} {call!r} and then {again!r} on the same "
            "evidence. A verdict that is not a function of its evidence cannot be "
            "defended to anybody.")
        grade_reason(reason, {**evidence,
                              **{f"limit_{k}": float(v) for k, v in limits.items()}},
                     key=f"lab3:reason:{name}", minimum_keys=2)
        calls[name], reasons[name] = call, reason

    # The reason has to be about the day it is about.
    for name, deciding in DECIDING.items():
        spoken = reasons[name].lower().replace("_", " ")
        assert deciding.replace("_", " ") in spoken, explain(
            f"lab3:deciding:{name}",
            f"your reason for {name!r} never names {deciding}",
            f"On that day the other four quantities are as good as the best day's and "
            f"{deciding} is the one that is out of line. Whatever you decided about it, "
            "the quantity that decided it has to appear in the argument — otherwise the "
            "reason is about a different day.")
    distinct = {reason.strip().lower() for reason in reasons.values()}
    assert len(distinct) == len(reasons), explain(
        "lab3:same-reason",
        f"{len(reasons)} days and {len(distinct)} distinct reason(s)",
        "One sentence cannot be the argument for a day you use and a day you refuse. "
        "Build the reason out of the evidence you were handed, day by day.")

    # The two ends. Neither is a threshold of ours: one day is at least as good
    # as every other on all five quantities, the other at least as bad.
    assert calls[BEST] == "use", explain(
        "lab3:best-day",
        f"you called {BEST!r} {calls[BEST]!r}",
        f"{BEST!r} is at least as good as every other day here on all five quantities. "
        "If it cannot be used, nothing can, and 'do not use' has stopped being a "
        "judgement and become a default — which is the failure mode this question "
        "exists to catch.")
    assert calls[WORST] != "use", explain(
        "lab3:worst-day",
        f"you called {WORST!r} {calls[WORST]!r}",
        f"{WORST!r} is at least as bad as every other day here on all five quantities "
        "at once — one row in three out of order, six independent readings in the whole "
        "day, and nearly half the rows outside the range you yourself declared. If that "
        "is usable then the word means nothing.")
    assert "do not use" in calls.values(), explain(
        "lab3:no-refusal",
        "not one of the five days was refused",
        "Three calls exist because some days cannot be rescued by a caveat. A verdict "
        "function that never refuses is a function of nothing.")

    # The boundary the student declared, applied to the days they judged.
    for name, evidence in FIXTURES.items():
        outside = breaches(evidence, limits)
        if not outside:
            assert calls[name] == "use", explain(
                f"lab3:limits-clear:{name}",
                f"nothing about {name!r} is outside your own FITNESS_LIMITS and you "
                f"called it {calls[name]!r}",
                "Then either the limits are not where you think they are, or the verdict "
                "is not using them. A boundary that your own verdicts ignore is not a "
                "boundary, and the reason you wrote is describing a rule you did not "
                "apply.")
        if outside:
            # Without this the boundary bound only the two ends, and a verdict
            # that judged on one quantity and ignored the other four passed:
            # every day with between one and four breaches was unconstrained.
            # A limit is the point at which a quantity stops being a wobble and
            # starts being a reason -- so a day that is outside one may still go
            # forward, but not silently and not unconditionally.
            assert calls[name] != "use", explain(
                f"lab3:limits-breached:{name}",
                f"{sorted(outside)} on {name!r} lie outside your own FITNESS_LIMITS "
                f"and you still called it {calls[name]!r}",
                "You declared that limit as the point where the quantity stops being "
                "a wobble and starts being a reason. A day that crosses it can still "
                "go forward, but only with the crossing written down as a condition — "
                "that is what the middle call is for. If you meant this day to be used "
                "as it stands, the limit is in the wrong place; move it and say why, "
                "and remember that the day which breaks nothing still has to come out "
                "'use'.")
        if len(outside) == len(EVIDENCE_KEYS):
            assert calls[name] == "do not use", explain(
                f"lab3:limits-all:{name}",
                f"every one of the five quantities on {name!r} is outside your own "
                f"FITNESS_LIMITS and you called it {calls[name]!r}",
                "A caveat names the one thing you are working around. When all five are "
                "outside the limits you set, there is nothing left to work around.")

    # Consistency between the days: a day no worse on any quantity than another
    # may not be treated more harshly. This is the whole of what "applied
    # consistently" can mean without the check owning a threshold.
    for better in FIXTURES:
        for worse in FIXTURES:
            if better == worse or not at_least_as_good(FIXTURES[better], FIXTURES[worse]):
                continue
            assert SEVERITY[calls[better]] <= SEVERITY[calls[worse]], explain(
                f"lab3:order:{better}|{worse}",
                f"you called {better!r} {calls[better]!r} and {worse!r} "
                f"{calls[worse]!r}",
                f"{better!r} is at least as good as {worse!r} on every one of the five "
                "quantities — not better on balance, better or equal on each one. Two "
                "verdicts that reverse that order cannot both come from one boundary, "
                "and an examiner will ask which of the two you meant.")


def body(lab):
    frame = load_slice()
    before = frame.shape
    expected = truth(frame)
    measured = lab.profile(frame)

    assert frame.shape == before, (
        "profile() changed the frame it was given. This lab describes; it does not repair.")

    grade_the_profile(lab, frame, expected, measured)
    declaration = grade_the_declaration(lab, frame, expected, measured)
    grade_the_verdict(lab, frame, measured, declaration)


run(3, "03_profile_the_day", "profile", body)
