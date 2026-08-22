"""Two things every lab needs: the unsolved marker, and the data.

Kept in one small module so that a lab file contains the exercise and nothing
else.
"""
from __future__ import annotations

import pathlib

import pandas as pd

HERE = pathlib.Path(__file__).resolve().parent
SLICE = HERE / "data" / "bus_slice.csv.gz"


class NotSolved(Exception):
    """A lab stub raises this. The check turns it into exit code 2.

    It is not an error. It means "you have not written this yet", which is a
    different state from "you wrote it and it is wrong", and the checks say so.
    """


def load_slice() -> pd.DataFrame:
    """The real vehicle telemetry: one shuttle, both days, every column.

    This is the archive, not a simulation — shuttle VJRD1A10224000055 on the
    22nd and 23rd of January 2020, 48,290 rows. It identifies nobody, which is
    why you may have it. The phone traces from the same trial identify sixteen
    people and stay out of this repository entirely.

    The rows are not in time order. 11,143 of the 48,289 consecutive row pairs
    step backwards in utc_time, and the largest step backwards is 3102.5
    seconds. That is how the file arrived from the trial and it is left that
    way on purpose: sorting it for you would teach you to trust files. This
    function therefore returns the bytes as they ship and sorts nothing.

    Put the rows in time order yourself before you compute anything that
    depends on order — a lag, a difference, a rolling window, a split by date.
    Lab 1 is where you first do it, and where you measure what skipping it
    costs.
    """
    return pd.read_csv(SLICE, low_memory=False)
