"""Grades: read scores from a file, one score per line.

Usage: python grades.py scores.txt
"""

import math
import sys
from decimal import ROUND_HALF_UP, Decimal

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


def highest(scores):
    return max(scores)


def lowest(scores):
    return min(scores)


def two_places(value):
    """Round to two decimal places, halves rounding up (78.125 -> 78.13)."""
    return Decimal(repr(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def average(scores):
    """Return the average as a Decimal rounded to two decimal places."""
    total = sum(Decimal(repr(score)) for score in scores)
    return (total / len(scores)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


# Lowest average needed for each letter, checked from the top down.
GRADE_CUTOFFS = [(90, "A"), (80, "B"), (70, "C"), (60, "D")]


def letter_grade(avg):
    """Letter for an average: A 90-100, B 80-89, C 70-79, D 60-69, F 0-59."""
    for cutoff, letter in GRADE_CUTOFFS:
        if avg >= cutoff:
            return letter
    return "F"


def format_score(score):
    """Show a score the way it was entered: 90 not 90.0, 85.5 as 85.5."""
    return str(int(score)) if score.is_integer() else repr(score)


def scores_row(scores):
    return ", ".join(format_score(score) for score in scores)


def build_report(scores):
    avg = average(scores)
    return "\n".join([
        f"Highest: {two_places(highest(scores))}",
        f"Lowest: {two_places(lowest(scores))}",
        f"Average: {avg}",
        f"Letter grade: {letter_grade(avg)}",
        f"Scores: {scores_row(scores)}",
    ])


def main(argv):
    if len(argv) != 1:
        print(USAGE)
        return 2
    try:
        scores = read_scores(argv[0])
    except ScoreError as err:
        print(err)
        return 1
    print(build_report(scores))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
