# Assignment 2 Rubric: Ask the Code

100 points. Every item can be checked on its own. Where an item says "in proportion",
the points are the share of tests passed, rounded to the nearest whole point.

Before grading, the grader restores the official given files and public tests, so
editing them changes nothing. The grader also runs a set of hidden tests that check the
same written rules as the public tests, on more cases.

## A. Your code, checked by tests (50 points)

| Item | Points | How it is checked |
| --- | --- | --- |
| A1 | 6 | `pytest tests/test_split.py` passes; in proportion |
| A2 | 6 | `pytest tests/test_search_words.py` passes; in proportion |
| A3 | 5 | `pytest tests/test_prompt.py` passes; in proportion |
| A4 | 6 | `pytest tests/test_answer.py` passes; in proportion |
| A5 | 5 | `pytest tests/test_search_meaning.py` passes; in proportion |
| A6 | 22 | Hidden tests pass, in proportion within each group: split 6, word search 5, prompt 3, reply check 5, meaning search 3 |

## B. Your questions and results (26 points)

| Item | Points | How it is checked |
| --- | --- | --- |
| B1 | 4 | `pytest tests/test_questions.py` passes: ten questions with ids q01 to q10, at least one the code cannot answer, no repeats, and every named function exists |
| B2 | 4 | `python -m askcode.check_freeze` passes: questions.json was last changed in a commit before the first commit that adds anything to results/ |
| B3 | 6 | One point for each file present in results/: retrieval_words.csv, retrieval_meaning.csv, top3_words_five_part.csv, whole_five_part.csv, gold_five_part.csv, top3_words_minimal.csv |
| B4 | 6 | One point for each of those six runs that the grader reproduces from your committed code and ai_replies/ with no API key: identical except the correct column (for retrieval_meaning, identical hit and hit_rank columns) |
| B5 | 6 | 2 points: every row of the four AI runs has correct marked yes or no. 4 points: the grader checks five random marks against your expected answers and agrees with at least four |

## C. Your report and ledger (24 points)

| Item | Points | How it is checked |
| --- | --- | --- |
| C1 | 4 | 2 points each: Table 1 and Table 2 in REPORT.md match the output of `python -m askcode.summary`, row for row |
| C2 | 5 | Every question marked wrong in top3_words_five_part has a fault label that follows the Step 5 rule, given its hit value and its gold run mark, plus one sentence of evidence. 1 point off per missing or wrong label, down to 0 |
| C3 | 3 | Section 3 names the prompt that did better on right place and on correct, gives both numbers for both prompts, and names one question where the two prompts' replies differed |
| C4 | 3 | Section 4 names one question meaning search ranked higher than word search, and one the other way (or says none exists), each with the ranks from Table 4 |
| C5 | 3 | Section 5 states one decision rule for this codebase, choosing between pasting everything and searching, and cites the measured cost and the measured correct count of both |
| C6 | 6 | 2 points: at least five ledger entries with all seven fields. 2 points: at least two experiment entries with dataset, result and changed. 2 points: every entry's checks field names a command and its result, and its prompts field names a file that exists in prompts/ |

## Deductions outside the points

Submitting unreviewed AI output, fabricated ledger entries or fabricated results is an
academic integrity violation under the course syllabus, not a points question.
