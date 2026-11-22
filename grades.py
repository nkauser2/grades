"""Grades: read scores from a file, one score per line.

Usage: python grades.py scores.txt
"""

import math
import sys

NOT_FOUND = "Error: Not Found"
CONTENT_NOT_FOUND = "Content Not Found"
USAGE = "Usage: python grades.py scores.txt"

MIN_SCORE = 0
MAX_SCORE = 100


class ScoreError(Exception):
    """Raised when the score file is missing, empty, or has a bad score."""


def parse_score(text):
    """Turn one line into a score, or raise ScoreError if it isn't valid."""
    try:
        score = float(text)
    except ValueError:
        raise ScoreError(NOT_FOUND) from None
    if not math.isfinite(score) or not MIN_SCORE <= score <= MAX_SCORE:
        raise ScoreError(NOT_FOUND)
    return score


def read_scores(path):
    """Read the score file and return its scores as a list of floats.

    Blank lines are skipped. The file is only read, never changed.
    """
    try:
        with open(path, encoding="utf-8-sig") as f:
            lines = f.read().splitlines()
    except OSError:
        raise ScoreError(NOT_FOUND) from None

    scores = [parse_score(line.strip()) for line in lines if line.strip()]
    if not scores:
        raise ScoreError(CONTENT_NOT_FOUND)
    return scores


def main(argv):
    if len(argv) != 1:
        print(USAGE)
        return 2
    try:
        read_scores(argv[0])
    except ScoreError as err:
        print(err)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
