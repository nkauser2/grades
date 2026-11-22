Spec Project 3

"Grades" is a program that reads scores from a file given on the command line.  One score per line in the file.

The program must print the highest, lowest, and average score (rounded to two decimal places).

The program must show an error message "Error: Not Found" if the file is missing or a score is not a valid number. The score range is (0-100, inclusive). The program must say if it encounters an empty file and say "Content Not Found" Program stops. 

Scores outside 0-100 are invalid ("Error: Not Found"). Decimals (e.g. 85.5) are valid. "nan" and "infinity" are invalid. A missing or extra argument prints "Usage: python grades.py scores.txt".

The program must print a letter equivalent grade for the average found. F: 0 to 59, D: 60 to 69, C: 70-79, B: 80-89, A: 90-100.

The program must print all the scores in a row at the bottom of the output.