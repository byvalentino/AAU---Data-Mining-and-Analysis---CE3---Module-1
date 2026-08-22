#!/usr/bin/env python3
"""Check 2 — a full day collected, nothing lost, the rules of the road obeyed."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from _harness import run, explain                                    # noqa: E402
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from mock.provider import Provider, NoSuchDay                        # noqa: E402


def body(lab):
    provider = Provider()
    records = lab.collect(provider, "2020-01-22")
    expected = provider.expected_ids("2020-01-22")
    repeats = provider.redelivered_ids("2020-01-22")

    # The de-duplication test is only a test if the provider actually re-sent
    # something. A mock that never repeats grades nothing here, which is exactly
    # what this check used to do.
    assert provider.records_delivered > len(expected), (
        f"the provider handed out {provider.records_delivered} records for a day of "
        f"{len(expected)} and this check is meant to prove you removed the repeats. "
        "It delivered no repeat, so nothing was proved — mock/provider.py has been "
        "changed and this check cannot grade against it.")

    collected = [r["id"] for r in records]
    assert len(set(collected)) == len(collected), explain(
        "lab2:duplicates",
        f"{len(collected) - len(set(collected))} record(s) came back more than once",
        "The provider re-sent a page you already had: once a day the cursor it hands "
        "back steps inside the page just served. That is at-least-once delivery, and "
        "your half of it is to drop an identifier you have already returned. Appending "
        "every page as it arrives is not collecting a day, it is transcribing a stream.")
    assert len(collected) == len(expected), explain(
        "lab2:count",
        f"expected {len(expected)} records, got {len(collected)}",
        "Too few and you stopped before the provider said there was no next page, or "
        "you threw away a record that was not a repeat; too many and a repeat survived. "
        "The day holds exactly one record per identifier.")
    assert collected == expected, explain(
        "lab2:order",
        "the records are complete and unique but out of order",
        "Keep the first delivery of an identifier, not the last: the order of the day "
        "is the order of first arrival, and a repeat arrives later than the record it "
        "repeats.")
    assert all(identifier in collected for identifier in repeats), (
        "the identifiers the provider sent twice are missing from your answer entirely. "
        "De-duplicating means keeping one copy, not dropping both.")

    assert provider.slept_when_told, (
        "you were refused with Throttled and retried without waiting retry_after. "
        "On a real interface that earns a block, not a page.")

    # A permanent error must not be retried. The provider records a second ask.
    second = Provider()
    try:
        lab.collect(second, "1999-12-31")
        raise AssertionError(
            "collect() swallowed NoSuchDay. A day that does not exist is permanent — "
            "let it propagate so the caller learns something true.")
    except NoSuchDay:
        pass
    assert not second.retried_a_permanent_error, (
        "you retried a day that does not exist. Read the error before deciding "
        "what to do about it: NoSuchDay will never succeed.")

    # A second day must work on a fresh provider, so nothing is hard-coded — and
    # its repeated page is a different page, so a hard-coded skip fails here.
    third = Provider()
    assert [r["id"] for r in lab.collect(third, "2020-01-23")] == third.expected_ids("2020-01-23"), \
        "collect() works for 22 January but not 23 January — something is hard-coded"
    assert third.records_delivered > len(third.expected_ids("2020-01-23")), (
        "the second day delivered no repeat either; mock/provider.py has been changed")


run(2, "02_collect_the_day", "collect", body)
