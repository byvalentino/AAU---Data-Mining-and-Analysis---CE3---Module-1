"""Block one — what a pipeline is, and what kind of data you have; Laboratory 1."""

S = "Module 1/exercises/solutions"
LABS = "Module 1/exercises/labs"
MAKE_FIGS = "Module 1/slides/make_figs.py"


def build(nb, explain) -> None:
    nb.md("""
    ---
    # Block one — What a pipeline is, and what kind of data you have

    *Slides 4–33.* Data underpin four things — decision making, prediction,
    monitoring and compliance — and every one of them inherits whatever went wrong
    at collection. The block ends with the first measurement of the module: whether
    a reading of the shuttle is an independent draw or nearly a copy of the one
    before it.

    ### Why collect data, and the three kinds of compliance

    *Slides: "Why to collect data?" and "Compliance: 3 examples".* Ethical compliance
    (research on people follows the Declaration of Helsinki), legal and ethical
    scraping (the terms of a site, and in the United States the Computer Fraud and
    Abuse Act, as in hiQ Labs against LinkedIn), and regulatory compliance (the
    General Data Protection Regulation) [@gdpr2016]. The slides' pictures are
    photographs and stock illustrations; they carry no data and are not redrawn
    (`figure_map.json` lists each with its reason). Block two returns to the law.
    """)

    # --- slide 7: what is data -----------------------------------------------------
    nb.md("""
    ### What is data?

    *Slide: "What is data?" — raw facts without context, processed information,
    knowledge, action. The same slide returns eighteen times in the "References and
    Backup Material", once per kind of data it shows.* Of its five pictures three are
    photographs (a till receipt, a cat and a dog, the Ames room) and are not redrawn.
    Two carry a structure that can be drawn from data: a weighted directed graph with
    its adjacency list, and a sound wave. They are drawn below, the second with the
    shuttle's own speed as the signal.
    """)
    explain(
        "Draw the weighted directed graph whose adjacency list is printed on the slide's "
        "picture, from that list.",
        "The slide's point is that one piece of data can be held in several structures. "
        "A graph is structured data: five nodes, seven weighted edges, and the adjacency "
        "list and the adjacency matrix are two exact encodings of the same object.",
        "Types in the adjacency list as the picture prints it — node 1 points to 2 "
        "(weight 5), 4 (4) and 5 (2); node 2 to 3 (6) and 5 (7); node 3 to 5 (10); node 4 "
        "to 5 (8); node 5 to nothing — draws each edge as an arrow with its weight, and "
        "prints the adjacency matrix built from the same list.",
        "The picture, the list and the matrix hold the same seven numbers; which one you "
        "store decides which questions are cheap to ask.")
    nb.figure("weighted_digraph", '''
    adjacency = {1: [(2, 5), (4, 4), (5, 2)], 2: [(3, 6), (5, 7)], 3: [(5, 10)],
                 4: [(5, 8)], 5: []}
    place = {1: (0.1, 0.0), 2: (0.0, 0.55), 3: (0.5, 1.0), 4: (0.8, 0.0), 5: (1.0, 0.55)}
    fig = go.Figure()
    for source, edges in adjacency.items():
        for target, weight in edges:
            (x0, y0), (x1, y1) = place[source], place[target]
            fig.add_annotation(x=x1 - 0.08 * (x1 - x0), y=y1 - 0.08 * (y1 - y0),
                               ax=x0 + 0.08 * (x1 - x0), ay=y0 + 0.08 * (y1 - y0),
                               xref="x", yref="y", axref="x", ayref="y", showarrow=True,
                               arrowhead=3, arrowsize=1.5, arrowwidth=2, arrowcolor=GREY)
            fig.add_annotation(x=(x0 + x1) / 2, y=(y0 + y1) / 2, text=f"<b>{weight}</b>",
                               showarrow=False, font=dict(color=ORANGE, size=18),
                               bgcolor="white")
    fig.add_scatter(x=[p[0] for p in place.values()], y=[p[1] for p in place.values()],
                    mode="markers+text", text=[str(k) for k in place], textposition="middle center",
                    marker=dict(size=46, color=[RED, BLUE, BLUE, BLUE, BLUE]),
                    textfont=dict(color="white", size=20), showlegend=False)
    listing = "<br>".join(f"{k}: {v}" for k, v in adjacency.items())
    fig.add_annotation(x=1.45, y=0.5, text="adjacency list with weights<br><br>" + listing,
                       showarrow=False, align="left", font=dict(family="monospace", size=15))
    fig.update_xaxes(visible=False, range=[-0.15, 1.85])
    fig.update_yaxes(visible=False, range=[-0.15, 1.15])
    fig.update_layout(title="A weighted directed graph and its adjacency list — the same data, "
                            "two structures")
    show(fig, "weighted_digraph", height=460)
    matrix = pd.DataFrame(0, index=list(adjacency), columns=list(adjacency))
    for source, edges in adjacency.items():
        for target, weight in edges:
            matrix.loc[source, target] = weight
    print("the same graph as an adjacency matrix (row = from, column = to, 0 = no edge):")
    print(matrix.to_string())
    ''', slides=["7", "85-102"], treatment="exact: the adjacency list the slide's picture prints")
    explain(
        "Draw the shuttle's speed as a signal, the analogue of the slide's sound wave.",
        "A sound wave is a quantity sampled at a fixed rate and ordered in time. So is "
        "the vehicle telemetry: speed, twice a second, for a whole day. Seeing it as a "
        "signal is the first step to seeing why consecutive readings are not independent.",
        "Puts the slice in time order with a stable sort (the rule of Lab 1, applied here "
        "ahead of the lab so the picture is right) and plots signed speed against local "
        "time for 22 January. It then measures, on both days, the stretches of consecutive "
        "readings below zero: how many, how long the longest lasts, and in which driving "
        "mode (`mode`: auto or manual) the negative readings were taken.",
        "Stretches at zero are the shuttle standing still. The stretches below zero are the "
        "negative speeds the validity slides ask about in block three; the printed line says "
        "how many there are, how long they last and in which mode. Whether they are the "
        "vehicle reversing, only a data dictionary can say — the telemetry cannot.")
    nb.figure("speed_signal", '''
    in_order = bus.assign(_utc=pd.to_datetime(bus["utc_time"])).sort_values(
        "_utc", kind="mergesort")
    day_one = in_order[in_order["_utc"].dt.date.astype(str) == FIRST_DAY]
    local = pd.to_datetime(day_one["local_time"])
    fig = go.Figure(go.Scatter(x=local, y=day_one["speed"], mode="lines",
                               line=dict(color=NAVY, width=1)))
    fig.add_hline(y=0, line=dict(color=GREY, width=1))
    fig.update_layout(title=f"Speed as a signal — vehicle {BOTH_DAYS_VEHICLE}, {FIRST_DAY}, "
                            f"{len(day_one):,} readings, twice a second",
                      xaxis_title="local time (Copenhagen)", yaxis_title="speed (metres per second, signed)")
    show(fig, "speed_signal", height=420)
    print(f"{FIRST_DAY}: {len(day_one):,} readings from {local.min():%H:%M} to {local.max():%H:%M} local time; "
          f"speed from {day_one['speed'].min():.3f} to {day_one['speed'].max():.3f} m/s")
    below = in_order["speed"] < 0
    day_key = in_order["_utc"].dt.date
    run = ((below != below.shift()) | (day_key != day_key.shift())).cumsum()
    run_seconds = in_order[below].groupby(run[below])["_utc"].agg(lambda t: (t.max() - t.min()).total_seconds())
    auto_share = (in_order.loc[below, "mode"] == "auto").mean()
    print(f"both days: {int(below.sum()):,} readings below zero in {len(run_seconds)} stretches, the longest "
          f"{run_seconds.max():.1f} s; {100 * auto_share:.0f} per cent of the negative readings in mode 'auto'")
    ''', slides=["7", "85-102"], treatment="lab data: the slide's sound-wave picture replaced by the "
                                            "slice's speed signal")

    nb.md("""
    ### Metadata, data regimes, the data lifecycle and the layered architecture

    *Slides: "Metadata", "Other data regimes", "Data lifecycle" and "Supporting data
    products on layered data architecture".* Metadata is data about data — units,
    timestamps, source, version — and the rest of this module keeps finding what its
    absence costs [@riley2017]. The metadata slide's picture is a generated poster; its
    concept is drawn in block three as the slice's own data dictionary, because that is
    where Lab 3 measures the ranges the dictionary rests on. The regimes grid, the
    lifecycle diagrams and the bronze–silver–gold diagram are pictures of labels and
    are not redrawn; the slides "So what kind of data is this?" (block three) and
    "Where it lands" (block four) state their content in words, and this notebook
    measures the part the slice can speak to: that it is a time series.
    """)

    # --- slides 12-14: pipeline in series, overbooking ----------------------------------
    nb.md("""
    ### A pipeline is elements in series, and what an early error costs

    *Slides: "A pipeline is elements in series, and that is the whole problem",
    "Overbooking — flight industry" and "What an early error costs — an arithmetic,
    not a warning".* Collect, store, clean, model, serve: an error at any stage reaches
    every stage after it, and nothing downstream can repair a fact recorded wrongly
    upstream — the slide's own argument. The slide credits its conclusion, that the
    expensive failures therefore happen before the model, to {@huyen2022}; the early
    release of that book held in the literature folder does not state it in those words.
    The nearest it comes is a review of 96 failures of a large machine-learning pipeline
    at Google, 60 of them not directly caused by the machine learning, many of those in
    the data pipeline [@huyen2022, ch. 7 of the early release, "Causes of ML System
    Failures"]. The overbooking slide asks the cost of bad-quality data with
    three words and two numbers — *Economy*, *250*, *220*. The notebook reads them as
    250 tickets sold for 220 economy seats (an assumption: the slide does not say which
    number is which) and does the arithmetic the slide's poster only suggests.
    """)
    explain(
        "Write the probability that more passengers turn up than there are seats.",
        "An airline overbooks because some ticket holders do not show. If each of the 250 "
        "holders shows independently with probability p, the number who show is binomial, "
        "and a denied boarding happens when more than 220 show [@wasserman2004, § 2.3].",
        "Builds the binomial tail as a sympy sum and evaluates it exactly at three show-up "
        "rates.",
        "The rate p is not known; it is estimated from past data. The formula is where a "
        "data-quality error turns into a cost.")
    nb.equation("overbooking", r'''
    p, j = sp.symbols("p j", positive=True)
    tickets, seats = 250, 220
    denied = sp.Sum(sp.binomial(tickets, j) * p**j * (1 - p)**(tickets - j), (j, seats + 1, tickets))
    formula(sp.Eq(sp.Function("P")(sp.Symbol(r"\text{denied boarding}")), denied, evaluate=False))
    for rate in ("0.85", "0.88", "0.90"):
        exact = denied.subs(p, sp.Rational(rate)).doit()
        print(f"show-up rate {rate}: P(more than {seats} of {tickets} show) = {float(exact):.3f}")
    ''', slides=["13"])
    explain(
        "Draw the denied-boarding probability against the show-up rate — illustrative.",
        "The slide's picture is a generated poster (eight tickets, six seats, profit). The "
        "concept it carries is that the decision rests on one estimated number, and that "
        "a small error in it moves the risk a great deal.",
        "Evaluates the same tail with `math.comb` for show-up rates from 0.80 to 0.95 and "
        "marks the three rates above.",
        "Believe the show-up rate is 0.85 when it is really 0.90, and a 7.5 per cent risk of "
        "a denied boarding becomes 83 per cent. The error was in the data, not the model.")
    nb.figure("overbooking", '''
    def p_denied(rate, tickets=250, seats=220):
        return sum(math.comb(tickets, k) * rate**k * (1 - rate)**(tickets - k)
                   for k in range(seats + 1, tickets + 1))

    rates = np.round(np.arange(0.80, 0.9501, 0.0025), 4)
    fig = go.Figure(go.Scatter(x=rates, y=[100 * p_denied(r) for r in rates], mode="lines",
                               line=dict(color=NAVY, width=3), name="P(denied boarding)"))
    for rate, colour in ((0.85, BLUE), (0.88, GREY), (0.90, RED)):
        fig.add_scatter(x=[rate], y=[100 * p_denied(rate)], mode="markers+text",
                        marker=dict(size=12, color=colour), text=[f"{100 * p_denied(rate):.1f}%"],
                        textposition="top left", showlegend=False)
    fig.update_layout(title="Illustrative: 250 tickets for 220 seats — the risk of a denied boarding "
                            "rests on one estimated rate",
                      xaxis_title="probability that a ticket holder shows up (estimated from data)",
                      yaxis_title="probability that more than 220 show (per cent)", showlegend=False)
    show(fig, "overbooking", height=440)
    agrees("P(denied) at a show-up rate of 0.85, per cent", 100 * p_denied(0.85), 7.5, 1,
           expected_from="notebook")
    agrees("P(denied) at a show-up rate of 0.90, per cent", 100 * p_denied(0.90), 83.0, 1,
           expected_from="notebook")
    ''', slides=["13"], treatment="illustrative: the slide's numbers 250 and 220 read as tickets "
                                  "and seats; the show-up rates are chosen, not measured")
    nb.md("""
    *Note on the two checks above:* they are labelled *notebook* because the stated
    values are this notebook's own reading of the arithmetic, not numbers the slide
    prints; `agrees()` is used so that the sentence above the figure cannot drift from
    the figure.

    ### Five industries, one shape

    *Slides: "Example 1" to "Example 5" and "Five industries, one shape".* Wind-turbine
    test platforms, trading systems, hospital monitoring, recommendation services and
    city mobility: different domains, the same five stages, and in every one the costly
    failures are upstream of the model. The pictures are photographs, a publication's
    montage of medical images and stock art, and are not redrawn.
    """)

    # --- slide 21: the case ---------------------------------------------------------------
    nb.md("""
    ### The case — two shuttles, sixteen phones, five beacons

    *Slide: "The case — two shuttles, sixteen phones, five beacons".* Two automated
    shuttles ran a fixed loop in Copenhagen on 22 and 23 January 2020, with Bluetooth
    beacons on the two vehicles and at three stops [@servizi2023, Sec. III-D]; sixteen
    volunteers carried instrumented phones, and researchers recorded by hand where each
    person was. The phone traces identify people and are not in this repository. The
    vehicle telemetry identifies nobody.

    The slide says "a fixed loop". The trial's paper describes the set-up more exactly:
    two autonomous vehicles on two distinct routes with three stops, one stop shared by
    the routes together with a segment of the test track, and the vehicles' assignment
    to the routes switched during the experiment for technical reasons [@servizi2023,
    Sec. III-D]. The slide's wording is kept; the paper's may explain the spur west of
    the loop on the route map below — a reading, not a measurement: the telemetry does
    not say which route a reading belongs to.
    """)
    explain(
        "Measure what the slide says about the vehicle file, on the file the labs ship.",
        "The slide describes the archive: 53,155 rows, 22 columns, 2 vehicles. The slice is "
        "one of those two vehicles, so two of the three numbers must differ and the reader "
        "must be told why.",
        "Counts rows, columns and vehicles on the slice, and measures the route's bounding "
        "box with `make_figs.py`'s own recipe (degrees to metres at 111,320 m per degree, "
        "the east–west side scaled by the cosine of the latitude).",
        "The box is the same, 67 by 86 metres: the one shuttle drives the whole loop. The "
        "row and vehicle counts are the archive's, and are printed as such.")
    nb.code('''
    agrees("columns", bus.shape[1], 22)
    beside("rows", f"{len(bus):,} (the slice)", f"{archive('rows'):,} (archive)",
           "the slice holds one of the archive's two vehicles, on both days")
    beside("vehicles", bus["vehicle_id"].nunique(), f"{archive('vehicles')} (archive)",
           f"the slice is vehicle {BOTH_DAYS_VEHICLE}, the one that ran on both days")
    agrees("route bounding box, north-south, metres (slice)", on_the_slice["extent_m"]["value"][0], 67)
    agrees("route bounding box, east-west, metres (slice)", on_the_slice["extent_m"]["value"][1], 86)
    ''')
    explain(
        "Draw the route from the telemetry itself.",
        "The slide shows a sketch of the loop with its three stops. The shuttle's own "
        "positions draw the loop more truthfully, and they show where it stands still.",
        "Converts latitude and longitude to metres east and north of the loop's centre and "
        "draws each day in its own panel — on one panel the second day's points would hide "
        "the first's — with the 67 by 86 metre box of both days. In each panel it marks the "
        "day's three longest dwells: readings at zero speed, pooled on a 3-metre grid, "
        "counted as minutes at half a second each.",
        "The stops A, B and C of the slide are not in the telemetry, so the marks are "
        "dwells, not stops: places where the vehicle stood still, for any reason — a stop, "
        "a wait, a parking place. They are measured rather than drawn by hand, and the "
        "printed table says how many minutes each one is.")
    nb.figure("route_map", '''
    lat0, lon0 = bus["lat"].mean(), bus["lon"].mean()
    east = (bus["lon"] - lon0) * 111_320 * np.cos(np.radians(lat0))
    north = (bus["lat"] - lat0) * 111_320
    days = pd.to_datetime(bus["utc_time"]).dt.date.astype(str)
    both_days = (FIRST_DAY, "2020-01-23")
    fig = make_subplots(rows=1, cols=2, subplot_titles=both_days, horizontal_spacing=0.06)
    dwells = []
    for column, (day, colour) in enumerate(zip(both_days, (BLUE, ORANGE)), start=1):
        chosen = days == day
        fig.add_scatter(x=east[chosen], y=north[chosen], mode="markers", showlegend=False,
                        marker=dict(size=3, color=colour, opacity=0.5), row=1, col=column)
        fig.add_shape(type="rect", x0=east.min(), x1=east.max(), y0=north.min(), y1=north.max(),
                      line=dict(color=GREY, dash="dash"), row=1, col=column)
        still = chosen & (bus["speed"] == 0)
        grid = pd.DataFrame({"e": (east[still] / 3).round() * 3, "n": (north[still] / 3).round() * 3})
        for rank, ((e, n), readings) in enumerate(grid.value_counts().head(3).items(), start=1):
            minutes = readings * 0.5 / 60
            dwells.append((day, rank, e, n, round(minutes, 1)))
            fig.add_scatter(x=[e], y=[n], mode="markers+text", marker=dict(size=14, color=RED, symbol="x"),
                            text=[f"dwell {rank}: {minutes:.0f} min"], showlegend=False,
                            textposition=("top center", "bottom right", "top right")[rank - 1],
                            row=1, col=column)
        fig.update_xaxes(title_text="metres east of the loop's centre", range=[-45, 60],
                         scaleanchor=f"y{'' if column == 1 else column}", scaleratio=1, row=1, col=column)
    fig.update_yaxes(title_text="metres north of the loop's centre", row=1, col=1)
    fig.update_layout(title=f"The loop, drawn by the shuttle — vehicle {BOTH_DAYS_VEHICLE}, one panel per day<br>"
                            f"<sup>the dashed box, both days: {north.max() - north.min():.0f} m north–south by "
                            f"{east.max() - east.min():.0f} m east–west; ✕ = the day's three longest dwells</sup>",
                      margin=dict(l=70, r=30, t=110, b=60))
    show(fig, "route_map", width=1100, height=560)
    print(pd.DataFrame(dwells, columns=["day", "dwell", "metres east", "metres north", "minutes"]).to_string(index=False))
    ''', slides=["21"], treatment="lab data: the route drawn from the slice's positions, one panel per day; "
                                  "the marks are measured dwells, not the slide's stops")

    # --- slide 22: noise --------------------------------------------------------------------
    nb.md("""
    ### Localisation noise

    *Slide: "BLE (and GPS) localization noise".* A phone's position and its Bluetooth
    signal strength are disturbed by a covered antenna, absorption, nearby bodies, the
    phone's orientation, and the beacon's orientation and height (the slide's list; the
    slide credits it to {@thesis}, a work it names without author or year). The phone
    traces are not in this repository, so the phone's noise cannot be measured here.
    What can be measured is the other end: how still the *vehicle's* reported position
    is when the vehicle is still.
    """)
    explain(
        "Measure how much the vehicle's reported position moves while it stands still, and "
        "set an illustrative phone-grade error beside it.",
        "Every distance between a phone and a bus combines two positions. On the vehicle "
        "side the telemetry can say how repeatable the reported position is at a standstill; "
        "on the phone side the slide lists the causes but the data are not ours to open.",
        "Takes the longest stretch at zero speed within one day, counts how many distinct "
        "positions it reports (one would mean a held value), measures how far they scatter "
        "(the 95th-percentile distance from their mean), and draws, around the same point, "
        "circles of radius 2σ for a phone error of σ = 2, 5 and 10 metres — values chosen for "
        "illustration, not measured — with 300 simulated fixes at σ = 5 m (seed 20200122).",
        "The printed line shows the position is not held — the readings differ — yet they "
        "scatter within about a centimetre. That is repeatability at a standstill: it says the "
        "reported position is steady, not that it is accurate to a centimetre, which only a "
        "second instrument could tell. A phone error of a few metres is already a large share "
        "of a loop only 67 by 86 metres across: on this "
        "route, \"near the bus\" and \"on the other side of the loop\" are not far apart.")
    nb.figure("gps_noise", '''
    ordered_utc = pd.to_datetime(bus["utc_time"])
    ordered = bus.assign(_utc=ordered_utc, east=east, north=north).sort_values("_utc", kind="mergesort")
    stopped = ordered["speed"].eq(0)
    day_of = ordered["_utc"].dt.date
    stretch = ((stopped != stopped.shift()) | (day_of != day_of.shift())).cumsum()
    lengths = ordered[stopped].groupby(stretch[stopped])["_utc"].agg(lambda t: (t.max() - t.min()).total_seconds())
    longest = ordered[stopped & (stretch == lengths.idxmax())]
    centre_e, centre_n = longest["east"].mean(), longest["north"].mean()
    jitter = np.hypot(longest["east"] - centre_e, longest["north"] - centre_n)
    rng = np.random.default_rng(20200122)
    fixes = rng.normal(0, 5, size=(300, 2))
    fig = go.Figure()
    fig.add_scatter(x=east, y=north, mode="markers", marker=dict(size=2, color="#BBBBBB"),
                    name="the route (all readings)")
    fig.add_scatter(x=centre_e + fixes[:, 0], y=centre_n + fixes[:, 1], mode="markers",
                    marker=dict(size=5, color=ORANGE, opacity=0.6),
                    name="illustrative phone fixes, σ = 5 m (simulated)")
    for sigma in (2, 5, 10):
        fig.add_shape(type="circle", x0=centre_e - 2 * sigma, x1=centre_e + 2 * sigma,
                      y0=centre_n - 2 * sigma, y1=centre_n + 2 * sigma, line=dict(color=ORANGE, dash="dot"))
    fig.add_scatter(x=longest["east"], y=longest["north"], mode="markers",
                    marker=dict(size=9, color=BLUE), name=f"the shuttle standing still: {len(longest):,} readings")
    fig.update_xaxes(title_text="metres east", scaleanchor="y", scaleratio=1)
    fig.update_yaxes(title_text="metres north")
    fig.update_layout(title="The shuttle standing still (measured) and a phone's fixes (illustrative)",
                      legend=dict(orientation="h", y=-0.15))
    show(fig, "gps_noise", width=900, height=640)
    distinct = len(longest[["lat", "lon"]].drop_duplicates())
    print(f"longest stretch at zero speed: {lengths.max() / 60:.1f} minutes, {len(longest):,} readings, "
          f"{distinct:,} distinct positions; 95 per cent of them lie within "
          f"{100 * jitter.quantile(0.95):.1f} cm of their mean")
    ''', slides=["22"], treatment="lab data for the vehicle's jitter; illustrative for the phone's "
                                  "error (σ chosen, fixes simulated)")

    # --- slide 23: uncertainty -------------------------------------------------------------
    nb.md("""
    ### Uncertainty from positioning and from logging

    *Slide: "Uncertainty: GPS + logging".* The distance between a phone and a bus is
    computed from two positions stamped by two clocks. The slide's rule is
    Δd = ΔGPS + ΔSpeed·ΔT: the positioning error, plus the distance the objects move
    while their timestamps disagree by ΔT. Logging frequency, synchronisation, the
    connection, the device's position and its reception all set ΔT.
    """)
    explain(
        "Write the slide's rule, and put the slice's numbers into it.",
        "The formula says that a timing error is a distance error, in proportion to speed. "
        "The telemetry gives both the speeds and the intervals between readings.",
        "Builds Δd = ΔGPS + ΔS·ΔT in sympy and evaluates the timing term with the shuttle's "
        "95th-percentile moving speed at three values of ΔT: half the median interval, one "
        "minute, and the longest gap within a day. It then computes the diagonal of the "
        "route's bounding box — no two points on this route are further apart, so no "
        "distance between two positions on it can be wrong by more — and the ΔT at which "
        "the timing term reaches it.",
        "Half a reading's interval costs under a metre. ΔS·ΔT is the length of the path "
        "driven while the clocks disagree, not how far the vehicle ends up from where it "
        "was: on a loop the second cannot exceed the box's diagonal, about 109 metres. So "
        "the 2,872 metres printed for the longest gap is not an error in the distance; it "
        "says that past the printed ΔT the error has reached its ceiling and the distance "
        "carries no information at all — which is why the gaps are measured in block three.")
    nb.equation("delta_d", r'''
    d_gps, d_speed, d_time = sp.symbols(r"\Delta_{GPS} \Delta_S \Delta_T", positive=True)
    delta_d = d_gps + d_speed * d_time
    formula(sp.Eq(sp.Symbol(r"\Delta d"), delta_d, evaluate=False))
    moving = bus.loc[bus["speed"].abs() > 0.1, "speed"].abs()
    fast = float(moving.quantile(0.95))
    diagonal = float(np.hypot(east.max() - east.min(), north.max() - north.min()))
    print(f"moving speed on the slice: median {moving.median():.2f} m/s, 95th percentile {fast:.2f} m/s")
    for label, seconds in (("half the median interval", 0.25), ("one minute", 60.0),
                           ("the longest gap within a day", archive("longest_gap_s"))):
        timing = delta_d.subs({d_gps: 0, d_speed: fast, d_time: seconds})
        print(f"  ΔT = {seconds:>6} s ({label}): the timing term alone is {float(timing):8.1f} m "
              f"of path; the distance error it can cause, at most {min(float(timing), diagonal):6.1f} m")
    reach = sp.solve(sp.Eq(delta_d.subs({d_gps: 0, d_speed: fast}), diagonal), d_time)[0]
    print(f"the route's bounding box, diagonal: {diagonal:.1f} m; the timing term reaches it at "
          f"ΔT = {float(reach):.1f} s at {fast:.2f} m/s, and at {diagonal / float(moving.median()):.1f} s "
          f"at the median {moving.median():.2f} m/s")
    ''', slides=["23"])
    explain(
        "Draw the timing term of Δd against ΔT for the shuttle's measured speeds, and the "
        "ceiling the route puts on the error.",
        "The slide's diagram shows two clocks and a gap between their readings; the "
        "consequence is a line whose slope is the speed — until the error reaches the "
        "largest distance the route allows.",
        "Plots ΔS·ΔT for ΔT from 0.01 to 1,000 seconds at the median and the 95th-percentile "
        "moving speed, with the diagonal of the route's bounding box (the largest possible "
        "error between two points on the route) and the slice's median interval, one-minute "
        "threshold and longest gap marked.",
        "Left of where a line meets the diagonal, a timing error is a distance error in "
        "proportion to speed. Right of it, the product is only path length: the distance "
        "between phone and bus is no longer known at all. The positioning error ΔGPS adds "
        "on top.")
    nb.figure("timing_uncertainty", '''
    grid = np.logspace(-2, 3, 200)
    fig = go.Figure()
    for speed, colour, label in ((float(moving.median()), BLUE, "median moving speed"),
                                 (fast, ORANGE, "95th-percentile moving speed")):
        fig.add_scatter(x=grid, y=speed * grid, mode="lines", line=dict(color=colour, width=3),
                        name=f"{label}, {speed:.2f} m/s")
    # Reference lines are drawn as traces: on logarithmic axes they then sit in data units.
    fig.add_scatter(x=[grid[0], grid[-1]], y=[diagonal, diagonal], mode="lines+text",
                    line=dict(color=GREY, dash="dash"), showlegend=False, textposition="top right",
                    text=[f"the route box's diagonal, {diagonal:.0f} m: the largest possible distance error", ""])
    for seconds, text, height in ((0.5, "median interval 0.5 s", 2000), (60, "one minute", 0.02),
                                  (archive("longest_gap_s"), "longest gap within a day", 2000)):
        fig.add_scatter(x=[seconds, seconds], y=[0.005, 4000], mode="lines", line=dict(color=RED, dash="dot"),
                        showlegend=False)
        fig.add_scatter(x=[seconds], y=[height], mode="text", text=[text + " "], textposition="middle left",
                        textfont=dict(color=RED), showlegend=False)
    fig.update_layout(title="Δd from logging alone: the distance moved while two timestamps disagree",
                      xaxis=dict(title="ΔT, seconds (logarithmic)", type="log", range=[-2, 3]),
                      yaxis=dict(title="ΔS·ΔT, metres (logarithmic)", type="log", range=[-2.3, 3.6]),
                      legend=dict(orientation="h", y=-0.2))
    show(fig, "timing_uncertainty", height=480)
    agrees("longest gap within a day, seconds (slice)", on_the_slice["longest_gap_s"]["value"], 876.3, 1)
    ''', slides=["23"], treatment="lab data: the slice's speeds and intervals in the slide's rule")

    # --- slides 24-26 -----------------------------------------------------------------------
    nb.md("""
    ### Ground truth is measured too, and ten flavours of bias

    *Slides: "Ground truth is measured too, so it is not truth", "Is not the truth the
    truth?" and "Ten flavours of bias, named once — then met where they occur".* The
    labels the researchers recorded by hand are themselves measurements with an error;
    the literature calls them acceptable truth rather than ground truth
    [@prelipcean2018], and on this very trial the people's own errors were measured
    [@servizi2023, Sec. IV-A]. A model can be evaluated only as precisely as its labels
    are accurate. The ten flavours — sampling and selection, measurement and labelling,
    missing data, leakage, shift, modelling, evaluation, deployment and fairness,
    feedback loops, time — are each met where they occur; today's are sampling (block
    two) and time (this block). The slides' picture is a press photograph used as a
    meme and is not reproduced.
    """)

    # --- slide 27: the first mess ------------------------------------------------------------
    nb.md("""
    ### The first mess — this file is not in time order

    *Slide: "The first mess — this file is not in time order".*
    """)
    explain(
        "Ask the slice's timestamp one question: does it always increase?",
        "Every computation that depends on order — a lag, a difference, a rolling "
        "window, a split by date — silently answers a different question when the rows "
        "are out of order. Nothing in the file announces it.",
        "Parses `utc_time`, takes the step from each row to the next in the order the file "
        "ships, and counts the steps that go backwards; then the same within one day.",
        "23.1 per cent of consecutive pairs step backwards, by up to 3,102.5 seconds, in a "
        "file that samples twice a second. Every slide number here is the slice's.")
    nb.code('''
    stamp = pd.to_datetime(bus["utc_time"])
    step = stamp.diff().dt.total_seconds().iloc[1:]
    same_day = (stamp.dt.date == stamp.dt.date.shift()).iloc[1:]
    within_day = step[same_day]
    print("utc_time only ever increases:", stamp.is_monotonic_increasing)
    agrees("consecutive row pairs", len(step), 48289)
    agrees("pairs stepping backwards in time", int((step < 0).sum()), 11143)
    agrees("share of pairs stepping backwards, per cent", 100 * (step < 0).mean(), 23.1, 1)
    agrees("largest single step backwards, seconds", step.min(), -3102.5, 1)
    agrees("within a day: smallest step, seconds", within_day.min(), -3102.5, 1)
    agrees("within a day: largest step, seconds", within_day.max(), 4532.5, 1)
    agrees("within a day: median step, seconds", within_day.median(), 0.502, 3)
    ''')

    # --- slide 28: definition r_k -----------------------------------------------------------
    nb.md("""
    ### Definition — lag-k sample autocorrelation

    *Slide: "Definition — lag-k sample autocorrelation".*
    """)
    explain(
        "Write the estimator Lab 1 grades.",
        "The lag-k sample autocorrelation is the summed product of each value's and its "
        "k-places-earlier value's deviation from the one mean, over the summed squared "
        "deviation of all n values [@box2015, § 2.1; @hyndman2021, § 2.8].",
        "Builds the ratio of two sympy sums, with one mean x̄ — itself a sympy sum over all n "
        "values — and one denominator over the whole series.",
        "The next cells check, on real readings, that this expression and the lab's code "
        "compute the same number.")
    nb.equation("autocorrelation_definition", r'''
    x = sp.IndexedBase("x")
    t, k, n = sp.symbols("t k n", integer=True, positive=True)
    x_bar = sp.Symbol(r"\bar{x}")
    r_k = (sp.Sum((x[t] - x_bar) * (x[t - k] - x_bar), (t, k + 1, n))
           / sp.Sum((x[t] - x_bar) ** 2, (t, 1, n)))
    formula(sp.Eq(sp.Symbol("r_k"), r_k, evaluate=False),
            sp.Eq(x_bar, sp.Sum(x[t], (t, 1, n)) / n, evaluate=False))
    ''', slides=["28"])
    nb.md("""
    ## Laboratory 1 — the solution, function by function

    The four functions of Lab 1 are defined where the deck introduces each concept. The
    lab's statement, and its demonstrations, follow at the end of the block.
    """)
    explain(
        "Define `autocorrelation()` as the Lab 1 solution writes it.",
        "It is the first deliverable of Lab 1, and its docstring states the four rules "
        "that make it correct rather than nearly correct: deviations from the mean, one "
        "mean and one denominator, the overlap rule for missing values, and a floor of "
        "thirty pairs below which the answer is not-a-number.",
        "Copies `LAB`, `MINIMUM_PAIRS` and `autocorrelation` from `solutions/lab_01.py`, "
        "verbatim.",
        "The function the check grades to four decimals, on the page.")
    nb.source(f"{S}/lab_01.py", "LAB", "MINIMUM_PAIRS", "autocorrelation",
              cite="[@box2015; @hyndman2021]")
    explain(
        "Check that the slide's formula and the lab's function are the same computation.",
        "A formula and its code can drift apart without anyone noticing; evaluating both "
        "on the same numbers is cheap.",
        "Takes the first block of 60 consecutive speed readings of the slice, as shipped, in "
        "which speed varies (a block of a standing shuttle is all zeros and has no "
        "correlation to compute), evaluates the sympy expression exactly in rational "
        "arithmetic at lags 1 and 5, and compares with `autocorrelation()`.",
        "They agree to twelve decimals; the definition card, the stub and the solution "
        "describe one estimator.")
    nb.code('''
    start = next(i for i in range(0, len(bus), 60) if bus["speed"].iloc[i:i + 60].std() > 0.5)
    block = bus["speed"].iloc[start:start + 60].reset_index(drop=True)
    readings = [sp.Rational(str(v)) for v in block]
    mean = sum(readings) / len(readings)
    for lag in (1, 5):
        exact = r_k.subs({n: len(readings), k: lag, x_bar: mean}).doit()
        exact = exact.subs({x[i + 1]: value for i, value in enumerate(readings)})
        code = autocorrelation(block, lag)
        print(f"rows {start}-{start + 59}, lag {lag}: the slide's formula {float(exact):.12f}   "
              f"autocorrelation() {code:.12f}")
        assert abs(float(exact) - code) < 1e-12
    ''')

    # --- slide 29: monotone rule ---------------------------------------------------------------
    nb.md("""
    ### Definition — the monotone-timestamp rule

    *Slide: "The Monotone-Timestamp Rule".* A row shift equals a time shift only when the
    rows are in strict chronological order, so sort by the parsed timestamp before any
    lag, difference, rolling window or split, and report the lag-one autocorrelation
    both ways.
    """)
    explain(
        "Define `in_time_order()` and `lag_one_both_ways()` as the Lab 1 solution writes them.",
        "Sorting is one line; the three choices that make it a measurement are a stable "
        "sort (rows sharing an instant keep their arrival order on every machine), a reset "
        "index, and leaving the caller's frame untouched.",
        "Copies both functions from `solutions/lab_01.py`, verbatim.",
        "The pair of numbers the next cell prints is the finding of Lab 1.")
    nb.source(f"{S}/lab_01.py", "in_time_order", "lag_one_both_ways", cite="[@box2015]")
    explain(
        "Measure the lag-one autocorrelation of speed twice on the same rows.",
        "One of the two numbers describes the vehicle; the other describes the order "
        "somebody wrote the rows in. Only the timestamp says which.",
        "Calls `lag_one_both_ways()` on the slice as it ships, checks that "
        "`in_time_order()` left the shipped frame alone, and compares with the numbers the "
        "deck prints.",
        "0.9608 as shipped, 0.9970 in time order. The disorder pushes the number down — "
        "towards what independent draws would look like, the direction that gets believed.")
    nb.code('''
    before = bus.copy()
    both = lag_one_both_ways(bus)
    assert bus.equals(before), "in_time_order() must not change the frame it was given"
    agrees("lag-1 autocorrelation of speed, as shipped (slice)", both["as_shipped"], 0.9608, 4)
    agrees("lag-1 autocorrelation of speed, in time order (slice)", both["in_time_order"], 0.997, 3)
    beside("the dataset the monotone-timestamp slide names", "the slice, 23.1 per cent of pairs "
           "out of order", "\\"Data Challenge (bus.csv)\\", 23.1%",
           "the 23.1 per cent is measured on exercises/data/bus_slice.csv.gz, not on the "
           "archive's bus file; measured.json files it under slice_backward_share_pct")
    ''')

    # --- slide 31: independent draw -------------------------------------------------------------
    nb.md("""
    ### Is a reading an independent draw, or nearly a copy?

    *Slide: "Is a reading an independent draw, or nearly a copy?"* Independent and
    identically distributed means each record is drawn afresh, unaffected by the last,
    from one distribution [@casella2002; @wasserman2004, Definition 2.41]. The slide's
    figure is drawn by `slides/make_figs.py`; the next cells run that script's own
    functions on the slice.
    """)
    explain(
        "Bring in the slide's figure function.",
        "The surest way to reproduce the slide's figure is to run the function that drew it.",
        "Copies `figure_autocorrelation()` from `make_figs.py`, verbatim; it draws through "
        "the notebook's `write_figure` defined in the set-up.",
        "The next figure is the deck's, recomputed.")
    nb.source(MAKE_FIGS, "figure_autocorrelation")
    explain(
        "Draw the autocorrelation of speed in three orders: sorted, as shipped, shuffled.",
        "Only the sorted line is a function of time. The shuffled line is the control: it "
        "shows what independence looks like, so the measurement is known to work.",
        "Runs `measure_slice()` (the deck's slice measurements) and "
        "`figure_autocorrelation()` on its series, then checks the deck's numbers — the "
        "figure's lag-one labels from the whole slice, and the text's day-one numbers from "
        "`measure()`, which restricts to 22 January.",
        "At lag one the sorted readings correlate at 0.997: a reading is almost its "
        "predecessor.")
    nb.figure("autocorrelation", '''
    slice_facts, series = measure_slice()
    figure_autocorrelation(series)
    agrees("figure label, lag 1, rows sorted by utc_time (whole slice)",
           slice_facts["slice_speed_autocorrelation_lag1"]["value"]["time_sorted"], 0.9970, 4)
    agrees("figure label, lag 1, rows as the file ships (whole slice)",
           slice_facts["slice_speed_autocorrelation_lag1"]["value"]["as_shipped"], 0.9608, 4)
    agrees("text: speed, lag 1, sorted, 22 January", on_the_slice["speed_autocorrelation_lag1"]["value"], 0.9967, 4)
    agrees("text: payload, lag 1, sorted, 22 January", on_the_slice["payload_autocorrelation_lag1"]["value"], 0.9981, 4)
    agrees("text: speed shuffled with seed 0, lag 1, 22 January",
           on_the_slice["shuffled_autocorrelation_lag1"]["value"], -0.0008, 4)
    beside("lag-1 autocorrelation of speed in time order", "0.9970 in the figure (both days)",
           "0.9967 in the text", "the text's numbers are 22 January only (make_figs.measure); the "
           "figure's are the whole slice (make_figs.measure_slice). Both are right; the slide does "
           "not say that they differ in scope")
    ''', slides=["31"], treatment="exact: the slide's own code, on the slice it names")
    explain(
        "Derive the effective sample size rather than quote it.",
        "The slide says 48,290 rows are worth about 73 independent draws. The factor "
        "(1 − ρ)/(1 + ρ) comes from the variance of a mean of correlated readings "
        "[@bayley1946]: for a series whose correlation at lag h is ρ^h the variance of the "
        "mean is (σ²/n) (1 + 2 Σ ρ^h) for large n, and the effective sample is the size of an "
        "independent sample with the same variance.",
        "Sums the geometric series in sympy, simplifies, and evaluates at ρ = 0.9970 and "
        "n = 48,290.",
        "73 draws' worth of evidence about the mean speed, from 48,290 rows. That is the "
        "number the fitness verdict in block three weighs.")
    nb.equation("effective_sample", r'''
    rho_, n_, h = sp.symbols(r"\rho n h", positive=True)
    geometric = sp.summation(rho_**h, (h, 1, sp.oo))      # rho/(1 - rho), for rho < 1
    if isinstance(geometric, sp.Piecewise):
        geometric = geometric.args[0][0]
    n_eff = sp.simplify(n_ / (1 + 2 * geometric))
    formula(sp.Eq(sp.Symbol(r"n_{\mathrm{eff}}"), n_eff, evaluate=False))
    rho_measured = both["in_time_order"]
    value = float(n_eff.subs({rho_: rho_measured, n_: len(bus)}))
    agrees("effective sample size n(1 - rho)/(1 + rho) (slice)", value, 73, 0)
    agrees("the same, as make_figs.py stored it", slice_facts["slice_effective_sample_size"]["value"], 73)
    ''', slides=["31"])
    explain(
        "Show the difference between independent draws and a time series on the slice itself.",
        "The backup slides \"IID vs time series\" contrast the two with a generated poster. "
        "The slice can make the same contrast with real numbers: the same speed values, in "
        "time order and shuffled.",
        "Among the windows of 600 consecutive readings of 22 January (five minutes at the "
        "nominal rate), keeps only those in which no step between readings exceeds one "
        "second and no value repeats for more than 40 readings in a row (20 seconds) — so the "
        "window has no gap and no stuck value, only real driving and short stops — and takes "
        "the one in which speed varies most. It plots the readings against their real time "
        "and the same values shuffled (seed 0), and beside each the scatter of every reading "
        "against its predecessor.",
        "In time order each reading lies on the diagonal next to the last one; shuffled, the "
        "cloud has no direction. Order carries information in one and none in the other. The "
        "printed line states the window and both lag-one autocorrelations.")
    nb.figure("iid_vs_series", '''
    in_order = in_time_order(bus)
    first = in_order[pd.to_datetime(in_order["utc_time"]).dt.date.astype(str) == FIRST_DAY].reset_index(drop=True)
    when_1, speed_1 = pd.to_datetime(first["utc_time"]), first["speed"]
    size = 600
    step_1 = when_1.diff().dt.total_seconds().to_numpy()
    repeated = speed_1.groupby((speed_1 != speed_1.shift()).cumsum()).transform("size").to_numpy()
    windows = np.lib.stride_tricks.sliding_window_view
    no_gap = windows(step_1[1:], size - 1).max(axis=1) <= 1.0
    not_stuck = windows(repeated, size).max(axis=1) <= 40
    spread = windows(speed_1.to_numpy(), size).std(axis=1, ddof=1)
    start = int(np.argmax(np.where(no_gap & not_stuck, spread, -1.0)))
    assert no_gap[start] and not_stuck[start]
    window = speed_1.iloc[start:start + size].reset_index(drop=True)
    seconds = (when_1.iloc[start:start + size] - when_1.iloc[start]).dt.total_seconds().to_numpy()
    shuffled = window.sample(frac=1, random_state=0).reset_index(drop=True)
    fig = make_subplots(rows=2, cols=2, column_widths=[0.68, 0.32], horizontal_spacing=0.08,
                        vertical_spacing=0.16,
                        subplot_titles=("in time order: a time series", "reading against its predecessor",
                                        "the same 600 values shuffled: independent draws",
                                        "reading against its predecessor"))
    for row, values, colour in ((1, window, BLUE), (2, shuffled, GREY)):
        fig.add_scatter(x=seconds, y=values, mode="lines", line=dict(color=colour),
                        showlegend=False, row=row, col=1)
        fig.add_scatter(x=values.iloc[:-1], y=values.iloc[1:], mode="markers",
                        marker=dict(size=4, color=colour, opacity=0.5), showlegend=False, row=row, col=2)
        r1 = autocorrelation(values, 1)
        fig.add_annotation(text=f"r₁ = {r1:.3f}", x=0.02, y=0.98, xref=f"x{2 * row} domain",
                           yref=f"y{2 * row} domain", showarrow=False, font=dict(size=15),
                           bgcolor="white", xanchor="left", yanchor="top")
        fig.update_xaxes(title_text="seconds from the window's first reading", row=row, col=1)
        fig.update_yaxes(title_text="speed, m/s", row=row, col=1)
        fig.update_xaxes(title_text="x_(t−1)", row=row, col=2)
        fig.update_yaxes(title_text="x_t", row=row, col=2)
    local_1 = pd.to_datetime(first["local_time"])
    fig.update_layout(title=f"Independent draws or a time series? The same 600 speed readings, two orders<br>"
                            f"<sup>{FIRST_DAY}, {local_1.iloc[start]:%H:%M:%S}–{local_1.iloc[start + size - 1]:%H:%M:%S} "
                            "local time, no step over 1 s</sup>", margin=dict(l=70, r=30, t=110, b=60))
    show(fig, "iid_vs_series", height=640)
    held = start + int(np.argmax(repeated[start:start + size]))
    print(f"window: {FIRST_DAY}, {local_1.iloc[start]:%H:%M:%S} to {local_1.iloc[start + size - 1]:%H:%M:%S} local "
          f"time, {seconds[-1]:.1f} s; largest step {step_1[start + 1:start + size].max():.2f} s; longest run of "
          f"one repeated value {repeated[held]} readings, of speed {speed_1.iloc[held]:g} m/s")
    print(f"lag-one autocorrelation: {autocorrelation(window, 1):.4f} in time order, "
          f"{autocorrelation(shuffled, 1):.4f} shuffled")
    ''', slides=["103", "104"], treatment="lab data: the slides' poster replaced by the slice's "
                                          "readings in two orders")

    # --- slide 32: split by time ---------------------------------------------------------------
    nb.md("""
    ### Split by time — and when at random

    *Slide: "Split by time!! When at random?"* A split by time keeps every training
    observation earlier than every test observation, so the test set asks what the model
    will face in service [@bergmeir2012; @roberts2017]. The slide adds the exception:
    many independent subjects, each producing its own time series, may be sampled at
    random *as subjects*; the readings within one series may not.
    """)
    explain(
        "Write the split by time.",
        "The definition graded by Lab 1 is a statement about sets.",
        "Writes the training set and the test set for one cut instant t_c as sympy sets of "
        "readings x_t over intervals: training on [t₀, t_c), testing on [t_c, t_end].",
        "One cut, chosen before the model sees anything. Module 2 chooses it on this archive.")
    nb.equation("split_by_time", r'''
    t0, tc, tend, instant = sp.symbols(r"t_0 t_c t_{\mathrm{end}} t", real=True)
    reading = sp.IndexedBase("x")
    formula(sp.Eq(sp.Symbol(r"\mathrm{train}"),
                  sp.ImageSet(sp.Lambda(instant, reading[instant]), sp.Interval.Ropen(t0, tc)), evaluate=False),
            sp.Eq(sp.Symbol(r"\mathrm{test}"),
                  sp.ImageSet(sp.Lambda(instant, reading[instant]), sp.Interval(tc, tend)), evaluate=False),
            r"\text{never a random permutation of the rows}")
    ''', slides=["32"])
    explain(
        "Define `split_strategy()` as the Lab 1 solution writes it.",
        "The fourth deliverable is a one-word verdict, and the docstring is the argument "
        "for it.",
        "Copies `split_strategy` from `solutions/lab_01.py`, verbatim; the next cell asks "
        "it for its verdict after measuring what the other choice would do.",
        "The answer is \"by time\"; the next cell supplies the measurement behind it.")
    nb.source(f"{S}/lab_01.py", "split_strategy", cite="[@bergmeir2012; @roberts2017]")
    explain(
        "Measure what a random split does to this series, then ask the lab for its verdict.",
        "The slide's argument is that a random split puts a reading and its neighbour on "
        "both sides of the line. That is a count, so count it.",
        "Puts the slice in time order, assigns each reading to test with probability 0.2 "
        "(seed 20200122), and counts the test readings whose predecessor — half a second "
        "earlier — is in training; then the typical speed difference to that predecessor, "
        "against the typical deviation of speed from its mean. A split by time at one "
        "instant is counted the same way. Last, `split_strategy()`.",
        "About four test readings in five have their near-copy in training, differing by a "
        "twentieth of the variation the model is supposed to explain. The test set is a "
        "paraphrase of the training set, and the verdict is \"by time\".")
    nb.code('''
    speed_in_order = in_time_order(bus)["speed"].to_numpy(float)
    rng = np.random.default_rng(20200122)
    in_test = rng.random(len(speed_in_order)) < 0.2
    leaked = in_test[1:] & ~in_test[:-1]
    share = leaked.sum() / in_test[1:].sum()
    gap_to_neighbour = np.abs(np.diff(speed_in_order))[leaked].mean()
    spread = np.abs(speed_in_order - speed_in_order.mean()).mean()
    print(f"random split: {in_test.sum():,} test readings; {100 * share:.1f} per cent have their "
          "predecessor in training")
    print(f"  mean |speed difference| to that predecessor {gap_to_neighbour:.3f} m/s, against a mean "
          f"absolute deviation of speed of {spread:.3f} m/s")
    cut = int(0.8 * len(speed_in_order))
    in_test_by_time = np.arange(len(speed_in_order)) >= cut
    leaked_by_time = in_test_by_time[1:] & ~in_test_by_time[:-1]
    print(f"split by time at one instant: {int(leaked_by_time.sum())} test reading of "
          f"{int(in_test_by_time.sum()):,} has its predecessor in training — the one at position "
          f"{int(np.flatnonzero(leaked_by_time)[0]) + 1:,}, the first after the cut")
    print("split_strategy():", split_strategy())
    ''')

    # --- the laboratory ----------------------------------------------------------------------------
    nb.md("""
    ## Laboratory 1 — Is it independent?

    *Slide: "Lab 1 — Is it independent?"* Three small functions and a one-word verdict,
    twenty-five minutes. The check passes when both numbers match its own arithmetic to
    four decimal places, when the ordered frame really is ordered, and when the verdict
    names the consequence for splitting data.
    """)
    nb.statement(f"{LABS}/01_is_it_independent.py")
    nb.md("""
    ### The demonstrations

    The four functions were defined above. First the stub's own demonstration, as a
    student sees it once the file is complete; then the solution's, as
    `python3 solutions/lab_01.py` runs it.
    """)
    explain(
        "Run the stub's `__main__` block against the solved functions.",
        "It is what a student sees when the file is complete.",
        "The lines below are the stub's demonstration, verbatim (step 0: its whole "
        "unnumbered block).",
        "The monotone question answered False, four lags in both orders, both lag-one "
        "numbers and the split.")
    nb.step(f"{LABS}/01_is_it_independent.py", 0)
    explain(
        "Make the solution's demonstration believe it is running from its own file.",
        "Its first line puts the folder above `__file__` on the import path, as "
        "`python3 solutions/lab_01.py` would.",
        "Points `__file__` at `solutions/lab_01.py` in the working copy.",
        "The demonstration below runs unchanged; its imports resolve to the stand-ins "
        "registered in the set-up.")
    nb.code('''
    __file__ = str(Path.cwd() / "solutions" / "lab_01.py")
    ''')
    explain(
        "Run the solution's demonstration, verbatim.",
        "It narrates the whole argument: the unsorted file, the stable sort, a control, "
        "eleven lags in three orders, the effective sample size, and the figure.",
        "The lines below are the solution's `__main__` block (step 0: its whole unnumbered "
        "block), unchanged.",
        "The same numbers as above, from the lab's own narration; the figure is the lab's "
        "version of the slide's.")
    nb.step(f"{S}/lab_01.py", 0)
    explain(
        "Show the estimator the check rejects, beside the one it grades.",
        "`pandas.Series.autocorr` computes the Pearson correlation of the series with its "
        "shifted copy, each copy with its own mean and spread. Both are legitimate "
        "statistics; the definition card fixes one so everybody computes the same number.",
        "Computes both at lags 1 and 120 on the slice as shipped.",
        "They agree to four decimals at lag 1 and differ by about 4.5e-4 at lag 120 — past "
        "the check's tolerance, which is why the check names the estimator it grades.")
    nb.code('''
    shipped = bus["speed"].astype(float)
    for lag in (1, 120):
        graded, pairwise = autocorrelation(shipped, lag), shipped.autocorr(lag)
        print(f"lag {lag:>3}: Box–Jenkins {graded:.4f}   pandas autocorr {pairwise:.4f}   "
              f"difference {pairwise - graded:.1e}")
    agrees("lag 120, as shipped, Box–Jenkins", autocorrelation(shipped, 120), 0.0874, 4,
           expected_from="WHY.md")
    agrees("lag 120, as shipped, pandas autocorr", shipped.autocorr(120), 0.0878, 4,
           expected_from="WHY.md")
    ''')
    nb.md("""
    **Finish early?** The stub suggests running the autocorrelation on `payload` instead
    of speed. The practice questions at the end of the notebook do it, with an answer.

    *Stub discrepancy, recorded:* the stub's docstring places the lab under the slide
    "What disorder costs, and the rule that prevents it"; that slide is hidden in the
    deck. Its content is on "The Monotone-Timestamp Rule" and "Is a reading an
    independent draw, or nearly a copy?" above.
    """)
