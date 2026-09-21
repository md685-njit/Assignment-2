"""Print the tables for REPORT.md from the files in results/.

GIVEN CODE. Do not change it.

    python -m askcode.summary

Copy each table into REPORT.md exactly as printed. The grader runs this same command
on your repository and compares.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

from askcode import RESULTS_DIR

RETRIEVAL_RUNS = ["retrieval_words", "retrieval_meaning"]
AI_RUNS = ["top3_words_five_part", "whole_five_part", "gold_five_part", "top3_words_minimal"]
MARKS = {"yes", "no"}


def read_run(results_dir: Path, name: str) -> list[dict] | None:
    path = results_dir / f"{name}.csv"
    if not path.exists():
        return None
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _mark(value: str) -> str:
    return value.strip().lower()


def retrieval_table(runs: dict[str, list[dict]]) -> list[str]:
    lines = ["| Run | Right function in top 3 |", "| --- | --- |"]
    for name in RETRIEVAL_RUNS:
        rows = runs.get(name)
        if rows is None:
            lines.append(f"| {name} | not run yet |")
            continue
        answerable = [r for r in rows if r["hit"] != "n/a"]
        hits = sum(r["hit"] == "yes" for r in answerable)
        lines.append(f"| {name} | {hits} of {len(answerable)} |")
    return lines


def _cost(rows: list[dict]) -> str:
    first = rows[0]
    if not first.get("price_input_per_mtok") or not first.get("price_output_per_mtok"):
        return "prices not set"
    tin = sum(int(r["input_tokens"]) for r in rows)
    tout = sum(int(r["output_tokens"]) for r in rows)
    dollars = tin / 1e6 * float(first["price_input_per_mtok"]) + tout / 1e6 * float(first["price_output_per_mtok"])
    return f"{dollars:.4f}"


def answers_table(runs: dict[str, list[dict]], names: list[str]) -> list[str]:
    lines = [
        "| Run | Valid JSON | Right place | Correct (your marks) | Input tokens | Output tokens | Cost (USD) |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for name in names:
        rows = runs.get(name)
        if rows is None:
            lines.append(f"| {name} | not run yet | | | | | |")
            continue
        n = len(rows)
        valid = sum(r["valid_json"] == "yes" for r in rows)
        place = sum(r["right_place"] == "yes" for r in rows)
        correct = sum(_mark(r["correct"]) == "yes" for r in rows)
        unmarked = sum(_mark(r["correct"]) not in MARKS for r in rows)
        correct_text = f"{correct} of {n}" + (f" ({unmarked} unmarked)" if unmarked else "")
        tin = sum(int(r["input_tokens"]) for r in rows)
        tout = sum(int(r["output_tokens"]) for r in rows)
        lines.append(
            f"| {name} | {valid} of {n} | {place} of {n} | {correct_text} | {tin:,} | {tout:,} | {_cost(rows)} |"
        )
    return lines


def attribution_table(runs: dict[str, list[dict]]) -> list[str]:
    top3 = runs.get("top3_words_five_part")
    gold = runs.get("gold_five_part")
    if top3 is None or gold is None:
        return ["Run top3_words_five_part and gold_five_part first."]
    gold_by_id = {r["id"]: r for r in gold}
    wrong = [r for r in top3 if _mark(r["correct"]) == "no"]
    if not wrong:
        return ["No question is marked correct = no in top3_words_five_part."]
    lines = ["| Question | Hit in top 3 | Correct with gold context |", "| --- | --- | --- |"]
    for r in wrong:
        g = gold_by_id.get(r["id"])
        gold_mark = _mark(g["correct"]) if g else "missing"
        lines.append(f"| {r['id']} | {r['hit']} | {gold_mark or 'unmarked'} |")
    return lines


def rank_table(runs: dict[str, list[dict]]) -> list[str]:
    words_rows = runs.get("retrieval_words")
    meaning_rows = runs.get("retrieval_meaning")
    if words_rows is None or meaning_rows is None:
        return ["Run retrieval_words and retrieval_meaning first."]
    meaning_by_id = {r["id"]: r for r in meaning_rows}
    lines = ["| Question | Rank with words | Rank with meaning |", "| --- | --- | --- |"]
    for r in words_rows:
        if r["hit"] == "n/a":
            continue
        m = meaning_by_id.get(r["id"], {})
        lines.append(f"| {r['id']} | {r['hit_rank'] or 'not in top 3'} | {m.get('hit_rank') or 'not in top 3'} |")
    return lines


def problems(runs: dict[str, list[dict]]) -> list[str]:
    found = []
    for name in RETRIEVAL_RUNS + AI_RUNS:
        if name not in runs:
            found.append(f"results/{name}.csv is missing.")
    for name in AI_RUNS:
        for r in runs.get(name) or []:
            if _mark(r["correct"]) not in MARKS:
                found.append(f"results/{name}.csv, {r['id']}: correct must be yes or no.")
    return found


def main(argv: list[str] | None = None) -> int:
    results_dir = Path(argv[0]) if argv else RESULTS_DIR
    runs = {}
    for path in sorted(results_dir.glob("*.csv")):
        rows = read_run(results_dir, path.stem)
        if rows:
            runs[path.stem] = rows
    extra_ai = sorted(n for n, rows in runs.items() if n not in AI_RUNS and "valid_json" in rows[0])

    print("Table 1. Finding the right function\n")
    print("\n".join(retrieval_table(runs)))
    print("\nTable 2. Answers\n")
    print("\n".join(answers_table(runs, AI_RUNS + extra_ai)))
    print("\nTable 3. Evidence for Step 5: questions marked wrong in top3_words_five_part\n")
    print("\n".join(attribution_table(runs)))
    print("\nTable 4. Evidence for Step 7: where each search ranked the right function\n")
    print("\n".join(rank_table(runs)))
    issues = problems(runs)
    if issues:
        print("\nStill to do:")
        for issue in issues:
            print(f"  {issue}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
