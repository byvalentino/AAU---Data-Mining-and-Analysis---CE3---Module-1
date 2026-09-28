"""Block two — where data comes from, and what you may take; Laboratory 2."""

S = "Module 1/exercises/solutions"
LABS = "Module 1/exercises/labs"
PROVIDER = "Module 1/exercises/mock/provider.py"


def build(nb, explain) -> None:
    nb.md("""
    ---
    # Block two — Where data comes from, and what you may take

    *Slides 34–42.*

    ### Four ways to get data, and who is not in your data

    *Slides: "Four ways to get data, and what each costs" and "Sampling, and who is
    not in your data".* Primary or secondary, manual or automated — and this case is all
    four at once: sensors on the vehicles, phones carried by people, beacons in the
    environment, researchers with clipboards. The sixteen volunteers are a convenience
    sample: people willing to carry a research phone for two days in January. Who is
    missing — people without smartphones, people who declined, children — is sampling
    and selection bias, and it is not fixable downstream. It is only ever declarable.
    """)

    # --- slide 36: sampling rate -----------------------------------------------------------
    nb.md("""
    ### Person-to-device, device-to-device, and the battery

    *Slide: "Person-to-device, device-to-device, and the battery".* Every continuous
    sensing decision is a battery decision: position once a second empties a phone in
    hours; once a minute misses a stop entirely. The vehicle is plugged in and reports at
    a median of half a second. The slide's diagram is icons and an architecture drawing
    of the survey application; its claim about the sampling rate can be measured on the
    slice.
    """)
    explain(
        "Measure what sampling once a minute would miss, on the shuttle's own stops.",
        "The slide says that sampling once a minute \"misses a stop entirely\". The slice "
        "records speed twice a second, so every stop is in it — and so is what a slower "
        "sampler would have seen.",
        "Puts the slice in time order, finds every stretch at zero speed within a day, keeps "
        "the short stops (5 to 60 seconds), and keeps one reading per clock minute — what a "
        "sampler at one reading a minute would have recorded. A stop is seen if any kept "
        "reading falls inside it. The figure shows the twenty minutes with the most short "
        "stops.",
        "At the vehicle's own rate every stop is there. At one reading a minute, two in "
        "three of the short stops never appear in the data — and nothing in the thinner "
        "file would say so.")
    nb.figure("sampling_rate", '''
    in_order = in_time_order(bus)
    when = pd.to_datetime(in_order["utc_time"])
    day_of = when.dt.date
    still = in_order["speed"].eq(0)
    stretch = ((still != still.shift()) | (day_of != day_of.shift())).cumsum()
    stops = when[still].groupby(stretch[still]).agg(["min", "max"])
    stops["seconds"] = (stops["max"] - stops["min"]).dt.total_seconds()
    short = stops[(stops["seconds"] >= 5) & (stops["seconds"] < 60)]
    once_a_minute = in_order.groupby(when.dt.floor("60s")).head(1).index
    seen_by_minute = set(stretch[once_a_minute][still[once_a_minute]])
    short = short.assign(seen=short.index.isin(seen_by_minute))
    counts = [((short["min"] >= s) & (short["min"] < s + pd.Timedelta("20min"))).sum() for s in short["min"]]
    begin = short["min"].iloc[int(np.argmax(counts))]
    window = (when >= begin) & (when < begin + pd.Timedelta("20min"))
    sampled = [i for i in once_a_minute if window[i]]
    fig = go.Figure()
    for _, stop in short[(short["min"] >= begin) & (short["min"] < begin + pd.Timedelta("20min"))].iterrows():
        fig.add_vrect(x0=stop["min"], x1=stop["max"], line_width=0, opacity=0.25,
                      fillcolor=GREEN if stop["seen"] else RED)
    fig.add_scatter(x=when[window], y=in_order.loc[window, "speed"], mode="lines",
                    line=dict(color=GREY, width=1), name="twice a second (the vehicle's rate)")
    fig.add_scatter(x=when[sampled], y=in_order.loc[sampled, "speed"], mode="lines+markers",
                    line=dict(color=ORANGE, width=2), marker=dict(size=9),
                    name="once a minute")
    fig.update_layout(title="What a slower sampler sees: short stops seen (green) and missed (red) "
                            "at one reading a minute",
                      xaxis_title="time (UTC)", yaxis_title="speed (m/s)",
                      legend=dict(orientation="h", y=-0.2))
    show(fig, "sampling_rate", height=460)
    print(f"stops of 5 to 60 seconds within a day: {len(short)}; seen at one reading a minute: "
          f"{int(short['seen'].sum())}; missed: {int((~short['seen']).sum())} "
          f"({100 * (~short['seen']).mean():.0f} per cent)")
    agrees("median interval between readings, seconds (slice)", on_the_slice["median_interval_s"]["value"], 0.5, 1)
    ''', slides=["36"], treatment="lab data: the slide's claim about the sampling rate measured "
                                  "on the slice's stops")
    explain(
        "Redraw the slide's architecture diagram of the survey application — illustrative.",
        "The slide's claim is that sensing is a battery decision. Its diagram shows where "
        "that decision lives: battery optimisation appears twice, once in the application "
        "and once in the phone's operating system, beside the sensors that spend the "
        "battery. The diagram carries a concept and no data, so it is redrawn as boxes and "
        "labels, credited as the slide credits it: {@thesis}.",
        "Draws the client application's four components (A.1–A.4) above the operating "
        "system's five (OS.1–OS.5, the hardware listing the sensors), the server application "
        "with its two components (B.1–B.2) and the external geographic data, with the "
        "arrows the slide draws between them. The two battery-optimisation boxes are "
        "coloured orange; nothing else is emphasised.",
        "The phone's battery is managed in two places that the survey's designer controls "
        "only one of — the reason the sampling rate is a design decision, not a detail. The "
        "boxes are the slide's, the colours this notebook's.")
    nb.figure("survey_app_architecture", '''
    fig = go.Figure()


    def box(x0, y0, x1, y1, text, fill="#F4F6FA", line=NAVY, size=13, colour=NAVY):
        """One labelled rectangle of the diagram."""
        fig.add_shape(type="rect", x0=x0, y0=y0, x1=x1, y1=y1, fillcolor=fill, line=dict(color=line, width=2),
                      layer="below")
        fig.add_annotation(x=(x0 + x1) / 2, y=(y0 + y1) / 2, text=text, showarrow=False,
                           font=dict(size=size, color=colour), align="center")


    def link(x0, y0, x1, y1):
        """A two-headed arrow, as the slide draws every connection."""
        for (xa, ya), (xb, yb) in (((x0, y0), (x1, y1)), ((x1, y1), (x0, y0))):
            fig.add_annotation(x=xb, y=yb, ax=xa, ay=ya, xref="x", yref="y", axref="x", ayref="y",
                               showarrow=True, arrowhead=2, arrowsize=1.2, arrowwidth=2, arrowcolor=GREY, text="")


    box(0, 0, 12.4, 12, "", fill="#FAFAFA", line=GREY)
    fig.add_annotation(x=6.2, y=11.5, text="<b>A — CLIENT APPLICATION</b> (the phone)", showarrow=False,
                       font=dict(size=16, color=NAVY))
    for k, (name, fill) in enumerate((("A.1 Human<br>interaction", "#F4F6FA"),
                                      ("A.2 Machine<br>intelligence", "#F4F6FA"),
                                      ("A.3 Data<br>management", "#F4F6FA"),
                                      ("A.4 Battery<br>optimisation", "#FBE3D3"))):
        box(0.3 + 3.0 * k, 9.2, 3.1 + 3.0 * k, 10.8, f"<b>{name}</b>", fill=fill)
        link(1.7 + 3.0 * k, 9.2, 1.7 + 3.0 * k, 8.1)
    box(0.3, 0.4, 12.1, 8.0, "", fill="#EEF0F4", line=GREY)
    fig.add_annotation(x=6.2, y=7.6, text="<b>OS</b> — the phone's operating system", showarrow=False,
                       font=dict(size=14, color=NAVY))
    box(0.6, 5.3, 5.9, 7.0, "<b>OS.1</b> Location service")
    box(6.5, 5.3, 11.8, 7.0, "<b>OS.2</b> Other accessible services")
    box(0.6, 1.9, 3.2, 4.9, "<b>OS.4</b> Battery<br>optimisation", fill="#FBE3D3")
    box(3.4, 1.9, 11.8, 4.9, "<b>OS.5</b> Hardware<br>AGPS · accelerometer · gyroscope · magnetometer<br>"
                               "CPU · GPU · WiFi/4G")
    box(0.6, 0.6, 11.8, 1.6, "<b>OS.3</b> Network service")
    box(13.6, 4.2, 20, 12, "", fill="#FAFAFA", line=GREY)
    fig.add_annotation(x=16.8, y=11.4, text="<b>B — SERVER APPLICATION</b><br>(RESTful API)", showarrow=False,
                       font=dict(size=15, color=NAVY))
    box(13.9, 6.4, 16.7, 10.4, "<b>B.1 Machine<br>intelligence</b><br><br>mode detection<br>"
                               "purpose imputation<br>map-matching")
    box(16.9, 6.4, 19.7, 10.4, "<b>B.2 Big data</b><br><br>INS · GPS<br>survey answers<br>personal info")
    box(13.6, 0.4, 20, 2.0, "<b>EXTERNAL DATA (GIS)</b>", fill="#E6F2EA", line=GREEN)
    link(12.1, 3.4, 13.6, 5.4)        # the phone and the server
    link(16.8, 4.2, 16.8, 2.0)        # the server and the external data
    link(12.1, 1.2, 13.6, 1.2)        # the phone and the external data
    fig.update_xaxes(visible=False, range=[-0.2, 20.2])
    fig.update_yaxes(visible=False, range=[-0.2, 12.2])
    fig.update_layout(title="Illustrative: the survey application's architecture, redrawn from the slide<br>"
                            "<sup>battery optimisation (orange) sits in the app and in the operating system</sup>",
                      margin=dict(l=20, r=20, t=80, b=20))
    show(fig, "survey_app_architecture", width=1100, height=640)
    ''', slides=["36"], treatment="illustrative: the slide's architecture diagram redrawn as boxes and "
                                  "labels; no data")

    nb.md("""
    ### Taking data through an interface — five things that go wrong

    *Slide: "Taking data through an interface — five things that go wrong".* The
    endpoint, authentication, pagination (stop early and you silently have partial data;
    a pointer can step backwards and a page arrives twice), rate limits (status 429 and a
    wait time) and errors (a 500 is temporary and retried; a 404 is permanent and is not)
    [@rfc9110; @rfc6585]. The honest test of a collector is not whether it works, but
    whether it is correct when the far end misbehaves.

    Lab 2 does not call a real interface. It calls a provider that runs inside the lab's
    own process and misbehaves on purpose, on a fixed seed. That provider is the next
    cell, in full.
    """)
    explain(
        "Define the mock provider Lab 2 collects from.",
        "The provider pages, throttles, fails, refuses, and re-delivers one page per day. "
        "Every lesson of the lab is one of those behaviours, so its code belongs on the page.",
        "Copies the constants, the three exceptions and the `Provider` class from "
        "`mock/provider.py`, verbatim. Everything is seeded, so it fails in the same places "
        "on every run.",
        "700 records a day, delivered as 14 pages of 50, one page of which repeats 20 records "
        "the caller already holds.")
    nb.source(PROVIDER, "PAGE_SIZE", "PAGES_PER_DAY", "RECORDS_PER_DAY", "KNOWN_DAYS", "OVERLAP",
              "Throttled", "ServerBusy", "NoSuchDay", "Provider",
              cite="[@rfc9110; @rfc6585; @kleppmann2017]")
    explain(
        "Let the lab's `from mock.provider import …` find the provider defined above.",
        "The Lab 2 solution imports its provider by module name.",
        "Registers `mock.provider` (and its parent `mock`) as stand-ins holding the objects "
        "of the previous cell.",
        "The solution's import line runs unchanged and binds to the code printed above.")
    nb.code('''
    module("mock.provider", PAGE_SIZE=PAGE_SIZE, PAGES_PER_DAY=PAGES_PER_DAY,
           RECORDS_PER_DAY=RECORDS_PER_DAY, KNOWN_DAYS=KNOWN_DAYS, OVERLAP=OVERLAP,
           Throttled=Throttled, ServerBusy=ServerBusy, NoSuchDay=NoSuchDay, Provider=Provider)
    module("mock", provider=sys.modules["mock.provider"])
    print("stand-ins registered:", [n for n in ("mock", "mock.provider") if n in sys.modules])
    ''')

    nb.md("""
    ### Definition — a correct collector

    *Slide: "Definition — a correct collector".* A collector is correct when it returns
    every record of the day exactly once and in order, stops only when the provider says
    there is no next page, and treats each failure as what it is: wait `retry_after`
    exactly after a 429, repeat a 500 at most five times, never repeat a 404, and remove
    the repeated page by record identifier, first delivery winning — at-least-once
    delivery plus de-duplication [@kleppmann2017, ch. 11].

    ## Laboratory 2 — the solution
    """)
    explain(
        "Define `collect()` as the Lab 2 solution writes it.",
        "It is the one function of Lab 2. Its docstring is the argument: read the error "
        "before deciding what to do about it — three exceptions, three different correct "
        "responses, and a fourth behaviour with no exception to announce it.",
        "Copies `LAB`, `MAX_ATTEMPTS` and `collect` from `solutions/lab_02.py`, verbatim, "
        "with the file's imports (among them the provider's stand-in).",
        "The loop ends when the provider says `next: None`, and only then.")
    nb.source(f"{S}/lab_02.py", "LAB", "MAX_ATTEMPTS", "collect",
              cite="[@rfc9110; @rfc6585; @kleppmann2017]")
    explain(
        "Write what a correct collection must return, and check `collect()` against it.",
        "The slide's formula is a contract with countable consequences: the provider hands "
        "out P pages of s records plus an overlap o, and a correct collector returns P·s "
        "distinct identifiers in order.",
        "Writes the two counts and the de-duplication of the pages in arrival order in "
        "sympy, substitutes the provider's constants, collects "
        "22 January from a fresh provider, and compares.",
        "720 records delivered, 700 returned, every identifier once and in order — and the "
        "wait the provider asked for was honoured.")
    nb.equation("collector", r'''
    P, s, o = sp.symbols("P s o", positive=True, integer=True)
    delivered, returned = P * s + o, P * s
    d = sp.Symbol("d")
    delivered_on, collect_on = sp.Function(r"\mathrm{delivered}")(d), sp.Function(r"\mathrm{collect}")(d)
    page = sp.IndexedBase(r"\mathrm{page}")
    formula(sp.Eq(card(delivered_on), delivered, evaluate=False),
            sp.Eq(card(collect_on), returned, evaluate=False))
    formula(sp.Eq(collect_on, sp.Function(r"\mathrm{dedup}_{\mathrm{id}}")(
                      sp.Tuple(page[0], page[1], sp.Symbol(r"\ldots"))), evaluate=False),
            r"\text{the pages' records in the order they arrived; the first delivery of an id wins}")
    constants = {P: PAGES_PER_DAY, s: PAGE_SIZE, o: OVERLAP}
    provider = Provider()
    collected = collect(provider, "2020-01-22")
    agrees("records the provider handed out", provider.records_delivered, int(delivered.subs(constants)),
           expected_from="P·s + o")
    agrees("records collect() returned", len(collected), int(returned.subs(constants)), expected_from="P·s")
    agrees("every identifier once and in order", [r["id"] for r in collected] == provider.expected_ids("2020-01-22"),
           True, expected_from="check_02")
    agrees("waited when told to", provider.slept_when_told, True, expected_from="check_02")
    ''', slides=["39"])

    # --- slides 116-117: JSON -----------------------------------------------------------------
    nb.md("""
    ### What the provider returns: one JSON object per page

    *Backup slides: "APIs" and "JSON".* JavaScript Object Notation is a text format for
    objects (key–value pairs) and arrays [@rfc8259]. The slide's two pictures annotate a
    JSON document found on the web; the provider's own page carries the same structure.
    """)
    explain(
        "Draw one page of the provider as the JSON document it is, with its parts named.",
        "An interface hands back structure, not a table. Seeing the page as an object that "
        "holds an array of objects is what makes `page[\"records\"]` and `page[\"next\"]` "
        "obvious in the collector's code.",
        "Asks a fresh provider for the first page of 22 January, serialises it with "
        "`json.dumps`, keeps the first two records, and draws the text with keys in blue and "
        "values in orange, with the structure labelled on the right. It then prints one row "
        "of the slice as Lab 4 will land it: one JSON object per line.",
        "The page is one object; `records` is an array of objects; each record is key–value "
        "pairs; `next` is a number, or `null` on the last page. And the slice's row shows a "
        "missing value written as `NaN`, which Python reads back but strict JSON does not "
        "allow [@rfc8259, § 6].")
    nb.figure("json_record", '''
    page = Provider().get("2020-01-22", 0)
    shown = {"records": page["records"][:2], "next": page["next"]}
    text = json.dumps(shown, indent=2)
    lines = text.splitlines()
    lines.insert(len(lines) - 3, f'    … {len(page["records"]) - 2} more objects …')


    def coloured(line):
        """Keys blue, values orange, punctuation grey — plotly's HTML subset; the
        indentation kept as non-breaking spaces so the nesting stays visible."""
        indent, body = len(line) - len(line.lstrip(" ")), line.lstrip(" ")
        if '": ' in body:
            key, value = body.split('": ', 1)
            body = (f'<span style="color:{BLUE}">{key}"</span>: '
                    f'<span style="color:{ORANGE}">{value}</span>')
        else:
            body = f'<span style="color:{GREY}">{body}</span>'
        return "&nbsp;" * indent + body


    fig = go.Figure()
    for row, line in enumerate(lines):
        fig.add_annotation(x=0, y=-row, text=coloured(line), showarrow=False,
                           xanchor="left", font=dict(family="Courier New, monospace", size=17))
    labels = [(0, len(lines) - 1, 0, "the page: one JSON object"),
              (1, len(lines) - 3, 1, "\\"records\\": an array of objects"),
              (2, 6, 4, "one object: key–value pairs"),
              (len(lines) - 2, len(lines) - 2, len(lines) - 2, "\\"next\\": a number, or null on the last page")]
    for column, (top, bottom, row, label) in enumerate(labels):
        x = 0.60 + 0.04 * column
        fig.add_shape(type="line", x0=x, x1=x, y0=-top + 0.3, y1=-bottom - 0.3, line=dict(color=NAVY, width=3))
        fig.add_shape(type="line", x0=x, x1=0.76, y0=-row, y1=-row, line=dict(color=NAVY, width=1, dash="dot"))
        fig.add_annotation(x=0.77, y=-row, text=label, showarrow=False, xanchor="left",
                           font=dict(color=NAVY, size=15))
    fig.update_xaxes(visible=False, range=[-0.02, 1.25])
    fig.update_yaxes(visible=False, range=[-len(lines) - 0.5, 0.8])
    fig.update_layout(title="One page from Lab 2's provider, as JSON — keys in blue, values in orange")
    show(fig, "json_record", width=1100, height=520)
    print("one row of the slice, as land() will write it (one JSON object per line):")
    print(json.dumps(bus.iloc[0].to_dict(), default=str))
    ''', slides=["117"], treatment="lab data: the slide's annotated JSON screenshots replaced by a "
                                   "page of Lab 2's provider")

    # --- the laboratory ------------------------------------------------------------------------
    nb.md("""
    ## Laboratory 2 — Collect the day

    *Slide: "Lab 2 — Collect the day".* One function, twenty-five minutes. Retrieve a
    full day with no record lost and no record twice — the second half is now work,
    because the provider delivers more records than the day holds. The check passes when
    every page is accounted for, retries respect the wait the server asked for, and a
    permanent error is not retried.
    """)
    nb.statement(f"{LABS}/02_collect_the_day.py")
    explain(
        "Run the stub's `__main__` block against the solved `collect()`.",
        "It is what a student sees when the file is complete.",
        "The lines below are the stub's demonstration, verbatim.",
        "700 records in the calls it took, 720 handed out, so 20 were repeats; the wait "
        "honoured; no permanent error retried.")
    nb.step(f"{LABS}/02_collect_the_day.py", 0)
    explain(
        "Run the solution's demonstration, verbatim.",
        "It watches every call the collector makes — without touching `collect()` — and "
        "tabulates the pages, the refusals and the failures in order; then it asks for a day "
        "that does not exist.",
        "The lines below are the solution's `__main__` block, unchanged. Its "
        "`from _narrate import …` resolves to the stand-in, so its figure appears here.",
        "The flat steps in the figure are the refusals and failures, each repeated and "
        "never skipped; the 404 is asked once and let through.")
    nb.step(f"{S}/lab_02.py", 0)

    nb.md("""
    ### Scraping, and the law you are actually bound by

    *Slides: "Scraping, and the four limits on it" and "The law you are actually bound
    by".* Scraping reads pages meant for people and is the method of last resort
    [@boegershausen2022]: it is brittle, `robots.txt` states what the operator asks,
    terms of service may forbid it by contract, and a scraper that degrades a service for
    its users does harm regardless of legality. Prefer an interface: it is a contract; a
    page is not.

    The law: personal data is any information relating to an identified or identifiable
    natural person (Article 4), and processing needs one of six lawful bases, named in
    advance (Article 6) [@gdpr2016]. Research on people also engages the Declaration of
    Helsinki and needs ethics approval before collection. In Denmark the supervisory
    authority is Datatilsynet.

    **Applied here.** The vehicle telemetry identifies nobody, and this notebook uses it
    freely. The phone traces of the same trial are the position records of sixteen
    identifiable people; they are not in this repository and no cell of this notebook
    opens them. In this course they appear only as aggregates, from Module 2 on.
    """)
