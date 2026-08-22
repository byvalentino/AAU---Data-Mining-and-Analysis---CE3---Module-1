"""A vehicle-position provider that misbehaves on purpose, in this process.

No network, no account, no key. It runs inside the lab so that thirty students
behind one university address cannot rate-limit each other, and so that the lab
still works on a train.

It behaves like the interfaces you will actually meet:

  * it pages       — one call returns a page and a cursor to the next
  * it throttles   — ask too fast and it refuses with Throttled(retry_after)
  * it fails       — some calls raise ServerBusy, which is temporary
  * it says no     — an unknown day raises NoSuchDay, which is permanent
  * it re-delivers — once per day the cursor it hands back steps behind the page
                     it has just served, so the next page repeats records you
                     already hold. That is at-least-once delivery, and it is the
                     normal behaviour of a paging interface that has retried
                     something internally. Nothing is lost; something arrives
                     twice; the caller removes the repeat by identifier.

Everything is seeded, so the same code fails in the same places every time. The
provider also keeps score: it records whether you waited when told to, whether
you retried something that will never succeed, and how many records it handed
out in total — which is more than the day holds, because of the repeat.
"""
from __future__ import annotations

import random
import time
from dataclasses import dataclass, field

PAGE_SIZE = 50
PAGES_PER_DAY = 14  # 14 pages of 50 -> 700 records for a full day
RECORDS_PER_DAY = PAGE_SIZE * PAGES_PER_DAY
KNOWN_DAYS = ("2020-01-22", "2020-01-23")

# How far the cursor steps back at the one re-delivery point of each day. Twenty
# of the fifty records on the following page are then repeats. The size is fixed
# rather than random so that a student can count the repeats by hand and check
# their de-duplication against the number.
OVERLAP = 20


class Throttled(Exception):
    """Too many requests. Temporary. Wait retry_after seconds, then repeat."""

    def __init__(self, retry_after: float):
        super().__init__(f"too many requests, retry after {retry_after} s")
        self.retry_after = retry_after


class ServerBusy(Exception):
    """The far end failed. Temporary. Repeating the same request may work."""


class NoSuchDay(Exception):
    """There is no such day and there never will be. Permanent. Do not retry."""


@dataclass
class Provider:
    """One instance per lab run. Seeded, so failures are reproducible."""

    seed: int = 20200122
    throttle_every: int = 5     # every 5th call is refused, once
    fail_every: int = 7         # every 7th call fails temporarily, once
    retry_after: float = 0.05   # seconds; short, because this is a lesson not a wait

    calls: int = 0
    records_delivered: int = 0  # repeats included, so it exceeds the day's total
    slept_when_told: bool = True
    retried_a_permanent_error: bool = False
    _already_throttled: set = field(default_factory=set)
    _already_failed: set = field(default_factory=set)
    _permanent_seen: set = field(default_factory=set)
    _told_to_wait_at: dict = field(default_factory=dict)

    def _redelivery_boundary(self, day: str) -> int:
        """The record index at which this day steps its cursor backwards.

        Drawn once per day from the seed, so the same page repeats on every run
        and a different one repeats on the other day. It is a whole number of
        pages and never the first or the last, so the repeat is always a page
        the caller has already stored.
        """
        page = random.Random(f"{self.seed}-{day}-redelivery").randrange(1, PAGES_PER_DAY - 1)
        return page * PAGE_SIZE

    def _record(self, day: str, index: int) -> dict:
        """The record at an absolute position in the day — the same bytes every time.

        A record that changed between deliveries would make de-duplication by
        identifier a lie: the second copy would carry a different speed and the
        caller would have to decide which one is true. Real interfaces re-send
        the same row; so does this one.
        """
        page = index // PAGE_SIZE
        values = random.Random(f"{self.seed}-{day}-{page}").sample(range(10_000), PAGE_SIZE)
        return {"id": f"{day}-{index:04d}",
                "day": day,
                "speed": round(values[index % PAGE_SIZE] / 3000, 3)}

    def get(self, day: str, cursor: int = 0) -> dict:
        """Return {"records": [...], "next": cursor or None} for one page."""
        self.calls += 1

        if day not in KNOWN_DAYS:
            if day in self._permanent_seen:
                # A second ask for a day that does not exist. This is the mistake
                # the lab is really about: a permanent error retried forever.
                self.retried_a_permanent_error = True
            self._permanent_seen.add(day)
            raise NoSuchDay(f"no data for {day}")

        key = (day, cursor)
        # If we refused this request last time, check that the caller actually
        # waited. Honouring retry_after is the whole point of a rate limit.
        if key in self._told_to_wait_at:
            waited = time.monotonic() - self._told_to_wait_at.pop(key)
            if waited < self.retry_after * 0.9:
                self.slept_when_told = False

        if self.calls % self.throttle_every == 0 and key not in self._already_throttled:
            self._already_throttled.add(key)
            self._told_to_wait_at[key] = time.monotonic()
            raise Throttled(self.retry_after)
        if self.calls % self.fail_every == 0 and key not in self._already_failed:
            self._already_failed.add(key)
            raise ServerBusy("upstream unavailable")

        start = max(0, min(int(cursor), RECORDS_PER_DAY))
        stop = min(start + PAGE_SIZE, RECORDS_PER_DAY)
        records = [self._record(day, index) for index in range(start, stop)]
        self.records_delivered += len(records)

        following = stop
        if following == self._redelivery_boundary(day):
            # The one re-delivery of the day: hand back a cursor that sits
            # inside the page just served. Every record still arrives; OVERLAP
            # of them arrive twice.
            following -= OVERLAP
        return {"records": records,
                "next": following if following < RECORDS_PER_DAY else None}

    def expected_ids(self, day: str) -> list[str]:
        """Every identifier a correct collector must return, once each, in order."""
        return [f"{day}-{n:04d}" for n in range(RECORDS_PER_DAY)]

    def redelivered_ids(self, day: str) -> list[str]:
        """The identifiers this day hands out twice — the repeat to be removed."""
        boundary = self._redelivery_boundary(day)
        return [f"{day}-{n:04d}" for n in range(boundary - OVERLAP, boundary)]
