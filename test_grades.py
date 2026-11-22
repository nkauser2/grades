"""Tests for grades.py."""

import subprocess
import sys
from decimal import Decimal
from pathlib import Path

import pytest

from grades import (
    ScoreError,
    average,
    build_report,
    highest,
    letter_grade,
    lowest,
    main,
    read_scores,
    scores_row,
)

GRADES_PY = Path(__file__).parent / "grades.py"


def write_file(tmp_path, text, name="scores.txt"):
    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    return path


# --- Reading valid files -----------------------------------------------------

def test_reads_whole_number_scores(tmp_path):
    path = write_file(tmp_path, "90\n75\n60\n")
    assert read_scores(path) == [90.0, 75.0, 60.0]


def test_reads_decimal_scores(tmp_path):
    path = write_file(tmp_path, "87.5\n92.25\n")
    assert read_scores(path) == [87.5, 92.25]


def test_reads_file_without_trailing_newline(tmp_path):
    path = write_file(tmp_path, "80\n70")
    assert read_scores(path) == [80.0, 70.0]


def test_reads_single_score(tmp_path):
    path = write_file(tmp_path, "55\n")
    assert read_scores(path) == [55.0]


def test_ignores_spaces_around_scores(tmp_path):
    path = write_file(tmp_path, "  88  \n\t72\n")
    assert read_scores(path) == [88.0, 72.0]


def test_skips_blank_lines(tmp_path):
    path = write_file(tmp_path, "88\n\n72\n   \n")
    assert read_scores(path) == [88.0, 72.0]


def test_keeps_scores_in_file_order(tmp_path):
    path = write_file(tmp_path, "10\n100\n50\n")
    assert read_scores(path) == [10.0, 100.0, 50.0]


def test_accepts_boundary_scores_0_and_100(tmp_path):
    path = write_file(tmp_path, "0\n100\n")
    assert read_scores(path) == [0.0, 100.0]


def test_reads_file_with_windows_bom(tmp_path):
    path = tmp_path / "scores.txt"
    path.write_bytes(b"\xef\xbb\xbf90\r\n80\r\n")
    assert read_scores(path) == [90.0, 80.0]


def test_does_not_change_the_score_file(tmp_path):
    original = "90\n75\n60\n"
    path = write_file(tmp_path, original)
    read_scores(path)
    assert path.read_text(encoding="utf-8") == original


# --- Error cases -------------------------------------------------------------

def test_missing_file_is_an_error(tmp_path):
    with pytest.raises(ScoreError) as err:
        read_scores(tmp_path / "does_not_exist.txt")
    assert str(err.value) == "Error: Not Found"


@pytest.mark.parametrize("bad", ["abc", "9O", "85%", "seventy", "1,5", "--5"])
def test_non_numeric_score_is_an_error(tmp_path, bad):
    path = write_file(tmp_path, f"90\n{bad}\n80\n")
    with pytest.raises(ScoreError) as err:
        read_scores(path)
    assert str(err.value) == "Error: Not Found"


@pytest.mark.parametrize("bad", ["-1", "-0.01", "100.01", "101", "1000"])
def test_score_outside_0_to_100_is_an_error(tmp_path, bad):
    path = write_file(tmp_path, f"90\n{bad}\n")
    with pytest.raises(ScoreError) as err:
        read_scores(path)
    assert str(err.value) == "Error: Not Found"


@pytest.mark.parametrize("bad", ["nan", "inf", "-inf", "Infinity"])
def test_nan_and_infinity_are_errors(tmp_path, bad):
    path = write_file(tmp_path, f"{bad}\n")
    with pytest.raises(ScoreError) as err:
        read_scores(path)
    assert str(err.value) == "Error: Not Found"


def test_empty_file_says_content_not_found(tmp_path):
    path = write_file(tmp_path, "")
    with pytest.raises(ScoreError) as err:
        read_scores(path)
    assert str(err.value) == "Content Not Found"


def test_file_of_only_blank_lines_says_content_not_found(tmp_path):
    path = write_file(tmp_path, "\n   \n\t\n")
    with pytest.raises(ScoreError) as err:
        read_scores(path)
    assert str(err.value) == "Content Not Found"


# --- main(): what the user sees and the exit code ----------------------------

def test_main_valid_file_prints_report(tmp_path, capsys):
    path = write_file(tmp_path, "95\n80\n60\n")
    assert main([str(path)]) == 0
    assert capsys.readouterr().out == EXPECTED_REPORT + "\n"


@pytest.mark.parametrize("text", [None, "90\nabc\n", ""])
def test_errors_print_no_report(tmp_path, capsys, text):
    if text is None:
        path = tmp_path / "missing.txt"
    else:
        path = write_file(tmp_path, text)
    assert main([str(path)]) == 1
    out = capsys.readouterr().out
    assert out.strip() in ("Error: Not Found", "Content Not Found")
    for label in ("Highest", "Lowest", "Average", "Letter grade", "Scores"):
        assert label not in out


def test_main_missing_file_prints_error_and_stops(tmp_path, capsys):
    code = main([str(tmp_path / "nope.txt")])
    assert code == 1
    assert capsys.readouterr().out.strip() == "Error: Not Found"


