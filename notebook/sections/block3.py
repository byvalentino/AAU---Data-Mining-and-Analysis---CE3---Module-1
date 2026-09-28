"""Block three — what you actually have, measured; Laboratory 3."""

S = "Module 1/exercises/solutions"
LABS = "Module 1/exercises/labs"
MAKE_FIGS = "Module 1/slides/make_figs.py"
HARNESS = "Module 1/exercises/verify/_harness.py"
CHECK_3 = "Module 1/exercises/verify/check_03.py"


def build(nb, explain) -> None:
    nb.md("""
    ---
    # Block three — What you actually have, measured

    *Slides 43–61.*

    ### Metadata is the difference between a number and a fact

    *Slides: "Metadata is the difference between a number and a fact", "Metadata — the
    data dictionary, and the profile you write" and "The five dimensions of data
    quality".* For every field four things must be written down: the unit, the source,
    the valid range and the owner [@riley2017]; a datasheet asks the same of a whole
    dataset [@gebru2021]. Without the unit, 170 is not a payload.

    The five dimensions measured here are completeness, uniqueness, validity,
    consistency and timeliness: the six primary dimensions of the DAMA UK working group
    minus accuracy [@dama2013], which this archive cannot measure without a second
    instrument. The UK Government Data Quality Hub restates the same six "as defined by"
    DAMA UK [@govuk]. That quality is fitness for use is {@wang1996}; that each dimension
    is a computable ratio is {@pipino2002}; the survey is {@batini2009}.

    ## Laboratory 3 — the solution, dimension by dimension
    """)
    explain(
        "Make the Lab 3 solution's paths resolve in the working copy.",
        "The solution writes `DATA_PROFILE.md` and `out/data_profile.json` beside the "
        "folder above its own file.",
        "Points `__file__` at `solutions/lab_03.py` in the working copy.",
        "The next cell's `REPOSITORY` is the working copy, so every file Lab 3 writes lands "
        "there and nowhere else.")
    nb.code('''
    __file__ = str(Path.cwd() / "solutions" / "lab_03.py")
    ''')
    explain(
        "Define the constants of Lab 3: the paths, the schema, the units, and the boundary "
        "of the fitness verdict.",
        "Every number here is a choice, and the comment above each says why it has the "
        "value it has — standing rule 2: a number carries the choice that produced it.",
        "Copies them from `solutions/lab_03.py`, verbatim, with their comments.",
        "`FITNESS_LIMITS` is the reference solution's boundary; the check holds none of its "
        "own and grades only that the verdicts obey whichever boundary the student declares.")
    nb.source(f"{S}/lab_03.py", "LAB", "REPOSITORY", "PROFILE_PATH", "PROFILE_JSON",
              "MILEAGE_CEILING", "PROFILE_SCHEMA", "EVIDENCE_KEYS", "HIGHER_IS_BETTER",
              "VERDICT_CALLS", "FITNESS_LIMITS", "NO_CAVEAT_REPAIRS_IT", "CAVEATS",
              "RANGE_MARGIN", "MISSING_MARGIN", "STEP_TOLERANCE", "UNITS",
              cite="[@bayley1946]")

    # --- slide 47: completeness ------------------------------------------------------------------
    nb.md("### Definition — completeness\n\n*Slide: \"Definition — completeness\".*")
    explain(
        "Write completeness as the slide defines it.",
        "Completeness of a column is the share of the n rows that carry a value in it, "
        "measured before anything is cleaned [@dama2013; @pipino2002].",
        "Writes the ratio as a sympy sum of indicators over rows.",
        "Present means not null, so an empty string counts as present; the ratio is not "
        "rounded before it is compared.")
    nb.equation("completeness", r'''
    i, n_rows = sp.symbols("i n", integer=True, positive=True)
    j_ = sp.Symbol("j", integer=True, positive=True)
    present = sp.Function(r"\mathbf{1}")(sp.Ne(sp.IndexedBase("x")[i, j_], sp.Symbol(r"\mathrm{null}")))
    formula(sp.Eq(sp.Indexed(r"\mathrm{completeness}", j_), sp.Sum(present, (i, 1, n_rows)) / n_rows,
                  evaluate=False), r"\text{for every column } j")
    ''', slides=["47"])
    explain(
        "Define `profile()` as the Lab 3 solution writes it.",
        "It measures the five dimensions and repairs nothing: the negative speeds stay, the "
        "ceiling values stay. A profile that has quietly cleaned its subject describes a "
        "dataset that does not exist.",
        "Copies `profile` from `solutions/lab_03.py`, verbatim.",
        "One function returns all five dimensions; the cells below check each against the "
        "slide that defines it.")
    nb.source(f"{S}/lab_03.py", "profile", cite="[@dama2013; @pipino2002]")
    explain(
        "Profile the slice, and check completeness against the slides.",
        "The completeness slides quote two scopes in one breath: 55.344 per cent of archive "
        "rows carry `emergency_stop`, and 52.574 per cent of the slice's.",
        "Runs `profile()` on the slice as shipped, confirms the frame was left unchanged, and "
        "checks the incomplete columns and the count of complete ones.",
        "The slice reproduces the slice numbers exactly; the archive's 55.344 is printed "
        "beside, as the archive's.")
    nb.code('''
    shape_before = bus.shape
    measurements = profile(bus)
    assert bus.shape == shape_before
    completeness = pd.Series(measurements["completeness"])
    agrees("complete columns of 22 (slice)", int((completeness == 1).sum()), 19)
    agrees("emergency_stop present, per cent of rows (slice)", 100 * completeness["emergency_stop"], 52.574, 3)
    agrees("platform present, per cent of rows (slice)", 100 * completeness["platform"], 99.981, 3,
           expected_from="slide 52's figure")
    agrees("battery_level present, per cent of rows (slice)", 100 * completeness["battery_level"], 99.998, 3,
           expected_from="slide 52's figure")
    beside("emergency_stop present, per cent of rows", f"{100 * completeness['emergency_stop']:.3f} (slice)",
           f"{archive('completeness_incomplete')['emergency_stop']} (archive)",
           "the archive holds a second vehicle, which only ran on 22 January")
    ''')

    # --- slides 48-50: uniqueness, validity, consistency ------------------------------------------
    nb.md("### Definitions — uniqueness, validity, consistency\n\n*Slides: \"Definition — "
          "uniqueness\", \"Definition — validity\" and \"Definition — consistency\".*")
    explain(
        "Write the three definitions as the slides state them.",
        "Uniqueness fails when one thing is recorded twice; validity is conformance to a "
        "stated rule of type and range; consistency asks whether fields that must agree do "
        "agree [@dama2013; @pipino2002].",
        "Writes the duplicate counts as differences of set sizes, the validity counts as set "
        "sizes, and the consistency measure as a set of offsets in hours — each a sympy set "
        "object built over the rows {1, …, n} of the file, counted with `card`.",
        "Each is a number or a set a program can compare; none is an opinion.")
    nb.equation("uniqueness_validity_consistency", r'''
    i, n_rows = sp.symbols("i n", integer=True, positive=True)
    rows_of_file = NamedSet(r"\{1, \ldots, n\}")
    row, vehicle, utc = sp.IndexedBase("r"), sp.IndexedBase(r"\mathrm{vehicle\_id}"), sp.IndexedBase(r"\mathrm{utc\_time}")
    speed_i, mileage_i = sp.IndexedBase(r"\mathrm{speed}"), sp.IndexedBase(r"\mathrm{mileage}")
    stamp_i = sp.IndexedBase(r"\mathrm{timestamp}")
    ceiling = sp.Add(sp.Pow(2, 16, evaluate=False), -1, evaluate=False)
    formula(sp.Eq(sp.Symbol(r"\mathrm{duplicate\_rows}"),
                  n_rows - card(sp.ImageSet(sp.Lambda(i, row[i]), rows_of_file)), evaluate=False),
            sp.Eq(sp.Symbol(r"\mathrm{duplicate\_vehicle\_time}"),
                  n_rows - card(sp.ImageSet(sp.Lambda(i, sp.Tuple(vehicle[i], utc[i])), rows_of_file)),
                  evaluate=False))
    formula(sp.Eq(sp.Symbol(r"\mathrm{negative\_speed\_rows}"),
                  card(sp.ConditionSet(i, speed_i[i] < 0, rows_of_file)), evaluate=False),
            sp.Eq(sp.Symbol(r"\mathrm{mileage\_at\_ceiling}"),
                  card(sp.ConditionSet(i, sp.Eq(mileage_i[i], ceiling, evaluate=False), rows_of_file)),
                  evaluate=False),
            sp.Eq(ceiling, 2**16 - 1, evaluate=False))
    formula(sp.Eq(sp.Symbol(r"\mathrm{timestamp\_minus\_utc\_hours}"),
                  sp.ImageSet(sp.Lambda(i, sp.Function(r"\operatorname{round}_{2}")(sp.Add(stamp_i[i], -utc[i], evaluate=False))),
                              rows_of_file), evaluate=False),
            r"\text{in hours, listed in increasing order}")
    ''', slides=["48", "49", "50"])
    explain(
        "Check the three dimensions against the slides, and the three columns with "
        "insufficient metadata.",
        "The uniqueness and validity slides quote archive counts; the Lab 3 check grades "
        "the same counts on the slice. The slide on three columns describes `timestamp`, "
        "`emergency_stop` and `mileage`, and four constant columns.",
        "Compares `profile()`'s counts with the slides, and measures what the slide on the "
        "three columns says.",
        "Uniqueness and the offset agree; the slice has five fewer negative speeds than the "
        "archive and one more constant column (the vehicle identifier, since it holds one "
        "vehicle). Both are printed as the archive's.")
    nb.code('''
    agrees("identical rows (slice; the archive's is also 0)", measurements["uniqueness"]["duplicate_rows"], 0)
    agrees("repeated (vehicle_id, utc_time) keys (slice; archive also 0)",
           measurements["uniqueness"]["duplicate_vehicle_time"], 0)
    beside("rows with speed below zero", f"{measurements['validity']['negative_speed_rows']:,} (slice)",
           f"{archive('negative_speed_rows'):,} (archive)", "the archive holds a second vehicle")
    print(f"  rows with mileage at the ceiling {MILEAGE_CEILING} (slice): "
          f"{measurements['validity']['mileage_at_ceiling']}")
    agrees("timestamp minus utc_time, hours (slice)", measurements["consistency"]["timestamp_minus_utc_hours"], [1.0])
    agrees("distinct values of mileage (slice)", int(bus["mileage"].nunique()), 14)
    agrees("largest mileage (slice)", int(bus["mileage"].max()), 65535)
    agrees("values of emergency_stop (slice)", sorted(bus["emergency_stop"].dropna().unique()),
           ["core_control", "estop_button", "lms_rl", "lms_rr"])
    constant = [c for c in bus.columns if bus[c].nunique(dropna=True) == 1]
    beside("columns holding one value in every row", f"{constant} (slice)",
           f"{archive('constant_columns')} (archive)",
           "the slice holds one vehicle, so vehicle_id is constant too")
    agrees("speed range, metres per second (slice; the archive's is the same)",
           [round(float(bus["speed"].min()), 3), round(float(bus["speed"].max()), 3)], [-3.361, 3.555])
    ''')

    # --- slide 52: completeness figure ----------------------------------------------------------
    nb.md("### Completeness — measured before anything is cleaned\n\n*Slide: \"Completeness — "
          "measured before anything is cleaned\".* The figure is drawn by `make_figs.py`.")
    explain(
        "Bring in the slide's completeness figure function.",
        "The slide's figure is the slice's, drawn by the deck's script.",
        "Copies `figure_completeness()` from `make_figs.py`, verbatim.",
        "The next figure is the deck's, recomputed.")
    nb.source(MAKE_FIGS, "figure_completeness")
    explain(
        "Draw completeness per column, every incomplete column and three complete ones.",
        "Nineteen identical full bars teach nothing; the contrast is the three that are not "
        "full. `emergency_stop` is empty because no emergency stop occurred: the absence is "
        "the measurement.",
        "Runs `figure_completeness()` on the completeness `measure_slice()` computed, and "
        "checks it equals `profile()`'s.",
        "52.574 for `emergency_stop`, on the slice — the number the slide's bar shows.")
    nb.figure("completeness", '''
    figure_completeness(series["completeness"])
    assert series["completeness"].to_dict() == measurements["completeness"]
    agrees("emergency_stop bar, per cent (slice)", 100 * series["completeness"]["emergency_stop"], 52.574, 3)
    ''', slides=["52"], treatment="exact: the slide's own code, on the slice it names")
    nb.md("""
    ### The other four dimensions

    *Slide: "The other four dimensions, and what they say here".* Measure all five
    before cleaning. Is a negative speed invalid, or is the field a signed velocity and
    the vehicle reversing? Without the data dictionary nobody can say — so the rows are
    counted, not dropped.
    """)

    # --- slide 54-55: timeliness -------------------------------------------------------------------
    nb.md("### Definition — timeliness\n\n*Slide: \"Definition — timeliness\".*")
    explain(
        "Write timeliness as the slide defines it.",
        "Timeliness is whether readings arrive when they should: the interval between "
        "consecutive readings once the rows are in time order, within a day [@dama2013; "
        "@pipino2002].",
        "Writes the interval and the two summaries in sympy.",
        "Within a day, because across days the largest gap is the night; one minute as the "
        "threshold; the rows sorted first.")
    nb.equation("timeliness", r'''
    i_ = sp.Symbol("i", integer=True)
    t_ = sp.IndexedBase("t")
    dt_ = sp.IndexedBase(r"\Delta t")
    intervals = NamedSet(r"\{1, \ldots, n - 1\}")
    formula(sp.Eq(dt_[i_], sp.Add(t_[i_ + 1], -t_[i_], evaluate=False), evaluate=False),
            r"\text{rows sorted by utc\_time, within one day}")
    formula(sp.Eq(sp.Symbol(r"\mathrm{median\_interval\_s}"),
                  sp.Function(r"\operatorname{median}")(dt_[1], sp.Symbol(r"\ldots"),
                                                         dt_[sp.Symbol("n", integer=True, positive=True) - 1]),
                  evaluate=False),
            sp.Eq(sp.Symbol(r"\mathrm{gaps\_over\_60s}"), card(sp.ConditionSet(i_, dt_[i_] > 60, intervals)),
                  evaluate=False),
            r"\Delta t \text{ in seconds}")
    ''', slides=["54"])
    explain(
        "Check timeliness against the slides.",
        "The timeliness slides quote a median of 0.5 seconds, ten gaps over a minute and a "
        "longest gap of 876.3 seconds, for the one vehicle within a day.",
        "Compares `profile()`'s timeliness with the slides, and the longest gap with "
        "`make_figs.measure()`'s on the slice.",
        "The slice reproduces all three: they are properties of the one vehicle, and the "
        "slice is that vehicle.")
    nb.code('''
    agrees("median interval, seconds (slice)", measurements["timeliness"]["median_interval_s"], 0.5, 3)
    agrees("intervals over one minute, within a day (slice)", measurements["timeliness"]["gaps_over_60s"], 10)
    agrees("longest interval within a day, seconds (slice)", series["gaps"].max(), 876.3, 1)
    ''')
    explain(
        "Bring in the slide's interval-histogram function.",
        "The slide's figure is drawn by the deck's script.",
        "Copies `figure_gaps()` from `make_figs.py`, verbatim.",
        "The next figure is the deck's, recomputed.")
    nb.source(MAKE_FIGS, "figure_gaps")
    explain(
        "Draw the interval between consecutive readings, on logarithmic scales.",
        "A gap is not a missing value: no row exists, so nothing counts it and nothing warns "
        "you. An average over a window containing the gap is real; the window is not.",
        "Runs `figure_gaps()` on the within-day intervals `measure_slice()` computed.",
        "Twice a second, except ten times; the longest is about a quarter of an hour.")
    nb.figure("sampling_gaps", '''
    figure_gaps(series["gaps"])
    agrees("gaps over one minute in the figure (slice)", int((series["gaps"] > 60).sum()), 10)
    ''', slides=["55"], treatment="exact: the slide's own code, on the slice it names")

    # --- write_profile -------------------------------------------------------------------------------
    nb.md("### Definition — the data dictionary, and the profile you write\n\n*Slide: "
          "\"Metadata — the data dictionary, and the profile you write\".* The profile is the "
          "dictionary's measured counterpart: one line per dimension, `- name: value`, where a "
          "program will find it.")
    explain(
        "Define `write_profile()` as the Lab 3 solution writes it.",
        "The five `- name: value` lines are a contract: the check parses them, so the names "
        "are fixed and the values are measured, never copied.",
        "Copies `write_profile` from `solutions/lab_03.py`, verbatim.",
        "A document a person reads, written by the same code every time.")
    nb.source(f"{S}/lab_03.py", "write_profile", cite="[@riley2017; @gebru2021]")
    explain(
        "Write `DATA_PROFILE.md` for the slice, in the working copy.",
        "The check reads this file, parses the five numbers out of it and compares them "
        "with its own measurement.",
        "Calls `write_profile()` and prints the file it wrote.",
        "Everything in it was measured above; nothing has been repaired.")
    nb.code('''
    text = write_profile(measurements)
    assert PROFILE_PATH.read_text() == text
    print(text)
    empty = 1 - measurements["completeness"]["emergency_stop"]
    beside("share of rows where emergency_stop is empty", f"{100 * empty:.1f} per cent (slice)",
           "\\"empty on most rows\\" (the profile's own wording, from solutions/lab_03.py)",
           f"not most: {100 * empty:.1f} per cent of the slice and "
           f"{100 - archive('completeness_incomplete')['emergency_stop']:.1f} per cent of the archive; "
           "the deck's own phrase, \\"nearly half\\", is the accurate one. A lab text, recorded "
           "here and not changed: the labs are delivered")
    ''')

    nb.md("""
    ### Article 10 of the Artificial Intelligence Act

    *Slide: "Article 10 of the Artificial Intelligence Act — the examination is this
    measurement".* Article 10(3): training, validation and testing data sets shall be
    relevant, sufficiently representative, and to the best extent possible free of
    errors and complete in view of the intended purpose. Article 10(2)(f) requires their
    examination in view of possible biases, and 10(2)(h) the identification of relevant
    data gaps or shortcomings and how they can be addressed [@aiact2024]. The slide
    says Annex III lists "transport infrastructure"; the Annex's words (point 2) are
    "safety components in the management and operation of critical digital
    infrastructure, road traffic, or in the supply of water, gas, heating or
    electricity". The obligations for Annex III systems apply from 2 December 2027,
    under the Digital Omnibus on AI, Regulation (EU) 2026/1744 of 8 July 2026
    [@omnibus2026]. *This is the text of the Regulations, not legal advice.*

    The completeness measured above, the profile declared below and the fitness verdict
    that closes the lab are that examination — written down, dated, and reproducible
    from the data.
    """)

    # --- slide 57: declare / check_against ---------------------------------------------------------------
    nb.md("### Definition — the profile a program can read\n\n*Slide: \"Definition — the "
          "profile a program can read\".* A declaration is a commitment: too tight and "
          "tomorrow's ordinary day is reported broken until nobody believes the alarm; too "
          "loose and nothing can ever violate it.")
    explain(
        "Define `declare_profile()` and `check_against()` as the Lab 3 solution writes them.",
        "The first turns the measurements into rules and writes `out/data_profile.json`, "
        "the contract Module 2 loads (its schema is `HANDOFF.md`). The second applies those "
        "rules to a day, in the order presence → type → range → missing share → step.",
        "Copies both functions from `solutions/lab_03.py`, verbatim.",
        "The margins — five per cent of the observed span, one percentage point of absence — "
        "are the whole design, and they are printed beside the numbers they produce.",
        )
    nb.source(f"{S}/lab_03.py", "declare_profile", "check_against", cite="[@gebru2021; @riley2017]")
    explain(
        "Declare the slice's profile, and test the slice against it.",
        "A declaration that its own data violates is a wish, not a declaration.",
        "Calls `declare_profile()` (which writes `out/data_profile.json` in the working "
        "copy), checks the file equals the returned dictionary, and runs `check_against()` "
        "on the same day.",
        "Silent on the day it was declared from — an empty list is a result, as the next "
        "cells show by breaking the day.")
    nb.code('''
    declaration = declare_profile(bus, measurements)
    assert json.loads(PROFILE_JSON.read_text()) == json.loads(json.dumps(declaration))
    print(f"declared {len(declaration['columns'])} columns, schema {declaration['schema']}, "
          f"expected step {declaration['expected_step_seconds']} s ± {declaration['step_tolerance_share']:.0%}")
    print("speed:", declaration["columns"]["speed"])
    print("payload:", declaration["columns"]["payload"])
    print("check_against() on the day it was declared from:", check_against(bus, declaration))
    ''')
    explain(
        "Draw the slice's data dictionary: for every field, its unit, source, valid range "
        "and owner.",
        "The metadata slide (block one) shows a generated poster; the concept it names is the "
        "document this block has just produced. The four things the slide asks for are the "
        "unit, the source, the valid range and the owner [@riley2017].",
        "Builds a table from the declaration: the type and unit it declares (null where "
        "nobody wrote one down), the range it permits, the absence it tolerates, the source "
        "file — and the owner, which the archive does not record.",
        "Most fields have no unit written down. For text, identifiers and timestamps that is "
        "expected — they need a format, not a unit; but two numeric columns, `payload` and "
        "`mileage`, carry numbers nobody has said how to read (the printed lines list them). "
        "And no field has an owner. The dictionary is honest about both, which is the point "
        "of writing one.")
    nb.figure("data_dictionary", '''
    columns = declaration["columns"]
    rows = [(name, rule["type"], rule["unit"] or "— none written down —",
             "" if rule["minimum"] is None else f"{rule['minimum']:g} to {rule['maximum']:g}",
             f"{rule['max_missing_share']:.4g}") for name, rule in columns.items()]
    table = pd.DataFrame(rows, columns=["field", "type", "unit", "valid range (declared)",
                                        "absence allowed (share)"])
    table["source"] = "bus_slice.csv.gz"
    table["owner"] = "not recorded"
    fig = go.Figure(go.Table(
        columnwidth=[1.4, 0.6, 1.5, 1.9, 1.0, 1.1, 0.9],
        header=dict(values=[f"<b>{c}</b>" for c in table.columns], fill_color=NAVY,
                    font=dict(color="white", size=13), align="left"),
        cells=dict(values=[table[c] for c in table.columns], align="left", font=dict(size=12),
                   fill_color=[["#F4F6FA" if k % 2 else "white" for k in range(len(table))]]
                   * len(table.columns))))
    fig.update_layout(title="The slice's data dictionary — unit, source, valid range, owner "
                            "(declared by Lab 3's declare_profile())", margin=dict(l=20, r=20, t=60, b=10))
    show(fig, "data_dictionary", width=1150, height=640)
    no_unit = [n for n, r in columns.items() if r["unit"] is None]
    print(f"fields with no unit written down ({len(no_unit)} of {len(columns)}):", no_unit)
    print("of those, numeric:", [n for n in no_unit if pd.api.types.is_numeric_dtype(bus[n])])
    ''', slides=["8"], treatment="lab data: the slide's generated metadata poster replaced by the "
                                 "slice's data dictionary, from Lab 3's declaration")

    explain(
        "Let the check's own fixtures be defined here: first, the check harness they import.",
        "`verify/check_03.py` builds a seeded corruption of the day and five invented days "
        "for the verdict, and imports `run`, `close`, `explain` and `grade_reason` from "
        "`verify/_harness.py`. The fixtures are the synthetic data this lab is graded on.",
        "Points `__file__` at `verify/_harness.py` in the working copy, so the harness's "
        "`REPOSITORY` is the working copy.",
        "The next cell copies the harness verbatim.")
    nb.code('''
    __file__ = str(Path.cwd() / "verify" / "_harness.py")
    ''')
    explain(
        "Define the harness functions the check imports, verbatim.",
        "`grade_reason()` is how the check grades a verdict's argument: every number in the "
        "reason must be one the student measured, and at least two quantities must be named. "
        "It belongs on the page as much as the verdict does.",
        "Copies `crashed_in`, `load`, `run`, `close`, `attempts`, `explain`, `numbers_in` "
        "and `grade_reason` with the constants they read, from `verify/_harness.py`; then "
        "registers them as the stand-in `_harness`. The colour constants the terminal "
        "report uses are not copied (they would replace this notebook's palette), and "
        "`run()` is never called here.",
        "The check's grading code, runnable in this notebook.")
    nb.source(HARNESS, "REPOSITORY", "crashed_in", "load", "run", "close", "_ATTEMPTS", "_NUMBER",
              "attempts", "explain", "numbers_in", "grade_reason")
    explain(
        "Register the harness as a stand-in module.",
        "`check_03.py` imports it by name.",
        "Registers `_harness` with the functions defined in the previous cell.",
        "The check's import line, in the next cell, runs unchanged.")
    nb.code('''
    module("_harness", run=run, close=close, explain=explain, grade_reason=grade_reason,
           numbers_in=numbers_in, attempts=attempts)
    print("stand-in registered: _harness")
    ''')
    explain(
        "Define the check's corruption and its five days, verbatim.",
        "The corruption breaks five declared rules the same way on every machine (seed "
        "20200122). The five days are dictionaries, not files: a verdict is a judgement "
        "about evidence, and the evidence is five numbers. One day is at least as good as "
        "every other, one at least as bad, and the three between are pairwise "
        "incomparable — defensible either way.",
        "Copies `SEED`, `FIXTURES`, `BEST`, `WORST` and `corrupt` from "
        "`verify/check_03.py`, verbatim.",
        "The data the check lands on a student's declaration and verdict.")
    nb.source(CHECK_3, "SEED", "FIXTURES", "BEST", "WORST", "corrupt")
    explain(
        "Land the check's corruption on the declaration.",
        "\"Returns nothing\" is only a result if the same function speaks when the day is "
        "broken.",
        "Builds the corrupted day with `corrupt()` and prints every line `check_against()` "
        "returns for it.",
        "Five rules broken, five lines, each beginning with the field it concerns — the "
        "missing column, the text in a numeric column, 500 impossible speeds, a column "
        "absent three rows in five, and a tripled sampling step.")
    nb.code('''
    broken = corrupt(bus)
    complaints = check_against(broken, declaration)
    for complaint in complaints:
        print(" -", complaint)
    agrees("breaches found on the check's corruption (at least 5)", len(complaints) >= 5, True,
           expected_from="check_03")
    ''')

    # --- slides 58-59: the verdict ---------------------------------------------------------------------
    nb.md("""
    ### Where the line goes, and the fitness verdict

    *Slides: "Where the line goes, and what a caveat can and cannot repair" and
    "Definition — the fitness verdict".* Quality is fitness for use, so the verdict is
    the measurement that matters and the five dimensions are only its evidence
    [@wang1996; @batini2009]. Three of the five quantities a caveat repairs, because each
    names an operation or a window: sort the rows, exclude the window around the long
    gap, widen every interval to the effective number of independent readings. Two no
    caveat repairs: an absent column has no subset of the day in which it is present, and
    rows outside the declared range cannot be dropped without knowing which rows they are.
    """)
    explain(
        "Write the verdict rule the reference solution applies.",
        "The slide states the constraints every student's verdict must satisfy; the "
        "reference solution's rule is one way to satisfy them.",
        "Writes the call as a sympy piecewise function of the set B of breached quantities "
        "and the set F of those no caveat repairs; B as the quantities of Q whose measured "
        "value v(q) is on the wrong side of their limit ℓ(q) — below it for the set H where "
        "higher is better, above it otherwise; and Q, H and F built from the solution's own "
        "constants `EVIDENCE_KEYS`, `HIGHER_IS_BETTER` and `NO_CAVEAT_REPAIRS_IT`.",
        "Nothing breached: use. A fatal quantity breached: do not use. Anything else: use "
        "with the breach written down as a condition.")
    nb.equation("fitness_verdict", r'''
    Q, H, B, F = (NamedSet(name) for name in "QHBF")
    call = sp.Piecewise((sp.Symbol(r"\text{use}"), sp.Eq(card(B), 0)),
                        (sp.Symbol(r"\text{do not use}"), sp.Ne(sp.Intersection(B, F, evaluate=False), sp.EmptySet)),
                        (sp.Symbol(r"\text{use with a caveat}"), True))
    formula(sp.Eq(sp.Symbol(r"\mathrm{call}"), call, evaluate=False))
    q, value, limit = sp.Symbol("q"), sp.Function("v"), sp.Function(r"\ell")
    breached = sp.Or(sp.And(sp.Contains(q, H), value(q) < limit(q)),
                     sp.And(sp.Contains(q, sp.Complement(Q, H, evaluate=False)), value(q) > limit(q)))
    formula(sp.Eq(B, sp.ConditionSet(q, breached, Q), evaluate=False),
            r"v(q) \text{ measured on the day, } \ell(q) \text{ from FITNESS\_LIMITS}")
    named = lambda keys: sp.FiniteSet(*(sp.Symbol(r"\mathrm{" + key.replace("_", r"\_") + "}") for key in keys))
    formula(sp.Eq(Q, named(EVIDENCE_KEYS), evaluate=False))
    formula(sp.Eq(H, named(HIGHER_IS_BETTER), evaluate=False), sp.Eq(F, named(NO_CAVEAT_REPAIRS_IT), evaluate=False))
    ''', slides=["59"])
    explain(
        "Define the verdict and the evidence it reads, as the Lab 3 solution writes them.",
        "`fitness_verdict()` is the only place in the module where the check does not know "
        "the answer. `evidence_from()` is given to the student; its two decisions change "
        "the answer and are stated in its docstring.",
        "Copies `fitness_verdict`, its three helpers, `evidence_from` and "
        "`_lag_one_autocorrelation` from `solutions/lab_03.py`, verbatim.",
        "Every number the reason quotes is one of the numbers it was handed.")
    nb.source(f"{S}/lab_03.py", "fitness_verdict", "_breaches", "_tightest", "_g", "evidence_from",
              "_lag_one_autocorrelation", cite="[@wang1996; @batini2009; @bayley1946]")
    explain(
        "Judge the slice, and check the verdict against the slide.",
        "The slide says the slice is worth 73 independent readings out of 48,290, that 23.1 "
        "per cent of its pairs step backwards, and that its verdict is \"use with a caveat\".",
        "Computes the evidence from the slice and its declaration, and calls "
        "`fitness_verdict()`.",
        "Three quantities outside the boundary, all three repairable — so the day goes "
        "forward with the caveat Module 2 needs: sort it, exclude the long gap, do not treat "
        "48,290 rows as 48,290 observations.")
    nb.code('''
    evidence = evidence_from(bus, measurements, declaration)
    call, reason = fitness_verdict(evidence)
    print(json.dumps(evidence, indent=1))
    agrees("effective sample size in the evidence (slice)", evidence["effective_sample_size"], 73, 0)
    agrees("backward-step share, per cent (slice)", 100 * evidence["backward_step_share"], 23.1, 1)
    agrees("the verdict on the slice", call, "use with a caveat")
    print("\\nbecause:", reason)
    ''')
    explain(
        "Judge the check's five days, and grade each reason the way the check does.",
        "The check holds no threshold of its own. It grades that the verdicts obey the "
        "declared boundary and each other, and that every number in each reason is one of "
        "the day's measurements or limits.",
        "Calls `fitness_verdict()` on each of the five `FIXTURES`, runs the harness's "
        "`grade_reason()` on each reason with the evidence and the limits, and tabulates "
        "the calls.",
        "The clean day is used, the ruined day refused, and the three incomparable days "
        "get the call this boundary gives them — each with a reason built from its own "
        "numbers.")
    nb.code('''
    rows = []
    for name, day in FIXTURES.items():
        day_call, day_reason = fitness_verdict(dict(day))
        grade_reason(day_reason, {**day, **{f"limit_{k}": float(v) for k, v in FITNESS_LIMITS.items()}},
                     key=f"notebook:{name}", minimum_keys=2)
        rows.append((name, day_call, [key for key in EVIDENCE_KEYS if _breaches(key, day[key])]))
    verdicts = pd.DataFrame(rows, columns=["day", "call", "outside FITNESS_LIMITS"])
    agrees("the best day's call", verdicts.set_index("day").loc[BEST, "call"], "use")
    agrees("the worst day's call", verdicts.set_index("day").loc[WORST, "call"], "do not use")
    verdicts
    ''')
    nb.md("""
    ### So what kind of data is this?

    *Slide: "So what kind of data is this?"* Not independent draws, as block one
    measured. A time series, strongly. A panel too, unevenly: on the archive both
    shuttles ran on day one and one on day two — a fact of the archive that the
    one-vehicle slice cannot show — and pooling the fleet by day then measures a change
    of fleet, not of world; a difference can even reverse when unequal groups are pooled
    [@simpson1951]. Spatial and spatio-temporal, though within 86 metres everything is
    nearly everywhere (the route figure in block one). The regime decides which methods
    are admissible; choose it deliberately and write it down.
    """)

    # --- the laboratory ----------------------------------------------------------------------------
    nb.md("""
    ## Laboratory 3 — Profile the day

    *Slide: "Lab 3 — Profile the day".* Five functions, in order: `profile`,
    `write_profile`, `declare_profile`, `check_against`, `fitness_verdict`. No cleaning.
    Measurement, declaration, and a judgement you would defend to somebody who was not in
    the room. Twenty-five minutes.
    """)
    nb.statement(f"{LABS}/03_profile_the_day.py")
    explain(
        "Run the stub's `__main__` block against the solved functions.",
        "It is what a student sees when the file is complete.",
        "The lines below are the stub's demonstration, verbatim.",
        "The four dimensions, the profile document, the declaration, the silence on its own "
        "day, the evidence and the verdict.")
    nb.step(f"{LABS}/03_profile_the_day.py", 0)
    explain(
        "Make the solution's demonstration believe it is running from its own file.",
        "The harness cells above pointed `__file__` at `verify/`; the solution's "
        "demonstration puts the folder above its own file on the import path.",
        "Points `__file__` back at `solutions/lab_03.py` in the working copy.",
        "The demonstration below runs unchanged.")
    nb.code('''
    __file__ = str(Path.cwd() / "solutions" / "lab_03.py")
    ''')
    explain(
        "Run the solution's demonstration, verbatim.",
        "It narrates the five dimensions as it measures them, writes both profiles, lands a "
        "broken copy on the declaration, returns the verdict, and draws three figures from "
        "its own profile.",
        "The lines below are the solution's `__main__` block, unchanged.",
        "The headroom figure shows how far each quantity sits from the boundary, in units of "
        "the boundary: three outside, two inside.")
    nb.step(f"{S}/lab_03.py", 0)
