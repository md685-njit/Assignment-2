"""Check the freeze rule: your questions were committed before any results.

GIVEN CODE. Do not change it.

    python -m askcode.check_freeze

The rule (slide 57): write the questions and their answers first, commit them, and only
then run anything. If you write questions after seeing results, you will write the
ones that pass. So in your git history, the last commit that changes
questions/questions.json must come before the first commit that adds anything to
results/.
"""

from __future__ import annotations

import subprocess
import sys

from askcode import QUESTIONS_FILE, REPO_ROOT
from askcode.questions import load_questions

QUESTIONS_PATH = "questions/questions.json"
RESULTS_PATH = "results"


def git(*args: str) -> list[str]:
    out = subprocess.run(
        ["git", *args], cwd=REPO_ROOT, capture_output=True, text=True, check=True
    ).stdout
    return [line for line in out.splitlines() if line.strip()]


def main(argv: list[str] | None = None) -> int:
    try:
        history = git("log", "--format=%H", "--reverse")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("FAIL  This folder is not a git repository, or git is not installed.")
        return 1

    order = {sha: i for i, sha in enumerate(history)}
    question_commits = git("log", "--format=%H", "--", QUESTIONS_PATH)
    result_commits = git("log", "--format=%H", "--", RESULTS_PATH)
    failures = 0

    ids = [q.id for q in load_questions(QUESTIONS_FILE)]
    if ids != [f"q{n:02d}" for n in range(1, 11)]:
        print("FAIL  questions.json must hold your 10 questions with ids q01 to q10.")
        failures += 1

    if git("status", "--porcelain", "--", QUESTIONS_PATH):
        print("FAIL  questions.json has changes that are not committed.")
        failures += 1

    if not question_commits:
        print("FAIL  questions.json has never been committed.")
        failures += 1
    if not result_commits:
        print("FAIL  Nothing in results/ has been committed yet. Commit your results after your runs.")
        failures += 1

    if question_commits and result_commits:
        last_question = max(order[sha] for sha in question_commits)
        first_result = min(order[sha] for sha in result_commits)
        if last_question < first_result:
            print(
                f"PASS  questions last changed in {history[last_question][:7]}, "
                f"before the first results commit {history[first_result][:7]}."
            )
        else:
            print(
                f"FAIL  questions.json changed in {history[last_question][:7]}, which is not before "
                f"the first results commit {history[first_result][:7]}."
            )
            failures += 1

    return 0 if failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
