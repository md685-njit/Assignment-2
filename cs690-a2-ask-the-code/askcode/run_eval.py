"""Run every question through the pipeline and write one results file.

GIVEN CODE. Do not change it.

    python -m askcode.run_eval --search words --no-ai
    python -m askcode.run_eval --search words --context top3 --prompt five_part
    python -m askcode.run_eval --context whole --prompt five_part
    python -m askcode.run_eval --context gold --prompt five_part
    python -m askcode.run_eval --search words --context top3 --prompt minimal
    python -m askcode.run_eval --search meaning --no-ai

Options
  --search   words or meaning: how the top 3 chunks are found (context top3 only)
  --context  top3: send the 3 chunks search found
             whole: send the whole codebase (paste everything)
             gold: send only the function you said answers the question
  --prompt   five_part (yours, prompt.py) or minimal (the fixed baseline)
  --no-ai    measure search only; no AI calls, no cost
  --dry-run  build every prompt and estimate tokens and cost; no AI calls
  --fresh    ignore saved replies in ai_replies/ and ask the AI again (costs money)
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

from askcode import CORPUS_DIR, QUESTIONS_FILE, RESULTS_DIR
from askcode.core import BadReply, Chunk, Prompt, build_prompt_minimal, whole_codebase
from askcode.questions import Question, load_questions

TOP_K = 3

RETRIEVAL_COLUMNS = ["id", "question", "expected_file", "expected_function", "retrieved", "hit", "hit_rank"]
AI_COLUMNS = RETRIEVAL_COLUMNS + [
    "valid_json",
    "reply_answer",
    "reply_file",
    "reply_line",
    "right_place",
    "input_tokens",
    "output_tokens",
    "provider",
    "model",
    "price_input_per_mtok",
    "price_output_per_mtok",
    "raw_reply",
    "correct",
]


class StepNotDone(Exception):
    """A student function still raises NotImplementedError."""


def run_name(args: argparse.Namespace) -> str:
    if args.no_ai:
        return f"retrieval_{args.search}"
    if args.context == "top3":
        return f"top3_{args.search}_{args.prompt}"
    return f"{args.context}_{args.prompt}"


def _call_student(step: str, func, *call_args):
    try:
        return func(*call_args)
    except NotImplementedError as exc:
        raise StepNotDone(f"{step} is not written yet: {exc}") from exc


def load_chunks() -> list[Chunk]:
    from askcode.split import split_corpus

    return _call_student("Step 2 (split.py)", split_corpus, CORPUS_DIR)


def find_expected(questions: list[Question], chunks: list[Chunk]) -> dict[str, Chunk]:
    """Map each answerable question id to the chunk its expected_function names."""
    by_key = {(c.file, c.name): c for c in chunks}
    expected, missing = {}, []
    for q in questions:
        if not q.answerable:
            continue
        chunk = by_key.get((q.expected_file, q.expected_function))
        if chunk is None:
            missing.append(f"  {q.id}: {q.expected_file} :: {q.expected_function}")
        else:
            expected[q.id] = chunk
    if missing:
        raise ValueError(
            "These questions name a function your splitter did not produce. Check the "
            "spelling (methods are written ClassName.method_name) and that split.py "
            "follows the Step 2 rules:\n" + "\n".join(missing)
        )
    return expected


def make_searcher(kind: str, chunks: list[Chunk]):
    if kind == "words":
        from askcode.search_words import search_words

        return lambda question: _call_student("Step 3 (search_words.py)", search_words, question, chunks, TOP_K)
    from askcode.search_meaning import MeaningIndex

    print("Embedding all chunks with the local model (the first run downloads it once)...")
    index = _call_student("Step 7 (search_meaning.py)", MeaningIndex, chunks)
    return lambda question: _call_student("Step 7 (search_meaning.py)", index.search, question, TOP_K)


def retrieval_row(q: Question, retrieved: list[Chunk] | None, expected: dict[str, Chunk]) -> dict:
    row = {
        "id": q.id,
        "question": q.question,
        "expected_file": q.expected_file or "",
        "expected_function": q.expected_function or "",
        "retrieved": "",
        "hit": "n/a",
        "hit_rank": "",
    }
    if retrieved is not None:
        row["retrieved"] = "; ".join(c.id for c in retrieved)
        if q.answerable:
            ids = [c.id for c in retrieved]
            target = expected[q.id].id
            row["hit"] = "yes" if target in ids else "no"
            row["hit_rank"] = str(ids.index(target) + 1) if target in ids else ""
    return row


def right_place(q: Question, parsed: dict | None, expected: dict[str, Chunk]) -> str:
    if parsed is None:
        return "no"
    if not q.answerable:
        return "yes" if parsed["file"] is None and parsed["line"] is None else "no"
    target = expected[q.id]
    if parsed["file"] != target.file or parsed["line"] is None:
        return "no"
    return "yes" if target.start_line <= parsed["line"] <= target.end_line else "no"


def previous_marks(path: Path) -> dict[str, tuple[str, str]]:
    """Keep hand-marked 'correct' values when a rerun produces the same reply."""
    if not path.exists():
        return {}
    with path.open(newline="", encoding="utf-8") as f:
        return {r["id"]: (r.get("raw_reply", ""), r.get("correct", "")) for r in csv.DictReader(f)}


def write_csv(path: Path, columns: list[str], rows: list[dict]) -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m askcode.run_eval",
        description="Run every question through the pipeline and write results/<run name>.csv.",
    )
    parser.add_argument("--search", choices=["words", "meaning"], default="words")
    parser.add_argument("--context", choices=["top3", "whole", "gold"], default="top3")
    parser.add_argument("--prompt", choices=["five_part", "minimal"], default="five_part")
    parser.add_argument("--no-ai", action="store_true", help="measure search only; no AI calls")
    parser.add_argument("--dry-run", action="store_true", help="build prompts and estimate cost; no AI calls")
    parser.add_argument("--fresh", action="store_true", help="ignore saved replies and ask again")
    parser.add_argument("--questions", default=str(QUESTIONS_FILE), help=argparse.SUPPRESS)
    args = parser.parse_args(argv)

    if args.no_ai and args.context != "top3":
        parser.error("--no-ai measures search, so it only works with --context top3.")

    from askcode import llm

    try:
        return _run(args)
    except (StepNotDone, ValueError, llm.SetupError, llm.AIError) as exc:
        print(f"\nStopped: {exc}")
        return 1


def _run(args: argparse.Namespace) -> int:
    from askcode import llm

    questions = load_questions(args.questions)
    chunks = load_chunks()
    expected = find_expected(questions, chunks)
    name = run_name(args)
    out_path = RESULTS_DIR / f"{name}.csv"

    retrieved_for: dict[str, list[Chunk] | None] = {q.id: None for q in questions}
    if args.context == "top3":
        searcher = make_searcher(args.search, chunks)
        for q in questions:
            retrieved_for[q.id] = searcher(q.question)

    if args.no_ai:
        rows = [retrieval_row(q, retrieved_for[q.id], expected) for q in questions]
        write_csv(out_path, RETRIEVAL_COLUMNS, rows)
        answerable = [r for r in rows if r["hit"] != "n/a"]
        hits = sum(r["hit"] == "yes" for r in answerable)
        print(f"\nRun: {name}")
        print(f"Right function in the top {TOP_K}: {hits} of {len(answerable)} answerable questions")
        print(f"Wrote {out_path.relative_to(out_path.parent.parent)}")
        return 0

    if args.prompt == "five_part":
        from askcode.prompt import build_prompt_five_part

        def build(question: str, context: list[Chunk]) -> Prompt:
            return _call_student("Step 4 (prompt.py)", build_prompt_five_part, question, context)
    else:
        build = build_prompt_minimal

    whole = whole_codebase(CORPUS_DIR) if args.context == "whole" else None
    prompts: dict[str, Prompt] = {}
    for q in questions:
        if args.context == "top3":
            context = retrieved_for[q.id] or []
        elif args.context == "whole":
            context = whole
        else:
            context = [expected[q.id]] if q.answerable else []
        prompts[q.id] = build(q.question, context)

    if args.dry_run:
        try:
            settings = llm.load_settings()
        except llm.SetupError:
            settings = None
        return _dry_run(name, questions, prompts, settings, llm)

    settings = llm.load_settings()

    from askcode.answer import parse_reply

    old = previous_marks(out_path)
    rows = []
    for number, q in enumerate(questions, start=1):
        reply = llm.ask_model(prompts[q.id], settings, fresh=args.fresh)
        source = "saved" if reply.cached else "asked"
        print(f"  [{number}/{len(questions)}] {q.id}: {source}, {reply.input_tokens} in, {reply.output_tokens} out")
        row = retrieval_row(q, retrieved_for[q.id], expected)
        try:
            parsed = _call_student("Step 4 (answer.py)", parse_reply, reply.text)
            valid = "yes"
        except BadReply:
            parsed, valid = None, "no"
        prev_raw, prev_mark = old.get(q.id, ("", ""))
        row.update(
            {
                "valid_json": valid,
                "reply_answer": parsed["answer"] if parsed else "",
                "reply_file": (parsed["file"] or "") if parsed else "",
                "reply_line": (str(parsed["line"]) if parsed["line"] is not None else "") if parsed else "",
                "right_place": right_place(q, parsed, expected),
                "input_tokens": str(reply.input_tokens),
                "output_tokens": str(reply.output_tokens),
                "provider": reply.provider,
                "model": reply.model,
                "price_input_per_mtok": "" if settings.price_input_per_mtok is None else str(settings.price_input_per_mtok),
                "price_output_per_mtok": "" if settings.price_output_per_mtok is None else str(settings.price_output_per_mtok),
                "raw_reply": reply.text,
                "correct": prev_mark if prev_raw == reply.text else "",
            }
        )
        rows.append(row)

    write_csv(out_path, AI_COLUMNS, rows)
    _print_ai_summary(name, rows, out_path, llm)
    return 0


def _dry_run(name, questions, prompts, settings, llm) -> int:
    first = prompts[questions[0].id]
    print(f"Dry run: {name}. Nothing is sent. Here is the prompt for {questions[0].id}:\n")
    print("----- system -----")
    print(first.system or "(empty)")
    print("----- user -----")
    lines = first.user.split("\n")
    if len(lines) > 60:
        print("\n".join(lines[:30]))
        print(f"... {len(lines) - 60} more lines ...")
        print("\n".join(lines[-30:]))
    else:
        print(first.user)
    total = sum(llm.estimate_tokens(p.system + p.user) for p in prompts.values())
    print("\n----- estimate -----")
    print(f"Questions: {len(prompts)}")
    print(f"Estimated input tokens for the whole run: about {total:,} (characters divided by 4)")
    dollars = None
    if settings is not None:
        dollars = llm.cost_usd(total, 0, settings.price_input_per_mtok, settings.price_output_per_mtok)
    if dollars is None:
        print("Set PRICE_INPUT_PER_MTOK and PRICE_OUTPUT_PER_MTOK in .env to see an input cost estimate.")
    else:
        print(f"Estimated input cost: about ${dollars:.4f} with {settings.provider} {settings.model}")
    return 0


def _print_ai_summary(name, rows, out_path, llm) -> None:
    n = len(rows)
    valid = sum(r["valid_json"] == "yes" for r in rows)
    place = sum(r["right_place"] == "yes" for r in rows)
    tin = sum(int(r["input_tokens"]) for r in rows)
    tout = sum(int(r["output_tokens"]) for r in rows)
    price_in = float(rows[0]["price_input_per_mtok"]) if rows[0]["price_input_per_mtok"] else None
    price_out = float(rows[0]["price_output_per_mtok"]) if rows[0]["price_output_per_mtok"] else None
    dollars = llm.cost_usd(tin, tout, price_in, price_out)
    print(f"\nRun: {name}")
    print(f"Valid JSON:  {valid} of {n}")
    print(f"Right place: {place} of {n}")
    print(f"Tokens: {tin:,} in, {tout:,} out")
    print(f"Cost: ${dollars:.4f}" if dollars is not None else "Cost: set the prices in .env and rerun to record it")
    print(f"Wrote {out_path.relative_to(out_path.parent.parent)}")
    print("Next: open the file and fill the 'correct' column with yes or no for every row.")


if __name__ == "__main__":
    sys.exit(main())
