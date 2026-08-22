"""Lab 2 — Collect the day.

Why this lab exists: every interface you will ever collect from pages its
answers, refuses you when you ask too fast, fails now and then, and says no to
some things for ever — and a collector that handles those four wrongly either
loses records silently or loops until somebody notices the bill. You prove
that yours returns a whole day, once, in order, against a provider that
misbehaves on purpose.
Where it sits: Block 2 — "Taking data through an interface — five things that
go wrong", and the definition slide "Definition — a correct collector".
What the check grades: every identifier of the day once and in order, with the
page the provider delivers twice removed by identifier; the retry_after wait
honoured; the permanent error asked once and let through; and a second day on a
fresh provider, so nothing is hard-coded.
Needs: time; mock.provider; for the demonstration _narrate, pandas and plotly.

Twenty-five minutes.

A provider that always works teaches nothing. This one pages, throttles, fails
temporarily, refuses permanently, and once a day sends you a page you already
have — inside your own process, so there is no network, no account and no key
to find.

What you write: collect(provider, day).

Read mock/provider.py before you start. Five minutes there saves twenty here.

The five behaviours you must handle, and the status code each stands for:

  paging      provider.get(day, cursor) returns {"records": [...], "next": ...}.
              Keep asking until "next" is None. Stop early and you silently have
              partial data, which is the worst of the failure modes because
              nothing complains.

  Throttled   temporary — a 429 Too Many Requests carrying Retry-After. The
              exception carries .retry_after, in seconds. Wait that long —
              time.sleep — and repeat the same request. The provider notices
              whether you actually waited.

  ServerBusy  temporary — a 500 Internal Server Error. Repeat the same request.
              Give up after a few tries rather than looping forever.

  NoSuchDay   permanent — a 404 Not Found. There is no such day and there never
              will be. Let it propagate. Retrying it is the mistake this lab is
              really about, and the provider records it if you do.

  re-delivery once per day the cursor you are handed steps back inside the page
              you have just been given, so the next page repeats records you
              already hold. Nothing is lost; something arrives twice. This is
              at-least-once delivery, which is what an interface can honestly
              promise, and the caller's half of the bargain is to remove the
              repeat by identifier — the first delivery wins, the order does not
              change. "Exactly once" is what the two halves add up to; it is not
              something the far end can give you on its own.

Return the records in order, once each. Note what that sentence now costs: the
provider hands you more records than the day contains, and `records.extend(...)`
alone will not do.
"""
from __future__ import annotations

import pathlib
import sys
import time

import pandas as pd
import plotly.graph_objects as go

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from lab_support import NotSolved  # noqa: E402
from mock.provider import Provider, Throttled, ServerBusy, NoSuchDay  # noqa: E402,F401
from _narrate import narrator, show_table, save_figure  # noqa: E402,F401

LAB = 2

# How many times the same request is repeated after a temporary failure before
# the collector gives up loudly. A stated choice: the check grades that a
# permanent error is never repeated, not this number.
MAX_ATTEMPTS = 5


def collect(provider: Provider, day: str) -> list[dict]:
    """Every record for `day`, in order, with none lost and none twice.

    Args:
        provider: a mock.provider.Provider.
        day:      a date string such as "2020-01-22".

    Returns:
        A list of record dictionaries.

    Raises:
        NoSuchDay: if the provider says the day does not exist. Let it through.

    Definition graded by the check:
        repeat get(day, cursor) until next is None; 429 → sleep(retry_after),
        then repeat; 500 → repeat, bounded; 404 → raise, never repeat;
        de-duplicate by record["id"], first wins; every record once, in order
        (Fielding, Nottingham & Reschke, 2022, RFC 9110 §§9.2.2, 10.2.3,
        15.5.5, 15.6.1; Nottingham & Fielding, 2012, RFC 6585 §4; Kleppmann,
        2017). Choices: Throttled is the 429, ServerBusy the 500, NoSuchDay the
        404; wait exactly retry_after seconds; the reference solution repeats a
        500 at most MAX_ATTEMPTS times; the identifier is record["id"] and the
        first delivery of it is the one that is kept, so the order of the day is
        the order of first arrival. Slide: "Definition — a correct collector".

    Needs: provider.get, time.sleep, a while loop that ends only when the
    provider says next is None, and something that remembers which identifiers
    have already been returned
    """
    # TODO: page through the provider, handling the three exceptions correctly.
    raise NotSolved("collect(provider, day) still raises instead of returning records")


if __name__ == "__main__":
    say = narrator(LAB)
    provider = Provider()
    records = collect(provider, "2020-01-22")
    say.info("%d records in %d calls; the provider handed out %d, so %d were repeats",
             len(records), provider.calls, provider.records_delivered,
             provider.records_delivered - len(records))
    say.info("waited when told to: %s", provider.slept_when_told)
    say.info("retried a permanent error: %s", provider.retried_a_permanent_error)
