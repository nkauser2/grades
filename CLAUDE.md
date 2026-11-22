# Claude.md #Project 3

Language: The program's main language will be Python.

How the program is run: It is run from the project folder, run python grades.py scores.txt. The argument is the score file, one score per line.

How the program is tested: run python -m pytest
All tests must pass. A skipped test doesn't count as a pass. Automated testing will be used and it will test on reading the file, the highest, lowest, and average calculation, the letter grades assigned, the error cases, and the scores-in-a-row output.

What must never happen: Never use or require API keys, paid services/payments, or user accounts. Never change the score file without asking. Never add a feature without a test for it. 