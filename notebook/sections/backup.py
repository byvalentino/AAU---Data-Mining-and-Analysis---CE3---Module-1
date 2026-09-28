"""The deck's "References and Backup Material" (slides 76-123), practice, and closing notes."""


def build(nb, explain) -> None:
    nb.md("""
    ---
    # References and Backup Material

    *Slides 76–123.* The deck's references (slides 78–83) are the reference list at the
    end of this notebook, each checked against the course's literature folders or marked
    as not held there. The backup slides revisit the concepts of block one and block two
    in more depth; the pictures among them that carry data or a concept are drawn in the
    blocks above or below, and the rest — generated posters, vendor diagrams, a
    publication's figure, a screenshot of code — are listed in `figure_map.json` with the
    reason they are not redrawn.

    ### What is data? — eighteen views of one slide

    *Slides 85–102.* The same five pictures, captioned in turn: a social-network post
    (semi-structured), text (qualitative, unstructured), reactions (quantitative), a
    graph (structured), an image (qualitative), a sound wave (quantitative), a cat and a
    dog (nominal categories), short and tall (ordinal), a payment method (nominal), a
    timestamp (quantitative, continuous), a location (quantitative, discrete), a
    spatio-temporal observation, a price (quantitative, continuous) — then "Anything
    odd?", and a bias: the Ames room, where two people of the same height look unequal.
    The graph and the sound wave are drawn in block one. The same classification can be
    applied to the slice's own twenty-two columns.
    """)
    explain(
        "Classify the slice's columns the way the backup slides classify data.",
        "The kinds of data on the slides are not abstractions: the vehicle file holds most "
        "of them, and a column's kind decides what arithmetic on it means.",
        "Measures each column's stored type, its number of distinct values and its "
        "completeness, and sets beside it a reading of its kind. The reading is a judgement "
        "made for this notebook — the measured columns are facts, the last column is not.",
        "Several columns are not what their stored type suggests: `mileage` is an integer "
        "that is a counter at its ceiling, `timestamp` is text that holds local time, "
        "`emergency_stop` is a category whose absence is a value, and four columns carry one "
        "value only.")
    nb.code('''
    reading = {
        "vehicle_id": "nominal (an identifier)", "platform": "nominal, constant",
        "state": "nominal, constant", "lat": "quantitative, continuous (location)",
        "lon": "quantitative, continuous (location)", "utc_time": "timestamp (UTC), stored as text",
        "mode": "nominal (auto / manual)", "mileage": "quantitative, discrete — a 16-bit counter at its ceiling",
        "speed": "quantitative, continuous, signed", "outside_temperature": "quantitative, recorded as integers",
        "inside_temperature": "quantitative, recorded as integers", "payload": "quantitative, unit never written down",
        "battery_level": "quantitative, continuous (per cent)", "door_state": "nominal (closed / opened / moving)",
        "ramp_state": "nominal, constant", "tz": "nominal, constant", "local_time": "timestamp (local), stored as text",
        "emergency_stop": "nominal — its absence is a value", "theta": "quantitative, circular (radians)",
        "timestamp": "timestamp (local, despite its name), stored as text",
        "x_web": "quantitative, continuous (Web Mercator metres)", "y_web": "quantitative, continuous (Web Mercator metres)",
    }
    kinds = pd.DataFrame({
        "stored as": bus.dtypes.astype(str),
        "distinct values": bus.nunique(dropna=True),
        "completeness": bus.notna().mean().round(5),
        "kind (a reading, not a measurement)": pd.Series(reading),
    })
    kinds
    ''')
    nb.md("""
    ### Other data regimes — seven examples

    *Slides 105–111.* Each shows the same list of regimes — panel, spatial,
    spatio-temporal, survival, network, functional, point processes — with one example and
    one question. The grid picture is not redrawn. As practice, decide which regime each
    example is, and what that rules out:

    | Slide | Example | Question |
    |---|---|---|
    | 105 | House prices in DKK per m² in Denmark, over ten years | How has the house-market price evolved? |
    | 106 | House prices in DKK per m² in Denmark | What is the house-market price? |
    | 107 | Daily PM2.5 at monitoring stations across Denmark | What is the national air-quality nowcast? |
    | 108 | Component failures of a vehicle | What is the expected lifetime of my car, from today? |
    | 109 | Structure and activity of a chemical compound | What is the activity of compound X on human subjects? |
    | 110 | A near-infrared light spectrum | Which material does the spectrum correspond to? |
    | 111 | Satellite tiles with per-pixel reflectance | Which crops were planted this season, and where? |

    ### Sources, methods, and what a mistake costs

    *Slides 112–114.* Primary or secondary, manual or automated; surveys, observation,
    experiments, interfaces, scraping, sensors — and for each, why and what a data
    scientist needs to know. Slide 114 asks what a mistake costs and what the data costs;
    its first picture (a wrong table against wrong custom windows) is a generated poster
    and is not redrawn; its second is a Pareto frontier of accuracy against cost, redrawn
    below.
    """)
    explain(
        "Redraw the slide's accuracy-against-cost frontier — illustrative.",
        "Better instruments cost more, and past some point each gain in accuracy costs "
        "more than the last. The frontier is the set of instruments no other instrument "
        "beats on both counts.",
        "Places the four points where the slide's picture puts them (read off the picture, "
        "on a unitless 0–1 scale: neither axis has numbers on the slide) and labels them as "
        "the picture does — the picture writes \"Caliper\" beside the laser ruler's point "
        "and gives it no point of its own, and the redraw keeps that. It then computes which "
        "points are non-dominated.",
        "All four lie on the frontier. The positions are the picture's, not measurements of "
        "any instrument.")
    nb.figure("pareto_accuracy_cost", '''
    instruments = {"Measuring tape (dm)": (0.30, 0.07), "Laser ruler (cm) / Caliper": (0.37, 0.25),
                   "Laser distance meter": (0.51, 0.48), "Laser micrometer": (0.81, 0.79)}
    frontier = [name for name, (cost, accuracy) in instruments.items()
                if not any(c <= cost and a >= accuracy and (c, a) != (cost, accuracy)
                           for c, a in instruments.values())]
    ordered_points = sorted(instruments.items(), key=lambda item: item[1][0])
    fig = go.Figure()
    fig.add_scatter(x=[p[0] for _, p in ordered_points], y=[p[1] for _, p in ordered_points], mode="lines",
                    line=dict(color=GREY, width=3), name="Pareto frontier")
    fig.add_scatter(x=[p[0] for p in instruments.values()], y=[p[1] for p in instruments.values()],
                    mode="markers+text", text=list(instruments), textposition="top left",
                    marker=dict(size=16, color=ORANGE), name="instrument")
    fig.update_layout(title="Illustrative: accuracy against cost — positions read off the slide's picture",
                      xaxis=dict(title="cost (€), no scale on the slide", range=[0, 1], showticklabels=False),
                      yaxis=dict(title="accuracy (higher is better), no scale on the slide", range=[0, 1],
                                 showticklabels=False), showlegend=False)
    show(fig, "pareto_accuracy_cost", height=480)
    print("on the frontier:", frontier)
    ''', slides=["114"], treatment="illustrative: positions read off the slide's picture, no data")
    nb.md("""
    ### Data quality dimensions, APIs and JSON, scraping, and legality

    *Slides 115–123.* Slide 115 lists accuracy with the four dimensions measured in
    block three, together with sampling strategies and the risks of bias; its picture is
    a generated cartoon. Slides 116–117 (REST, endpoints, pagination; JSON) are drawn in
    block two from Lab 2's provider. Slides 118–121 cover scraping — the workflow
    (request, parse, extract, store), tools, the scraping pipeline, the MediaWiki
    interface against HTML scraping, and the trade-offs between an interface and a
    scraper [@boegershausen2022]; slide 122 the legal and ethical boundaries (personal
    data, copyright, terms of service, the hiQ Labs case) [@gdpr2016]; slide 123 the
    questions to ask before building a pipeline: what data is available, what fulfils
    the pipeline's requirements and the problem's, and where to implement it. Their
    pictures are generated posters and vendor diagrams, which are not redrawn; a
    screenshot of code, transcribed below as text; and a publication's figure, redrawn
    below because it carries a concept.
    """)
    nb.md('''
    ### Example: wiki-crawling — the code on slide 120, as text

    *Slide 120: "Example: wiki-crawling — MediaWiki API (structured) vs HTML scraping
    (unstructured)".* The slide shows a screenshot of the author's crawler. It is
    transcribed here so it can be read and copied; it is **not run**, because it calls
    a live third-party service (Wikipedia's interfaces), which this notebook does not
    call — Lab 2's provider stands in for an interface. The screenshot ends at its
    line 22, inside the first function; the rest of the file is not on the slide. One
    thing is left out on purpose: the contact e-mail address in the `UA` string.

    ```python
    #!/usr/bin/env python3
    """
    Wikipedia API crawler (BFS)
    - Stays on en.wikipedia.org, namespace 0 (articles).
    - Uses Action API (prop=links) to discover neighbors.
    - Uses REST Summary API to fetch a short extract per page.
    - Writes results to JSONL (one page per line).

    Run:  python wiki_crawl.py --seed "Data science" --max-pages 200
    """

    import argparse, json, random, time
    from urllib.parse import quote
    import requests

    ACTION_API = "https://en.wikipedia.org/w/api.php"
    REST_SUMMARY = "https://en.wikipedia.org/api/rest_v1/page/summary/{}"

    UA = "Valentino Data Science/1.0 (+contact: <address on the slide, left out here>)"

    def get_links(title, session, limit_per_page=500):
        """Return set of linked article titles (namespace 0) from given page."""
    ```

    Two things in those lines connect to this module: the crawler identifies itself
    with a `User-Agent` string that names a contact, so the operator of the service can
    reach whoever runs it; and it writes one JSON object per line ("JSONL"), the format
    Lab 4 lands.

    ### Interface or scraper: the three stages of a scraping project

    *Slide 121: "API vs. scraping trade-offs".* Structure, speed, legality, stability,
    cost. The slide's picture is the three-stage framework of {@boegershausen2022}.
    ''')
    explain(
        "Redraw the slide's three-stage funnel — illustrative.",
        "The picture carries a concept, not data: a scraping project passes through three "
        "stages, drawn as a funnel between technical feasibility on one side and legal and "
        "ethical risks on the other, ending in validity [@boegershausen2022].",
        "Draws a funnel with the three stage names the picture shows — source selection, "
        "collection design, data extraction — the two forces above it and validity below, "
        "and beside each stage the number of questions the picture lists for it and their "
        "labels (#1.1 to #3.3). The questions themselves are the publication's text and "
        "are not copied.",
        "Deciding to scrape belongs to the first stage, not the last: among the picture's "
        "source-selection questions is whether alternatives to web scraping were considered "
        "— the slides' advice to prefer an interface.")
    nb.figure("scraping_funnel", '''
    stages = [("1. Source selection", 3, "#1.1–#1.3"), ("2. Collection design", 4, "#2.1–#2.4"),
              ("3. Data extraction", 3, "#3.1–#3.3")]
    fig = go.Figure()
    fig.add_shape(type="path", path="M 1,10 L 9,10 L 5,0.6 Z", fillcolor="#E4E6EA", line=dict(width=0),
                  layer="below")
    for k, (name, questions, labels) in enumerate(stages):
        top = 9.2 - 2.9 * k
        fig.add_shape(type="rect", x0=2.9, x1=7.1, y0=top - 1.9, y1=top, fillcolor="white",
                      line=dict(color=NAVY, width=2))
        fig.add_annotation(x=5, y=top - 0.95, text=f"<b>{name}</b>", showarrow=False, font=dict(size=18, color=NAVY))
        side = 9.6 if k != 1 else 0.4
        fig.add_annotation(x=side, y=top - 0.95, text=f"{questions} questions ({labels})", showarrow=False,
                           xanchor="left" if k != 1 else "right", font=dict(size=14, color=GREY))
        fig.add_shape(type="line", x0=7.1 if k != 1 else 2.9, x1=9.5 if k != 1 else 0.5,
                      y0=top - 0.95, y1=top - 0.95, line=dict(color=GREY, width=1))
    fig.add_annotation(x=2.2, y=11.0, text="<b>Technical feasibility</b>", showarrow=False, font=dict(size=16))
    fig.add_annotation(x=7.8, y=11.0, text="<b>Legal and ethical risks</b>", showarrow=False, font=dict(size=16))
    fig.add_annotation(x=5, y=0.0, text="<b>Validity</b>", showarrow=False, font=dict(size=16))
    fig.update_xaxes(visible=False, range=[-3.5, 13.5])
    fig.update_yaxes(visible=False, range=[-0.6, 11.8])
    fig.update_layout(title="Illustrative: the three stages of a web-scraping project<br>"
                            "<sup>stage names from Boegershausen et al. (2022), the figure on slide 121</sup>",
                      margin=dict(l=20, r=20, t=60, b=20))
    show(fig, "scraping_funnel", width=1100, height=560)
    ''', slides=["121"], treatment="illustrative: the publication's three-stage funnel redrawn with its "
                                     "stage names; the questions counted, not copied")
    nb.md("""
    ---
    ## Practice

    Three questions. Each is a few lines of code with the functions defined above, and
    each has a definite answer.

    1. **Which decays more slowly, `speed` or `payload`?** Compute the lag-k sample
       autocorrelation of both at lags 1, 20 and 120 on the slice in time order, and say
       what the difference tells you about how quickly each quantity can change.
    2. **Where are the ten long gaps?** Find the intervals over 60 seconds within a day,
       and print the local time each begins and how long it lasts. Do they cluster?
    3. **How many rows would a naive cleaning destroy?** Count the rows a careless
       pipeline would drop by treating negative speed, the mileage ceiling and the empty
       `emergency_stop` as defects, as a share of the file.

    Answers below — try first.
    """)
    explain(
        "A place for your own workings.",
        "Answers read before trying teach less than answers checked after.",
        "Nothing; it is empty on purpose.",
        "Write your answer, then compare with the next cells.")
    nb.code("# Your workings here.")
    nb.md("### Answers")
    explain(
        "Answer the three practice questions.",
        "Each answer is a measurement, so it is computed rather than asserted.",
        "1: `autocorrelation()` on the time-ordered slice for both columns at three lags. "
        "2: the within-day intervals over one minute, with their start in local time. "
        "3: the rows a careless filter would drop, as a count and a share.",
        "Payload decays more slowly than speed — the load changes only when someone boards, "
        "speed changes continuously. The gaps are listed with their times. And a careless "
        "cleaning would drop about half the file, none of it a defect.")
    nb.code('''
    # 1. payload against speed
    in_order = in_time_order(bus)
    for column in ("speed", "payload"):
        values = in_order[column].astype(float)
        print(f"{column:8}", "   ".join(f"lag {k}: {autocorrelation(values, k):.4f}" for k in (1, 20, 120)))

    # 2. where the long gaps begin
    when = pd.to_datetime(in_order["utc_time"])
    local = pd.to_datetime(in_order["local_time"])
    step_s = when.groupby(when.dt.date).diff().dt.total_seconds()
    print("\\nintervals over one minute, within a day:")
    for position in step_s[step_s > 60].index:
        print(f"  begins {local[position - 1]:%d %b %H:%M:%S} local, lasts {step_s[position] / 60:5.1f} minutes")

    # 3. what a careless cleaning would destroy
    careless = (bus["speed"] < 0) | (bus["mileage"] == MILEAGE_CEILING) | bus["emergency_stop"].isna()
    print(f"\\nrows a naive 'drop the odd ones' pass would remove: {careless.sum():,} "
          f"({100 * careless.mean():.1f} per cent of the slice). None of them is a defect.")
    ''')

    nb.md("""
    ---
    ## Deck discrepancies found while building this notebook

    Each is explained where it occurs; those that are numbers are also printed there by
    `beside()`, with the reason, and gathered in the table at the end of the notebook.
    None is fixed here: the deck is the master and is edited only in PowerPoint.

    1. **"The case" slide** quotes the archive — 53,155 rows, 2 vehicles — under a
       footer that names `data/bus.csv`; the labs ship the 48,290-row, one-vehicle slice.
       Scope, not error; the route's 67 × 86 m box is the same on both.
    2. **"The Monotone-Timestamp Rule"** labels its data challenge "(bus.csv)" beside
       23.1 per cent of pairs out of order; the 23.1 is measured on the slice
       (`slice_backward_share_pct` in `measured.json`). Most slides of blocks one and
       three carry the footer "Numbers: the archive — data/bus.csv" on numbers measured
       on the slice.
    3. **"Is a reading an independent draw…"** quotes 0.9967, 0.9981 and −0.0008 in its
       text (22 January only) above a figure labelled 0.9970 (both days of the slice);
       the slide does not say the scopes differ.
    4. **Completeness**: slides 47 and 52 quote `emergency_stop` at 55.344 per cent
       (archive) and 52.574 (slice); stated on the slides, repeated here with scope.
    5. **Validity**: 4,434 negative speeds (archive) against 4,429 on the slice the lab
       grades.
    6. **"Three columns with insufficient metadata"**: four constant columns on the
       archive; five on the slice, which holds one vehicle.
    7. **Format cost**: "the same 53,155 rows" and all sizes and seconds are the
       archive's, on the instructor's machine; the lab measures the slice.
    8. **Article 10 slide**: "Annex III lists transport infrastructure"; the Annex's
       wording (point 2) is safety components in the management and operation of road
       traffic, among other critical infrastructure.
    9. **Lab 1 stub** places the lab under "What disorder costs, and the rule that
       prevents it", which is a hidden slide.
    10. **Naming**: the definition slide is titled "write, flush, sync, rename, record"
        and slide 69 "Write, flush, rename, record — four steps"; the stub, the solution
        and the slide's own formula say fsync, and slide 69 lists a fifth property.
    11. **Overbooking slide**: it prints "250", "220" and "Economy" without saying
        which number is which; the notebook reads them as tickets and seats.
    12. **"The case" slide** says the two shuttles ran "a fixed loop"; the trial's paper
        describes two routes and three stops, one stop and a segment of track shared,
        and the vehicles' assignment to the routes switched during the experiment
        (Servizi et al., 2023, Sec. III-D). The slide's stops A, B and C are not in the
        telemetry: the route map marks measured dwells, not stops.
    13. **Pipeline slide**: it credits "the expensive failures happen before the model"
        to Huyen (2022); the early release held in the literature folder does not say it
        in those words. The notebook keeps the slide's credit and cites the book only for
        what the held text states.
    14. **Credits**: slides 3, 19, 21, 22, 23 and 36 credit "Mining User Transport
        Behavior from Smartphones" without author, year or publisher; the notebook
        cites it as the slide does and does not call it the trial's own study.
    15. **Format cost**: slide 72's "0.08 of its read time" is one wall-clock ratio on
        the archive and the instructor's machine; the slice's ratio is printed beside it
        and differs from run to run.

    One text in the labs, not the deck, is recorded the same way: the profile Lab 3's
    solution writes says `emergency_stop` "is empty on most rows"; it is empty on 47.4
    per cent of the slice (44.7 per cent of the archive) — the deck's "nearly half".

    ## A note on what is not here

    The phone traces from the same trial (`passengers.csv`) are the position records of
    sixteen identifiable people — personal data under Article 4 of the General Data
    Protection Regulation, whatever the columns are called [@gdpr2016]. They are not in
    this repository and no cell of this notebook opens them. The vehicle telemetry
    identifies nobody.
    """)