def test_main_invalid_score_prints_error_and_stops(tmp_path, capsys):
    path = write_file(tmp_path, "90\nabc\n")
    assert main([str(path)]) == 1
    assert capsys.readouterr().out.strip() == "Error: Not Found"


def test_main_empty_file_prints_content_not_found_and_stops(tmp_path, capsys):
    path = write_file(tmp_path, "")
    assert main([str(path)]) == 1
    assert capsys.readouterr().out.strip() == "Content Not Found"


def test_main_without_file_argument_prints_usage(capsys):
    assert main([]) == 2
    assert capsys.readouterr().out.strip() == "Usage: python grades.py scores.txt"


def test_main_with_extra_arguments_prints_usage(tmp_path, capsys):
    path = write_file(tmp_path, "90\n")
    assert main([str(path), "extra"]) == 2
    assert capsys.readouterr().out.strip() == "Usage: python grades.py scores.txt"


# --- Running from the command line -------------------------------------------

def run_cli(*args, cwd):
    return subprocess.run(
        [sys.executable, str(GRADES_PY), *args],
        cwd=cwd, capture_output=True, text=True,
    )


def test_command_line_missing_file(tmp_path):
    result = run_cli("scores.txt", cwd=tmp_path)
    assert result.returncode == 1
    assert result.stdout.strip() == "Error: Not Found"


def test_command_line_valid_file_prints_report(tmp_path):
    write_file(tmp_path, "95\n80\n60\n")
    result = run_cli("scores.txt", cwd=tmp_path)
    assert result.returncode == 0
    assert result.stderr == ""
    assert result.stdout.strip() == EXPECTED_REPORT


# --- Highest and lowest ------------------------------------------------------

def test_highest_returns_largest_score():
    assert highest([70.0, 95.0, 82.0]) == 95.0


def test_lowest_returns_smallest_score():
    assert lowest([70.0, 95.0, 82.0]) == 70.0


def test_highest_and_lowest_of_single_score_are_equal():
    assert highest([77.0]) == lowest([77.0]) == 77.0


def test_highest_and_lowest_with_decimal_scores():
    scores = [85.5, 85.25, 85.75]
    assert highest(scores) == 85.75
    assert lowest(scores) == 85.25


def test_highest_and_lowest_with_repeated_scores():
    scores = [90.0, 60.0, 90.0, 60.0]
    assert highest(scores) == 90.0
    assert lowest(scores) == 60.0


# --- Average -----------------------------------------------------------------

def test_average_of_whole_numbers():
    assert average([90.0, 80.0, 70.0]) == Decimal("80.00")


def test_average_rounds_to_two_decimals():
    assert average([95.0, 80.0, 60.0]) == Decimal("78.33")


def test_average_rounds_half_up():
    assert average([80.0, 76.25]) == Decimal("78.13")


def test_average_rounds_up_into_next_whole_number():
    assert average([89.999, 90.0]) == Decimal("90.00")


def test_average_of_single_score():
    assert average([67.5]) == Decimal("67.50")


def test_average_of_all_zeros():
    assert average([0.0, 0.0, 0.0]) == Decimal("0.00")


def test_average_of_all_hundreds():
    assert average([100.0, 100.0]) == Decimal("100.00")


# --- Letter grade ------------------------------------------------------------

@pytest.mark.parametrize("avg, letter", [
    ("0", "F"), ("59", "F"), ("59.99", "F"),
    ("60", "D"), ("69.99", "D"),
    ("70", "C"), ("79.99", "C"),
    ("80", "B"), ("89.99", "B"),
    ("90", "A"), ("100", "A"),
])
def test_letter_grade_boundaries(avg, letter):
    assert letter_grade(Decimal(avg)) == letter


def test_letter_grade_uses_rounded_average(tmp_path, capsys):
    # Raw average is 89.996, which prints as 90.00, so the grade is A.
    path = write_file(tmp_path, "89.992\n90\n")
    main([str(path)])
    out = capsys.readouterr().out
    assert "Average: 90.00" in out
    assert "Letter grade: A" in out


# --- Scores in a row ---------------------------------------------------------

def test_scores_row_keeps_file_order():
    assert scores_row([60.0, 95.0, 80.0]) == "60, 95, 80"


def test_scores_row_shows_whole_numbers_without_decimals():
    assert scores_row([90.0]) == "90"


def test_scores_row_shows_decimals_as_entered():
    assert scores_row([85.5, 92.25]) == "85.5, 92.25"


def test_scores_row_single_score():
    assert scores_row([100.0]) == "100"


# --- Full report -------------------------------------------------------------

EXPECTED_REPORT = (
    "Highest: 95.00\n"
    "Lowest: 60.00\n"
    "Average: 78.33\n"
    "Letter grade: C\n"
    "Scores: 95, 80, 60"
)


def test_report_has_all_lines_in_order():
    assert build_report([95.0, 80.0, 60.0]) == EXPECTED_REPORT


def test_scores_row_is_last_line():
    lines = build_report([72.5, 88.0]).splitlines()
    assert lines[-1] == "Scores: 72.5, 88"
