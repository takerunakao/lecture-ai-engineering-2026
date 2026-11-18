#!/usr/bin/env python3
"""Run Day5 with --setup / --check / --run / --resume latest."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from day5_lab.experiment import main

if __name__ == "__main__":
    raise SystemExit(main(ROOT))
