"""Step 0: check that everything is installed and your key works.

GIVEN CODE. Do not change it.

    python -m askcode.check_setup                    everything (one tiny AI call, less than a cent)
    python -m askcode.check_setup --skip-ai          no AI call
    python -m askcode.check_setup --skip-embeddings  do not load the local embedding model
"""

from __future__ import annotations

import argparse
import importlib
import sys

from askcode import CORPUS_DIR
from askcode.core import Prompt

EXPECTED_FILES = 18
EXPECTED_LINES = 5642

_failures = 0


def report(ok: bool, label: str, detail: str = "") -> None:
    global _failures
    if not ok:
        _failures += 1
    print(f"{'PASS' if ok else 'FAIL'}  {label}{': ' + detail if detail else ''}")


def note(label: str, detail: str) -> None:
    print(f"NOTE  {label}: {detail}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m askcode.check_setup")
    parser.add_argument("--skip-ai", action="store_true")
    parser.add_argument("--skip-embeddings", action="store_true")
    args = parser.parse_args(argv)

    version = sys.version_info
    report((3, 11) <= version[:2] <= (3, 13), "Python 3.11 to 3.13", f"you have {version.major}.{version.minor}.{version.micro}")

    for module, label in [
        ("anthropic", "anthropic"),
        ("openai", "openai"),
        ("dotenv", "python-dotenv"),
        ("pytest", "pytest"),
        ("fastembed", "fastembed"),
    ]:
        try:
            mod = importlib.import_module(module)
            report(True, f"package {label}", getattr(mod, "__version__", "installed"))
        except ImportError:
            report(False, f"package {label}", "not installed; run: pip install -r requirements.txt")

    files = sorted(CORPUS_DIR.rglob("*.py"))
    lines = sum(len(p.read_text(encoding="utf-8").splitlines()) for p in files)
    report(
        len(files) == EXPECTED_FILES and lines == EXPECTED_LINES,
        "corpus is requests v2.32.3, unmodified",
        f"{len(files)} files, {lines:,} lines (expected {EXPECTED_FILES} and {EXPECTED_LINES:,})",
    )

    from askcode import llm

    settings = None
    try:
        settings = llm.load_settings()
        masked = (settings.api_key[:7] + "...") if settings.api_key else "(none)"
        report(settings.api_key is not None, ".env", f"provider {settings.provider}, model {settings.model}, key {masked}")
        if settings.price_input_per_mtok is None or settings.price_output_per_mtok is None:
            note("prices", "PRICE_INPUT_PER_MTOK and PRICE_OUTPUT_PER_MTOK are not set yet; set them before Step 5")
        else:
            note(
                "prices",
                f"${settings.price_input_per_mtok} in and ${settings.price_output_per_mtok} out per million tokens",
            )
    except llm.SetupError as exc:
        report(False, ".env", str(exc))

    if not args.skip_ai and settings is not None and settings.api_key:
        try:
            text, tin, tout = llm.call_model(Prompt(system="", user="Reply with the single word: ok"), settings)
            report(True, "AI call", f"reply {text.strip()[:40]!r}, {tin} tokens in, {tout} out")
        except (llm.AIError, llm.SetupError) as exc:
            report(False, "AI call", str(exc))

    if not args.skip_embeddings:
        try:
            from askcode import embed

            print("      loading the embedding model (the first time downloads about 67 MB)...")
            vector = embed.embed_query("How are redirects handled?")
            report(len(vector) == 384, "local embedding model", f"{embed.MODEL_NAME}, {len(vector)} numbers per text")
        except Exception as exc:  # show any failure plainly; this is a diagnostic tool
            report(False, "local embedding model", f"{type(exc).__name__}: {exc}")

    print()
    print("All checks passed." if _failures == 0 else f"{_failures} check(s) failed. See README.md, Troubleshooting.")
    return 0 if _failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
