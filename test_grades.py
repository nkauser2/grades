"""Tests for file reading and score checking in grades.py."""

import subprocess
import sys
from pathlib import Path

import pytest

from grades import ScoreError, main, read_scores

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

def test_main_valid_file_returns_0(tmp_path, capsys):
    path = write_file(tmp_path, "90\n80\n")
    assert main([str(path)]) == 0
    assert "Error" not in capsys.readouterr().out


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


def test_command_line_valid_file(tmp_path):
    write_file(tmp_path, "90\n80\n")
    result = run_cli("scores.txt", cwd=tmp_path)
    assert result.returncode == 0
    assert result.stderr == ""
