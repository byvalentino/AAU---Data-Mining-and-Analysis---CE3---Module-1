"""Lab 2, solved — with the reasoning, not only the code.

Run it: `python3 solutions/lab_02.py` from exercises/, or `python3
labs/02_collect_the_day.py` after `python3 apply.py`. It narrates every call
the collector makes to the mock provider and writes the figure
out/lab_02_collection_timeline.html (and .png): records collected against
calls made, with the refusals and failures marked.
"""
from __future__ import annotations

import pathlib
import sys
import time

import pandas as pd
import plotly.graph_objects as go

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from mock.provider import Provider, Throttled, ServerBusy, NoSuchDay  # noqa: E402,F401

LAB = 2

# How many times the same request is repeated after a temporary failure before
# the collector gives up loudly. A stated choice: the check grades that a
# permanent error is never repeated, not this number.
MAX_ATTEMPTS = 5


def collect(provider: Provider, day: str) -> list[dict]:
    """Page through the provider, treating each failure as what it actually is.

    Implements the collector on the slide "Definition — a correct collector":
    repeat get(day, cursor) until next is None; 429 → sleep(retry_after), then
    repeat; 500 → repeat, bounded; 404 → raise, never repeat; de-duplicate by
    record identifier, first delivery wins; every record once, in order — the
    semantics of RFC 9110 and RFC 6585 (Fielding, Nottingham & Reschke, 2022;
    Nottingham & Fielding, 2012) with the de-duplication half of at-least-once
    delivery (Kleppmann, 2017).

    The one idea worth carrying out of this lab: read the error before deciding
    what to do about it. Three exceptions, three different correct responses.

      Throttled   The server told us how long to wait (a 429 with Retry-After).
                  Waiting less is not cleverness, it is a second refusal — and
                  on a real interface, eventually a block. So sleep exactly as
                  asked and repeat.

      ServerBusy  Temporary and unexplained (a 500). Repeat, but bounded: an
                  unbounded retry loop against a dead server is an outage you
                  inflicted on yourself. Five attempts, then give up loudly.

      NoSuchDay   Permanent (a 404). No amount of repetition will conjure the
                  day into existence. Let it propagate so the caller learns
                  something true. This is the failure the lab is really about,
                  because the tempting `except Exception: retry` catches it and
                  spins forever while looking diligent.

    And the fourth response, which has no exception to announce it: once a day
    the cursor steps back inside the page just served, and the next page repeats
    records already held. That is at-least-once delivery — the honest promise of
    a network. The caller supplies the other half by dropping any identifier it
    has already returned, first delivery winning, and the two together give the
    exactly-once *effect* that no far end can give on its own (Kleppmann, 2017).
    Keeping the first copy rather than the last is what keeps the order of the
    day equal to the order of first arrival; since the provider re-sends the
    same bytes, there is nothing to prefer in the second copy anyway.

    Note also what is NOT here: no early return, no break on an empty page. The
    loop ends when the provider says "next": None, and only then. Stopping on a
    short page is how you end up with three quarters of a day and no warning.
    """
    records: list[dict] = []
    already_returned: set[str] = set()
    cursor = 0

    while True:
        page = None
        for attempt in range(MAX_ATTEMPTS):
            try:
                page = provider.get(day, cursor)
                break
            except Throttled as throttled:
                time.sleep(throttled.retry_after)
            except ServerBusy:
                time.sleep(0.01 * (attempt + 1))  # back off a little each time
            # NoSuchDay is deliberately not caught. It is permanent.

        if page is None:
            raise RuntimeError(
                f"gave up on {day} at cursor {cursor} after {MAX_ATTEMPTS} attempts")

        for record in page["records"]:
            # The identifier, not the position: a repeat arrives at a different
            # place in the stream and is the same record all the same.
            if record["id"] in already_returned:
                continue
            already_returned.add(record["id"])
            records.append(record)

        if page["next"] is None:
            return records
        cursor = page["next"]


if __name__ == "__main__":
    from _narrate import narrator, show_table, save_figure

    say = narrator(LAB)
    say.info("Lab 2 — collect one day from a provider that pages, throttles, fails and refuses")
    provider = Provider()
    say.info("mock provider in this process, seed %d: every %dth call refused once with "
             "retry_after %.2f s, every %dth failed once; no network, no account",
             provider.seed, provider.throttle_every, provider.retry_after,
             provider.fail_every)

    # Watch every call the collector makes, without touching collect() itself:
    # the instance attribute shadows the class method for this provider only.
    events: list[dict] = []
    original_get = provider.get

    def watched_get(day, cursor=0):
        try:
            page = original_get(day, cursor)
        except Throttled as refusal:
            events.append({"call": provider.calls, "cursor": cursor, "outcome": "throttled",
                           "records": 0, "detail": f"wait {refusal.retry_after} s"})
            raise
        except ServerBusy:
            events.append({"call": provider.calls, "cursor": cursor, "outcome": "server busy",
                           "records": 0, "detail": "repeat, bounded"})
            raise
        events.append({"call": provider.calls, "cursor": cursor, "outcome": "page",
                       "records": len(page["records"]),
                       "detail": "last page" if page["next"] is None else f"next {page['next']}"})
        return page

    provider.get = watched_get
    records = collect(provider, "2020-01-22")

    log = pd.DataFrame(events)
    log["collected so far"] = log["records"].cumsum()
    show_table(log, "the calls, in order (outcome, records on the page, running total)",
               logger=say)
    say.info("%d records in %d calls: %d pages, %d refusals honoured, %d temporary failures "
             "repeated", len(records), provider.calls, (log["outcome"] == "page").sum(),
             (log["outcome"] == "throttled").sum(), (log["outcome"] == "server busy").sum())
    repeats = provider.redelivered_ids("2020-01-22")
    say.info("the provider handed out %d records for a day that holds %d: %d arrived twice "
             "(%s … %s), and de-duplication by identifier removed exactly those",
             provider.records_delivered, len(records),
             provider.records_delivered - len(records), repeats[0], repeats[-1])
    say.info("waited when told to: %s — the provider timed the gap itself", provider.slept_when_told)
    say.info("every identifier once and in order: %s",
             [r["id"] for r in records] == provider.expected_ids("2020-01-22"))

    # The permanent error, asked once and let through.
    second = Provider()
    try:
        collect(second, "1999-12-31")
    except NoSuchDay as refusal:
        say.info("a day that does not exist raised %s after %d call(s) — propagated, not "
                 "retried (retried_a_permanent_error = %s)", type(refusal).__name__,
                 second.calls, second.retried_a_permanent_error)

    colours = {"page": "#2A78D6", "throttled": "#E07B39", "server busy": "#C0392B"}
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=log["call"], y=log["collected so far"], mode="lines",
                             name="records collected so far", line_color="#52514E"))
    for outcome, colour in colours.items():
        part = log[log["outcome"] == outcome]
        fig.add_trace(go.Scatter(x=part["call"], y=part["collected so far"], mode="markers",
                                 name=outcome, marker=dict(color=colour, size=10)))
    fig.update_layout(
        title="Collecting one day: records collected against calls made — the flat steps "
              "are the refusals and the failures, each repeated, never skipped",
        xaxis_title="call number (count)", yaxis_title="records collected so far (count)",
        legend=dict(x=0.02, y=0.98))
    save_figure(fig, "collection_timeline", LAB, logger=say)

    say.info("what the check grades: %d identifiers once and in order after a page arrived "
             "twice; the retry_after wait honoured; NoSuchDay asked once and let through; a "
             "second day on a fresh provider", len(provider.expected_ids("2020-01-22")))
