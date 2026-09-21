# CS 690 Assignment 2: Ask the Code

This repository is the starter code for Assignment 2. The assignment itself, what to do
and why, is in **HANDOUT.md**. This file covers setup and the commands you will run.

## What you need

- Python 3.11, 3.12 or 3.13 (3.12 recommended). Check with `python --version`
  (on macOS and Linux it may be `python3 --version`).
- git
- An API key from Anthropic (platform.claude.com) or OpenAI (platform.openai.com),
  with a few dollars of credit. A chat subscription is not an API key.
- About 300 MB of free disk space.

## Setup

**1. Get the code.** Clone the repository and go into it:

    git clone <the repository URL from Canvas>
    cd cs690-a2-ask-the-code

**2. Make a virtual environment and turn it on.**

macOS and Linux:

    python3 -m venv .venv
    source .venv/bin/activate

Windows (PowerShell):

    py -m venv .venv
    .venv\Scripts\Activate.ps1

Your prompt now starts with `(.venv)`. Turn it on again in every new terminal.

**3. Install the packages.**

    pip install -r requirements.txt

**4. Add your key.** Copy the settings file:

    cp .env.example .env          (macOS and Linux)
    copy .env.example .env        (Windows)

Open `.env` and paste your key after `ANTHROPIC_API_KEY=` or after `OPENAI_API_KEY=`.
Paste only one; the code uses whichever you paste. Leave `AI_MODEL` blank to use the
default model. Fill in the two prices in Step 0 of the handout.

**5. Check everything.**

    python -m askcode.check_setup

This checks your Python, the packages, the code in `corpus/`, your `.env`, one tiny AI
call (less than a cent), and the local embedding model (the first time, it downloads
about 67 MB). You are ready when it prints "All checks passed."

## Commands

All commands run from the top folder of the repository, with the virtual environment on.

Check your code, one step at a time:

    pytest tests/test_split.py           Step 2
    pytest tests/test_questions.py       Steps 1 and 2
    pytest tests/test_search_words.py    Step 3
    pytest tests/test_prompt.py          Step 4
    pytest tests/test_answer.py          Step 4
    pytest tests/test_search_meaning.py  Step 7
    pytest                               everything

Run the experiments. Each writes one file in `results/`:

| Step | Command | Results file | Cost |
| --- | --- | --- | --- |
| 3 | `python -m askcode.run_eval --search words --no-ai` | retrieval_words.csv | free |
| 5 | `python -m askcode.run_eval --search words --context top3 --prompt five_part` | top3_words_five_part.csv | a few cents |
| 5 | `python -m askcode.run_eval --context whole --prompt five_part` | whole_five_part.csv | the expensive one |
| 5 | `python -m askcode.run_eval --context gold --prompt five_part` | gold_five_part.csv | about a cent |
| 6 | `python -m askcode.run_eval --search words --context top3 --prompt minimal` | top3_words_minimal.csv | a few cents |
| 7 | `python -m askcode.run_eval --search meaning --no-ai` | retrieval_meaning.csv | free |

Add `--dry-run` to any AI run to see the prompt and a cost estimate without spending
anything. Every AI reply is saved in `ai_replies/`, so running the same command again
costs nothing. `--fresh` ignores the saved replies and asks again, which costs money.

Other commands:

    python -m askcode.summary        print the tables for REPORT.md
    python -m askcode.check_freeze   check that your questions were committed before any results

## What is in this repository

| Path | What it is |
| --- | --- |
| HANDOUT.md | The assignment: what, why, every step, how it is graded |
| RUBRIC.md | The grading checklist |
| REPORT.md | Your report; fill it in during Step 8 |
| LEDGER.md | Your provenance ledger |
| prompts/ | The prompts you gave AI tools, one file per ledger entry |
| questions/questions.json | Your ten questions (Step 1) |
| askcode/core.py | Given: the types and helpers everything uses. Read it first |
| askcode/split.py, search_words.py, prompt.py, answer.py, search_meaning.py | Yours to write |
| askcode/llm.py, embed.py, run_eval.py, summary.py, questions.py, check_setup.py, check_freeze.py | Given; do not change |
| tests/ | Public tests; do not change |
| corpus/requests/ | The requests library, v2.32.3, unmodified; do not change |
| results/ | Your experiment results; created by run_eval; commit it |
| ai_replies/ | Every AI reply, saved; created by run_eval; commit it |
| .env | Your key and settings; never commit it |
| .models/ | The downloaded embedding model; ignored by git |

## Troubleshooting

**`NotImplementedError: Step 2: write split_file ...`**
That step is not written yet. The message names the file.

**`No API key found`**
You have not created `.env`, or the key line is empty. See Setup step 4.

**`Both ANTHROPIC_API_KEY and OPENAI_API_KEY are set`**
Set `AI_PROVIDER=anthropic` or `AI_PROVIDER=openai` in `.env`. A key exported in your
terminal counts too.

**`rejected your API key`**
The key was mistyped or revoked. Paste it again, with no quotes and no spaces.

**`rate limit or spend limit reached`**, or a quota message
Wait a minute and run the same command again. Answers already received are saved and
are not paid for twice. New API accounts start with low limits; if the whole-codebase
run keeps failing, check that your account has credit.

**`does not know the model`**
Leave `AI_MODEL` blank to use the default, or check the model name on your provider's
models page.

**`These questions name a function your splitter did not produce`**
Check the spelling in questions.json. Methods are written `ClassName.method_name`, and
the file is written as it appears under corpus/requests, for example `sessions.py`.

**`pip install` fails on fastembed or onnxruntime**
Check `python --version`: it must be 3.11, 3.12 or 3.13. On an Intel Mac, Python 3.14
cannot install this package; use 3.12.

**The embedding model will not download**
The first `--search meaning` run downloads the model from Hugging Face. Some campus or
company networks block it; try another network once. After that it works offline.

**PowerShell says running scripts is disabled** when you activate the environment
Run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once, then activate again.
