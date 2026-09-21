"""Public tests for Step 1 (questions/questions.json). Run: pytest tests/test_questions.py

These fail until you replace the two examples with your own ten questions.
They also need your Step 2 splitter, to check that every function you name exists.
"""

from askcode import CORPUS_DIR, QUESTIONS_FILE
from askcode.questions import load_questions
from askcode.split import split_corpus


def test_ten_questions_with_ids_q01_to_q10():
    ids = [q.id for q in load_questions(QUESTIONS_FILE)]
    assert ids == [f"q{n:02d}" for n in range(1, 11)]


def test_at_least_one_question_the_code_cannot_answer():
    assert any(not q.answerable for q in load_questions(QUESTIONS_FILE))


def test_no_question_is_asked_twice():
    texts = [q.question.strip().lower() for q in load_questions(QUESTIONS_FILE)]
    assert len(set(texts)) == len(texts)


def test_every_named_function_exists():
    names = {(c.file, c.name) for c in split_corpus(CORPUS_DIR)}
    missing = [
        f"{q.id}: {q.expected_file} :: {q.expected_function}"
        for q in load_questions(QUESTIONS_FILE)
        if q.answerable and (q.expected_file, q.expected_function) not in names
    ]
    assert missing == [], "These do not match any chunk: " + "; ".join(missing)
