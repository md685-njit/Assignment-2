# Assignment 2: Ask the Code

CS 690, AI-Assisted Software Engineering, Fall 2026, Individual Assignment (100 points).
Setup and commands are in README.md. The grading checklist is in RUBRIC.md.

## What you will build

You will write a small Python program that answers questions about a codebase you did
not write: the `requests` library, the same code we used in the Week 4 lecture. The
program works in four steps:

1. Split the code into pieces, one per function.
2. Take a question and find the 3 functions that match it best.
3. Send only those 3 functions and the question to an AI model.
4. Get back an answer as JSON, with the file and line it came from, and check it.

This design is called RAG (retrieval-augmented generation): find the right text first,
then let the AI answer from it. Then you measure it. You write 10 questions whose answers
you already know, and you find out how often the program gets them right, what it costs,
and, when it is wrong, whether the search or the AI is to blame.

## Why this matters at work

**Everything you build here in this assignment is something developers build and debug in industry.**

| What you build | Where it shows up at work |
| --- | --- |
| A splitter that cuts code into functions (Step 2) | The first step of every "chat with our codebase or docs" feature: deciding what the pieces are |
| Keyword search that weighs rare words (Step 3) | Code search and log search; BM25 is the default ranking in Elasticsearch and OpenSearch |
| A five-part prompt with a fixed system part (Step 4) | Every AI feature has a system prompt that a team reviews like code; keeping the fixed part first is what lets prompt caching cut the bill |
| A strict check on the AI's JSON reply (Step 4) | Any program that uses AI output must catch a bad reply instead of trusting it |
| Ten questions with known answers (Steps 1 and 5) | An eval set: how teams decide whether a new prompt or model made things better or worse |
| Paste everything or search, with real token counts and cost (Step 5) | The cost and design decision behind every RAG feature |
| Blaming the right stage when an answer is wrong (Step 5) | The first question in debugging any AI feature: did the right text ever reach the model? |
| Meaning search with embeddings (Step 7) | Semantic search and vector databases |

When you finish, you can say in an interview: "I built a RAG pipeline over a real
codebase and measured its accuracy and its cost."

## What you need

Python 3.11 to 3.13, git, and an API key from Anthropic or OpenAI with a few dollars of
credit. The whole assignment should cost you about $1 or less with the default Anthropic
model and about $0.20 with the default OpenAI model. These are estimates from character
counts; the dry run in Step 4 shows your own estimate before you spend anything.
The meaning search in Step 7 runs on your laptop for free.

## What you write, and what is given

You write five files. Everything else is given; read it, but do not change it (the
grader restores the given files before grading).

| You write | What it does | Step |
| --- | --- | --- |
| `questions/questions.json` | Your ten questions and their known answers | 1 |
| `askcode/split.py` | Splits the code into functions | 2 |
| `askcode/search_words.py` | Finds functions by shared words | 3 |
| `askcode/prompt.py` | Builds the five-part prompt | 4 |
| `askcode/answer.py` | Checks the AI's reply | 4 |
| `askcode/search_meaning.py` | Finds functions by meaning | 7 |

Given: `askcode/core.py` (the types and helpers you use; read this first), `llm.py`
(calls the AI and saves every reply), `embed.py` (the local embedding model),
`run_eval.py` (runs the experiments), `summary.py` (prints your report tables),
`check_setup.py` and `check_freeze.py`, the public tests in `tests/`, and the code
itself in `corpus/requests/`.

Each file you write starts with its exact rules in the docstring. The tests check those
rules, and hidden tests check the same rules on more cases.

## The rules for AI tools

AI tools are permitted and expected on this assignment. You must submit a provenance
ledger recording which tools you used, a summary of what you asked them, and what
review actions you took on the output. Submitting AI-generated work you have not
reviewed is misrepresentation of authorship and is treated as an academic-integrity
violation under the course syllabus, as is fabricating ledger entries. You are
responsible for every line you submit, including lines you did not type. You may be
asked in class to explain any part of your submission.

You do not need an agent for this assignment. A chat window or an inline assistant in
your editor is enough.

### The provenance ledger

Keep `LEDGER.md` as you go, using exactly this schema. It already contains one worked
example; your own entries go below it.

```
## Entry <n>
artifact:  what this entry covers: a file, a commit SHA, a document, or an experiment
tool:      product name, model name, model version, and the date of use
prompts:   one-line summary each; the verbatim prompts live in prompts/ and are
           referenced here by file path
review:    what you read, what you changed, what you rejected, and why
checks:    the commands you ran and their results
evidence:  the requirement, test, or evidence ID this traces to
risk:      what remains unverified after this change

For an experiment, add three fields:
dataset:   task set identifier and its commit SHA or version
result:    metric, N, and the result table or its file path
changed:   what you did differently as a result
```

