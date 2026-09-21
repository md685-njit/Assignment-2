"""Ask the Code: answer questions about a codebase by finding the right code first.

CS 690, Assignment 2. Read HANDOUT.md for the assignment and README.md for setup.
"""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CORPUS_DIR = REPO_ROOT / "corpus" / "requests"
QUESTIONS_FILE = REPO_ROOT / "questions" / "questions.json"
RESULTS_DIR = REPO_ROOT / "results"
REPLIES_DIR = REPO_ROOT / "ai_replies"
MODELS_DIR = REPO_ROOT / ".models"
ENV_FILE = REPO_ROOT / ".env"
