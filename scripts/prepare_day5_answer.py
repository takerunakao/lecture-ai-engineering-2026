#!/usr/bin/env python3
"""Prepare Day5 only from completed live runs and reviewed observations."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from day5_lab.experiment import prepare_main

if __name__ == "__main__":
    raise SystemExit(prepare_main(ROOT))