An entry is written when the work is done, not reconstructed at submission time. A
ledger that is one entry per session rather than one per reviewable change is wrong.

For this assignment: at least five entries, at least two of them experiment entries (a
run from Step 5, 6 or 7 counts as an experiment). Save the prompts you typed into AI
tools in `prompts/`, one file per entry, and name that file in the entry.

## The steps

### Step 0. Set up (20 minutes)

1. Follow README.md, "Setup", steps 1 to 5.
2. Look up the current price of your model on your provider's pricing page and put
   both numbers in `.env` (`PRICE_INPUT_PER_MTOK`, `PRICE_OUTPUT_PER_MTOK`). Prices
   change, so do not copy them from anywhere else.
3. Write ledger entry 1: your provider, your model, the two prices and the page you
   found them on.

Done when: `python -m askcode.check_setup` prints "All checks passed."

### Step 1. Write your ten questions (30 minutes)

Slides 54 to 57 and 62. You started this in class; the three questions you wrote there
are your first three.

1. Replace the two examples in `questions/questions.json` with ten questions of your
   own, with ids `q01` to `q10`. Do not reuse the two examples.
2. Each question is something a new teammate would really ask about this code, answered
   by one function. For each, write the file (`expected_file`, for example
   `"sessions.py"`), the function (`expected_function`, written `ClassName.method_name`
   for a method, for example `"SessionRedirectMixin.should_strip_auth"`), and the
   answer in a sentence (`expected_answer`).
3. At least one question must be one the code cannot answer. Set its `expected_file`
   and `expected_function` to `null`.
4. Choose answers that sit inside a function or method. Your splitter will not see code
   outside functions, or the three functions defined inside `if` or `try` blocks
   (`proxy_bypass` and `proxy_bypass_registry` in utils.py, `SOCKSProxyManager` in
   adapters.py).
5. Commit the file before you run anything:
   `git add questions/questions.json` then `git commit -m "Freeze my questions"`.

This is the freeze rule from slide 57. If you write questions after seeing results, you
will write the ones that pass. After your first results commit, do not change this file;
`python -m askcode.check_freeze` checks it. Fixing a misspelled function name before your
first results commit is fine.

Done when: the file is committed. (`pytest tests/test_questions.py` can only fully pass
after Step 2, because it uses your splitter to check the function names.)

### Step 2. Split the code into functions (45 minutes)

Slides 40 to 42: the cut decides what can be found.

Write `split_file` and `split_corpus` in `askcode/split.py`, using Python's built-in
`ast` module. A method becomes a chunk named `ClassName.method_name`; decorators belong
to the function they decorate; code outside functions is not a chunk. The six rules are
in the docstring. For the requests code your splitter must produce 230 chunks, and
`SessionRedirectMixin.should_strip_auth` must run from line 127 to line 157 of
sessions.py.

Done when: `pytest tests/test_split.py` and `pytest tests/test_questions.py` pass.

### Step 3. Search by words (45 minutes)

Slide 45: keyword search, and what it misses.

Write `search_words` in `askcode/search_words.py`. A chunk scores points for every
question word it contains, and rare words score more than common ones. In this codebase,
"authorization" appears in 8 of the 230 functions, so it weighs log(230 / 8) = 3.36;
"self" appears in 155, so it weighs only log(230 / 155) = 0.39. The exact formula is in
the docstring.

Then run the first experiment. It makes no AI calls and costs nothing:

    python -m askcode.run_eval --search words --no-ai

It writes `results/retrieval_words.csv` and prints how many of your answerable questions
had the right function in the top 3.

Done when: `pytest tests/test_search_words.py` passes and the results file exists.

### Step 4. Build the prompt and check the reply (60 minutes)

Slides 5 to 7 (a prompt is a spec, in five parts), 20 and 26 (standing instructions go
first), 30 to 33 (JSON your program can use, and what a schema does not buy you), and 49.

Part A. Write `build_prompt_five_part` in `askcode/prompt.py`. The prompt has two parts:

- `system`: the five labeled parts (Goal, Inputs and outputs, Rules, Example, Reply
  format). It is the same for every question, so it goes first.
- `user`: the code, then the question, last.

Your rules must say what to do when the code shown does not answer the question: reply
"not found in the code shown" with null file and line.

Part B. Write `parse_reply` in `askcode/answer.py`. Your program trusts nothing the AI
sends until it passes this check: exactly one JSON object, exactly the keys answer, file
and line, with the right types. A reply that adds a friendly sentence around the JSON
fails, and that is the point (slide 37). A reply that passes is well formed, not
necessarily true; that is what Step 5 measures.

Before you spend anything, look at a real prompt and the cost estimate:

    python -m askcode.run_eval --search words --context top3 --prompt five_part --dry-run

