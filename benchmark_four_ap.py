#!/usr/bin/env python3
# Copyright (c) 2026 Boon Suan Ho
# SPDX-License-Identifier: MIT

"""Benchmark fresh-instance queries, excluding interpreter startup and printing.

Run ``python3 benchmark_four_ap.py --count 1000 --repeat 7``. This is a manual
benchmark, not a wall-clock assertion in the tests: machine speeds vary.
"""

import argparse
from collections.abc import Callable
import platform
import statistics
from time import perf_counter

from four_ap import Permutation


def positive_int(text: str) -> int:
    try:
        number = int(text)
    except ValueError as error:
        raise argparse.ArgumentTypeError("expected a positive integer") from error
    if number <= 0:
        raise argparse.ArgumentTypeError("expected a positive integer")
    return number


def measure(label: str, action: Callable[[], object], repeats: int) -> None:
    samples = []
    for _ in range(repeats):
        start = perf_counter()
        action()
        samples.append(perf_counter() - start)
    print(f"{label}: median {statistics.median(samples):.6f} s "
          f"(min {min(samples):.6f}, max {max(samples):.6f}, n={repeats})")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--count", type=positive_int, default=1000)
    parser.add_argument("--repeat", type=positive_int, default=7)
    args = parser.parse_args()
    index = args.count - 1
    value = Permutation().value(index)
    print(f"Python {platform.python_version()} / {platform.platform()}")
    measure(f"prefix({args.count})", lambda: Permutation().prefix(args.count), args.repeat)
    measure(f"value({index})", lambda: Permutation().value(index), args.repeat)
    measure("position(last value)", lambda: Permutation().position(value), args.repeat)


if __name__ == "__main__":
    main()