Done when: `pytest tests/test_prompt.py` and `pytest tests/test_answer.py` pass.

### Step 5. Measure it (45 minutes)

Slides 24 and 25 (tokens are the bill; stuffing everything in fails) and 58 to 61
(measure, then find whose fault it is).

1. Run three experiments. Each asks the AI all ten questions, with different code in
   the prompt:

       python -m askcode.run_eval --search words --context top3 --prompt five_part
       python -m askcode.run_eval --context whole --prompt five_part
       python -m askcode.run_eval --context gold --prompt five_part

   `top3` sends the 3 functions your search found. `whole` pastes the entire codebase,
   18 files, into every question; it costs by far the most, so run it with `--dry-run`
   first. `gold` sends exactly the function you named in your answer key; it shows what
   the AI does when the search is perfect.

2. Mark every answer. Open each of the three results files in a spreadsheet or editor.
   In the `correct` column, write `yes` or `no` for every row, comparing `reply_answer`
   with your `expected_answer`. For the question the code cannot answer, `yes` only if
   the reply says it was not found. A row with `valid_json` = no is `no`. Your marks
   survive reruns as long as the reply is unchanged.

3. Blame the right stage. For every question marked `no` in `top3_words_five_part`:

   - The right function was not in the top 3 (`hit` = no), and with the gold context
     the answer was correct: **retrieval** failure. The AI never saw the right code.
   - `hit` = no, and the gold run was also wrong: **both**.
   - `hit` = yes, or `n/a` for the question the code cannot answer: **generation**
     failure. The right code was there, or there was nothing to find, and the AI still
     got it wrong.

   `python -m askcode.summary` prints Table 3 with this evidence for each question.

4. Commit `results/` and `ai_replies/`. Write an experiment entry in your ledger.

Every AI reply is saved in `ai_replies/`, so running the same command again reads the
saved reply and costs nothing. `--fresh` asks again and costs money.

Done when: the three files exist with every `correct` cell filled, and they are committed.

### Step 6. Addition 1: does the five-part prompt beat a minimal one? (30 minutes)

Slides 4 to 8: what makes one prompt better than another.

The given `build_prompt_minimal` in core.py sends just the question, the code and "Reply
in JSON with the keys answer, file and line." No goal, no rules, no example. Run it on
exactly the same search results as your five-part prompt:

    python -m askcode.run_eval --search words --context top3 --prompt minimal

Mark the `correct` column. Compare with `top3_words_five_part`: valid JSON, right place
and correct. Only the prompt changed between the two runs, so any difference comes from
the prompt. Find one question where the two replies differed and look at why.

Done when: `results/top3_words_minimal.csv` has every `correct` cell filled and is committed.

### Step 7. Addition 2: search by meaning (60 minutes)

Slides 43 to 47: embeddings, and why keyword search and meaning search fail in opposite
directions.

Write `cosine` and `MeaningIndex` in `askcode/search_meaning.py`. The given `embed.py`
turns text into 384 numbers with a small free model on your own laptop; texts with
similar meaning get similar numbers. Your index embeds every function once, then scores
each question against all of them with cosine similarity.

    pytest tests/test_search_meaning.py
    python -m askcode.run_eval --search meaning --no-ai

The first run downloads the model once, about 67 MB. It makes no AI calls and costs
nothing. Then compare `retrieval_meaning` with `retrieval_words` in Tables 1 and 4 of
`python -m askcode.summary`: which questions did each search find that the other missed?

Done when: the tests pass and `results/retrieval_meaning.csv` is committed.

### Step 8. Write the report and finish the ledger (30 minutes)

Slide 63: the decision rule.

1. Run `python -m askcode.summary` and paste Tables 1 and 2 into REPORT.md exactly as
   printed. The grader runs the same command and compares.
2. Fill in the five sections of REPORT.md. Each asks for specific numbers from your
   own results.
3. Finish LEDGER.md and check that every prompts file it names exists in `prompts/`.
4. After your final runs, do not change the code that splits, searches or builds
   prompts. If you do, run the experiments again, because the grader reproduces every
   result from your committed code and `ai_replies/`.
5. Commit and push.

## What to submit

Push your repository to GitHub and submit its link on Canvas, as with Assignment 1. It
must contain:

- your five code files and `questions/questions.json`
- `results/` with the six files: retrieval_words, retrieval_meaning,
  top3_words_five_part, whole_five_part, gold_five_part, top3_words_minimal
- `ai_replies/`
- `REPORT.md`, `LEDGER.md` and `prompts/`

Never commit `.env`; it holds your key. `.gitignore` already leaves it out.

## How it is graded

RUBRIC.md has every item. In short: your code, checked by public and hidden tests, is 50
points; your questions and results, including whether the grader can reproduce them from
your commits, are 26; your report and ledger are 24.
